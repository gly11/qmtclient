from __future__ import annotations

import json
import unittest

import httpx

from qmtclient import (
    QmtClient,
    QmtDataEmptyError,
    QmtRpcError,
    QmtSchemaMismatchError,
    stock_account,
)


def _trader_response(data: dict[str, object]) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "ok": True,
            "data": data,
            "error": None,
            "meta": {"schema": "trader.readonly.v1"},
        },
    )


class StrategyFacadeTests(unittest.TestCase):
    def test_stock_account_is_json_friendly(self) -> None:
        self.assertEqual(
            stock_account("10001"),
            {"__type__": "StockAccount", "account_id": "10001", "account_type": "STOCK"},
        )

    def test_market_get_full_tick_calls_xtdata_rpc(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            self.assertEqual(payload["target"], "xtdata")
            self.assertEqual(payload["method"], "get_full_tick")
            self.assertEqual(payload["args"], [["000001.SZ", "600000.SH"]])
            return httpx.Response(200, json={"ok": True, "data": {"000001.SZ": {"last": 1}}})

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        self.assertEqual(
            client.market.get_full_tick(("000001.SZ", "600000.SH")),
            {"000001.SZ": {"last": 1}},
        )

    def test_market_daily_bars_returns_typed_response(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/v1/market/bars/daily")
            self.assertEqual(request.url.params["symbols"], "000001.SZ")
            self.assertEqual(request.url.params["start"], "20260501")
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "data": {
                        "bars": [
                            {
                                "symbol": "000001.SZ",
                                "date": "2026-05-25",
                                "open": 10,
                                "high": 11,
                                "low": 9,
                                "close": 10.5,
                                "volume": 1000,
                                "amount": 10500,
                                "meta": {},
                            }
                        ]
                    },
                    "error": None,
                    "meta": {"schema": "market.bars.v1", "row_count": 1},
                },
            )

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        response = client.market.daily_bars(["000001.SZ"], start_time="20260501")

        self.assertEqual(response["schema_version"], "qmtclient.market.v1")
        self.assertEqual(response["meta"]["kind"], "daily_bars")
        self.assertEqual(response["data"][0]["code"], "000001.SZ")
        self.assertIsInstance(response["data"][0]["close"], float)

    def test_market_intraday_bars_rejects_empty_data(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/v1/market/bars/intraday")
            return httpx.Response(
                200,
                json={"ok": True, "data": {"bars": []}, "error": None, "meta": {}},
            )

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        with self.assertRaises(QmtDataEmptyError):
            client.market.intraday_bars(["000001.SZ"], period="1m")

    def test_market_instruments_rejects_schema_mismatch(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/v1/reference/instruments")
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "data": {"instruments": [{"name": "missing-code"}]},
                    "error": None,
                    "meta": {},
                },
            )

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        with self.assertRaises(QmtSchemaMismatchError):
            client.market.instruments(["000001.SZ"])

    def test_trader_readonly_helpers_call_stable_endpoints(self) -> None:
        seen_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_paths.append(request.url.path)
            if request.url.path == "/v1/trader/account-status":
                return _trader_response({"statuses": [{"account_id": "10001"}]})
            if request.url.path == "/v1/trader/asset":
                self.assertEqual(request.url.params["account_id"], "10001")
                self.assertEqual(request.url.params["account_type"], "CREDIT")
                return _trader_response({"asset": {"account_id": "10001"}})
            if request.url.path == "/v1/trader/positions":
                return _trader_response({"positions": [{"stock_code": "000001.SZ"}]})
            if request.url.path == "/v1/trader/orders":
                self.assertEqual(request.url.params["cancelable_only"], "true")
                return _trader_response({"orders": [{"order_id": "O10001"}]})
            if request.url.path == "/v1/trader/trades":
                return _trader_response({"trades": [{"trade_id": "T10001"}]})
            raise AssertionError(request.url.path)

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        self.assertEqual(client.trader_account_status(), [{"account_id": "10001"}])
        self.assertEqual(
            client.trader_asset("10001", account_type="CREDIT"), {"account_id": "10001"}
        )
        self.assertEqual(client.trader_positions("10001"), [{"stock_code": "000001.SZ"}])
        self.assertEqual(
            client.trader_orders("10001", cancelable_only=True), [{"order_id": "O10001"}]
        )
        self.assertEqual(client.trader_trades("10001"), [{"trade_id": "T10001"}])
        self.assertEqual(
            seen_paths,
            [
                "/v1/trader/account-status",
                "/v1/trader/asset",
                "/v1/trader/positions",
                "/v1/trader/orders",
                "/v1/trader/trades",
            ],
        )

    def test_trader_readonly_helpers_raise_rpc_error_for_api_error_envelope(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "ok": False,
                    "data": None,
                    "error": {"code": "TRADER_ACCOUNT_REQUIRED", "message": "account required"},
                    "meta": {"request_id": "readonly-request"},
                },
            )

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        with self.assertRaises(QmtRpcError) as raised:
            client.trader_asset()

        self.assertEqual(raised.exception.code, "TRADER_ACCOUNT_REQUIRED")
        self.assertEqual(raised.exception.message, "account required")
        self.assertEqual(raised.exception.target, "trader")
        self.assertEqual(raised.exception.method, "asset")
        self.assertEqual(raised.exception.request_id, "readonly-request")

    def test_account_facade_uses_stable_trader_readonly_endpoints(self) -> None:
        seen_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_paths.append(request.url.path)
            if request.url.path == "/v1/rpc":
                payload = json.loads(request.content)
                self.assertEqual(payload["target"], "trader")
                self.assertEqual(payload["method"], "query_account_infos")
                self.assertEqual(payload["args"], [])
                return httpx.Response(200, json={"ok": True, "data": [{"account_id": "10001"}]})
            if request.url.path == "/v1/trader/account-status":
                return _trader_response({"statuses": [{"account_id": "10001"}]})
            if request.url.path == "/v1/trader/asset":
                self.assertEqual(request.url.params["account_id"], "10001")
                self.assertEqual(request.url.params["account_type"], "STOCK")
                return _trader_response({"asset": {"account_id": "10001"}})
            if request.url.path == "/v1/trader/positions":
                return _trader_response({"positions": [{"stock_code": "000001.SZ"}]})
            if request.url.path == "/v1/trader/orders":
                self.assertEqual(request.url.params["cancelable_only"], "true")
                return _trader_response({"orders": [{"order_id": "O10001"}]})
            if request.url.path == "/v1/trader/trades":
                return _trader_response({"trades": [{"trade_id": "T10001"}]})
            raise AssertionError(request.url.path)

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        self.assertEqual(client.account.infos(), [{"account_id": "10001"}])
        self.assertEqual(client.account.status(), [{"account_id": "10001"}])
        self.assertEqual(client.account.asset("10001"), {"account_id": "10001"})
        self.assertEqual(client.account.positions("10001"), [{"stock_code": "000001.SZ"}])
        self.assertEqual(
            client.account.orders("10001", cancelable_only=True), [{"order_id": "O10001"}]
        )
        self.assertEqual(client.account.trades("10001"), [{"trade_id": "T10001"}])
        self.assertEqual(
            seen_paths,
            [
                "/v1/rpc",
                "/v1/trader/account-status",
                "/v1/trader/asset",
                "/v1/trader/positions",
                "/v1/trader/orders",
                "/v1/trader/trades",
            ],
        )

    def test_account_facade_exposes_cached_order_and_trade_helpers(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/orders":
                self.assertEqual(request.url.params["limit"], "2")
                return httpx.Response(200, json={"ok": True, "data": [{"order_id": "1"}]})
            if request.url.path == "/v1/trades":
                self.assertEqual(request.url.params["limit"], "3")
                return httpx.Response(200, json={"ok": True, "data": [{"trade_id": "2"}]})
            raise AssertionError(request.url.path)

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        self.assertEqual(client.account.cached_orders(limit=2), [{"order_id": "1"}])
        self.assertEqual(client.account.cached_trades(limit=3), [{"trade_id": "2"}])

    def test_trading_facade_only_builds_rpc_payload(self) -> None:
        requests: list[dict[str, object]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            requests.append(payload)
            return httpx.Response(200, json={"ok": True, "data": 123})

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        self.assertEqual(
            client.trading.order_stock("10001", "000001.SZ", 23, 100, 5, 10.5),
            123,
        )
        self.assertEqual(client.trading.cancel_order_stock("10001", "order-1"), 123)

        self.assertEqual(requests[0]["target"], "trader")
        self.assertEqual(requests[0]["method"], "order_stock")
        self.assertEqual(
            requests[0]["args"],
            [
                {"__type__": "StockAccount", "account_id": "10001", "account_type": "STOCK"},
                "000001.SZ",
                23,
                100,
                5,
                10.5,
            ],
        )
        self.assertEqual(requests[1]["method"], "cancel_order_stock")
        self.assertEqual(
            requests[1]["args"],
            [
                {"__type__": "StockAccount", "account_id": "10001", "account_type": "STOCK"},
                "order-1",
            ],
        )

    def test_trading_facade_preserves_server_rejection(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "ok": False,
                    "data": None,
                    "error": {"code": "TRADING_DISABLED", "message": "disabled"},
                    "meta": {"request_id": "trade-request"},
                },
            )

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        with self.assertRaises(QmtRpcError) as raised:
            client.trading.order_stock("10001", "000001.SZ", 23, 100, 5, 10.5)

        self.assertEqual(raised.exception.code, "TRADING_DISABLED")
        self.assertEqual(raised.exception.request_id, "trade-request")


if __name__ == "__main__":
    unittest.main()

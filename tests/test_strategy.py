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
            payload = json.loads(request.content)
            self.assertEqual(payload["target"], "xtdata")
            self.assertEqual(payload["method"], "get_market_data")
            self.assertEqual(payload["kwargs"]["period"], "1d")
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "data": [
                        {
                            "code": "000001.SZ",
                            "date": "2026-05-25",
                            "open": 10,
                            "high": 11,
                            "low": 9,
                            "close": 10.5,
                            "volume": 1000,
                            "amount": 10500,
                        }
                    ],
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
            return httpx.Response(200, json={"ok": True, "data": []})

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        with self.assertRaises(QmtDataEmptyError):
            client.market.intraday_bars(["000001.SZ"], period="1m")

    def test_market_instruments_rejects_schema_mismatch(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"ok": True, "data": [{"name": "missing-code"}]})

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        with self.assertRaises(QmtSchemaMismatchError):
            client.market.instruments(["000001.SZ"])

    def test_account_facade_uses_stock_account_payload(self) -> None:
        seen_methods: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            seen_methods.append(payload["method"])
            if payload["method"] == "query_account_infos":
                self.assertEqual(payload["args"], [])
                return httpx.Response(200, json={"ok": True, "data": [{"account_id": "10001"}]})
            self.assertEqual(payload["target"], "trader")
            self.assertEqual(
                payload["args"],
                [{"__type__": "StockAccount", "account_id": "10001", "account_type": "STOCK"}],
            )
            return httpx.Response(200, json={"ok": True, "data": {"method": payload["method"]}})

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        self.assertEqual(client.account.infos(), [{"account_id": "10001"}])
        self.assertEqual(client.account.asset("10001"), {"method": "query_stock_asset"})
        self.assertEqual(client.account.positions("10001"), {"method": "query_stock_positions"})
        self.assertEqual(client.account.orders("10001"), {"method": "query_stock_orders"})
        self.assertEqual(client.account.trades("10001"), {"method": "query_stock_trades"})
        self.assertEqual(
            seen_methods,
            [
                "query_account_infos",
                "query_stock_asset",
                "query_stock_positions",
                "query_stock_orders",
                "query_stock_trades",
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

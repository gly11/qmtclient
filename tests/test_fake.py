from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from qmtclient import EventReplay, FakeQmtClient, QmtRpcError, load_fixture, load_jsonl


class FakeClientTests(unittest.TestCase):
    def test_fake_client_supports_strategy_facades(self) -> None:
        client = FakeQmtClient(
            rpc_results={
                "xtdata.get_full_tick": {"000001.SZ": {"last": 10.5}},
                "trader.query_stock_asset": {"account_id": "example-account", "cash": 1000},
                "trader.order_stock": {"dry_run": True, "order_id": "fake-order"},
            },
            orders=[{"order_id": "fake-order", "stock_code": "000001.SZ"}],
            trades=[{"trade_id": "fake-trade", "stock_code": "000001.SZ"}],
        )

        self.assertEqual(client.market.get_full_tick(["000001.SZ"])["000001.SZ"]["last"], 10.5)
        self.assertEqual(client.account.asset("example-account")["cash"], 1000)
        self.assertEqual(
            client.trading.order_stock("example-account", "000001.SZ", 23, 100, 5, 10.5),
            {"dry_run": True, "order_id": "fake-order"},
        )
        self.assertEqual(client.account.cached_orders(limit=1)[0]["order_id"], "fake-order")
        self.assertEqual(client.account.cached_trades(limit=1)[0]["trade_id"], "fake-trade")

    def test_fake_client_missing_rpc_result_raises_rpc_error(self) -> None:
        client = FakeQmtClient()

        with self.assertRaises(QmtRpcError) as raised:
            client.market.get_full_tick(["000001.SZ"])

        self.assertEqual(raised.exception.code, "METHOD_NOT_ALLOWED")
        self.assertEqual(raised.exception.target, "xtdata")
        self.assertEqual(raised.exception.method, "get_full_tick")

    def test_fake_client_loads_fixture_file(self) -> None:
        fixture = {
            "health": {"ok": True, "api_versions": ["v1"]},
            "status": {"ok": True, "service": "fake"},
            "rpc": {
                "xtdata.get_full_tick": {"000001.SZ": {"last": 10.5}},
                "trader.query_stock_positions": [{"stock_code": "000001.SZ", "volume": 100}],
            },
            "orders": [{"order_id": "order-1"}],
            "trades": [{"trade_id": "trade-1"}],
            "events": [{"type": "stock_order", "data": {"order_id": "order-1"}}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fixture.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")

            client = FakeQmtClient.from_fixture(path)
            loaded = load_fixture(path)

        self.assertEqual(loaded["status"]["service"], "fake")
        self.assertEqual(client.status()["service"], "fake")
        self.assertEqual(client.market.get_full_tick(["000001.SZ"])["000001.SZ"]["last"], 10.5)
        self.assertEqual(client.account.positions("example-account")[0]["volume"], 100)
        self.assertEqual(client.orders()[0]["order_id"], "order-1")
        self.assertEqual(next(iter(client.events()))["type"], "stock_order")

    def test_load_jsonl_and_event_replay_filter_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "heartbeat", "data": {}}),
                        json.dumps({"type": "stock_order", "data": {"order_id": "1"}}),
                        json.dumps({"type": "stock_trade", "data": {"trade_id": "2"}}),
                    ]
                ),
                encoding="utf-8",
            )

            events = load_jsonl(path)

        replayed = list(EventReplay(events, types=["stock_trade"]))

        self.assertEqual([event["type"] for event in replayed], ["heartbeat", "stock_trade"])
        replayed[1]["data"]["trade_id"] = "changed"
        self.assertEqual(events[2]["data"]["trade_id"], "2")

    def test_recent_events_filters_and_limits(self) -> None:
        client = FakeQmtClient(
            events=[
                {"type": "heartbeat", "data": {}},
                {"type": "stock_order", "data": {"order_id": "1"}},
                {"type": "stock_trade", "data": {"trade_id": "2"}},
            ]
        )

        self.assertEqual(
            [event["type"] for event in client.recent_events(types=["stock_trade"], limit=2)],
            ["heartbeat", "stock_trade"],
        )

    def test_fake_client_loads_standard_market_fixture(self) -> None:
        fixture = {
            "market": {
                "daily_bars": [
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
                "intraday_bars": [
                    {
                        "code": "000001.SZ",
                        "datetime": "2026-05-25 09:31:00",
                        "open": 10,
                        "high": 10.1,
                        "low": 9.9,
                        "close": 10.05,
                        "volume": 100,
                        "amount": 1005,
                    }
                ],
                "instruments": [{"code": "000001.SZ", "name": "Example Bank", "exchange": "SZ"}],
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "market.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")

            client = FakeQmtClient.from_fixture(path)

        self.assertEqual(client.market.daily_bars(["000001.SZ"])["data"][0]["code"], "000001.SZ")
        self.assertEqual(client.market.instruments(["000001.SZ"])["data"][0]["exchange"], "SZ")


if __name__ == "__main__":
    unittest.main()

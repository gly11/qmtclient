from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from qmtclient.errors import QmtRpcError
from qmtclient.fixtures import EventReplay, load_fixture
from qmtclient.proxy import RpcTargetProxy
from qmtclient.strategy import AccountFacade, MarketFacade, TradingFacade


class FakeQmtClient:
    def __init__(
        self,
        *,
        health: dict[str, Any] | None = None,
        status: dict[str, Any] | None = None,
        methods: dict[str, Any] | None = None,
        rpc_results: dict[str, Any] | None = None,
        market: dict[str, Any] | None = None,
        orders: list[dict[str, Any]] | None = None,
        trades: list[dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
    ) -> None:
        self._health = health or {"ok": True, "api_versions": ["v1"]}
        self._status = status or {"ok": True}
        self._rpc_results = rpc_results or {}
        self._market = market or {}
        self._methods = methods or {"methods": _methods_from_rpc_results(self._rpc_results)}
        self._orders = orders or []
        self._trades = trades or []
        self._events = events or []
        self.xtdata = RpcTargetProxy(self, "xtdata")
        self.trader = RpcTargetProxy(self, "trader")
        self.market = MarketFacade(self)
        self.account = AccountFacade(self)
        self.trading = TradingFacade(self)

    @classmethod
    def from_fixture(cls, path: str | Path) -> FakeQmtClient:
        fixture = load_fixture(path)
        return cls(
            health=_dict_or_none(fixture.get("health")),
            status=_dict_or_none(fixture.get("status")),
            methods=_dict_or_none(fixture.get("methods")),
            rpc_results=_dict_or_none(fixture.get("rpc")),
            market=_dict_or_none(fixture.get("market")),
            orders=_dict_list_or_none(fixture.get("orders")),
            trades=_dict_list_or_none(fixture.get("trades")),
            events=_dict_list_or_none(fixture.get("events")),
        )

    def close(self) -> None:
        return None

    def __enter__(self) -> FakeQmtClient:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        return deepcopy(self._health)

    def version(self) -> dict[str, Any]:
        return self.health()

    def status(self) -> dict[str, Any]:
        return deepcopy(self._status)

    def methods(self) -> dict[str, Any]:
        return deepcopy(self._methods)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if method == "GET" and path == "/market/capabilities":
            return {
                "ok": True,
                "data": {
                    "schema_versions": ["market.bars.v1"],
                    "periods": ["1m", "5m", "1d"],
                    "adjust_modes": ["none"],
                },
                "error": None,
                "meta": {},
            }
        if method == "GET" and path == "/market/bars/daily":
            return _market_response(self._market.get("daily_bars"))
        if method == "GET" and path == "/market/bars/intraday":
            return _market_response(self._market.get("intraday_bars"))
        if method == "GET" and path == "/reference/instruments":
            return {
                "ok": True,
                "data": {"instruments": deepcopy(self._market.get("instruments", []))},
                "error": None,
                "meta": {"schema": "reference.instruments.v1"},
            }
        if method == "GET" and path == "/market/bars/daily/quality":
            return {
                "ok": True,
                "data": {
                    "missing_dates": [],
                    "duplicate_rows": [],
                    "price_anomalies": [],
                    "volume_anomalies": [],
                },
                "error": None,
                "meta": {"schema": "market.quality.v1"},
            }
        raise QmtRpcError(
            code="METHOD_NOT_ALLOWED",
            message=f"Fake request result is not configured: {method} {path}",
            target="api",
            method=path,
            response={
                "ok": False,
                "data": None,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": f"Fake request result is not configured: {method} {path}",
                },
            },
        )

    def rpc(
        self,
        target: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        key = f"{target}.{method}"
        market_result = self._market_rpc_result(target, method, kwargs or {})
        if market_result is not None:
            return deepcopy(market_result)
        if key not in self._rpc_results:
            raise QmtRpcError(
                code="METHOD_NOT_ALLOWED",
                message=f"Fake RPC result is not configured: {key}",
                target=target,
                method=method,
                response={
                    "ok": False,
                    "data": None,
                    "error": {
                        "code": "METHOD_NOT_ALLOWED",
                        "message": f"Fake RPC result is not configured: {key}",
                    },
                },
            )
        return deepcopy(self._rpc_results[key])

    def _market_rpc_result(
        self,
        target: str,
        method: str,
        kwargs: dict[str, Any],
    ) -> Any:
        if target != "xtdata":
            return None
        if method == "get_market_data":
            period = kwargs.get("period")
            key = "daily_bars" if period == "1d" else "intraday_bars"
            return self._market.get(key)
        if method == "get_instruments":
            return self._market.get("instruments")
        return None

    def orders(self, limit: int | None = None) -> list[dict[str, Any]]:
        return _limited(self._orders, limit)

    def order(self, order_id: str) -> dict[str, Any]:
        for order in self._orders:
            if str(order.get("order_id")) == str(order_id):
                return deepcopy(order)
        return {}

    def trades(self, limit: int | None = None) -> list[dict[str, Any]]:
        return _limited(self._trades, limit)

    def recent_events(
        self,
        *,
        types: list[str] | tuple[str, ...] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        events = list(EventReplay(self._events, types=types))
        return _limited(events, limit)

    def events(self, *, types: list[str] | tuple[str, ...] | None = None) -> EventReplay:
        return EventReplay(self._events, types=types)


def _methods_from_rpc_results(rpc_results: dict[str, Any]) -> dict[str, list[str]]:
    methods: dict[str, list[str]] = {}
    for key in rpc_results:
        target, _, method = key.partition(".")
        if target and method:
            methods.setdefault(target, []).append(method)
    return {target: sorted(items) for target, items in sorted(methods.items())}


def _limited(items: list[dict[str, Any]], limit: int | None) -> list[dict[str, Any]]:
    selected = items if limit is None else items[:limit]
    return deepcopy(selected)


def _market_response(rows: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "data": {"bars": deepcopy(rows or [])},
        "error": None,
        "meta": {"schema": "market.bars.v1"},
    }


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _dict_list_or_none(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    return [item for item in value if isinstance(item, dict)]

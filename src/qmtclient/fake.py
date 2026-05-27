from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from qmtclient.errors import QmtRpcError
from qmtclient.fixtures import EventReplay, load_fixture
from qmtclient.proxy import RpcTargetProxy
from qmtclient.strategy import AccountFacade, MarketFacade, TradingFacade, stock_account


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
        self._subscriptions = _dict_list(self._market.get("subscriptions", []))
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
        if method == "POST" and path == "/market/subscriptions":
            payload = kwargs.get("json")
            if not isinstance(payload, dict):
                payload = {}
            symbols = payload.get("symbols")
            if not isinstance(symbols, list):
                symbols = []
            period = payload.get("period", "tick")
            subscription = _subscription(
                "sub_fake",
                symbols=[str(item) for item in symbols],
                period=str(period),
                status="active",
            )
            self._subscriptions = [
                item
                for item in self._subscriptions
                if item.get("subscription_id") != subscription["subscription_id"]
            ]
            self._subscriptions.append(subscription)
            return _api_response(subscription, schema="market.subscription.v1")
        if method == "GET" and path == "/market/subscriptions":
            return _api_response(
                {"subscriptions": deepcopy(self._subscriptions)},
                schema="market.subscription.v1",
            )
        if path.startswith("/market/subscriptions/"):
            subscription_id = path.rsplit("/", 1)[-1]
            if method == "GET":
                return _api_response(
                    _find_subscription(self._subscriptions, subscription_id),
                    schema="market.subscription.v1",
                )
            if method == "DELETE":
                subscription = _update_subscription_status(
                    self._subscriptions,
                    subscription_id,
                    "stopped",
                )
                return _api_response(subscription, schema="market.subscription.v1")
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

    def trader_account_status(self) -> list[dict[str, Any]]:
        data = self.rpc("trader", "query_account_status")
        return _dict_list(data)

    def trader_asset(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
    ) -> dict[str, Any]:
        data = self.rpc(
            "trader",
            "query_stock_asset",
            [_stock_account_arg(account_id, account_type)],
        )
        return data if isinstance(data, dict) else {}

    def trader_positions(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
    ) -> list[dict[str, Any]]:
        data = self.rpc(
            "trader",
            "query_stock_positions",
            [_stock_account_arg(account_id, account_type)],
        )
        return _dict_list(data)

    def trader_orders(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
        cancelable_only: bool = False,
    ) -> list[dict[str, Any]]:
        data = self.rpc(
            "trader",
            "query_stock_orders",
            [_stock_account_arg(account_id, account_type), cancelable_only],
        )
        return _dict_list(data)

    def trader_trades(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
    ) -> list[dict[str, Any]]:
        data = self.rpc(
            "trader",
            "query_stock_trades",
            [_stock_account_arg(account_id, account_type)],
        )
        return _dict_list(data)

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


def _stock_account_arg(account_id: str | None, account_type: str | None) -> dict[str, str]:
    return stock_account(account_id or "", account_type or "STOCK")


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return deepcopy([item for item in value if isinstance(item, dict)])


def _market_response(rows: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "data": {"bars": deepcopy(rows or [])},
        "error": None,
        "meta": {"schema": "market.bars.v1"},
    }


def _api_response(data: dict[str, Any], *, schema: str) -> dict[str, Any]:
    return {"ok": True, "data": deepcopy(data), "error": None, "meta": {"schema": schema}}


def _subscription(
    subscription_id: str,
    *,
    symbols: list[str],
    period: str,
    status: str,
) -> dict[str, Any]:
    return {
        "schema": "market.subscription.v1",
        "subscription_id": subscription_id,
        "symbols": symbols,
        "period": period,
        "status": status,
        "created_at": "2026-05-27T09:30:00+00:00",
        "updated_at": "2026-05-27T09:30:00+00:00",
        "upstream_id": [1],
        "last_error": None,
    }


def _find_subscription(
    subscriptions: list[dict[str, Any]],
    subscription_id: str,
) -> dict[str, Any]:
    for subscription in subscriptions:
        if str(subscription.get("subscription_id")) == subscription_id:
            return deepcopy(subscription)
    raise QmtRpcError(
        code="MARKET_SUBSCRIPTION_NOT_FOUND",
        message=f"Market subscription not found: {subscription_id}",
        target="market",
        method="subscription",
        response={
            "ok": False,
            "data": None,
            "error": {
                "code": "MARKET_SUBSCRIPTION_NOT_FOUND",
                "message": f"Market subscription not found: {subscription_id}",
            },
        },
    )


def _update_subscription_status(
    subscriptions: list[dict[str, Any]],
    subscription_id: str,
    status: str,
) -> dict[str, Any]:
    for index, subscription in enumerate(subscriptions):
        if str(subscription.get("subscription_id")) == subscription_id:
            updated = deepcopy(subscription)
            updated["status"] = status
            subscriptions[index] = updated
            return updated
    return _find_subscription(subscriptions, subscription_id)


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _dict_list_or_none(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    return [item for item in value if isinstance(item, dict)]

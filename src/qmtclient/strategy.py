from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class StrategyClient(Protocol):
    def rpc(
        self,
        target: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any: ...

    def orders(self, limit: int | None = None) -> list[dict[str, Any]]: ...

    def trades(self, limit: int | None = None) -> list[dict[str, Any]]: ...


def stock_account(account_id: str, account_type: str = "STOCK") -> dict[str, str]:
    return {
        "__type__": "StockAccount",
        "account_id": account_id,
        "account_type": account_type,
    }


class MarketFacade:
    def __init__(self, client: StrategyClient) -> None:
        self._client = client

    def get_full_tick(self, codes: Sequence[str]) -> dict[str, Any]:
        data = self._client.rpc("xtdata", "get_full_tick", [list(codes)])
        return data if isinstance(data, dict) else {}

    def rpc(
        self,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        return self._client.rpc("xtdata", method, args, kwargs)


class AccountFacade:
    def __init__(self, client: StrategyClient) -> None:
        self._client = client

    def infos(self) -> Any:
        return self._client.rpc("trader", "query_account_infos")

    def status(self) -> Any:
        return self._client.rpc("trader", "query_account_status")

    def asset(self, account_id: str, account_type: str = "STOCK") -> Any:
        return self._client.rpc(
            "trader",
            "query_stock_asset",
            [stock_account(account_id, account_type)],
        )

    def positions(self, account_id: str, account_type: str = "STOCK") -> Any:
        return self._client.rpc(
            "trader",
            "query_stock_positions",
            [stock_account(account_id, account_type)],
        )

    def orders(self, account_id: str, account_type: str = "STOCK") -> Any:
        return self._client.rpc(
            "trader",
            "query_stock_orders",
            [stock_account(account_id, account_type)],
        )

    def trades(self, account_id: str, account_type: str = "STOCK") -> Any:
        return self._client.rpc(
            "trader",
            "query_stock_trades",
            [stock_account(account_id, account_type)],
        )

    def cached_orders(self, limit: int | None = None) -> list[dict[str, Any]]:
        return self._client.orders(limit=limit)

    def cached_trades(self, limit: int | None = None) -> list[dict[str, Any]]:
        return self._client.trades(limit=limit)

    def rpc(
        self,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        return self._client.rpc("trader", method, args, kwargs)


class TradingFacade:
    def __init__(self, client: StrategyClient) -> None:
        self._client = client

    def order_stock(
        self,
        account_id: str,
        stock_code: str,
        order_type: int,
        volume: int,
        price_type: int,
        price: float,
        *,
        account_type: str = "STOCK",
    ) -> Any:
        return self._order_stock(
            "order_stock",
            account_id,
            stock_code,
            order_type,
            volume,
            price_type,
            price,
            account_type=account_type,
        )

    def order_stock_async(
        self,
        account_id: str,
        stock_code: str,
        order_type: int,
        volume: int,
        price_type: int,
        price: float,
        *,
        account_type: str = "STOCK",
    ) -> Any:
        return self._order_stock(
            "order_stock_async",
            account_id,
            stock_code,
            order_type,
            volume,
            price_type,
            price,
            account_type=account_type,
        )

    def cancel_order_stock(
        self,
        account_id: str,
        order_id: int | str,
        *,
        account_type: str = "STOCK",
    ) -> Any:
        return self._cancel_order_stock(
            "cancel_order_stock",
            account_id,
            order_id,
            account_type=account_type,
        )

    def cancel_order_stock_async(
        self,
        account_id: str,
        order_id: int | str,
        *,
        account_type: str = "STOCK",
    ) -> Any:
        return self._cancel_order_stock(
            "cancel_order_stock_async",
            account_id,
            order_id,
            account_type=account_type,
        )

    def _order_stock(
        self,
        method: str,
        account_id: str,
        stock_code: str,
        order_type: int,
        volume: int,
        price_type: int,
        price: float,
        *,
        account_type: str,
    ) -> Any:
        return self._client.rpc(
            "trader",
            method,
            [
                stock_account(account_id, account_type),
                stock_code,
                order_type,
                volume,
                price_type,
                price,
            ],
        )

    def _cancel_order_stock(
        self,
        method: str,
        account_id: str,
        order_id: int | str,
        *,
        account_type: str,
    ) -> Any:
        return self._client.rpc(
            "trader",
            method,
            [stock_account(account_id, account_type), order_id],
        )

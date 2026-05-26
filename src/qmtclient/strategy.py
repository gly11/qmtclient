from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from qmtclient.models import MarketResponse, normalize_bars, normalize_instruments


class StrategyClient(Protocol):
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]: ...

    def rpc(
        self,
        target: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any: ...

    def orders(self, limit: int | None = None) -> list[dict[str, Any]]: ...

    def trades(self, limit: int | None = None) -> list[dict[str, Any]]: ...

    def trader_account_status(self) -> list[dict[str, Any]]: ...

    def trader_asset(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
    ) -> dict[str, Any]: ...

    def trader_positions(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
    ) -> list[dict[str, Any]]: ...

    def trader_orders(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
        cancelable_only: bool = False,
    ) -> list[dict[str, Any]]: ...

    def trader_trades(
        self,
        account_id: str | None = None,
        *,
        account_type: str | None = None,
    ) -> list[dict[str, Any]]: ...


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

    def capabilities(self) -> dict[str, Any]:
        response = self._client._request("GET", "/market/capabilities")
        return _response_data(response)

    def daily_bars(
        self,
        codes: Sequence[str],
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        count: int | None = None,
        dividend_type: str | None = None,
    ) -> MarketResponse:
        if count is None:
            response = self._client._request(
                "GET",
                "/market/bars/daily",
                params=_stable_market_params(codes, start_time, end_time, dividend_type),
            )
            _raise_api_error(response, "market", "daily_bars")
            return normalize_bars(response, kind="daily_bars", codes=codes, period="1d")

        period = "1d"
        data = self._client.rpc(
            "xtdata",
            "get_market_data",
            kwargs=_market_kwargs(codes, period, start_time, end_time, count, dividend_type),
        )
        return normalize_bars(data, kind="daily_bars", codes=codes, period=period)

    def intraday_bars(
        self,
        codes: Sequence[str],
        *,
        period: str = "1m",
        start_time: str | None = None,
        end_time: str | None = None,
        count: int | None = None,
        dividend_type: str | None = None,
    ) -> MarketResponse:
        if count is None:
            params = _stable_market_params(codes, start_time, end_time, dividend_type)
            params["period"] = period
            response = self._client._request("GET", "/market/bars/intraday", params=params)
            _raise_api_error(response, "market", "intraday_bars")
            return normalize_bars(response, kind="intraday_bars", codes=codes, period=period)

        data = self._client.rpc(
            "xtdata",
            "get_market_data",
            kwargs=_market_kwargs(codes, period, start_time, end_time, count, dividend_type),
        )
        return normalize_bars(data, kind="intraday_bars", codes=codes, period=period)

    def instruments(self, codes: Sequence[str]) -> MarketResponse:
        response = self._client._request(
            "GET",
            "/reference/instruments",
            params={"symbols": ",".join(codes)},
        )
        _raise_api_error(response, "reference", "instruments")
        return normalize_instruments(response, codes=codes)

    def daily_quality(
        self,
        codes: Sequence[str],
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        dividend_type: str | None = None,
    ) -> dict[str, Any]:
        response = self._client._request(
            "GET",
            "/market/bars/daily/quality",
            params=_stable_market_params(codes, start_time, end_time, dividend_type),
        )
        _raise_api_error(response, "market", "daily_quality")
        return response

    def rpc(
        self,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        return self._client.rpc("xtdata", method, args, kwargs)


def _market_kwargs(
    codes: Sequence[str],
    period: str,
    start_time: str | None,
    end_time: str | None,
    count: int | None,
    dividend_type: str | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"codes": list(codes), "period": period}
    if start_time is not None:
        kwargs["start_time"] = start_time
    if end_time is not None:
        kwargs["end_time"] = end_time
    if count is not None:
        kwargs["count"] = count
    if dividend_type is not None:
        kwargs["dividend_type"] = dividend_type
    return kwargs


def _stable_market_params(
    codes: Sequence[str],
    start_time: str | None,
    end_time: str | None,
    dividend_type: str | None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"symbols": ",".join(codes)}
    if start_time is not None:
        params["start"] = start_time
    if end_time is not None:
        params["end"] = end_time
    if dividend_type is not None:
        params["adjust"] = dividend_type
    return params


def _response_data(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    return data if isinstance(data, dict) else {}


def _raise_api_error(response: dict[str, Any], target: str, method: str) -> None:
    if response.get("ok", True):
        return
    error_value = response.get("error")
    error = error_value if isinstance(error_value, dict) else {}
    from qmtclient.errors import QmtRpcError

    raise QmtRpcError(
        code=str(error.get("code", "API_ERROR")),
        message=str(error.get("message", "qmtserver API call failed")),
        target=target,
        method=method,
        response=response,
    )


class AccountFacade:
    def __init__(self, client: StrategyClient) -> None:
        self._client = client

    def infos(self) -> Any:
        return self._client.rpc("trader", "query_account_infos")

    def status(self) -> list[dict[str, Any]]:
        return self._client.trader_account_status()

    def asset(
        self,
        account_id: str | None = None,
        account_type: str | None = "STOCK",
    ) -> dict[str, Any]:
        return self._client.trader_asset(account_id, account_type=account_type)

    def positions(
        self,
        account_id: str | None = None,
        account_type: str | None = "STOCK",
    ) -> list[dict[str, Any]]:
        return self._client.trader_positions(account_id, account_type=account_type)

    def orders(
        self,
        account_id: str | None = None,
        account_type: str | None = "STOCK",
        *,
        cancelable_only: bool = False,
    ) -> list[dict[str, Any]]:
        return self._client.trader_orders(
            account_id,
            account_type=account_type,
            cancelable_only=cancelable_only,
        )

    def trades(
        self,
        account_id: str | None = None,
        account_type: str | None = "STOCK",
    ) -> list[dict[str, Any]]:
        return self._client.trader_trades(account_id, account_type=account_type)

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

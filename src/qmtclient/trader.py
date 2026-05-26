from __future__ import annotations

from typing import Any, Protocol

from qmtclient.errors import QmtRpcError


class TraderRequestClient(Protocol):
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]: ...


def trader_account_status(client: TraderRequestClient) -> list[dict[str, Any]]:
    response = client._request("GET", "/trader/account-status")
    _raise_api_error(response, "account_status")
    return _response_named_list(response, "statuses")


def trader_asset(
    client: TraderRequestClient,
    account_id: str | None = None,
    *,
    account_type: str | None = None,
) -> dict[str, Any]:
    response = client._request(
        "GET",
        "/trader/asset",
        params=_account_params(account_id, account_type),
    )
    _raise_api_error(response, "asset")
    return _response_named_dict(response, "asset")


def trader_positions(
    client: TraderRequestClient,
    account_id: str | None = None,
    *,
    account_type: str | None = None,
) -> list[dict[str, Any]]:
    response = client._request(
        "GET",
        "/trader/positions",
        params=_account_params(account_id, account_type),
    )
    _raise_api_error(response, "positions")
    return _response_named_list(response, "positions")


def trader_orders(
    client: TraderRequestClient,
    account_id: str | None = None,
    *,
    account_type: str | None = None,
    cancelable_only: bool = False,
) -> list[dict[str, Any]]:
    params = _account_params(account_id, account_type) or {}
    if cancelable_only:
        params["cancelable_only"] = "true"
    response = client._request("GET", "/trader/orders", params=params or None)
    _raise_api_error(response, "orders")
    return _response_named_list(response, "orders")


def trader_trades(
    client: TraderRequestClient,
    account_id: str | None = None,
    *,
    account_type: str | None = None,
) -> list[dict[str, Any]]:
    response = client._request(
        "GET",
        "/trader/trades",
        params=_account_params(account_id, account_type),
    )
    _raise_api_error(response, "trades")
    return _response_named_list(response, "trades")


def _response_named_dict(response: dict[str, Any], key: str) -> dict[str, Any]:
    data = response.get("data")
    if not isinstance(data, dict):
        return {}
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _response_named_list(response: dict[str, Any], key: str) -> list[dict[str, Any]]:
    data = response.get("data")
    if not isinstance(data, dict):
        return []
    value = data.get(key)
    return value if isinstance(value, list) else []


def _raise_api_error(response: dict[str, Any], method: str) -> None:
    if response.get("ok", True):
        return
    error_value = response.get("error")
    error = error_value if isinstance(error_value, dict) else {}
    raise QmtRpcError(
        code=str(error.get("code", "API_ERROR")),
        message=str(error.get("message", "qmtserver API call failed")),
        target="trader",
        method=method,
        response=response,
        request_id=_request_id(response),
    )


def _account_params(
    account_id: str | None,
    account_type: str | None,
) -> dict[str, str] | None:
    params: dict[str, str] = {}
    if account_id is not None:
        params["account_id"] = account_id
    if account_type is not None:
        params["account_type"] = account_type
    return params or None


def _request_id(response: dict[str, Any]) -> str | None:
    meta = response.get("meta")
    if isinstance(meta, dict):
        request_id = meta.get("request_id")
        return str(request_id) if request_id is not None else None
    return None

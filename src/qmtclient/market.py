from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from qmtclient.errors import QmtRpcError


class MarketRequestClient(Protocol):
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]: ...


def create_subscription(
    client: MarketRequestClient,
    symbols: Sequence[str],
    *,
    period: str = "tick",
) -> dict[str, Any]:
    response = client._request(
        "POST",
        "/market/subscriptions",
        json={"symbols": list(symbols), "period": period},
    )
    _raise_api_error(response, "create_subscription")
    return _response_data_dict(response)


def subscriptions(client: MarketRequestClient) -> list[dict[str, Any]]:
    response = client._request("GET", "/market/subscriptions")
    _raise_api_error(response, "subscriptions")
    data = response.get("data")
    if not isinstance(data, dict):
        return []
    value = data.get("subscriptions")
    return value if isinstance(value, list) else []


def subscription(client: MarketRequestClient, subscription_id: str) -> dict[str, Any]:
    response = client._request("GET", f"/market/subscriptions/{subscription_id}")
    _raise_api_error(response, "subscription")
    return _response_data_dict(response)


def stop_subscription(client: MarketRequestClient, subscription_id: str) -> dict[str, Any]:
    response = client._request("DELETE", f"/market/subscriptions/{subscription_id}")
    _raise_api_error(response, "stop_subscription")
    return _response_data_dict(response)


def _response_data_dict(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    return data if isinstance(data, dict) else {}


def _raise_api_error(response: dict[str, Any], method: str) -> None:
    if response.get("ok", True):
        return
    error_value = response.get("error")
    error = error_value if isinstance(error_value, dict) else {}
    raise QmtRpcError(
        code=str(error.get("code", "API_ERROR")),
        message=str(error.get("message", "qmtserver API call failed")),
        target="market",
        method=method,
        response=response,
        request_id=_request_id(response),
    )


def _request_id(response: dict[str, Any]) -> str | None:
    meta = response.get("meta")
    if isinstance(meta, dict):
        request_id = meta.get("request_id")
        return str(request_id) if request_id is not None else None
    return None

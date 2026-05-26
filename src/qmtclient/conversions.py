from __future__ import annotations

from importlib import import_module
from typing import Any

from qmtclient.errors import QmtOptionalDependencyError


def market_to_dataframe(response: dict[str, Any]) -> Any:
    try:
        pd = import_module("pandas")
    except ImportError as exc:
        raise QmtOptionalDependencyError("pandas", "market_to_dataframe") from exc
    return pd.DataFrame(_response_data(response))


def market_to_arrow(response: dict[str, Any]) -> Any:
    try:
        pa = import_module("pyarrow")
    except ImportError as exc:
        raise QmtOptionalDependencyError("pyarrow", "market_to_arrow") from exc
    return pa.Table.from_pylist(_response_data(response))


def _response_data(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data", [])
    return data if isinstance(data, list) else []

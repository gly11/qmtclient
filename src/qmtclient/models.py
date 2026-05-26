from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal, TypedDict

from qmtclient.errors import QmtDataEmptyError, QmtSchemaMismatchError

MARKET_SCHEMA_VERSION = "qmtclient.market.v1"
DIAGNOSE_SCHEMA_VERSION = "qmtclient.diagnose.v1"


class MarketBar(TypedDict, total=False):
    code: str
    date: str
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


class Instrument(TypedDict, total=False):
    code: str
    name: str
    exchange: str
    instrument_type: str
    status: str


class MarketResponse(TypedDict):
    schema_version: str
    data: list[dict[str, Any]]
    meta: dict[str, Any]


class DiagnoseCheck(TypedDict, total=False):
    name: str
    ok: bool
    data: dict[str, Any]
    error: dict[str, Any]


class DiagnoseResponse(TypedDict):
    schema_version: str
    ok: bool
    checks: list[DiagnoseCheck]
    meta: dict[str, Any]


BarKind = Literal["daily_bars", "intraday_bars"]


def market_response(kind: str, data: list[dict[str, Any]], meta: dict[str, Any]) -> MarketResponse:
    merged_meta = {"kind": kind, **meta}
    return {"schema_version": MARKET_SCHEMA_VERSION, "data": data, "meta": merged_meta}


def normalize_bars(
    raw: Any,
    *,
    kind: BarKind,
    codes: Iterable[str],
    period: str,
) -> MarketResponse:
    source_meta = (
        raw.get("meta") if isinstance(raw, dict) and isinstance(raw.get("meta"), dict) else {}
    )
    rows = [_normalize_bar(item, kind=kind) for item in _iter_market_rows(raw, codes)]
    if not rows:
        raise QmtDataEmptyError(
            "qmtserver returned no market bars",
            schema_version=MARKET_SCHEMA_VERSION,
        )
    return market_response(
        kind,
        rows,
        {"codes": list(codes), "period": period, "source_meta": source_meta},
    )


def normalize_instruments(raw: Any, *, codes: Iterable[str]) -> MarketResponse:
    rows = [_normalize_instrument(item) for item in _iter_market_rows(raw, codes)]
    if not rows:
        raise QmtDataEmptyError(
            "qmtserver returned no instruments",
            schema_version=MARKET_SCHEMA_VERSION,
        )
    return market_response("instruments", rows, {"codes": list(codes)})


def _iter_market_rows(raw: Any, codes: Iterable[str]) -> list[dict[str, Any]]:
    data = raw.get("data") if isinstance(raw, dict) and "data" in raw else raw
    if isinstance(data, dict) and isinstance(data.get("bars"), list):
        return [item for item in data["bars"] if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("instruments"), list):
        return [item for item in data["instruments"] if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        rows: list[dict[str, Any]] = []
        for code, value in data.items():
            if isinstance(value, list):
                rows.extend(_with_code(item, str(code)) for item in value if isinstance(item, dict))
            elif isinstance(value, dict):
                rows.append(_with_code(value, str(code)))
        return rows
    if data is None and not list(codes):
        return []
    raise QmtSchemaMismatchError(
        "market response must be a list or code-keyed object",
        schema_version=MARKET_SCHEMA_VERSION,
    )


def _with_code(item: dict[str, Any], code: str) -> dict[str, Any]:
    return {"code": code, **item} if "code" not in item else dict(item)


def _normalize_bar(item: dict[str, Any], *, kind: BarKind) -> dict[str, Any]:
    required_time = "date" if kind == "daily_bars" else "datetime"
    time_value = item.get(required_time)
    if kind == "intraday_bars" and time_value is None:
        time_value = item.get("timestamp")
    code_value = item.get("code", item.get("symbol"))
    if code_value is None or time_value is None:
        raise QmtSchemaMismatchError(
            f"market bar requires code and {required_time}",
            schema_version=MARKET_SCHEMA_VERSION,
        )
    return {
        "code": str(code_value),
        required_time: str(time_value),
        "open": _number(item, "open"),
        "high": _number(item, "high"),
        "low": _number(item, "low"),
        "close": _number(item, "close"),
        "volume": _number(item, "volume"),
        "amount": _number(item, "amount"),
    }


def _normalize_instrument(item: dict[str, Any]) -> dict[str, Any]:
    code_value = item.get("code", item.get("symbol"))
    if code_value is None:
        raise QmtSchemaMismatchError(
            "instrument requires code",
            schema_version=MARKET_SCHEMA_VERSION,
        )
    return {
        "code": str(code_value),
        "name": str(item.get("name", "")),
        "exchange": str(item.get("exchange", "")),
        "instrument_type": str(item.get("instrument_type", item.get("type", ""))),
        "status": str(item.get("status", "")),
    }


def _number(item: dict[str, Any], key: str) -> float:
    value = item.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    raise QmtSchemaMismatchError(
        f"market bar field must be numeric: {key}",
        schema_version=MARKET_SCHEMA_VERSION,
    )

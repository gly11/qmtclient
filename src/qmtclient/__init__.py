from __future__ import annotations

from qmtclient.cache import MemoryCache
from qmtclient.client import QmtClient
from qmtclient.conversions import market_to_arrow, market_to_dataframe
from qmtclient.errors import (
    QmtAuthError,
    QmtClientError,
    QmtConnectionError,
    QmtDataEmptyError,
    QmtHttpError,
    QmtOptionalDependencyError,
    QmtProtocolError,
    QmtRpcError,
    QmtSchemaMismatchError,
    QmtServerUnavailableError,
)
from qmtclient.fake import FakeQmtClient
from qmtclient.fixtures import EventReplay, load_fixture, load_json, load_jsonl
from qmtclient.models import DIAGNOSE_SCHEMA_VERSION, MARKET_SCHEMA_VERSION
from qmtclient.snapshots import SnapshotClient, load_snapshot_manifest
from qmtclient.strategy import AccountFacade, MarketFacade, TradingFacade, stock_account

__version__ = "0.3.0"

__all__ = [
    "DIAGNOSE_SCHEMA_VERSION",
    "MARKET_SCHEMA_VERSION",
    "AccountFacade",
    "EventReplay",
    "FakeQmtClient",
    "MarketFacade",
    "MemoryCache",
    "QmtAuthError",
    "QmtClient",
    "QmtClientError",
    "QmtConnectionError",
    "QmtDataEmptyError",
    "QmtHttpError",
    "QmtOptionalDependencyError",
    "QmtProtocolError",
    "QmtRpcError",
    "QmtSchemaMismatchError",
    "QmtServerUnavailableError",
    "SnapshotClient",
    "TradingFacade",
    "load_fixture",
    "load_json",
    "load_jsonl",
    "load_snapshot_manifest",
    "market_to_arrow",
    "market_to_dataframe",
    "stock_account",
]

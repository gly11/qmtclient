from __future__ import annotations

from qmtclient.client import QmtClient
from qmtclient.errors import (
    QmtAuthError,
    QmtClientError,
    QmtConnectionError,
    QmtHttpError,
    QmtProtocolError,
    QmtRpcError,
)
from qmtclient.fake import FakeQmtClient
from qmtclient.fixtures import EventReplay, load_fixture, load_json, load_jsonl
from qmtclient.strategy import AccountFacade, MarketFacade, TradingFacade, stock_account

__version__ = "0.1.0"

__all__ = [
    "AccountFacade",
    "EventReplay",
    "FakeQmtClient",
    "MarketFacade",
    "QmtAuthError",
    "QmtClient",
    "QmtClientError",
    "QmtConnectionError",
    "QmtHttpError",
    "QmtProtocolError",
    "QmtRpcError",
    "TradingFacade",
    "load_fixture",
    "load_json",
    "load_jsonl",
    "stock_account",
]

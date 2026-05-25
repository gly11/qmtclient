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
from qmtclient.strategy import AccountFacade, MarketFacade, TradingFacade, stock_account

__version__ = "0.1.0.dev0"

__all__ = [
    "AccountFacade",
    "MarketFacade",
    "QmtAuthError",
    "QmtClient",
    "QmtClientError",
    "QmtConnectionError",
    "QmtHttpError",
    "QmtProtocolError",
    "QmtRpcError",
    "TradingFacade",
    "stock_account",
]

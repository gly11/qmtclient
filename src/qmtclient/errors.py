from __future__ import annotations

from typing import Any


class QmtClientError(Exception):
    """Base error raised by qmtclient."""


class QmtConnectionError(QmtClientError):
    """Raised when qmtserver cannot be reached."""


class QmtRetryableError(QmtClientError):
    """Marker for errors that may succeed on a later retry."""


class QmtHttpError(QmtClientError):
    def __init__(
        self,
        status_code: int,
        message: str,
        response: Any = None,
        *,
        code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.response = response
        self.request_id = request_id


class QmtAuthError(QmtHttpError):
    """Raised when qmtserver rejects authentication."""


class QmtServerUnavailableError(QmtHttpError, QmtRetryableError):
    """Raised when qmtserver is temporarily unavailable."""


class QmtProtocolError(QmtClientError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        self.request_id = request_id


class QmtRpcError(QmtClientError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        target: str,
        method: str,
        response: dict[str, Any],
        request_id: str | None = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.target = target
        self.method = method
        self.response = response
        self.request_id = request_id


class QmtDataEmptyError(QmtClientError):
    def __init__(self, message: str, *, schema_version: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.schema_version = schema_version


class QmtSchemaMismatchError(QmtClientError):
    def __init__(self, message: str, *, schema_version: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.schema_version = schema_version


class QmtOptionalDependencyError(QmtClientError):
    def __init__(self, dependency: str, feature: str) -> None:
        super().__init__(f"{feature} requires optional dependency: {dependency}")
        self.dependency = dependency
        self.feature = feature

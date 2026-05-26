from __future__ import annotations

from typing import Any

import httpx

from qmtclient.batch import BatchClient
from qmtclient.cache import MemoryCache
from qmtclient.errors import (
    QmtAuthError,
    QmtConnectionError,
    QmtHttpError,
    QmtProtocolError,
    QmtRpcError,
    QmtServerUnavailableError,
)
from qmtclient.events import ConnectFactory, EventStream
from qmtclient.models import DIAGNOSE_SCHEMA_VERSION, DiagnoseCheck, DiagnoseResponse
from qmtclient.proxy import RpcTargetProxy
from qmtclient.strategy import AccountFacade, MarketFacade, TradingFacade

API_VERSION = "v1"
RETRY_STATUS_CODES = {502, 503, 504}


class QmtClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        token: str | None = None,
        timeout: float = 10.0,
        retries: int = 0,
        backoff: float = 0.0,
        cache_enabled: bool = False,
        api_version: str | None = API_VERSION,
        transport: httpx.BaseTransport | None = None,
        http_client: httpx.Client | None = None,
        event_connect_factory: ConnectFactory | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.api_version = api_version.strip("/") if api_version else None
        self._event_connect_factory = event_connect_factory
        self._owns_http_client = http_client is None
        self._http = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers(),
            transport=transport,
        )
        self.xtdata = RpcTargetProxy(self, "xtdata")
        self.trader = RpcTargetProxy(self, "trader")
        self.market = MarketFacade(self)
        self.account = AccountFacade(self)
        self.trading = TradingFacade(self)
        self.batch = BatchClient(self)
        self.cache = MemoryCache(enabled=cache_enabled)

    def close(self) -> None:
        if self._owns_http_client:
            self._http.close()

    def __enter__(self) -> QmtClient:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def version(self) -> dict[str, Any]:
        return self.health()

    def status(self) -> dict[str, Any]:
        return self._request("GET", "/qmt/status")

    def methods(self) -> dict[str, Any]:
        return self._request("GET", "/rpc/methods")

    def rpc(
        self,
        target: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        response = self._request(
            "POST",
            "/rpc",
            json={
                "target": target,
                "method": method,
                "args": args or [],
                "kwargs": kwargs or {},
            },
        )
        if not response.get("ok", False):
            error = response.get("error") or {}
            raise QmtRpcError(
                code=str(error.get("code", "RPC_ERROR")),
                message=str(error.get("message", "RPC call failed")),
                target=target,
                method=method,
                response=response,
                request_id=_response_request_id(response),
            )
        return response.get("data")

    def orders(self, limit: int | None = None) -> list[dict[str, Any]]:
        params = {"limit": limit} if limit is not None else None
        response = self._request("GET", "/orders", params=params)
        return _response_list(response)

    def order(self, order_id: str) -> dict[str, Any]:
        response = self._request("GET", f"/orders/{order_id}")
        data = response.get("data")
        return data if isinstance(data, dict) else {}

    def trades(self, limit: int | None = None) -> list[dict[str, Any]]:
        params = {"limit": limit} if limit is not None else None
        response = self._request("GET", "/trades", params=params)
        return _response_list(response)

    def recent_events(
        self,
        *,
        types: list[str] | tuple[str, ...] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if types:
            params["types"] = ",".join(types)
        if limit is not None:
            params["limit"] = limit
        response = self._request("GET", "/events/recent", params=params or None)
        return _response_list(response)

    def diagnose(self, *, sample_code: str | None = None) -> DiagnoseResponse:
        checks: list[DiagnoseCheck] = []
        checks.append(_run_check("http", self.health))
        checks.append(_run_check("ready", self.status))
        checks.append(_run_check("methods", self.methods))
        if sample_code is not None:
            checks.append(_run_check("sample", lambda: self.market.get_full_tick([sample_code])))
        return {
            "schema_version": DIAGNOSE_SCHEMA_VERSION,
            "ok": all(check["ok"] for check in checks),
            "checks": checks,
            "meta": {"api_version": self.api_version, "sample_code": sample_code},
        }

    def check_compatibility(
        self,
        *,
        api_version: str = API_VERSION,
        schema_version: str | None = None,
    ) -> DiagnoseResponse:
        health = _run_check("api_version", self.health)
        if health["ok"]:
            versions = health.get("data", {}).get("api_versions", [])
            health["ok"] = api_version in versions
            if not health["ok"]:
                health["error"] = {
                    "type": "QmtSchemaMismatchError",
                    "message": f"qmtserver does not advertise API version: {api_version}",
                }
        checks = [health]
        if schema_version is not None:
            checks.append(
                {
                    "name": "schema_version",
                    "ok": True,
                    "data": {"schema_version": schema_version},
                }
            )
        return {
            "schema_version": DIAGNOSE_SCHEMA_VERSION,
            "ok": all(check["ok"] for check in checks),
            "checks": checks,
            "meta": {"api_version": api_version, "schema_version": schema_version},
        }

    def events(
        self,
        *,
        types: list[str] | tuple[str, ...] | None = None,
        reconnects: int = 0,
    ) -> EventStream:
        return EventStream(
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            api_version=self.api_version,
            types=types,
            reconnects=reconnects,
            connect_factory=self._event_connect_factory,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        last_error: QmtConnectionError | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._request_once(method, path, **kwargs)
            except QmtConnectionError as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise
                _sleep_backoff(self.backoff, attempt)
            except QmtServerUnavailableError:
                if attempt >= self.retries:
                    raise
                _sleep_backoff(self.backoff, attempt)
        if last_error is not None:
            raise last_error
        raise QmtConnectionError("request failed without response")

    def _request_once(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._http.request(method, self._api_path(path), **kwargs)
        except httpx.RequestError as exc:
            raise QmtConnectionError(str(exc)) from exc

        request_id = response.headers.get("X-Request-ID")
        try:
            response_body = _response_json(response)
        except ValueError as exc:
            if response.status_code in RETRY_STATUS_CODES:
                raise QmtServerUnavailableError(
                    response.status_code,
                    response.text,
                    {"data": response.text},
                    code="SERVER_UNAVAILABLE",
                    request_id=request_id,
                ) from exc
            if response.status_code >= 400:
                raise QmtHttpError(
                    response.status_code,
                    response.text,
                    {"data": response.text},
                    code="HTTP_ERROR",
                    request_id=request_id,
                ) from exc
            raise QmtProtocolError(
                "qmtserver returned a non-JSON response",
                status_code=response.status_code,
                response_text=response.text,
                request_id=request_id,
            ) from exc

        if response.status_code == 401:
            code, message = _http_error_detail(response_body, "UNAUTHORIZED", "Unauthorized")
            raise QmtAuthError(
                response.status_code,
                message,
                response_body,
                code=code,
                request_id=request_id,
            )
        if response.status_code in RETRY_STATUS_CODES:
            code, message = _http_error_detail(response_body, "SERVER_UNAVAILABLE", response.text)
            raise QmtServerUnavailableError(
                response.status_code,
                message,
                response_body,
                code=code,
                request_id=request_id,
            )
        if response.status_code >= 400:
            code, message = _http_error_detail(response_body, "HTTP_ERROR", response.text)
            raise QmtHttpError(
                response.status_code,
                message,
                response_body,
                code=code,
                request_id=request_id,
            )
        return response_body

    def _headers(self) -> dict[str, str]:
        if self.token is None:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def _api_path(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        if self.api_version is None:
            return normalized
        return f"/{self.api_version}{normalized}"


def _response_json(response: httpx.Response) -> dict[str, Any]:
    if not response.content:
        return {}
    value = response.json()
    if isinstance(value, dict):
        return value
    return {"data": value}


def _http_error_detail(
    response: dict[str, Any],
    default_code: str,
    default_message: str,
) -> tuple[str, str]:
    detail = response.get("detail")
    if isinstance(detail, dict):
        return str(detail.get("code", default_code)), str(detail.get("message", default_message))
    error = response.get("error")
    if isinstance(error, dict):
        return str(error.get("code", default_code)), str(error.get("message", default_message))
    return default_code, default_message


def _response_request_id(response: dict[str, Any]) -> str | None:
    meta = response.get("meta")
    if isinstance(meta, dict):
        request_id = meta.get("request_id")
        return str(request_id) if request_id is not None else None
    return None


def _response_list(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data", [])
    return data if isinstance(data, list) else []


def _run_check(name: str, func: Any) -> DiagnoseCheck:
    try:
        data = func()
    except Exception as exc:
        return {"name": name, "ok": False, "error": _error_detail(exc)}
    return {"name": name, "ok": True, "data": data if isinstance(data, dict) else {"data": data}}


def _error_detail(exc: Exception) -> dict[str, Any]:
    detail = {"type": exc.__class__.__name__, "message": str(exc)}
    code = getattr(exc, "code", None)
    request_id = getattr(exc, "request_id", None)
    if code is not None:
        detail["code"] = str(code)
    if request_id is not None:
        detail["request_id"] = str(request_id)
    return detail


def _sleep_backoff(backoff: float, attempt: int) -> None:
    if backoff <= 0:
        return
    import time

    time.sleep(backoff * (2**attempt))

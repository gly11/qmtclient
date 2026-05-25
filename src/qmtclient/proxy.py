from __future__ import annotations

from typing import Any, Protocol


class RpcClient(Protocol):
    def rpc(
        self,
        target: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any: ...


class RpcTargetProxy:
    def __init__(self, client: RpcClient, target: str) -> None:
        self._client = client
        self._target = target

    def __getattr__(self, method: str) -> RpcMethodProxy:
        if method.startswith("_"):
            raise AttributeError(method)
        return RpcMethodProxy(self._client, self._target, method)


class RpcMethodProxy:
    def __init__(self, client: RpcClient, target: str, method: str) -> None:
        self._client = client
        self._target = target
        self._method = method

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._client.rpc(self._target, self._method, list(args), kwargs)

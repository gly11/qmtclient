from __future__ import annotations

from typing import Any, Protocol


class RequestClient(Protocol):
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]: ...


class BatchClient:
    def __init__(self, client: RequestClient) -> None:
        self._client = client

    def create_job(self, kind: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._client._request(
            "POST",
            "/batch/jobs",
            json={"kind": kind, "params": params},
        )
        return _response_dict(response)

    def get_job(self, job_id: str) -> dict[str, Any]:
        response = self._client._request("GET", f"/batch/jobs/{job_id}")
        return _response_dict(response)

    def download_snapshot(self, job_id: str) -> dict[str, Any]:
        response = self._client._request("GET", f"/batch/jobs/{job_id}/snapshot")
        return _response_dict(response)


def _response_dict(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    return data if isinstance(data, dict) else {}

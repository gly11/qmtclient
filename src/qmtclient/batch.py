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
            "/jobs/history-download",
            json=_history_payload(kind, params),
        )
        return _response_dict(response, "job")

    def create_history_download(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._client._request("POST", "/jobs/history-download", json=params)
        return _response_dict(response, "job")

    def get_job(self, job_id: str) -> dict[str, Any]:
        response = self._client._request("GET", f"/jobs/{job_id}")
        return _response_dict(response, "job")

    def get_result(self, job_id: str) -> dict[str, Any]:
        response = self._client._request("GET", f"/jobs/{job_id}/result")
        return _response_dict(response, "manifest")

    def download_snapshot(self, job_id: str) -> dict[str, Any]:
        return self.get_result(job_id)

    def cancel(self, job_id: str) -> dict[str, Any]:
        response = self._client._request("POST", f"/jobs/{job_id}/cancel")
        return _response_dict(response, "job")


def _response_dict(response: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    data = response.get("data")
    if not isinstance(data, dict):
        return {}
    if key is not None and isinstance(data.get(key), dict):
        return data[key]
    return data


def _history_payload(kind: str, params: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(params)
    if kind.startswith("market."):
        kind = kind.removeprefix("market.")
    normalized["kind"] = kind
    if "symbols" not in normalized and "codes" in normalized:
        normalized["symbols"] = normalized.pop("codes")
    if "start" not in normalized and "start_time" in normalized:
        normalized["start"] = normalized.pop("start_time")
    if "end" not in normalized and "end_time" in normalized:
        normalized["end"] = normalized.pop("end_time")
    normalized.setdefault("format", "csv")
    return normalized

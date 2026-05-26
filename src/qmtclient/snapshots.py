from __future__ import annotations

import hashlib
import json
from builtins import list as list_type
from pathlib import Path
from typing import Any

from qmtclient.errors import QmtSchemaMismatchError

SNAPSHOT_SCHEMA_VERSION = "qmtclient.snapshot.v1"


class SnapshotClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self._client._request("POST", "/snapshots", json=request)
        return _response_dict(response)

    def list(self) -> list_type[dict[str, Any]]:
        response = self._client._request("GET", "/snapshots")
        data = response.get("data")
        if isinstance(data, dict) and isinstance(data.get("snapshots"), list):
            return [item for item in data["snapshots"] if isinstance(item, dict)]
        return []

    def manifest(self, snapshot_id: str) -> dict[str, Any]:
        response = self._client._request("GET", f"/snapshots/{snapshot_id}/manifest")
        data = response.get("data")
        if isinstance(data, dict) and isinstance(data.get("manifest"), dict):
            return data["manifest"]
        return {}

    def quality(self, snapshot_id: str) -> dict[str, Any]:
        return self._client._request("GET", f"/snapshots/{snapshot_id}/quality")


def load_snapshot_manifest(path: str | Path, *, verify: bool = True) -> dict[str, Any]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8-sig") as file:
        manifest = json.load(file)
    if not isinstance(manifest, dict):
        raise QmtSchemaMismatchError("snapshot manifest root must be an object")
    if _is_qmtserver_manifest(manifest):
        if verify:
            _verify_qmtserver_manifest(manifest_path, manifest)
        return manifest
    if manifest.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise QmtSchemaMismatchError("unsupported snapshot manifest schema")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise QmtSchemaMismatchError("snapshot manifest files must be a list")
    if verify:
        for item in files:
            _verify_file(manifest_path.parent, item)
    return manifest


def _verify_file(root: Path, item: Any) -> None:
    if not isinstance(item, dict):
        raise QmtSchemaMismatchError("snapshot file entry must be an object")
    rel_path = item.get("path")
    expected_hash = item.get("sha256")
    expected_rows = item.get("row_count")
    if not isinstance(rel_path, str) or not isinstance(expected_hash, str):
        raise QmtSchemaMismatchError("snapshot file entry requires path and sha256")
    data_path = root / rel_path
    actual_hash = _sha256(data_path)
    if actual_hash != expected_hash:
        raise QmtSchemaMismatchError(f"snapshot file hash mismatch: {rel_path}")
    if expected_rows is not None and _row_count(data_path) != expected_rows:
        raise QmtSchemaMismatchError(f"snapshot file row count mismatch: {rel_path}")


def _is_qmtserver_manifest(manifest: dict[str, Any]) -> bool:
    return (
        isinstance(manifest.get("snapshot_id"), str)
        and isinstance(manifest.get("schema"), str)
        and isinstance(manifest.get("format"), str)
        and isinstance(manifest.get("hash"), str)
    )


def _verify_qmtserver_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    snapshot_id = str(manifest["snapshot_id"])
    format_name = str(manifest["format"])
    data_path = manifest_path.with_name(f"{snapshot_id}.{format_name}")
    expected_hash = str(manifest["hash"])
    actual_hash = f"sha256:{_sha256(data_path)}"
    if actual_hash != expected_hash:
        raise QmtSchemaMismatchError(f"snapshot file hash mismatch: {data_path.name}")
    expected_rows = manifest.get("row_count")
    if expected_rows is not None and _data_row_count(data_path, format_name) != expected_rows:
        raise QmtSchemaMismatchError(f"snapshot file row count mismatch: {data_path.name}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig") as file:
        return sum(1 for line in file if line.strip())


def _data_row_count(path: Path, format_name: str) -> int:
    rows = _row_count(path)
    if format_name == "csv" and rows > 0:
        return rows - 1
    return rows


def _response_dict(response: dict[str, Any]) -> dict[str, Any]:
    data = response.get("data")
    return data if isinstance(data, dict) else {}

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from qmtclient.errors import QmtSchemaMismatchError

SNAPSHOT_SCHEMA_VERSION = "qmtclient.snapshot.v1"


def load_snapshot_manifest(path: str | Path, *, verify: bool = True) -> dict[str, Any]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8-sig") as file:
        manifest = json.load(file)
    if not isinstance(manifest, dict):
        raise QmtSchemaMismatchError("snapshot manifest root must be an object")
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig") as file:
        return sum(1 for line in file if line.strip())

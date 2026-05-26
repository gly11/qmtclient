from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from qmtclient import __version__
from qmtclient.client import API_VERSION
from qmtclient.errors import (
    QmtAuthError,
    QmtClientError,
    QmtConnectionError,
    QmtProtocolError,
    QmtSchemaMismatchError,
)
from qmtclient.fixtures import load_fixture, load_jsonl
from qmtclient.snapshots import load_snapshot_manifest

EXIT_FAILED_CHECK = 1
EXIT_AUTH_ERROR = 3
EXIT_CONNECTION_ERROR = 4
EXIT_SCHEMA_ERROR = 5


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except Exception as exc:
        return _emit_error(exc, json_output=args.json)
    _emit(result, json_output=args.json)
    return 0 if result.get("ok", True) else EXIT_FAILED_CHECK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qmtclient")
    parser.add_argument("--json", action="store_true", help="output JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    version = subparsers.add_parser("version", help="show qmtclient version")
    version.set_defaults(func=_cmd_version)

    snapshot = subparsers.add_parser("snapshot-verify", help="verify snapshot manifest")
    snapshot.add_argument("manifest")
    snapshot.set_defaults(func=_cmd_snapshot_verify)

    fixture = subparsers.add_parser("fixture-check", help="check JSON or JSONL fixture")
    fixture.add_argument("path")
    fixture.set_defaults(func=_cmd_fixture_check)
    return parser


def _cmd_version(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "ok": True,
        "qmtclient": __version__,
        "api_version": API_VERSION,
    }


def _cmd_snapshot_verify(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_snapshot_manifest(args.manifest)
    return {
        "ok": True,
        "path": str(args.manifest),
        "schema_version": manifest.get("schema_version") or manifest.get("schema"),
        "file_count": _manifest_file_count(manifest),
    }


def _cmd_fixture_check(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.path)
    if path.suffix.lower() == ".jsonl":
        events = load_jsonl(path)
        return {
            "ok": True,
            "path": str(path),
            "fixture_type": "jsonl",
            "events": len(events),
        }
    fixture = load_fixture(path)
    return {
        "ok": True,
        "path": str(path),
        "fixture_type": "json",
        "events": _list_count(fixture.get("events")),
        "orders": _list_count(fixture.get("orders")),
        "trades": _list_count(fixture.get("trades")),
        "market_keys": _sorted_keys(fixture.get("market")),
    }


def _manifest_file_count(manifest: dict[str, Any]) -> int:
    files = manifest.get("files")
    if isinstance(files, list):
        return len(files)
    return 1 if manifest.get("snapshot_id") else 0


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _sorted_keys(value: Any) -> list[str]:
    return sorted(value) if isinstance(value, dict) else []


def _emit(result: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
    for key, value in result.items():
        if key == "ok":
            continue
        print(f"{key}: {value}")


def _emit_error(exc: Exception, *, json_output: bool) -> int:
    detail = {
        "ok": False,
        "error": {
            "type": exc.__class__.__name__,
            "message": str(exc),
        },
    }
    _emit(detail, json_output=json_output)
    return _exit_code(exc)


def _exit_code(exc: Exception) -> int:
    if isinstance(exc, QmtAuthError):
        return EXIT_AUTH_ERROR
    if isinstance(exc, QmtConnectionError):
        return EXIT_CONNECTION_ERROR
    if isinstance(exc, (QmtProtocolError, QmtSchemaMismatchError)):
        return EXIT_SCHEMA_ERROR
    if isinstance(exc, QmtClientError):
        return EXIT_FAILED_CHECK
    return EXIT_FAILED_CHECK


if __name__ == "__main__":
    sys.exit(main())

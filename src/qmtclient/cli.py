from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from qmtclient import __version__
from qmtclient.client import API_VERSION, QmtClient
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


def main(argv: list[str] | None = None, *, client_factory: Callable[..., Any] = QmtClient) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.client_factory = client_factory
    try:
        result = args.func(args)
    except Exception as exc:
        return _emit_error(exc, json_output=args.json)
    _emit(result, json_output=args.json)
    return 0 if result.get("ok", True) else EXIT_FAILED_CHECK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qmtclient")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token")
    parser.add_argument("--token-env", default="QMTCLIENT_TOKEN")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--api-version", default=API_VERSION)
    parser.add_argument("--json", action="store_true", help="output JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    version = subparsers.add_parser("version", help="show qmtclient version")
    version.set_defaults(func=_cmd_version)

    check = subparsers.add_parser("check", help="check qmtserver health and compatibility")
    check.set_defaults(func=_cmd_check)

    diagnose = subparsers.add_parser("diagnose", help="run qmtclient diagnostics")
    diagnose.add_argument("--sample-code")
    diagnose.set_defaults(func=_cmd_diagnose)

    methods = subparsers.add_parser("methods", help="list qmtserver RPC methods")
    methods.set_defaults(func=_cmd_methods)

    ws_check = subparsers.add_parser("ws-check", help="wait for one websocket event")
    ws_check.add_argument("--wait-seconds", type=float, default=10.0)
    ws_check.add_argument("--types")
    ws_check.set_defaults(func=_cmd_ws_check)

    market_capabilities = subparsers.add_parser(
        "market-capabilities",
        help="check stable market capabilities endpoint",
    )
    market_capabilities.set_defaults(func=_cmd_market_capabilities)

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


def _cmd_check(args: argparse.Namespace) -> dict[str, Any]:
    client = _create_client(args)
    try:
        health = client.health()
        compatibility = client.check_compatibility()
    finally:
        _close_client(client)
    return {
        "ok": bool(health.get("ok", False)) and bool(compatibility.get("ok", False)),
        "health": health,
        "compatibility": compatibility,
    }


def _cmd_diagnose(args: argparse.Namespace) -> dict[str, Any]:
    client = _create_client(args)
    try:
        return client.diagnose(sample_code=args.sample_code)
    finally:
        _close_client(client)


def _cmd_methods(args: argparse.Namespace) -> dict[str, Any]:
    client = _create_client(args)
    try:
        response = client.methods()
    finally:
        _close_client(client)
    methods = response.get("methods")
    method_list = methods if isinstance(methods, list) else []
    return {
        "ok": bool(response.get("ok", True)),
        "method_count": len(method_list),
        "methods": method_list,
    }


def _cmd_market_capabilities(args: argparse.Namespace) -> dict[str, Any]:
    client = _create_client(args)
    try:
        capabilities = client.market.capabilities()
    finally:
        _close_client(client)
    return {
        "ok": True,
        "capabilities": capabilities,
    }


def _cmd_ws_check(args: argparse.Namespace) -> dict[str, Any]:
    client = _create_client(args)
    try:
        event = _next_event_with_timeout(
            client,
            types=_split_types(args.types),
            wait_seconds=args.wait_seconds,
        )
    finally:
        _close_client(client)
    return {
        "ok": True,
        "event_type": event.get("type"),
        "event": event,
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


def _next_event_with_timeout(
    client: Any,
    *,
    types: list[str] | None,
    wait_seconds: float,
) -> dict[str, Any]:
    results: queue.Queue[dict[str, Any] | BaseException] = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            event = next(iter(client.events(types=types)))
        except BaseException as exc:
            results.put(exc)
            return
        results.put(event)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    try:
        result = results.get(timeout=max(wait_seconds, 0.0))
    except queue.Empty as exc:
        raise TimeoutError("timed out waiting for websocket event") from exc
    if isinstance(result, BaseException):
        raise result
    return result


def _split_types(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _create_client(args: argparse.Namespace) -> Any:
    return args.client_factory(
        args.base_url,
        token=_resolve_token(args),
        timeout=args.timeout,
        api_version=args.api_version,
    )


def _resolve_token(args: argparse.Namespace) -> str | None:
    if args.token is not None:
        return args.token
    token_env = args.token_env
    if token_env:
        return os.environ.get(token_env)
    return None


def _close_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()


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
    if isinstance(exc, TimeoutError):
        return EXIT_CONNECTION_ERROR
    if isinstance(exc, (QmtProtocolError, QmtSchemaMismatchError)):
        return EXIT_SCHEMA_ERROR
    if isinstance(exc, QmtClientError):
        return EXIT_FAILED_CHECK
    return EXIT_FAILED_CHECK


if __name__ == "__main__":
    sys.exit(main())

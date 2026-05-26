from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from qmtclient import __version__
from qmtclient.cli import main
from qmtclient.client import API_VERSION
from qmtclient.errors import QmtAuthError


class CliTests(unittest.TestCase):
    def test_project_defines_console_script(self) -> None:
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("[project.scripts]", pyproject)
        self.assertIn('qmtclient = "qmtclient.cli:main"', pyproject)

    def test_version_prints_client_version_and_api_version(self) -> None:
        code, stdout, stderr = _run_cli(["version"])

        self.assertEqual(code, 0)
        self.assertIn(__version__, stdout)
        self.assertIn(API_VERSION, stdout)
        self.assertEqual(stderr, "")

    def test_snapshot_verify_outputs_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_path = root / "bars.jsonl"
            data = b'{"code":"000001.SZ"}\n'
            data_path.write_bytes(data)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "qmtclient.snapshot.v1",
                        "files": [
                            {
                                "path": data_path.name,
                                "sha256": hashlib.sha256(data).hexdigest(),
                                "row_count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            code, stdout, stderr = _run_cli(["--json", "snapshot-verify", str(manifest_path)])

        summary = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["schema_version"], "qmtclient.snapshot.v1")
        self.assertEqual(summary["file_count"], 1)

    def test_snapshot_verify_maps_schema_error_to_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_path = root / "bars.jsonl"
            data = b'{"code":"000001.SZ"}\n'
            data_path.write_bytes(data)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "qmtclient.snapshot.v1",
                        "files": [
                            {
                                "path": data_path.name,
                                "sha256": hashlib.sha256(data).hexdigest(),
                                "row_count": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            code, stdout, stderr = _run_cli(["--json", "snapshot-verify", str(manifest_path)])

        summary = json.loads(stdout)
        self.assertEqual(code, 5)
        self.assertEqual(stderr, "")
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["error"]["type"], "QmtSchemaMismatchError")

    def test_fixture_check_outputs_json_summary_for_json_fixture(self) -> None:
        fixture = {
            "market": {"daily_bars": [{"code": "000001.SZ"}]},
            "orders": [{"order_id": "order-1"}],
            "trades": [{"trade_id": "trade-1"}],
            "events": [{"type": "heartbeat"}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fixture.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")

            code, stdout, stderr = _run_cli(["--json", "fixture-check", str(path)])

        summary = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["fixture_type"], "json")
        self.assertEqual(summary["events"], 1)
        self.assertEqual(summary["orders"], 1)
        self.assertEqual(summary["trades"], 1)
        self.assertEqual(summary["market_keys"], ["daily_bars"])

    def test_fixture_check_outputs_json_summary_for_jsonl_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            path.write_text('{"type":"heartbeat"}\n{"type":"stock_trade"}\n', encoding="utf-8")

            code, stdout, stderr = _run_cli(["--json", "fixture-check", str(path)])

        summary = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["fixture_type"], "jsonl")
        self.assertEqual(summary["events"], 2)

    def test_check_uses_connection_arguments_and_token_env(self) -> None:
        captured: dict[str, Any] = {}

        class FakeClient:
            def __init__(self, *args: object, **kwargs: object) -> None:
                captured["args"] = args
                captured["kwargs"] = kwargs

            def health(self) -> dict[str, object]:
                return {"ok": True, "api_versions": ["v1"]}

            def check_compatibility(self) -> dict[str, object]:
                return {"ok": True, "checks": []}

        with mock.patch.dict(os.environ, {"QMTCLIENT_TEST_TOKEN": "env-token"}):
            code, stdout, stderr = _run_cli(
                [
                    "--json",
                    "--base-url",
                    "http://qmt.test",
                    "--token-env",
                    "QMTCLIENT_TEST_TOKEN",
                    "--timeout",
                    "2.5",
                    "--api-version",
                    "v1",
                    "check",
                ],
                client_factory=FakeClient,
            )

        summary = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(summary["ok"])
        self.assertEqual(captured["args"], ("http://qmt.test",))
        self.assertEqual(
            captured["kwargs"],
            {"token": "env-token", "timeout": 2.5, "api_version": "v1"},
        )

    def test_token_argument_overrides_environment_token(self) -> None:
        captured: dict[str, Any] = {}

        class FakeClient:
            def __init__(self, *args: object, **kwargs: object) -> None:
                captured["kwargs"] = kwargs

            def health(self) -> dict[str, object]:
                return {"ok": True, "api_versions": ["v1"]}

            def check_compatibility(self) -> dict[str, object]:
                return {"ok": True, "checks": []}

        with mock.patch.dict(os.environ, {"QMTCLIENT_TOKEN": "env-token"}):
            code, stdout, stderr = _run_cli(
                ["--json", "--token", "arg-token", "check"],
                client_factory=FakeClient,
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(json.loads(stdout)["ok"])
        self.assertEqual(captured["kwargs"]["token"], "arg-token")

    def test_diagnose_passes_sample_code(self) -> None:
        class FakeClient:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            def diagnose(self, *, sample_code: str | None = None) -> dict[str, object]:
                return {
                    "schema_version": "qmtclient.diagnose.v1",
                    "ok": True,
                    "checks": [],
                    "meta": {"sample_code": sample_code},
                }

        code, stdout, stderr = _run_cli(
            ["--json", "diagnose", "--sample-code", "000001.SZ"],
            client_factory=FakeClient,
        )

        summary = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(summary["meta"]["sample_code"], "000001.SZ")

    def test_auth_error_maps_to_exit_code(self) -> None:
        class FakeClient:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            def health(self) -> dict[str, object]:
                raise QmtAuthError(401, "bad token", {}, code="UNAUTHORIZED")

        code, stdout, stderr = _run_cli(["--json", "check"], client_factory=FakeClient)

        summary = json.loads(stdout)
        self.assertEqual(code, 3)
        self.assertEqual(stderr, "")
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["error"]["type"], "QmtAuthError")


def _run_cli(argv: list[str], **kwargs: Any) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(argv, **kwargs)
    return code, stdout.getvalue(), stderr.getvalue()


if __name__ == "__main__":
    unittest.main()

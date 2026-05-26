from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import httpx

from qmtclient import QmtClient, QmtSchemaMismatchError, load_snapshot_manifest


class BatchAndSnapshotTests(unittest.TestCase):
    def test_batch_client_creates_polls_and_downloads_snapshot(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/batch/jobs" and request.method == "POST":
                payload = json.loads(request.content)
                self.assertEqual(payload["kind"], "market.daily_bars")
                return httpx.Response(200, json={"ok": True, "data": {"job_id": "job-1"}})
            if request.url.path == "/v1/batch/jobs/job-1":
                return httpx.Response(200, json={"ok": True, "data": {"status": "done"}})
            if request.url.path == "/v1/batch/jobs/job-1/snapshot":
                return httpx.Response(200, json={"ok": True, "data": {"snapshot_id": "snap-1"}})
            raise AssertionError(request.url.path)

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        job = client.batch.create_job("market.daily_bars", {"codes": ["000001.SZ"]})

        self.assertEqual(job["job_id"], "job-1")
        self.assertEqual(client.batch.get_job("job-1")["status"], "done")
        self.assertEqual(client.batch.download_snapshot("job-1")["snapshot_id"], "snap-1")

    def test_snapshot_manifest_validates_hash_and_row_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_path = root / "bars.jsonl"
            data_path.write_bytes(b'{"code":"000001.SZ"}\n{"code":"600000.SH"}\n')
            manifest_path = root / "manifest.json"
            valid_hash = "bc6d5ce58a8593b7565f39d4c740c037cad800f69c5be59f010772ad39d7d8dd"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "qmtclient.snapshot.v1",
                        "files": [
                            {
                                "path": "bars.jsonl",
                                "sha256": valid_hash,
                                "row_count": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            manifest = load_snapshot_manifest(manifest_path)

        self.assertEqual(manifest["schema_version"], "qmtclient.snapshot.v1")
        self.assertEqual(manifest["files"][0]["row_count"], 2)

    def test_snapshot_manifest_rejects_row_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "bars.jsonl").write_bytes(b'{"code":"000001.SZ"}\n')
            manifest_path = root / "manifest.json"
            valid_hash = "7425d94d6b2dbbfa26691450f5a78a6a09acbed31173ee598976365e88fdb204"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "qmtclient.snapshot.v1",
                        "files": [
                            {
                                "path": "bars.jsonl",
                                "sha256": valid_hash,
                                "row_count": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(QmtSchemaMismatchError):
                load_snapshot_manifest(manifest_path)


if __name__ == "__main__":
    unittest.main()

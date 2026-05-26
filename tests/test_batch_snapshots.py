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
            if request.url.path == "/v1/jobs/history-download" and request.method == "POST":
                payload = json.loads(request.content)
                self.assertEqual(payload["kind"], "daily_bars")
                self.assertEqual(payload["symbols"], ["000001.SZ"])
                return httpx.Response(200, json={"ok": True, "data": {"job": {"job_id": "job-1"}}})
            if request.url.path == "/v1/jobs/job-1":
                return httpx.Response(
                    200,
                    json={"ok": True, "data": {"job": {"status": "succeeded"}}},
                )
            if request.url.path == "/v1/jobs/job-1/result":
                return httpx.Response(
                    200,
                    json={"ok": True, "data": {"manifest": {"snapshot_id": "snap-1"}}},
                )
            raise AssertionError(request.url.path)

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        job = client.batch.create_job("market.daily_bars", {"codes": ["000001.SZ"]})

        self.assertEqual(job["job_id"], "job-1")
        self.assertEqual(client.batch.get_job("job-1")["status"], "succeeded")
        self.assertEqual(client.batch.download_snapshot("job-1")["snapshot_id"], "snap-1")

    def test_snapshot_client_creates_lists_and_reads_quality(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/snapshots" and request.method == "POST":
                return httpx.Response(
                    200,
                    json={
                        "ok": True,
                        "data": {"manifest": {"snapshot_id": "snap-1"}, "cached": False},
                    },
                )
            if request.url.path == "/v1/snapshots":
                return httpx.Response(
                    200,
                    json={"ok": True, "data": {"snapshots": [{"snapshot_id": "snap-1"}]}},
                )
            if request.url.path == "/v1/snapshots/snap-1/manifest":
                return httpx.Response(
                    200,
                    json={"ok": True, "data": {"manifest": {"snapshot_id": "snap-1"}}},
                )
            if request.url.path == "/v1/snapshots/snap-1/quality":
                return httpx.Response(
                    200,
                    json={
                        "ok": True,
                        "data": {"missing_dates": []},
                        "meta": {"schema": "market.quality.v1"},
                    },
                )
            raise AssertionError(request.url.path)

        client = QmtClient("http://qmt.test", transport=httpx.MockTransport(handler))

        self.assertEqual(
            client.snapshots.create({"kind": "daily_bars"})["manifest"]["snapshot_id"],
            "snap-1",
        )
        self.assertEqual(client.snapshots.list()[0]["snapshot_id"], "snap-1")
        self.assertEqual(client.snapshots.manifest("snap-1")["snapshot_id"], "snap-1")
        self.assertEqual(client.snapshots.quality("snap-1")["meta"]["schema"], "market.quality.v1")

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

    def test_server_snapshot_manifest_validates_csv_hash_and_row_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_path = root / "daily_bars-abc.csv"
            data = (
                b"date,symbol,open,high,low,close,volume,amount,meta\n"
                b"2026-01-02,000001.SZ,10,11,9,10.5,1000,10500,{}\n"
            )
            data_path.write_bytes(data)
            manifest_path = root / "daily_bars-abc.manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "snapshot_id": "daily_bars-abc",
                        "request_hash": "sha256:req",
                        "schema": "market.bars.v1",
                        "format": "csv",
                        "request": {"kind": "daily_bars"},
                        "hash": (
                            "sha256:"
                            "196eee47e6a48b2d4612bc849e97af1bee6d3b37f894b4167c4ab4efeca0c6c3"
                        ),
                        "row_count": 1,
                        "symbol_count": 1,
                        "coverage_start": "2026-01-02",
                        "coverage_end": "2026-01-02",
                        "generated_at": "2026-05-26T00:00:00+00:00",
                        "qmtserver_version": "0.3.0",
                        "xtquant_version": None,
                    }
                ),
                encoding="utf-8",
            )

            manifest = load_snapshot_manifest(manifest_path)

        self.assertEqual(manifest["schema"], "market.bars.v1")
        self.assertEqual(manifest["row_count"], 1)


if __name__ == "__main__":
    unittest.main()

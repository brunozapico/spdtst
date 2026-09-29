import tempfile
import unittest
from pathlib import Path

from spdtst.models import Result
from spdtst.storage import save


class StorageTests(unittest.TestCase):
    def test_save_appends_jsonl(self) -> None:
        result = Result("Example", 100.0, 50.0, 10.0, 1.0, "2026-01-01T00:00:00+00:00")
        with tempfile.TemporaryDirectory() as directory:
            destination = save(result, Path(directory) / "history.jsonl")
            self.assertEqual(
                destination.read_text(),
                ('{"server": "Example", "download_mbps": 100.0, "upload_mbps": 50.0, '
                 '"latency_ms": 10.0, "jitter_ms": 1.0, '
                 '"timestamp": "2026-01-01T00:00:00+00:00", "public_ip": null, "isp": null, "location": null}\n'),
            )

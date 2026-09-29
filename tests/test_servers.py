import unittest

from spdtst.servers import custom_server, endpoint


class ServerTests(unittest.TestCase):
    def test_custom_server_has_expected_paths(self) -> None:
        server = custom_server("https://speed.example.com/backend")
        self.assertEqual(server.base_url, "https://speed.example.com/backend/")
        self.assertTrue(
            endpoint(server, server.download_path).startswith(
                "https://speed.example.com/backend/garbage.php?r="
            )
        )

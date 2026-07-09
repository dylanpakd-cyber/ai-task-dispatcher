import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from app import Handler


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        with urllib.request.urlopen(url) as resp:
            return resp.status, json.loads(resp.read())

    def test_health(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok"})

    def test_version(self):
        # red until the add-endpoint task ships GET /version
        status, body = self.get("/version")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"version": "1.0.0"})


if __name__ == "__main__":
    unittest.main()

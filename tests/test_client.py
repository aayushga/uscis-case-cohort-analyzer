import json
import unittest

from uscis_cohort.client import ApiError, UscisClient
from uscis_cohort.config import Settings


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(client_id="id", client_secret="secret")
        self.clock = FakeClock()

    def test_caches_token_and_throttles_case_requests(self):
        calls = []

        def transport(request, timeout):
            calls.append(request)
            if request.full_url.endswith("accesstoken"):
                return 200, {}, json.dumps({"access_token": "token", "expires_in": 1799}).encode()
            receipt = request.full_url.rsplit("/", 1)[-1]
            return 200, {}, json.dumps({"case_status": {"receiptNumber": receipt}}).encode()

        client = UscisClient(
            self.settings, transport=transport, clock=self.clock, sleep=self.clock.sleep
        )
        client.get_case("EAC9999103402")
        client.get_case("EAC9999103403")
        self.assertEqual(len(calls), 3)
        self.assertGreaterEqual(self.clock.now, 0.2)
        self.assertEqual(calls[1].get_header("Authorization"), "Bearer token")

    def test_surfaces_structured_error_message(self):
        def transport(request, timeout):
            if request.full_url.endswith("accesstoken"):
                return 200, {}, b'{"access_token":"token","expires_in":1799}'
            return 404, {}, b'{"errors":[{"message":"Case was not found"}]}'

        client = UscisClient(self.settings, transport=transport)
        with self.assertRaisesRegex(ApiError, "Case was not found"):
            client.get_case("EAC9999103402")


if __name__ == "__main__":
    unittest.main()


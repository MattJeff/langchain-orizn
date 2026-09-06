"""Run: python test_tools.py

Checks the only non-trivial logic here: turning an HTTP failure into a message
an agent can act on (it must carry the key URL).
"""
import json
import os

import langchain_orizn.tools as t
from langchain_orizn import OriznQuickVisaCheckTool, OriznVisaCheckTool


class FakeResp:
    def __init__(self, status, payload):
        self.status_code = status
        self.ok = status < 400
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


calls = {}


def fake_get(url, params=None, headers=None, timeout=None):
    calls["url"] = url
    calls["params"] = params
    calls["headers"] = headers
    return calls["resp"]


t.requests.get = fake_get


def raises_with(fn, needle):
    try:
        fn()
    except Exception as e:  # noqa: BLE001 — asserting on the message is the point
        assert needle in str(e), f'expected "{needle}" in: {e}'
        return
    raise AssertionError(f'expected a raise containing "{needle}"')


os.environ.pop("ORIZN_API_KEY", None)

# 1. No key at all -> the error tells you where to get one.
raises_with(
    lambda: OriznQuickVisaCheckTool()._run("FRA", "JPN"),
    "https://visa.orizn.app/visa-api",
)

# 2. Key rejected -> error carries the API's reason AND the key URL.
calls["resp"] = FakeResp(401, {"error": "API key required"})
raises_with(
    lambda: OriznQuickVisaCheckTool("bad")._run("FRA", "JPN"),
    "https://visa.orizn.app/visa-api",
)
raises_with(lambda: OriznQuickVisaCheckTool("bad")._run("FRA", "JPN"), "API key required")

# 3. Quota exceeded -> points at billing, not at signup.
calls["resp"] = FakeResp(429, {"error": "Monthly limit exceeded"})
raises_with(lambda: OriznVisaCheckTool("k")._run("FRA", "JPN"), "billing")

# 3b. Envelope since 2026-08-13: error is an object whose message already carries
#     price + checkout link -> shown as-is, no second link, no dict repr.
calls["resp"] = FakeResp(429, {"error": {"code": "QUOTA_EXCEEDED", "message": "Monthly quota reached. Starter is $49/mo for 30,000 requests: https://visa.orizn.app/visa-api/login?next=%2Fvisa-api%2Fdashboard%2Fbilling%3Fplan%3Dstarter",
                                         "docs_url": "https://visa.orizn.app/docs"}})
try:
    OriznVisaCheckTool("k")._run("FRA", "JPN")
except Exception as e:  # noqa: BLE001
    assert str(e).count("http") == 1 and "Hobby" not in str(e) and "{" not in str(e), e

# 4. Happy path: key sent as header, real endpoint + params, JSON string out.
calls["resp"] = FakeResp(200, {"data": {"passport": "FRA", "requirement": "visa_free"}})
out = OriznVisaCheckTool("k123")._run("fra", "jpn", "fr")
assert calls["url"] == "https://visa.orizn.app/api/v1/visa", calls["url"]
assert calls["params"] == {"passport": "FRA", "destination": "JPN", "lang": "fr"}, calls["params"]
assert calls["headers"] == {"x-api-key": "k123"}, calls["headers"]
assert json.loads(out)["data"]["requirement"] == "visa_free"

calls["resp"] = FakeResp(200, {"passport": "FRA", "requirement": "visa_free"})
OriznQuickVisaCheckTool("k123")._run("FRA", "JPN")
assert calls["url"] == "https://visa.orizn.app/api/v1/visa/check", calls["url"]

print("ok — 5 checks passed")

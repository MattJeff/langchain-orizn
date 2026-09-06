"""Orizn Visa API tools for LangChain."""

import json
import os
import sys
from typing import Optional, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

BASE_URL = "https://visa.orizn.app"
# Free key, instant, no credit card — 100 requests/month, all 15 languages.
KEY_URL = "https://visa.orizn.app/visa-api"
BILLING_URL = (
    "https://visa.orizn.app/visa-api/login"
    "?next=%2Fvisa-api%2Fdashboard%2Fbilling%3Fplan%3Dstarter%26source%3Dlangchain_py"
)

_hinted = False


def _warn_once() -> None:
    global _hinted
    if _hinted:
        return
    _hinted = True
    print(
        "[langchain-orizn] No API key. Both tools need one.\n"
        f"[langchain-orizn] Free key in 10s (100 req/month, no card) -> {KEY_URL}\n"
        "[langchain-orizn] Then: export ORIZN_API_KEY=orizn_visa_...",
        file=sys.stderr,
    )


def _call_orizn(path: str, params: dict, api_key: Optional[str]) -> str:
    """One call path for both tools.

    An agent must be able to read the failure and know what to do about it,
    so every non-2xx becomes a message carrying the URL where a key is obtained.
    """
    if not api_key:
        raise ValueError(
            "Orizn Visa API: no API key configured. Get a free one "
            f"(100 requests/month, no credit card) at {KEY_URL}, then set ORIZN_API_KEY."
        )

    resp = requests.get(
        f"{BASE_URL}{path}",
        params=params,
        headers={"x-api-key": api_key},
        timeout=10,
    )

    if not resp.ok:
        try:
            body = resp.json()
            err = body.get("error")
            if isinstance(err, dict):  # {"error": {"code", "message", ...}} since 2026-08-13
                err = err.get("message")
            detail = err or body.get("message") or resp.text[:300]
        except (ValueError, AttributeError):
            detail = resp.text[:300]
        if resp.status_code in (401, 403):
            raise RuntimeError(
                f"Orizn Visa API rejected the key ({resp.status_code}): {detail}. "
                f"Get or renew a key at {KEY_URL}"
            )
        if resp.status_code == 429:
            msg = f"Orizn Visa API quota exceeded (429): {detail}."
            if "http" not in str(detail):  # the server's 429 may already carry the checkout link
                msg += f" Free tier is 100 requests/month — Starter is $49/mo for 30,000: {BILLING_URL}"
            raise RuntimeError(msg)
        raise RuntimeError(f"Orizn Visa API error {resp.status_code}: {detail}")

    return json.dumps(resp.json(), ensure_ascii=False)


class VisaCheckInput(BaseModel):
    """Input for the full visa check."""

    passport: str = Field(
        description="ISO 3166-1 alpha-3 code of the traveller's passport country (e.g., FRA, USA, JPN)"
    )
    destination: str = Field(
        description="ISO 3166-1 alpha-3 code of the destination country (e.g., THA, BRA, GBR)"
    )
    lang: str = Field(
        default="en",
        description=(
            "Language of the answer, available on every plan including free: "
            "en, fr, es, pt, de, it, ja, ko, zh, ru, ar, hi, th, vi, tl"
        ),
    )


class QuickVisaCheckInput(BaseModel):
    """Input for the quick visa check."""

    passport: str = Field(
        description="ISO 3166-1 alpha-3 code of the traveller's passport country"
    )
    destination: str = Field(
        description="ISO 3166-1 alpha-3 code of the destination country"
    )


class OriznVisaCheckTool(BaseTool):
    """Full visa requirements for one passport/destination pair (needs an API key)."""

    name: str = "orizn_visa_check"
    description: str = (
        "Authoritative visa requirements for one passport/destination pair. "
        "Call this whenever someone asks whether they need a visa, how long they may stay, "
        "which documents to prepare, what it costs, how long it takes, or the application steps — "
        "visa rules change, never answer from memory. "
        "Returns requirement type, visa-free days, description, documents, process, fees, "
        "processing time, validity and country info. "
        "199 passports x 202 destinations, 15 languages. Requires an API key "
        f"(free at {KEY_URL}). "
        "Use ISO 3166-1 alpha-3 country codes (FRA for France, JPN for Japan, USA for the United States)."
    )
    args_schema: Type[BaseModel] = VisaCheckInput

    api_key: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.environ.get("ORIZN_API_KEY")
        if not self.api_key:
            _warn_once()

    def _run(self, passport: str, destination: str, lang: str = "en") -> str:
        return _call_orizn(
            "/api/v1/visa",
            {
                "passport": passport.upper(),
                "destination": destination.upper(),
                "lang": lang,
            },
            self.api_key,
        )


class OriznQuickVisaCheckTool(BaseTool):
    """Quick visa yes/no for one passport/destination pair (needs an API key)."""

    name: str = "orizn_quick_visa_check"
    description: str = (
        "Fast visa yes/no for one passport/destination pair: requirement type "
        "(visa_free, visa_required, e_visa, visa_on_arrival, eta, no_admission), "
        "allowed stay in days, and the date the pair was last verified. "
        "Use this when the question is only 'do I need a visa and for how long'; "
        "use orizn_visa_check instead when documents, fees or the application process are asked for. "
        f"Requires an API key (free at {KEY_URL}). Use ISO 3166-1 alpha-3 codes."
    )
    args_schema: Type[BaseModel] = QuickVisaCheckInput

    api_key: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.environ.get("ORIZN_API_KEY")
        if not self.api_key:
            _warn_once()

    def _run(self, passport: str, destination: str) -> str:
        return _call_orizn(
            "/api/v1/visa/check",
            {
                "passport": passport.upper(),
                "destination": destination.upper(),
            },
            self.api_key,
        )

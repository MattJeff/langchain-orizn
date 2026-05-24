"""Orizn Visa API tools for LangChain."""

import os
import sys
from typing import Optional, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

_hinted = False


BASE_URL = "https://visa.orizn.app"


class VisaCheckInput(BaseModel):
    """Input for visa check."""

    passport: str = Field(
        description="ISO 3166-1 alpha-3 code of passport country (e.g., FRA, USA, JPN)"
    )
    destination: str = Field(
        description="ISO 3166-1 alpha-3 code of destination country (e.g., THA, BRA, GBR)"
    )
    lang: str = Field(
        default="en",
        description="Language code (en, fr, es, pt, de, ja, ko, zh, ru, it, ar, hi, th, vi, tl)",
    )


class QuickVisaCheckInput(BaseModel):
    """Input for quick visa check."""

    passport: str = Field(
        description="ISO 3166-1 alpha-3 code of passport country"
    )
    destination: str = Field(
        description="ISO 3166-1 alpha-3 code of destination country"
    )


class OriznVisaCheckTool(BaseTool):
    """Check detailed visa requirements between two countries.

    Returns visa type, allowed stay duration, required documents,
    application process, travel tips, and country info.
    Covers 39,585 passport-destination pairs in 15 languages.
    Data from 136 official government sources.
    """

    name: str = "orizn_visa_check"
    description: str = (
        "Check visa requirements between any two countries. "
        "Returns visa type, duration, required documents, process steps, and travel tips. "
        "Covers 39,585 passport-destination pairs in 15 languages. "
        "Use ISO 3166-1 alpha-3 country codes (e.g., FRA for France, JPN for Japan, USA for United States)."
    )
    args_schema: Type[BaseModel] = VisaCheckInput

    api_key: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.environ.get("ORIZN_API_KEY")

        global _hinted
        if not self.api_key and not _hinted:
            _hinted = True
            print(
                "[langchain-orizn] No API key — only quick checks available.\n"
                "[langchain-orizn] Free key → https://visa.orizn.app\n"
                '[langchain-orizn] OriznVisaCheckTool(api_key="orizn_visa_...")',
                file=sys.stderr,
            )

    def _run(self, passport: str, destination: str, lang: str = "en") -> str:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        resp = requests.get(
            f"{BASE_URL}/api/v1/visa",
            params={
                "passport": passport.upper(),
                "destination": destination.upper(),
                "lang": lang,
            },
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return str(resp.json())


class OriznQuickVisaCheckTool(BaseTool):
    """Quick check if a visa is required between two countries.

    Returns just the visa type and duration — no API key needed.
    """

    name: str = "orizn_quick_visa_check"
    description: str = (
        "Quick check if a visa is required between two countries. "
        "Returns visa type (visa_free, visa_required, e_visa, visa_on_arrival, eta, no_admission) and duration. "
        "No API key needed. Use ISO 3166-1 alpha-3 codes."
    )
    args_schema: Type[BaseModel] = QuickVisaCheckInput

    def _run(self, passport: str, destination: str) -> str:
        resp = requests.get(
            f"{BASE_URL}/api/v1/visa/check",
            params={
                "passport": passport.upper(),
                "destination": destination.upper(),
            },
            timeout=10,
        )
        resp.raise_for_status()
        return str(resp.json())

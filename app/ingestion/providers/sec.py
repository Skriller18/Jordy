from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.ingestion.http import HttpClient
from app.ingestion.types import SecFilingSignal


class SecProvider:
    def __init__(self, http_client: HttpClient | None = None) -> None:
        self.http = http_client or HttpClient()
        self._ticker_to_cik: dict[str, str] | None = None

    def _load_ticker_map(self) -> dict[str, str]:
        if self._ticker_to_cik is not None:
            return self._ticker_to_cik

        payload = self.http.get_json("https://www.sec.gov/files/company_tickers.json")
        mapping: dict[str, str] = {}
        if isinstance(payload, dict):
            for _, row in payload.items():
                if not isinstance(row, dict):
                    continue
                ticker = str(row.get("ticker") or "").upper().strip()
                cik = row.get("cik_str")
                if ticker and isinstance(cik, int):
                    mapping[ticker] = f"{cik:010d}"

        self._ticker_to_cik = mapping
        return mapping

    def _parse_recent_signal(self, submissions: dict[str, Any]) -> SecFilingSignal:
        filings = ((submissions.get("filings") or {}).get("recent") or {})
        forms = filings.get("form") or []
        dates = filings.get("filingDate") or []

        now = datetime.now(UTC).date()
        cutoff_30 = now - timedelta(days=30)
        cutoff_365 = now - timedelta(days=365)

        recent_8k = 0
        nt_flag = False

        for form, date_str in zip(forms, dates):
            if not isinstance(form, str) or not isinstance(date_str, str):
                continue
            try:
                filing_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            normalized = form.upper().strip()
            if filing_date >= cutoff_30 and normalized == "8-K":
                recent_8k += 1
            if filing_date >= cutoff_365 and normalized.startswith("NT "):
                nt_flag = True

        return SecFilingSignal(
            recent_8k_count_30d=recent_8k,
            has_recent_nt_filing=nt_flag,
        )

    def fetch_signal(self, ticker: str) -> SecFilingSignal:
        ticker_map = self._load_ticker_map()
        cik = ticker_map.get(ticker.upper().strip())
        if not cik:
            return SecFilingSignal()

        submissions = self.http.get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        if not isinstance(submissions, dict):
            return SecFilingSignal()

        return self._parse_recent_signal(submissions)

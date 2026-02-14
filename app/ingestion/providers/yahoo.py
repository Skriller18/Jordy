from __future__ import annotations

from typing import Any

from app.ingestion.http import HttpClient
from app.ingestion.types import MarketSnapshot
from app.models import Country, TickerTarget


def _get_numeric(payload: dict[str, Any], *path: str) -> float | None:
    node: Any = payload
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    if isinstance(node, dict):
        raw = node.get("raw")
        if isinstance(raw, (int, float)):
            return float(raw)
        return None
    if isinstance(node, (int, float)):
        return float(node)
    return None


class YahooProvider:
    def __init__(self, http_client: HttpClient | None = None) -> None:
        self.http = http_client or HttpClient()

    @staticmethod
    def resolve_symbol(target: TickerTarget) -> str:
        ticker = target.ticker.strip().upper()
        if target.yahoo_suffix:
            suffix = target.yahoo_suffix.strip()
            if not suffix.startswith("."):
                suffix = f".{suffix}"
            return f"{ticker}{suffix}"
        if target.country == Country.INDIA and "." not in ticker:
            return f"{ticker}.NS"
        return ticker

    def fetch_snapshot(self, target: TickerTarget) -> MarketSnapshot:
        symbol = self.resolve_symbol(target)

        summary = self.http.get_json(
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}",
            params={
                "modules": "assetProfile,price,defaultKeyStatistics,financialData,summaryDetail",
            },
        )
        chart = self.http.get_json(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"range": "1y", "interval": "1d"},
        )

        quote_result = (summary.get("quoteSummary") or {}).get("result") or []
        quote_data = quote_result[0] if quote_result else {}

        price = quote_data.get("price") or {}
        profile = quote_data.get("assetProfile") or {}

        chart_result = (chart.get("chart") or {}).get("result") or []
        chart_data = chart_result[0] if chart_result else {}
        quote_series = ((chart_data.get("indicators") or {}).get("quote") or [{}])[0]
        closes = [float(c) for c in (quote_series.get("close") or []) if isinstance(c, (int, float))]

        company_name = str(
            price.get("longName")
            or price.get("shortName")
            or profile.get("longBusinessSummary", "")[:60]
            or target.ticker.upper()
        )

        return MarketSnapshot(
            symbol=symbol,
            company_name=company_name,
            country=target.country,
            sector=str(profile.get("sector") or "Unknown"),
            industry=str(profile.get("industry") or "Unknown"),
            pe_ratio=_get_numeric(quote_data, "defaultKeyStatistics", "trailingPE")
            or _get_numeric(quote_data, "summaryDetail", "trailingPE"),
            pb_ratio=_get_numeric(quote_data, "defaultKeyStatistics", "priceToBook"),
            revenue_growth=_get_numeric(quote_data, "financialData", "revenueGrowth"),
            eps_growth=_get_numeric(quote_data, "financialData", "earningsGrowth"),
            roa=_get_numeric(quote_data, "financialData", "returnOnAssets"),
            debt_to_equity=_get_numeric(quote_data, "financialData", "debtToEquity"),
            closes=closes,
        )

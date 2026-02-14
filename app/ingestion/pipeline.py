from __future__ import annotations

from typing import List

from app.ingestion.feature_builder import build_company_input
from app.ingestion.providers.news import NewsProvider
from app.ingestion.providers.sec import SecProvider
from app.ingestion.providers.yahoo import YahooProvider
from app.models import CompanyInput, Country, TickerTarget


class IngestionPipeline:
    def __init__(
        self,
        yahoo: YahooProvider | None = None,
        news: NewsProvider | None = None,
        sec: SecProvider | None = None,
    ) -> None:
        self.yahoo = yahoo or YahooProvider()
        self.news = news or NewsProvider()
        self.sec = sec or SecProvider()

    def ingest_targets(self, targets: List[TickerTarget], news_items: int = 10) -> tuple[List[CompanyInput], List[str]]:
        companies: List[CompanyInput] = []
        warnings: List[str] = []

        for target in targets:
            try:
                snapshot = self.yahoo.fetch_snapshot(target)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{target.ticker}: market/fundamental fetch failed ({exc})")
                continue

            sentiment = 0.0
            try:
                sentiment, _ = self.news.fetch_sentiment(snapshot.company_name, limit=news_items)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{target.ticker}: news sentiment fetch failed ({exc})")

            sec_signal = None
            if target.country == Country.USA:
                try:
                    sec_signal = self.sec.fetch_signal(target.ticker)
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"{target.ticker}: SEC filing fetch failed ({exc})")

            try:
                company = build_company_input(
                    target=target,
                    snapshot=snapshot,
                    sentiment=sentiment,
                    sec_signal=sec_signal,
                )
                companies.append(company)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{target.ticker}: feature build failed ({exc})")

        return companies, warnings

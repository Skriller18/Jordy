from __future__ import annotations

from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.types import MarketSnapshot, SecFilingSignal
from app.models import Country, TickerTarget


class FakeYahoo:
    def fetch_snapshot(self, target: TickerTarget) -> MarketSnapshot:
        closes = [100 + i * 0.5 for i in range(260)]
        return MarketSnapshot(
            symbol=target.ticker,
            company_name=f"{target.ticker} Corp",
            country=target.country,
            sector="Technology",
            industry="Software",
            pe_ratio=22.0,
            pb_ratio=4.0,
            revenue_growth=0.12,
            eps_growth=0.15,
            roa=0.14,
            debt_to_equity=85.0,
            closes=closes,
        )


class FakeNews:
    def fetch_sentiment(self, query: str, limit: int = 10) -> tuple[float, list[str]]:
        return 0.25, ["Strong growth and profit outlook"]


class FakeSec:
    def fetch_signal(self, ticker: str) -> SecFilingSignal:
        return SecFilingSignal(recent_8k_count_30d=2, has_recent_nt_filing=False)


class BrokenYahoo:
    def fetch_snapshot(self, target: TickerTarget) -> MarketSnapshot:
        raise RuntimeError("network down")


class BrokenNews:
    def fetch_sentiment(self, query: str, limit: int = 10) -> tuple[float, list[str]]:
        raise RuntimeError("rss blocked")


def test_ingestion_pipeline_builds_company_inputs() -> None:
    pipeline = IngestionPipeline(yahoo=FakeYahoo(), news=FakeNews(), sec=FakeSec())
    targets = [TickerTarget(ticker="AAPL", country=Country.USA)]

    companies, warnings = pipeline.ingest_targets(targets)

    assert len(companies) == 1
    assert warnings == []
    company = companies[0]

    # debtToEquity values often arrive as percentages from providers.
    assert 0.84 <= company.quant.debt_to_equity <= 0.86
    assert company.quant.price_momentum_6m_pct > 0
    assert company.quant.volatility_30d_pct >= 0
    assert company.qual.sentiment_score == 0.25


def test_ingestion_pipeline_collects_source_warnings() -> None:
    pipeline = IngestionPipeline(yahoo=BrokenYahoo(), news=BrokenNews(), sec=FakeSec())
    targets = [TickerTarget(ticker="TCS", country=Country.INDIA)]

    companies, warnings = pipeline.ingest_targets(targets)

    assert companies == []
    assert len(warnings) == 1
    assert "market/fundamental fetch failed" in warnings[0]

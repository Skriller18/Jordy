from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class Country(str, Enum):
    USA = "USA"
    INDIA = "INDIA"


class Horizon(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class QuantMetrics(BaseModel):
    pe_ratio: float = Field(..., ge=-200, le=500)
    pb_ratio: float = Field(..., ge=0, le=100)
    revenue_growth_pct: float = Field(..., ge=-100, le=300)
    eps_growth_pct: float = Field(..., ge=-300, le=500)
    roa_pct: float = Field(..., ge=-100, le=100)
    debt_to_equity: float = Field(..., ge=0, le=20)
    price_momentum_6m_pct: float = Field(..., ge=-100, le=300)
    volatility_30d_pct: float = Field(..., ge=0, le=300)


class QualMetrics(BaseModel):
    management_score: float = Field(..., ge=0, le=10)
    moat_score: float = Field(..., ge=0, le=10)
    governance_score: float = Field(..., ge=0, le=10)
    regulatory_risk_score: float = Field(..., ge=0, le=10)
    sentiment_score: float = Field(..., ge=-1, le=1)


class CompanyInput(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=30)
    company_name: str = Field(..., min_length=1, max_length=120)
    country: Country
    sector: str = Field(..., min_length=1, max_length=60)
    industry: str = Field(..., min_length=1, max_length=80)
    quant: QuantMetrics
    qual: QualMetrics


class ScoreBreakdown(BaseModel):
    quant_score: float
    qual_score: float
    composite_score: float
    quant_components: Dict[str, float]
    qual_components: Dict[str, float]


class RankedIdea(BaseModel):
    ticker: str
    company_name: str
    country: Country
    sector: str
    industry: str
    recommendation: Literal["strong_candidate", "watchlist", "avoid"]
    score: ScoreBreakdown
    positives: List[str]
    negatives: List[str]
    risk_notes: List[str]


class RankRequest(BaseModel):
    horizon: Horizon = Horizon.LONG_TERM
    companies: List[CompanyInput] = Field(..., min_length=1)


class RankResponse(BaseModel):
    horizon: Horizon
    results: List[RankedIdea]
    disclaimer: str


class TickerTarget(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=30)
    country: Country
    yahoo_suffix: str | None = Field(
        default=None,
        description="Optional explicit Yahoo suffix, e.g. '.NS' for NSE tickers",
    )


class IngestRankRequest(BaseModel):
    horizon: Horizon = Horizon.LONG_TERM
    targets: List[TickerTarget] = Field(..., min_length=1)
    news_items: int = Field(default=10, ge=1, le=50)


class IngestRankResponse(RankResponse):
    ingested_count: int
    warnings: List[str] = Field(default_factory=list)

from __future__ import annotations

from dataclasses import dataclass, field

from app.models import Country


@dataclass
class MarketSnapshot:
    symbol: str
    company_name: str
    country: Country
    sector: str
    industry: str
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    revenue_growth: float | None = None
    eps_growth: float | None = None
    roa: float | None = None
    debt_to_equity: float | None = None
    closes: list[float] = field(default_factory=list)


@dataclass
class NewsSignal:
    sentiment: float
    headlines: list[str] = field(default_factory=list)


@dataclass
class SecFilingSignal:
    recent_8k_count_30d: int = 0
    has_recent_nt_filing: bool = False

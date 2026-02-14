from __future__ import annotations

import math
import statistics

from app.ingestion.types import MarketSnapshot, SecFilingSignal
from app.models import CompanyInput, Country, QualMetrics, QuantMetrics, TickerTarget


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _percent_value(raw: float | None, default: float) -> float:
    if raw is None:
        return default
    if -2 <= raw <= 2:
        return raw * 100
    return raw


def _de_ratio(raw: float | None, default: float) -> float:
    if raw is None:
        return default
    if raw > 20:
        return raw / 100.0
    return raw


def _calc_momentum_6m(closes: list[float]) -> float:
    if len(closes) < 2:
        return 0.0

    lookback = 126
    if len(closes) > lookback:
        reference = closes[-lookback - 1]
    else:
        reference = closes[0]

    latest = closes[-1]
    if reference <= 0:
        return 0.0
    return ((latest / reference) - 1.0) * 100.0


def _calc_volatility_30d(closes: list[float]) -> float:
    if len(closes) < 31:
        return 25.0

    window = closes[-31:]
    returns: list[float] = []
    for prev, nxt in zip(window, window[1:]):
        if prev <= 0 or nxt <= 0:
            continue
        returns.append((nxt / prev) - 1.0)

    if len(returns) < 2:
        return 25.0

    daily_vol = statistics.pstdev(returns)
    annualized = daily_vol * math.sqrt(252.0) * 100.0
    return annualized


def _qual_scores(
    target: TickerTarget,
    revenue_growth_pct: float,
    eps_growth_pct: float,
    roa_pct: float,
    debt_to_equity: float,
    sentiment: float,
    sec_signal: SecFilingSignal | None,
) -> QualMetrics:
    management = 5.0 + _clamp((roa_pct - 6.0) / 6.0, -2.0, 2.0) + _clamp(eps_growth_pct / 30.0, -1.5, 1.5)
    moat = 5.0 + _clamp((roa_pct - 8.0) / 8.0, -1.8, 1.8) + _clamp(revenue_growth_pct / 35.0, -1.0, 1.0)
    governance = 6.0 - _clamp((debt_to_equity - 1.0) * 0.8, -1.5, 2.5)

    if target.country == Country.USA:
        regulatory = 4.3
    else:
        regulatory = 5.0

    if sec_signal:
        regulatory += min(2.0, sec_signal.recent_8k_count_30d * 0.4)
        if sec_signal.has_recent_nt_filing:
            regulatory += 1.5

    return QualMetrics(
        management_score=round(_clamp(management, 0.0, 10.0), 2),
        moat_score=round(_clamp(moat, 0.0, 10.0), 2),
        governance_score=round(_clamp(governance, 0.0, 10.0), 2),
        regulatory_risk_score=round(_clamp(regulatory, 0.0, 10.0), 2),
        sentiment_score=round(_clamp(sentiment, -1.0, 1.0), 3),
    )


def build_company_input(
    target: TickerTarget,
    snapshot: MarketSnapshot,
    sentiment: float,
    sec_signal: SecFilingSignal | None = None,
) -> CompanyInput:
    pe_ratio = snapshot.pe_ratio if snapshot.pe_ratio is not None else 25.0
    pb_ratio = snapshot.pb_ratio if snapshot.pb_ratio is not None else 3.5

    revenue_growth_pct = _percent_value(snapshot.revenue_growth, default=6.0)
    eps_growth_pct = _percent_value(snapshot.eps_growth, default=5.0)
    roa_pct = _percent_value(snapshot.roa, default=8.0)
    debt_to_equity = _de_ratio(snapshot.debt_to_equity, default=0.8)

    momentum_6m = _calc_momentum_6m(snapshot.closes)
    vol_30d = _calc_volatility_30d(snapshot.closes)

    quant = QuantMetrics(
        pe_ratio=round(_clamp(pe_ratio, -200.0, 500.0), 2),
        pb_ratio=round(_clamp(pb_ratio, 0.0, 100.0), 2),
        revenue_growth_pct=round(_clamp(revenue_growth_pct, -100.0, 300.0), 2),
        eps_growth_pct=round(_clamp(eps_growth_pct, -300.0, 500.0), 2),
        roa_pct=round(_clamp(roa_pct, -100.0, 100.0), 2),
        debt_to_equity=round(_clamp(debt_to_equity, 0.0, 20.0), 3),
        price_momentum_6m_pct=round(_clamp(momentum_6m, -100.0, 300.0), 2),
        volatility_30d_pct=round(_clamp(vol_30d, 0.0, 300.0), 2),
    )

    qual = _qual_scores(
        target=target,
        revenue_growth_pct=quant.revenue_growth_pct,
        eps_growth_pct=quant.eps_growth_pct,
        roa_pct=quant.roa_pct,
        debt_to_equity=quant.debt_to_equity,
        sentiment=sentiment,
        sec_signal=sec_signal,
    )

    return CompanyInput(
        ticker=target.ticker.upper(),
        company_name=snapshot.company_name,
        country=target.country,
        sector=snapshot.sector,
        industry=snapshot.industry,
        quant=quant,
        qual=qual,
    )

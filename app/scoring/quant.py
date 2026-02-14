from __future__ import annotations

from typing import Dict, List, Tuple

from app.models import Horizon, QuantMetrics
from app.scoring.utils import linear_score


def score_quant(metrics: QuantMetrics, horizon: Horizon) -> Tuple[float, Dict[str, float], List[str], List[str]]:
    valuation = (linear_score(metrics.pe_ratio, 5, 40, higher_is_better=False) * 0.6) + (
        linear_score(metrics.pb_ratio, 0.8, 12, higher_is_better=False) * 0.4
    )

    growth = (linear_score(metrics.revenue_growth_pct, -20, 35, higher_is_better=True) * 0.5) + (
        linear_score(metrics.eps_growth_pct, -30, 45, higher_is_better=True) * 0.5
    )

    quality = (linear_score(metrics.roa_pct, -5, 20, higher_is_better=True) * 0.6) + (
        linear_score(metrics.debt_to_equity, 0.0, 2.5, higher_is_better=False) * 0.4
    )

    momentum = linear_score(metrics.price_momentum_6m_pct, -30, 40, higher_is_better=True)
    stability = linear_score(metrics.volatility_30d_pct, 10, 70, higher_is_better=False)

    if horizon == Horizon.SHORT_TERM:
        weights = {
            "valuation": 0.15,
            "growth": 0.20,
            "quality": 0.15,
            "momentum": 0.30,
            "stability": 0.20,
        }
    else:
        weights = {
            "valuation": 0.25,
            "growth": 0.25,
            "quality": 0.25,
            "momentum": 0.15,
            "stability": 0.10,
        }

    components = {
        "valuation": valuation,
        "growth": growth,
        "quality": quality,
        "momentum": momentum,
        "stability": stability,
    }

    score = sum(components[name] * weight for name, weight in weights.items())

    positives: List[str] = []
    negatives: List[str] = []

    if metrics.pe_ratio > 0 and metrics.pe_ratio < 20:
        positives.append("Reasonable earnings valuation (P/E below 20)")
    if metrics.pb_ratio < 4:
        positives.append("Book valuation is not stretched")
    if metrics.revenue_growth_pct > 12:
        positives.append("Healthy revenue growth")
    if metrics.eps_growth_pct > 12:
        positives.append("Strong EPS growth")
    if metrics.roa_pct > 8:
        positives.append("Strong return on assets")
    if metrics.debt_to_equity < 0.8:
        positives.append("Conservative leverage")
    if metrics.price_momentum_6m_pct > 10:
        positives.append("Positive 6-month momentum")

    if metrics.pe_ratio < 0:
        negatives.append("Negative earnings (P/E below 0)")
    elif metrics.pe_ratio > 35:
        negatives.append("Expensive earnings valuation (P/E above 35)")
    if metrics.pb_ratio > 8:
        negatives.append("High price-to-book multiple")
    if metrics.revenue_growth_pct < 0:
        negatives.append("Negative revenue growth")
    if metrics.eps_growth_pct < 0:
        negatives.append("Negative EPS growth")
    if metrics.roa_pct < 3:
        negatives.append("Weak return on assets")
    if metrics.debt_to_equity > 1.8:
        negatives.append("High leverage risk")
    if metrics.volatility_30d_pct > 45:
        negatives.append("Elevated short-term volatility")

    return round(score, 2), {k: round(v, 2) for k, v in components.items()}, positives, negatives

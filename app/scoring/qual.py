from __future__ import annotations

from typing import Dict, List, Tuple

from app.models import Horizon, QualMetrics
from app.scoring.utils import linear_score


def score_qual(metrics: QualMetrics, horizon: Horizon) -> Tuple[float, Dict[str, float], List[str], List[str]]:
    management = linear_score(metrics.management_score, 0, 10, higher_is_better=True)
    moat = linear_score(metrics.moat_score, 0, 10, higher_is_better=True)
    governance = linear_score(metrics.governance_score, 0, 10, higher_is_better=True)
    regulatory = linear_score(metrics.regulatory_risk_score, 0, 10, higher_is_better=False)
    sentiment = linear_score(metrics.sentiment_score, -1, 1, higher_is_better=True)

    if horizon == Horizon.SHORT_TERM:
        weights = {
            "management": 0.15,
            "moat": 0.15,
            "governance": 0.20,
            "regulatory": 0.20,
            "sentiment": 0.30,
        }
    else:
        weights = {
            "management": 0.25,
            "moat": 0.30,
            "governance": 0.25,
            "regulatory": 0.15,
            "sentiment": 0.05,
        }

    components = {
        "management": management,
        "moat": moat,
        "governance": governance,
        "regulatory": regulatory,
        "sentiment": sentiment,
    }

    score = sum(components[name] * weight for name, weight in weights.items())

    positives: List[str] = []
    negatives: List[str] = []

    if metrics.management_score >= 7:
        positives.append("Management quality signal is strong")
    if metrics.moat_score >= 7:
        positives.append("Durable competitive moat signal")
    if metrics.governance_score >= 7:
        positives.append("Good governance signal")
    if metrics.regulatory_risk_score <= 3:
        positives.append("Low regulatory overhang")
    if metrics.sentiment_score > 0.2:
        positives.append("Constructive market/news sentiment")

    if metrics.management_score <= 4:
        negatives.append("Management quality concerns")
    if metrics.moat_score <= 4:
        negatives.append("Weak moat or differentiation")
    if metrics.governance_score <= 4:
        negatives.append("Governance concerns")
    if metrics.regulatory_risk_score >= 7:
        negatives.append("High regulatory risk")
    if metrics.sentiment_score < -0.2:
        negatives.append("Negative market/news sentiment")

    return round(score, 2), {k: round(v, 2) for k, v in components.items()}, positives, negatives

from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def linear_score(
    value: float,
    low: float,
    high: float,
    *,
    higher_is_better: bool,
) -> float:
    if high == low:
        return 50.0

    ratio = (value - low) / (high - low)
    score = ratio * 100.0
    if not higher_is_better:
        score = 100.0 - score
    return clamp(score)

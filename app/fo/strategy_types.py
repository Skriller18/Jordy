from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class StrategyPickModel(BaseModel):
    underlying: str
    strategy: str
    risk: Literal["low", "medium", "high"]
    expected_edge: str
    score: float
    rationale: List[str]
    key_metrics: Dict[str, Any]


class StrategiesRunRequest(BaseModel):
    underlyings: List[str] = Field(..., min_length=1)
    horizon: Literal["short_term", "long_term"] = "short_term"
    expiry_date: Optional[str] = None  # YYYY-MM-DD


class StrategiesRunResponse(BaseModel):
    disclaimer: str

    # Profit-seeking (may include high-risk strategies)
    best_overall: StrategyPickModel

    # Conservative best pick (defined-risk preference)
    best_min_risk: StrategyPickModel

    results: List[StrategyPickModel]
    warnings: List[str]


class StrategiesUniverseResponse(BaseModel):
    strategies: List[str]
    risk_levels: List[str]
    supported_underlyings: List[str]

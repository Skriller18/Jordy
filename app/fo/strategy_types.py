from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from app.fo.strategy_explain_types import StrategyExplanationModel

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

    # If true, compute explanations + proxy backtests for top picks.
    include_explanations: bool = False


class StrategiesRunResponse(BaseModel):
    disclaimer: str

    # Profit-seeking (may include high-risk strategies)
    best_overall: StrategyPickModel

    # Conservative best pick (defined-risk preference)
    best_min_risk: StrategyPickModel

    # Optional explainability payload for the top picks.
    best_overall_explain: StrategyExplanationModel | None = None
    best_min_risk_explain: StrategyExplanationModel | None = None

    results: List[StrategyPickModel]
    warnings: List[str]


class StrategiesUniverseResponse(BaseModel):
    strategies: List[str]
    risk_levels: List[str]
    supported_underlyings: List[str]

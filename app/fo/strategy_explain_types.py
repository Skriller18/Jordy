from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ProxyBacktestModel(BaseModel):
    horizon_days: int
    samples: int
    avg_return_pct: float
    median_return_pct: float
    win_rate_pct: float
    worst_return_pct: float
    best_return_pct: float


class StrategyExplanationModel(BaseModel):
    underlying: str
    strategy: str
    hypothesis: List[str]
    assumptions: List[str]
    failure_modes: List[str]
    proxy_backtests: List[ProxyBacktestModel]
    notes: List[str]

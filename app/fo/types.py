from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class FoHorizon(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class IndexKey(str, Enum):
    NIFTY = "NIFTY"
    SENSEX = "SENSEX"


class FoUniverseResponse(BaseModel):
    indices: List[IndexKey]
    nifty50: List[str]


class UnderlyingSnapshot(BaseModel):
    trading_symbol: str
    exchange: Literal["NSE", "BSE"]
    segment: Literal["CASH", "FNO"]
    last_price: Optional[float] = None
    ohlc: Optional[Dict[str, float]] = None
    day_change_perc: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class IndicesSnapshotResponse(BaseModel):
    as_of_epoch_ms: int
    indices: Dict[IndexKey, UnderlyingSnapshot]
    warnings: List[str] = Field(default_factory=list)


class Nifty50SnapshotRow(BaseModel):
    ticker: str
    exchange: Literal["NSE", "BSE"] = "NSE"
    last_price: Optional[float] = None
    day_change_perc: Optional[float] = None


class Nifty50SnapshotResponse(BaseModel):
    as_of_epoch_ms: int
    rows: List[Nifty50SnapshotRow]
    warnings: List[str] = Field(default_factory=list)

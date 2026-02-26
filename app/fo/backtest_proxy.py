from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


def _pct_change(a: float, b: float) -> float:
    if a == 0:
        return 0.0
    return (b / a) - 1.0


def _stdev(xs: List[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    return math.sqrt(var)


def realized_vol_pct(closes: List[float], window: int = 20) -> List[Optional[float]]:
    """Compute realized vol (%) from daily closes using log returns.

    Returns a list aligned to closes with Nones for the initial period.
    """

    if len(closes) < window + 1:
        return [None for _ in closes]

    # log returns
    rets: List[float] = [0.0]
    for i in range(1, len(closes)):
        a = float(closes[i - 1])
        b = float(closes[i])
        if a <= 0 or b <= 0:
            rets.append(0.0)
        else:
            rets.append(math.log(b / a))

    vols: List[Optional[float]] = [None] * len(closes)
    for i in range(window, len(closes)):
        w = rets[i - window + 1 : i + 1]
        vol_daily = _stdev(w)
        vol_annual = vol_daily * math.sqrt(252)
        vols[i] = vol_annual * 100.0

    return vols


@dataclass
class ProxyBacktestResult:
    horizon_days: int
    samples: int
    avg_return_pct: float
    median_return_pct: float
    win_rate_pct: float
    worst_return_pct: float
    best_return_pct: float


def _median(xs: List[float]) -> float:
    xs2 = sorted(xs)
    n = len(xs2)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return xs2[mid]
    return 0.5 * (xs2[mid - 1] + xs2[mid])


def proxy_forward_returns(
    closes: List[float],
    *,
    match_vol_range: Tuple[float, float],
    horizon_days: int,
    vol_window: int = 20,
) -> ProxyBacktestResult:
    """Proxy backtest: filter history by realized-vol regime and measure forward underlying returns.

    NOTE: This is NOT options P&L backtesting. It only backtests the underlying's forward returns
    conditional on volatility regime.
    """

    vols = realized_vol_pct(closes, window=vol_window)
    lo, hi = match_vol_range

    fwd: List[float] = []
    for i in range(len(closes) - horizon_days):
        v = vols[i]
        if v is None:
            continue
        if not (lo <= v <= hi):
            continue
        a = float(closes[i])
        b = float(closes[i + horizon_days])
        fwd.append(_pct_change(a, b) * 100.0)

    if not fwd:
        return ProxyBacktestResult(
            horizon_days=horizon_days,
            samples=0,
            avg_return_pct=0.0,
            median_return_pct=0.0,
            win_rate_pct=0.0,
            worst_return_pct=0.0,
            best_return_pct=0.0,
        )

    avg = sum(fwd) / len(fwd)
    med = _median(fwd)
    wins = sum(1 for x in fwd if x > 0)
    return ProxyBacktestResult(
        horizon_days=horizon_days,
        samples=len(fwd),
        avg_return_pct=avg,
        median_return_pct=med,
        win_rate_pct=(wins / len(fwd)) * 100.0,
        worst_return_pct=min(fwd),
        best_return_pct=max(fwd),
    )

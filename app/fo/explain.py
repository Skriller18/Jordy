from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.fo.backtest_proxy import ProxyBacktestResult, proxy_forward_returns, realized_vol_pct


@dataclass
class StrategyExplanation:
    underlying: str
    strategy: str
    hypothesis: List[str]
    assumptions: List[str]
    failure_modes: List[str]
    proxy_backtests: List[ProxyBacktestResult]
    notes: List[str]


def _vol_band(vols: list[float], current: float) -> Tuple[float, float]:
    # Use a simple +/- 25% band around current, with a minimum width.
    lo = max(0.0, current * 0.75)
    hi = current * 1.25
    if hi - lo < 2.0:
        lo = max(0.0, current - 1.0)
        hi = current + 1.0
    return lo, hi


def build_explanation(
    *,
    underlying: str,
    strategy: str,
    key_metrics: Dict[str, Any],
    closes: List[float],
    backtest_days: int = 252,
) -> StrategyExplanation:
    hyp: List[str] = []
    assumptions: List[str] = []
    failures: List[str] = []
    notes: List[str] = []

    atm_iv = key_metrics.get("atm_iv")
    pcr = key_metrics.get("pcr")

    # General regime hypothesis
    if isinstance(atm_iv, (int, float)):
        hyp.append(f"ATM implied vol is ~{float(atm_iv):.1f} (proxy for option premium richness).")
        if float(atm_iv) >= 18:
            hyp.append("High IV regime: premium-selling structures tend to have positive expectancy if realized volatility stays lower than implied.")
        elif float(atm_iv) <= 12:
            hyp.append("Low IV regime: long-vol structures can benefit if realized volatility expands.")
        else:
            hyp.append("Mid IV regime: defined-risk premium strategies may be preferred.")
    else:
        hyp.append("Implied vol not available; strategy selection falls back to conservative heuristics.")

    if isinstance(pcr, (int, float)):
        hyp.append(f"PCR is ~{float(pcr):.2f} (rough positioning / skew proxy).")

    # Strategy-specific framing
    if strategy in ("short_strangle", "iron_condor"):
        assumptions += [
            "Underlying remains range-bound or mean-reverting over the holding window.",
            "Implied volatility is priced above subsequent realized volatility.",
            "You can manage tail risk with position sizing and stop rules.",
        ]
        failures += [
            "Large directional trend / gap moves.",
            "Volatility expansion after entry.",
            "Liquidity/margin shocks.",
        ]
    elif strategy in ("call_ratio_spread", "put_ratio_spread"):
        assumptions += [
            "Implied volatility is very high and likely to mean-revert (IV crush helps).",
            "Directional move is limited/moderate; extreme tail moves are rare over the holding window.",
            "You size the position to survive adverse tails and understand assignment/margin behavior.",
        ]
        failures += [
            "Large tail move beyond the short strike region (ratio spreads can have convex/unbounded risk depending on construction).",
            "Volatility expands further after entry.",
            "Liquidity/margin shocks or early assignment impacts.",
        ]
    elif strategy in ("bull_put_spread", "bear_call_spread"):
        assumptions += [
            "Directional bias is mild-to-moderate (trend or mean reversion).",
            "Defined-risk spread width is chosen to keep max loss acceptable.",
        ]
        failures += [
            "Strong move against the spread direction.",
            "Entry at poor volatility level (selling too cheap / buying too expensive).",
        ]
    elif strategy in ("covered_call", "cash_secured_put"):
        assumptions += [
            "You are comfortable owning/holding the underlying (or getting assigned).",
            "Income is prioritized over uncapped upside.",
        ]
        failures += [
            "Sharp drawdown in the underlying (for CSP).",
            "Big rally that caps upside (for CC).",
        ]
    elif strategy == "long_straddle":
        assumptions += [
            "A volatility event is likely and will exceed implied vol.",
            "You can exit quickly if IV crush happens.",
        ]
        failures += [
            "IV crush / time decay dominates.",
            "Range-bound underlying.",
        ]

    # Proxy backtest using realized-vol regime (underlying-only)
    # Keep the backtest window bounded (default: last 252 trading days), while ensuring
    # we have enough lookback for vol_window and forward horizons.
    max_h = 20
    vol_window = 20
    need = backtest_days + vol_window + max_h + 1
    closes_bt = closes[-need:] if len(closes) > need else closes

    proxy: List[ProxyBacktestResult] = []
    vols = realized_vol_pct(closes_bt, window=vol_window)
    curr = None
    for v in reversed(vols):
        if v is not None:
            curr = float(v)
            break

    if curr is None:
        notes.append("Not enough price history to compute realized volatility proxy backtest.")
    else:
        lo, hi = _vol_band([x for x in vols if x is not None], curr)
        notes.append(f"Proxy backtest conditioned on realized vol ~{curr:.1f}% (band {lo:.1f}-{hi:.1f}%).")
        # 5d and 20d forward returns
        proxy.append(proxy_forward_returns(closes_bt, match_vol_range=(lo, hi), horizon_days=5, vol_window=vol_window))
        proxy.append(proxy_forward_returns(closes_bt, match_vol_range=(lo, hi), horizon_days=20, vol_window=vol_window))

    notes.append("Proxy backtest measures underlying forward returns, NOT options strategy P&L.")

    return StrategyExplanation(
        underlying=underlying,
        strategy=strategy,
        hypothesis=hyp,
        assumptions=assumptions,
        failure_modes=failures,
        proxy_backtests=proxy,
        notes=notes,
    )

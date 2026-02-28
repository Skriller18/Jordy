from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StrategyPick:
    underlying: str
    strategy: str
    risk: str  # low|medium|high
    expected_edge: str  # qualitative
    score: float
    rationale: List[str]
    key_metrics: Dict[str, Any]


def _nearest_strike(strikes: List[int], ltp: float) -> int:
    return min(strikes, key=lambda s: abs(float(s) - float(ltp)))


def _strike_step(strikes: List[float], atm: float) -> float:
    """Estimate the strike interval around ATM."""

    if not strikes or len(strikes) < 2:
        return 50.0
    xs = sorted(float(x) for x in strikes)
    # find nearest index
    idx = min(range(len(xs)), key=lambda i: abs(xs[i] - float(atm)))
    # look at local diffs
    diffs: List[float] = []
    for j in range(max(1, idx - 5), min(len(xs), idx + 6)):
        diffs.append(abs(xs[j] - xs[j - 1]))
    diffs = [d for d in diffs if d > 0]
    if not diffs:
        return 50.0
    diffs.sort()
    return float(diffs[len(diffs) // 2])


def _pick_nearest(xs: List[float], target: float) -> float:
    return min(xs, key=lambda v: abs(float(v) - float(target)))


def strikes_considered(*, strategy: str, strike_prices: List[float], atm_strike: float) -> List[float]:
    """Choose a small set of strikes that the strategy would typically use.

    Note: this is a heuristic mapping used for display/explainability.
    """

    xs = sorted(float(x) for x in (strike_prices or []))
    if not xs:
        return []

    step = _strike_step(xs, atm_strike)

    def near(t: float) -> float:
        return _pick_nearest(xs, t)

    # Offsets expressed in strike steps around ATM
    if strategy == "long_straddle":
        return [near(atm_strike)]

    if strategy == "cash_secured_put":
        return [near(atm_strike - 1 * step)]

    if strategy == "covered_call":
        return [near(atm_strike + 1 * step)]

    if strategy == "bull_put_spread":
        sp = near(atm_strike - 1 * step)
        lp = near(atm_strike - 3 * step)
        return sorted({sp, lp})

    if strategy == "bear_call_spread":
        sc = near(atm_strike + 1 * step)
        lc = near(atm_strike + 3 * step)
        return sorted({sc, lc})

    if strategy == "iron_condor":
        sp = near(atm_strike - 1 * step)
        lp = near(atm_strike - 3 * step)
        sc = near(atm_strike + 1 * step)
        lc = near(atm_strike + 3 * step)
        return sorted({sp, lp, sc, lc})

    if strategy == "short_strangle":
        sp = near(atm_strike - 2 * step)
        sc = near(atm_strike + 2 * step)
        return sorted({sp, sc})

    if strategy == "call_ratio_spread":
        sc = near(atm_strike + 1 * step)
        bc = near(atm_strike + 3 * step)
        return sorted({sc, bc})

    if strategy == "put_ratio_spread":
        sp = near(atm_strike - 1 * step)
        bp = near(atm_strike - 3 * step)
        return sorted({sp, bp})

    return []


def summarize_nse_chain(nse: dict) -> dict:
    """Extract usable metrics from NSE option chain response."""

    records = ((nse.get("records") or {}).get("data") or [])
    if not isinstance(records, list) or not records:
        return {"records": 0}

    underlying = (nse.get("records") or {}).get("underlyingValue")
    if not isinstance(underlying, (int, float)):
        return {"records": len(records)}

    strikes: List[int] = []
    p_oi = 0.0
    c_oi = 0.0
    atm_iv = None
    for row in records:
        try:
            sp = int(row.get("strikePrice"))
            strikes.append(sp)
        except Exception:
            continue

        ce = row.get("CE") if isinstance(row, dict) else None
        pe = row.get("PE") if isinstance(row, dict) else None
        if isinstance(ce, dict):
            c_oi += float(ce.get("openInterest") or 0.0)
        if isinstance(pe, dict):
            p_oi += float(pe.get("openInterest") or 0.0)

    strikes = sorted(set(strikes))
    if not strikes:
        return {"underlying": underlying, "records": len(records)}

    atm = _nearest_strike(strikes, float(underlying))
    # try compute ATM IV from CE/PE if available
    for row in records:
        if int(row.get("strikePrice", -1)) != atm:
            continue
        ce = row.get("CE") if isinstance(row, dict) else None
        pe = row.get("PE") if isinstance(row, dict) else None
        ivs: List[float] = []
        for side in (ce, pe):
            if isinstance(side, dict) and isinstance(side.get("impliedVolatility"), (int, float)):
                ivs.append(float(side.get("impliedVolatility")))
        if ivs:
            atm_iv = sum(ivs) / len(ivs)
        break

    pcr = (p_oi / c_oi) if c_oi > 0 else None

    return {
        "underlying": float(underlying),
        "atm_strike": atm,
        "atm_iv": atm_iv,
        "pcr": pcr,
        "call_oi": c_oi,
        "put_oi": p_oi,
        # strike ladder available in the chain
        "strike_prices": [float(s) for s in strikes],
        "records": len(records),
    }


def pick_strategy(metrics: dict, *, horizon: str = "short_term") -> StrategyPick:
    """Pick a strategy based on rough option-chain conditions.

    This is research-only heuristics, NOT advice.
    """

    und = metrics.get("underlying")
    if not isinstance(und, (int, float)):
        msg = "Option chain data unavailable; cannot compute strategy."
        if metrics.get("groww_strikes_present"):
            msg = (
                "Groww option chain returned strikes, but we haven't normalized/parsed Groww strikes yet. "
                "(Implementation pending.)"
            )
        return StrategyPick(
            underlying=str(metrics.get("symbol") or "UNKNOWN"),
            strategy="no_data",
            risk="low",
            expected_edge="none",
            score=0.0,
            rationale=[msg],
            key_metrics=metrics,
        )

    atm_iv = metrics.get("atm_iv")
    pcr = metrics.get("pcr")
    iv_pct = metrics.get("iv_percentile")

    # Defaults
    strategy = "cash_secured_put"
    risk = "medium"
    edge = "income"
    score = 50.0
    rationale: List[str] = []

    # Prefer IV percentile when available (relative regime), else fall back to absolute IV thresholds.
    if isinstance(iv_pct, (int, float)):
        pct = float(iv_pct)
        rationale.append(f"IV percentile ~{pct:.0f} (vs stored history)")

        if pct >= 90:
            rationale.append("IV is in an extreme high percentile; prefer ratio spreads / premium-selling with convex protection")
            if pcr is not None and pcr >= 1.0:
                strategy = "put_ratio_spread"
            elif pcr is not None and pcr <= 0.9:
                strategy = "call_ratio_spread"
            else:
                # balanced: defined-risk neutral structure
                strategy = "iron_condor"
                risk = "medium"
            edge = "premium_capture_with_wings"
            score = 78.0

        elif pct >= 70:
            rationale.append("High IV percentile; premium selling favored, prefer defined-risk")
            if pcr is not None and 0.8 <= pcr <= 1.2:
                strategy = "iron_condor" if horizon == "long_term" else "short_strangle"
                risk = "medium" if strategy == "iron_condor" else "high"
                edge = "premium_capture"
                score = 70.0
            else:
                strategy = "bear_call_spread" if (pcr is not None and pcr < 0.9) else "bull_put_spread"
                risk = "medium"
                edge = "defined_risk_premium"
                score = 66.0

        elif pct <= 25:
            rationale.append("Low IV percentile; long-vol structures may be favored")
            strategy = "long_straddle"
            risk = "high"
            edge = "vol_expansion"
            score = 62.0

        else:
            rationale.append("Mid IV percentile; prefer defined-risk income structures")
            strategy = "bull_put_spread" if (pcr is not None and pcr >= 1.0) else "bear_call_spread"
            risk = "medium"
            edge = "defined_risk_premium"
            score = 58.0

    elif isinstance(atm_iv, (int, float)):
        # Absolute IV regime fallback
        if atm_iv > 25:
            rationale.append(f"ATM IV is very high (~{atm_iv:.1f}); prefer ratio spreads over naked premium selling")
            if pcr is not None and pcr >= 1.0:
                strategy = "put_ratio_spread"
                edge = "premium_capture_with_wings"
            else:
                strategy = "call_ratio_spread"
                edge = "premium_capture_with_wings"
            risk = "high"
            score = 75.0
            if pcr is not None:
                rationale.append(f"PCR ~{pcr:.2f} used for ratio-spread direction")
        elif atm_iv >= 18:
            rationale.append(f"ATM IV is elevated (~{atm_iv:.1f}), option premiums relatively rich")
            if pcr is not None and 0.8 <= pcr <= 1.2:
                strategy = "short_strangle"
                risk = "high"
                edge = "premium_capture"
                score = 70.0
                rationale.append(f"PCR ~{pcr:.2f} suggests more balanced positioning")
            else:
                strategy = "bear_call_spread" if (pcr is not None and pcr < 0.9) else "bull_put_spread"
                risk = "medium"
                edge = "defined_risk_premium"
                score = 65.0
                if pcr is not None:
                    rationale.append(f"PCR ~{pcr:.2f} used for mild directional tilt")
        elif atm_iv <= 12:
            rationale.append(f"ATM IV is low (~{atm_iv:.1f}); volatility buying may be favored")
            strategy = "long_straddle"
            risk = "high"
            edge = "vol_expansion"
            score = 60.0
        else:
            rationale.append(f"ATM IV is moderate (~{atm_iv:.1f}); prefer defined-risk income structures")
            strategy = "bull_put_spread" if (pcr is not None and pcr >= 1.0) else "bear_call_spread"
            risk = "medium"
            edge = "defined_risk_premium"
            score = 58.0
    else:
        rationale.append("ATM IV unavailable; falling back to conservative income bias")

    # For positional, prefer defined-risk spreads over naked strangles
    if horizon == "long_term" and strategy == "short_strangle":
        strategy = "iron_condor"
        risk = "medium"
        edge = "defined_risk_premium"
        score = min(score, 66.0)
        rationale.append("Positional horizon: using defined-risk variant (iron condor) instead of naked strangle")

    # Attach strike ladder info for UI display (if available)
    try:
        atm = metrics.get("atm_strike")
        ladder = metrics.get("strike_prices")
        if isinstance(atm, (int, float)) and isinstance(ladder, list) and ladder:
            cons = strikes_considered(strategy=strategy, strike_prices=[float(x) for x in ladder], atm_strike=float(atm))
            metrics["strike_prices_considered"] = cons
    except Exception:
        pass

    return StrategyPick(
        underlying=str(metrics.get("symbol") or "UNKNOWN"),
        strategy=strategy,
        risk=risk,
        expected_edge=edge,
        score=float(score),
        rationale=rationale,
        key_metrics=metrics,
    )

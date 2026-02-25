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
        "records": len(records),
    }


def pick_strategy(metrics: dict, *, horizon: str = "short_term") -> StrategyPick:
    """Pick a strategy based on rough option-chain conditions.

    This is research-only heuristics, NOT advice.
    """

    und = metrics.get("underlying")
    if not isinstance(und, (int, float)):
        return StrategyPick(
            underlying=str(metrics.get("symbol") or "UNKNOWN"),
            strategy="no_data",
            risk="low",
            expected_edge="none",
            score=0.0,
            rationale=["Option chain data unavailable; cannot compute strategy."],
            key_metrics=metrics,
        )

    atm_iv = metrics.get("atm_iv")
    pcr = metrics.get("pcr")

    # Defaults
    strategy = "cash_secured_put"
    risk = "medium"
    edge = "income"
    score = 50.0
    rationale: List[str] = []

    if isinstance(atm_iv, (int, float)):
        if atm_iv >= 18:
            rationale.append(f"ATM IV is elevated (~{atm_iv:.1f}), option premiums relatively rich")
            # premium-selling candidates
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

    return StrategyPick(
        underlying=str(metrics.get("symbol") or "UNKNOWN"),
        strategy=strategy,
        risk=risk,
        expected_edge=edge,
        score=float(score),
        rationale=rationale,
        key_metrics=metrics,
    )

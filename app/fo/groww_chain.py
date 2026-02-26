from __future__ import annotations

from typing import Any, Dict, List, Optional


def summarize_groww_chain(oc: dict) -> dict:
    """Summarize Groww option chain payload into the same metric fields as NSE summarizer.

    Groww payload (per docs):
      {
        underlying_ltp: float,
        strikes: {
          <strike>: {
            CE: { iv, open_interest, volume, ltp, ... },
            PE: { iv, open_interest, volume, ltp, ... }
          },
          ...
        }
      }

    Returns:
      metrics dict containing: underlying, atm_strike, atm_iv, pcr, call_oi, put_oi
    """

    underlying = oc.get("underlying_ltp")
    strikes = oc.get("strikes")

    if not isinstance(underlying, (int, float)) or not isinstance(strikes, dict) or not strikes:
        return {"records": 0}

    # parse strike keys
    strike_vals: List[float] = []
    for k in strikes.keys():
        try:
            strike_vals.append(float(k))
        except Exception:
            continue
    if not strike_vals:
        return {"underlying": float(underlying), "records": 0}

    strike_vals.sort()
    atm = min(strike_vals, key=lambda s: abs(s - float(underlying)))

    call_oi = 0.0
    put_oi = 0.0
    atm_iv_vals: List[float] = []

    for k, node in strikes.items():
        if not isinstance(node, dict):
            continue
        ce = node.get("CE") if isinstance(node.get("CE"), dict) else None
        pe = node.get("PE") if isinstance(node.get("PE"), dict) else None

        if ce is not None:
            call_oi += float(ce.get("open_interest") or 0.0)
        if pe is not None:
            put_oi += float(pe.get("open_interest") or 0.0)

        # ATM IV: Groww nests greeks under side["greeks"]["iv"]
        try:
            if float(k) == float(atm):
                for side in (ce, pe):
                    if side is None:
                        continue
                    greeks = side.get("greeks") if isinstance(side.get("greeks"), dict) else None
                    iv = greeks.get("iv") if greeks is not None else None
                    if isinstance(iv, (int, float)):
                        atm_iv_vals.append(float(iv))
        except Exception:
            pass

    atm_iv = (sum(atm_iv_vals) / len(atm_iv_vals)) if atm_iv_vals else None
    pcr = (put_oi / call_oi) if call_oi > 0 else None

    return {
        "underlying": float(underlying),
        "atm_strike": float(atm),
        "atm_iv": atm_iv,
        "pcr": pcr,
        "call_oi": call_oi,
        "put_oi": put_oi,
        "records": len(strikes),
    }

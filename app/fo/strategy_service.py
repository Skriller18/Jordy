from __future__ import annotations

from typing import Any, Dict, List, Optional

import time

from app.fo.expiry import candidate_expiries
from app.fo.groww_chain import summarize_groww_chain
from app.fo.groww_client import GrowwFoClient
from app.fo.nse_client import NseClient
from app.fo.strategies import StrategyPick, pick_strategy, summarize_nse_chain
from app.iv_history import iv_percentile


class StrategyService:
    def __init__(self, groww: GrowwFoClient | None = None, nse: NseClient | None = None) -> None:
        self.groww = groww or GrowwFoClient()
        self.nse = nse or NseClient()
        self._expiry_cache: dict[str, tuple[str, float]] = {}

    def _resolve_expiry(self, *, exchange: str = "NSE", underlying: str = "NIFTY") -> str | None:
        """Find a working expiry date (Groww strikes non-empty). Cached for 1 hour."""

        key = f"{exchange}:{underlying}"
        cached = self._expiry_cache.get(key)
        if cached:
            exp, ts = cached
            if (time.time() - ts) < 3600:
                return exp

        for exp in candidate_expiries():
            try:
                oc = self.groww.get_option_chain(exchange, underlying, exp)
                strikes = oc.get("strikes")
                if isinstance(strikes, dict) and len(strikes) > 0:
                    self._expiry_cache[key] = (exp, time.time())
                    return exp
            except Exception:
                continue

        return None

    def run_for_underlyings(
        self,
        underlyings: List[str],
        *,
        horizon: str = "short_term",
        expiry_date: Optional[str] = None,
    ) -> tuple[List[StrategyPick], List[str]]:
        warnings: List[str] = []
        picks: List[StrategyPick] = []

        # If expiry not provided, try to auto-resolve using NIFTY as a probe.
        resolved_expiry = expiry_date
        if not resolved_expiry:
            resolved_expiry = self._resolve_expiry(exchange="NSE", underlying="NIFTY")
            if resolved_expiry:
                warnings.append(f"Using auto-resolved expiry_date={resolved_expiry}")
            else:
                warnings.append("Could not auto-resolve a working expiry; strategy picks may be no_data")

        for sym in underlyings:
            sym_u = sym.strip().upper()
            metrics: Dict[str, Any] = {"symbol": sym_u}

            # Try Groww option chain first
            if resolved_expiry:
                try:
                    oc = self.groww.get_option_chain("NSE", sym_u, resolved_expiry)
                    strikes = oc.get("strikes")
                    if isinstance(strikes, dict) and len(strikes) > 0:
                        metrics["groww_strikes_present"] = True
                        metrics.update(summarize_groww_chain(oc))
                    else:
                        warnings.append(f"{sym_u}: Groww option chain empty for expiry {resolved_expiry}; falling back to NSE")
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"{sym_u}: Groww option chain failed ({exc}); falling back to NSE")

            # NSE fallback
            try:
                if sym_u in ("NIFTY", "BANKNIFTY"):
                    nse = self.nse.get_option_chain_index(sym_u)
                else:
                    nse = self.nse.get_option_chain_equity(sym_u)
                metrics.update(summarize_nse_chain(nse))
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{sym_u}: NSE option chain failed ({exc})")

            # If we have current IV, compute IV percentile from stored historical series (if present).
            try:
                if isinstance(metrics.get("atm_iv"), (int, float)):
                    pct = iv_percentile(symbol=sym_u, current_iv=float(metrics.get("atm_iv")))
                    if pct is not None:
                        metrics["iv_percentile"] = float(pct)
            except Exception:
                pass

            picks.append(pick_strategy(metrics, horizon=horizon))

        picks.sort(key=lambda p: p.score, reverse=True)
        return picks, warnings

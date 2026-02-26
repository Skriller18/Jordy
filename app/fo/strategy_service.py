from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.fo.groww_chain import summarize_groww_chain
from app.fo.groww_client import GrowwFoClient
from app.fo.nse_client import NseClient
from app.fo.strategies import StrategyPick, pick_strategy, summarize_nse_chain


class StrategyService:
    def __init__(self, groww: GrowwFoClient | None = None, nse: NseClient | None = None) -> None:
        self.groww = groww or GrowwFoClient()
        self.nse = nse or NseClient()

    def run_for_underlyings(
        self,
        underlyings: List[str],
        *,
        horizon: str = "short_term",
        expiry_date: Optional[str] = None,
    ) -> tuple[List[StrategyPick], List[str]]:
        warnings: List[str] = []
        picks: List[StrategyPick] = []

        for sym in underlyings:
            sym_u = sym.strip().upper()
            metrics: Dict[str, Any] = {"symbol": sym_u}

            # Try Groww option chain first (may be empty strikes)
            if expiry_date:
                try:
                    oc = self.groww.get_option_chain("NSE", sym_u, expiry_date)
                    strikes = oc.get("strikes")
                    if isinstance(strikes, dict) and len(strikes) > 0:
                        metrics["groww_strikes_present"] = True
                        metrics.update(summarize_groww_chain(oc))
                    else:
                        warnings.append(f"{sym_u}: Groww option chain empty; falling back to NSE")
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

            picks.append(pick_strategy(metrics, horizon=horizon))

        # Sort best-first
        picks.sort(key=lambda p: p.score, reverse=True)
        return picks, warnings

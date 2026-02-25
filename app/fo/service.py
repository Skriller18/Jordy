from __future__ import annotations

import time
from typing import Dict, List, Tuple

from app.fo.groww_client import GrowwFoClient
from app.fo.types import (
    IndexKey,
    IndicesSnapshotResponse,
    Nifty50SnapshotResponse,
    Nifty50SnapshotRow,
    UnderlyingSnapshot,
)
from app.fo.universe import NIFTY50


class FoService:
    def __init__(self, groww: GrowwFoClient | None = None) -> None:
        self.groww = groww or GrowwFoClient()

    def indices_snapshot(self) -> IndicesSnapshotResponse:
        warnings: List[str] = []
        indices: Dict[IndexKey, UnderlyingSnapshot] = {}
        now_ms = int(time.time() * 1000)

        # Groww examples show NIFTY works as trading_symbol for quotes.
        # SENSEX may require BSE + a specific trading symbol; try a couple fallbacks.
        try:
            q = self.groww.get_quote_cash("NSE", "NIFTY")
            indices[IndexKey.NIFTY] = UnderlyingSnapshot(
                trading_symbol="NIFTY",
                exchange="NSE",
                segment="CASH",
                last_price=q.get("last_price"),
                ohlc=(q.get("ohlc") if isinstance(q.get("ohlc"), dict) else None),
                day_change_perc=q.get("day_change_perc"),
                week_52_high=q.get("week_52_high"),
                week_52_low=q.get("week_52_low"),
                raw=q,
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"NIFTY: quote failed ({exc})")

        sensex_done = False
        for exch, sym in [("BSE", "SENSEX"), ("NSE", "SENSEX")]:
            if sensex_done:
                break
            try:
                q = self.groww.get_quote_cash(exch, sym)
                indices[IndexKey.SENSEX] = UnderlyingSnapshot(
                    trading_symbol=sym,
                    exchange=exch,  # type: ignore[arg-type]
                    segment="CASH",
                    last_price=q.get("last_price"),
                    ohlc=(q.get("ohlc") if isinstance(q.get("ohlc"), dict) else None),
                    day_change_perc=q.get("day_change_perc"),
                    week_52_high=q.get("week_52_high"),
                    week_52_low=q.get("week_52_low"),
                    raw=q,
                )
                sensex_done = True
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"SENSEX ({exch}:{sym}): quote failed ({exc})")

        return IndicesSnapshotResponse(as_of_epoch_ms=now_ms, indices=indices, warnings=warnings)

    def nifty50_snapshot(self, limit: int = 50) -> Nifty50SnapshotResponse:
        now_ms = int(time.time() * 1000)
        warnings: List[str] = []

        # Groww get_ltp expects strings like "NSE_RELIANCE" (exchange + '_' + symbol)
        symbols = tuple(f"NSE_{t}" for t in NIFTY50[:limit])
        rows: List[Nifty50SnapshotRow] = []

        try:
            payload = self.groww.get_ltp_cash(symbols)
            # Expected shape is SDK-defined; we handle common dict-ish formats.
            for t in NIFTY50[:limit]:
                key = f"NSE_{t}"
                node = payload.get(key) if isinstance(payload, dict) else None
                ltp = None
                if isinstance(node, dict):
                    ltp = node.get("ltp")
                elif isinstance(node, (int, float)):
                    ltp = float(node)
                rows.append(
                    Nifty50SnapshotRow(
                        ticker=t,
                        exchange="NSE",
                        last_price=ltp,
                        day_change_perc=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"NIFTY50: LTP fetch failed ({exc})")
            # Fallback to empty rows
            rows = [Nifty50SnapshotRow(ticker=t, exchange="NSE") for t in NIFTY50[:limit]]

        return Nifty50SnapshotResponse(as_of_epoch_ms=now_ms, rows=rows, warnings=warnings)

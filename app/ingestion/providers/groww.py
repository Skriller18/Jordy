from __future__ import annotations

import os
import time
from typing import Any

from app.ingestion.types import MarketSnapshot
from app.models import Country, TickerTarget


class GrowwProvider:
    """Groww Trading API provider (Python SDK).

    Auth (per Groww docs):
      - API key + secret flow: GrowwAPI.get_access_token(api_key=..., secret=...)
      - TOTP flow: GrowwAPI.get_access_token(api_key=<TOTP_TOKEN>, totp=<current_totp>)

    Env vars supported by this provider:
      - GROWW_ACCESS_TOKEN: if set, used directly.

      - GROWW_API_KEY + GROWW_API_SECRET: used to mint an access token.
        Note: Groww docs mention daily approval for this flow.

      - GROWW_TOTP_TOKEN + GROWW_TOTP_SECRET: used to mint an access token.
        This is the more automation-friendly flow.

    This provider focuses on live price + historical candles. Fundamentals are not
    expected from Groww, so they are left as None and Jordy defaults kick in.
    """

    def __init__(self) -> None:
        self._groww = None
        self._access_token: str | None = None

    def _load_client(self):
        if self._groww is not None:
            return self._groww

        try:
            from growwapi import GrowwAPI  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Missing dependency 'growwapi'. Install with: pip install growwapi") from exc

        access_token = os.getenv("GROWW_ACCESS_TOKEN")
        if not access_token:
            # Prefer TOTP flow (no expiry) if present.
            totp_token = os.getenv("GROWW_TOTP_TOKEN")
            totp_secret = os.getenv("GROWW_TOTP_SECRET")
            if totp_token and totp_secret:
                try:
                    import pyotp  # type: ignore
                except Exception as exc:  # noqa: BLE001
                    raise RuntimeError("Missing dependency 'pyotp' for TOTP flow. Install with: pip install pyotp") from exc
                totp = pyotp.TOTP(totp_secret).now()
                access_token = GrowwAPI.get_access_token(api_key=totp_token, totp=totp)
            else:
                api_key = os.getenv("GROWW_API_KEY")
                api_secret = os.getenv("GROWW_API_SECRET")
                if api_key and api_secret:
                    access_token = GrowwAPI.get_access_token(api_key=api_key, secret=api_secret)

        if not access_token:
            raise RuntimeError(
                "Groww credentials missing. Set GROWW_ACCESS_TOKEN or GROWW_TOTP_TOKEN+GROWW_TOTP_SECRET or GROWW_API_KEY+GROWW_API_SECRET."
            )

        self._access_token = access_token
        self._groww = GrowwAPI(access_token)
        return self._groww

    @staticmethod
    def _resolve_symbol(target: TickerTarget) -> tuple[str, str, str]:
        """Return (exchange, segment, trading_symbol).

        For India equities, Groww typically expects:
          exchange=NSE, segment=CASH, trading_symbol=<NSE symbol>

        If you pass tickers like TCS/RELIANCE, this should work.
        """

        ticker = target.ticker.strip().upper()
        # basic default mapping
        if target.country == Country.INDIA:
            return ("NSE", "CASH", ticker)
        # For non-India, keep a reasonable default; may require explicit mapping.
        return ("NSE", "CASH", ticker)

    def fetch_snapshot(self, target: TickerTarget) -> MarketSnapshot:
        groww = self._load_client()

        exch, segment, sym = self._resolve_symbol(target)

        # Map to SDK constants if present; fall back to raw strings.
        exchange = getattr(groww, f"EXCHANGE_{exch}", exch)
        seg = getattr(groww, f"SEGMENT_{segment}", segment)

        quote: dict[str, Any] = groww.get_quote(exchange=exchange, segment=seg, trading_symbol=sym)

        closes: list[float] = []
        try:
            end_ms = int(time.time() * 1000)
            start_ms = end_ms - (365 * 24 * 60 * 60 * 1000)
            hist = groww.get_historical_candle_data(
                trading_symbol=sym,
                exchange=exchange,
                segment=seg,
                start_time=str(start_ms),
                end_time=str(end_ms),
                interval_in_minutes=1440,
            )
            candles = hist.get("candles") or []
            for c in candles:
                # [ts, open, high, low, close, volume]
                if isinstance(c, (list, tuple)) and len(c) >= 5 and isinstance(c[4], (int, float)):
                    closes.append(float(c[4]))
        except Exception:
            # Historical is optional; momentum/vol will fall back.
            closes = []

        last_price = None
        try:
            last_price = quote.get("last_price")
        except Exception:
            last_price = None
        if isinstance(last_price, (int, float)) and last_price > 0:
            if not closes:
                closes = [float(last_price)]

        return MarketSnapshot(
            symbol=sym,
            company_name=str(target.ticker).upper(),
            country=target.country,
            sector="Unknown",
            industry="Unknown",
            closes=closes,
        )

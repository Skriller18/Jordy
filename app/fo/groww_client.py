from __future__ import annotations

import os
from typing import Any, Dict, Tuple


class GrowwFoClient:
    """Thin wrapper around GrowwAPI for F&O + indices usage.

    Uses the same env var scheme as app.ingestion.providers.groww.GrowwProvider.

    Env vars:
      - GROWW_ACCESS_TOKEN
      - GROWW_TOTP_TOKEN + GROWW_TOTP_SECRET
      - GROWW_API_KEY + GROWW_API_SECRET
    """

    def __init__(self) -> None:
        self._client = None

    def _load(self):
        if self._client is not None:
            return self._client

        try:
            from growwapi import GrowwAPI  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Missing dependency 'growwapi'. Install with: pip install growwapi") from exc

        access_token = os.getenv("GROWW_ACCESS_TOKEN")
        if not access_token:
            totp_token = os.getenv("GROWW_TOTP_TOKEN")
            totp_secret = os.getenv("GROWW_TOTP_SECRET")
            if totp_token and totp_secret:
                try:
                    import pyotp  # type: ignore
                except Exception as exc:  # noqa: BLE001
                    raise RuntimeError("Missing dependency 'pyotp'. Install with: pip install pyotp") from exc
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

        self._client = GrowwAPI(access_token)
        return self._client

    def get_quote_cash(self, exchange: str, trading_symbol: str) -> Dict[str, Any]:
        g = self._load()
        ex = getattr(g, f"EXCHANGE_{exchange}", exchange)
        seg = getattr(g, "SEGMENT_CASH", "CASH")
        return g.get_quote(exchange=ex, segment=seg, trading_symbol=trading_symbol)

    def get_ltp_cash(self, exchange_trading_symbols: Tuple[str, ...]) -> Dict[str, Any]:
        g = self._load()
        seg = getattr(g, "SEGMENT_CASH", "CASH")
        return g.get_ltp(segment=seg, exchange_trading_symbols=exchange_trading_symbols)

    def get_option_chain(self, exchange: str, underlying: str, expiry_date: str) -> Dict[str, Any]:
        g = self._load()
        ex = getattr(g, f"EXCHANGE_{exchange}", exchange)
        return g.get_option_chain(exchange=ex, underlying=underlying, expiry_date=expiry_date)

    def get_greeks(self, exchange: str, underlying: str, trading_symbol: str, expiry: str) -> Dict[str, Any]:
        g = self._load()
        ex = getattr(g, f"EXCHANGE_{exchange}", exchange)
        return g.get_greeks(exchange=ex, underlying=underlying, trading_symbol=trading_symbol, expiry=expiry)

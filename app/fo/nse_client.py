from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


@dataclass
class CacheEntry:
    ts: float
    value: dict


class NseClient:
    """Lightweight NSE option chain client with cookie priming + TTL cache + throttling.

    NSE endpoints are prone to 403 without proper headers/cookies.
    """

    def __init__(self, min_interval_s: float = 0.8, ttl_s: float = 20.0) -> None:
        self._s = requests.Session()
        self._last_req_ts = 0.0
        self._min_interval_s = min_interval_s
        self._ttl_s = ttl_s
        self._cache: Dict[Tuple[str, str], CacheEntry] = {}
        self._primed = False

    def _throttle(self) -> None:
        delta = time.time() - self._last_req_ts
        if delta < self._min_interval_s:
            time.sleep(self._min_interval_s - delta)

    def _prime(self) -> None:
        if self._primed:
            return
        self._throttle()
        r = self._s.get("https://www.nseindia.com/", headers=DEFAULT_HEADERS, timeout=10)
        self._last_req_ts = time.time()
        r.raise_for_status()
        self._primed = True

    def get_option_chain_index(self, symbol: str) -> dict:
        return self._get_json("index", symbol)

    def get_option_chain_equity(self, symbol: str) -> dict:
        return self._get_json("equity", symbol)

    def _get_json(self, kind: str, symbol: str) -> dict:
        symbol = symbol.strip().upper()
        cache_key = (kind, symbol)
        ent = self._cache.get(cache_key)
        if ent and (time.time() - ent.ts) < self._ttl_s:
            return ent.value

        self._prime()
        self._throttle()

        if kind == "index":
            url = "https://www.nseindia.com/api/option-chain-indices"
        else:
            url = "https://www.nseindia.com/api/option-chain-equities"

        r = self._s.get(url, params={"symbol": symbol}, headers=DEFAULT_HEADERS, timeout=15)
        self._last_req_ts = time.time()
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected NSE response")

        self._cache[cache_key] = CacheEntry(ts=time.time(), value=data)
        return data

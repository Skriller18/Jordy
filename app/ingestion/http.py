from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any


class HttpClient:
    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self.user_agent = os.getenv(
            "EQUITY_BOT_USER_AGENT",
            "equity-research-bot/0.1 (contact: research@example.com)",
        )

    def _request(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json,text/xml,application/xml,text/plain,*/*",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        if params:
            query = urllib.parse.urlencode(params)
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{query}"
        raw = self._request(url)
        return json.loads(raw)

    def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        if params:
            query = urllib.parse.urlencode(params)
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{query}"
        return self._request(url)

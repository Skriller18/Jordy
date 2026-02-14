from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET

from app.ingestion.http import HttpClient


POSITIVE_WORDS = {
    "beat",
    "beats",
    "growth",
    "surge",
    "record",
    "strong",
    "upgrade",
    "profit",
    "outperform",
    "expands",
    "bullish",
}

NEGATIVE_WORDS = {
    "miss",
    "misses",
    "fall",
    "drop",
    "fraud",
    "probe",
    "downgrade",
    "lawsuit",
    "weak",
    "bearish",
    "risk",
    "decline",
}


class NewsProvider:
    def __init__(self, http_client: HttpClient | None = None) -> None:
        self.http = http_client or HttpClient()

    @staticmethod
    def _score_title(title: str) -> float:
        tokens = re.findall(r"[A-Za-z]+", title.lower())
        if not tokens:
            return 0.0
        pos = sum(1 for token in tokens if token in POSITIVE_WORDS)
        neg = sum(1 for token in tokens if token in NEGATIVE_WORDS)
        return (pos - neg) / max(len(tokens), 1)

    def fetch_sentiment(self, query: str, limit: int = 10) -> tuple[float, list[str]]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}+stock&hl=en-US&gl=US&ceid=US:en"
        xml_text = self.http.get_text(url)
        root = ET.fromstring(xml_text)

        titles: list[str] = []
        scores: list[float] = []

        for item in root.findall("./channel/item")[:limit]:
            title = (item.findtext("title") or "").strip()
            if not title:
                continue
            titles.append(title)
            scores.append(self._score_title(title))

        sentiment = 0.0
        if scores:
            sentiment = sum(scores) / len(scores)
            sentiment = max(-1.0, min(1.0, sentiment * 8.0))

        return sentiment, titles

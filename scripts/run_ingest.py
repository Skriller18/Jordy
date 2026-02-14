from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.ingestion import IngestionPipeline
from app.models import Country, Horizon, IngestRankResponse, TickerTarget
from app.scoring.ranking import rank_companies


def parse_targets(raw: str) -> list[TickerTarget]:
    targets: list[TickerTarget] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" in token:
            ticker, country = token.split(":", 1)
            country = country.strip().upper()
        else:
            ticker, country = token, "USA"

        targets.append(
            TickerTarget(
                ticker=ticker.strip().upper(),
                country=Country(country),
            )
        )
    return targets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest live data and rank targets")
    parser.add_argument(
        "--targets",
        required=True,
        help="Comma-separated TICKER:COUNTRY values, e.g. AAPL:USA,MSFT:USA,TCS:INDIA",
    )
    parser.add_argument(
        "--horizon",
        default="long_term",
        choices=["short_term", "long_term"],
        help="Scoring horizon",
    )
    parser.add_argument("--news-items", type=int, default=10, help="News headlines to inspect per company")
    args = parser.parse_args()

    pipeline = IngestionPipeline()
    targets = parse_targets(args.targets)
    companies, warnings = pipeline.ingest_targets(targets, news_items=max(1, min(args.news_items, 50)))

    if not companies:
        raise SystemExit("No companies ingested. Check ticker format and network access.")

    ranked = rank_companies(companies, horizon=Horizon(args.horizon))
    response = IngestRankResponse(
        **ranked.model_dump(),
        ingested_count=len(companies),
        warnings=warnings,
    )
    print(json.dumps(response.model_dump(), indent=2))

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.data.sample_universe import sample_companies
from app.ingestion import IngestionPipeline
from app.models import (
    Horizon,
    IngestRankRequest,
    IngestRankResponse,
    RankRequest,
    RankResponse,
)
from app.scoring.ranking import rank_companies

app = FastAPI(title="Equity Research Bot API", version="0.1.0")
ingestion_pipeline = IngestionPipeline()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/sample", response_model=RankResponse)
def sample(horizon: Horizon = Horizon.LONG_TERM) -> RankResponse:
    companies = sample_companies()
    return rank_companies(companies, horizon=horizon)


@app.post("/v1/rank", response_model=RankResponse)
def rank(payload: RankRequest) -> RankResponse:
    return rank_companies(payload.companies, horizon=payload.horizon)


@app.post("/v1/ingest-and-rank", response_model=IngestRankResponse)
def ingest_and_rank(payload: IngestRankRequest) -> IngestRankResponse:
    companies, warnings = ingestion_pipeline.ingest_targets(payload.targets, news_items=payload.news_items)
    if not companies:
        raise HTTPException(status_code=400, detail="No companies could be ingested from the provided targets.")

    ranked = rank_companies(companies, horizon=payload.horizon)
    return IngestRankResponse(
        **ranked.model_dump(),
        ingested_count=len(companies),
        warnings=warnings,
    )

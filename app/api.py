from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.data.sample_universe import sample_companies
from app.fo.service import FoService
from app.fo.strategy_service import StrategyService
from app.fo.explain import build_explanation
from app.ingestion.providers.groww import GrowwProvider
from app.fo.strategy_explain_types import StrategyExplanationModel
from app.fo.strategy_types import (
    StrategiesRunRequest,
    StrategiesRunResponse,
    StrategiesUniverseResponse,
)
from app.fo.types import FoUniverseResponse, IndicesSnapshotResponse, Nifty50SnapshotResponse
from app.fo.universe import NIFTY50
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
fo_service = FoService()
strategy_service = StrategyService()
_groww_provider = GrowwProvider()


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


# -----------------
# F&O / Indices APIs
# -----------------


@app.get("/v1/fo/universe", response_model=FoUniverseResponse)
def fo_universe() -> FoUniverseResponse:
    # Indices: NIFTY + SENSEX; NIFTY 50 constituents list.
    return FoUniverseResponse(indices=["NIFTY", "SENSEX"], nifty50=NIFTY50)


@app.get("/v1/fo/indices/snapshot", response_model=IndicesSnapshotResponse)
def fo_indices_snapshot() -> IndicesSnapshotResponse:
    return fo_service.indices_snapshot()


@app.get("/v1/fo/nifty50/snapshot", response_model=Nifty50SnapshotResponse)
def fo_nifty50_snapshot(limit: int = 50) -> Nifty50SnapshotResponse:
    limit = max(1, min(50, limit))
    return fo_service.nifty50_snapshot(limit=limit)


# -----------------
# Strategy lab APIs (research-only)
# -----------------


@app.get("/v1/fo/strategies/universe", response_model=StrategiesUniverseResponse)
def fo_strategies_universe() -> StrategiesUniverseResponse:
    return StrategiesUniverseResponse(
        strategies=[
            "cash_secured_put",
            "covered_call",
            "bull_put_spread",
            "bear_call_spread",
            "iron_condor",
            "long_straddle",
            "short_strangle",
            "call_ratio_spread",
            "put_ratio_spread",
            "no_data",
        ],
        risk_levels=["low", "medium", "high"],
        supported_underlyings=["NIFTY", *NIFTY50],
    )


@app.post("/v1/fo/strategies/run", response_model=StrategiesRunResponse)
def fo_strategies_run(payload: StrategiesRunRequest) -> StrategiesRunResponse:
    picks, warnings = strategy_service.run_for_underlyings(
        payload.underlyings, horizon=payload.horizon, expiry_date=payload.expiry_date
    )

    disclaimer = (
        "Research-only output. Not investment advice. Options are risky; strategies here are heuristic and may lose money. "
        "Always validate liquidity, margins, and risk limits."
    )

    best = picks[0]

    def to_model(p):
        return {
            "underlying": p.underlying,
            "strategy": p.strategy,
            "risk": p.risk,
            "expected_edge": p.expected_edge,
            "score": p.score,
            "rationale": p.rationale,
            "key_metrics": p.key_metrics,
        }

    # Conservative pick: prefer defined-risk / non-high-risk strategies
    allowed = {"covered_call", "cash_secured_put", "bull_put_spread", "bear_call_spread", "iron_condor"}

    def conservative_score(p):
        base = float(p.score)
        # penalize high risk heavily
        if p.risk == "high":
            base -= 100.0
        # penalize non-defined-risk strategies
        if p.strategy not in allowed:
            base -= 30.0
        return base

    best_min_risk = max(picks, key=conservative_score)

    best_overall_explain = None
    best_min_risk_explain = None

    if payload.include_explanations:
        def _closes(sym: str) -> list[float]:
            # Use Groww candles for underlying proxy backtest; for NIFTY use cash symbol.
            from app.models import Country, TickerTarget
            snap = _groww_provider.fetch_snapshot(TickerTarget(ticker=sym, country=Country.INDIA))
            return [float(x) for x in (snap.closes or []) if isinstance(x, (int, float))]

        try:
            c = _closes(best.underlying)
            exp = build_explanation(
                underlying=best.underlying,
                strategy=best.strategy,
                key_metrics=best.key_metrics,
                closes=c,
            )
            best_overall_explain = {
                "underlying": exp.underlying,
                "strategy": exp.strategy,
                "hypothesis": exp.hypothesis,
                "assumptions": exp.assumptions,
                "failure_modes": exp.failure_modes,
                "proxy_backtests": [
                    {
                        "horizon_days": b.horizon_days,
                        "samples": b.samples,
                        "avg_return_pct": b.avg_return_pct,
                        "median_return_pct": b.median_return_pct,
                        "win_rate_pct": b.win_rate_pct,
                        "worst_return_pct": b.worst_return_pct,
                        "best_return_pct": b.best_return_pct,
                    }
                    for b in exp.proxy_backtests
                ],
                "notes": exp.notes,
            }
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{best.underlying}: explain/backtest failed ({exc})")

        try:
            c = _closes(best_min_risk.underlying)
            exp = build_explanation(
                underlying=best_min_risk.underlying,
                strategy=best_min_risk.strategy,
                key_metrics=best_min_risk.key_metrics,
                closes=c,
            )
            best_min_risk_explain = {
                "underlying": exp.underlying,
                "strategy": exp.strategy,
                "hypothesis": exp.hypothesis,
                "assumptions": exp.assumptions,
                "failure_modes": exp.failure_modes,
                "proxy_backtests": [
                    {
                        "horizon_days": b.horizon_days,
                        "samples": b.samples,
                        "avg_return_pct": b.avg_return_pct,
                        "median_return_pct": b.median_return_pct,
                        "win_rate_pct": b.win_rate_pct,
                        "worst_return_pct": b.worst_return_pct,
                        "best_return_pct": b.best_return_pct,
                    }
                    for b in exp.proxy_backtests
                ],
                "notes": exp.notes,
            }
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{best_min_risk.underlying}: explain/backtest failed ({exc})")

    return StrategiesRunResponse(
        disclaimer=disclaimer,
        best_overall=to_model(best),
        best_min_risk=to_model(best_min_risk),
        best_overall_explain=best_overall_explain,
        best_min_risk_explain=best_min_risk_explain,
        results=[to_model(p) for p in picks],
        warnings=warnings,
    )

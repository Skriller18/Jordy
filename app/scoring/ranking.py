from __future__ import annotations

from typing import List

from app.models import CompanyInput, Horizon, RankResponse, RankedIdea, ScoreBreakdown
from app.scoring.qual import score_qual
from app.scoring.quant import score_quant


def recommendation_band(score: float) -> str:
    if score >= 80:
        return "strong_candidate"
    if score >= 65:
        return "watchlist"
    return "avoid"


def risk_notes_for(company: CompanyInput, quant_score: float, qual_score: float) -> List[str]:
    notes: List[str] = []
    if company.quant.volatility_30d_pct > 40:
        notes.append("High volatility: position sizing should be conservative")
    if company.quant.debt_to_equity > 1.5:
        notes.append("Balance sheet leverage is elevated")
    if company.qual.regulatory_risk_score >= 7:
        notes.append("Regulatory headline risk may be material")
    if quant_score < 50 or qual_score < 50:
        notes.append("One side of the model is weak; treat conviction as low")
    if not notes:
        notes.append("No exceptional risk flag from current scoring inputs")
    return notes


def rank_companies(companies: List[CompanyInput], horizon: Horizon) -> RankResponse:
    ranked: List[RankedIdea] = []

    for company in companies:
        quant_score, quant_components, quant_pos, quant_neg = score_quant(company.quant, horizon)
        qual_score, qual_components, qual_pos, qual_neg = score_qual(company.qual, horizon)

        composite = round((quant_score * 0.6) + (qual_score * 0.4), 2)
        recommendation = recommendation_band(composite)

        positives = (quant_pos + qual_pos)[:8]
        negatives = (quant_neg + qual_neg)[:8]

        ranked.append(
            RankedIdea(
                ticker=company.ticker,
                company_name=company.company_name,
                country=company.country,
                sector=company.sector,
                industry=company.industry,
                recommendation=recommendation,
                score=ScoreBreakdown(
                    quant_score=quant_score,
                    qual_score=qual_score,
                    composite_score=composite,
                    quant_components=quant_components,
                    qual_components=qual_components,
                ),
                positives=positives,
                negatives=negatives,
                risk_notes=risk_notes_for(company, quant_score, qual_score),
            )
        )

    ranked.sort(key=lambda idea: idea.score.composite_score, reverse=True)

    return RankResponse(
        horizon=horizon,
        results=ranked,
        disclaimer=(
            "Educational/research output only. Not investment advice. "
            "Validate with latest filings, liquidity checks, and risk limits before any trade."
        ),
    )

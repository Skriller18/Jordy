from __future__ import annotations

from app.data.sample_universe import sample_companies
from app.models import Horizon
from app.scoring.ranking import rank_companies


def test_ranking_returns_sorted_scores() -> None:
    companies = sample_companies()
    response = rank_companies(companies, horizon=Horizon.LONG_TERM)
    scores = [item.score.composite_score for item in response.results]
    assert scores == sorted(scores, reverse=True)


def test_recommendation_band_valid() -> None:
    companies = sample_companies()
    response = rank_companies(companies, horizon=Horizon.SHORT_TERM)
    valid = {"strong_candidate", "watchlist", "avoid"}
    for item in response.results:
        assert item.recommendation in valid


def test_scores_are_bounded() -> None:
    companies = sample_companies()
    response = rank_companies(companies, horizon=Horizon.LONG_TERM)
    for item in response.results:
        assert 0 <= item.score.quant_score <= 100
        assert 0 <= item.score.qual_score <= 100
        assert 0 <= item.score.composite_score <= 100

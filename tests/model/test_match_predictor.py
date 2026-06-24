import numpy as np
import pandas as pd
import pytest

from src.model.match_predictor import MatchPredictor
from src.model.poisson_model import PoissonModel


def _make_fitted_model():
    matches = pd.DataFrame({
        "home_team_iso":   ["A"] * 20 + ["B"] * 20,
        "away_team_iso":   ["B"] * 20 + ["A"] * 20,
        "home_team_score": [2] * 20 + [1] * 20,
        "away_team_score": [1] * 20 + [2] * 20,
        "year":            [2022] * 40,
        "host_team_iso":   [np.nan] * 40,
    })
    teams = pd.DataFrame({
        "iso_code":          ["A",    "B"   ],
        "elo_rating":        [1800.0, 1800.0],
        "squad_value_m_eur": [500.0,  500.0 ],
        "sb_xg_per90":       [1.0,    1.0   ],
        "sq_npxg_per90":     [np.nan, np.nan],
        "fb_npgls_per90":    [np.nan, np.nan],
    })
    return PoissonModel(ridge_lambda=0.01).fit(matches, teams, year_ref=2022)


def _make_predictor():
    m = _make_fitted_model()
    return MatchPredictor(
        model_goals=m, model_corners=m, model_cards=m,
        model_shots=m, model_fouls=m,
    )


def test_predict_match_has_all_markets():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    assert "result"  in result
    assert "goals"   in result
    assert "corners" in result
    assert "cards"   in result
    assert "shots"   in result
    assert "fouls"   in result


def test_result_probabilities_sum_to_one():
    pred = _make_predictor()
    r = pred.predict_match("A", "B")["result"]
    assert abs(r["p_home"] + r["p_draw"] + r["p_away"] - 1.0) < 1e-3


def test_over_under_sum_to_one():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    for market in ["goals", "corners", "cards", "shots", "fouls"]:
        m = result[market]
        lines = set(k.replace("over_", "") for k in m if k.startswith("over_"))
        for line in lines:
            over  = m[f"over_{line}"]
            under = m[f"under_{line}"]
            assert abs(over + under - 1.0) < 1e-6, f"{market} {line}: {over} + {under} ≠ 1"


def test_btts_in_goals():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    assert "btts" in result["goals"]
    assert 0.0 <= result["goals"]["btts"] <= 1.0


def test_expected_total_positive():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    for market in ["goals", "corners", "cards", "shots", "fouls"]:
        assert result[market]["expected_total"] > 0

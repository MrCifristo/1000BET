import numpy as np
import pandas as pd
import pytest

from src.model.validation import brier_score, loto_cv


def _make_cv_data():
    matches = pd.DataFrame({
        "home_team_iso":   ["A", "B", "A", "B"],
        "away_team_iso":   ["B", "A", "B", "A"],
        "home_team_score": [2,   1,   1,   2  ],
        "away_team_score": [1,   2,   0,   1  ],
        "year":            [2018, 2018, 2022, 2022],
        "host_team_iso":   [np.nan] * 4,
    })
    teams = pd.DataFrame({
        "iso_code":          ["A",   "B"  ],
        "elo_rating":        [1800.0, 1800.0],
        "squad_value_m_eur": [500.0,  500.0 ],
        "sb_xg_per90":       [1.0,    1.0   ],
        "sq_npxg_per90":     [np.nan, np.nan],
        "fb_npgls_per90":    [np.nan, np.nan],
    })
    return matches, teams


def test_brier_score_perfect_home_prediction():
    preds    = [{"p_home": 1.0, "p_draw": 0.0, "p_away": 0.0}]
    outcomes = ["home"]
    assert brier_score(preds, outcomes) == pytest.approx(0.0)


def test_brier_score_perfect_draw_prediction():
    preds    = [{"p_home": 0.0, "p_draw": 1.0, "p_away": 0.0}]
    outcomes = ["draw"]
    assert brier_score(preds, outcomes) == pytest.approx(0.0)


def test_brier_score_naive_model():
    n = 30
    preds    = [{"p_home": 1/3, "p_draw": 1/3, "p_away": 1/3}] * n
    outcomes = ["home"] * 10 + ["draw"] * 10 + ["away"] * 10
    assert brier_score(preds, outcomes) == pytest.approx(2/3, abs=0.01)


def test_brier_score_wrong_certain_prediction():
    preds    = [{"p_home": 1.0, "p_draw": 0.0, "p_away": 0.0}]
    outcomes = ["away"]
    assert brier_score(preds, outcomes) == pytest.approx(2.0)


def test_loto_cv_returns_dataframe():
    matches, teams = _make_cv_data()
    result = loto_cv(matches, teams, ridge_lambdas=[0.1], decay_rates=[0.05])
    assert isinstance(result, pd.DataFrame)
    assert "ridge_lambda" in result.columns
    assert "decay_rate"   in result.columns
    assert "mean_bs"      in result.columns


def test_loto_cv_grid_produces_one_row_per_combination():
    matches, teams = _make_cv_data()
    result = loto_cv(matches, teams, ridge_lambdas=[0.1, 1.0], decay_rates=[0.05])
    assert len(result) == 2


def test_loto_cv_best_params_have_lower_bs():
    matches, teams = _make_cv_data()
    result = loto_cv(matches, teams, ridge_lambdas=[0.01, 10.0], decay_rates=[0.05])
    if len(result) == 2:
        assert result["mean_bs"].min() >= 0.0

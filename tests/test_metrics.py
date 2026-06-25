import pandas as pd
import pytest

from src.evaluation.metrics import outcome, brier_1x2, logloss_1x2, rps_1x2, hit_rate


def _df(rows):
    return pd.DataFrame(rows, columns=[
        "goals_a", "goals_b", "p_home_pred", "p_draw_pred", "p_away_pred"])


def test_outcome():
    assert outcome(2, 0) == "home"
    assert outcome(1, 1) == "draw"
    assert outcome(0, 3) == "away"


def test_perfect_prediction_scores_zero_brier_and_logloss():
    df = _df([[2, 0, 1.0, 0.0, 0.0]])
    assert brier_1x2(df) == pytest.approx(0.0)
    assert logloss_1x2(df) == pytest.approx(0.0, abs=1e-9)
    assert rps_1x2(df) == pytest.approx(0.0)
    assert hit_rate(df) == pytest.approx(1.0)


def test_naive_third_brier_matches_reference():
    df = _df([[2, 0, 1/3, 1/3, 1/3]])
    # (1/3-1)^2 + (1/3)^2 + (1/3)^2 = 0.6667
    assert brier_1x2(df) == pytest.approx(0.6667, abs=1e-4)


def test_rps_penalizes_distant_errors_more():
    # actual = home; predicting all-away is worse than all-draw
    away = _df([[2, 0, 0.0, 0.0, 1.0]])
    draw = _df([[2, 0, 0.0, 1.0, 0.0]])
    assert rps_1x2(away) > rps_1x2(draw)


def test_hit_rate_counts_argmax_matches():
    df = _df([[2, 0, 0.6, 0.3, 0.1],   # argmax home, actual home -> hit
              [0, 1, 0.6, 0.3, 0.1]])  # argmax home, actual away -> miss
    assert hit_rate(df) == pytest.approx(0.5)

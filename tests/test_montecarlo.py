import pickle
from pathlib import Path

import pandas as pd
import pytest

from src.tournament.montecarlo import simulate_tournament

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def predictor():
    with open(ROOT / "outputs/match_predictor.pkl", "rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="module")
def results():
    return pd.read_csv(ROOT / "data/processed/wc2026_actual_results.csv")


def test_returns_expected_columns(predictor, results):
    out = simulate_tournament(results, predictor, n_sims=50, seed=0)
    assert list(out.columns) == [
        "ISO", "p_advance", "p_r16", "p_qf", "p_sf", "p_final", "p_champion"]
    assert len(out) > 0


def test_champion_probs_sum_to_one(predictor, results):
    out = simulate_tournament(results, predictor, n_sims=200, seed=0)
    assert out["p_champion"].sum() == pytest.approx(1.0, abs=1e-9)


def test_round_probabilities_are_monotonic(predictor, results):
    out = simulate_tournament(results, predictor, n_sims=200, seed=0)
    for _, r in out.iterrows():
        assert r.p_advance >= r.p_r16 >= r.p_qf >= r.p_sf >= r.p_final >= r.p_champion - 1e-9


def test_deterministic_with_seed(predictor, results):
    a = simulate_tournament(results, predictor, n_sims=100, seed=7)
    b = simulate_tournament(results, predictor, n_sims=100, seed=7)
    pd.testing.assert_frame_equal(a, b)

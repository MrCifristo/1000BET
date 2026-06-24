import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.model.updater import update_elo, log_result, ELO_K


def _make_elo_df():
    return pd.DataFrame({
        "iso_code":   ["ARG", "FRA", "BRA"],
        "elo_rank":   [1,     2,     3    ],
        "elo_rating": [2100.0, 2080.0, 1980.0],
        "elo_peak":   [2172.0, 2135.0, 2050.0],
    })


def test_update_elo_winner_gains():
    elo = _make_elo_df()
    updated = update_elo(elo, "ARG", "FRA", goals_a=2, goals_b=0)
    assert updated.loc[updated["iso_code"]=="ARG","elo_rating"].values[0] > 2100.0
    assert updated.loc[updated["iso_code"]=="FRA","elo_rating"].values[0] < 2080.0


def test_update_elo_draw_near_equal_teams():
    elo = _make_elo_df()
    updated = update_elo(elo, "ARG", "FRA", goals_a=1, goals_b=1)
    arg_new = updated.loc[updated["iso_code"]=="ARG","elo_rating"].values[0]
    fra_new = updated.loc[updated["iso_code"]=="FRA","elo_rating"].values[0]
    assert arg_new < 2100.0
    assert fra_new > 2080.0


def test_update_elo_sum_preserved():
    elo = _make_elo_df()
    updated = update_elo(elo, "ARG", "FRA", goals_a=3, goals_b=1)
    orig_sum = elo.loc[elo["iso_code"].isin(["ARG","FRA"]), "elo_rating"].sum()
    new_sum  = updated.loc[updated["iso_code"].isin(["ARG","FRA"]), "elo_rating"].sum()
    assert abs(orig_sum - new_sum) < 0.01


def test_update_elo_returns_copy():
    elo = _make_elo_df()
    update_elo(elo, "ARG", "FRA", goals_a=1, goals_b=0)
    assert elo.loc[elo["iso_code"]=="ARG","elo_rating"].values[0] == 2100.0


def test_log_result_creates_file(tmp_path):
    log_path = tmp_path / "results_log.csv"
    log_result(
        match_date="2026-06-15", iso_a="ARG", iso_b="FRA", host_iso=None,
        goals_a=2, goals_b=1,
        p_home=0.42, p_draw=0.24, p_away=0.34,
        source="wc2026", log_path=log_path,
    )
    assert log_path.exists()
    df = pd.read_csv(log_path)
    assert len(df) == 1
    assert df["iso_a"].iloc[0] == "ARG"
    # BS = (0.42-1)² + (0.24-0)² + (0.34-0)² = 0.3364+0.0576+0.1156
    expected_bs = (0.42-1)**2 + (0.24-0)**2 + (0.34-0)**2
    assert df["brier_score"].iloc[0] == pytest.approx(expected_bs, abs=0.001)


def test_log_result_appends(tmp_path):
    log_path = tmp_path / "results_log.csv"
    for i in range(3):
        log_result(
            match_date=f"2026-06-{15+i}", iso_a="ARG", iso_b="FRA", host_iso=None,
            goals_a=1, goals_b=0,
            p_home=0.5, p_draw=0.25, p_away=0.25,
            source="friendly", log_path=log_path,
        )
    df = pd.read_csv(log_path)
    assert len(df) == 3

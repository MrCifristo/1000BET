import numpy as np
import pandas as pd
import pytest

from src.model.features import build_xg_priority, compute_time_weights, impute_to_median, build_match_rows


def test_compute_time_weights_reference_year_is_one():
    weights = compute_time_weights(np.array([2022]), year_ref=2022, decay_rate=0.05)
    assert weights[0] == pytest.approx(1.0)


def test_compute_time_weights_decay_order():
    weights = compute_time_weights(np.array([2002, 2012, 2022]), year_ref=2022, decay_rate=0.05)
    assert weights[0] < weights[1] < weights[2]


def test_compute_time_weights_known_value():
    weights = compute_time_weights(np.array([2002]), year_ref=2022, decay_rate=0.05)
    assert weights[0] == pytest.approx(np.exp(-1.0), rel=1e-4)


def test_build_xg_priority_prefers_statsbomb():
    teams = pd.DataFrame({
        "sb_xg_per90": [1.2, np.nan],
        "sq_npxg_per90": [0.8, 0.9],
        "fb_npgls_per90": [0.5, 0.6],
    }, index=["ARG", "BRA"])
    xg = build_xg_priority(teams)
    assert xg["ARG"] == pytest.approx(1.2)
    assert xg["BRA"] == pytest.approx(0.9)


def test_build_xg_priority_falls_back_to_fbref():
    teams = pd.DataFrame({
        "sb_xg_per90": [np.nan],
        "sq_npxg_per90": [np.nan],
        "fb_npgls_per90": [0.192],
    }, index=["CUW"])
    xg = build_xg_priority(teams)
    assert xg["CUW"] == pytest.approx(0.192)


def test_build_xg_priority_returns_nan_when_all_missing():
    teams = pd.DataFrame({
        "sb_xg_per90": [np.nan],
        "sq_npxg_per90": [np.nan],
        "fb_npgls_per90": [np.nan],
    }, index=["ZZZ"])
    xg = build_xg_priority(teams)
    assert pd.isna(xg["ZZZ"])


def test_impute_to_median_fills_nan():
    s = pd.Series([1.0, 2.0, np.nan, 4.0])
    result = impute_to_median(s)
    assert result[2] == pytest.approx(2.0)
    assert result.isna().sum() == 0


def test_impute_to_median_no_nan_unchanged():
    s = pd.Series([1.0, 2.0, 3.0])
    result = impute_to_median(s)
    pd.testing.assert_series_equal(result, s)


def _make_teams_df():
    return pd.DataFrame({
        "iso_code": ["ARG", "FRA", "BRA", "DEU"],
        "elo_rating": [2100.0, 2080.0, 1980.0, 1950.0],
        "squad_value_m_eur": [800.0, 1400.0, 900.0, 700.0],
        "sb_xg_per90": [1.1, 1.0, 0.9, 0.8],
        "sq_npxg_per90": [np.nan, np.nan, np.nan, np.nan],
        "fb_npgls_per90": [np.nan, np.nan, np.nan, np.nan],
    })


def _make_matches_df():
    return pd.DataFrame({
        "home_team_iso": ["ARG", "BRA"],
        "away_team_iso": ["FRA", "DEU"],
        "home_team_score": [2, 1],
        "away_team_score": [1, 0],
        "year": [2022, 2018],
        "host_team_iso": [np.nan, np.nan],
    })


def test_build_match_rows_two_rows_per_match():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    assert len(rows) == 4


def test_build_match_rows_goals_for_correct():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["goals_for"] == 2
    assert fra_row["goals_for"] == 1


def test_build_match_rows_host_flag():
    matches = _make_matches_df().copy()
    matches["host_team_iso"] = matches["host_team_iso"].astype(object)
    matches.loc[0, "host_team_iso"] = "ARG"
    rows = build_match_rows(matches, _make_teams_df(), year_ref=2026, decay_rate=0.05)
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["host_flag"] == pytest.approx(1.0)
    assert fra_row["host_flag"] == pytest.approx(0.0)


def test_build_match_rows_time_weight_year_ref():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2022, decay_rate=0.05)
    row_2022 = rows[rows["year"] == 2022].iloc[0]
    assert row_2022["time_weight"] == pytest.approx(1.0)


def test_build_match_rows_elo_diff_sign():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["elo_diff"] > 0
    assert fra_row["elo_diff"] < 0
    assert arg_row["elo_diff"] == pytest.approx(-fra_row["elo_diff"])


def test_build_match_rows_no_nan_in_output():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    for col in ["goals_for", "time_weight", "host_flag", "elo_diff", "xg_diff", "log_value_ratio"]:
        assert rows[col].isna().sum() == 0, f"NaN en columna {col}"


def test_build_match_rows_custom_score_cols():
    matches = pd.DataFrame({
        "home_team_iso":   ["ARG"],
        "away_team_iso":   ["FRA"],
        "home_corners":    [7],
        "away_corners":    [5],
        "year":            [2022],
        "host_team_iso":   [np.nan],
    })
    rows = build_match_rows(
        matches, _make_teams_df(), year_ref=2026, decay_rate=0.05,
        home_score_col="home_corners", away_score_col="away_corners",
    )
    assert len(rows) == 2
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["goals_for"] == 7
    assert fra_row["goals_for"] == 5


def test_build_match_rows_default_score_col_unchanged():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    assert "goals_for" in rows.columns
    assert rows["goals_for"].iloc[0] == 2


def test_build_match_rows_always_paired():
    """Cuando un equipo no está en teams_df, se omite el partido completo (ambas filas)."""
    matches = pd.DataFrame({
        "home_team_iso":   ["ARG", "BRA"],
        "away_team_iso":   ["FRA", "DEU"],
        "home_team_score": [2, 1],
        "away_team_score": [1, 0],
        "year":            [2022, 2018],
        "host_team_iso":   [np.nan, np.nan],
    })
    teams_partial = _make_teams_df()[_make_teams_df()["iso_code"].isin(["ARG", "FRA"])]
    rows = build_match_rows(matches, teams_partial, year_ref=2026, decay_rate=0.05)
    assert len(rows) % 2 == 0
    assert len(rows) == 2

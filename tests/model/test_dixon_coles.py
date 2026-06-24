import numpy as np
import pandas as pd
import pytest

from src.model.poisson_model import PoissonModel


def _matches():
    """Dataset mixto con marcadores bajos (0-0, 1-1) para que ρ sea estimable."""
    records = []
    for _ in range(25):
        records += [
            {"home_team_iso":"A","away_team_iso":"B","home_team_score":2,"away_team_score":1,
             "year":2022,"host_team_iso":np.nan},
            {"home_team_iso":"B","away_team_iso":"A","home_team_score":1,"away_team_score":2,
             "year":2022,"host_team_iso":np.nan},
        ]
    # Añadir partidos de bajo marcador para que DC tenga señal
    for _ in range(15):
        records += [
            {"home_team_iso":"A","away_team_iso":"B","home_team_score":0,"away_team_score":0,
             "year":2022,"host_team_iso":np.nan},
            {"home_team_iso":"B","away_team_iso":"A","home_team_score":0,"away_team_score":0,
             "year":2022,"host_team_iso":np.nan},
            {"home_team_iso":"A","away_team_iso":"B","home_team_score":1,"away_team_score":1,
             "year":2022,"host_team_iso":np.nan},
            {"home_team_iso":"B","away_team_iso":"A","home_team_score":1,"away_team_score":1,
             "year":2022,"host_team_iso":np.nan},
        ]
    return pd.DataFrame(records)


def _teams():
    return pd.DataFrame({
        "iso_code":["A","B"],"elo_rating":[1800.0,1800.0],
        "squad_value_m_eur":[500.0,500.0],"sb_xg_per90":[1.0,1.0],
        "sq_npxg_per90":[np.nan,np.nan],"fb_npgls_per90":[np.nan,np.nan],
    })


def test_dc_model_has_rho_param():
    model = PoissonModel(use_dc=True).fit(_matches(), _teams(), year_ref=2022)
    assert "rho" in model.params_
    assert model.params_["rho"] <= 0.0


def test_dc_score_matrix_sums_to_one():
    model = PoissonModel(use_dc=True).fit(_matches(), _teams(), year_ref=2022)
    matrix = model.predict_score_matrix("A", "B")
    assert matrix.sum() == pytest.approx(1.0, abs=1e-3)


def test_dc_vs_standard_score_matrix_differs():
    m_dc  = PoissonModel(use_dc=True,  ridge_lambda=0.01).fit(_matches(), _teams(), year_ref=2022)
    m_std = PoissonModel(use_dc=False, ridge_lambda=0.01).fit(_matches(), _teams(), year_ref=2022)
    mat_dc  = m_dc.predict_score_matrix("A", "B")
    mat_std = m_std.predict_score_matrix("A", "B")
    low_score_cells = [(0,0),(1,0),(0,1),(1,1)]
    diffs = [abs(mat_dc[r,c] - mat_std[r,c]) for r,c in low_score_cells]
    assert max(diffs) > 1e-6


def test_dc_probabilities_sum_to_one():
    model = PoissonModel(use_dc=True).fit(_matches(), _teams(), year_ref=2022)
    result = model.predict_match("A", "B")
    assert abs(result["p_home"] + result["p_draw"] + result["p_away"] - 1.0) < 1e-3


def test_no_dc_model_backward_compatible():
    """use_dc=False produce el mismo comportamiento que el modelo original."""
    model = PoissonModel(use_dc=False, ridge_lambda=0.01).fit(_matches(), _teams(), year_ref=2022)
    result = model.predict_match("A", "B")
    assert abs(result["p_home"] + result["p_draw"] + result["p_away"] - 1.0) < 1e-3
    assert model.params_["rho"] == 0.0

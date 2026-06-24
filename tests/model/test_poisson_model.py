import numpy as np
import pandas as pd
import pytest

from src.model.poisson_model import PoissonModel


def _synthetic_matches():
    records = []
    for _ in range(30):
        records.append({
            "home_team_iso": "A", "away_team_iso": "B",
            "home_team_score": 2, "away_team_score": 1,
            "year": 2022, "host_team_iso": np.nan,
        })
        records.append({
            "home_team_iso": "B", "away_team_iso": "A",
            "home_team_score": 1, "away_team_score": 2,
            "year": 2022, "host_team_iso": np.nan,
        })
    return pd.DataFrame(records)


def _synthetic_teams():
    # Features iguales para que solo α/β absorban la diferencia de goles
    return pd.DataFrame({
        "iso_code":          ["A",    "B"   ],
        "elo_rating":        [1800.0, 1800.0],
        "squad_value_m_eur": [500.0,  500.0 ],
        "sb_xg_per90":       [1.0,    1.0   ],
        "sq_npxg_per90":     [np.nan, np.nan],
        "fb_npgls_per90":    [np.nan, np.nan],
    })


def test_fit_returns_self():
    model = PoissonModel(ridge_lambda=0.1, decay_rate=0.05)
    result = model.fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    assert result is model


def test_fit_sets_teams():
    model = PoissonModel().fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    assert set(model.teams_) == {"A", "B"}


def test_fit_attack_ordering():
    model = PoissonModel(ridge_lambda=0.01).fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    alpha = model.params_["alpha"]
    assert alpha["A"] > alpha["B"]


def test_fit_lambdas_correct():
    """El modelo debe predecir λ_A≈2 y λ_B≈1 dado el dataset sintético."""
    model = PoissonModel(ridge_lambda=0.01).fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    lam_a = model._lambda("A", "B", None)
    lam_b = model._lambda("B", "A", None)
    assert lam_a == pytest.approx(2.0, abs=0.1)
    assert lam_b == pytest.approx(1.0, abs=0.1)


@pytest.fixture
def fitted_model():
    model = PoissonModel(ridge_lambda=0.01, decay_rate=0.05)
    model.fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    return model


def test_predict_probabilities_sum_to_one(fitted_model):
    result = fitted_model.predict_match("A", "B")
    total = result["p_home"] + result["p_draw"] + result["p_away"]
    assert total == pytest.approx(1.0, abs=1e-3)


def test_predict_score_matrix_shape(fitted_model):
    matrix = fitted_model.predict_score_matrix("A", "B")
    assert matrix.shape == (9, 9)


def test_predict_score_matrix_sums_to_one(fitted_model):
    matrix = fitted_model.predict_score_matrix("A", "B")
    assert matrix.sum() == pytest.approx(1.0, abs=1e-3)


def test_predict_stronger_team_wins_more(fitted_model):
    result = fitted_model.predict_match("A", "B")
    assert result["p_home"] > result["p_away"]


def test_predict_symmetry_flipped(fitted_model):
    ab = fitted_model.predict_match("A", "B")
    ba = fitted_model.predict_match("B", "A")
    assert ab["p_home"] == pytest.approx(ba["p_away"], abs=1e-3)


def test_predict_likely_score_format(fitted_model):
    result = fitted_model.predict_match("A", "B")
    parts = result["likely_score"].split("-")
    assert len(parts) == 2
    assert all(p.isdigit() for p in parts)


def test_likely_score_prob_matches_top(fitted_model):
    """La probabilidad del marcador más probable debe ser la del top_scores[0]."""
    result = fitted_model.predict_match("A", "B")
    assert result["top_scores"][0][0] == result["likely_score"]
    assert result["likely_score_prob"] == pytest.approx(result["top_scores"][0][1])


def test_top_scores_are_three_descending(fitted_model):
    result = fitted_model.predict_match("A", "B")
    top = result["top_scores"]
    assert len(top) == 3
    probs = [p for _, p in top]
    assert probs == sorted(probs, reverse=True)
    assert all(0.0 < p < 1.0 for p in probs)


def test_coherent_score_agrees_with_modal_outcome(fitted_model):
    """El marcador coherente debe pertenecer al resultado 1X2 modal."""
    result = fitted_model.predict_match("A", "B")
    ph, pd_, pa = result["p_home"], result["p_draw"], result["p_away"]
    a, b = (int(x) for x in result["coherent_score"].split("-"))
    modal = max((ph, "home"), (pd_, "draw"), (pa, "away"))[1]
    if modal == "home":
        assert a > b
    elif modal == "away":
        assert a < b
    else:
        assert a == b


def test_coherent_draw_when_draw_is_modal():
    """Si el empate es el resultado modal, coherent_score es un empate aunque el
    argmax global de marcador no lo sea (el caso de la jornada 1).

    Dos equipos parejos y de bajo marcador (siempre 0-0) → λ bajo → el empate
    domina el 1X2."""
    recs = []
    for _ in range(40):
        recs.append({"home_team_iso": "A", "away_team_iso": "B",
                     "home_team_score": 0, "away_team_score": 0,
                     "year": 2022, "host_team_iso": np.nan})
        recs.append({"home_team_iso": "B", "away_team_iso": "A",
                     "home_team_score": 0, "away_team_score": 0,
                     "year": 2022, "host_team_iso": np.nan})
    model = PoissonModel(ridge_lambda=0.01).fit(
        pd.DataFrame(recs), _synthetic_teams(), year_ref=2022)
    res = model.predict_match("A", "B")
    assert res["modal_outcome"] == "draw"
    a, b = (int(x) for x in res["coherent_score"].split("-"))
    assert a == b

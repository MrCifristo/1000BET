"""
Validación del modelo de Poisson: Brier Score y Leave-One-Tournament-Out CV.
"""
from itertools import product

import numpy as np
import pandas as pd

from src.model.poisson_model import PoissonModel


def brier_score(predictions: list[dict], outcomes: list[str]) -> float:
    """
    Brier Score multiclase (3 resultados: home / draw / away).

    BS = (1/N) Σ [(p_home − o_home)² + (p_draw − o_draw)² + (p_away − o_away)²]

    Referencia: modelo naive (1/3, 1/3, 1/3) → BS ≈ 0.667.
    """
    total = 0.0
    for pred, outcome in zip(predictions, outcomes):
        o_home = 1.0 if outcome == "home"  else 0.0
        o_draw = 1.0 if outcome == "draw"  else 0.0
        o_away = 1.0 if outcome == "away"  else 0.0
        total += (pred["p_home"] - o_home) ** 2
        total += (pred["p_draw"] - o_draw) ** 2
        total += (pred["p_away"] - o_away) ** 2
    return total / len(predictions)


def loto_cv(
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    ridge_lambdas: list[float],
    decay_rates: list[float],
    year_ref_train: int = 2026,
    home_score_col: str = "home_team_score",
    away_score_col: str = "away_team_score",
) -> pd.DataFrame:
    """
    Leave-One-Tournament-Out cross-validation con grid search.

    Para cada combinación (ridge_lambda, decay_rate):
      Para cada año T de torneo en matches_df:
        - Entrenar con partidos de año != T
        - Predecir partidos de año == T
        - Calcular Brier Score del resultado (1X2)
      Retornar BS promedio.

    Nota: usa features de teams_df (estado actual) para todos los torneos.
    """
    tournament_years = sorted(matches_df["year"].unique())
    records = []

    for ridge, decay in product(ridge_lambdas, decay_rates):
        bs_per_tournament = []
        for test_year in tournament_years:
            train = matches_df[matches_df["year"] != test_year]
            test  = matches_df[matches_df["year"] == test_year]

            if len(train) == 0 or len(test) == 0:
                continue

            model = PoissonModel(ridge_lambda=ridge, decay_rate=decay)
            try:
                model.fit(train, teams_df, year_ref=year_ref_train,
                          home_score_col=home_score_col,
                          away_score_col=away_score_col)
            except Exception:
                continue

            preds, outcomes = [], []
            for _, match in test.iterrows():
                hi   = match["home_team_iso"]
                ai   = match["away_team_iso"]
                host = match.get("host_team_iso", np.nan)
                host = None if pd.isna(host) else host

                if hi not in model.teams_ or ai not in model.teams_:
                    continue

                pred = model.predict_match(hi, ai, host_iso=host)
                preds.append(pred)

                hs  = int(match[home_score_col])
                as_ = int(match[away_score_col])
                if hs > as_:
                    outcomes.append("home")
                elif hs == as_:
                    outcomes.append("draw")
                else:
                    outcomes.append("away")

            if preds:
                bs_per_tournament.append(brier_score(preds, outcomes))

        if bs_per_tournament:
            records.append({
                "ridge_lambda":   ridge,
                "decay_rate":     decay,
                "mean_bs":        float(np.mean(bs_per_tournament)),
                "std_bs":         float(np.std(bs_per_tournament)),
                "n_tournaments":  len(bs_per_tournament),
            })

    return pd.DataFrame(records).sort_values("mean_bs").reset_index(drop=True)

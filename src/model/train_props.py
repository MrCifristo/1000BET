"""
Fase 4 — Entrenamiento de submodelos de props (corners, tarjetas, disparos, faltas).

Carga statsbomb_match_props.csv, entrena 4 PoissonModel independientes via LOTO-CV,
ensambla MatchPredictor junto al modelo de goles ya entrenado, y guarda
outputs/match_predictor.pkl.

Requiere: outputs/poisson_model.pkl (correr python -m src.model.train primero).
"""
import pickle
from pathlib import Path

import pandas as pd

from src.model.match_predictor import MatchPredictor
from src.model.poisson_model import PoissonModel
from src.model.validation import loto_cv

ROOT            = Path(__file__).resolve().parents[2]
MATCH_PROPS_CSV = ROOT / "data/processed/statsbomb_match_props.csv"
PROP_STATS_CSV  = ROOT / "data/features/prop_team_stats.csv"
TEAMS_CSV       = ROOT / "data/features/teams_features_v3.csv"
GOALS_MODEL_PKL = ROOT / "outputs/poisson_model.pkl"
OUTPUT_PKL      = ROOT / "outputs/match_predictor.pkl"

RIDGE_LAMBDAS = [0.01, 0.05, 0.1, 0.5, 1.0]
DECAY_RATES   = [0.02, 0.05, 0.1]

MARKETS = {
    "corners": ("home_corners", "away_corners"),
    "cards":   ("home_yellow",  "away_yellow"),
    "shots":   ("home_shots",   "away_shots"),
    "fouls":   ("home_fouls",   "away_fouls"),
}

SANITY_MATCHES = [
    ("ARG", "FRA", None),
    ("ESP", "ENG", None),
    ("MEX", "USA", "MEX"),
    ("JPN", "DEU", None),
]


def main():
    print("=== train_props.py — Submodelos de props ===\n")

    match_props = pd.read_csv(MATCH_PROPS_CSV)
    prop_stats  = pd.read_csv(PROP_STATS_CSV)
    teams_base  = pd.read_csv(TEAMS_CSV)

    # Merge equipos con prop stats (las covariables del modelo son elo + squad_value + xG)
    teams_df = teams_base.merge(
        prop_stats[["iso_code", "prop_corners_per90", "prop_yellow_per90",
                    "prop_shots_per90", "prop_fouls_per90"]],
        on="iso_code", how="left",
    )

    print(f"Partidos StatsBomb: {len(match_props)}")
    print(f"Torneos: {sorted(match_props['year'].unique())}")
    print(f"Equipos con prop stats: {prop_stats['iso_code'].nunique()}/48")

    with open(GOALS_MODEL_PKL, "rb") as f:
        model_goals = pickle.load(f)
    print(f"Modelo de goles cargado desde {GOALS_MODEL_PKL.name}\n")

    trained = {}
    for market, (home_col, away_col) in MARKETS.items():
        print(f"  === {market.upper()} ===")
        print(f"  Grid search {len(RIDGE_LAMBDAS)}×{len(DECAY_RATES)} ...")
        cv = loto_cv(
            match_props, teams_df, RIDGE_LAMBDAS, DECAY_RATES,
            home_score_col=home_col, away_score_col=away_col,
        )
        best = cv.iloc[0]
        print(f"  Mejor: ridge={best['ridge_lambda']}, decay={best['decay_rate']}, BS={best['mean_bs']:.4f}")

        model = PoissonModel(
            ridge_lambda=float(best["ridge_lambda"]),
            decay_rate=float(best["decay_rate"]),
        )
        model.fit(match_props, teams_df, year_ref=2026,
                  home_score_col=home_col, away_score_col=away_col)
        trained[market] = model

    predictor = MatchPredictor(
        model_goals   = model_goals,
        model_corners = trained["corners"],
        model_cards   = trained["cards"],
        model_shots   = trained["shots"],
        model_fouls   = trained["fouls"],
    )

    print("\n\nSanity check — predicciones completas WC 2026:")
    for iso_a, iso_b, host in SANITY_MATCHES:
        if iso_a not in model_goals.teams_ or iso_b not in model_goals.teams_:
            continue
        r = predictor.predict_match(iso_a, iso_b, host_iso=host)
        print(f"\n{iso_a} vs {iso_b}" + (f" (sede: {host})" if host else ""))
        print(f"  Resultado:  {iso_a} {r['result']['p_home']:.0%} | Empate {r['result']['p_draw']:.0%} | {iso_b} {r['result']['p_away']:.0%}")
        print(f"  Goles:      exp={r['goals']['expected_total']} | O2.5={r['goals']['over_2_5']:.0%} | U2.5={r['goals']['under_2_5']:.0%} | BTTS={r['goals']['btts']:.0%}")
        print(f"  Corners:    exp={r['corners']['expected_total']} | O10.5={r['corners']['over_10_5']:.0%} | U10.5={r['corners']['under_10_5']:.0%}")
        print(f"  Tarjetas:   exp={r['cards']['expected_total']} | O3.5={r['cards']['over_3_5']:.0%} | U3.5={r['cards']['under_3_5']:.0%}")
        print(f"  Disparos:   exp={r['shots']['expected_total']} | O24.5={r['shots']['over_24_5']:.0%} | U24.5={r['shots']['under_24_5']:.0%}")
        print(f"  Faltas:     exp={r['fouls']['expected_total']} | O22.5={r['fouls']['over_22_5']:.0%} | U22.5={r['fouls']['under_22_5']:.0%}")

    OUTPUT_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PKL, "wb") as f:
        pickle.dump(predictor, f)
    print(f"\n\nMatchPredictor guardado → {OUTPUT_PKL.relative_to(ROOT)}")

    # Guardar hiperparámetros de props en best_params.json
    import json
    best_params_path = ROOT / "outputs/best_params.json"
    best_params = {}
    if best_params_path.exists():
        with open(best_params_path) as f:
            best_params = json.load(f)
    for market, model in [("corners", trained["corners"]), ("cards", trained["cards"]),
                           ("shots", trained["shots"]), ("fouls", trained["fouls"])]:
        best_params[market] = {"ridge_lambda": model.ridge_lambda, "decay_rate": model.decay_rate}
    with open(best_params_path, "w") as f:
        json.dump(best_params, f, indent=2)
    print(f"Hiperparámetros de props guardados → {best_params_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

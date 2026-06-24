"""
Fase 4 — Script de entrenamiento del modelo de Poisson bivariado (goles).

1. Grid search via LOTO-CV para tunear ridge_lambda y decay_rate
2. Entrena modelo final con los mejores hiperparámetros + corrección Dixon-Coles
3. Imprime sanity check: predicciones para 5 partidos representativos del WC 2026
4. Guarda modelo entrenado en outputs/poisson_model.pkl
5. Guarda mejores hiperparámetros en outputs/best_params.json
"""
import json
import pickle
from pathlib import Path

import pandas as pd

from src.model.poisson_model import PoissonModel
from src.model.validation import loto_cv

ROOT     = Path(__file__).resolve().parents[2]
MATCHES  = ROOT / "data/processed/matches_historical_v2.csv"
TEAMS    = ROOT / "data/features/teams_features_v2.csv"
OUT_PKL  = ROOT / "outputs/poisson_model.pkl"

RIDGE_LAMBDAS = [0.01, 0.05, 0.1, 0.5, 1.0]
DECAY_RATES   = [0.02, 0.05, 0.1]

SANITY_MATCHES = [
    ("ARG", "BRA", None),
    ("ESP", "FRA", None),
    ("MEX", "USA", "MEX"),
    ("JPN", "DEU", None),
    ("MAR", "PRT", None),
]


def main():
    print("=== train.py — Fase 4: Poisson Bivariado (Goles) ===\n")

    matches = pd.read_csv(MATCHES)
    teams   = pd.read_csv(TEAMS)

    print(f"Partidos históricos: {len(matches)} (años {matches['year'].min()}–{matches['year'].max()})")
    print(f"Torneos disponibles para LOTO-CV: {sorted(matches['year'].unique())}\n")
    print(f"Grid search: {len(RIDGE_LAMBDAS)} ridge_lambdas × {len(DECAY_RATES)} decay_rates")
    print("Esto puede tardar 5-15 minutos...\n")

    cv_results = loto_cv(matches, teams, RIDGE_LAMBDAS, DECAY_RATES)

    print("Top 5 combinaciones por Brier Score (menor = mejor):")
    print(cv_results.head(5).to_string(index=False))

    best       = cv_results.iloc[0]
    best_ridge = float(best["ridge_lambda"])
    best_decay = float(best["decay_rate"])
    print(f"\nMejores hiperparámetros → ridge_lambda={best_ridge}, decay_rate={best_decay}")
    print(f"Mean BS: {best['mean_bs']:.4f} ± {best['std_bs']:.4f}  (referencia naive: 0.6667)\n")

    print("Entrenando modelo final sobre todos los datos (con Dixon-Coles) ...")
    model = PoissonModel(ridge_lambda=best_ridge, decay_rate=best_decay, use_dc=True)
    model.fit(matches, teams, year_ref=2026)
    print(f"  Selecciones en el modelo: {len(model.teams_)}\n")

    print("Sanity check — predicciones WC 2026:")
    print(f"{'Partido':<15} {'P(A gana)':>9} {'P(Empate)':>9} {'P(B gana)':>9} {'Esperado':>10} {'Probable':>8}")
    print("-" * 65)
    for iso_a, iso_b, host in SANITY_MATCHES:
        if iso_a not in model.teams_ or iso_b not in model.teams_:
            print(f"  {iso_a} vs {iso_b}: omitido")
            continue
        r = model.predict_match(iso_a, iso_b, host_iso=host)
        print(f"{iso_a+' vs '+iso_b:<15} {r['p_home']:>9.3f} {r['p_draw']:>9.3f} {r['p_away']:>9.3f} "
              f"  {r['expected'][0]:.1f}-{r['expected'][1]:.1f}  {r['likely_score']:>8}")

    OUT_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PKL, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModelo guardado → {OUT_PKL.relative_to(ROOT)}")
    print(f"  ρ (Dixon-Coles): {model.params_['rho']:.4f}")

    # Guardar mejores hiperparámetros para re-entrenamiento futuro
    best_params_path = ROOT / "outputs/best_params.json"
    best_params = {"goals": {"ridge_lambda": best_ridge, "decay_rate": best_decay}}
    if best_params_path.exists():
        with open(best_params_path) as f:
            existing = json.load(f)
        existing.update(best_params)
        best_params = existing
    with open(best_params_path, "w") as f:
        json.dump(best_params, f, indent=2)
    print(f"Hiperparámetros guardados → {best_params_path.relative_to(ROOT)}")

    alpha    = model.params_["alpha"]
    top_att  = sorted(alpha.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 por parámetro de ataque (α):")
    for iso, val in top_att:
        print(f"  {iso}: {val:+.3f}")


if __name__ == "__main__":
    main()

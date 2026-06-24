"""
Fase 4 (v3) — Entrenamiento del modelo de goles con el corpus internacional ampliado.

Reemplaza el entrenamiento sobre solo-mundiales (484 partidos efectivos) por los
~22k partidos internacionales 2002+ con Elo rodante point-in-time.

Hiperparámetros ridge=1.0, decay=0.05 validados en banco de experimentos temporal
(src/evaluation/experiments.py). El barrido sobre 4 Mundiales (2010–2022, sin
leakage) mostró que regularizar fuerte los efectos fijos α/β (0.1→1.0) es el único
ajuste que mejora Brier Y log-loss a la vez:
  ridge 0.1 → Brier 0.5967 / LL 1.0050   (config vieja)
  ridge 1.0 → Brier 0.5931 / LL 0.9999   (config actual)
Esto corrige el sobreajuste de α/β (p.ej. "ataque" de minnows de OFC inflado por
calendario débil). Blend con Elo, peso por importancia, ablación de covariables y
calibración (temperature scaling) se probaron y NO ayudaron — ver experiments.py.

Salida: outputs/poisson_model.pkl  (consumido luego por train_props.py)
"""
import json
import pickle
from pathlib import Path

import pandas as pd

from src.model.poisson_model import PoissonModel

ROOT     = Path(__file__).resolve().parents[2]
MATCHES  = ROOT / "data/processed/matches_intl_v3.csv"
TEAMS    = ROOT / "data/features/teams_features_v3.csv"
OUT_PKL  = ROOT / "outputs/poisson_model.pkl"
PARAMS   = ROOT / "outputs/best_params.json"

RIDGE, DECAY = 1.0, 0.05

SANITY = [
    ("CAN", "UZB", None), ("HRV", "BEL", None), ("ARG", "BRA", None),
    ("ESP", "FRA", None), ("MEX", "USA", "MEX"), ("USA", "ENG", None),
]


def main():
    print("=== train_goals_intl.py — Goles con corpus internacional ===\n")
    matches = pd.read_csv(MATCHES)
    teams   = pd.read_csv(TEAMS)
    print(f"Corpus: {len(matches)} partidos ({matches['year'].min()}–{matches['year'].max()})")

    model = PoissonModel(ridge_lambda=RIDGE, decay_rate=DECAY, use_dc=True)
    model.fit(matches, teams, year_ref=2026, impute_missing=True)
    p = model.params_
    print(f"Equipos con α/β: {len(model.teams_)}")
    print(f"Pesos: mu={p['mu']:.3f} gamma={p['gamma']:.3f} delta(elo)={p['delta']:.4f} "
          f"eps(xg)={p['eps']:.4f} zeta(val)={p['zeta']:.4f} rho={p['rho']:.4f}\n")

    print("Sanity check WC 2026:")
    print(f"{'Partido':<14}{'P(A)':>7}{'P(X)':>7}{'P(B)':>7}{'Esperado':>11}")
    print("-" * 46)
    for a, b, h in SANITY:
        r = model.predict_match(a, b, host_iso=h)
        print(f"{a+' vs '+b:<14}{r['p_home']:>7.2f}{r['p_draw']:>7.2f}{r['p_away']:>7.2f}"
              f"{r['expected'][0]:>6.2f}-{r['expected'][1]:.2f}")

    OUT_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PKL, "wb") as f:
        pickle.dump(model, f)
    print(f"\nGuardado → {OUT_PKL.relative_to(ROOT)}")

    best_params = {}
    if PARAMS.exists():
        best_params = json.load(open(PARAMS))
    best_params["goals"] = {"ridge_lambda": RIDGE, "decay_rate": DECAY}
    json.dump(best_params, open(PARAMS, "w"), indent=2)


if __name__ == "__main__":
    main()

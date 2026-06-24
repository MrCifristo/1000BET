"""
Línea base honesta del modelo de goles (resultado 1X2).

Compara, vía Leave-One-Tournament-Out sobre los mundiales del corpus:
  1. Modelo actual    — Poisson con efectos fijos α/β + covariables (Elo, xG, valor)
  2. Baseline Elo-puro — solo la fórmula logística de Elo, SIN entrenar nada
  3. Baseline naive    — (1/3, 1/3, 1/3)

Métricas: Brier Score multiclase y log-loss (menor = mejor).

Punto clave de honestidad: cuenta cuántos partidos del test el modelo NO puede
predecir (algún equipo fuera del corpus de entrenamiento) en vez de esconderlos.
Si el baseline Elo-puro iguala o supera al modelo actual, los α/β están
destruyendo la señal de fuerza actual.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.model.poisson_model import PoissonModel

ROOT    = Path(__file__).resolve().parents[2]
MATCHES = ROOT / "data/processed/matches_historical_v2.csv"
TEAMS   = ROOT / "data/features/teams_features_v2.csv"

RIDGE = 0.1   # best_params actuales
DECAY = 0.05
EPS   = 1e-12


def outcome_of(hs: int, as_: int) -> str:
    if hs > as_:
        return "home"
    if hs == as_:
        return "draw"
    return "away"


def brier(p: dict, o: str) -> float:
    return ((p["p_home"] - (o == "home")) ** 2
            + (p["p_draw"] - (o == "draw")) ** 2
            + (p["p_away"] - (o == "away")) ** 2)


def logloss(p: dict, o: str) -> float:
    key = {"home": "p_home", "draw": "p_draw", "away": "p_away"}[o]
    return -np.log(max(p[key], EPS))


def elo_pure_probs(elo_a: float, elo_b: float, draw_rate: float,
                   host_a: bool = False, host_b: bool = False) -> dict:
    """
    1X2 derivado SOLO del Elo. El 'expected score' Elo = P(win) + 0.5·P(draw).
    Con draw_rate fijo (frecuencia empírica del train) se despejan P(home)/P(away).
    Ventaja de localía: +65 puntos Elo al anfitrión (convención eloratings.net).
    """
    dr = (elo_a + (65 if host_a else 0)) - (elo_b + (65 if host_b else 0))
    exp_a = 1.0 / (1.0 + 10.0 ** (-dr / 400.0))   # P(home) + 0.5·P(draw)
    p_home = exp_a - 0.5 * draw_rate
    p_away = (1.0 - exp_a) - 0.5 * draw_rate
    p_home = max(p_home, 0.0)
    p_away = max(p_away, 0.0)
    p_draw = draw_rate
    s = p_home + p_draw + p_away
    return {"p_home": p_home / s, "p_draw": p_draw / s, "p_away": p_away / s}


def main():
    matches = pd.read_csv(MATCHES)
    teams   = pd.read_csv(TEAMS)
    elo     = teams.set_index("iso_code")["elo_rating"].astype(float)
    in48    = set(teams["iso_code"])

    years = sorted(matches["year"].unique())

    # Cobertura del corpus: ¿cuántos partidos tienen AMBOS equipos en los 48?
    both_in = matches.apply(
        lambda m: m["home_team_iso"] in in48 and m["away_team_iso"] in in48, axis=1
    )
    print("=" * 64)
    print("COBERTURA DEL CORPUS")
    print("=" * 64)
    print(f"Partidos de Mundial totales (1930–2022): {len(matches)}")
    print(f"Partidos con AMBOS equipos en los 48 de 2026: {both_in.sum()} "
          f"({100*both_in.mean():.1f}%)")
    print(f"→ El modelo solo aprende de esos {both_in.sum()} partidos.\n")

    naive = {"p_home": 1/3, "p_draw": 1/3, "p_away": 1/3}

    acc = {  # acumuladores de métricas
        "model": {"bs": [], "ll": []},
        "elo":   {"bs": [], "ll": []},
        "naive": {"bs": [], "ll": []},
    }
    n_pred = n_skip_model = 0

    for test_year in years:
        train = matches[matches["year"] != test_year]
        test  = matches[matches["year"] == test_year]
        if len(train) == 0 or len(test) == 0:
            continue

        model = PoissonModel(ridge_lambda=RIDGE, decay_rate=DECAY, use_dc=True)
        try:
            model.fit(train, teams, year_ref=2026)
        except Exception as e:
            print(f"  [skip year {test_year}] fit falló: {e}")
            continue

        # draw_rate empírico del train (para el baseline Elo)
        tr_out = train.apply(
            lambda m: outcome_of(int(m["home_team_score"]), int(m["away_team_score"])),
            axis=1,
        )
        draw_rate = float((tr_out == "draw").mean())

        for _, m in test.iterrows():
            hi, ai = m["home_team_iso"], m["away_team_iso"]
            host   = m.get("host_team_iso", np.nan)
            host   = None if pd.isna(host) else host
            o      = outcome_of(int(m["home_team_score"]), int(m["away_team_score"]))

            # Solo evaluamos partidos donde ambos equipos tienen Elo (están en los 48),
            # para comparar manzanas con manzanas entre modelo y baseline.
            if hi not in in48 or ai not in in48:
                continue
            n_pred += 1

            # Modelo actual (si algún equipo no entró al corpus de train → no puede)
            if hi in model.teams_ and ai in model.teams_:
                pm = model.predict_match(hi, ai, host_iso=host)
                acc["model"]["bs"].append(brier(pm, o))
                acc["model"]["ll"].append(logloss(pm, o))
            else:
                n_skip_model += 1  # el modelo "no sabe" → cae a naive implícito
                acc["model"]["bs"].append(brier(naive, o))
                acc["model"]["ll"].append(logloss(naive, o))

            # Baseline Elo-puro
            pe = elo_pure_probs(elo[hi], elo[ai], draw_rate,
                                host_a=(hi == host), host_b=(ai == host))
            acc["elo"]["bs"].append(brier(pe, o))
            acc["elo"]["ll"].append(logloss(pe, o))

            # Naive
            acc["naive"]["bs"].append(brier(naive, o))
            acc["naive"]["ll"].append(logloss(naive, o))

    print("=" * 64)
    print("RESULTADOS LOTO-CV  (sobre partidos con ambos equipos en los 48)")
    print("=" * 64)
    print(f"Partidos evaluados: {n_pred}")
    print(f"De esos, el modelo NO pudo predecir (equipo fuera del train, "
          f"cae a naive): {n_skip_model} ({100*n_skip_model/max(n_pred,1):.1f}%)\n")

    print(f"{'Modelo':<22}{'Brier ↓':>12}{'Log-loss ↓':>14}")
    print("-" * 48)
    labels = {"model": "Actual (α/β+cov)", "elo": "Elo-puro", "naive": "Naive (1/3)"}
    for k in ["model", "elo", "naive"]:
        bs = np.mean(acc[k]["bs"])
        ll = np.mean(acc[k]["ll"])
        print(f"{labels[k]:<22}{bs:>12.4f}{ll:>14.4f}")

    print("\nInterpretación:")
    bs_m, bs_e = np.mean(acc["model"]["bs"]), np.mean(acc["elo"]["bs"])
    if bs_e <= bs_m:
        print(f"  ⚠️  El Elo-puro ({bs_e:.4f}) iguala o SUPERA al modelo actual "
              f"({bs_m:.4f}).")
        print("      El modelo está desperdiciando su mejor señal de entrada.")
    else:
        print(f"  El modelo ({bs_m:.4f}) supera al Elo-puro ({bs_e:.4f}) por "
              f"{bs_e - bs_m:.4f}.")


if __name__ == "__main__":
    main()

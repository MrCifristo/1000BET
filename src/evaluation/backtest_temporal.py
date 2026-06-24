"""
Backtest temporal honesto del modelo de goles con el corpus internacional ampliado.

Para cada Mundial reciente (2010, 2014, 2018, 2022):
  - Entrena SOLO con partidos internacionales ANTERIORES al inicio del torneo
    (sin leakage temporal).
  - Predice cada partido del torneo usando el Elo point-in-time de ese momento
    (elo_*_pre del corpus), no el Elo actual de 2026.
  - Compara contra baseline Elo-puro (point-in-time) y naive.

Métrica: Brier Score multiclase y log-loss (menor = mejor).
Referencia: la línea base del modelo viejo (solo-mundiales) era Brier 0.6128.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.model.poisson_model import PoissonModel

ROOT    = Path(__file__).resolve().parents[2]
MATCHES = ROOT / "data/processed/matches_intl_v3.csv"
TEAMS   = ROOT / "data/features/teams_features_v3.csv"

RIDGE, DECAY = 1.0, 0.05  # ridge 0.1→1.0 tras barrido en experiments.py (regulariza α/β)
WC_YEARS = [2010, 2014, 2018, 2022]
EPS = 1e-12


def outcome_of(hs, as_):
    return "home" if hs > as_ else ("draw" if hs == as_ else "away")


def brier(p, o):
    return ((p["p_home"] - (o == "home")) ** 2
            + (p["p_draw"] - (o == "draw")) ** 2
            + (p["p_away"] - (o == "away")) ** 2)


def logloss(p, o):
    return -np.log(max(p[{"home": "p_home", "draw": "p_draw", "away": "p_away"}[o]], EPS))


def rps(p, o):
    """Ranked Probability Score sobre el resultado ordinal [home, draw, away].
    Penaliza menos los errores 'cercanos' (predecir local cuando fue empate pesa
    menos que predecir local cuando fue visitante). Menor = mejor."""
    probs = [p["p_home"], p["p_draw"], p["p_away"]]
    obs   = [float(o == "home"), float(o == "draw"), float(o == "away")]
    cum_p = cum_o = 0.0
    total = 0.0
    for i in range(2):                       # r-1 = 2 sumandos acumulados
        cum_p += probs[i]; cum_o += obs[i]
        total += (cum_p - cum_o) ** 2
    return total / 2.0


def elo_pure(elo_a, elo_b, draw_rate):
    exp_a = 1.0 / (1.0 + 10.0 ** (-(elo_a - elo_b) / 400.0))
    ph, pa = max(exp_a - 0.5 * draw_rate, 0.0), max((1 - exp_a) - 0.5 * draw_rate, 0.0)
    s = ph + draw_rate + pa
    return {"p_home": ph / s, "p_draw": draw_rate / s, "p_away": pa / s}


def main():
    df = pd.read_csv(MATCHES, parse_dates=["date"])
    teams = pd.read_csv(TEAMS)
    naive = {"p_home": 1/3, "p_draw": 1/3, "p_away": 1/3}

    acc = {k: {"bs": [], "ll": [], "rps": []} for k in ("model", "elo", "naive")}
    # Aciertos de marcador exacto: argmax global vs marcador coherente con 1X2 modal.
    score_hits = {"likely": 0, "coherent": 0}
    n_total = 0

    for wc_year in WC_YEARS:
        wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"].dt.year == wc_year)]
        if wc.empty:
            continue
        cutoff = wc["date"].min()
        train = df[df["date"] < cutoff]
        draw_rate = float((train["home_team_score"] == train["away_team_score"]).mean())

        model = PoissonModel(ridge_lambda=RIDGE, decay_rate=DECAY, use_dc=True)
        model.fit(train, teams, year_ref=wc_year, impute_missing=True)

        n_wc = 0
        for m in wc.itertuples(index=False):
            hi, ai = m.home_team_iso, m.away_team_iso
            host = None if pd.isna(m.host_team_iso) else m.host_team_iso
            o = outcome_of(int(m.home_team_score), int(m.away_team_score))
            ovr = {hi: float(m.elo_home_pre), ai: float(m.elo_away_pre)}

            pm = model.predict_match(hi, ai, host_iso=host, elo_override=ovr)
            acc["model"]["bs"].append(brier(pm, o)); acc["model"]["ll"].append(logloss(pm, o))
            acc["model"]["rps"].append(rps(pm, o))

            real_score = f"{int(m.home_team_score)}-{int(m.away_team_score)}"
            score_hits["likely"]   += (pm["likely_score"]   == real_score)
            score_hits["coherent"] += (pm["coherent_score"] == real_score)

            pe = elo_pure(m.elo_home_pre + (100 if host == hi else 0),
                          m.elo_away_pre + (100 if host == ai else 0), draw_rate)
            acc["elo"]["bs"].append(brier(pe, o)); acc["elo"]["ll"].append(logloss(pe, o))
            acc["elo"]["rps"].append(rps(pe, o))

            acc["naive"]["bs"].append(brier(naive, o)); acc["naive"]["ll"].append(logloss(naive, o))
            acc["naive"]["rps"].append(rps(naive, o))
            n_wc += 1
        n_total += n_wc
        print(f"WC {wc_year}: {n_wc} partidos | train={len(train)} partidos previos")

    print("\n" + "=" * 56)
    print(f"BACKTEST TEMPORAL — {n_total} partidos de Mundial (2010–2022)")
    print("=" * 56)
    print(f"{'Modelo':<26}{'Brier ↓':>12}{'Log-loss ↓':>14}{'RPS ↓':>10}")
    print("-" * 62)
    lbl = {"model": "Nuevo (corpus ampliado)", "elo": "Elo-puro (point-in-time)", "naive": "Naive (1/3)"}
    for k in ("model", "elo", "naive"):
        print(f"{lbl[k]:<26}{np.mean(acc[k]['bs']):>12.4f}"
              f"{np.mean(acc[k]['ll']):>14.4f}{np.mean(acc[k]['rps']):>10.4f}")
    print(f"\nReferencia modelo VIEJO (solo-mundiales, LOTO): Brier 0.6128")
    print(f"Modelo NUEVO: Brier {np.mean(acc['model']['bs']):.4f} "
          f"→ mejora de {0.6128 - np.mean(acc['model']['bs']):+.4f}")

    # Acierto de marcador EXACTO (mercado correct-score): el techo realista ronda
    # 9-12% — incluso el marcador más probable es improbable en términos absolutos.
    print("\n" + "-" * 62)
    print("Acierto de marcador exacto (correct score):")
    print(f"  argmax global  : {score_hits['likely']:>4}/{n_total} "
          f"({100*score_hits['likely']/n_total:.1f}%)")
    print(f"  coherente 1X2  : {score_hits['coherent']:>4}/{n_total} "
          f"({100*score_hits['coherent']/n_total:.1f}%)")


if __name__ == "__main__":
    main()

"""
Fase 4-datos — Elo rodante point-in-time (World Football Elo system).

Recorre los 22k partidos internacionales (2002+) en orden cronológico y mantiene
un rating Elo por selección. Para cada partido registra el Elo PRE-partido de
ambos equipos (sin leakage) y al final guarda el Elo actual de cada selección.

Sistema (eloratings.net / World Football Elo):
  - K por importancia del torneo: Mundial=60, copa continental=50,
    eliminatorias/Nations League=40, otros torneos=30, amistoso=20.
  - Factor de margen de gol G: 1 (≤1), 1.5 (=2), (11+m)/8 (≥3).
  - Ventaja de localía: +100 al Elo del local (solo si la cancha no es neutral).
  - Todos parten de 1500; con cientos de partidos por equipo convergen al 2026.

Salidas:
  - data/processed/matches_intl_v3.csv  (+ columnas elo_home_pre, elo_away_pre)
  - data/features/elo_ratings_rolling.csv  (iso_code, elo_rating, elo_rank, n_matches)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT     = Path(__file__).resolve().parents[2]
MATCHES  = ROOT / "data/processed/matches_intl_v3.csv"
OUT_ELO  = ROOT / "data/features/elo_ratings_rolling.csv"
TEAMS    = ROOT / "data/features/teams_features_v2.csv"

INIT_ELO = 1500.0
HFA      = 100.0   # ventaja de localía en puntos Elo


def k_for(tournament: str) -> float:
    t = tournament.lower()
    if "world cup" in t and "qualif" not in t:
        return 60.0
    if "qualif" in t or "nations league" in t:
        return 40.0
    if any(x in t for x in (
        "uefa euro", "copa américa", "copa america",
        "african cup of nations", "afc asian cup",
        "gold cup", "confederations cup", "copa rica",
    )):
        return 50.0
    if "friendly" in t:
        return 20.0
    return 30.0


def g_for(margin: int) -> float:
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11.0 + margin) / 8.0


def main():
    df = pd.read_csv(MATCHES).sort_values("date").reset_index(drop=True)
    print(f"Partidos para Elo rodante: {len(df)}")

    elo: dict[str, float] = {}
    n_matches: dict[str, int] = {}
    home_pre = np.empty(len(df))
    away_pre = np.empty(len(df))

    for i, m in enumerate(df.itertuples(index=False)):
        h, a = m.home_team_iso, m.away_team_iso
        eh = elo.get(h, INIT_ELO)
        ea = elo.get(a, INIT_ELO)
        home_pre[i] = eh
        away_pre[i] = ea

        neutral = bool(m.neutral_venue)
        dr  = eh - ea + (0.0 if neutral else HFA)
        e_h = 1.0 / (1.0 + 10.0 ** (-dr / 400.0))

        hs, as_ = int(m.home_team_score), int(m.away_team_score)
        w_h = 1.0 if hs > as_ else (0.5 if hs == as_ else 0.0)

        k     = k_for(str(m.tournament))
        g     = g_for(abs(hs - as_))
        delta = k * g * (w_h - e_h)

        elo[h] = eh + delta
        elo[a] = ea - delta
        n_matches[h] = n_matches.get(h, 0) + 1
        n_matches[a] = n_matches.get(a, 0) + 1

    df["elo_home_pre"] = np.round(home_pre, 1)
    df["elo_away_pre"] = np.round(away_pre, 1)
    df.to_csv(MATCHES, index=False)
    print(f"Elo pre-partido añadido → {MATCHES.relative_to(ROOT)}")

    elo_df = (pd.DataFrame({"iso_code": list(elo.keys()),
                            "elo_rating": [round(v, 1) for v in elo.values()],
                            "n_matches": [n_matches[k] for k in elo.keys()]})
              .sort_values("elo_rating", ascending=False)
              .reset_index(drop=True))
    elo_df["elo_rank"] = elo_df.index + 1
    elo_df = elo_df[["iso_code", "elo_rank", "elo_rating", "n_matches"]]
    OUT_ELO.parent.mkdir(parents=True, exist_ok=True)
    elo_df.to_csv(OUT_ELO, index=False)
    print(f"Elo actual guardado → {OUT_ELO.relative_to(ROOT)}  ({len(elo_df)} equipos)\n")

    # Sanity check
    print("Top 15 Elo (debería ser ~ARG/FRA/ESP/BRA arriba):")
    print(elo_df.head(15).to_string(index=False))
    teams48 = set(pd.read_csv(TEAMS)["iso_code"])
    print("\nElo de selecciones de referencia:")
    ref = elo_df[elo_df["iso_code"].isin(
        ["CAN", "UZB", "HRV", "BEL", "ARG", "ESP", "BRA", "FRA", "USA", "MEX"])]
    print(ref.to_string(index=False))
    miss = teams48 - set(elo_df["iso_code"])
    if miss:
        print(f"\n⚠️ Equipos de los 48 SIN Elo rodante: {miss}")


if __name__ == "__main__":
    main()

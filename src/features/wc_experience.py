"""
wc_experience.py — Features de experiencia mundialista por selección.

Para cada selección clasificada al Mundial 2026, calcula su historial en Mundiales
masculinos hasta 2022 (con aliases históricos aplicados).

Features:
  - wc_appearances              # de ediciones en las que participó
  - wc_matches                  # partidos jugados
  - wc_wins / wc_draws / wc_losses
  - wc_win_rate                 wins / matches
  - wc_points_per_match         (3*W + 1*D) / matches
  - wc_goals_for / wc_goals_against
  - wc_goal_diff_per_match
  - wc_knockout_matches         # partidos en fase de eliminación directa
  - wc_best_stage_reached       string: 'final', 'semi-finals', 'quarter-finals', 'round of 16', 'group stage', 'never'
  - wc_years_since_last_appearance   2026 menos último año en el que jugó
  - wc_finals_played            # apariciones en finales

Las selecciones debutantes (Cape Verde, Curaçao, Uzbekistan, Jordan) reciben ceros + best_stage='never'.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
REFERENCE = PROJECT_ROOT / "data" / "raw" / "reference"
FEATURES_DIR = PROJECT_ROOT / "data" / "features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)


STAGE_RANK = {
    "final": 7,
    "third place match": 6,
    "semi-finals": 5,
    "quarter-finals": 4,
    "round of 16": 3,
    "second group stage": 2,
    "final round": 2,
    "group stage": 1,
    "never": 0,
}
# Mapeo inverso para imprimir
RANK_TO_STAGE = {v: k for k, v in STAGE_RANK.items()}


def best_stage_from_matches(team_matches: pd.DataFrame) -> str:
    """Determina la mejor etapa alcanzada (no la jugada): si jugó la final, su mejor etapa es 'final'.
       Tercer puesto se trata como mejor que semis (ranking 6) por convención."""
    if len(team_matches) == 0:
        return "never"
    ranks = team_matches["stage"].map(STAGE_RANK).fillna(0)
    return RANK_TO_STAGE.get(int(ranks.max()), "group stage")


def compute_team_experience(iso: str, historical: pd.DataFrame, reference_year: int = 2026) -> dict:
    """Calcula features de experiencia para una selección."""
    home = historical[historical["home_team_iso"] == iso]
    away = historical[historical["away_team_iso"] == iso]

    appearances = pd.concat([home["year"], away["year"]]).nunique()
    matches = len(home) + len(away)

    if matches == 0:
        return {
            "iso_code": iso,
            "wc_appearances": 0,
            "wc_matches": 0,
            "wc_wins": 0,
            "wc_draws": 0,
            "wc_losses": 0,
            "wc_win_rate": 0.0,
            "wc_points_per_match": 0.0,
            "wc_goals_for": 0,
            "wc_goals_against": 0,
            "wc_goal_diff_per_match": 0.0,
            "wc_knockout_matches": 0,
            "wc_best_stage_reached": "never",
            "wc_years_since_last_appearance": pd.NA,
            "wc_finals_played": 0,
        }

    # Resultados desde la perspectiva de la selección
    home_wins = (home["result_1x2"] == "H").sum()
    home_losses = (home["result_1x2"] == "A").sum()
    home_draws = (home["result_1x2"] == "D").sum()
    away_wins = (away["result_1x2"] == "A").sum()
    away_losses = (away["result_1x2"] == "H").sum()
    away_draws = (away["result_1x2"] == "D").sum()

    wins = int(home_wins + away_wins)
    losses = int(home_losses + away_losses)
    draws = int(home_draws + away_draws)

    goals_for = int(home["home_team_score"].sum() + away["away_team_score"].sum())
    goals_against = int(home["away_team_score"].sum() + away["home_team_score"].sum())

    # Concatenamos para evaluar etapas y knockout
    all_team_matches = pd.concat([home, away])
    knockout_matches = int(all_team_matches["knockout_stage"].sum())
    finals_played = int((all_team_matches["stage"] == "final").sum())
    best_stage = best_stage_from_matches(all_team_matches)
    last_year = int(all_team_matches["year"].max())

    return {
        "iso_code": iso,
        "wc_appearances": int(appearances),
        "wc_matches": matches,
        "wc_wins": wins,
        "wc_draws": draws,
        "wc_losses": losses,
        "wc_win_rate": wins / matches,
        "wc_points_per_match": (3 * wins + draws) / matches,
        "wc_goals_for": goals_for,
        "wc_goals_against": goals_against,
        "wc_goal_diff_per_match": (goals_for - goals_against) / matches,
        "wc_knockout_matches": knockout_matches,
        "wc_best_stage_reached": best_stage,
        "wc_years_since_last_appearance": reference_year - last_year,
        "wc_finals_played": finals_played,
    }


def main() -> None:
    print(">>> Cargando matches_historical_v2 y mapeo de selecciones 2026...")
    historical = pd.read_csv(PROCESSED / "matches_historical_v2.csv")
    teams_2026 = pd.read_csv(REFERENCE / "team_codes_mapping.csv")

    rows = [compute_team_experience(iso, historical) for iso in teams_2026["iso_code"]]
    df = pd.DataFrame(rows)

    # Para presentación: orden por puntos-por-partido desc (potencia "raw")
    df_sorted = df.sort_values("wc_points_per_match", ascending=False).reset_index(drop=True)

    out = FEATURES_DIR / "team_wc_experience.csv"
    df.to_csv(out, index=False)

    print(f">>> Escrito {out.relative_to(PROJECT_ROOT)} ({len(df)} selecciones)")
    print()
    print("Top 10 por puntos/partido en Mundiales (mín. 10 partidos):")
    top = df_sorted[df_sorted["wc_matches"] >= 10].head(10)
    print(top[["iso_code", "wc_appearances", "wc_matches", "wc_wins", "wc_draws",
               "wc_losses", "wc_points_per_match", "wc_goal_diff_per_match",
               "wc_best_stage_reached"]].to_string(index=False))
    print()
    debutants = df[df["wc_matches"] == 0]
    print(f"Debutantes en 2026 (sin historia mundialista): "
          f"{', '.join(debutants['iso_code'])}")


if __name__ == "__main__":
    main()

"""
upset_index.py — "Factor sorpresa" features.

Tres componentes que tratan de capturar la "imprevisibilidad" / capacidad de upset
de una selección, derivados puramente del historial mundialista (sin usar Elo aún —
eso entra en Phase 3).

  1) goal_diff_stdev_wc
       Desviación estándar de (goles_propios - goles_rivales) por partido.
       Alta = errático (puede romper 5-0 o perder 0-3). Bajo = consistente.
       Útil para representar la "varianza" alrededor de su nivel medio.

  2) upset_rate
       % de partidos donde la selección ganó o empató CONTRA un rival que en ese momento
       tenía más wins acumulados en Mundiales. La idea: cuántas veces "el chico" sacó
       resultado contra "el grande" históricamente.
       NOTA: usa wins acumulados al inicio del partido (no incluye el partido actual)
       como proxy de "prestigio histórico" en ausencia de Elo.

  3) recent_form_delta
       Goles_for_per_match en los últimos 2 Mundiales menos en todos los anteriores.
       Positivo: están viniendo mejor de lo normal (sorpresa "alta probable").
       Negativo: están viniendo peor de lo histórico (caída).

Las debutantes (Cape Verde, Curaçao, Jordan, Uzbekistan) reciben NaN — no hay historia.
El consolidate.py final imputará valores razonables (e.g. medianas + flag is_debutant).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
REFERENCE = PROJECT_ROOT / "data" / "raw" / "reference"
FEATURES_DIR = PROJECT_ROOT / "data" / "features"


def long_format(historical: pd.DataFrame) -> pd.DataFrame:
    """Convierte matches en formato 'una fila por (team_iso, partido)' con perspectiva del equipo."""
    home = historical.rename(columns={
        "home_team_iso": "team_iso",
        "away_team_iso": "opponent_iso",
        "home_team_score": "goals_for",
        "away_team_score": "goals_against",
    })[["match_id", "year", "match_date", "team_iso", "opponent_iso",
        "goals_for", "goals_against", "result_1x2"]]
    home["is_home"] = True
    home["team_won"] = home["result_1x2"] == "H"
    home["team_drew"] = home["result_1x2"] == "D"

    away = historical.rename(columns={
        "away_team_iso": "team_iso",
        "home_team_iso": "opponent_iso",
        "away_team_score": "goals_for",
        "home_team_score": "goals_against",
    })[["match_id", "year", "match_date", "team_iso", "opponent_iso",
        "goals_for", "goals_against", "result_1x2"]]
    away["is_home"] = False
    away["team_won"] = away["result_1x2"] == "A"
    away["team_drew"] = away["result_1x2"] == "D"

    long = pd.concat([home, away], ignore_index=True)
    long["match_date"] = pd.to_datetime(long["match_date"])
    long["goal_diff"] = long["goals_for"] - long["goals_against"]
    return long.sort_values("match_date").reset_index(drop=True)


def compute_cumulative_wins(long: pd.DataFrame) -> pd.DataFrame:
    """Para cada (team, partido) calcula wins acumulados ANTES del partido."""
    long = long.sort_values(["team_iso", "match_date"]).copy()
    long["wins_before"] = long.groupby("team_iso")["team_won"].cumsum() - long["team_won"].astype(int)
    return long


def compute_upset_rate(long: pd.DataFrame) -> pd.Series:
    """% partidos donde team ganó o empató contra rival con MÁS wins acumulados al inicio del partido."""
    # Para cada partido del team, necesitamos los wins acumulados del oponente en ese momento.
    # Hacemos un self-merge: cada fila (team, match) busca la fila (opponent, match) y obtiene
    # los wins_before del oponente.
    opp = long[["match_id", "team_iso", "wins_before"]].rename(
        columns={"team_iso": "opponent_iso", "wins_before": "opp_wins_before"}
    )
    merged = long.merge(opp, on=["match_id", "opponent_iso"], how="left")
    # "Underdog opportunity" = opp tenía MÁS wins que team al inicio del partido
    merged["is_underdog"] = merged["opp_wins_before"] > merged["wins_before"]
    merged["got_result"] = merged["team_won"] | merged["team_drew"]
    merged["is_upset"] = merged["is_underdog"] & merged["got_result"]

    grouped = merged.groupby("team_iso").agg(
        upset_opportunities=("is_underdog", "sum"),
        upset_count=("is_upset", "sum"),
    )
    grouped["upset_rate"] = np.where(
        grouped["upset_opportunities"] > 0,
        grouped["upset_count"] / grouped["upset_opportunities"],
        np.nan,
    )
    return grouped


def compute_recent_form_delta(long: pd.DataFrame, recent_n_tournaments: int = 2) -> pd.Series:
    """Diferencia entre goles/partido en últimos N Mundiales vs historia previa."""
    deltas = {}
    for team, g in long.groupby("team_iso"):
        years_sorted = sorted(g["year"].unique())
        if len(years_sorted) < 2:
            deltas[team] = np.nan
            continue
        recent_years = years_sorted[-recent_n_tournaments:]
        prior_years = years_sorted[:-recent_n_tournaments]
        if not prior_years:
            deltas[team] = np.nan
            continue
        recent = g[g["year"].isin(recent_years)]
        prior = g[g["year"].isin(prior_years)]
        delta = recent["goals_for"].mean() - prior["goals_for"].mean()
        deltas[team] = delta
    return pd.Series(deltas, name="recent_form_delta")


def main() -> None:
    print(">>> Cargando matches_historical_v2...")
    historical = pd.read_csv(PROCESSED / "matches_historical_v2.csv")
    teams_2026 = pd.read_csv(REFERENCE / "team_codes_mapping.csv")

    long = long_format(historical)
    long = compute_cumulative_wins(long)

    # (1) Volatility: stdev del goal_diff
    goal_diff_stdev = long.groupby("team_iso")["goal_diff"].std(ddof=0).rename("goal_diff_stdev_wc")

    # (2) Upset rate
    upset_data = compute_upset_rate(long)

    # (3) Recent form delta
    recent_delta = compute_recent_form_delta(long, recent_n_tournaments=2)

    df = pd.DataFrame({"iso_code": teams_2026["iso_code"]})
    df = df.merge(goal_diff_stdev.reset_index().rename(columns={"team_iso": "iso_code"}),
                  on="iso_code", how="left")
    df = df.merge(upset_data.reset_index().rename(columns={"team_iso": "iso_code"}),
                  on="iso_code", how="left")
    df = df.merge(recent_delta.reset_index().rename(columns={"index": "iso_code"}),
                  on="iso_code", how="left")

    df["is_debutant_2026"] = df["upset_opportunities"].isna().astype(int)

    out = FEATURES_DIR / "team_upset_index.csv"
    df.to_csv(out, index=False)

    print(f">>> Escrito {out.relative_to(PROJECT_ROOT)} ({len(df)} selecciones)")
    print()
    print("Top 10 por upset_rate (sorpresas históricas, mín. 5 oportunidades):")
    qualified = df[df["upset_opportunities"] >= 5].copy()
    print(qualified.sort_values("upset_rate", ascending=False).head(10)[
        ["iso_code", "upset_opportunities", "upset_count", "upset_rate",
         "goal_diff_stdev_wc", "recent_form_delta"]
    ].to_string(index=False))
    print()
    print("Top 10 más volátiles (alto goal_diff_stdev) — partidos impredecibles:")
    print(df.sort_values("goal_diff_stdev_wc", ascending=False).head(10)[
        ["iso_code", "goal_diff_stdev_wc", "upset_rate", "recent_form_delta"]
    ].to_string(index=False))
    print()
    print("Top 10 mejorando recientemente (recent_form_delta + alto):")
    print(df.sort_values("recent_form_delta", ascending=False).head(10)[
        ["iso_code", "recent_form_delta", "upset_rate"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()

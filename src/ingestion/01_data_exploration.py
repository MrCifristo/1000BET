"""
01_data_exploration.py

Fase 1 — Carga, explora y consolida los datos base del proyecto:
  - Fjelstul World Cup DB (CSV histórico 1930–2022)
  - openfootball/worldcup.json (fixtures 2018, 2022, 2026)

Salidas (en data/processed/):
  - matches_historical.csv  -> base de entrenamiento (todos los partidos de Mundiales masculinos)
  - matches_2026_fixtures.csv -> fixtures del Mundial 2026 a predecir
  - exploration_summary.txt -> resumen legible de la exploración

Ejecutar:
    cd mundial2026-predictor
    source .venv/bin/activate
    python src/ingestion/01_data_exploration.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FJELSTUL = PROJECT_ROOT / "data" / "raw" / "fjelstul"
RAW_OPENFOOTBALL = PROJECT_ROOT / "data" / "raw" / "openfootball"
PROCESSED = PROJECT_ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_fjelstul_tables() -> dict[str, pd.DataFrame]:
    """Lee las tablas core de Fjelstul que usaremos en Fase 1."""
    tables = {}
    for name in ("matches", "teams", "tournaments"):
        path = RAW_FJELSTUL / f"{name}.csv"
        tables[name] = pd.read_csv(path)
    return tables


def load_openfootball(year: int) -> list[dict]:
    """Lee la lista de matches de openfootball para un año dado."""
    path = RAW_OPENFOOTBALL / str(year) / "worldcup.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f).get("matches", [])


# ---------------------------------------------------------------------------
# Transformations
# ---------------------------------------------------------------------------

# Solo nos importa el Mundial masculino para el modelo principal.
MENS_TOURNAMENT_FILTER = "Men's"


def build_matches_historical(matches: pd.DataFrame, tournaments: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el DataFrame base de partidos históricos para entrenamiento.

    Reglas:
      - Solo Mundiales masculinos.
      - home_team_score / away_team_score = goles de regulación + tiempo extra
        (no incluyen penales en tanda).
      - Conservamos flags `extra_time` y `penalty_shootout` para uso futuro.
    """
    mens_ids = tournaments.loc[
        tournaments["tournament_name"].str.contains(MENS_TOURNAMENT_FILTER, na=False),
        "tournament_id",
    ]
    df = matches[matches["tournament_id"].isin(mens_ids)].copy()

    # Año del torneo (parseado del tournament_id "WC-YYYY")
    df["year"] = df["tournament_id"].str.extract(r"WC-(\d{4})").astype(int)

    # Tipo de etapa (group vs knockout) en una sola columna semántica.
    df["stage"] = df["stage_name"].str.lower().str.strip()

    # Resultado canónico 1X2 (independiente del shootout).
    def _result_1x2(row):
        if row["home_team_score"] > row["away_team_score"]:
            return "H"
        if row["home_team_score"] < row["away_team_score"]:
            return "A"
        return "D"

    df["result_1x2"] = df.apply(_result_1x2, axis=1)

    keep = [
        "year",
        "tournament_id",
        "match_id",
        "match_date",
        "stage",
        "group_name",
        "knockout_stage",
        "home_team_code",
        "home_team_name",
        "away_team_code",
        "away_team_name",
        "home_team_score",
        "away_team_score",
        "extra_time",
        "penalty_shootout",
        "home_team_score_penalties",
        "away_team_score_penalties",
        "result_1x2",
    ]
    df = df[keep].reset_index(drop=True)
    df["match_date"] = pd.to_datetime(df["match_date"])
    return df.sort_values(["year", "match_date", "match_id"]).reset_index(drop=True)


def build_2026_fixtures() -> pd.DataFrame:
    """Construye el DataFrame de fixtures del Mundial 2026 (target de predicción)."""
    matches = load_openfootball(2026)
    rows = []
    for m in matches:
        rows.append(
            {
                "match_date": m.get("date"),
                "match_time": m.get("time"),
                "round": m.get("round"),
                "group": m.get("group"),
                "team1_name": m.get("team1"),
                "team2_name": m.get("team2"),
                "ground": m.get("ground"),
            }
        )
    df = pd.DataFrame(rows)
    df["match_date"] = pd.to_datetime(df["match_date"], errors="coerce")
    return df.sort_values("match_date").reset_index(drop=True)


def build_openfootball_results(year: int) -> pd.DataFrame:
    """Lee resultados completos de openfootball para un mundial pasado (validación cruzada)."""
    matches = load_openfootball(year)
    rows = []
    for m in matches:
        score = (m.get("score") or {}).get("ft") or [None, None]
        rows.append(
            {
                "year": year,
                "date": m.get("date"),
                "team1": m.get("team1"),
                "team2": m.get("team2"),
                "score1": score[0],
                "score2": score[1],
                "group": m.get("group"),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Exploration / reporting
# ---------------------------------------------------------------------------

def summarize(historical: pd.DataFrame, fixtures_2026: pd.DataFrame) -> str:
    """Genera un resumen legible de la exploración."""
    lines = []
    add = lines.append

    add("=" * 70)
    add(" MUNDIAL 2026 PREDICTOR — Fase 1 / Exploración de datos base")
    add("=" * 70)
    add("")

    # --- Histórico ---
    add(f"[HISTÓRICO] partidos: {len(historical)}")
    add(f"[HISTÓRICO] mundiales: {historical['year'].nunique()} "
        f"(rango {historical['year'].min()}–{historical['year'].max()})")
    add(f"[HISTÓRICO] selecciones únicas: "
        f"{pd.concat([historical['home_team_code'], historical['away_team_code']]).nunique()}")
    add("")

    # Cobertura por torneo
    by_year = historical.groupby("year").size().rename("matches")
    add("Partidos por mundial:")
    for yr, n in by_year.items():
        add(f"  {yr}: {n} partidos")
    add("")

    # Nulls
    nulls = historical.isna().sum()
    nulls = nulls[nulls > 0]
    add(f"[HISTÓRICO] columnas con nulls: {len(nulls)}")
    if len(nulls):
        for col, n in nulls.items():
            add(f"  {col}: {n}")
    add("")

    # Estadísticas de resultados
    res = historical["result_1x2"].value_counts(normalize=True).sort_index()
    add("Distribución 1X2 (todo el histórico):")
    for k, v in res.items():
        label = {"H": "Home win", "D": "Draw", "A": "Away win"}[k]
        add(f"  {label}: {v:.1%}")
    add("")

    # Solo era moderna (>=1994, 32+ equipos)
    modern = historical[historical["year"] >= 1994]
    res_modern = modern["result_1x2"].value_counts(normalize=True).sort_index()
    add(f"Distribución 1X2 (era moderna 1994–2022, {len(modern)} partidos):")
    for k, v in res_modern.items():
        label = {"H": "Home win", "D": "Draw", "A": "Away win"}[k]
        add(f"  {label}: {v:.1%}")
    add("")

    # Goles promedio por partido
    avg_goals = (historical["home_team_score"] + historical["away_team_score"]).mean()
    avg_goals_modern = (modern["home_team_score"] + modern["away_team_score"]).mean()
    add(f"Goles promedio por partido (histórico): {avg_goals:.2f}")
    add(f"Goles promedio por partido (1994–2022): {avg_goals_modern:.2f}")
    add("")

    # Extra time y shootouts
    add(f"Partidos a tiempo extra: {historical['extra_time'].sum()} "
        f"({historical['extra_time'].mean():.1%})")
    add(f"Partidos a penales: {historical['penalty_shootout'].sum()} "
        f"({historical['penalty_shootout'].mean():.1%})")
    add("")

    # --- Fixtures 2026 ---
    add("=" * 70)
    add(f"[2026] fixtures cargados: {len(fixtures_2026)}")
    add(f"[2026] grupos: {fixtures_2026['group'].nunique()} grupos detectados")

    # openfootball usa placeholders para slots no asignados:
    #   "1A","2B" (1ro/2do de grupo), "3A/B/C/D/F" (3ros), "W73","L102" (ganador/perdedor de match).
    all_names = pd.concat([fixtures_2026["team1_name"], fixtures_2026["team2_name"]]).dropna()
    placeholder_regex = r"^(\d+[A-Z](/[A-Z])*|[WL]\d+)$"
    real_teams = all_names[~all_names.str.match(placeholder_regex)].unique()
    placeholders = all_names[all_names.str.match(placeholder_regex)].unique()
    add(f"[2026] selecciones confirmadas: {len(real_teams)} (esperado: 48)")
    add(f"[2026] placeholders de bracket sin resolver: {len(placeholders)}")
    add(f"[2026] rango de fechas: {fixtures_2026['match_date'].min().date()} → "
        f"{fixtures_2026['match_date'].max().date()}")
    add("")

    # Primer fixture como sanity check
    first = fixtures_2026.iloc[0]
    add(f"Primer partido programado: {first['match_date'].date()} — "
        f"{first['team1_name']} vs {first['team2_name']} ({first['group']}, {first['ground']})")
    add("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(">>> Cargando Fjelstul...")
    fjelstul = load_fjelstul_tables()
    print(f"    matches:     {len(fjelstul['matches'])} filas")
    print(f"    teams:       {len(fjelstul['teams'])} filas")
    print(f"    tournaments: {len(fjelstul['tournaments'])} filas")

    print(">>> Construyendo matches_historical (Mundial masculino solamente)...")
    historical = build_matches_historical(fjelstul["matches"], fjelstul["tournaments"])
    print(f"    {len(historical)} partidos consolidados")

    print(">>> Cargando fixtures 2026 (openfootball)...")
    fixtures_2026 = build_2026_fixtures()
    print(f"    {len(fixtures_2026)} fixtures cargados")

    print(">>> Cross-check: openfootball 2018 y 2022 (validación de consistencia futura)...")
    of_2018 = build_openfootball_results(2018)
    of_2022 = build_openfootball_results(2022)
    print(f"    openfootball 2018: {len(of_2018)} partidos")
    print(f"    openfootball 2022: {len(of_2022)} partidos")

    # --- Persistencia ---
    historical_path = PROCESSED / "matches_historical.csv"
    fixtures_path = PROCESSED / "matches_2026_fixtures.csv"
    summary_path = PROCESSED / "exploration_summary.txt"

    historical.to_csv(historical_path, index=False)
    fixtures_2026.to_csv(fixtures_path, index=False)
    of_2018.to_csv(PROCESSED / "openfootball_2018_results.csv", index=False)
    of_2022.to_csv(PROCESSED / "openfootball_2022_results.csv", index=False)

    summary = summarize(historical, fixtures_2026)
    summary_path.write_text(summary, encoding="utf-8")

    print()
    print(summary)
    print()
    print(f">>> Salidas escritas en {PROCESSED}/")
    print(f"    - {historical_path.name}")
    print(f"    - {fixtures_path.name}")
    print(f"    - openfootball_2018_results.csv")
    print(f"    - openfootball_2022_results.csv")
    print(f"    - {summary_path.name}")


if __name__ == "__main__":
    main()

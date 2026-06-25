"""
Tablas de grupos del Mundial 2026 con desempates FIFA.

Calcula las 12 tablas (A–L) a partir de los resultados jugados y los fixtures
oficiales, y deriva clasificados: ganadores (1X), segundos (2X) y el ranking de
los 12 terceros (para los 8 mejores → Round of 32).

Orden de desempate (reglamento FIFA, fase de grupos):
  1. Puntos
  2. Diferencia de goles (todos los partidos)
  3. Goles a favor (todos los partidos)
  Si persiste el empate, SOLO entre los equipos empatados:
  4. Puntos en los enfrentamientos directos
  5. Diferencia de goles en enfrentamientos directos
  6. Goles a favor en enfrentamientos directos
  7. Fair play
  8. Sorteo
Los criterios 7–8 no son replicables sin datos de tarjetas/azar; se usa un
fallback determinista por Elo descendente (documentado) para garantizar un orden
estable y reproducible.
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT         = Path(__file__).resolve().parents[2]
FIXTURES_CSV = ROOT / "data/processed/matches_2026_fixtures.csv"
MAPPING_CSV  = ROOT / "data/raw/reference/team_codes_mapping.csv"
ELO_CSV      = ROOT / "data/features/elo_ratings_rolling.csv"


@lru_cache(maxsize=None)
def load_groups(fixtures_csv: Path = FIXTURES_CSV,
                mapping_csv: Path = MAPPING_CSV) -> tuple[dict, dict]:
    """Devuelve (team_to_group, group_to_teams) usando ISO codes."""
    fix = pd.read_csv(fixtures_csv)
    ref = pd.read_csv(mapping_csv)
    n2i = dict(zip(ref["openfootball_name"], ref["iso_code"]))
    md  = fix[fix["round"].astype(str).str.startswith("Matchday")]

    team_to_group: dict = {}
    group_to_teams: dict = {}
    for _, r in md.iterrows():
        if pd.isna(r["group"]):
            continue
        grp = str(r["group"]).replace("Group ", "").strip()
        for name in (r["team1_name"], r["team2_name"]):
            iso = n2i.get(name)
            if iso is None:
                continue
            team_to_group[iso] = grp
            group_to_teams.setdefault(grp, set()).add(iso)
    return team_to_group, {g: sorted(t) for g, t in group_to_teams.items()}


def _elo_lookup(elo_csv: Path = ELO_CSV) -> dict:
    if not Path(elo_csv).exists():
        return {}
    e = pd.read_csv(elo_csv)
    return dict(zip(e["iso_code"], e["elo_rating"].astype(float)))


def _blank(team: str) -> dict:
    return {"team": team, "Pld": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0}


def _accumulate(stats: dict, matches: pd.DataFrame) -> None:
    """Suma estadísticas de `matches` (cols iso_a/iso_b/goals_a/goals_b) en stats."""
    for m in matches.itertuples(index=False):
        a, b, ga, gb = m.iso_a, m.iso_b, int(m.goals_a), int(m.goals_b)
        if a not in stats or b not in stats:
            continue
        stats[a]["Pld"] += 1; stats[b]["Pld"] += 1
        stats[a]["GF"] += ga; stats[a]["GA"] += gb
        stats[b]["GF"] += gb; stats[b]["GA"] += ga
        if ga > gb:
            stats[a]["W"] += 1; stats[a]["Pts"] += 3; stats[b]["L"] += 1
        elif ga < gb:
            stats[b]["W"] += 1; stats[b]["Pts"] += 3; stats[a]["L"] += 1
        else:
            stats[a]["D"] += 1; stats[b]["D"] += 1
            stats[a]["Pts"] += 1; stats[b]["Pts"] += 1
    for s in stats.values():
        s["GD"] = s["GF"] - s["GA"]


def _head_to_head_order(tied: list, matches: pd.DataFrame, elo: dict) -> list:
    """Ordena un grupo de equipos empatados en (Pts,GD,GF) globales por criterios
    de enfrentamiento directo (Pts→GD→GF entre ellos), luego Elo desc."""
    sub = matches[matches["iso_a"].isin(tied) & matches["iso_b"].isin(tied)]
    h2h = {t: _blank(t) for t in tied}
    _accumulate(h2h, sub)
    return sorted(
        tied,
        key=lambda t: (h2h[t]["Pts"], h2h[t]["GD"], h2h[t]["GF"], elo.get(t, 0.0)),
        reverse=True,
    )


def compute_group_table(teams: list, matches: pd.DataFrame, elo: dict) -> list:
    """Tabla ordenada de un grupo. `matches` = partidos jugados de ESE grupo.
    Devuelve lista de dicts con stats + 'rank' (1..4)."""
    stats = {t: _blank(t) for t in teams}
    _accumulate(stats, matches)

    # Orden primario por (Pts, GD, GF); desempate por H2H y Elo
    order = sorted(teams, key=lambda t: (stats[t]["Pts"], stats[t]["GD"],
                                         stats[t]["GF"]), reverse=True)
    # Resolver clusters empatados en (Pts,GD,GF)
    final, i = [], 0
    while i < len(order):
        j = i + 1
        key_i = (stats[order[i]]["Pts"], stats[order[i]]["GD"], stats[order[i]]["GF"])
        while j < len(order) and (stats[order[j]]["Pts"], stats[order[j]]["GD"],
                                  stats[order[j]]["GF"]) == key_i:
            j += 1
        cluster = order[i:j]
        final.extend(cluster if len(cluster) == 1
                     else _head_to_head_order(cluster, matches, elo))
        i = j

    return [{**stats[t], "rank": k + 1} for k, t in enumerate(final)]


def all_standings(results: pd.DataFrame,
                  fixtures_csv: Path = FIXTURES_CSV,
                  mapping_csv: Path = MAPPING_CSV,
                  elo_csv: Path = ELO_CSV) -> dict:
    """Calcula las tablas de los 12 grupos.

    results: DataFrame con cols iso_a, iso_b, goals_a, goals_b (partidos jugados;
    se filtran automáticamente a los intra-grupo). Devuelve {grupo: tabla}.
    """
    team_to_group, group_to_teams = load_groups(fixtures_csv, mapping_csv)
    elo = _elo_lookup(elo_csv)

    played = results.dropna(subset=["goals_a", "goals_b"]).copy()
    played["goals_a"] = played["goals_a"].astype(int)
    played["goals_b"] = played["goals_b"].astype(int)
    # solo partidos donde ambos equipos comparten grupo (group stage)
    played = played[played.apply(
        lambda r: team_to_group.get(r["iso_a"]) is not None
        and team_to_group.get(r["iso_a"]) == team_to_group.get(r["iso_b"]), axis=1)]

    tables = {}
    for grp in sorted(group_to_teams):
        gm = played[played["iso_a"].map(team_to_group) == grp]
        tables[grp] = compute_group_table(group_to_teams[grp], gm, elo)
    return tables


def group_qualifiers(tables: dict) -> dict:
    """Devuelve {'1A': iso, '2A': iso, '3A': iso, ...} para grupos con tabla."""
    out = {}
    for grp, table in tables.items():
        for row in table:
            out[f"{row['rank']}{grp}"] = row["team"]
    return out


def rank_thirds(tables: dict, elo_csv: Path = ELO_CSV) -> list:
    """Ranking de los terceros de cada grupo (mejor primero) por Pts→GD→GF→Elo.
    Devuelve lista de dicts con 'group', 'team' y stats. Los 8 primeros clasifican."""
    elo = _elo_lookup(elo_csv)
    thirds = []
    for grp, table in tables.items():
        for row in table:
            if row["rank"] == 3:
                thirds.append({**row, "group": grp})
    thirds.sort(key=lambda r: (r["Pts"], r["GD"], r["GF"], elo.get(r["team"], 0.0)),
                reverse=True)
    return thirds

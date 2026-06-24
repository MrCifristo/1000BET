"""
Cuadro de eliminatorias del Mundial 2026 — resolución en cascada.

El archivo de fixtures ya codifica la estructura oficial del bracket con
placeholders:
  - "1A"/"2B"  → ganador / segundo de un grupo.
  - "3A/B/C/D/F" → tercero de uno de esos grupos (slot con restricción de grupos).
  - "W73"/"L101" → ganador / perdedor del partido nº 73 / 101.

Numeración de partidos (estándar FIFA): grupos 1–72, Round of 32 = 73–88,
Round of 16 = 89–96, Cuartos = 97–100, Semis = 101–102, 3er puesto = 103,
Final = 104.

`resolve_bracket(results)` resuelve tantos slots como permitan los resultados
jugados hasta ahora (grupos completos → 1X/2X/3X; partidos KO jugados → W##/L##),
en cascada. Devuelve los 32 partidos KO con equipos resueltos o el placeholder
original si aún no se puede.

⚠️ Asignación de terceros: FIFA usa una tabla oficial de 495 combinaciones (en el
reglamento, no disponible en forma estructurada). Aquí se usa un emparejamiento
por restricciones determinista (respeta los grupos permitidos de cada slot). Es
correcto cuando la asignación válida es única; en combinaciones ambiguas puede
diferir de la tabla oficial. Sustituible en `assign_thirds()` antes del 28-jun.
"""
import re
from pathlib import Path

import pandas as pd

from src.tournament.standings import (
    FIXTURES_CSV, MAPPING_CSV, load_groups, all_standings,
    group_qualifiers, rank_thirds,
)

# Numeración de la primera ronda KO por ronda (en orden de aparición en fixtures).
KO_ROUNDS = ["Round of 32", "Round of 16", "Quarter-final",
             "Semi-final", "Match for third place", "Final"]


def parse_knockout(fixtures_csv: Path = FIXTURES_CSV) -> pd.DataFrame:
    """Filas KO con número de partido asignado y los placeholders de cada lado."""
    fix = pd.read_csv(fixtures_csv)
    ko = fix[fix["round"].isin(KO_ROUNDS)].copy()
    # Orden por ronda (según KO_ROUNDS) y luego por aparición → numeración 73+
    ko["round_ord"] = ko["round"].map({r: i for i, r in enumerate(KO_ROUNDS)})
    ko = ko.sort_values(["round_ord"], kind="stable").reset_index(drop=True)
    ko["match_no"] = range(73, 73 + len(ko))
    return ko[["match_no", "round", "match_date", "ground",
               "team1_name", "team2_name"]].rename(
        columns={"team1_name": "slot_a", "team2_name": "slot_b"})


def third_slots(ko: pd.DataFrame) -> dict:
    """{match_no: (host_slot, allowed_groups)} para los slots de tercero (3X/Y/..)."""
    out = {}
    for r in ko.itertuples(index=False):
        for host, other in ((r.slot_a, r.slot_b), (r.slot_b, r.slot_a)):
            m = re.fullmatch(r"3([A-L/]+)", str(other))
            if m:
                groups = m.group(1).split("/")
                out[r.match_no] = (host, groups)
    return out


def _backtrack_match(slots: list, allowed: dict, groups: set,
                     assign: dict) -> bool:
    """Empareja slots→grupos (perfect matching) de forma determinista (slot más
    restringido primero; grupo en orden alfabético)."""
    if not slots:
        return True
    slots = sorted(slots, key=lambda s: len(allowed[s] & groups))
    s = slots[0]
    for g in sorted(allowed[s] & groups):
        assign[s] = g
        if _backtrack_match(slots[1:], allowed, groups - {g}, assign):
            return True
        del assign[s]
    return False


def assign_thirds(ko: pd.DataFrame, tables: dict) -> dict:
    """Asigna los 8 mejores terceros a sus slots. Devuelve {match_no: iso_tercero}.
    Vacío si aún no están los 12 grupos completos.

    ⚠️ Interim por restricciones — ver nota de módulo. Sustituir por tabla FIFA."""
    team_to_group, group_to_teams = load_groups()
    # ¿Los 12 grupos completos? (cada equipo jugó sus 3 partidos)
    complete = all(all(row["Pld"] == 3 for row in tables.get(g, []))
                   and len(tables.get(g, [])) == 4 for g in group_to_teams)
    if not complete:
        return {}

    thirds = rank_thirds(tables)[:8]              # 8 mejores terceros
    qual_groups = {t["group"] for t in thirds}
    third_by_group = {t["group"]: t["team"] for t in thirds}

    ts = third_slots(ko)
    allowed = {mn: set(groups) for mn, (_host, groups) in ts.items()}
    assign: dict = {}
    if not _backtrack_match(list(allowed), allowed, set(qual_groups), assign):
        raise ValueError(f"Sin emparejamiento válido para terceros {qual_groups}")
    return {mn: third_by_group[g] for mn, g in assign.items()}


def _played_lookup(results: pd.DataFrame) -> dict:
    """{(frozenset{isoA,isoB}): (winner, loser, goals)} de partidos jugados.
    Devuelve winner=None en empate (los KO no deberían empatar tras definición)."""
    out = {}
    played = results.dropna(subset=["goals_a", "goals_b"])
    for r in played.itertuples(index=False):
        a, b, ga, gb = r.iso_a, r.iso_b, int(r.goals_a), int(r.goals_b)
        key = frozenset((a, b))
        if ga > gb:
            out[key] = (a, b)
        elif gb > ga:
            out[key] = (b, a)
        else:
            out[key] = (None, None)  # empate sin desempate registrado
    return out


def resolve_bracket(results: pd.DataFrame,
                    fixtures_csv: Path = FIXTURES_CSV) -> pd.DataFrame:
    """Resuelve el cuadro KO tanto como permitan los resultados actuales.

    results: DataFrame con iso_a, iso_b, goals_a, goals_b (grupos + KO jugados).
    Devuelve `parse_knockout` con columnas extra team_a/team_b (iso resuelto o
    None si aún placeholder) y winner (iso) si el partido ya se jugó.
    """
    ko     = parse_knockout(fixtures_csv)
    tables = all_standings(results, fixtures_csv)
    quals  = group_qualifiers_completed(tables)        # 1X/2X/3X solo si grupo completo
    thirds = assign_thirds(ko, tables)                 # {match_no: iso}
    played = _played_lookup(results)

    resolved: dict = {}  # match_no → (team_a, team_b)

    def resolve_slot(slot, match_no=None):
        s = str(slot)
        if re.fullmatch(r"[12][A-L]", s):
            return quals.get(s)
        if re.fullmatch(r"3[A-L/]+", s):              # slot de tercero
            return thirds.get(match_no)
        m = re.fullmatch(r"([WL])(\d+)", s)
        if m:
            kind, num = m.group(1), int(m.group(2))
            if num not in resolved:
                return None
            ta, tb = resolved[num]
            if ta is None or tb is None:
                return None
            res = played.get(frozenset((ta, tb)))
            if res is None or res[0] is None:
                return None
            return res[0] if kind == "W" else res[1]
        return None

    rows = []
    # Iterar por número de partido asegura que los W/L de rondas previas ya estén
    for r in ko.itertuples(index=False):
        ta = resolve_slot(r.slot_a, r.match_no)
        tb = resolve_slot(r.slot_b, r.match_no)
        resolved[r.match_no] = (ta, tb)
        winner = None
        if ta and tb:
            res = played.get(frozenset((ta, tb)))
            if res and res[0] is not None:
                winner = res[0]
        rows.append({"match_no": r.match_no, "round": r.round,
                     "match_date": r.match_date, "ground": r.ground,
                     "slot_a": r.slot_a, "slot_b": r.slot_b,
                     "team_a": ta, "team_b": tb, "winner": winner})
    return pd.DataFrame(rows)


def group_qualifiers_completed(tables: dict) -> dict:
    """Como group_qualifiers pero solo para grupos COMPLETOS (cada equipo Pld==3)."""
    out = {}
    for grp, table in tables.items():
        if len(table) == 4 and all(row["Pld"] == 3 for row in table):
            for row in table:
                out[f"{row['rank']}{grp}"] = row["team"]
    return out

"""Tests de resolución del cuadro KO."""
import pandas as pd

from src.tournament.standings import load_groups
from src.tournament.bracket import (
    parse_knockout, third_slots, resolve_bracket,
)


def test_parse_knockout_numeracion():
    ko = parse_knockout()
    assert len(ko) == 32
    assert ko["match_no"].tolist() == list(range(73, 105))
    r32 = ko[ko["round"] == "Round of 32"]
    assert r32["match_no"].min() == 73 and r32["match_no"].max() == 88
    assert ko[ko["round"] == "Final"]["match_no"].iloc[0] == 104


def test_third_slots_son_ocho():
    ts = third_slots(parse_knockout())
    assert len(ts) == 8
    for _host, groups in ts.values():
        assert all(g in "ABCDEFGHIJKL" for g in groups)


def test_resolve_sin_grupos_completos_no_crashea():
    # Solo unos pocos resultados → ningún grupo completo → KO todo placeholder
    res = pd.read_csv("data/processed/wc2026_actual_results.csv")
    br = resolve_bracket(res)
    assert len(br) == 32
    assert br["team_a"].isna().all() and br["team_b"].isna().all()


def _full_group_results() -> pd.DataFrame:
    """Genera los 72 partidos de grupos con un orden claro 1>2>3>4 por grupo
    (el i-ésimo equipo vence a todos los de índice mayor, 1-0)."""
    _, group_to_teams = load_groups()
    rows = []
    for teams in group_to_teams.values():
        ts = sorted(teams)
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                rows.append((ts[i], ts[j], 1, 0))  # mejor índice gana
    return pd.DataFrame(rows, columns=["iso_a", "iso_b", "goals_a", "goals_b"])


def test_grupos_completos_resuelven_r32():
    res = _full_group_results()
    br = resolve_bracket(res)
    r32 = br[br["round"] == "Round of 32"]
    # Todos los 32 lados resueltos (1X/2X y los 8 terceros asignados)
    assert r32["team_a"].notna().all() and r32["team_b"].notna().all()
    # 32 equipos distintos en R32
    teams = pd.concat([r32["team_a"], r32["team_b"]])
    assert teams.nunique() == 32


def test_cascada_ko_winner():
    res = _full_group_results()
    br = resolve_bracket(res)
    # Tomar el partido 73 ya resuelto y simular un resultado
    m73 = br[br["match_no"] == 73].iloc[0]
    ta, tb = m73["team_a"], m73["team_b"]
    extra = pd.DataFrame([(ta, tb, 2, 0)], columns=["iso_a", "iso_b", "goals_a", "goals_b"])
    res2 = pd.concat([res, extra], ignore_index=True)
    br2 = resolve_bracket(res2)
    # match 73 ahora tiene ganador = ta
    assert br2[br2["match_no"] == 73].iloc[0]["winner"] == ta
    # El partido de R16 que consume W73 ahora tiene a ta colocado
    r16 = br2[br2["round"] == "Round of 16"]
    consumer = r16[(r16["slot_a"] == "W73") | (r16["slot_b"] == "W73")].iloc[0]
    side = "team_a" if consumer["slot_a"] == "W73" else "team_b"
    assert consumer[side] == ta

"""Tests de desempates FIFA en standings.compute_group_table / rank_thirds."""
from pathlib import Path

import pandas as pd

from src.tournament.standings import compute_group_table, rank_thirds

NO_ELO = {}  # elo neutro: no debe influir salvo como último recurso


def _matches(rows):
    return pd.DataFrame(rows, columns=["iso_a", "iso_b", "goals_a", "goals_b"])


def test_orden_por_puntos():
    m = _matches([("A", "B", 3, 0), ("A", "C", 2, 0), ("B", "C", 1, 0)])
    table = compute_group_table(["A", "B", "C"], m, NO_ELO)
    assert [r["team"] for r in table] == ["A", "B", "C"]
    assert table[0]["Pts"] == 6 and table[0]["rank"] == 1


def test_dg_global_antes_que_h2h():
    # B venció a A en head-to-head, pero A tiene mejor DG global → A va primero.
    # C arriba de B por GF global (ambos -2). Verifica criterios 2 y 3 sobre el 4.
    m = _matches([("A", "C", 5, 0), ("B", "A", 1, 0), ("C", "B", 3, 0)])
    table = compute_group_table(["A", "B", "C"], m, NO_ELO)
    assert [r["team"] for r in table] == ["A", "C", "B"]


def test_h2h_desempata_igualdad_global():
    # A y B quedan iguales en Pts/DG/GF globales (4, 0, 1); A venció a B → A arriba.
    # D gana el grupo, C último.
    m = _matches([
        ("A", "B", 1, 0), ("A", "C", 0, 0), ("A", "D", 0, 1),
        ("B", "C", 1, 0), ("B", "D", 0, 0), ("C", "D", 0, 0),
    ])
    table = compute_group_table(["A", "B", "C", "D"], m, NO_ELO)
    # A y B iguales en lo global
    sa = next(r for r in table if r["team"] == "A")
    sb = next(r for r in table if r["team"] == "B")
    assert (sa["Pts"], sa["GD"], sa["GF"]) == (sb["Pts"], sb["GD"], sb["GF"]) == (4, 0, 1)
    assert [r["team"] for r in table] == ["D", "A", "B", "C"]


def test_elo_como_ultimo_recurso():
    # Ciclo perfecto: A,B,C iguales en todo (global y h2h). Elo decide.
    m = _matches([("A", "B", 1, 0), ("B", "C", 1, 0), ("C", "A", 1, 0)])
    table = compute_group_table(["A", "B", "C"], m, {"B": 2000, "A": 1000, "C": 500})
    assert [r["team"] for r in table] == ["B", "A", "C"]


def test_rank_thirds_ordena_por_pts_dg_gf():
    tables = {
        "A": [{"team": "W", "rank": 1, "Pts": 9, "GD": 5, "GF": 7},
              {"team": "X", "rank": 3, "Pts": 4, "GD": 1, "GF": 3}],
        "B": [{"team": "Y", "rank": 3, "Pts": 4, "GD": 2, "GF": 2}],
        "C": [{"team": "Z", "rank": 3, "Pts": 3, "GD": 0, "GF": 5}],
    }
    thirds = rank_thirds(tables, elo_csv=Path("/nonexistent"))
    # Y (4,+2) > X (4,+1) > Z (3,...)
    assert [t["team"] for t in thirds] == ["Y", "X", "Z"]

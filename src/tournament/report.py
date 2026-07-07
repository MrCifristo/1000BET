"""
Calcula y persiste el estado del torneo (tablas de grupos + cuadro KO) a partir
de los resultados jugados, y lo imprime de forma legible.

Lee  data/processed/wc2026_actual_results.csv
Escribe data/processed/wc2026_standings.csv  (12 grupos, ordenado, con rank)
        data/processed/wc2026_bracket.csv     (32 partidos KO resueltos)

Uso: python -m src.tournament.report
"""
from pathlib import Path

import pandas as pd

from src.tournament.standings import all_standings, rank_thirds
from src.tournament.bracket import bracket_view

ROOT          = Path(__file__).resolve().parents[2]
RESULTS_CSV   = ROOT / "data/processed/wc2026_actual_results.csv"
STANDINGS_CSV = ROOT / "data/processed/wc2026_standings.csv"
BRACKET_CSV   = ROOT / "data/processed/wc2026_bracket.csv"


def build_and_save(results_csv: Path = RESULTS_CSV) -> tuple[dict, pd.DataFrame]:
    results = pd.read_csv(results_csv)
    tables  = all_standings(results)
    bracket = bracket_view(results)          # cuadro real, desde partidos jugados

    # Persistir standings (long format con grupo + rank)
    rows = []
    for grp in sorted(tables):
        for row in tables[grp]:
            rows.append({"group": grp, **row})
    pd.DataFrame(rows).to_csv(STANDINGS_CSV, index=False)
    bracket.to_csv(BRACKET_CSV, index=False)
    return tables, bracket


def main():
    tables, bracket = build_and_save()

    print("=" * 60)
    print("TABLAS DE GRUPOS — Mundial 2026")
    print("=" * 60)
    for grp in sorted(tables):
        print(f"\nGrupo {grp}")
        print(f"  {'Equipo':<6}{'PJ':>3}{'G':>3}{'E':>3}{'P':>3}"
              f"{'GF':>4}{'GC':>4}{'DG':>4}{'Pts':>5}")
        for row in tables[grp]:
            mark = "✓" if row["rank"] <= 2 else ("·" if row["rank"] == 3 else " ")
            print(f"{mark} {row['team']:<6}{row['Pld']:>3}{row['W']:>3}{row['D']:>3}"
                  f"{row['L']:>3}{row['GF']:>4}{row['GA']:>4}{row['GD']:>4}{row['Pts']:>5}")

    # Ranking de terceros (los 8 mejores clasifican)
    thirds = rank_thirds(tables)
    if any(t["Pld"] > 0 for t in thirds):
        print("\n" + "=" * 60)
        print("RANKING DE TERCEROS (8 mejores → Round of 32)")
        print("=" * 60)
        for i, t in enumerate(thirds, 1):
            q = "✓" if i <= 8 else "✗"
            print(f"{q} {i:>2}. {t['team']} (Grupo {t['group']}) "
                  f"Pts {t['Pts']} DG {t['GD']:+d} GF {t['GF']}")

    print("\n" + "=" * 60)
    print("CUADRO DE ELIMINATORIAS (rondas jugadas)")
    print("=" * 60)
    ko_order = ["Round of 32", "Round of 16", "Quarter-final",
                "Semi-final", "Match for third place", "Final"]
    for rnd in ko_order:
        rows = bracket[bracket["round"] == rnd]
        if rows.empty:
            continue
        print(f"\n{rnd}")
        for r in rows.itertuples(index=False):
            a = r.team_a if r.team_a else r.slot_a
            b = r.team_b if r.team_b else r.slot_b
            w = f"  → {r.winner}" if r.winner else "  (pendiente)"
            print(f"  {r.match_date}  {a:<5} vs {b:<5}{w}")

    print(f"\nGuardado → {STANDINGS_CSV.relative_to(ROOT)} | "
          f"{BRACKET_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

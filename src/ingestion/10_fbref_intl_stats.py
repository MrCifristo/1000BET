"""
Fase 3 — Script 10: FBref International Stats

Procesa los CSVs exportados manualmente desde FBref (Standard Stats de selección nacional)
para 15 selecciones con baja cobertura en Understat/Big 5.

Input:  FbrefData/{CODE}-Tabla 1.csv  (exportados manualmente por el usuario)
Output: data/features/fbref_intl_stats.csv

Columnas generadas por selección:
  fb_npgls_per90, fb_gls_per90, fb_ast_per90,
  fb_intl_mins_avg, fb_intl_coverage_pct, fb_squad_matched
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FBREF_DIR = ROOT / "FbrefData"
SQUADS_CSV = ROOT / "data/processed/wc2026_squads.csv"
OUT_CSV = ROOT / "data/features/fbref_intl_stats.csv"

MIN_INTL_90S = 0.5  # mínimo 45 minutos acumulados para contar al jugador

FILE_TO_ISO = {
    "AUS": "AUS", "CUW": "CUW", "HAI": "HTI", "IRQ": "IRQ",
    "JOR": "JOR", "JPN": "JPN", "MAR": "MAR", "MEX": "MEX",
    "PAN": "PAN", "QAT": "QAT", "SAU": "SAU", "SKOREA": "KOR",
    "TUN": "TUN", "USA": "USA", "UZB": "UZB",
}


def normalize_name(s: str) -> str:
    s = str(s)
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = re.sub(r"\s*\[.*?\]", "", s)
    s = re.sub(r"\s*\*+$", "", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def parse_fbref_csv(path: Path) -> pd.DataFrame:
    """
    FBref exporta 2 filas de encabezado: row 0 = categorías (Playing Time / Performance / Per 90),
    row 1 = nombres de columna con duplicados (Gls, Ast… aparecen dos veces).
    pandas resuelve duplicados con sufijo .1 en la segunda aparición.
    """
    df = pd.read_csv(path, skiprows=1, header=0)

    # Descartar filas de totales / encabezados repetidos que FBref inserta
    df = df[df["Player"].notna() & (df["Player"] != "Player")].copy()

    df["90s"] = pd.to_numeric(df["90s"], errors="coerce").fillna(0)

    # Columnas de totales (primera aparición): Gls, Ast, G-PK
    gls = pd.to_numeric(df.get("Gls", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
    ast = pd.to_numeric(df.get("Ast", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
    # G-PK puede no existir en todos los exports; si falta, usar Gls
    npgls = pd.to_numeric(df.get("G-PK", gls), errors="coerce").fillna(0)

    result = pd.DataFrame({
        "player_norm": df["Player"].apply(normalize_name),
        "intl_90s":    df["90s"],
        "intl_gls":    gls,
        "intl_ast":    ast,
        "intl_npgls":  npgls,
    })
    return result[result["intl_90s"] >= MIN_INTL_90S].reset_index(drop=True)


def aggregate_squad(squads: pd.DataFrame, fbref: pd.DataFrame, iso: str) -> dict:
    squad_norms = set(squads[squads["iso_code"] == iso]["player_norm"])
    squad_size  = len(squad_norms)
    in_squad    = fbref[fbref["player_norm"].isin(squad_norms)].copy()
    n_matched   = len(in_squad)
    total_90s   = in_squad["intl_90s"].sum()

    if n_matched == 0 or total_90s == 0:
        return {
            "iso_code": iso,
            "fb_npgls_per90":       None,
            "fb_gls_per90":         None,
            "fb_ast_per90":         None,
            "fb_intl_mins_avg":     None,
            "fb_intl_coverage_pct": 0.0,
            "fb_squad_matched":     0,
        }

    return {
        "iso_code": iso,
        "fb_npgls_per90":       round(in_squad["intl_npgls"].sum() / total_90s, 3),
        "fb_gls_per90":         round(in_squad["intl_gls"].sum()   / total_90s, 3),
        "fb_ast_per90":         round(in_squad["intl_ast"].sum()   / total_90s, 3),
        "fb_intl_mins_avg":     round((total_90s * 90) / n_matched, 1),
        "fb_intl_coverage_pct": round(100 * n_matched / squad_size, 1) if squad_size > 0 else 0.0,
        "fb_squad_matched":     n_matched,
    }


def main():
    print("=== 10_fbref_intl_stats.py ===")

    squads = pd.read_csv(SQUADS_CSV)
    print(f"  Squad list: {len(squads)} jugadores / {squads['iso_code'].nunique()} selecciones")

    records = []
    for code, iso in FILE_TO_ISO.items():
        path = FBREF_DIR / f"{code}-Tabla 1.csv"
        if not path.exists():
            print(f"  WARNING: {path.name} no encontrado — omitiendo {iso}")
            continue

        fbref  = parse_fbref_csv(path)
        record = aggregate_squad(squads, fbref, iso)
        records.append(record)
        print(
            f"  {iso:3s}: {record['fb_squad_matched']:2d} jugadores squad | "
            f"coverage={record['fb_intl_coverage_pct']:5.1f}% | "
            f"npgls/90={record['fb_npgls_per90']}"
        )

    result = pd.DataFrame(records).sort_values("iso_code").reset_index(drop=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_CSV, index=False)

    print(f"\nGuardado → {OUT_CSV.relative_to(ROOT)}")
    print(f"  Selecciones procesadas: {len(result)}")
    print(f"  Con coverage > 0: {(result['fb_intl_coverage_pct'] > 0).sum()}")
    print(f"\n{result[['iso_code','fb_npgls_per90','fb_gls_per90','fb_ast_per90','fb_intl_coverage_pct']].to_string(index=False)}")


if __name__ == "__main__":
    main()

"""
Fase 4-datos — Ingestión de partidos internacionales (martj42/international_results).

Reemplaza el corpus de solo-mundiales (484 partidos efectivos) por TODOS los
partidos internacionales de la era moderna (2002+): amistosos, eliminatorias,
Nations League, copas continentales y mundiales.

Salida: data/processed/matches_intl_v3.csv con el mismo esquema que consume
build_match_rows():
  home_team_iso, away_team_iso, home_team_score, away_team_score,
  year, neutral_venue, host_team_iso, tournament, date

Mapeo nombre→ISO: country_converter (coco) para el grueso + overrides para los
códigos propios del proyecto (selecciones británicas separadas, etc.).
Los nombres no mapeables (selecciones no-FIFA, regiones) se descartan.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import country_converter as coco

ROOT    = Path(__file__).resolve().parents[2]
RAW     = ROOT / "data/raw/martj42/results.csv"
OUT     = ROOT / "data/processed/matches_intl_v3.csv"
TEAMS   = ROOT / "data/features/teams_features_v2.csv"
YEAR_MIN = 2002

# Overrides: coco colapsa las selecciones británicas a GBR — el proyecto las
# trata como ISO separadas (FIFA-style). También fija casos ambiguos.
OVERRIDES = {
    "England": "ENG", "Scotland": "SCO", "Wales": "WAL",
    "Northern Ireland": "NIR",
    "United States": "USA", "South Korea": "KOR", "North Korea": "PRK",
    "Czechia": "CZE", "Czech Republic": "CZE",
    "Cape Verde": "CPV", "Curaçao": "CUW", "Curacao": "CUW",
    "DR Congo": "COD", "Congo": "COG",
    "Ivory Coast": "CIV", "Türkiye": "TUR", "Turkey": "TUR",
    "Kosovo": "XKX",
}

# coco mapea por substring algunos equipos NO-FIFA (CONIFA) a una selección FIFA
# real, contaminándola. Forzamos su descarte.
DISCARD = {
    "Western Armenia", "Northern Cyprus", "Iraqi Kurdistan",
    "United Koreans in Japan", "Somaliland", "Parishes of Jersey",
}

SENTINEL = "__NF__"


def build_name_to_iso(names: list[str]) -> dict[str, str]:
    """Mapea cada nombre de equipo a ISO3 (o None si no es selección FIFA)."""
    cc = coco.CountryConverter()
    mapping = {}
    to_convert = [n for n in names if n not in OVERRIDES and n not in DISCARD]
    # not_found=SENTINEL: coco con None *mantiene el input*, así que usamos un
    # centinela explícito para detectar los no mapeados y descartarlos.
    converted = cc.convert(to_convert, to="ISO3", not_found=SENTINEL)
    if isinstance(converted, str):
        converted = [converted]
    for name, iso in zip(to_convert, converted):
        mapping[name] = None if iso == SENTINEL else iso
    for name in DISCARD:
        mapping[name] = None
    mapping.update(OVERRIDES)
    return mapping


def main():
    logging.getLogger("country_converter").setLevel(logging.ERROR)

    df = pd.read_csv(RAW)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    # Filtrar: era moderna + partidos efectivamente jugados
    df = df[(df["year"] >= YEAR_MIN)
            & df["home_score"].notna()
            & df["away_score"].notna()].copy()
    print(f"Partidos {YEAR_MIN}+ jugados: {len(df)}")

    # Mapeo nombre → ISO
    names = sorted(set(df["home_team"]) | set(df["away_team"]))
    name2iso = build_name_to_iso(names)
    unmapped = sorted(n for n, iso in name2iso.items() if iso is None)
    print(f"Nombres únicos: {len(names)} | no mapeados (descartados): {len(unmapped)}")
    if unmapped:
        print("  Ejemplos no mapeados:", unmapped[:20])

    df["home_team_iso"] = df["home_team"].map(name2iso)
    df["away_team_iso"] = df["away_team"].map(name2iso)
    before = len(df)
    df = df[df["home_team_iso"].notna() & df["away_team_iso"].notna()].copy()
    print(f"Partidos con ambos equipos mapeados: {len(df)} (descartados {before-len(df)})")

    # Esquema compatible con build_match_rows
    df["home_team_score"] = df["home_score"].astype(int)
    df["away_team_score"] = df["away_score"].astype(int)
    df["neutral_venue"]   = df["neutral"].astype(str).str.upper().eq("TRUE")
    # host = local del partido (ventaja de jugar en casa); NaN si cancha neutral
    df["host_team_iso"]   = np.where(df["neutral_venue"], np.nan, df["home_team_iso"])

    out = df[[
        "date", "year", "tournament",
        "home_team_iso", "away_team_iso",
        "home_team_score", "away_team_score",
        "neutral_venue", "host_team_iso",
    ]].sort_values("date").reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"\nGuardado → {OUT.relative_to(ROOT)}  ({len(out)} partidos)")

    # Cobertura de los 48 del Mundial 2026
    teams48 = set(pd.read_csv(TEAMS)["iso_code"])
    appearances = pd.concat([out["home_team_iso"], out["away_team_iso"]])
    counts = appearances.value_counts()
    cov = {t: int(counts.get(t, 0)) for t in sorted(teams48)}
    missing = [t for t, c in cov.items() if c == 0]
    print(f"\nCobertura de los 48 de 2026:")
    print(f"  con partidos: {48 - len(missing)}/48 | sin partidos: {missing}")
    print(f"  mín partidos: {min(cov.values())} | mediana: "
          f"{int(np.median(list(cov.values())))} | máx: {max(cov.values())}")
    debutantes = ["UZB", "JOR", "CPV", "CUW"]
    print("  Debutantes 2026:", {t: cov[t] for t in debutantes if t in cov})


if __name__ == "__main__":
    main()

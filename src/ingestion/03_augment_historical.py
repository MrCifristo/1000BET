"""
03_augment_historical.py

Aplica las decisiones de Fase 1 al DataFrame histórico:
  - Aplica aliases (Czechoslovakia -> Czech Republic, East Germany -> Germany)
  - Marca neutral_venue (el partido NO se jugó en país del local NI del visitante)
  - Identifica host_team_iso (selección que es anfitriona si una de las dos lo es)
  - Calcula time_weight = exp(-decay * (REF_YEAR - year))
  - Verifica consistencia: 100% de partidos con country_name mapeable a un ISO

Inputs:
  data/processed/matches_historical.csv
  data/raw/fjelstul/teams.csv
  data/raw/reference/historical_team_aliases.csv

Output:
  data/processed/matches_historical_v2.csv
  data/processed/team_name_mapping.csv  (alias openfootball-name <-> ISO)
  data/processed/augmentation_summary.txt
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
REFERENCE = PROJECT_ROOT / "data" / "raw" / "reference"
FJELSTUL = PROJECT_ROOT / "data" / "raw" / "fjelstul"

# Hiperparámetros para el time-decay weighting (parametrizable en Phase 4)
REFERENCE_YEAR = 2022       # último Mundial conocido — peso máximo
DECAY_RATE = 0.05           # por año. exp(-0.05 * 28) ~ 0.247 para 1994
                            # exp(-0.05 * 52) ~ 0.074 para 1970


def load_aliases() -> dict[str, str]:
    df = pd.read_csv(REFERENCE / "historical_team_aliases.csv")
    return dict(zip(df["historical_iso"], df["modern_iso"]))


def load_country_name_to_iso() -> dict[str, str]:
    """Construye mapeo nombre-de-país -> ISO usando Fjelstul teams.csv (autoritativo)."""
    teams = pd.read_csv(FJELSTUL / "teams.csv")
    # En matches: country_name == team_name del país anfitrión. United States, Mexico, etc.
    mapping = dict(zip(teams["team_name"], teams["team_code"]))
    # Casos especiales que aparecen en Fjelstul matches con valor compuesto:
    mapping["Korea, Japan"] = "KOR"   # WC 2002 fue co-anfitrionado; los matches individuales
                                       # usan país específico. Este es solo fallback defensivo.
    return mapping


def augment(historical: pd.DataFrame, aliases: dict[str, str],
            country_to_iso: dict[str, str], match_country_lookup: dict[str, str]) -> pd.DataFrame:
    df = historical.copy()

    # Renombramos los códigos crudos para evitar confusión más adelante
    df = df.rename(columns={
        "home_team_code": "home_team_iso_raw",
        "away_team_code": "away_team_iso_raw",
    })

    # Códigos canónicos (con alias aplicado)
    df["home_team_iso"] = df["home_team_iso_raw"].map(lambda c: aliases.get(c, c))
    df["away_team_iso"] = df["away_team_iso_raw"].map(lambda c: aliases.get(c, c))

    # ISO del país anfitrión de cada partido (Fjelstul ya da country_name correcto por partido)
    df["host_country_iso"] = df["match_country_name"].map(match_country_lookup)
    missing = df[df["host_country_iso"].isna()]["match_country_name"].unique()
    if len(missing):
        raise ValueError(
            f"No se pudo mapear país anfitrión a ISO para: {list(missing)}. "
            f"Revisar Fjelstul teams.csv."
        )

    # neutral_venue: el venue no corresponde a ninguno de los dos equipos
    df["neutral_venue"] = (df["host_country_iso"] != df["home_team_iso"]) & \
                          (df["host_country_iso"] != df["away_team_iso"])

    # host_team_iso: cuál equipo del partido es el anfitrión (NaN si neutral)
    def _host_team(row):
        if row["host_country_iso"] == row["home_team_iso"]:
            return row["home_team_iso"]
        if row["host_country_iso"] == row["away_team_iso"]:
            return row["away_team_iso"]
        return pd.NA
    df["host_team_iso"] = df.apply(_host_team, axis=1)

    # time_weight (decay exponencial desde REFERENCE_YEAR)
    df["time_weight"] = df["year"].map(
        lambda y: math.exp(-DECAY_RATE * (REFERENCE_YEAR - y))
    )

    return df


def build_team_name_mapping() -> pd.DataFrame:
    """Une el roster de 2026 (openfootball) con códigos ISO para uso downstream."""
    return pd.read_csv(REFERENCE / "team_codes_mapping.csv")[
        ["openfootball_name", "iso_code", "country_full"]
    ]


def main() -> None:
    print(">>> Cargando matches_historical.csv...")
    # Renombrar country_name -> match_country_name para evitar colisión con
    # potencial team country_name posterior.
    historical = pd.read_csv(
        PROCESSED / "matches_historical.csv",
    )
    # El esquema actual no tiene country_name (lo dejamos fuera en Phase 1).
    # Re-leemos directo de Fjelstul matches para extraerlo.
    fjelstul_matches = pd.read_csv(FJELSTUL / "matches.csv")[
        ["match_id", "country_name"]
    ].rename(columns={"country_name": "match_country_name"})
    historical = historical.merge(fjelstul_matches, on="match_id", how="left")

    aliases = load_aliases()
    name_to_iso = load_country_name_to_iso()
    print(f"    aliases cargados: {len(aliases)}")
    print(f"    mapeo país->ISO: {len(name_to_iso)} entradas")

    print(">>> Augmentando...")
    augmented = augment(historical, aliases, name_to_iso, name_to_iso)

    # Persistencia
    out_path = PROCESSED / "matches_historical_v2.csv"
    augmented.to_csv(out_path, index=False)

    mapping = build_team_name_mapping()
    mapping_path = PROCESSED / "team_name_mapping.csv"
    mapping.to_csv(mapping_path, index=False)

    # Resumen
    lines = []
    add = lines.append
    add("=" * 70)
    add(" Augmentación de matches_historical -> v2")
    add("=" * 70)
    add(f"Total partidos: {len(augmented)}")
    add(f"neutral_venue=True: {augmented['neutral_venue'].sum()} "
        f"({augmented['neutral_venue'].mean():.1%})")
    add(f"Anfitrión jugando como local: "
        f"{(augmented['host_team_iso'] == augmented['home_team_iso']).sum()}")
    add(f"Anfitrión jugando como visitante: "
        f"{((augmented['host_team_iso'] == augmented['away_team_iso']) & augmented['host_team_iso'].notna()).sum()}")
    add("")
    add("Resultado por anfitrión presente vs ausente:")
    host_present = augmented[augmented["host_team_iso"].notna()]
    host_absent = augmented[augmented["host_team_iso"].isna()]
    add(f"  Anfitrión presente ({len(host_present)} partidos):")
    add(f"    Win-rate del anfitrión: "
        f"{((host_present['host_team_iso'] == host_present['home_team_iso']) & (host_present['result_1x2'] == 'H')).sum() + ((host_present['host_team_iso'] == host_present['away_team_iso']) & (host_present['result_1x2'] == 'A')).sum()}/{len(host_present)} "
        f"({(((host_present['host_team_iso'] == host_present['home_team_iso']) & (host_present['result_1x2'] == 'H')).sum() + ((host_present['host_team_iso'] == host_present['away_team_iso']) & (host_present['result_1x2'] == 'A')).sum()) / len(host_present):.1%})")
    add(f"  Anfitrión ausente / neutral ({len(host_absent)} partidos):")
    res_neutral = host_absent['result_1x2'].value_counts(normalize=True).sort_index()
    for k in ("H", "D", "A"):
        if k in res_neutral:
            add(f"    {k}: {res_neutral[k]:.1%}")
    add("")
    add("Time weights muestra (rate=0.05, ref=2022):")
    sample_years = [1930, 1950, 1970, 1990, 1994, 2002, 2014, 2022]
    for y in sample_years:
        w = math.exp(-DECAY_RATE * (REFERENCE_YEAR - y))
        add(f"  {y}: {w:.3f}")
    add("")
    add("Aliases aplicados (cantidad de filas con código histórico):")
    for hist_iso, mod_iso in aliases.items():
        n = ((historical["home_team_code"] == hist_iso) | (historical["away_team_code"] == hist_iso)).sum() if "home_team_code" in historical.columns else 0
        # Recalculamos desde augmented (que ya renombró)
        n2 = ((augmented["home_team_iso_raw"] == hist_iso) | (augmented["away_team_iso_raw"] == hist_iso)).sum()
        add(f"  {hist_iso} -> {mod_iso}: {n2} apariciones aliasadas")
    add("")

    summary = "\n".join(lines)
    (PROCESSED / "augmentation_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)
    print(f">>> Outputs: {out_path.name}, {mapping_path.name}, augmentation_summary.txt")


if __name__ == "__main__":
    main()

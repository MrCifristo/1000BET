"""
consolidate_team_features.py — Une todas las features de selección en un único DataFrame.

Joins (sobre iso_code):
  team_wc_experience.csv   (1 fila/team)
  team_upset_index.csv     (1 fila/team)
  team_host_affinity.csv   (3 filas/team, pivotado a wide: _usa _can _mex)

Imputación de NaN para debutantes (CPV, CUW, JOR, UZB):
  - métricas de win/draw/loss: 0
  - upset_rate / recent_form_delta: mediana del corpus (decisión transparente)
  - is_debutant_2026 ya está flagged → el modelo puede tratarlos distinto

Output:
  data/features/teams_features.csv  (48 selecciones × ~40 features)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE = PROJECT_ROOT / "data" / "raw" / "reference"
FEATURES_DIR = PROJECT_ROOT / "data" / "features"


def pivot_host_affinity(affinity: pd.DataFrame) -> pd.DataFrame:
    """De long (team × host) a wide (1 fila/team con columnas _usa/_can/_mex)."""
    pieces = []
    for host in ("USA", "CAN", "MEX"):
        sub = affinity[affinity["host_iso"] == host].drop(columns=["host_iso"])
        suffix = host.lower()
        sub = sub.rename(columns={
            c: f"{c}_{suffix}" for c in sub.columns if c != "iso_code"
        })
        pieces.append(sub.set_index("iso_code"))
    return pd.concat(pieces, axis=1).reset_index()


def main() -> None:
    teams_meta = pd.read_csv(REFERENCE / "team_codes_mapping.csv")[
        ["iso_code", "openfootball_name", "country_full"]
    ]
    experience = pd.read_csv(FEATURES_DIR / "team_wc_experience.csv")
    upset = pd.read_csv(FEATURES_DIR / "team_upset_index.csv")
    affinity = pd.read_csv(FEATURES_DIR / "team_host_affinity.csv")

    affinity_wide = pivot_host_affinity(affinity)

    df = teams_meta.merge(experience, on="iso_code", how="left")
    df = df.merge(upset, on="iso_code", how="left")
    df = df.merge(affinity_wide, on="iso_code", how="left")

    # --- Imputación para debutantes ---
    # Marcamos explícito quién no tiene historia (ya hay is_debutant_2026 desde upset_index)
    debutants_mask = df["wc_matches"] == 0
    # Imputamos métricas histórico-dependientes con la MEDIANA del corpus no-debutante
    impute_cols = ["upset_rate", "recent_form_delta", "goal_diff_stdev_wc"]
    median_vals = df.loc[~debutants_mask, impute_cols].median()
    for c in impute_cols:
        df[c] = df[c].fillna(median_vals[c])

    # Para wc_years_since_last_appearance debutantes: usamos un valor "muy alto" para
    # señalizar "no han estado nunca" — 100 es claro y separable.
    df["wc_years_since_last_appearance"] = df["wc_years_since_last_appearance"].fillna(100)

    out = FEATURES_DIR / "teams_features.csv"
    df.to_csv(out, index=False)

    print(f">>> Escrito {out.relative_to(PROJECT_ROOT)}")
    print(f"    Shape: {df.shape}")
    print(f"    Columnas: {len(df.columns)}")
    print()
    print("Columnas:")
    for c in df.columns:
        print(f"  - {c}")
    print()
    print("Sample (5 selecciones):")
    sample_isos = ["BRA", "ARG", "USA", "JPN", "CPV"]
    sub = df[df["iso_code"].isin(sample_isos)].set_index("iso_code")
    print(sub[[
        "wc_appearances", "wc_points_per_match", "wc_best_stage_reached",
        "upset_rate", "recent_form_delta",
        "distance_km_usa", "diaspora_estimate_usa", "shared_language_usa",
        "is_debutant_2026",
    ]].to_string())


if __name__ == "__main__":
    main()

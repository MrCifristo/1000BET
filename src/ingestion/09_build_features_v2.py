"""
Fase 3 — Script 09: Build teams_features_v2.csv

Consolida todos los features de Fase 2 y Fase 3 en un único DataFrame:
  - teams_features.csv          (Fase 2: WC experience + host affinity + upset index)
  - elo_ratings.csv             (Fase 3: Elo actual + peak)
  - squad_values.csv            (Fase 3: valor de plantilla Transfermarkt)
  - statsbomb_team_stats.csv    (Fase 3: xG/90, xGA/90, possession WC+Euros+Copa+AFCON)
  - squad_club_stats.csv        (Fase 3: stats club 2024-25 vía Understat Big 5)
  - fbref_intl_stats.csv        (Fase 3: stats internacionales vía FBref — 15 selecciones non-Big5)

Salida: data/features/teams_features_v2.csv
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = ROOT / "data/features"
OUTPUT_CSV = FEATURES_DIR / "teams_features_v2.csv"

INPUTS = {
    "base":        FEATURES_DIR / "teams_features.csv",
    "elo":         FEATURES_DIR / "elo_ratings.csv",
    "squad_value": FEATURES_DIR / "squad_values.csv",
    "statsbomb":   FEATURES_DIR / "statsbomb_team_stats.csv",
    "squad_stats": FEATURES_DIR / "squad_club_stats.csv",
    "fbref_intl":  FEATURES_DIR / "fbref_intl_stats.csv",
}


def load_and_check(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input: {path.relative_to(ROOT)}")
    df = pd.read_csv(path)
    assert "iso_code" in df.columns, f"{name}: missing iso_code column"
    print(f"  {name}: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


def main():
    print("=== 09_build_features_v2.py ===")

    dfs = {name: load_and_check(path, name) for name, path in INPUTS.items()}

    # ── Join strategy: left join all onto base (48 teams) ──────────────────────
    result = dfs["base"]

    # Elo: add elo_rank, elo_rating, elo_peak
    elo_cols = ["iso_code", "elo_rank", "elo_rating", "elo_peak"]
    result = result.merge(dfs["elo"][elo_cols], on="iso_code", how="left")

    # Squad values: add squad_value_m_eur, squad_avg_value_m_eur, log_squad_value, etc.
    sv_cols = ["iso_code", "squad_value_m_eur", "squad_avg_value_m_eur",
               "log_squad_value", "squad_value_rank", "squad_avg_age"]
    result = result.merge(dfs["squad_value"][sv_cols], on="iso_code", how="left")

    # StatsBomb: add xG features
    sb_cols = [
        "iso_code", "sb_total_matches", "sb_tournaments",
        "sb_xg_per90", "sb_xga_per90", "sb_xg_diff_per90",
        "sb_shots_per90", "sb_shots_on_target_per90", "sb_possession_pct",
    ]
    result = result.merge(
        dfs["statsbomb"][[c for c in sb_cols if c in dfs["statsbomb"].columns]],
        on="iso_code", how="left"
    )

    # Squad club stats: add Understat-based squad features
    sq_cols = [
        "iso_code", "sq_npxg_per90", "sq_xa_per90", "sq_npxgxa_per90",
        "sq_xg_chain_per90", "sq_avg_minutes", "sq_big5_coverage_pct", "sq_players_in_big5",
    ]
    result = result.merge(
        dfs["squad_stats"][[c for c in sq_cols if c in dfs["squad_stats"].columns]],
        on="iso_code", how="left"
    )

    # FBref international stats: goals/assists per 90 in international games (15 non-Big5 teams)
    fb_cols = [
        "iso_code", "fb_npgls_per90", "fb_gls_per90", "fb_ast_per90",
        "fb_intl_mins_avg", "fb_intl_coverage_pct", "fb_squad_matched",
    ]
    result = result.merge(
        dfs["fbref_intl"][[c for c in fb_cols if c in dfs["fbref_intl"].columns]],
        on="iso_code", how="left"
    )

    assert len(result) == 48, f"Expected 48 rows, got {len(result)}"

    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_CSV, index=False)

    n_new_cols = result.shape[1] - dfs["base"].shape[1]
    print(f"\nSaved → {OUTPUT_CSV.relative_to(ROOT)}")
    print(f"  Shape: {result.shape} (+{n_new_cols} new features vs Fase 2)")

    # Coverage report
    print("\n── Coverage report ──────────────────────────────────────────────────")
    key_features = [
        "elo_rating", "squad_value_m_eur",
        "sb_xg_per90", "sq_npxg_per90", "fb_npgls_per90",
    ]
    for col in key_features:
        non_null = result[col].notna().sum()
        print(f"  {col:30s}: {non_null}/48 teams ({100*non_null/48:.0f}%)")

    # Sanity check: top teams by composite signal
    print("\n── Sanity check: top 10 by Elo ─────────────────────────────────────")
    top = result.nlargest(10, "elo_rating")[
        ["iso_code", "elo_rating", "squad_value_m_eur", "sb_xg_diff_per90", "sq_npxgxa_per90"]
    ]
    print(top.to_string(index=False))

    print("\n── NaN summary (Phase 4 will need to handle these) ─────────────────")
    null_counts = result[key_features].isna().sum()
    print(null_counts.to_string())


if __name__ == "__main__":
    main()

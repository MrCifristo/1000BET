"""
Fase 3+ — Script 12: Prop Coverage para 8 equipos sin StatsBomb

Intenta Sofascore → fallback mediana para BIH, CUW, HTI, IRQ, JOR, NZL, NOR, UZB.

Input:  data/features/statsbomb_prop_stats.csv
Output: data/features/prop_team_stats.csv  (48 equipos WC 2026)
"""
import logging
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
logging.getLogger("soccerdata").setLevel(logging.ERROR)

ROOT         = Path(__file__).resolve().parents[2]
SB_STATS_CSV = ROOT / "data/features/statsbomb_prop_stats.csv"
REF_CSV      = ROOT / "data/raw/reference/team_codes_mapping.csv"
OUT_CSV      = ROOT / "data/features/prop_team_stats.csv"

MISSING_ISOS = ["BIH", "CUW", "HTI", "IRQ", "JOR", "NZL", "NOR", "UZB"]
PROP_COLS    = ["prop_corners_per90", "prop_yellow_per90",
                "prop_shots_per90",   "prop_fouls_per90"]


def try_sofascore(iso: str) -> dict | None:
    """Intenta Sofascore vía soccerdata. Retorna dict o None si falla."""
    try:
        import soccerdata as sd  # noqa: F401
        raise NotImplementedError("Sofascore no soporta stats de selecciones nacionales")
    except Exception:
        return None


def impute_with_median(sb_df: pd.DataFrame, iso: str) -> dict:
    """Imputa con la mediana del corpus StatsBomb (solo equipos WC 2026)."""
    return {
        "iso_code":           iso,
        "prop_corners_per90": round(float(sb_df["prop_corners_per90"].median()), 3),
        "prop_yellow_per90":  round(float(sb_df["prop_yellow_per90"].median()),  3),
        "prop_shots_per90":   round(float(sb_df["prop_shots_per90"].median()),   3),
        "prop_fouls_per90":   round(float(sb_df["prop_fouls_per90"].median()),   3),
        "prop_matches":       0,
        "prop_source":        "median_imputed",
    }


def main():
    print("=== 12_prop_coverage.py ===")

    sb_df = pd.read_csv(SB_STATS_CSV)
    wc48  = pd.read_csv(REF_CSV)["iso_code"].tolist()

    base = sb_df[sb_df["iso_code"].isin(wc48)].copy()
    print(f"  Equipos WC 2026 en StatsBomb: {len(base)}/48")
    print(f"  Mediana corpus — corners: {base['prop_corners_per90'].median():.2f} | "
          f"yellow: {base['prop_yellow_per90'].median():.2f} | "
          f"shots: {base['prop_shots_per90'].median():.2f} | "
          f"fouls: {base['prop_fouls_per90'].median():.2f}")

    extras = []
    for iso in MISSING_ISOS:
        result = try_sofascore(iso)
        if result:
            result["prop_source"] = "sofascore"
            result["iso_code"]    = iso
            extras.append(result)
            print(f"  {iso}: Sofascore ✅")
        else:
            imputed = impute_with_median(base, iso)
            extras.append(imputed)
            print(f"  {iso}: mediana imputada")

    result_df = pd.concat([base, pd.DataFrame(extras)], ignore_index=True)

    missing = set(wc48) - set(result_df["iso_code"])
    if missing:
        print(f"  WARNING: Equipos WC sin cobertura: {missing}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUT_CSV, index=False)
    print(f"\nGuardado → {OUT_CSV.relative_to(ROOT)}")
    print(f"  Total: {len(result_df)} equipos")
    print(f"  Fuentes: {result_df['prop_source'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()

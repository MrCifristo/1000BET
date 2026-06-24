"""
Fase 3 — Script 06: StatsBomb Features
Fuente: data/raw/statsbomb/ (output de 05_statsbomb_ingestion.py)

Parsea los eventos JSON de StatsBomb para extraer:
1. xG por equipo por partido → data/processed/matches_enriched.csv
   (solo WC 2018 y 2022, para enriquecer el historial)
2. Stats agregadas por selección en los 6 torneos (xG, shots, possession) →
   data/features/statsbomb_team_stats.csv

Columnas clave del output de features:
  iso_code, sb_xg_per90, sb_xga_per90, sb_xg_diff_per90,
  sb_shots_per90, sb_shots_on_target_per90, sb_possession_pct,
  sb_matches_played, sb_tournaments
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_SB = ROOT / "data/raw/statsbomb"
REFERENCE_CSV = ROOT / "data/raw/reference/team_codes_mapping.csv"
TEAM_NAME_MAP_CSV = ROOT / "data/processed/team_name_mapping.csv"
OUT_ENRICHED = ROOT / "data/processed/matches_enriched.csv"
OUT_FEATURES = ROOT / "data/features/statsbomb_team_stats.csv"

# Torneos solo para matches_enriched (partidos WC históricos)
WC_COMPS = {(43, 3): "WC2018", (43, 106): "WC2022"}

# Todos los torneos para features de selección
ALL_COMPS = {
    (43, 3): "WC2018",
    (43, 106): "WC2022",
    (55, 43): "Euro2020",
    (55, 282): "Euro2024",
    (223, 282): "CopaAmerica2024",
    (1267, 107): "AFCON2023",
}

MINUTES_PER_MATCH = 90


def load_team_name_map() -> dict:
    """openfootball name → ISO 3-letter code"""
    df = pd.read_csv(TEAM_NAME_MAP_CSV)
    return dict(zip(df["openfootball_name"], df["iso_code"]))


def load_statsbomb_name_map() -> dict:
    """StatsBomb uses its own team names — build a best-effort name → ISO map."""
    # StatsBomb names closely follow openfootball / common English names
    # We supplement with manual overrides for known divergences
    base = load_team_name_map()
    overrides = {
        "United States": "USA",
        "United States of America": "USA",
        "USA": "USA",
        "Ivory Coast": "CIV",
        "DR Congo": "COD",
        "Republic of Ireland": "IRL",
        "Korea Republic": "KOR",
        "South Korea": "KOR",
        "Iran": "IRN",
        "Czech Republic": "CZE",
        "Czechia": "CZE",
        "Bosnia and Herzegovina": "BIH",
        "Bosnia & Herzegovina": "BIH",
        "Cape Verde": "CPV",
        "Cape Verde Islands": "CPV",
        "Curacao": "CUW",
        "Curaçao": "CUW",
        "Jordan": "JOR",
        "Uzbekistan": "UZB",
        "New Zealand": "NZL",
        "Côte d'Ivoire": "CIV",
        "Cote d'Ivoire": "CIV",
        "Congo DR": "COD",
        "DR Congo": "COD",
        "Democratic Republic of Congo": "COD",
    }
    base.update(overrides)
    return base


def load_matches(comp_dir: Path) -> list[dict]:
    path = comp_dir / "matches.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_events(comp_dir: Path, match_id: int) -> list[dict]:
    path = comp_dir / "events" / f"{match_id}.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def extract_match_xg(events: list[dict]) -> dict[str, float]:
    """Sum xG (shot.statsbomb_xg) per team from event list."""
    xg: dict[str, float] = {}
    for ev in events:
        if ev.get("type", {}).get("name") != "Shot":
            continue
        team = ev.get("team", {}).get("name", "")
        shot_xg = ev.get("shot", {}).get("statsbomb_xg", 0.0) or 0.0
        xg[team] = xg.get(team, 0.0) + shot_xg
    return xg


def extract_match_shots(events: list[dict]) -> dict[str, dict]:
    """Count shots and shots on target per team."""
    stats: dict[str, dict] = {}
    for ev in events:
        if ev.get("type", {}).get("name") != "Shot":
            continue
        team = ev.get("team", {}).get("name", "")
        if team not in stats:
            stats[team] = {"shots": 0, "shots_on_target": 0}
        stats[team]["shots"] += 1
        outcome = ev.get("shot", {}).get("outcome", {}).get("name", "")
        if outcome in ("Goal", "Saved", "Saved To Post"):
            stats[team]["shots_on_target"] += 1
    return stats


def extract_possession(events: list[dict]) -> dict[str, float]:
    """Approximate possession % from pass/carry/dribble event counts per team."""
    counts: dict[str, int] = {}
    relevant = {"Pass", "Carry", "Dribble"}
    for ev in events:
        if ev.get("type", {}).get("name") not in relevant:
            continue
        team = ev.get("team", {}).get("name", "")
        counts[team] = counts.get(team, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {t: v / total * 100 for t, v in counts.items()}


def parse_competition(comp_key: tuple, label: str, name_map: dict) -> tuple[list, list]:
    """
    Returns:
      enriched_rows: list of dicts for matches_enriched.csv (only for WC comps)
      feature_rows: list of dicts (team-level aggregated stats)
    """
    cid, sid = comp_key
    comp_dir = RAW_SB / f"{cid}_{sid}"
    matches = load_matches(comp_dir)
    if not matches:
        print(f"  WARNING: no data for {label} — run 05 first")
        return [], []

    is_wc = comp_key in WC_COMPS

    enriched_rows = []
    # team_stats[team_name] = {xg_for, xga, shots, shots_on_target, possession, matches}
    team_stats: dict[str, dict] = {}

    for match in matches:
        mid = match["match_id"]
        home_name = match.get("home_team", {}).get("home_team_name", "")
        away_name = match.get("away_team", {}).get("away_team_name", "")
        home_score = match.get("home_score", 0)
        away_score = match.get("away_score", 0)
        match_date = match.get("match_date", "")

        events = load_events(comp_dir, mid)
        if not events:
            continue

        xg = extract_match_xg(events)
        shots = extract_match_shots(events)
        possession = extract_possession(events)

        home_xg = xg.get(home_name, 0.0)
        away_xg = xg.get(away_name, 0.0)

        if is_wc:
            home_iso = name_map.get(home_name)
            away_iso = name_map.get(away_name)
            enriched_rows.append({
                "tournament": label,
                "match_id": mid,
                "match_date": match_date,
                "home_team": home_name,
                "away_team": away_name,
                "home_iso": home_iso,
                "away_iso": away_iso,
                "home_score": home_score,
                "away_score": away_score,
                "home_xg": round(home_xg, 4),
                "away_xg": round(away_xg, 4),
            })

        for team_name in [home_name, away_name]:
            if team_name not in team_stats:
                team_stats[team_name] = {
                    "xg_for": 0.0, "xg_against": 0.0,
                    "shots": 0, "shots_on_target": 0,
                    "possession_sum": 0.0, "matches": 0,
                }
            opponent = away_name if team_name == home_name else home_name
            s = team_stats[team_name]
            s["xg_for"] += xg.get(team_name, 0.0)
            s["xg_against"] += xg.get(opponent, 0.0)
            t_shots = shots.get(team_name, {})
            s["shots"] += t_shots.get("shots", 0)
            s["shots_on_target"] += t_shots.get("shots_on_target", 0)
            s["possession_sum"] += possession.get(team_name, 50.0)
            s["matches"] += 1

    feature_rows = []
    for team_name, s in team_stats.items():
        m = max(s["matches"], 1)
        minutes = m * MINUTES_PER_MATCH
        feature_rows.append({
            "team_name": team_name,
            "iso_code": name_map.get(team_name),
            "tournament": label,
            "sb_matches": m,
            "sb_xg_for": round(s["xg_for"], 3),
            "sb_xg_against": round(s["xg_against"], 3),
            "sb_xg_per90": round(s["xg_for"] / minutes * 90, 3),
            "sb_xga_per90": round(s["xg_against"] / minutes * 90, 3),
            "sb_xg_diff_per90": round((s["xg_for"] - s["xg_against"]) / minutes * 90, 3),
            "sb_shots_per90": round(s["shots"] / minutes * 90, 3),
            "sb_shots_on_target_per90": round(s["shots_on_target"] / minutes * 90, 3),
            "sb_possession_pct": round(s["possession_sum"] / m, 2),
        })

    print(f"  {label}: {len(matches)} matches, {len(feature_rows)} teams parsed")
    return enriched_rows, feature_rows


def aggregate_across_tournaments(all_rows: list[dict]) -> pd.DataFrame:
    """
    Weighted average of per-90 metrics across tournaments.
    Weight = number of matches played in each tournament.
    """
    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    # Drop rows with no ISO match (teams not in our 48)
    wc48 = pd.read_csv(REFERENCE_CSV)["iso_code"].tolist()
    df_known = df[df["iso_code"].isin(wc48)].copy()

    metric_cols = [
        "sb_xg_per90", "sb_xga_per90", "sb_xg_diff_per90",
        "sb_shots_per90", "sb_shots_on_target_per90", "sb_possession_pct",
    ]

    records = []
    for iso, grp in df_known.groupby("iso_code"):
        total_matches = grp["sb_matches"].sum()
        weights = grp["sb_matches"].values
        row = {
            "iso_code": iso,
            "sb_total_matches": int(total_matches),
            "sb_tournaments": ", ".join(sorted(grp["tournament"].tolist())),
        }
        for col in metric_cols:
            row[col] = round(
                (grp[col] * weights).sum() / total_matches, 3
            )
        records.append(row)

    result = pd.DataFrame(records).sort_values("iso_code").reset_index(drop=True)

    # Teams with no StatsBomb data get NaN (model handles missing)
    all_isos = pd.DataFrame({"iso_code": wc48})
    result = all_isos.merge(result, on="iso_code", how="left")
    missing = result[result["sb_total_matches"].isna()]["iso_code"].tolist()
    if missing:
        print(f"  Teams with no StatsBomb data (NaN features): {missing}")

    return result


def main():
    print("=== 06_statsbomb_features.py ===")
    name_map = load_statsbomb_name_map()

    all_enriched = []
    all_feature_rows = []

    for comp_key, label in ALL_COMPS.items():
        enriched, features = parse_competition(comp_key, label, name_map)
        all_enriched.extend(enriched)
        all_feature_rows.extend(features)

    # Save matches_enriched.csv (WC 2018 + 2022 with xG)
    if all_enriched:
        enr_df = pd.DataFrame(all_enriched).sort_values(["tournament", "match_date"])
        OUT_ENRICHED.parent.mkdir(parents=True, exist_ok=True)
        enr_df.to_csv(OUT_ENRICHED, index=False)
        print(f"\nSaved matches_enriched → {OUT_ENRICHED.relative_to(ROOT)}")
        print(f"  {len(enr_df)} WC matches with xG data")

    # Save aggregated team stats
    agg = aggregate_across_tournaments(all_feature_rows)
    OUT_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(OUT_FEATURES, index=False)
    print(f"Saved statsbomb_team_stats → {OUT_FEATURES.relative_to(ROOT)}")
    print(f"  {agg['sb_total_matches'].notna().sum()} teams with StatsBomb coverage")

    print("\nSample (top xG diff per 90):")
    sample = agg.dropna(subset=["sb_xg_diff_per90"]).nlargest(8, "sb_xg_diff_per90")
    print(sample[["iso_code", "sb_xg_diff_per90", "sb_xg_per90", "sb_total_matches"]].to_string(index=False))


if __name__ == "__main__":
    main()

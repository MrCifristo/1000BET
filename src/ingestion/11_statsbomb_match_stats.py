"""
Fase 3+ — Script 11: StatsBomb Match Props

Extrae corners, tarjetas, disparos y faltas de los 314 eventos JSON ya descargados.

Outputs:
  data/processed/statsbomb_match_props.csv  — una fila por partido (para training)
  data/features/statsbomb_prop_stats.csv    — promedios por equipo por 90' (para features)
"""
import json
from pathlib import Path

import pandas as pd

ROOT      = Path(__file__).resolve().parents[2]
SB_DIR    = ROOT / "data/raw/statsbomb"
OUT_MATCH = ROOT / "data/processed/statsbomb_match_props.csv"
OUT_TEAM  = ROOT / "data/features/statsbomb_prop_stats.csv"

SB_TO_ISO = {
    "Albania": "ALB", "Algeria": "DZA", "Angola": "AGO", "Argentina": "ARG",
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Bolivia": "BOL",
    "Brazil": "BRA", "Burkina Faso": "BFA", "Cameroon": "CMR", "Canada": "CAN",
    "Cape Verde Islands": "CPV", "Chile": "CHL", "Colombia": "COL", "Congo DR": "COD",
    "Costa Rica": "CRI", "Croatia": "HRV", "Czech Republic": "CZE",
    "Côte d'Ivoire": "CIV", "Denmark": "DNK", "Ecuador": "ECU", "Egypt": "EGY",
    "England": "ENG", "Equatorial Guinea": "GNQ", "Finland": "FIN", "France": "FRA",
    "Gambia": "GMB", "Georgia": "GEO", "Germany": "DEU", "Ghana": "GHA",
    "Guinea": "GIN", "Guinea-Bissau": "GNB", "Hungary": "HUN", "Iceland": "ISL",
    "Iran": "IRN", "Italy": "ITA", "Jamaica": "JAM", "Japan": "JPN", "Mali": "MLI",
    "Mauritania": "MRT", "Mexico": "MEX", "Morocco": "MAR", "Mozambique": "MOZ",
    "Namibia": "NAM", "Netherlands": "NLD", "Nigeria": "NGA",
    "North Macedonia": "MKD", "Panama": "PAN", "Paraguay": "PRY", "Peru": "PER",
    "Poland": "POL", "Portugal": "PRT", "Qatar": "QAT", "Romania": "ROU",
    "Russia": "RUS", "Saudi Arabia": "SAU", "Scotland": "SCO", "Senegal": "SEN",
    "Serbia": "SRB", "Slovakia": "SVK", "Slovenia": "SVN", "South Africa": "ZAF",
    "South Korea": "KOR", "Spain": "ESP", "Sweden": "SWE", "Switzerland": "CHE",
    "Tanzania": "TZA", "Tunisia": "TUN", "Turkey": "TUR", "Ukraine": "UKR",
    "United States": "USA", "Uruguay": "URY", "Venezuela": "VEN", "Wales": "WAL",
    "Zambia": "ZMB",
}

WC2026_ISOS = {
    "ARG","AUS","AUT","BEL","BIH","BRA","CAN","CPV","CIV","COD",
    "COL","CUW","CZE","DEU","DZA","ECU","EGY","ENG","ESP","FRA",
    "GHA","HRV","HTI","IRN","IRQ","JOR","JPN","KOR","MAR","MEX",
    "NLD","NOR","NZL","PAN","PRT","PRY","QAT","SAU","SCO","SEN",
    "SWE","CHE","TUN","TUR","URY","USA","UZB","ZAF",
}


def extract_team_stats(events: list, team_name: str) -> dict:
    corners = sum(
        1 for e in events
        if e["type"]["name"] == "Pass"
        and e.get("team", {}).get("name") == team_name
        and e.get("pass", {}).get("type", {}).get("name") == "Corner"
    )
    fouls = sum(
        1 for e in events
        if e["type"]["name"] == "Foul Committed"
        and e.get("team", {}).get("name") == team_name
    )
    yellow = (
        sum(1 for e in events
            if e["type"]["name"] == "Foul Committed"
            and e.get("team", {}).get("name") == team_name
            and e.get("foul_committed", {}).get("card", {}).get("name") == "Yellow Card")
        + sum(1 for e in events
              if "bad_behaviour" in e
              and e.get("team", {}).get("name") == team_name
              and e.get("bad_behaviour", {}).get("card", {}).get("name") == "Yellow Card")
    )
    red = (
        sum(1 for e in events
            if e["type"]["name"] == "Foul Committed"
            and e.get("team", {}).get("name") == team_name
            and e.get("foul_committed", {}).get("card", {}).get("name") in {"Red Card", "Second Yellow"})
        + sum(1 for e in events
              if "bad_behaviour" in e
              and e.get("team", {}).get("name") == team_name
              and e.get("bad_behaviour", {}).get("card", {}).get("name") in {"Red Card", "Second Yellow"})
    )
    shots = sum(
        1 for e in events
        if e["type"]["name"] == "Shot"
        and e.get("team", {}).get("name") == team_name
    )
    shots_ot = sum(
        1 for e in events
        if e["type"]["name"] == "Shot"
        and e.get("team", {}).get("name") == team_name
        and e.get("shot", {}).get("outcome", {}).get("name") in {"Goal", "Saved"}
    )
    return {
        "corners": corners, "yellow_cards": yellow, "red_cards": red,
        "fouls": fouls, "shots": shots, "shots_on_target": shots_ot,
    }


def main():
    print("=== 11_statsbomb_match_stats.py ===")

    match_rows = []
    skipped    = 0

    for comp_dir in sorted(SB_DIR.iterdir()):
        if not comp_dir.is_dir():
            continue
        matches_file = comp_dir / "matches.json"
        events_dir   = comp_dir / "events"
        if not matches_file.exists() or not events_dir.exists():
            continue

        with open(matches_file) as f:
            matches = json.load(f)

        comp_name = matches[0]["competition"]["competition_name"] if matches else comp_dir.name
        print(f"  {comp_name}: {len(matches)} partidos")

        for match in matches:
            home_name = match["home_team"]["home_team_name"]
            away_name = match["away_team"]["away_team_name"]
            home_iso  = SB_TO_ISO.get(home_name)
            away_iso  = SB_TO_ISO.get(away_name)

            if home_iso is None or away_iso is None:
                skipped += 1
                continue

            event_file = events_dir / f"{match['match_id']}.json"
            if not event_file.exists():
                skipped += 1
                continue

            with open(event_file) as f:
                events = json.load(f)

            hs  = extract_team_stats(events, home_name)
            as_ = extract_team_stats(events, away_name)
            year = int(match["match_date"][:4])

            match_rows.append({
                "match_id":      match["match_id"],
                "year":          year,
                "home_team_iso": home_iso,
                "away_team_iso": away_iso,
                "host_team_iso": None,
                "home_corners":  hs["corners"],    "away_corners":  as_["corners"],
                "home_yellow":   hs["yellow_cards"],"away_yellow":  as_["yellow_cards"],
                "home_red":      hs["red_cards"],   "away_red":     as_["red_cards"],
                "home_shots":    hs["shots"],       "away_shots":   as_["shots"],
                "home_shots_ot": hs["shots_on_target"], "away_shots_ot": as_["shots_on_target"],
                "home_fouls":    hs["fouls"],       "away_fouls":   as_["fouls"],
            })

    df = pd.DataFrame(match_rows)
    OUT_MATCH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_MATCH, index=False)
    print(f"\n  {len(df)} partidos → {OUT_MATCH.relative_to(ROOT)} ({skipped} omitidos)")

    # Promedios por equipo
    team_records = []
    all_isos = set(df["home_team_iso"]) | set(df["away_team_iso"])

    for iso in sorted(all_isos):
        hm = df[df["home_team_iso"] == iso]
        aw = df[df["away_team_iso"] == iso]
        n  = len(hm) + len(aw)
        if n == 0:
            continue
        team_records.append({
            "iso_code":           iso,
            "prop_corners_per90": round((hm["home_corners"].sum() + aw["away_corners"].sum()) / n, 3),
            "prop_yellow_per90":  round((hm["home_yellow"].sum()  + aw["away_yellow"].sum())  / n, 3),
            "prop_shots_per90":   round((hm["home_shots"].sum()   + aw["away_shots"].sum())   / n, 3),
            "prop_fouls_per90":   round((hm["home_fouls"].sum()   + aw["away_fouls"].sum())   / n, 3),
            "prop_matches":       n,
            "prop_source":        "statsbomb",
        })

    team_df = pd.DataFrame(team_records)
    OUT_TEAM.parent.mkdir(parents=True, exist_ok=True)
    team_df.to_csv(OUT_TEAM, index=False)
    print(f"  {len(team_df)} equipos → {OUT_TEAM.relative_to(ROOT)}")

    wc_covered = team_df[team_df["iso_code"].isin(WC2026_ISOS)]
    print(f"  Equipos WC 2026 cubiertos: {len(wc_covered)}/48")
    print(f"\nTop 10 por corners/partido:")
    print(team_df.nlargest(10, "prop_corners_per90")[
        ["iso_code", "prop_corners_per90", "prop_yellow_per90", "prop_shots_per90"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()

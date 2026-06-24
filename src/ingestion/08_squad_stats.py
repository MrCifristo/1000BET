"""
Fase 3 — Script 08: Squad Stats (Wikipedia squads + Understat club stats)

1. Descarga los squads confirmados del Mundial 2026 desde Wikipedia
   → data/processed/wc2026_squads.csv

2. Descarga stats de jugadores (temporada 2024-25) de las Big 5 ligas via Understat
   Coverage: ~60-70% de los jugadores del mundial (los que juegan en Big 5)

3. Agrega a nivel de selección ponderando por minutos jugados
   → data/features/squad_club_stats.csv

Columnas clave del output:
  iso_code, sq_npxg_per90, sq_xa_per90, sq_npxgxa_per90,
  sq_xg_chain_per90, sq_avg_minutes, sq_big5_coverage_pct,
  sq_players_in_big5
"""

import io
import logging
import time
import unicodedata
import warnings
from pathlib import Path

import pandas as pd
import requests
import soccerdata as sd
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")
logging.getLogger("soccerdata").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CSV = ROOT / "data/raw/reference/team_codes_mapping.csv"
OUT_SQUADS = ROOT / "data/processed/wc2026_squads.csv"
OUT_FEATURES = ROOT / "data/features/squad_club_stats.csv"

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIKI_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
UNDERSTAT_LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "FRA-Ligue 1",
    "GER-Bundesliga",
    "ITA-Serie A",
]
MIN_MINUTES = 90  # exclude players with fewer than this many club minutes

# Wikipedia team order matches the WC 2026 group draw.
# Built from the page ToC (48 teams in group order A→L, 4 per group).
# Static fallback mapping from Wikipedia team name → ISO code.
# Dynamically extracted from h3 headings on the page (order matters).
WIKI_NAME_TO_ISO = {
    "Czech Republic": "CZE", "Mexico": "MEX", "South Africa": "ZAF",
    "South Korea": "KOR", "Bosnia and Herzegovina": "BIH", "Canada": "CAN",
    "Qatar": "QAT", "Switzerland": "CHE", "Brazil": "BRA", "Haiti": "HTI",
    "Morocco": "MAR", "Scotland": "SCO", "Australia": "AUS", "Paraguay": "PRY",
    "Turkey": "TUR", "United States": "USA", "Curaçao": "CUW", "Ecuador": "ECU",
    "Germany": "DEU", "Ivory Coast": "CIV", "Japan": "JPN", "Netherlands": "NLD",
    "Sweden": "SWE", "Tunisia": "TUN", "Belgium": "BEL", "Egypt": "EGY",
    "Iran": "IRN", "New Zealand": "NZL", "Cape Verde": "CPV",
    "Saudi Arabia": "SAU", "Spain": "ESP", "Uruguay": "URY", "France": "FRA",
    "Iraq": "IRQ", "Norway": "NOR", "Senegal": "SEN", "Algeria": "DZA",
    "Argentina": "ARG", "Austria": "AUT", "Jordan": "JOR", "Colombia": "COL",
    "DR Congo": "COD", "Portugal": "PRT", "Uzbekistan": "UZB", "Croatia": "HRV",
    "England": "ENG", "Ghana": "GHA", "Panama": "PAN",
}
NON_TEAM_HEADINGS = {"Age", "Coach representation by country"}


def normalize_name(s: str) -> str:
    """Lowercase, strip accents, strip wiki annotations for name matching."""
    import re
    s = str(s)
    # Strip Wikipedia annotations: (captain), (c), [1], [note 1], etc.
    s = re.sub(r"\s*\(.*?\)", "", s)   # (captain), (c), (injured), etc.
    s = re.sub(r"\s*\[.*?\]", "", s)   # [1], [note 1], etc.
    s = re.sub(r"\s*\*+$", "", s)      # trailing asterisks
    # Strip accents
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Lowercase and collapse whitespace
    return " ".join(s.lower().split())


# ─── Part 1: Wikipedia squad lists ────────────────────────────────────────────

def _parse_wikitable(table_tag) -> pd.DataFrame | None:
    """Parse a wikitable tag into a DataFrame with columns player_name, position, club."""
    rows = table_tag.find_all("tr")
    if not rows:
        return None
    headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
    data = []
    for row in rows[1:]:
        cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
        if cells:
            data.append(cells)
    if not data:
        return None
    # Normalize column count
    max_len = max(len(h) for h in [headers] + data)
    headers = headers + [""] * (max_len - len(headers))
    df = pd.DataFrame(data, columns=headers[:max_len])
    # Find Player and Club columns (flexible matching)
    player_col = next((c for c in df.columns if "Player" in c), None)
    club_col = next((c for c in df.columns if "Club" in c), None)
    pos_col = next((c for c in df.columns if "Pos" in c), None)
    if player_col is None or club_col is None:
        return None
    result = pd.DataFrame({
        "player_name": df[player_col],
        "position": df[pos_col] if pos_col else None,
        "club": df[club_col],
    })
    return result.dropna(subset=["player_name"])


def fetch_wiki_squads() -> pd.DataFrame:
    """
    Parse WC 2026 squad tables from Wikipedia by walking the DOM linearly.

    Strategy: iterate all top-level elements in the article body. When we see
    an h3 team heading, mark the current team. When we see a wikitable with
    Player+Club columns BEFORE the next h3 (i.e., while the current team is
    active), assign that table to the current team. This avoids find_next()
    skipping over headings.
    """
    print("Fetching Wikipedia WC 2026 squads ...")
    headers_req = {"User-Agent": "Mozilla/5.0 (compatible; wc2026-predictor/1.0)"}
    r = requests.get(WIKI_URL, headers=headers_req, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Modern Wikipedia wraps each heading in <div class="mw-heading mw-heading3">.
    # Structure: div.mw-parser-output > [div.mw-heading3, table.wikitable, ...]
    content = soup.find("div", class_="mw-content-ltr")
    if content is None:
        content = soup.find("div", class_="mw-parser-output")

    current_team = None
    current_iso = None
    team_tables: dict[str, list] = {}  # iso → list of dfs

    for element in content.children:
        tag_name = getattr(element, "name", None)
        if tag_name is None:
            continue  # NavigableString

        # Detect heading divs (mw-heading3 = team, mw-heading2 = group)
        if tag_name == "div":
            cls = element.get("class", [])
            if "mw-heading2" in cls:
                # Group header — reset team
                current_team = None
                current_iso = None
                continue
            if "mw-heading3" in cls:
                inner_h3 = element.find("h3")
                if inner_h3 is None:
                    continue
                text = inner_h3.get_text(strip=True)
                if text in NON_TEAM_HEADINGS or text not in WIKI_NAME_TO_ISO:
                    current_team = None
                    current_iso = None
                    continue
                current_team = text
                current_iso = WIKI_NAME_TO_ISO[text]
                if current_iso not in team_tables:
                    team_tables[current_iso] = []
                continue
            # Regular div — scan for wikitables when team is active
            if current_iso is not None:
                for tbl in element.find_all("table", class_="wikitable"):
                    df = _parse_wikitable(tbl)
                    if df is not None and len(df) > 0 and "player_name" in df.columns:
                        team_tables[current_iso].append(df)
            continue

        # Detect tables directly (when not wrapped in div)
        if tag_name == "table" and current_iso is not None:
            cls = element.get("class", [])
            if "wikitable" in cls:
                df = _parse_wikitable(element)
                if df is not None and len(df) > 0 and "player_name" in df.columns:
                    team_tables[current_iso].append(df)
            continue

    records = []
    found_teams = 0
    for iso, dfs in team_tables.items():
        if not dfs:
            print(f"  WARNING: no table for ISO={iso}")
            continue
        # Take the FIRST matching table (the squad table)
        df = dfs[0].copy()
        team_name = next((n for n, c in WIKI_NAME_TO_ISO.items() if c == iso), iso)
        df["iso_code"] = iso
        df["team_name"] = team_name
        # Clamp to 26 rows (max squad size) to avoid spurious extra rows
        df = df.head(26)
        records.append(df)
        found_teams += 1

    print(f"  Teams parsed: {found_teams}/48")
    if not records:
        raise RuntimeError("No squad tables parsed — check Wikipedia HTML structure")

    result = pd.concat(records, ignore_index=True)
    result["player_norm"] = result["player_name"].apply(normalize_name)
    return result


# ─── Part 2: Understat player stats ───────────────────────────────────────────

def fetch_understat_stats() -> pd.DataFrame:
    print("Fetching Understat Big 5 player stats (2024-25) ...")
    us = sd.Understat(leagues=UNDERSTAT_LEAGUES, seasons=["2024-25"], no_store=True)
    stats = us.read_player_season_stats()
    stats = stats.reset_index()
    stats = stats.rename(columns={"player": "player_name_understat"})

    # Keep relevant columns
    keep = ["player_name_understat", "league_id", "team_id", "position",
            "matches", "minutes", "np_xg", "xa", "xg_chain", "xg_buildup",
            "goals", "assists"]
    stats = stats[[c for c in keep if c in stats.columns]].copy()
    stats["player_norm"] = stats["player_name_understat"].apply(normalize_name)

    print(f"  Players loaded: {len(stats)} from Big 5 leagues")
    return stats


# ─── Part 3: Match + aggregate ────────────────────────────────────────────────

def match_and_aggregate(squads: pd.DataFrame, understat: pd.DataFrame) -> pd.DataFrame:
    print("Matching squad players to Understat stats ...")

    # Build lookup: normalized name → understat row (take highest minutes if dupes)
    understat_best = (
        understat.sort_values("minutes", ascending=False)
        .drop_duplicates(subset=["player_norm"])
        .set_index("player_norm")
    )

    # Join squads to understat on normalized name
    squads["minutes"] = squads["player_norm"].map(
        understat_best["minutes"]
    )
    squads["np_xg"] = squads["player_norm"].map(understat_best["np_xg"])
    squads["xa"] = squads["player_norm"].map(understat_best["xa"])
    squads["xg_chain"] = squads["player_norm"].map(understat_best["xg_chain"])
    squads["xg_buildup"] = squads["player_norm"].map(understat_best["xg_buildup"])

    matched = squads["minutes"].notna().sum()
    total = len(squads)
    print(f"  Matched {matched}/{total} players ({100*matched/total:.1f}%)")

    # Aggregate per national team
    records = []
    wc48 = pd.read_csv(REFERENCE_CSV)["iso_code"].tolist()

    for iso, grp in squads.groupby("iso_code"):
        squad_size = len(grp)
        has_stats = grp[grp["minutes"].notna() & (grp["minutes"] >= MIN_MINUTES)]
        n_in_big5 = len(has_stats)
        coverage = n_in_big5 / squad_size if squad_size > 0 else 0

        if len(has_stats) == 0:
            records.append({
                "iso_code": iso,
                "sq_npxg_per90": None,
                "sq_xa_per90": None,
                "sq_npxgxa_per90": None,
                "sq_xg_chain_per90": None,
                "sq_avg_minutes": None,
                "sq_big5_coverage_pct": round(coverage * 100, 1),
                "sq_players_in_big5": n_in_big5,
            })
            continue

        total_mins = has_stats["minutes"].sum()

        def rate_per90(col):
            """Total col / total minutes × 90 (correct for season totals)."""
            valid = has_stats[has_stats[col].notna() & (has_stats["minutes"] > 0)]
            if len(valid) == 0 or valid["minutes"].sum() == 0:
                return None
            return round(valid[col].sum() / valid["minutes"].sum() * 90, 3)

        npxg_per90 = rate_per90("np_xg")
        xa_per90 = rate_per90("xa")
        xg_chain_per90 = rate_per90("xg_chain")

        records.append({
            "iso_code": iso,
            "sq_npxg_per90": npxg_per90,
            "sq_xa_per90": xa_per90,
            "sq_npxgxa_per90": (
                round(npxg_per90 + xa_per90, 3)
                if npxg_per90 is not None and xa_per90 is not None
                else None
            ),
            "sq_xg_chain_per90": xg_chain_per90,
            "sq_avg_minutes": round(total_mins / n_in_big5, 1),
            "sq_big5_coverage_pct": round(coverage * 100, 1),
            "sq_players_in_big5": n_in_big5,
        })

    df = pd.DataFrame(records)
    # Ensure all 48 teams present
    all_isos = pd.DataFrame({"iso_code": wc48})
    df = all_isos.merge(df, on="iso_code", how="left")
    return df.sort_values("iso_code").reset_index(drop=True)


def main():
    print("=== 08_squad_stats.py ===")

    squads = fetch_wiki_squads()
    OUT_SQUADS.parent.mkdir(parents=True, exist_ok=True)
    squads.to_csv(OUT_SQUADS, index=False)
    print(f"  Saved squads → {OUT_SQUADS.relative_to(ROOT)}")
    print(f"  Total players: {len(squads)} across {squads['iso_code'].nunique()} teams")

    understat = fetch_understat_stats()
    result = match_and_aggregate(squads, understat)

    OUT_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_FEATURES, index=False)
    print(f"\nSaved squad_club_stats → {OUT_FEATURES.relative_to(ROOT)}")

    valid = result[result["sq_npxg_per90"].notna()]
    print(f"Teams with Big 5 stats: {len(valid)}/48")
    print(f"Teams with <50% Big 5 coverage: "
          f"{(result['sq_big5_coverage_pct'].fillna(0) < 50).sum()}")

    print("\nTop 10 by npxG+xA per 90 (squad weighted avg):")
    top = result.dropna(subset=["sq_npxgxa_per90"]).nlargest(10, "sq_npxgxa_per90")
    print(top[["iso_code", "sq_npxgxa_per90", "sq_npxg_per90", "sq_xa_per90",
               "sq_big5_coverage_pct"]].to_string(index=False))

    print("\nBottom teams by Big 5 coverage (<30%):")
    low = result[result["sq_big5_coverage_pct"].fillna(0) < 30]
    print(low[["iso_code", "sq_big5_coverage_pct", "sq_players_in_big5"]].to_string(index=False))


if __name__ == "__main__":
    main()

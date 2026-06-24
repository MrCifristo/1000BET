"""
Fase 3 — Script 05: StatsBomb Open Data Ingestion
Fuente: github.com/statsbomb/open-data (raw GitHub API)

Descarga selectivamente solo los 6 torneos internacionales relevantes:
  - FIFA World Cup 2018 (comp 43, season 3)
  - FIFA World Cup 2022 (comp 43, season 106)
  - UEFA Euro 2020     (comp 55, season 43)
  - UEFA Euro 2024     (comp 55, season 282)
  - Copa America 2024  (comp 223, season 282)
  - AFCON 2023         (comp 1267, season 107)

Descarga: matches + lineups + events (NO three-sixty — demasiado pesado, no necesario)
Salida: data/raw/statsbomb/{competition_id}_{season_id}/
"""

import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW_SB = ROOT / "data/raw/statsbomb"

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; wc2026-predictor/1.0)"}

COMPETITIONS = [
    {"name": "FIFA World Cup 2018",  "competition_id": 43,   "season_id": 3},
    {"name": "FIFA World Cup 2022",  "competition_id": 43,   "season_id": 106},
    {"name": "UEFA Euro 2020",       "competition_id": 55,   "season_id": 43},
    {"name": "UEFA Euro 2024",       "competition_id": 55,   "season_id": 282},
    {"name": "Copa America 2024",    "competition_id": 223,  "season_id": 282},
    {"name": "AFCON 2023",           "competition_id": 1267, "season_id": 107},
]


def fetch_json(url: str, retries: int = 3) -> dict | list:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"    Retry {attempt}/{retries} (wait {wait}s): {e}")
            time.sleep(wait)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def download_competition(comp: dict) -> dict:
    cid = comp["competition_id"]
    sid = comp["season_id"]
    name = comp["name"]
    comp_dir = RAW_SB / f"{cid}_{sid}"

    print(f"\n── {name} (comp={cid}, season={sid}) ──────────────────────────")

    # 1. Matches index
    matches_url = f"{BASE_URL}/matches/{cid}/{sid}.json"
    matches_path = comp_dir / "matches.json"
    if matches_path.exists():
        print("  matches.json already exists, loading from cache")
        with open(matches_path) as f:
            matches = json.load(f)
    else:
        print("  Downloading matches index ...")
        matches = fetch_json(matches_url)
        save_json(matches_path, matches)

    match_ids = [m["match_id"] for m in matches]
    print(f"  {len(match_ids)} matches found")

    stats = {"name": name, "matches": len(match_ids), "events_new": 0,
             "lineups_new": 0, "events_cached": 0}

    for i, mid in enumerate(match_ids, 1):
        # 2. Lineups
        lineup_path = comp_dir / "lineups" / f"{mid}.json"
        if not lineup_path.exists():
            lineup_url = f"{BASE_URL}/lineups/{mid}.json"
            lineup_data = fetch_json(lineup_url)
            save_json(lineup_path, lineup_data)
            stats["lineups_new"] += 1
            time.sleep(0.15)  # polite rate limit

        # 3. Events
        events_path = comp_dir / "events" / f"{mid}.json"
        if events_path.exists():
            stats["events_cached"] += 1
        else:
            events_url = f"{BASE_URL}/events/{mid}.json"
            events_data = fetch_json(events_url)
            save_json(events_path, events_data)
            stats["events_new"] += 1
            time.sleep(0.15)

        if i % 10 == 0 or i == len(match_ids):
            print(f"  [{i}/{len(match_ids)}] lineups_new={stats['lineups_new']} "
                  f"events_new={stats['events_new']} cached={stats['events_cached']}")

    return stats


def main():
    print("=== 05_statsbomb_ingestion.py ===")
    RAW_SB.mkdir(parents=True, exist_ok=True)

    summary = []
    for comp in COMPETITIONS:
        stats = download_competition(comp)
        summary.append(stats)

    print("\n\n=== RESUMEN ===")
    total_matches = 0
    for s in summary:
        cached = s["events_cached"]
        new = s["events_new"]
        total_matches += s["matches"]
        print(f"  {s['name']}: {s['matches']} partidos "
              f"({new} descargados, {cached} ya en cache)")
    print(f"\nTotal partidos: {total_matches}")
    print(f"Datos guardados en: {RAW_SB.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()

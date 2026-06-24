"""
Fase 3 — Script 07: Transfermarkt Squad Values
Fuente: transfermarkt.co.uk/weltmeisterschaft/teilnehmer/pokalwettbewerb/FIWC

Scrapea los valores de mercado de plantilla para las 48 selecciones del Mundial 2026.
También intenta obtener las listas de convocados desde la página de cada equipo.
Salida: data/features/squad_values.csv
"""

import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CSV = ROOT / "data/raw/reference/team_codes_mapping.csv"
OUTPUT_CSV = ROOT / "data/features/squad_values.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.transfermarkt.co.uk/",
}

TM_WC_URL = "https://www.transfermarkt.co.uk/weltmeisterschaft/teilnehmer/pokalwettbewerb/FIWC"

# Transfermarkt team names → ISO 3-letter codes
TM_NAME_TO_ISO = {
    "France": "FRA",
    "England": "ENG",
    "Spain": "ESP",
    "Germany": "DEU",
    "Portugal": "PRT",
    "Brazil": "BRA",
    "Netherlands": "NLD",
    "Argentina": "ARG",
    "Norway": "NOR",
    "Turkiye": "TUR",
    "Turkey": "TUR",
    "Belgium": "BEL",
    "Ivory Coast": "CIV",
    "Côte d'Ivoire": "CIV",
    "Morocco": "MAR",
    "Senegal": "SEN",
    "Sweden": "SWE",
    "Croatia": "HRV",
    "Uruguay": "URY",
    "United States": "USA",
    "Switzerland": "CHE",
    "Colombia": "COL",
    "Japan": "JPN",
    "Austria": "AUT",
    "Ecuador": "ECU",
    "Ghana": "GHA",
    "Algeria": "DZA",
    "Canada": "CAN",
    "Czechia": "CZE",
    "Czech Republic": "CZE",
    "Scotland": "SCO",
    "Bosnia-Herzegovina": "BIH",
    "Bosnia and Herzegovina": "BIH",
    "Democratic Republic of the Congo": "COD",
    "DR Congo": "COD",
    "South Korea": "KOR",
    "Paraguay": "PRY",
    "Egypt": "EGY",
    "Mexico": "MEX",
    "Uzbekistan": "UZB",
    "Australia": "AUS",
    "Tunisia": "TUN",
    "Cape Verde": "CPV",
    "Haiti": "HTI",
    "South Africa": "ZAF",
    "Iran": "IRN",
    "New Zealand": "NZL",
    "Panama": "PAN",
    "Saudi Arabia": "SAU",
    "Curaçao": "CUW",
    "Iraq": "IRQ",
    "Qatar": "QAT",
    "Jordan": "JOR",
}


def parse_tm_value_to_millions(s: str) -> float | None:
    """Convert '€1.48bn' or '€56.18m' to millions (float)."""
    s = s.strip().replace(",", ".")
    match = re.search(r"[\d.]+", s)
    if not match:
        return None
    value = float(match.group())
    if "bn" in s.lower():
        return value * 1000
    elif "m" in s.lower():
        return value
    return None


def fetch_participants_page() -> BeautifulSoup:
    r = requests.get(TM_WC_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def parse_table(soup: BeautifulSoup, wc48: list[str]) -> pd.DataFrame:
    rows = soup.select("table.items tbody tr")
    records = []

    for row in rows:
        name_tag = row.select_one("td.links.no-border-links.hauptlink a")
        value_cells = row.select("td.rechts")
        squad_size_td = row.select("td.zentriert")

        if not name_tag or not value_cells:
            continue

        team_name = name_tag.get_text(strip=True)
        iso = TM_NAME_TO_ISO.get(team_name)
        if not iso or iso not in wc48:
            continue

        total_val = parse_tm_value_to_millions(value_cells[0].get_text(strip=True))
        avg_val = (
            parse_tm_value_to_millions(value_cells[1].get_text(strip=True))
            if len(value_cells) > 1
            else None
        )

        squad_size = None
        avg_age = None
        if len(squad_size_td) >= 2:
            try:
                squad_size = int(squad_size_td[0].get_text(strip=True))
            except ValueError:
                pass
            try:
                avg_age = float(squad_size_td[1].get_text(strip=True).replace(",", "."))
            except ValueError:
                pass

        records.append(
            {
                "iso_code": iso,
                "tm_team_name": team_name,
                "squad_value_m_eur": total_val,
                "squad_avg_value_m_eur": avg_val,
                "squad_size": squad_size,
                "squad_avg_age": avg_age,
            }
        )

    df = pd.DataFrame(records)
    df = df.sort_values("squad_value_m_eur", ascending=False).reset_index(drop=True)
    df["squad_value_rank"] = df.index + 1
    df["log_squad_value"] = df["squad_value_m_eur"].apply(
        lambda x: __import__("math").log1p(x) if x and x > 0 else None
    )
    return df


def main():
    print("=== 07_transfermarkt.py ===")
    wc48 = pd.read_csv(REFERENCE_CSV)["iso_code"].tolist()

    print(f"Fetching {TM_WC_URL} ...")
    soup = fetch_participants_page()

    print("Parsing squad values ...")
    df = parse_table(soup, wc48)
    print(f"  Teams scraped: {len(df)}/48")

    missing = [iso for iso in wc48 if iso not in df["iso_code"].values]
    if missing:
        print(f"  WARNING: missing teams: {missing}")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved → {OUTPUT_CSV.relative_to(ROOT)}")

    print("\nTop 10 by squad value:")
    print(
        df.head(10)[
            ["iso_code", "squad_value_m_eur", "squad_avg_value_m_eur", "squad_avg_age"]
        ].to_string(index=False)
    )
    print("\nBottom 10 by squad value:")
    print(
        df.tail(10)[
            ["iso_code", "squad_value_m_eur", "squad_avg_value_m_eur", "squad_avg_age"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()

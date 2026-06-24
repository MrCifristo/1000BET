"""
Fase 3 — Script 04: Elo Ratings
Fuente: eloratings.net/World.tsv

Descarga los ratings Elo actuales de todas las selecciones nacionales
y filtra a las 48 clasificadas al Mundial 2026.
Salida: data/features/elo_ratings.csv
"""

import io
import time
from pathlib import Path

import pandas as pd
import requests

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CSV = ROOT / "data/raw/reference/team_codes_mapping.csv"
OUTPUT_CSV = ROOT / "data/features/elo_ratings.csv"

# ── Mapping eloratings.net 2-letter → ISO 3166-1 alpha-3 ──────────────────────
# Standard ISO alpha-2 to alpha-3 covers most; non-standard overrides listed here.
ELO_CODE_TO_ISO = {
    # Non-standard codes used by eloratings.net
    "EN": "ENG",  # England (no separate ISO alpha-2)
    "SQ": "SCO",  # Scotland (SC = Seychelles in ISO)
    "WA": "WAL",  # Wales (not in our 48, but mapped for completeness)
    "EI": "IRL",  # Republic of Ireland
    "NI": "NIR",  # Northern Ireland
    # Standard alpha-2 → alpha-3 for all 48 WC 2026 teams
    "AR": "ARG",
    "AU": "AUS",
    "AT": "AUT",
    "BE": "BEL",
    "BA": "BIH",
    "BR": "BRA",
    "CA": "CAN",
    "CH": "CHE",
    "CI": "CIV",
    "CD": "COD",
    "CO": "COL",
    "CV": "CPV",
    "CW": "CUW",
    "CZ": "CZE",
    "DE": "DEU",
    "DZ": "DZA",
    "EC": "ECU",
    "EG": "EGY",
    "ES": "ESP",
    "FR": "FRA",
    "GH": "GHA",
    "HR": "HRV",
    "HT": "HTI",
    "IR": "IRN",
    "IQ": "IRQ",
    "JO": "JOR",
    "JP": "JPN",
    "KR": "KOR",
    "MA": "MAR",
    "MX": "MEX",
    "NL": "NLD",
    "NO": "NOR",
    "NZ": "NZL",
    "PA": "PAN",
    "PT": "PRT",
    "PY": "PRY",
    "QA": "QAT",
    "SA": "SAU",
    "SN": "SEN",
    "SE": "SWE",
    "TN": "TUN",
    "TR": "TUR",
    "UY": "URY",
    "US": "USA",
    "UZ": "UZB",
    "ZA": "ZAF",
}

TSV_URL = "https://www.eloratings.net/World.tsv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; wc2026-predictor/1.0)"}

# Column indices in the TSV (no header row)
COL_RANK = 0
COL_CODE = 2
COL_ELO = 3
COL_PEAK_ELO = 5


def fetch_tsv(url: str, retries: int = 3) -> str:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            if attempt == retries:
                raise
            print(f"  Retry {attempt}/{retries} after error: {e}")
            time.sleep(2 * attempt)


def parse_elo_tsv(raw: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(raw), sep="\t", header=None, dtype=str)
    df = df.rename(columns={
        COL_RANK: "elo_rank",
        COL_CODE: "elo_code",
        COL_ELO: "elo_rating",
        COL_PEAK_ELO: "elo_peak",
    })
    df = df[["elo_rank", "elo_code", "elo_rating", "elo_peak"]].copy()
    df["elo_rank"] = pd.to_numeric(df["elo_rank"], errors="coerce")
    df["elo_rating"] = pd.to_numeric(df["elo_rating"], errors="coerce")
    df["elo_peak"] = pd.to_numeric(df["elo_peak"], errors="coerce")
    return df.dropna(subset=["elo_rank", "elo_rating"])


def build_output(elo_df: pd.DataFrame, reference_csv: Path) -> pd.DataFrame:
    wc48 = pd.read_csv(reference_csv)["iso_code"].tolist()

    elo_df["iso_code"] = elo_df["elo_code"].map(ELO_CODE_TO_ISO)

    # Teams we expect but couldn't map
    mapped = elo_df[elo_df["iso_code"].notna()]
    found_isos = set(mapped["iso_code"])
    missing = [iso for iso in wc48 if iso not in found_isos]
    if missing:
        print(f"  WARNING: no Elo found for: {missing}")

    result = mapped[mapped["iso_code"].isin(wc48)].copy()
    result = result.sort_values("elo_rank").reset_index(drop=True)
    result["elo_rating"] = result["elo_rating"].astype(int)
    result["elo_peak"] = result["elo_peak"].astype(int)
    return result[["iso_code", "elo_rank", "elo_rating", "elo_peak"]]


def main():
    print("=== 04_elo_ratings.py ===")
    print(f"Fetching {TSV_URL} ...")
    raw = fetch_tsv(TSV_URL)

    print("Parsing TSV ...")
    elo_df = parse_elo_tsv(raw)
    print(f"  Total teams in dataset: {len(elo_df)}")

    print("Filtering to WC 2026 48 teams ...")
    result = build_output(elo_df, REFERENCE_CSV)
    print(f"  Matched: {len(result)}/48 teams")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved → {OUTPUT_CSV.relative_to(ROOT)}")

    print("\nTop 10 by Elo:")
    print(result.head(10).to_string(index=False))
    print("\nBottom 5 by Elo:")
    print(result.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()

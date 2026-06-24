"""
02_build_reference_data.py

Genera los CSVs de datos de referencia curados manualmente, usados por scripts posteriores:

  data/raw/reference/
    team_codes_mapping.csv      48 selecciones Mundial 2026: openfootball name <-> ISO code + capital + idiomas
    host_countries.csv          3 anfitriones (USA/CAN/MEX): centro representativo + idiomas + vecinos
    diaspora_estimates.csv      144 filas (48 teams x 3 hosts): estimaciones aproximadas
    historical_team_aliases.csv aliasing de selecciones históricas (CSK -> CZE, etc.)

NOTA SOBRE CÓDIGOS:
  Fjelstul usa ISO 3166-1 alpha-3, NO los códigos FIFA. Diferencias relevantes:
    Germany     DEU (FIFA: GER)
    Croatia     HRV (FIFA: CRO)
    Netherlands NLD (FIFA: NED)
    Portugal    PRT (FIFA: POR)
    Saudi Arabia SAU (FIFA: KSA)
    South Africa ZAF (FIFA: RSA)
    Switzerland  CHE (FIFA: SUI)
    Uruguay      URY (FIFA: URU)
  Usamos ISO como código canónico (es lo que vive en Fjelstul).

NOTA SOBRE DIASPORA:
  Las estimaciones provienen de:
    USA: US Census Bureau ACS 2020 (ancestry / foreign-born)
    CAN: Statistics Canada 2021 Census (ethnic origin)
    MEX: INEGI 2020 (foreign-born) + estimaciones de Wikipedia para diásporas chicas
  Son aproximaciones a orden de magnitud, NO cifras precisas. Cuando un país no tiene
  diáspora medible se asume 0. La idea es que el feature sea log-transformado en el modelo,
  así que lo que importa es la escala, no el dígito exacto.
"""
from __future__ import annotations

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = PROJECT_ROOT / "data" / "raw" / "reference"
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1) Team codes & geography — las 48 selecciones clasificadas a 2026
# ---------------------------------------------------------------------------
#
# Columnas:
#   openfootball_name : nombre exacto que aparece en openfootball worldcup.json (2026)
#   iso_code          : ISO 3166-1 alpha-3 (= código en Fjelstul matches/teams)
#   country_full      : nombre formal del país
#   capital           : capital usada para distancia (no necesariamente la legal — ej.
#                       Países Bajos usa Ámsterdam y no La Haya; SA usa Pretoria)
#   capital_lat, capital_lon
#   official_languages: separadas por ";"
#
TEAMS_2026 = [
    # name                       iso   country_full              capital          lat        lon       languages
    ("Algeria",                  "DZA", "Algeria",                "Algiers",      36.7538,    3.0588,  "Arabic"),
    ("Argentina",                "ARG", "Argentina",              "Buenos Aires", -34.6037, -58.3816,  "Spanish"),
    ("Australia",                "AUS", "Australia",              "Canberra",     -35.2809, 149.1300,  "English"),
    ("Austria",                  "AUT", "Austria",                "Vienna",        48.2082,  16.3738,  "German"),
    ("Belgium",                  "BEL", "Belgium",                "Brussels",      50.8503,   4.3517,  "Dutch;French;German"),
    ("Bosnia & Herzegovina",     "BIH", "Bosnia and Herzegovina", "Sarajevo",      43.8563,  18.4131,  "Bosnian;Croatian;Serbian"),
    ("Brazil",                   "BRA", "Brazil",                 "Brasilia",     -15.8267, -47.9218,  "Portuguese"),
    ("Canada",                   "CAN", "Canada",                 "Ottawa",        45.4215, -75.6972,  "English;French"),
    ("Cape Verde",               "CPV", "Cape Verde",             "Praia",         14.9330, -23.5133,  "Portuguese"),
    ("Colombia",                 "COL", "Colombia",               "Bogota",         4.7110, -74.0721,  "Spanish"),
    ("Croatia",                  "HRV", "Croatia",                "Zagreb",        45.8150,  15.9819,  "Croatian"),
    ("Curaçao",                  "CUW", "Curacao",                "Willemstad",    12.1224, -68.8825,  "Dutch;Papiamentu"),
    ("Czech Republic",           "CZE", "Czechia",                "Prague",        50.0755,  14.4378,  "Czech"),
    ("DR Congo",                 "COD", "DR Congo",               "Kinshasa",      -4.4419,  15.2663,  "French"),
    ("Ecuador",                  "ECU", "Ecuador",                "Quito",         -0.1807, -78.4678,  "Spanish"),
    ("Egypt",                    "EGY", "Egypt",                  "Cairo",         30.0444,  31.2357,  "Arabic"),
    ("England",                  "ENG", "England",                "London",        51.5074,  -0.1278,  "English"),
    ("France",                   "FRA", "France",                 "Paris",         48.8566,   2.3522,  "French"),
    ("Germany",                  "DEU", "Germany",                "Berlin",        52.5200,  13.4050,  "German"),
    ("Ghana",                    "GHA", "Ghana",                  "Accra",          5.6037,  -0.1870,  "English"),
    ("Haiti",                    "HTI", "Haiti",                  "Port-au-Prince",18.5944, -72.3074,  "French;Haitian Creole"),
    ("Iran",                     "IRN", "Iran",                   "Tehran",        35.6892,  51.3890,  "Persian"),
    ("Iraq",                     "IRQ", "Iraq",                   "Baghdad",       33.3152,  44.3661,  "Arabic"),
    ("Ivory Coast",              "CIV", "Cote d'Ivoire",          "Yamoussoukro",   6.8276,  -5.2893,  "French"),
    ("Japan",                    "JPN", "Japan",                  "Tokyo",         35.6762, 139.6503,  "Japanese"),
    ("Jordan",                   "JOR", "Jordan",                 "Amman",         31.9454,  35.9284,  "Arabic"),
    ("Mexico",                   "MEX", "Mexico",                 "Mexico City",   19.4326, -99.1332,  "Spanish"),
    ("Morocco",                  "MAR", "Morocco",                "Rabat",         34.0209,  -6.8416,  "Arabic;Berber"),
    ("Netherlands",              "NLD", "Netherlands",            "Amsterdam",     52.3676,   4.9041,  "Dutch"),
    ("New Zealand",              "NZL", "New Zealand",            "Wellington",   -41.2865, 174.7762,  "English"),
    ("Norway",                   "NOR", "Norway",                 "Oslo",          59.9139,  10.7522,  "Norwegian"),
    ("Panama",                   "PAN", "Panama",                 "Panama City",    8.9824, -79.5199,  "Spanish"),
    ("Paraguay",                 "PRY", "Paraguay",               "Asuncion",     -25.2637, -57.5759,  "Spanish"),
    ("Portugal",                 "PRT", "Portugal",               "Lisbon",        38.7223,  -9.1393,  "Portuguese"),
    ("Qatar",                    "QAT", "Qatar",                  "Doha",          25.2854,  51.5310,  "Arabic"),
    ("Saudi Arabia",             "SAU", "Saudi Arabia",           "Riyadh",        24.7136,  46.6753,  "Arabic"),
    ("Scotland",                 "SCO", "Scotland",               "Edinburgh",     55.9533,  -3.1883,  "English"),
    ("Senegal",                  "SEN", "Senegal",                "Dakar",         14.7167, -17.4677,  "French"),
    ("South Africa",             "ZAF", "South Africa",           "Pretoria",     -25.7461,  28.1881,  "English"),
    ("South Korea",              "KOR", "South Korea",            "Seoul",         37.5665, 126.9780,  "Korean"),
    ("Spain",                    "ESP", "Spain",                  "Madrid",        40.4168,  -3.7038,  "Spanish"),
    ("Sweden",                   "SWE", "Sweden",                 "Stockholm",     59.3293,  18.0686,  "Swedish"),
    ("Switzerland",              "CHE", "Switzerland",            "Bern",          46.9480,   7.4474,  "German;French;Italian"),
    ("Tunisia",                  "TUN", "Tunisia",                "Tunis",         36.8065,  10.1815,  "Arabic"),
    ("Turkey",                   "TUR", "Turkey",                 "Ankara",        39.9334,  32.8597,  "Turkish"),
    ("USA",                      "USA", "United States",          "Washington",    38.9072, -77.0369,  "English"),
    ("Uruguay",                  "URY", "Uruguay",                "Montevideo",   -34.9011, -56.1645,  "Spanish"),
    ("Uzbekistan",               "UZB", "Uzbekistan",             "Tashkent",      41.2995,  69.2401,  "Uzbek"),
]
TEAMS_HEADER = [
    "openfootball_name", "iso_code", "country_full",
    "capital", "capital_lat", "capital_lon", "official_languages",
]

# ---------------------------------------------------------------------------
# 2) Host countries — Mundial 2026 (USA / CAN / MEX)
# ---------------------------------------------------------------------------
#
# El "centro representativo" se usa como punto de referencia para distancia a un país
# anfitrión completo. Para USA elegimos NYC como anchor del este (donde está la final);
# para CAN, Toronto; para MEX, Ciudad de México. En Phase 6 podemos refinar a venue específico.
#
HOST_COUNTRIES = [
    # iso   name              center city     lat        lon       languages              neighbors_iso
    ("USA", "United States",   "New York",     40.7128,  -74.0060, "English",              "CAN;MEX"),
    ("CAN", "Canada",          "Toronto",      43.6532,  -79.3832, "English;French",       "USA"),
    ("MEX", "Mexico",          "Mexico City",  19.4326,  -99.1332, "Spanish",              "USA"),
]
HOSTS_HEADER = ["iso_code", "name", "center_city", "center_lat", "center_lon",
                "primary_languages", "neighbors_iso"]

# ---------------------------------------------------------------------------
# 3) Diaspora estimates (rough!) por (team x host_country)
# ---------------------------------------------------------------------------
#
# Estimación a orden de magnitud. Fuentes principales:
#   US: US Census Bureau ACS 2020, "Selected Population Profile" (ancestry + foreign-born).
#       Para diáporas grandes (German-American, English-American, etc.) reportamos
#       "claimed ancestry" — sobreestima vs foreign-born reciente.
#   CA: Statistics Canada 2021 Census, "Ethnic or cultural origin".
#   MX: INEGI 2020 (foreign-born) + Wikipedia para minorías.
#
# Convención: 0 = sin diáspora medible. Nunca usar como cifra exacta — el modelo aplica log1p.
#
# Formato: { iso_code: (diaspora_usa, diaspora_can, diaspora_mex) }
#
DIASPORA = {
    "DZA": (50_000,    75_000,     1_000),
    "ARG": (300_000,   40_000,    60_000),
    "AUS": (200_000,   26_000,     5_000),
    "AUT": (700_000,  200_000,     3_000),
    "BEL": (400_000,  180_000,     3_000),
    "BIH": (300_000,   25_000,       500),
    "BRA": (500_000,   70_000,    15_000),
    "CAN": (1_100_000, 0,          5_000),  # CAN vs USA: large cross-border
    "CPV": (100_000,    5_000,       100),
    "COL": (1_500_000, 75_000,    35_000),
    "HRV": (400_000,  130_000,     5_000),
    "CUW": (10_000,    5_000,       200),
    "CZE": (1_700_000,100_000,     1_500),
    "COD": (100_000,   25_000,       500),
    "ECU": (700_000,   20_000,     5_000),
    "EGY": (400_000,   73_000,     1_500),
    "ENG": (25_000_000, 5_300_000, 12_000),
    "FRA": (8_000_000, 4_700_000,  35_000),
    "DEU": (41_000_000, 3_300_000, 25_000),
    "GHA": (200_000,   30_000,       500),
    "HTI": (1_100_000,165_000,     5_000),
    "IRN": (1_000_000,210_000,     2_000),
    "IRQ": (500_000,   70_000,     1_500),
    "CIV": (100_000,    7_000,       500),
    "JPN": (1_500_000,110_000,    12_000),
    "JOR": (100_000,   15_000,     1_500),
    "MEX": (37_000_000, 130_000,        0),  # MEX vs MEX = N/A
    "MAR": (100_000,   90_000,     2_000),
    "NLD": (4_000_000, 1_000_000,  6_000),
    "NZL": (50_000,    12_000,     1_000),
    "NOR": (4_000_000, 460_000,    1_500),
    "PAN": (200_000,    5_000,     5_000),
    "PRY": (30_000,     5_000,     2_000),
    "PRT": (1_400_000, 480_000,    5_000),
    "QAT": (50_000,     5_000,       200),
    "SAU": (100_000,   10_000,       500),
    "SCO": (6_000_000, 4_700_000,  3_000),
    "SEN": (50_000,     8_000,       500),
    "ZAF": (130_000,   50_000,     1_500),
    "KOR": (1_900_000, 220_000,   12_000),
    "ESP": (900_000,   80_000,   350_000),  # Spain in MEX: history
    "SWE": (4_000_000, 350_000,    2_500),
    "CHE": (1_000_000, 150_000,    7_500),
    "TUN": (50_000,    30_000,       500),
    "TUR": (500_000,   60_000,     2_000),
    "USA": (0,          0,       800_000),  # USA vs USA = N/A; large in MEX
    "URY": (50_000,     5_000,     4_000),
    "UZB": (50_000,    10_000,       100),
}

# ---------------------------------------------------------------------------
# 4) Aliases históricos — para acumular experiencia bajo el código moderno
# ---------------------------------------------------------------------------
#
# Solo aliasamos casos no-ambiguos donde la herencia futbolística es directa.
# Casos ambiguos (Yugoslavia -> Croacia/Serbia/Bosnia; Soviet Union -> Russia; etc.)
# NO se aliasan; cuentan como histórico aparte. West/East Germany: Fjelstul ya las usa
# bajo DEU, no requiere alias adicional.
#
HISTORICAL_ALIASES = [
    # fjelstul_code, modern_iso_code, note
    ("CSK", "CZE", "Czechoslovakia -> Czech Republic (heredero futbolístico principal)"),
    ("DDR", "DEU", "East Germany -> Germany (post-reunificación)"),
]
ALIASES_HEADER = ["historical_iso", "modern_iso", "note"]


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  -> {path.relative_to(PROJECT_ROOT)}  ({len(rows)} filas)")


def build_diaspora_rows() -> list[tuple]:
    rows = []
    host_order = ("USA", "CAN", "MEX")
    for iso, counts in DIASPORA.items():
        for host, count in zip(host_order, counts):
            rows.append((iso, host, count))
    return rows


def main() -> None:
    print("Construyendo datos de referencia...")
    write_csv(REFERENCE_DIR / "team_codes_mapping.csv", TEAMS_HEADER, TEAMS_2026)
    write_csv(REFERENCE_DIR / "host_countries.csv", HOSTS_HEADER, HOST_COUNTRIES)
    write_csv(
        REFERENCE_DIR / "diaspora_estimates.csv",
        ["iso_code", "host_iso", "diaspora_estimate"],
        build_diaspora_rows(),
    )
    write_csv(REFERENCE_DIR / "historical_team_aliases.csv", ALIASES_HEADER, HISTORICAL_ALIASES)
    print("Listo.")


if __name__ == "__main__":
    main()

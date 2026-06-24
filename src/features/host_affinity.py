"""
host_affinity.py — "Local Influence" features.

Para cada (selección clasificada al Mundial 2026 × país anfitrión {USA, CAN, MEX}),
calcula features que pueden modelar el "advantage de cercanía" en un Mundial neutral:

  - distance_km        Haversine capital del equipo -> centro representativo del anfitrión.
                       Proxy de fatiga de viaje / huso horario.
  - diaspora_estimate  Estimación cruda del tamaño de la diáspora del equipo en el país.
                       Curado a mano en data/raw/reference/diaspora_estimates.csv.
                       USAR siempre log1p(diaspora_estimate) en el modelo — escala muy variable.
  - shared_language    Bool: 1 si al menos un idioma oficial coincide con un idioma primario del anfitrión.
  - shares_border      Bool: 1 si el país comparte frontera terrestre con el anfitrión
                       (solo USA-MEX, USA-CAN aplican).

NOTA SOBRE INTERPRETACIÓN:
  Estas features se exponen "crudas" — no se combinan en un score compuesto a priori.
  El modelo (Poisson o ensamble) aprende los pesos óptimos vs evidencia histórica.
  Esto es más honesto que inventar una fórmula tipo `affinity = 0.3*dist + 0.5*diaspora`.

LIMITACIONES CONOCIDAS:
  - Diáspora país-nivel (no city-nivel). Diáspora mexicana se concentra en CA/TX, no en NYC.
    Refinable en Phase 6 si vale la pena.
  - Idioma oficial != idioma mayoritario. España y Argentina ambos hablan castellano, pero el
    castellano mexicano y rioplatense tienen diferencias culturales.
  - "Shares border" es muy ruidoso para este conjunto — solo MEX-USA y CAN-USA.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE = PROJECT_ROOT / "data" / "raw" / "reference"
FEATURES_DIR = PROJECT_ROOT / "data" / "features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia gran-círculo en km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def overlap(a: str, b: str) -> bool:
    """True si dos strings separados por ';' comparten al menos un token (case-insensitive)."""
    tokens_a = {t.strip().lower() for t in a.split(";")}
    tokens_b = {t.strip().lower() for t in b.split(";")}
    return bool(tokens_a & tokens_b)


def main() -> None:
    teams = pd.read_csv(REFERENCE / "team_codes_mapping.csv")
    hosts = pd.read_csv(REFERENCE / "host_countries.csv")
    diaspora = pd.read_csv(REFERENCE / "diaspora_estimates.csv")

    rows = []
    for _, t in teams.iterrows():
        for _, h in hosts.iterrows():
            # Distance
            dist = haversine_km(
                t["capital_lat"], t["capital_lon"],
                h["center_lat"], h["center_lon"],
            )
            # Diaspora
            d = diaspora[(diaspora["iso_code"] == t["iso_code"]) &
                         (diaspora["host_iso"] == h["iso_code"])]
            diaspora_count = int(d["diaspora_estimate"].iloc[0]) if len(d) else 0

            # Language overlap
            shared_lang = overlap(t["official_languages"], h["primary_languages"])

            # Border (solo USA<->MEX, USA<->CAN históricamente)
            neighbors = set(h["neighbors_iso"].split(";")) if isinstance(h["neighbors_iso"], str) else set()
            shares_border = t["iso_code"] in neighbors

            # Self-host edge case (USA vs USA): forzamos distance=0 y un flag
            is_self_host = (t["iso_code"] == h["iso_code"])
            if is_self_host:
                dist = 0.0
                shares_border = False  # país no es vecino de sí mismo

            rows.append({
                "iso_code": t["iso_code"],
                "host_iso": h["iso_code"],
                "is_self_host": int(is_self_host),
                "distance_km": round(dist, 1),
                "diaspora_estimate": diaspora_count,
                "log_diaspora": math.log1p(diaspora_count),
                "shared_language": int(shared_lang),
                "shares_border": int(shares_border),
            })

    df = pd.DataFrame(rows)
    out = FEATURES_DIR / "team_host_affinity.csv"
    df.to_csv(out, index=False)

    print(f">>> Escrito {out.relative_to(PROJECT_ROOT)} ({len(df)} filas)")
    print()
    print("Top 15 (selección × anfitrión) por log_diaspora (afinidad histórica fuerte):")
    print(df.sort_values("log_diaspora", ascending=False).head(15).to_string(index=False))
    print()
    print("Top 10 menor distancia (selección × anfitrión, excluyendo self):")
    nonself = df[df["is_self_host"] == 0]
    print(nonself.sort_values("distance_km").head(10)[
        ["iso_code", "host_iso", "distance_km", "shares_border", "shared_language"]
    ].to_string(index=False))
    print()
    print("Selecciones con shared_language con USA (host principal de 2026):")
    eng_in_usa = df[(df["host_iso"] == "USA") & (df["shared_language"] == 1)]
    print(", ".join(sorted(eng_in_usa["iso_code"])))


if __name__ == "__main__":
    main()

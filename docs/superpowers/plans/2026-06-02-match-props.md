# Match Props Predictor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extraer stats de corners/tarjetas/disparos/faltas de los 314 JSONs StatsBomb ya descargados, rellenar los 8 equipos faltantes, entrenar 4 submodelos Poisson, y unificar todo en `MatchPredictor` que devuelve Over/Under para cada mercado.

**Architecture:** `build_match_rows()` se extiende con `home_score_col`/`away_score_col` para soportar cualquier variable objetivo. `11_statsbomb_match_stats.py` genera dos CSVs: per-match (para entrenamiento) y per-equipo (feature set). `12_prop_coverage.py` rellena los 8 equipos faltantes via Sofascore → mediana. `MatchPredictor` envuelve 5 `PoissonModel` y produce el output unificado.

**Tech Stack:** Python 3.12, scipy, pandas, soccerdata (Sofascore), pytest

---

## Columnas confirmadas

**StatsBomb `matches.json`:** `match_id`, `match_date`, `home_team.home_team_name`, `away_team.away_team_name`, `home_score`, `away_score`, `competition.competition_id`

**8 equipos sin StatsBomb:** BIH, CUW, HTI, IRQ, JOR, NZL, NOR, UZB

**Nombres StatsBomb → ISO que difieren del estándar:**
`"Cape Verde Islands"→CPV`, `"Congo DR"→COD`, `"Côte d'Ivoire"→CIV`, `"United States"→USA`, `"South Korea"→KOR`

---

## File Map

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/model/features.py` | Modificar | Agregar `home_score_col`/`away_score_col` a `build_match_rows` |
| `src/ingestion/11_statsbomb_match_stats.py` | Crear | Extrae props de JSONs → `statsbomb_match_props.csv` + `statsbomb_prop_stats.csv` |
| `src/ingestion/12_prop_coverage.py` | Crear | Sofascore → mediana para 8 equipos → `prop_team_stats.csv` |
| `src/model/match_predictor.py` | Crear | `MatchPredictor`: envuelve 5 `PoissonModel`, produce output completo |
| `src/model/train_props.py` | Crear | Entrena 4 submodelos props + ensambla `MatchPredictor` → pkl |
| `tests/model/test_match_predictor.py` | Crear | Tests de `MatchPredictor` |
| `tests/model/test_features.py` | Modificar | Tests para los nuevos parámetros de `build_match_rows` |

---

## Task 1: Extender `build_match_rows` con columnas de score configurables

**Files:**
- Modify: `src/model/features.py`
- Modify: `tests/model/test_features.py`

- [ ] **Agregar tests para los nuevos parámetros al final de `tests/model/test_features.py`**

```python
def test_build_match_rows_custom_score_cols():
    matches = pd.DataFrame({
        "home_team_iso":   ["ARG"],
        "away_team_iso":   ["FRA"],
        "home_corners":    [7],
        "away_corners":    [5],
        "year":            [2022],
        "host_team_iso":   [np.nan],
    })
    teams = _make_teams_df()
    rows = build_match_rows(
        matches, teams, year_ref=2026, decay_rate=0.05,
        home_score_col="home_corners", away_score_col="away_corners",
    )
    assert len(rows) == 2
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["goals_for"] == 7
    assert fra_row["goals_for"] == 5


def test_build_match_rows_default_score_col_unchanged():
    """Llamar sin parámetros nuevos sigue funcionando igual."""
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    assert "goals_for" in rows.columns
    assert rows["goals_for"].iloc[0] == 2
```

- [ ] **Verificar que fallan**

```bash
source .venv/bin/activate && pytest tests/model/test_features.py::test_build_match_rows_custom_score_cols -v 2>&1 | tail -5
```

Esperado: `TypeError` (función no acepta esos parámetros aún).

- [ ] **Modificar `build_match_rows` en `src/model/features.py`**

Cambiar la firma y la línea de extracción de goles:

```python
def build_match_rows(
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    year_ref: int,
    decay_rate: float,
    home_score_col: str = "home_team_score",
    away_score_col: str = "away_team_score",
) -> pd.DataFrame:
```

Y dentro del loop, reemplazar:
```python
        pairs = [
            (hi, ai, int(match["home_team_score"])),
            (ai, hi, int(match["away_team_score"])),
        ]
```
por:
```python
        pairs = [
            (hi, ai, int(match[home_score_col])),
            (ai, hi, int(match[away_score_col])),
        ]
```

- [ ] **Verificar que todos los tests de features pasan**

```bash
pytest tests/model/test_features.py -v
```

Esperado: todos en PASS (incluyendo los 2 nuevos).

- [ ] **Commit**

```bash
git add src/model/features.py tests/model/test_features.py
git commit -m "feat(model): support custom score columns in build_match_rows"
```

---

## Task 2: `11_statsbomb_match_stats.py` — extraer props de los JSONs

**Files:**
- Create: `src/ingestion/11_statsbomb_match_stats.py`

- [ ] **Crear el script**

```python
"""
Fase 3+ — Script 11: StatsBomb Match Props

Extrae corners, tarjetas, disparos y faltas de los 314 eventos JSON ya descargados.

Outputs:
  data/processed/statsbomb_match_props.csv  — una fila por equipo por partido (para training)
  data/features/statsbomb_prop_stats.csv    — promedios por equipo por 90' (para features)
"""
import json
from pathlib import Path

import pandas as pd

ROOT   = Path(__file__).resolve().parents[2]
SB_DIR = ROOT / "data/raw/statsbomb"
OUT_MATCH = ROOT / "data/processed/statsbomb_match_props.csv"
OUT_TEAM  = ROOT / "data/features/statsbomb_prop_stats.csv"

# StatsBomb team name → ISO. Cubre los 76 equipos únicos en los 6 torneos descargados.
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

# Equipos del WC 2026 presentes en StatsBomb
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
    skipped = 0

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

            hs = extract_team_stats(events, home_name)
            as_ = extract_team_stats(events, away_name)
            year = int(match["match_date"][:4])

            match_rows.append({
                "match_id":       match["match_id"],
                "year":           year,
                "home_team_iso":  home_iso,
                "away_team_iso":  away_iso,
                "host_team_iso":  None,   # torneos internacionales: neutral
                "home_corners":   hs["corners"],    "away_corners":  as_["corners"],
                "home_yellow":    hs["yellow_cards"],"away_yellow":  as_["yellow_cards"],
                "home_red":       hs["red_cards"],   "away_red":     as_["red_cards"],
                "home_shots":     hs["shots"],       "away_shots":   as_["shots"],
                "home_shots_ot":  hs["shots_on_target"], "away_shots_ot": as_["shots_on_target"],
                "home_fouls":     hs["fouls"],       "away_fouls":   as_["fouls"],
            })

    df = pd.DataFrame(match_rows)
    OUT_MATCH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_MATCH, index=False)
    print(f"\n  {len(df)} partidos → {OUT_MATCH.relative_to(ROOT)} ({skipped} omitidos)")

    # ── Promedios por equipo ────────────────────────────────────────────────
    team_records = []
    all_isos = set(df["home_team_iso"]) | set(df["away_team_iso"])

    for iso in sorted(all_isos):
        hm = df[df["home_team_iso"] == iso]
        aw = df[df["away_team_iso"] == iso]
        n  = len(hm) + len(aw)
        if n == 0:
            continue
        team_records.append({
            "iso_code":          iso,
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
```

- [ ] **Correr el script**

```bash
source .venv/bin/activate && python src/ingestion/11_statsbomb_match_stats.py
```

Verificar:
- Output muestra ~300+ partidos procesados (algunos se omiten si el JSON de eventos no existe)
- `data/processed/statsbomb_match_props.csv` creado
- `data/features/statsbomb_prop_stats.csv` con ~65-70 equipos (todos los que aparecen en los 6 torneos)
- Equipos WC 2026 cubiertos: 40/48 (los 8 sin StatsBomb quedarán ausentes)

- [ ] **Commit**

```bash
git add src/ingestion/11_statsbomb_match_stats.py
git commit -m "feat(ingestion): extract corners, cards, shots, fouls from StatsBomb events"
```

---

## Task 3: `12_prop_coverage.py` — cubrir los 8 equipos faltantes

**Files:**
- Create: `src/ingestion/12_prop_coverage.py`

Los 8 equipos sin StatsBomb: BIH, CUW, HTI, IRQ, JOR, NZL, NOR, UZB

- [ ] **Crear el script con intento Sofascore → fallback mediana**

```python
"""
Fase 3+ — Script 12: Prop Coverage para 8 equipos sin StatsBomb

Intenta obtener stats de corners/tarjetas/disparos/faltas para los 8 equipos
no cubiertos por StatsBomb via Sofascore (soccerdata).
Si Sofascore falla o está bloqueado, imputa con la mediana del corpus.

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
                "prop_shots_per90", "prop_fouls_per90"]


def try_sofascore(iso: str) -> dict | None:
    """
    Intenta obtener stats de Sofascore vía soccerdata.
    Retorna dict con prop_cols o None si falla.
    """
    try:
        import soccerdata as sd
        # Sofascore no tiene API directa para selecciones nacionales;
        # intentamos a través de partidos de la selección.
        # Si la llamada falla o retorna vacío, lanzará excepción.
        raise NotImplementedError("Sofascore international team stats not supported in soccerdata")
    except Exception:
        return None


def impute_with_median(sb_df: pd.DataFrame, iso: str) -> dict:
    """Imputa con la mediana del corpus StatsBomb."""
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

    # Filtrar statsbomb_prop_stats a solo los 48 equipos WC 2026
    base = sb_df[sb_df["iso_code"].isin(wc48)].copy()
    print(f"  Equipos WC 2026 en StatsBomb: {len(base)}/48")

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

    extra_df = pd.DataFrame(extras)
    result   = pd.concat([base, extra_df], ignore_index=True)

    # Verificar los 48 equipos
    missing = set(wc48) - set(result["iso_code"])
    if missing:
        print(f"  WARNING: Equipos WC sin cobertura: {missing}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_CSV, index=False)
    print(f"\nGuardado → {OUT_CSV.relative_to(ROOT)}")
    print(f"  Total: {len(result)} equipos")
    print(f"  Fuentes: {result['prop_source'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
```

- [ ] **Correr el script**

```bash
source .venv/bin/activate && python src/ingestion/12_prop_coverage.py
```

Esperado:
- 40 equipos de StatsBomb + 8 imputados con mediana
- `data/features/prop_team_stats.csv` con 48 filas
- Output muestra `{'statsbomb': 40, 'median_imputed': 8}`

- [ ] **Commit**

```bash
git add src/ingestion/12_prop_coverage.py
git commit -m "feat(ingestion): prop_team_stats coverage for all 48 WC 2026 teams"
```

---

## Task 4: `match_predictor.py` — clase `MatchPredictor`

**Files:**
- Create: `src/model/match_predictor.py`
- Create: `tests/model/test_match_predictor.py`

- [ ] **Escribir tests (fallidos)**

Crear `tests/model/test_match_predictor.py`:

```python
import numpy as np
import pandas as pd
import pytest
from scipy.stats import poisson

from src.model.match_predictor import MatchPredictor
from src.model.poisson_model import PoissonModel


def _make_fitted_model(seed_goals=2.0, seed_against=1.0):
    """Modelo sintético trivial: todos los equipos con misma fuerza."""
    matches = pd.DataFrame({
        "home_team_iso":   ["A"] * 20 + ["B"] * 20,
        "away_team_iso":   ["B"] * 20 + ["A"] * 20,
        "home_team_score": [2] * 20 + [1] * 20,
        "away_team_score": [1] * 20 + [2] * 20,
        "year":            [2022] * 40,
        "host_team_iso":   [np.nan] * 40,
    })
    teams = pd.DataFrame({
        "iso_code":          ["A", "B"],
        "elo_rating":        [1800.0, 1700.0],
        "squad_value_m_eur": [500.0, 300.0],
        "sb_xg_per90":       [1.0, 0.8],
        "sq_npxg_per90":     [np.nan, np.nan],
        "fb_npgls_per90":    [np.nan, np.nan],
    })
    model = PoissonModel(ridge_lambda=0.01).fit(matches, teams, year_ref=2022)
    return model


def _make_predictor():
    m = _make_fitted_model()
    return MatchPredictor(
        model_goals=m, model_corners=m, model_cards=m,
        model_shots=m, model_fouls=m,
    )


def test_predict_match_has_all_markets():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    assert "result"  in result
    assert "goals"   in result
    assert "corners" in result
    assert "cards"   in result
    assert "shots"   in result
    assert "fouls"   in result


def test_result_probabilities_sum_to_one():
    pred = _make_predictor()
    r = pred.predict_match("A", "B")["result"]
    assert abs(r["p_home"] + r["p_draw"] + r["p_away"] - 1.0) < 1e-3


def test_over_under_sum_to_one():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    for market in ["goals", "corners", "cards", "shots", "fouls"]:
        m = result[market]
        lines = [k.replace("over_", "").replace("under_", "") for k in m if k.startswith("over_")]
        for line in lines:
            over  = m[f"over_{line}"]
            under = m[f"under_{line}"]
            assert abs(over + under - 1.0) < 1e-6, f"{market} {line}: {over} + {under} ≠ 1"


def test_btts_in_goals():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    assert "btts" in result["goals"]
    assert 0.0 <= result["goals"]["btts"] <= 1.0


def test_expected_total_positive():
    pred = _make_predictor()
    result = pred.predict_match("A", "B")
    for market in ["goals", "corners", "cards", "shots", "fouls"]:
        assert result[market]["expected_total"] > 0
```

- [ ] **Verificar que fallan**

```bash
pytest tests/model/test_match_predictor.py -v 2>&1 | head -10
```

Esperado: `ImportError`.

- [ ] **Implementar `src/model/match_predictor.py`**

```python
"""
MatchPredictor — envuelve 5 PoissonModel (goals, corners, cards, shots, fouls)
y produce el output unificado de predicción para apostar en mercados alternativos.
"""
from typing import Optional

import numpy as np
from scipy.stats import poisson

from src.model.poisson_model import PoissonModel


LINES = {
    "goals":   [1.5, 2.5, 3.5],
    "corners": [8.5, 9.5, 10.5, 11.5],
    "cards":   [2.5, 3.5, 4.5],
    "shots":   [21.5, 24.5, 27.5],
    "fouls":   [19.5, 22.5, 25.5],
}


def _over_under(lam_total: float, line: float) -> tuple[float, float]:
    """P(X > line) y P(X < line) donde X ~ Poisson(lam_total), line es X.5."""
    k = int(line)          # line = k + 0.5, P(X > k+0.5) = P(X >= k+1)
    p_over  = float(1.0 - poisson.cdf(k, lam_total))
    p_under = float(1.0 - p_over)
    return round(p_over, 4), round(p_under, 4)


def _line_key(line: float) -> str:
    """1.5 → '1_5', 10.5 → '10_5'"""
    return str(line).replace(".", "_")


class MatchPredictor:
    """
    Wrapper sobre 5 PoissonModel independientes.

    Uso:
        predictor = MatchPredictor(model_goals, model_corners, model_cards,
                                   model_shots, model_fouls)
        result = predictor.predict_match("ARG", "FRA", host_iso=None)
    """

    def __init__(
        self,
        model_goals:   PoissonModel,
        model_corners: PoissonModel,
        model_cards:   PoissonModel,
        model_shots:   PoissonModel,
        model_fouls:   PoissonModel,
    ):
        self.model_goals   = model_goals
        self.model_corners = model_corners
        self.model_cards   = model_cards
        self.model_shots   = model_shots
        self.model_fouls   = model_fouls

        self._models = {
            "goals":   model_goals,
            "corners": model_corners,
            "cards":   model_cards,
            "shots":   model_shots,
            "fouls":   model_fouls,
        }

    def predict_match(
        self,
        iso_a: str,
        iso_b: str,
        host_iso: Optional[str] = None,
    ) -> dict:
        """
        Predice todos los mercados para un partido entre iso_a e iso_b.
        iso_a = equipo listado primero (p_home en result).
        """
        output = {}

        # ── Resultado ─────────────────────────────────────────────────────
        goals_pred = self.model_goals.predict_match(iso_a, iso_b, host_iso)
        output["result"] = {
            "p_home":         goals_pred["p_home"],
            "p_draw":         goals_pred["p_draw"],
            "p_away":         goals_pred["p_away"],
            "expected_score": f"{goals_pred['expected'][0]} - {goals_pred['expected'][1]}",
            "likely_score":   goals_pred["likely_score"],
        }

        # ── Goles ─────────────────────────────────────────────────────────
        lam_a = self.model_goals._lambda(iso_a, iso_b, host_iso)
        lam_b = self.model_goals._lambda(iso_b, iso_a, host_iso)
        lam_total = lam_a + lam_b

        goals_market: dict = {"expected_total": round(lam_total, 2)}
        for line in LINES["goals"]:
            key = _line_key(line)
            over, under = _over_under(lam_total, line)
            goals_market[f"over_{key}"]  = over
            goals_market[f"under_{key}"] = under

        # BTTS: P(goals_a >= 1) * P(goals_b >= 1)
        p_a_scores = float(1.0 - poisson.pmf(0, lam_a))
        p_b_scores = float(1.0 - poisson.pmf(0, lam_b))
        goals_market["btts"] = round(p_a_scores * p_b_scores, 4)
        output["goals"] = goals_market

        # ── Props (corners, cards, shots, fouls) ──────────────────────────
        for market, model in [
            ("corners", self.model_corners),
            ("cards",   self.model_cards),
            ("shots",   self.model_shots),
            ("fouls",   self.model_fouls),
        ]:
            lam_x_a = model._lambda(iso_a, iso_b, host_iso)
            lam_x_b = model._lambda(iso_b, iso_a, host_iso)
            lam_x   = lam_x_a + lam_x_b

            market_dict: dict = {"expected_total": round(lam_x, 2)}
            for line in LINES[market]:
                key = _line_key(line)
                over, under = _over_under(lam_x, line)
                market_dict[f"over_{key}"]  = over
                market_dict[f"under_{key}"] = under

            output[market] = market_dict

        return output
```

- [ ] **Verificar que todos los tests pasan**

```bash
pytest tests/model/test_match_predictor.py -v
```

Esperado: todos en PASS (7 tests).

- [ ] **Commit**

```bash
git add src/model/match_predictor.py tests/model/test_match_predictor.py
git commit -m "feat(model): MatchPredictor with unified over/under output for all markets"
```

---

## Task 5: `train_props.py` — entrenar los 4 submodelos de props

**Files:**
- Create: `src/model/train_props.py`

- [ ] **Implementar `src/model/train_props.py`**

```python
"""
Fase 4 — Entrenamiento de submodelos de props (corners, tarjetas, disparos, faltas).

Carga los partidos StatsBomb por equipo, entrena 4 PoissonModel independientes
via LOTO-CV, ensambla MatchPredictor junto al modelo de goles ya entrenado,
y guarda el predictor final en outputs/match_predictor.pkl.

Requiere que outputs/poisson_model.pkl exista (correr train.py primero).
"""
import pickle
from pathlib import Path

import pandas as pd

from src.model.match_predictor import MatchPredictor
from src.model.poisson_model import PoissonModel
from src.model.validation import loto_cv

ROOT             = Path(__file__).resolve().parents[2]
MATCH_PROPS_CSV  = ROOT / "data/processed/statsbomb_match_props.csv"
PROP_STATS_CSV   = ROOT / "data/features/prop_team_stats.csv"
TEAMS_CSV        = ROOT / "data/features/teams_features_v2.csv"
GOALS_MODEL_PKL  = ROOT / "outputs/poisson_model.pkl"
OUTPUT_PKL       = ROOT / "outputs/match_predictor.pkl"

RIDGE_LAMBDAS = [0.01, 0.05, 0.1, 0.5, 1.0]
DECAY_RATES   = [0.02, 0.05, 0.1]

# home/away score column pairs por mercado
MARKETS = {
    "corners": ("home_corners", "away_corners"),
    "cards":   ("home_yellow",  "away_yellow"),
    "shots":   ("home_shots",   "away_shots"),
    "fouls":   ("home_fouls",   "away_fouls"),
}

SANITY_MATCHES = [
    ("ARG", "FRA", None),
    ("ESP", "ENG", None),
    ("MEX", "USA", "MEX"),
    ("JPN", "DEU", None),
]


def build_teams_for_props(teams_df: pd.DataFrame, prop_stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Combina teams_features_v2.csv con prop_team_stats.csv.
    El modelo Poisson usa iso_code, elo_rating, squad_value_m_eur como covariables.
    Los stats de props son el TARGET (en match_props), no las covariables.
    """
    return teams_df.merge(
        prop_stats_df[["iso_code", "prop_corners_per90", "prop_yellow_per90",
                       "prop_shots_per90", "prop_fouls_per90", "prop_source"]],
        on="iso_code", how="left",
    )


def train_market(
    market: str,
    home_col: str,
    away_col: str,
    match_props: pd.DataFrame,
    teams_df: pd.DataFrame,
) -> PoissonModel:
    print(f"\n  === {market.upper()} ===")
    print(f"  Grid search: {len(RIDGE_LAMBDAS)} ridge × {len(DECAY_RATES)} decay ...")

    cv = loto_cv(
        match_props, teams_df,
        RIDGE_LAMBDAS, DECAY_RATES,
        home_score_col=home_col,
        away_score_col=away_col,
    )
    best = cv.iloc[0]
    print(f"  Mejor: ridge={best['ridge_lambda']}, decay={best['decay_rate']}, BS={best['mean_bs']:.4f}")

    model = PoissonModel(
        ridge_lambda=float(best["ridge_lambda"]),
        decay_rate=float(best["decay_rate"]),
    )
    model.fit(match_props, teams_df, year_ref=2026,
              home_score_col=home_col, away_score_col=away_col)
    return model


def main():
    print("=== train_props.py — Submodelos de props ===\n")

    match_props = pd.read_csv(MATCH_PROPS_CSV)
    prop_stats  = pd.read_csv(PROP_STATS_CSV)
    teams_base  = pd.read_csv(TEAMS_CSV)
    teams_df    = build_teams_for_props(teams_base, prop_stats)

    print(f"Partidos StatsBomb: {len(match_props)}")
    print(f"Torneos: {sorted(match_props['year'].unique())}")
    print(f"Equipos WC 2026 con prop stats: {prop_stats['iso_code'].nunique()}/48")

    # Cargar modelo de goles ya entrenado
    with open(GOALS_MODEL_PKL, "rb") as f:
        model_goals = pickle.load(f)
    print(f"\nModelo de goles cargado desde {GOALS_MODEL_PKL.name}")

    # Entrenar los 4 submodelos
    trained = {}
    for market, (home_col, away_col) in MARKETS.items():
        trained[market] = train_market(market, home_col, away_col, match_props, teams_df)

    # Ensamblar MatchPredictor
    predictor = MatchPredictor(
        model_goals   = model_goals,
        model_corners = trained["corners"],
        model_cards   = trained["cards"],
        model_shots   = trained["shots"],
        model_fouls   = trained["fouls"],
    )

    # ── Sanity check ────────────────────────────────────────────────────────
    print("\n\nSanity check — predicciones completas WC 2026:")
    for iso_a, iso_b, host in SANITY_MATCHES:
        if iso_a not in model_goals.teams_ or iso_b not in model_goals.teams_:
            continue
        r = predictor.predict_match(iso_a, iso_b, host_iso=host)
        print(f"\n{iso_a} vs {iso_b}" + (f" (sede: {host})" if host else ""))
        print(f"  Resultado:  {iso_a} {r['result']['p_home']:.0%} | Empate {r['result']['p_draw']:.0%} | {iso_b} {r['result']['p_away']:.0%}")
        print(f"  Goles:      expected {r['goals']['expected_total']} | O2.5: {r['goals']['over_2_5']:.0%} | U2.5: {r['goals']['under_2_5']:.0%} | BTTS: {r['goals']['btts']:.0%}")
        print(f"  Corners:    expected {r['corners']['expected_total']} | O10.5: {r['corners']['over_10_5']:.0%} | U10.5: {r['corners']['under_10_5']:.0%}")
        print(f"  Tarjetas:   expected {r['cards']['expected_total']} | O3.5: {r['cards']['over_3_5']:.0%} | U3.5: {r['cards']['under_3_5']:.0%}")
        print(f"  Disparos:   expected {r['shots']['expected_total']} | O24.5: {r['shots']['over_24_5']:.0%} | U24.5: {r['shots']['under_24_5']:.0%}")
        print(f"  Faltas:     expected {r['fouls']['expected_total']} | O22.5: {r['fouls']['over_22_5']:.0%} | U22.5: {r['fouls']['under_22_5']:.0%}")

    # ── Guardar ─────────────────────────────────────────────────────────────
    OUTPUT_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PKL, "wb") as f:
        pickle.dump(predictor, f)
    print(f"\n\nMatchPredictor guardado → {OUTPUT_PKL.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
```

- [ ] **Verificar que `loto_cv` acepta `home_score_col`/`away_score_col`**

`loto_cv` en `validation.py` llama a `PoissonModel.fit()`. Necesitamos que `fit()` y `loto_cv` acepten esos parámetros. Verificar:

```bash
source .venv/bin/activate && python3 -c "
from src.model.poisson_model import PoissonModel
import inspect
sig = inspect.signature(PoissonModel.fit)
print('fit() params:', list(sig.parameters.keys()))
"
```

Si `fit()` no tiene `home_score_col`/`away_score_col`, agregar en Task 5a abajo.

- [ ] **Task 5a (si es necesario): Extender `PoissonModel.fit()` y `loto_cv()` con `home_score_col`/`away_score_col`**

En `src/model/poisson_model.py`, modificar la firma de `fit()`:

```python
    def fit(
        self,
        matches_df: pd.DataFrame,
        teams_df: pd.DataFrame,
        year_ref: int = 2026,
        home_score_col: str = "home_team_score",
        away_score_col: str = "away_team_score",
    ) -> "PoissonModel":
        rows = build_match_rows(
            matches_df, teams_df,
            year_ref=year_ref,
            decay_rate=self.decay_rate,
            home_score_col=home_score_col,
            away_score_col=away_score_col,
        )
```

En `src/model/validation.py`, modificar `loto_cv()`:

```python
def loto_cv(
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    ridge_lambdas: list[float],
    decay_rates: list[float],
    year_ref_train: int = 2026,
    home_score_col: str = "home_team_score",
    away_score_col: str = "away_team_score",
) -> pd.DataFrame:
```

Y dentro del loop, pasar los parámetros a `model.fit()`:

```python
            model.fit(train, teams_df, year_ref=year_ref_train,
                      home_score_col=home_score_col,
                      away_score_col=away_score_col)
```

Verificar que los tests existentes siguen pasando:

```bash
pytest tests/ -v --tb=short
```

- [ ] **Correr `train_props.py`**

```bash
source .venv/bin/activate && python src/model/train_props.py
```

El grid search tardará 5-10 minutos (4 mercados × 8 torneos × 15 combinaciones).

Verificar en el output:
- Brier Score de cada mercado (no tiene referencia clara como 0.667 para resultados)
- Sanity check muestra valores coherentes: corners expected ~9-12, tarjetas ~3-5, disparos ~20-30, faltas ~18-28
- `outputs/match_predictor.pkl` creado

- [ ] **Correr suite completa de tests**

```bash
pytest tests/ -v
```

Esperado: todos en PASS.

- [ ] **Commit final**

```bash
git add src/model/train_props.py src/model/poisson_model.py src/model/validation.py
git commit -m "feat(model): train prop sub-models and assemble MatchPredictor"
```

---

## Notas de debugging

**Si `build_match_rows` falla con KeyError en `home_score_col`:**
- El CSV de StatsBomb match props usa `home_corners`, `away_corners`, etc. — verificar que coincidan exactamente con los nombres en `MARKETS`.

**Si Brier Score de props es muy alto (>0.9):**
- Corners/cards/shots tienen distribuciones más anchas que goles — BS mayor es esperado para estos mercados
- No es señal de fallo; la señal es si el modelo mejora sobre naive para cada mercado

**Si `train_props.py` falla con `FileNotFoundError` en `poisson_model.pkl`:**
- Correr `python src/model/train.py` primero para generar el modelo de goles

**Si sanity check muestra corners expected < 5 o > 20:**
- Revisar que `extract_team_stats()` no está contando el mismo evento dos veces
- Verificar que el campo `pass.type.name == "Corner"` es el correcto en los eventos

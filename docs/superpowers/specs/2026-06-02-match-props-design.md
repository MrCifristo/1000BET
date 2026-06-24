# Match Props Predictor — Diseño

**Fecha:** 2026-06-02  
**Estado:** Aprobado por usuario

---

## Objetivo

Expandir el predictor de resultados para cubrir mercados alternativos de apuestas: corners, tarjetas, disparos y faltas — además del resultado final. Para cada mercado se producen líneas Over/Under con probabilidades explícitas.

---

## Decisiones clave

| Decisión | Elección |
|---|---|
| Arquitectura | 5 submodelos Poisson independientes (reutilizar `PoissonModel`) |
| Datos props | StatsBomb 314 partidos ya descargados (corners, cards, shots, fouls en eventos JSON) |
| Datos goles | Fjelstul 964 partidos (sin cambio) |
| 8 equipos sin StatsBomb | Intentar WhoScored → Sofascore → mediana corpus |
| Output | `MatchPredictor` — clase que envuelve 5 modelos, un método por partido |

---

## 1. Capa de datos

### 1.1 StatsBomb → prop stats (40 equipos)

**Script nuevo:** `src/ingestion/11_statsbomb_match_stats.py`

Procesa los 314 JSONs de eventos ya descargados en `data/raw/statsbomb/`. Extrae por partido y por equipo:

| Campo | Extracción |
|---|---|
| `corners_for` | Eventos `Pass` con `pass.type.name == "Corner"` |
| `yellow_cards` | Eventos `Foul Committed` con `foul_committed.card.name == "Yellow Card"` + `Bad Behaviour` con card amarilla |
| `red_cards` | Tarjetas rojas en `Foul Committed` + `Bad Behaviour` |
| `fouls_committed` | Eventos `Foul Committed` |
| `shots_for` | Eventos `Shot` |
| `shots_on_target` | Eventos `Shot` con `shot.outcome.name in {"Goal", "Saved"}` |

Agrega a nivel de selección (promedio por 90 minutos sobre todos sus partidos):
- `prop_corners_per90`, `prop_yellow_per90`, `prop_red_per90`
- `prop_fouls_per90`, `prop_shots_per90`, `prop_sot_per90`

**Dos outputs:**
1. `data/processed/statsbomb_match_props.csv` — una fila por equipo por partido (para entrenar los submodelos, análogo a `matches_historical_v2.csv` para goles)
2. `data/features/statsbomb_prop_stats.csv` — promedio por equipo por 90' (para el feature set)

### 1.2 Fuente alternativa para 8 equipos sin StatsBomb

**Equipos:** BIH, CUW, HTI, IRQ, JOR, NZL, NOR, UZB

**Estrategia (orden de prioridad):**
1. **WhoScored** scraping directo — stats de internacionales disponibles públicamente
2. **Sofascore** vía soccerdata — instalado en el proyecto
3. **Mediana del corpus** de los 40 equipos cubiertos — fallback garantizado

**Output:** Filas adicionales que se concatenan a `statsbomb_prop_stats.csv` →  
`data/features/prop_team_stats.csv` (48 equipos, fuente documentada en columna `prop_source`)

### 1.3 Columnas finales de `prop_team_stats.csv`

```
iso_code, prop_corners_per90, prop_yellow_per90, prop_red_per90,
prop_fouls_per90, prop_shots_per90, prop_sot_per90, prop_source
```

`prop_source` ∈ `{"statsbomb", "whoscored", "sofascore", "median_imputed"}`

---

## 2. Arquitectura de submodelos

### 2.1 Reutilización de `PoissonModel`

Cada mercado entrena una instancia independiente de `PoissonModel` con diferente variable objetivo:

| Instancia | Variable objetivo | Dataset de entrenamiento | Equipos |
|---|---|---|---|
| `model_goals` | `goals_for` por team-match | Fjelstul 964 partidos | 48/48 |
| `model_corners` | `corners_for` por team-match | StatsBomb 314 partidos | 48/48 |
| `model_cards` | `yellow_cards` por team-match | StatsBomb 314 partidos | 48/48 |
| `model_shots` | `shots_for` por team-match | StatsBomb 314 partidos | 48/48 |
| `model_fouls` | `fouls_committed` por team-match | StatsBomb 314 partidos | 48/48 |

Los 4 submodelos de props usan el mismo `build_match_rows()` existente, pero con target diferente. El mismo LOTO-CV aplica para tunear `ridge_lambda` y `decay_rate` por separado para cada mercado.

### 2.2 Cálculo de Over/Under

La suma de dos Poisson es Poisson. Para un partido A vs B:

```
λ_total = λ_stat_a + λ_stat_b
P(total > X.5) = 1 − Poisson.cdf(floor(X + 0.5), λ_total)
P(total < X.5) = 1 − P(total > X.5)
```

### 2.3 Líneas por mercado

| Mercado | Líneas |
|---|---|
| Goles | 1.5, 2.5, 3.5 + BTTS |
| Corners | 8.5, 9.5, 10.5, 11.5 |
| Tarjetas amarillas | 2.5, 3.5, 4.5 |
| Disparos | 21.5, 24.5, 27.5 |
| Faltas | 19.5, 22.5, 25.5 |

Cada línea se reporta con `over_X_5` y `under_X_5` (suma a 1.0 siempre).

---

## 3. Output unificado

### 3.1 Clase `MatchPredictor`

**Archivo:** `src/model/match_predictor.py`

```python
class MatchPredictor:
    def __init__(self, model_goals, model_corners, model_cards, model_shots, model_fouls):
        ...

    def predict_match(self, iso_a: str, iso_b: str, host_iso: str | None = None) -> dict:
        ...
```

### 3.2 Formato del output

```python
{
  "result": {
    "p_home": 0.42, "p_draw": 0.24, "p_away": 0.34,
    "expected_score": "1.6 - 1.3", "likely_score": "2-1"
  },
  "goals": {
    "expected_total": 2.9,
    "over_1_5": 0.81, "under_1_5": 0.19,
    "over_2_5": 0.58, "under_2_5": 0.42,
    "over_3_5": 0.32, "under_3_5": 0.68,
    "btts": 0.52
  },
  "corners": {
    "expected_total": 10.4,
    "over_8_5": 0.74, "under_8_5": 0.26,
    "over_9_5": 0.61, "under_9_5": 0.39,
    "over_10_5": 0.47, "under_10_5": 0.53,
    "over_11_5": 0.33, "under_11_5": 0.67
  },
  "cards": {
    "expected_total": 3.8,
    "over_2_5": 0.71, "under_2_5": 0.29,
    "over_3_5": 0.54, "under_3_5": 0.46,
    "over_4_5": 0.35, "under_4_5": 0.65
  },
  "shots": {
    "expected_total": 26.1,
    "over_21_5": 0.78, "under_21_5": 0.22,
    "over_24_5": 0.55, "under_24_5": 0.45,
    "over_27_5": 0.34, "under_27_5": 0.66
  },
  "fouls": {
    "expected_total": 23.5,
    "over_19_5": 0.72, "under_19_5": 0.28,
    "over_22_5": 0.51, "under_22_5": 0.49,
    "over_25_5": 0.31, "under_25_5": 0.69
  }
}
```

### 3.3 Persistencia

`MatchPredictor` serializado en `outputs/match_predictor.pkl` (contiene los 5 modelos entrenados).

---

## 4. Archivos nuevos/modificados

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/ingestion/11_statsbomb_match_stats.py` | Crear | Extrae props de JSONs StatsBomb → `statsbomb_prop_stats.csv` |
| `src/ingestion/12_prop_coverage.py` | Crear | Busca datos para 8 equipos faltantes → `prop_team_stats.csv` |
| `src/model/match_predictor.py` | Crear | `MatchPredictor` — envuelve 5 `PoissonModel` |
| `src/model/train_props.py` | Crear | Entrena los 4 submodelos de props + grid search |
| `src/model/train.py` | Modificar | Usar `MatchPredictor` en el output final |

---

## 5. Fuera de scope

- Stats de primer tiempo por separado (HT over/under) — requiere parsear eventos por tiempo
- Estadísticas por jugador
- Mercados exóticos (primer equipo en hacer corner, etc.)
- Tarjetas rojas como mercado separado (muy raras, <0.3/partido — ruido estadístico)

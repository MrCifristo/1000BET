# ⚽ Mundial 2026 Predictor

Sistema de predicción estadística para la Copa Mundial de la FIFA 2026 (Canadá · EE. UU. · México).

![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![UI](https://img.shields.io/badge/UI-Streamlit-ff4b4b)

> **Modelo:** Poisson bivariado + corrección de Dixon-Coles + componente Elo.
> **Filosofía:** construir bien, no rápido. Una fase a la vez, reproducible y documentado.

---

## ¿Qué hace?

- **Predice partidos individuales:** probabilidades 1X2, marcador más probable (con su %),
  top-3 de marcadores y *expected goals* (λ) por equipo.
- **Simula el torneo completo:** motor de fase de grupos con los desempates oficiales FIFA,
  ranking de mejores terceros y cuadro de eliminatorias (R32 → final) que avanza a medida
  que se registran resultados reales.
- **Se evalúa con honestidad:** backtesting temporal con métricas Brier, RPS (ordinal 1X2)
  y *exact-score hit-rate*, comparando contra una línea base de Elo.
- **UI interactiva en Streamlit:** predecir partidos, explorar el torneo, ver la fiabilidad
  del modelo y su estado.

## Stack

Python 3.12 · pandas · numpy · scipy · Streamlit · pytest.

---

## Setup

```bash
git clone https://github.com/<tu-usuario>/1000BET.git
cd 1000BET

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Nota sobre los datos:** `data/raw/` (descargas de StatsBomb, openfootball, martj42…)
> **no se versiona** por tamaño y licencias de terceros — se regenera con los scripts de
> `src/ingestion/`. Sí se incluyen los datos de referencia curados a mano
> (`data/raw/reference/`) y los CSV exportados manualmente de FBref (`FbrefData/`).

## Uso

### Lanzar la UI

```bash
streamlit run src/ui/app.py
```

Páginas disponibles: **🔮 Predecir partido**, **🏆 Torneo**, **📊 Fiabilidad del modelo**
y **⚙️ Estado del modelo**.

### Pipeline de datos y entrenamiento

Los scripts de ingesta están numerados por orden de ejecución:

```bash
python src/ingestion/01_data_exploration.py
python src/ingestion/02_build_reference_data.py
# ... 03, 04, ... ver src/ingestion/
python src/model/train.py          # entrena el modelo de goles
```

Los DataFrames intermedios se guardan en `data/processed/` y las features por selección
en `data/features/`.

## Estructura

```
src/
  ingestion/    # descarga y parsing de datos (scripts numerados 01..12)
  features/     # ingeniería de features por selección
  model/        # modelo Poisson/Dixon-Coles, predictor y entrenamiento
  evaluation/   # backtesting temporal y métricas de calibración
  tournament/   # motor de grupos, desempates FIFA y cuadro de eliminatorias
  ui/           # aplicación Streamlit (app.py + pages/)
tests/          # suite de pytest (modelo + torneo)
data/
  raw/          # datos crudos descargados (no versionado; reference/ sí)
  processed/    # DataFrames consolidados
  features/     # features por selección
FbrefData/      # CSV de FBref exportados manualmente
outputs/        # artefactos del modelo (.pkl no versionados) y best_params.json
docs/           # specs y planes de diseño
notebooks/      # exploración y prototipado
```

## Tests

```bash
pytest
```

## Documentación interna

- `CLAUDE.md` — contexto y convenciones del proyecto.

## Convenciones

- Columnas en `snake_case` y en inglés.
- Selecciones identificadas por su código FIFA de 3 letras (`ARG`, `BRA`, `ESP`…).
- Partidos del mundial identificados como `{year}_{team1}_{team2}`.

## Fuentes de datos

[StatsBomb Open Data](https://github.com/statsbomb/open-data) ·
[openfootball](https://github.com/openfootball) ·
[martj42 international results](https://github.com/martj42/international_results) ·
FBref · estimaciones de valor de plantilla. Cada fuente conserva su licencia original.

## Licencia

Distribuido bajo la licencia **GNU GPL-3.0**. Ver [`LICENSE`](LICENSE).

Los datos de terceros (StatsBomb, FBref, etc.) están sujetos a sus propias licencias
y no se redistribuyen en este repositorio.

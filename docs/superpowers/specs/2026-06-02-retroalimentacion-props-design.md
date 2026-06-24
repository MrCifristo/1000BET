# Diseño: Retroalimentación multi-mercado del modelo

**Fecha:** 2026-06-02
**Estado:** Aprobado por el usuario

## Problema

Hoy el flujo "Ingresar resultado real" solo captura goles/resultado y reentrena el
modelo de goles. El usuario quiere cerrar el loop de aprendizaje con TODOS los
mercados: corners, disparos (remates), tarjetas y faltas — ingresar la data real
de cada partido y reentrenar los submodelos de props con ella.

## Decisiones de diseño (validadas)

1. **Granularidad:** por equipo (home/away separado), consistente con los modelos
   bivariados y con el corpus StatsBomb.
2. **Datos faltantes:** campos opcionales por mercado. Goles obligatorio; cada prop
   se puede dejar sin registrar. Cada submodelo se reentrena solo con los partidos
   que tengan ese dato.
3. **Reentrenamiento:** al guardar el partido se reentrenan goles + los props
   completados, usando los hiperparámetros ya guardados en `best_params.json`
   (sin grid search → rápido).

## Arquitectura

### 1. Captura (UI — `src/ui/pages/predict.py`)
En el expander "Ingresar resultado real":
- Goles A/B: obligatorio (ya existe).
- 4 mercados opcionales. Cada uno tras un `st.checkbox("Registrar <mercado>")`
  que, al activarse, despliega dos `number_input` (equipo A / equipo B).
- Mercados y campos: corners, shots (disparos), yellow (tarjetas), fouls (faltas).
- Al guardar, se arma un dict `props_real` solo con los mercados marcados.

### 2. Almacenamiento (`data/processed/results_log.csv` extendido)
Un partido = una fila. Columnas nuevas (NaN si no se registró el mercado):
`home_corners, away_corners, home_shots, away_shots, home_yellow, away_yellow,
home_fouls, away_fouls`.
La orientación home/away sigue a iso_a (home) / iso_b (away), igual que goals_a/b.

### 3. Reentrenamiento (`src/model/updater.py`)
- `log_result(...)`: acepta `props_real: dict | None` y escribe las 8 columnas
  (NaN donde no haya dato).
- `retrain_props_models(...)`: nueva función. Para cada mercado en
  `MARKETS = {corners, cards(=yellow), shots, fouls}`:
  - Filtra de `results_log` los partidos con ambos valores del mercado no-NaN.
  - Los convierte al esquema de `statsbomb_match_props` (home_<m>, away_<m>, year,
    host_team_iso, neutral_venue=True, time_weight implícito por year).
  - Concatena al corpus StatsBomb y reentrena `PoissonModel` con `best_params[m]`.
  - Reemplaza el submodelo correspondiente en `match_predictor.pkl`.
  - Si un mercado no tiene datos reales nuevos, se omite (no se toca su submodelo).
- Reutiliza el merge de `prop_team_stats` (covariables prop_*_per90) que ya hace
  `train_props.py`.

### 4. Flujo del botón (predict.py)
`log_result(goles + props_real)` → `update_elo` → `retrain_goals_model`
→ `retrain_props_models(mercados_con_datos)` → limpiar cache → rerun.

## Componentes y límites

- **predict.py**: solo captura y orquestación de UI. No conoce el detalle del
  reentrenamiento (delega en updater).
- **updater.py**: lógica de persistencia (`log_result`) y reentrenamiento
  (`retrain_goals_model`, `retrain_props_models`). Sin dependencias de Streamlit.
- **results_log.csv**: única fuente de verdad de resultados reales (goles + props).

## Manejo de errores
- Mercado marcado pero con corpus resultante vacío → omitir ese mercado sin fallar.
- `results_log.csv` con esquema antiguo (sin columnas de props) → al primer guardado
  con el nuevo `log_result`, pandas alinea por nombre de columna; si existiera un log
  previo incompatible se archiva (ya se hizo con `results_log_OLD_modelo_roto.csv`).

## Expectativa realista
Con 1-2 partidos reales por mercado el submodelo apenas se mueve (128 StatsBomb vs
pocos reales con time_weight). El valor está en la **acumulación** partido a partido.

## Fuera de alcance (YAGNI)
- Re-tuneo de hiperparámetros (grid search) en el loop online.
- Captura de stats a nivel jugador.
- Recalibración de líneas O/U mostradas (ajuste opcional separado).

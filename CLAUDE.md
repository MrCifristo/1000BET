# CLAUDE.md — Mundial 2026 Predictor

## Qué es este proyecto
Sistema de predicción estadística de partidos del Mundial 2026.
Modelo: Poisson bivariado + corrección Dixon-Coles + componente Elo.
Stack: Python, pandas, scipy, statsmodels.

## Filosofía
- Construir bien, no rápido. Una fase a la vez.
- Cada script debe ser reproducible y documentado.
- Preferir funciones pequeñas y testeables sobre monolitos.
- No saltar fases sin discusión previa con el usuario.

## Estado
El modelo está operativo: predicción de partidos, motor de torneo y UI Streamlit
funcionando. Ver `README.md` para el detalle de capacidades.

## Convenciones de código
- DataFrames intermedios se guardan en `data/processed/`.
- Nombres de columnas en `snake_case`, en inglés.
- Selecciones identificadas por su código FIFA de 3 letras (ARG, BRA, ESP...).
- Partidos del mundial identificados por: `{year}_{team1}_{team2}`.
- Scripts numerados por orden de ejecución: `01_data_exploration.py`, `02_...`.
- Funciones pequeñas, una responsabilidad. Imports en la cabecera.

## Estructura de carpetas
```
data/
  raw/        # datos crudos descargados (no editar)
  processed/  # DataFrames consolidados (output de scripts)
  features/   # features por selección
src/
  ingestion/  # descarga y parsing
  model/      # modelo estadístico
  evaluation/ # métricas y calibración
  prediction/ # predicción por partido
notebooks/    # exploración y prototipado
outputs/      # reportes generados
```

## Fuentes de datos
StatsBomb Open Data, openfootball, martj42 (resultados internacionales), FBref
(exportes manuales en `FbrefData/`) y datos de referencia curados en
`data/raw/reference/`.

## Reglas de operación con Claude Code
1. Una fase a la vez. No avanzar sin aprobación explícita.
2. Antes de terminar una fase: validar entregable funcional + dejar el estado documentado.
3. Cuando dudes de un enfoque técnico, plantear tradeoffs antes de implementar.

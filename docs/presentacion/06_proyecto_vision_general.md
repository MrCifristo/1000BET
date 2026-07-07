# 06 · Tu proyecto — Visión general y arquitectura

> **Idea en una frase:** construiste un **sistema de predicción estadística del Mundial
> 2026** que, dado dos selecciones, calcula la probabilidad de victoria/empate/derrota, los
> goles esperados y el marcador más probable — y además simula el torneo completo — todo en
> Python y expuesto en una app web interactiva.

Esta sección es el "mapa" del proyecto: qué hace, por qué Python, y cómo están organizadas
las piezas. Los archivos 07 y 08 hacen zoom en el modelo y su entrenamiento.

---

## 1. ¿Qué hace, en concreto?

Dado un partido entre dos selecciones (por su código FIFA de 3 letras, p. ej. `ARG` vs
`BRA`), el sistema produce:

- **Probabilidades 1X2:** P(gana A), P(empate), P(gana B).
- **Goles esperados (λ):** cuántos goles se espera que marque cada equipo.
- **Marcador más probable** y un **top-3** de marcadores con su probabilidad.
- **Marcador "coherente":** el marcador más probable que **concuerda** con el resultado
  1X2 más probable (evita mostrar "2-1" cuando lo más probable es el empate).
- **Mercados adicionales (props):** córners, tarjetas, tiros y faltas (over/under).

Y a nivel de torneo:
- **Tablas de grupos** con los **desempates oficiales de la FIFA**.
- **Cuadro eliminatorio** (de dieciseisavos —Round of 32— a la Final) que **avanza a
  medida que se registran resultados reales**.

Todo esto se usa desde una **app de Streamlit** con 4 páginas, pensada para que alguien no
técnico prediga un partido en segundos.

---

## 2. ¿Por qué Python? (la pregunta que te harán)

Cuatro razones, que además resumen toda la primera mitad de tu charla:

1. **El ecosistema estadístico.** El corazón del proyecto es un modelo de probabilidad. Lo
   que necesitaba —distribución de Poisson, un optimizador numérico, manejo de tablas de
   datos— **ya existe y es de primera clase** en Python: `scipy.stats.poisson`,
   `scipy.optimize.minimize`, `pandas`, `numpy`. En otro lenguaje habría tenido que
   reimplementar todo eso.
2. **Un solo lenguaje para todo el pipeline.** Con Python **descargo** los datos
   (scripts de ingestion), los **limpio** (pandas), **entreno** el modelo (SciPy), lo
   **evalúo** (backtesting) y lo **publico** en una web (Streamlit). Sin cambiar de
   tecnología. (Ver archivo 03, el punto que amarra todo.)
3. **Prototipado rápido.** Un modelo estadístico se explora por prueba y error. Python,
   interpretado y legible, permite iterar hipótesis rápidamente (archivo 01).
4. **Legibilidad y mantenibilidad.** El proyecto sigue una filosofía de "funciones
   pequeñas, una responsabilidad" — algo que Python favorece y que hace el código
   explicable (justo lo que necesitas para la demo).

> **Frase para la diapositiva:** "Elegí Python porque me deja hacer **todo el recorrido**
> —datos, modelo, evaluación y app— en un solo lenguaje, apoyándome en el mejor ecosistema
> estadístico que existe."

---

## 3. La arquitectura (el recorrido de los datos)

El proyecto está organizado como un **pipeline** por fases. Cada carpeta es una etapa con
una responsabilidad clara:

```
  DATOS CRUDOS                     src/ingestion/   (scripts 01…12, en orden)
  (StatsBomb, martj42,      ─────► descarga + parsing + Elo + StatsBomb + Transfermarkt
   openfootball, FBref)             │
                                    ▼
  FEATURES POR EQUIPO             src/features/    (experiencia mundialista, afinidad
  (fuerza, xG, valor,       ─────► de local, índice de sorpresa) + consolidación
   Elo, experiencia)                │   →  data/features/teams_features_v*.csv
                                    ▼
  MODELO ESTADÍSTICO              src/model/       (Poisson bivariado + Dixon-Coles + Elo)
  (aprende de partidos      ─────► poisson_model.py · train.py · match_predictor.py
   históricos)                      │   →  outputs/*.pkl
                                    ▼
  EVALUACIÓN                      src/evaluation/  (backtest temporal honesto, métricas
  (¿es bueno el modelo?)    ─────► Brier / log-loss / RPS vs baselines)
                                    │
                                    ▼
  MOTOR DE TORNEO                 src/tournament/  (grupos, desempates FIFA, bracket,
  (simula el Mundial)       ─────► Monte Carlo, reportes)
                                    │
                                    ▼
  INTERFAZ (UI)                   src/ui/          (Streamlit: app.py + views/)
  (el usuario final)        ─────► 4 páginas interactivas
```

**Carpetas de datos** (convención del proyecto):
- `data/raw/` — datos crudos descargados (no se editan; en gran parte no versionados).
- `data/processed/` — DataFrames consolidados (salida de los scripts).
- `data/features/` — tablas de características por selección.
- `outputs/` — artefactos del modelo entrenado (`*.pkl`) + `best_params.json`.

---

## 4. Las piezas clave del código (para orientarte en la demo)

| Archivo | Responsabilidad | Qué mostrar en clase |
|---|---|---|
| `src/model/poisson_model.py` | **El modelo**: define la fórmula, entrena (`fit`) y predice (`predict_match`) | El corazón matemático (archivo 07) |
| `src/model/features.py` | Construye las variables de entrada de cada partido | Cómo se convierte un partido en números |
| `src/model/train.py` | **Script de entrenamiento**: tuning + fit final + guardar `.pkl` | Cómo "se entrena" (archivo 08) |
| `src/model/validation.py` | Validación cruzada LOTO-CV + Brier Score | Cómo se elige lo mejor sin hacer trampa |
| `src/model/match_predictor.py` | Envuelve 5 modelos (goles + 4 props) en una predicción unificada | El resultado completo de un partido |
| `src/evaluation/backtest_temporal.py` | Backtest honesto vs Mundiales pasados | La prueba de que funciona |
| `src/model/updater.py` | Actualiza Elo y **re-entrena** con resultados reales | Cómo "sigue aprendiendo" en vivo |
| `src/tournament/` | Grupos, desempates FIFA, cuadro eliminatorio | La simulación del torneo |
| `src/ui/app.py` + `views/` | La app de Streamlit (lo que verá la clase) | **La demo** (archivo 10) |

---

## 5. El stack tecnológico (tabla de una diapositiva)

| Capa | Herramientas |
|---|---|
| Lenguaje | **Python 3.12** |
| Números / datos | `pandas`, `numpy`, `scipy` (Poisson + optimización L-BFGS-B) |
| Ingesta de datos | `requests`, `lxml`, `beautifulsoup4`, `soccerdata`, `country_converter` |
| Interfaz (UI) | `streamlit` |
| Visualización | `matplotlib`, `seaborn`, `jupyter` |
| Pruebas | `pytest` |

---

## 6. Lo que hace a este proyecto "presentable" (tus argumentos de venta)

- **De extremo a extremo:** no es solo un modelo, es todo el sistema (datos → app).
- **Honesto:** se valida con *backtesting temporal* sin mirar el futuro, y se compara
  contra baselines. No se autoengaña (archivo 08).
- **Interpretable:** cada parámetro tiene significado real (archivo 07).
- **Vivo:** avanza el cuadro del Mundial 2026 con resultados reales.
- **Reproducible y documentado:** scripts numerados, convenciones claras, suite de tests.

---

## Cómo presentar esta sección (30–45 s de guion)
> "Mi proyecto predice partidos del Mundial 2026. Pero no es solo una fórmula: es un
> sistema completo en Python que **descarga** datos históricos de fútbol, construye
> **características** de cada selección, **entrena** un modelo estadístico, **verifica** que
> funcione contra Mundiales pasados, y lo pone todo en una **app web** donde eliges dos
> equipos y ves la predicción al instante. Ahora les muestro cómo funciona el cerebro del
> sistema."

→ Continúa en **07_modelo_como_funciona.md**.

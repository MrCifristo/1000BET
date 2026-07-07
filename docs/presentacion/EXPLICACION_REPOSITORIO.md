# Explicación del repositorio — *Mundial 2026 Predictor*

> Guía para que **tú** puedas explicar tu propio código: qué hace cada parte, qué archivos
> son los importantes, cómo fluye todo, y qué te pueden preguntar.
> Ordenada de lo general a lo específico. Los datos de esta guía salen de leer el código real.

---

## 1 · La vista de 30 segundos (tu "elevator pitch" del repo)

> *"Es un sistema en Python que predice partidos del Mundial 2026. El corazón es un **modelo
> de Poisson bivariado** que estima cuántos goles esperamos de cada equipo, con una **corrección
> Dixon-Coles** para los marcadores bajos y **covariables** como el Elo y el valor de la plantilla.
> El modelo **aprende** de ~22.000 partidos internacionales reales ajustando sus parámetros con un
> optimizador. Encima hay un **motor de torneo** que arma los grupos con los desempates oficiales de
> la FIFA y resuelve el cuadro final, y una **app de Streamlit** que lo pone todo en una pantalla.
> Y lo validé con un **backtest honesto**: predecir Mundiales pasados con datos que el modelo no vio."*

El repo está organizado como una **tubería (pipeline)**: los datos entran crudos, se transforman en
características por selección, alimentan el modelo, y el resultado sale por la app.

```
datos crudos → features por equipo → modelo aprende → predice → torneo / app
 (ingestion)      (features)          (model)        (model)   (tournament / ui)
                                          ↑
                                   (evaluation valida que funcione)
```

---

## 2 · El modelo en una fórmula (lo que tienes que saber sí o sí)

Para un partido del equipo *i* (atacante) contra *j* (defensor), los goles esperados **λ** se calculan así:

```
log(λ_i) = μ + α_i − β_j + γ·host_i + δ·elo_diff + ε·xg_diff + ζ·log(valor_i / valor_j)
```

| Símbolo | Qué es | Por qué |
|---------|--------|---------|
| **μ** (mu) | media global de goles | el punto de partida común a todos |
| **α_i** (alfa) | fuerza de **ataque** del equipo i | se aprende de los datos |
| **β_j** (beta) | **debilidad defensiva** del rival j | se aprende de los datos |
| **γ·host** (gamma) | ventaja de jugar como **anfitrión** | localía |
| **δ·elo_diff** (delta) | diferencia de **Elo** (÷100) | ranking de forma reciente |
| **ε·xg_diff** (epsilon) | diferencia de **xG** (calidad de ocasiones) | qué tan bien generan chances |
| **ζ·log_value** (zeta) | ratio de **valor de mercado** de las plantillas | calidad de los jugadores |

**Por qué `log(λ)` y no `λ` directo:** al modelar el logaritmo, λ nunca sale negativo al deshacer el
log (`λ = e^(...)`), y no existen goles negativos. (Esto es un *modelo lineal generalizado* con enlace log.)

**De λ a la predicción:** con la λ de cada equipo se construye una **matriz de marcadores** (probabilidad
de 0-0, 1-0, 2-1, …) multiplicando las dos distribuciones de Poisson. De esa matriz sale todo:
- **1X2:** sumar el triángulo inferior = gana local, la diagonal = empate, el triángulo superior = gana visitante.
- **Marcador más probable:** la casilla más alta de la matriz.
- **Goles esperados:** las λ mismas.

**Dixon-Coles (la "corrección"):** un Poisson simple subestima los empates bajos (0-0, 1-1). Dixon y Coles
(1997) añadieron un factor **τ (tau)**, controlado por un parámetro **ρ (rho)**, que ajusta solo esas 4
casillas: {0-0, 1-0, 0-1, 1-1}. Por eso el modelo se llama "Poisson bivariado **+ Dixon-Coles**".

---

## 3 · Mapa de carpetas — qué hace cada una

```
src/
  ingestion/    ← 14 scripts numerados 01..12: bajan y limpian los datos (pipeline de datos)
  features/     ← construyen características por selección (experiencia, afinidad, sorpresa)
  model/        ← EL NÚCLEO: el modelo Poisson, el entrenamiento y la predicción
  evaluation/   ← el backtest honesto y las métricas (¿de verdad funciona?)
  tournament/   ← motor de grupos con desempates FIFA + cuadro final + Monte Carlo
  ui/           ← la app de Streamlit (4 páginas)
tests/          ← pruebas con pytest (modelo + torneo)
data/           ← raw/ (crudo) · processed/ (consolidado) · features/ (por equipo)
outputs/        ← el modelo entrenado (match_predictor.pkl) + best_params.json
```

**Si solo pudieras enseñar 3 carpetas, serían `model/`, `tournament/` y `ui/`.** El resto es la
plomería que las alimenta.

---

## 4 · Los archivos que DE VERDAD importan

Si te preguntan "muéstrame el código", abre estos, en este orden:

| # | Archivo | Por qué importa | Qué decir |
|---|---------|-----------------|-----------|
| 1 | `src/model/poisson_model.py` | **El cerebro.** Aquí vive la fórmula de λ, Dixon-Coles y el entrenamiento. | "Esta clase es todo el modelo estadístico." |
| 2 | `src/model/match_predictor.py` | El **envoltorio** que junta 5 modelos (goles + córners, tarjetas, tiros, faltas). | "Lo que la app consume: un objeto que predice todos los mercados." |
| 3 | `src/model/features.py` | Convierte partidos en las **filas** que el modelo entrena. | "La preparación de datos: de partidos crudos a covariables." |
| 4 | `src/model/train_goals_intl.py` | El **script de entrenamiento actual** (corpus internacional). | "Lo que corro para (re)entrenar el modelo." |
| 5 | `src/evaluation/backtest_temporal.py` | La **prueba honesta**: de aquí salen los 0.593 / 0.667 / 14.5%. | "Cómo demuestro que funciona sin hacer trampa." |
| 6 | `src/tournament/standings.py` | Los **desempates FIFA** y las tablas de grupo. | "El reglamento oficial, en código." |
| 7 | `src/tournament/bracket.py` | El **cuadro** que se resuelve en cascada (R32 → Final). | "Cómo avanza el torneo con resultados reales." |
| 8 | `src/ui/app.py` + `views/predict.py` | La **cara visible**: la app. | "Donde el usuario elige dos equipos y lee la predicción." |

---

## 5 · Recorrido por subsistema (con los detalles que te pueden preguntar)

### 5.1 · `src/model/` — el núcleo

**`poisson_model.py`** — la clase `PoissonModel`. Lo que hace:
- **`fit()`**: entrena. Construye una fila por equipo-atacante (dos por partido: local y visitante),
  arma la **verosimilitud de Poisson ponderada** (los partidos recientes pesan más, vía un
  decaimiento temporal `exp(-decay·años)`), le suma la **penalización ridge** y busca el mínimo con
  el optimizador **L-BFGS-B** de SciPy.
- **Regularización ridge (L2):** penaliza que las α y β se hagan grandes → evita el **sobreajuste**.
  Solo penaliza ataque/defensa, no las covariables.
- **Restricción de identificabilidad Σα = 0:** los α se fuerzan a sumar cero. Sin esto, μ y los α
  serían redundantes (podrías subir μ y bajar todos los α y dar lo mismo) y el modelo no sería único.
- **`predict_score_matrix()`**: producto externo de dos Poisson + corrección Dixon-Coles + renormalizar.
- **`predict_match()`**: de la matriz saca 1X2, goles esperados, marcador más probable, top-3 y el
  **marcador coherente** (que nunca contradiga al favorito del 1X2 — si el modal es empate, no muestra "2-1").

**`match_predictor.py`** — la clase `MatchPredictor`: envuelve **5** `PoissonModel` (goles + 4 props:
córners, tarjetas, tiros, faltas) y calcula los **over/under** (`P(over) = 1 − Poisson.cdf(línea)`) y el
**BTTS** (ambos marcan). Es el objeto que se serializa a `outputs/match_predictor.pkl` y que carga la app.

**`features.py`** — prepara los datos: expande cada partido en 2 filas, calcula los pesos temporales,
las diferencias de covariables (elo_diff, xg_diff, log_value_ratio) y usa el **Elo point-in-time**
(el Elo *antes* del partido, sin mirar el futuro). Imputa a la mediana los equipos sin datos.

**`train_goals_intl.py`** vs **`train.py`** (¡pregunta probable!):
- `train.py` es la **versión antigua**: entrenaba solo con Mundiales (~484 partidos) y hacía grid-search.
- `train_goals_intl.py` es la **versión actual**: entrena con el corpus internacional ampliado (~22.000
  partidos desde 2002) con hiperparámetros ya fijados (`ridge=1.0, decay=0.05`). *Ambos existen en el repo;
  el actual es el internacional.*

**`train_props.py`** entrena los 4 modelos de props y ensambla el `MatchPredictor` final.
**`validation.py`** tiene el **Brier score** y la **validación cruzada Leave-One-Tournament-Out (LOTO-CV)**.
**`updater.py`** + **`load_results.py`**: el **aprendizaje online** — cuando registras un resultado real,
actualiza el Elo, guarda el Brier de esa predicción y **reentrena** el modelo. "El siguiente partido aprende del anterior."

### 5.2 · `src/evaluation/` — ¿de verdad funciona?

**`backtest_temporal.py`** es la pieza estrella. Idea clave: **backtest "point-in-time" (sin look-ahead)**.
Para cada Mundial (2010, 2014, 2018, 2022) entrena **solo con partidos anteriores a ese torneo** y predice
ese Mundial. Nunca ve el futuro → la prueba es honesta.
- **Métricas** (menor = mejor en las tres): **Brier** (error cuadrático de las probabilidades),
  **log-loss** (castiga la sobre-confianza), **RPS** (tiene en cuenta el orden ganar/empatar/perder).
- **Baselines** contra los que compite: **Elo puro** (probabilidades solo del ranking) y **naive** (1/3 a cada resultado).
- **De aquí salen las cifras del deck:** son la **salida impresa** del backtest sobre **256 partidos**
  (2010–2022), no números inventados:

  | | Brier | interpretación |
  |---|---|---|
  | **Naive (azar)** | 0.667 | tirar una moneda de 3 caras |
  | **Modelo** | 0.593 | tu modelo |
  | **Elo puro** | 0.588 | solo el ranking |

  → **Ojo, pregunta trampa:** el Elo puro sale *marginalmente mejor* en Brier (0.588 < 0.593). Tu
  respuesta honesta y fuerte: *"En Brier están empatados; pero en **log-loss** mi modelo gana claro
  (1.00 vs 1.28), y además da goles, marcador y mercados que el Elo solo no da."*
  → **Marcador exacto 14.5%:** cuenta cuántas veces el marcador más probable coincidió con el real
  (el techo realista del "correct score" en fútbol ronda 9–12%, así que 14.5% es bueno).

**`experiments.py`** es el "laboratorio" donde probaste variantes (blends con Elo, temperature scaling,
distintos ridge) y decidiste `ridge=1.0`. **`baseline_eval.py`** es una auditoría LOTO adicional.
**`metrics.py`** son las mismas métricas vectorizadas para la app.

### 5.3 · `src/tournament/` — el motor del torneo

**`standings.py`** — las 12 tablas de grupo y **los desempates oficiales FIFA 2026**. El orden real
implementado (¡y verificado por los tests!) es:

1. **Puntos**
2. **Diferencia de goles global**
3. **Goles a favor global**
4. Si siguen empatados, **solo entre ellos**: puntos en enfrentamiento directo (head-to-head)
5. Diferencia de goles directa · 6. Goles a favor directos
7. (fair play / sorteo) → en el código, **desempate final por Elo** (determinista y reproducible)

> **Matiz importante para que no te pillen:** la diferencia de goles **global** va **ANTES** del
> head-to-head. Es el reglamento FIFA vigente. Hay un test (`test_dg_global_antes_que_h2h`) que lo
> comprueba justamente. No digas "primero el head-to-head" — es al revés.

También rankea los **8 mejores terceros** que pasan a la Ronda de 32.

**`bracket.py`** — el cuadro numerado al estándar FIFA (grupos 1–72, **R32 = 73–88**, R16 = 89–96,
cuartos 97–100, semis 101–102, 3er puesto 103, **Final = 104**). Resuelve los *placeholders* (`1A`,
`3A/B/C`, `W73` = ganador del partido 73, `L101` = perdedor…) **en cascada**: recorre los partidos en
orden y va colocando equipos reales a medida que hay resultados.

**`montecarlo.py`** — simula el resto del torneo **2000 veces** (por defecto): muestrea los marcadores
pendientes de la matriz Dixon-Coles del modelo y devuelve la probabilidad de que cada selección avance
por ronda y sea **campeón**. Reproducible (semilla fija).

**`report.py`** — orquesta todo y lo guarda a CSV (`wc2026_standings.csv`, `wc2026_bracket.csv`).

### 5.4 · `src/ingestion/` — la tubería de datos (scripts 01→12)

Se corren **en orden**; cada uno produce un archivo que el siguiente usa. Fuentes: **abiertas y públicas**.

| Script | Qué produce | Fuente |
|--------|-------------|--------|
| 01 | histórico de Mundiales + fixtures 2026 | Fjelstul WC DB + openfootball |
| 02 | datos de referencia curados (48 selecciones, anfitriones, diáspora) | curación manual (ISO 3166) |
| 03 | histórico enriquecido (alias, sede neutral, peso temporal) | — |
| 04 | Elo actual de selecciones | eloratings.net |
| 05–06 | eventos StatsBomb → **xG** por equipo | StatsBomb Open Data |
| 07 | **valor de mercado** de plantillas | Transfermarkt |
| 08 | plantillas + stats de club | Wikipedia + Understat |
| 09 | **consolida todas las features** en un DataFrame | (une las anteriores) |
| 10_intl | **corpus internacional ~22k partidos (2002+)** | martj42/international_results |
| 11_elo | **Elo rodante point-in-time** (sin leakage) | (calculado sobre el corpus) |
| 11_statsbomb / 12 | props (córners, tarjetas…) + imputación | StatsBomb / mediana |

> El **pivote clave** del proyecto fue pasar de "solo Mundiales" (~484 partidos) a "todos los
> internacionales modernos" (~22.000). Más datos = mejor aprendizaje. Ese es `10_intl` + `11_elo`.

### 5.5 · `src/ui/` — la app de Streamlit (4 páginas)

- **`app.py`**: el punto de entrada y la navegación entre las 4 páginas.
- **`predict.py`** (*Predecir partido*): eliges dos equipos → 1X2, goles esperados, **heatmap** de
  marcadores y mercados over/under. También puedes **registrar el resultado real** y reentrenar.
- **`tournament.py`** (*Torneo*): las 12 tablas, los mejores terceros, el cuadro KO y la **simulación
  Monte Carlo** con la probabilidad de campeón de cada selección.
- **`dashboard.py`** (*Fiabilidad*): el Brier acumulado sobre los partidos ya registrados, vs el naive.
- **`model_status.py`** (*Estado del modelo*): los hiperparámetros y el **ranking de ataque (α) y
  defensa (β)** aprendidos — aquí se ve que el modelo es **interpretable**.
- **`components.py`**: el componente compartido que muestra el forecast de marcador de forma "honesta"
  (distingue goles esperados, marcador más probable y marcador coherente).

---

## 6 · El flujo completo, de punta a punta

```
1. INGESTIÓN   scripts 01..12  → data/raw, data/processed, data/features
2. FEATURES    features/*.py   → teams_features.csv (una fila por selección)
3. ENTRENAR    train_goals_intl.py + train_props.py → outputs/match_predictor.pkl
4. VALIDAR     backtest_temporal.py → Brier 0.593 vs naive 0.667 (prueba honesta)
5. PREDECIR    match_predictor.predict_match(ARG, BRA, host) → 1X2 + goles + marcador
6. TORNEO      standings → bracket → montecarlo → probabilidad de campeón
7. APP         streamlit run src/ui/app.py → todo lo anterior en pantalla
8. APRENDER    registras un resultado real → updater reentrena → el modelo mejora
```

---

## 7 · Cómo correrlo (por si te lo piden en vivo)

```bash
# la app (lo más vistoso):
streamlit run src/ui/app.py

# reentrenar el modelo de goles:
python -m src.model.train_goals_intl

# la prueba honesta (backtest):
python -m src.evaluation.backtest_temporal

# el estado del torneo por consola:
python -m src.tournament.report

# las pruebas:
pytest
```

---

## 8 · Preguntas técnicas que te pueden hacer (y cómo responder)

- **"¿Por qué Poisson?"** → *"Los goles son eventos raros y discretos; Poisson es la distribución hecha
  para contar eventos raros por unidad de tiempo. Con un solo número, λ, describe toda la distribución de goles."*

- **"¿Qué es Dixon-Coles y por qué lo necesitas?"** → *"Poisson puro subestima los empates de marcador
  bajo (0-0, 1-1). Dixon-Coles corrige exactamente esas casillas con un parámetro ρ que también se aprende."*

- **"¿Cómo evitas el sobreajuste?"** → *"Tres cosas: regularización **ridge** que penaliza parámetros
  grandes, **decaimiento temporal** para no sobre-pesar partidos viejos, y validación en partidos que el
  modelo **no vio** (backtest point-in-time y LOTO-CV)."*

- **"¿Cómo sabes que no hiciste trampa en la validación?"** → *"El backtest es **point-in-time**: para
  predecir el Mundial 2018 solo entreno con partidos anteriores a 2018, y uso el Elo de ese momento, no el de hoy."*

- **"¿Qué optimizador usas?"** → *"**L-BFGS-B** de SciPy: busca los parámetros que maximizan la
  verosimilitud, minimizando el error 'cuesta abajo' hasta el mínimo."*

- **"¿Es una caja negra?"** → *"No. Cada parámetro significa algo: si ordeno los equipos por su α,
  obtengo un ranking real de ataques. Eso es **machine learning interpretable**."*

- **"¿Por qué no una red neuronal / deep learning?"** → *"Con miles (no millones) de partidos, un modelo
  interpretable rinde igual o mejor y puedo **explicar cada número**. Una red sería una caja negra con
  más riesgo de sobreajuste y sin ganancia clara aquí."*

- **"¿De dónde vienen los datos?"** → *"Fuentes abiertas: StatsBomb (eventos y xG), FBref, Transfermarkt
  (valor de plantilla), martj42 (22k resultados internacionales), eloratings.net. Todo público y reproducible."*

- **"¿Cómo actualiza el torneo?"** → *"El bracket se resuelve en cascada: cada partido tiene placeholders
  como 'ganador del 73', y a medida que registro resultados reales se van sustituyendo por equipos, de la
  Ronda de 32 hasta la final."*

- **"¿Tiene pruebas?"** → *"Sí, una suite de pytest que cubre el modelo, Dixon-Coles, la validación y el
  motor de torneo — incluyendo los desempates FIFA y la cascada del bracket."*

---

## 9 · Limitaciones honestas (menciónalas tú, suma credibilidad)

- El modelo **no lee noticias**: no sabe de lesiones de última hora ni cambios de técnico (usa forma vía
  Elo y valor de plantilla, pero no contexto cualitativo).
- El **Elo puro** es un rival muy duro: en Brier va parejo. El valor añadido del modelo está en **log-loss**
  y en todo lo extra que produce (goles, marcador, mercados, torneo).
- El **valor de mercado** favorece a ligas top; puede subestimar a selecciones con jugadores en ligas menos visibles.
- Las features de torneo (afinidad con el anfitrión, experiencia) se exponen "crudas" y el modelo aprende
  sus pesos — es una decisión de diseño, no una fórmula fija.

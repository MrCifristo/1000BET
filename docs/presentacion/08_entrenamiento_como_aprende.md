# 08 · Cómo aprende y se entrena el modelo

> **Idea en una frase:** "entrenar" el modelo significa **buscar los valores de los
> parámetros (α, β, μ, γ, δ, ε, ζ, ρ) que hacen que sus predicciones se parezcan lo más
> posible a los resultados reales de miles de partidos históricos** — y esa búsqueda la
> hace un optimizador numérico (L-BFGS-B de SciPy) minimizando una función de error.

Aquí está el "cómo aprende", que es lo que más impresiona explicar bien. Va de la intuición
del aprendizaje a los detalles: verosimilitud, optimización, regularización, validación y
actualización en vivo. Código: `poisson_model.py`, `train.py`, `validation.py`,
`updater.py`.

---

## 1. ¿Qué significa "aprender" aquí? (la intuición)

Antes de entrenar, los parámetros no valen nada (empiezan en cero). El modelo **no sabe**
que Brasil ataca bien o que Malta defiende mal.

**Aprender = ajustar esos números** hasta que el modelo "explique" bien el pasado:
> Si el modelo dice que Brasil marcaría 0.3 goles de media pero en la realidad histórica
> marcó 2.5, ese error es grande → hay que **subir** el α (ataque) de Brasil. Se repite
> este ajuste, para todos los equipos y parámetros a la vez, hasta minimizar el error
> total.

Es exactamente la idea del machine learning del archivo 05: **Datos + Respuestas → Reglas**.
Las "respuestas" son los goles reales; las "reglas" son los parámetros aprendidos.

---

## 2. La función que se minimiza: máxima verosimilitud

**¿Cómo medimos "qué tan bien explica el modelo los datos"?** Con la **verosimilitud
(likelihood)**: la probabilidad que el modelo le asigna a los goles que **realmente**
ocurrieron.

- Un buen modelo asigna **alta** probabilidad a lo que de verdad pasó.
- **Entrenar = encontrar los parámetros que maximizan esa verosimilitud** (Maximum
  Likelihood Estimation, MLE).

**Truco técnico estándar:** en vez de maximizar la verosimilitud, se **minimiza la
verosimilitud negativa logarítmica** (*negative log-likelihood*). Es matemáticamente
equivalente y numéricamente más estable. En tu código es la función `neg_ll(theta)` dentro
de `PoissonModel.fit`.

Para la Poisson, esa función de error tiene esta forma (por cada fila de partido):
```
contribución = goles · log(λ) − λ        (ponderada por el peso temporal de la fila)
```
El modelo suma esto sobre **todos** los partidos y busca los parámetros que lo optimizan.

---

## 3. El optimizador: L-BFGS-B (donde ocurre la magia)

No se puede "probar todas las combinaciones" de parámetros: hay cientos (dos por cada una
de ~200 selecciones). Se necesita un **algoritmo de optimización** que baje el error de
forma inteligente.

Tu código usa **L-BFGS-B**, de `scipy.optimize.minimize`:
```python
result = minimize(neg_ll, theta0, method="L-BFGS-B", bounds=bounds,
                  options={"maxiter": 3000, "ftol": 1e-12})
```

**Intuición (descenso de gradiente):** imagina el error como un **valle** y los parámetros
como tu posición. El optimizador mira la **pendiente** bajo sus pies y da pasos cuesta
abajo, una y otra vez, hasta llegar al fondo (el mínimo error). L-BFGS-B es una versión
eficiente y con memoria limitada de esa idea, que además admite **límites** (*bounds*) en
los parámetros (la "B" es de *Bounded*).

> **Frase clave:** "La parte que realmente *aprende* de mi proyecto es una sola llamada:
> `minimize(...)` con L-BFGS-B. Le doy la función de error y él encuentra los parámetros que
> la minimizan, deslizándose cuesta abajo por el 'valle' del error."

**Un detalle elegante — la restricción de identificabilidad (Σα = 0):** como solo importan
las **diferencias** de ataque entre equipos, hay infinitas soluciones equivalentes (subir
todos los α a la vez no cambia nada). Para fijar una única solución, se impone que **la suma
de los α sea 0**. En el código, α₀ se calcula como `−(suma del resto)`. Esto hace los
parámetros interpretables: un α positivo = ataque por encima de la media mundial.

---

## 4. Regularización ridge (para no "memorizar")

**El riesgo (overfitting):** con tantos parámetros, el modelo podría **memorizar** rarezas
del pasado (p. ej. un 7-0 aislado) y generalizar mal a partidos nuevos.

**La solución (regularización L2 / ridge):** añadir a la función de error una **penalización
por parámetros grandes**:
```
error_total = −log-verosimilitud  +  (ridge_lambda / 2) · (Σα² + Σβ²)
```
Esto "encoge" los α y β hacia cero salvo que los datos justifiquen fuertemente lo
contrario. Es un freno a la exageración → **mejor generalización**.

- `ridge_lambda` es un **hiperparámetro** (tú lo fijas, no se aprende). Controla cuánto
  frenas: mucho = modelo tímido; poco = modelo que se sobreajusta.

**Analogía:** la regularización es como un editor escéptico que te dice "no saques
conclusiones grandes de una sola anécdota"; solo te deja afirmar algo fuerte si tienes
mucha evidencia.

---

## 5. El peso temporal (los datos viejos importan menos)

No todos los partidos deben pesar igual: la forma de una selección en 2010 dice poco sobre
2026. Por eso cada partido entra con un **peso que decae con el tiempo**:
```
time_weight = exp(−decay_rate · (año_ref − año_del_partido))
```
Un partido de este año pesa 1.0; uno de hace 10 años pesa mucho menos. `decay_rate` es el
otro **hiperparámetro** clave. (Código: `compute_time_weights` en `features.py`.)

> Nota: existe también un peso opcional por **importancia del partido** (un Mundial pesa
> más que un amistoso), pero por defecto está **desactivado** porque tus experimentos
> mostraron que empeoraba el backtest. Es un buen ejemplo de decidir con datos, no con
> intuición.

---

## 6. Elegir los hiperparámetros sin hacer trampa: LOTO-CV

Los dos hiperparámetros (`ridge_lambda`, `decay_rate`) no se aprenden solos: hay que
**probarlos**. Y probarlos sobre los mismos datos con los que entrenas sería trampa. La
solución es **validación cruzada**, en tu caso una variante específica:

**LOTO-CV = Leave-One-Tournament-Out Cross-Validation** (`validation.py`):
> Para cada combinación de hiperparámetros, y para cada torneo T del historial:
> 1. **Entrena** con todos los partidos **excepto** los del torneo T.
> 2. **Predice** los partidos de T (que el modelo no vio).
> 3. **Mide** el error de esas predicciones.
> Se promedia el error sobre todos los torneos. Gana la combinación con menor error.

Es una simulación honesta de "¿qué tan bien predeciría un Mundial que no ha visto?". Se hace
por **grid search** (probar una rejilla de valores): en `train.py`, 5 `ridge_lambda` × 3
`decay_rate`. Los mejores se guardan en `outputs/best_params.json`.

---

## 7. ¿Con qué se mide el error? Brier Score (y compañía)

Como el modelo predice **probabilidades**, no un resultado seco, se necesita una métrica
que premie las probabilidades bien calibradas. La principal es el **Brier Score**
(`validation.py`, `metrics.py`):
```
BS = promedio de  (p_home − o_home)² + (p_draw − o_draw)² + (p_away − o_away)²
```
donde `o` es 1 para el resultado que ocurrió y 0 para los demás. **Menor = mejor.**

- **Referencia:** un modelo tonto que siempre diga 1/3, 1/3, 1/3 tiene Brier ≈ **0.667**.
  El tuyo debe estar claramente por debajo.
- También reportas **log-loss** (castiga más la confianza equivocada) y **RPS** (Ranked
  Probability Score, que respeta el orden home→draw→away: equivocarse por poco pesa menos).

---

## 8. El flujo de entrenamiento completo (lo que hace `train.py`)

```
1. Cargar corpus de partidos históricos + tabla de features de equipos   (pandas)
2. LOTO-CV grid search sobre (ridge_lambda × decay_rate)                  (validation.py)
   → elegir los mejores hiperparámetros por Brier Score
3. Entrenar el modelo FINAL con TODOS los datos y esos hiperparámetros    (fit → L-BFGS-B)
4. Sanity check: imprimir predicciones de 5 partidos representativos
5. Guardar el modelo entrenado → outputs/poisson_model.pkl               (pickle)
6. Guardar los mejores hiperparámetros → outputs/best_params.json
7. Imprimir el Top-10 de selecciones por parámetro de ataque (α)
```

Un `.pkl` (pickle) es el modelo **ya entrenado, congelado en disco**: la app lo carga y
predice al instante, **sin re-entrenar** cada vez.

---

## 9. La prueba de fuego: backtest temporal honesto

`evaluation/backtest_temporal.py` es tu evidencia de que el modelo **de verdad** funciona,
sin autoengaño. Para cada Mundial reciente (2010, 2014, 2018, 2022):
- Entrena **solo** con partidos **anteriores** al inicio de ese Mundial (sin *look-ahead*).
- Predice ese Mundial usando el **Elo point-in-time** (el de aquel momento, no el de hoy).
- Compara contra **dos baselines**: Elo-puro (point-in-time) y el naive (1/3, 1/3, 1/3).

Y reporta Brier / log-loss / RPS de los tres. **Si tu modelo no le gana claramente al naive
y al Elo-puro, no vale.** Este rigor es, quizá, el punto más "científico" de tu proyecto y
vale la pena destacarlo.

> **Frase para la diapositiva:** "No me creo mis propias predicciones: las pongo a prueba
> prediciendo Mundiales del pasado con datos que el modelo no había visto, y las comparo con
> métodos más simples. Solo si les gana, el modelo sirve."

---

## 10. Cómo "sigue aprendiendo" en vivo (updater.py)

El sistema no es estático durante el Mundial 2026. Cuando se registra un resultado real
(`updater.py`):
1. **Actualiza el Elo rodante** de ambos equipos con el sistema World Football Elo (K según
   la importancia del partido, factor por margen de goles, ventaja de local).
2. **Registra** el resultado y el Brier Score de esa predicción en `results_log.csv`.
3. **Re-entrena** el modelo de goles añadiendo el nuevo resultado al corpus, y actualiza el
   `.pkl`.

Es una forma de **aprendizaje incremental (online)**: el modelo mejora a medida que el
torneo avanza. (Ojo con el matiz de despliegue: en Streamlit Cloud el sistema de archivos es
efímero, así que en producción los cambios en vivo no persisten tras reiniciar; para
fijarlos hay que re-entrenar y versionar el `.pkl`.)

---

## El "cómo aprende" en un párrafo (memorízalo)
> "Le doy al modelo miles de partidos con su resultado real. Defino una función de error que
> mide cuánto se equivocan sus predicciones —la verosimilitud negativa— y un optimizador,
> L-BFGS-B de SciPy, ajusta todos los parámetros deslizándose cuesta abajo por esa función
> hasta minimizar el error. Le pongo un freno (regularización ridge) para que no memorice
> rarezas, doy más peso a los partidos recientes, y elijo los ajustes finos con validación
> cruzada dejando un torneo fuera cada vez. Finalmente lo pruebo prediciendo Mundiales
> pasados que no vio. Eso es aprender de los datos."

## Micro-glosario de esta sección
- **Verosimilitud (likelihood):** probabilidad que el modelo asigna a lo que sí ocurrió.
- **MLE:** estimación por máxima verosimilitud; el criterio de entrenamiento.
- **L-BFGS-B:** optimizador que minimiza el error "cuesta abajo", con límites.
- **Regularización (ridge/L2):** penalización que evita el sobreajuste.
- **Hiperparámetro:** ajuste que tú fijas antes de entrenar (ridge_lambda, decay_rate).
- **LOTO-CV / grid search:** validación cruzada dejando un torneo fuera / probar una rejilla.
- **Brier Score:** métrica de calidad de probabilidades (menor = mejor).
- **Backtest:** evaluar el modelo simulando el pasado sin mirar el futuro.
- **pickle (.pkl):** formato para guardar el modelo ya entrenado en disco.

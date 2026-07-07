# 04 · Python en la estadística: el ecosistema científico

> **Idea en una frase:** Python no es bueno para la estadística por sí solo — lo es por su
> **ecosistema de librerías** (NumPy, pandas, SciPy, statsmodels, matplotlib), un conjunto
> de herramientas que convierten a Python en un laboratorio de datos completo. **Tu
> proyecto está construido sobre exactamente estas librerías.**

Esta sección explica **qué hace cada pieza**, con la conexión directa a tu código, para
que la transición hacia "mi proyecto" sea natural.

---

## 1. El problema de fondo: Python "puro" es lento para números

Como Python es interpretado, hacer millones de operaciones matemáticas con listas
normales de Python sería **muy lento**. La comunidad científica resolvió esto con una
idea brillante:

> Escribir las partes que hacen números pesados **en C/Fortran** (rápido), y exponerlas
> con una interfaz **simple en Python** (legible).

Así obtienes lo mejor de dos mundos: **escribes** código sencillo y bonito, pero **corre**
casi a velocidad de C. Toda la "pila científica" (scientific stack) se basa en esto.

---

## 2. NumPy — el cimiento de todo

**Qué es:** la librería de **arreglos numéricos (arrays)**. Introduce el `ndarray`, una
estructura para manejar vectores y matrices de números de forma **vectorizada** (operas
sobre millones de números de golpe, sin bucles lentos).

**Analogía:** una lista de Python es como sumar recibos uno por uno con una calculadora;
un array de NumPy es como pasar todo el fajo por una máquina contadora de billetes.

```python
import numpy as np
precios = np.array([10, 20, 30])
precios * 1.16          # array([11.6, 23.2, 34.8]) — aplica el IVA a todos de una vez
```

**En tu proyecto:** NumPy está en todas partes. Ejemplos reales de tu código:
- `np.exp(log_lam)` para calcular los goles esperados λ (en `poisson_model.py`).
- `np.outer(...)` para construir la matriz de probabilidades de marcadores.
- `np.tril / np.triu / np.trace` para sumar las probabilidades de victoria/empate/derrota.

---

## 3. pandas — la hoja de cálculo con esteroides

**Qué es:** la librería de **DataFrames**, tablas etiquetadas (filas y columnas con
nombre), como una hoja de Excel pero programable y para millones de filas.

**Por qué importa en estadística:** el 80% del trabajo real de datos es **limpiar y
preparar** los datos. pandas hace eso: filtrar, agrupar, unir tablas (`merge`), rellenar
huecos, calcular columnas nuevas.

```python
import pandas as pd
df = pd.read_csv("partidos.csv")
df[df["year"] > 2010]                 # filtrar
df.groupby("equipo")["goles"].mean()  # promedio de goles por equipo
```

**En tu proyecto:** pandas es la columna vertebral del manejo de datos. Ejemplos reales:
- `pd.read_csv(MATCHES)` para cargar el corpus histórico de partidos (en `train.py`).
- `matches_df.iterrows()` para recorrer cada partido al construir las features.
- `teams_df.set_index("iso_code")` para indexar equipos por su código FIFA.
- Toda la convención de tu proyecto ("los DataFrames se guardan en `data/processed/`") gira
  en torno a pandas.

---

## 4. SciPy — las matemáticas y la estadística de verdad

**Qué es:** la caja de herramientas de **matemáticas avanzadas**: optimización,
estadística, álgebra lineal, distribuciones de probabilidad, integrales.

**Por qué importa:** aquí viven las **distribuciones estadísticas** y los **optimizadores**
que hacen que un modelo "aprenda".

**En tu proyecto SciPy es protagonista** (es literalmente donde ocurre el aprendizaje):
- `from scipy.stats import poisson` → la **distribución de Poisson** con la que modelas
  los goles. `poisson.pmf(g, lam)` te da la probabilidad de marcar `g` goles si esperas
  `lam`.
- `from scipy.optimize import minimize` → el **optimizador L-BFGS-B** que encuentra los
  mejores parámetros del modelo minimizando el error. **Esto es el "entrenamiento".**
  (Ver archivo 08.)

> **Frase clave:** "La parte de mi modelo que realmente *aprende* es una llamada a SciPy:
> `minimize(...)` con el método L-BFGS-B."

---

## 5. statsmodels — estadística clásica y econométrica

**Qué es:** modelos estadísticos "de manual" (regresiones lineales y logísticas, series
temporales, tests de hipótesis) con reportes detallados (p-valores, intervalos de
confianza), al estilo del software estadístico R.

**Dónde encaja:** cuando quieres **inferencia estadística** formal, no solo predicción.
Está en tu stack declarado como parte del ecosistema numérico del proyecto.

---

## 6. matplotlib / seaborn — visualización

**Qué es:** las librerías para **hacer gráficas** (líneas, barras, dispersión, mapas de
calor). "Una imagen vale más que mil filas de datos."

**En tu proyecto:** las usas para reportes y para la UI de fiabilidad del modelo (mapas de
calor de calibración, etc.). Están en tu stack de "Viz / notebooks".

---

## 7. Jupyter — el cuaderno del científico de datos

**Qué es:** un entorno interactivo (*notebooks*) donde mezclas **código, resultados,
gráficas y texto** en un mismo documento. Ideal para **explorar** datos y contar la
historia del análisis.

**En tu proyecto:** tienes una carpeta `notebooks/` justamente para exploración y
prototipado, siguiendo la filosofía de "construir bien, una fase a la vez".

---

## Cómo encajan las piezas (el flujo mental)

```
   Datos crudos (CSV)
        │  pandas  → cargar, limpiar, unir, features
        ▼
   Tabla ordenada (DataFrame)
        │  NumPy   → convertir a arrays, operar vectorizado
        ▼
   Arrays numéricos
        │  SciPy   → distribución de Poisson + optimizador L-BFGS-B  → APRENDIZAJE
        ▼
   Modelo entrenado (parámetros)
        │  matplotlib / Streamlit → mostrar predicciones y fiabilidad
        ▼
   Decisión / predicción legible
```

Este diagrama es **exactamente** el pipeline de tu proyecto, y es una gran diapositiva de
transición hacia la Parte C.

---

## Tabla resumen (para una diapositiva)

| Librería | Rol en una frase | En tu proyecto |
|---|---|---|
| **NumPy** | Números rápidos y vectorizados (arrays) | `np.exp`, `np.outer`, matrices de marcador |
| **pandas** | Tablas de datos (DataFrames) | Cargar y preparar el corpus de partidos |
| **SciPy** | Matemáticas/estadística avanzada | Distribución Poisson + optimizador (aprendizaje) |
| **statsmodels** | Estadística clásica / inferencia | Parte del stack numérico |
| **matplotlib/seaborn** | Gráficas | Reportes y UI de fiabilidad |
| **Jupyter** | Cuaderno interactivo | Carpeta `notebooks/` para explorar |

---

## El punto que amarra hacia el ML (archivo 05)

> "Estas mismas librerías —NumPy, pandas, SciPy— son también los **cimientos del machine
> learning**. Un modelo de ML no es magia: es estadística ejecutada sobre estos arrays a
> gran escala. Mi proyecto vive justo en la frontera entre la estadística clásica y el
> machine learning, y por eso es un buen ejemplo para entender ambos."

## Micro-glosario de esta sección
- **Array (ndarray):** vector/matriz de números de NumPy; se opera de golpe (vectorizado).
- **DataFrame:** tabla etiquetada de pandas (filas y columnas con nombre).
- **Vectorizar:** operar sobre todo un array a la vez en lugar de con bucles lentos.
- **Distribución de Poisson:** modelo de probabilidad para "cuántas veces ocurre algo raro
  en un intervalo" (ej. goles en un partido). Detalle en el archivo 07.
- **Optimizador:** algoritmo que busca los parámetros que minimizan un error (ej. L-BFGS-B).

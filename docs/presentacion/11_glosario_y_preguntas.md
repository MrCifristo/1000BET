# 11 · Glosario y banco de preguntas

Dos cosas para blindar tu presentación: un **glosario unificado** de todos los términos, y
un **banco de preguntas** probables (del profesor o compañeros) con respuestas listas.

---

## PARTE 1 · Glosario unificado

### Sobre el lenguaje Python
- **Interpretado:** el código se ejecuta al momento por un intérprete, sin compilar a un
  `.exe`. Python compila a un *bytecode* intermedio que ejecuta una máquina virtual (PVM).
- **Alto nivel:** cercano al lenguaje humano, lejos de los detalles del hardware.
- **Tipado dinámico:** no declaras el tipo de las variables; se determina en ejecución.
- **Tipado fuerte:** no mezcla tipos incompatibles a escondidas (`"3" + 5` da error).
- **Multiparadigma:** soporta programación estructurada, orientada a objetos y funcional.
- **Programación estructurada:** organizar el código en secuencia, condicionales y bucles,
  sin saltos caóticos.
- **POO (orientada a objetos):** organizar el código en objetos que unen datos y
  comportamiento (clases). Tu modelo es `class PoissonModel`.
- **Garbage collector:** el mecanismo que libera memoria automáticamente.
- **CPython:** la implementación estándar de Python (escrita en C).
- **BDFL:** *Benevolent Dictator For Life*, el rol histórico de Guido van Rossum.
- **PEP:** *Python Enhancement Proposal*, documento formal para cambios en Python.

### Sobre las librerías
- **NumPy:** arreglos numéricos rápidos (arrays), operaciones vectorizadas.
- **pandas:** tablas de datos etiquetadas (DataFrames).
- **SciPy:** matemáticas avanzadas: distribuciones estadísticas y optimización.
- **statsmodels:** modelos estadísticos clásicos e inferencia.
- **matplotlib / seaborn:** visualización (gráficas).
- **Streamlit:** framework para crear apps web de datos en puro Python (tu UI).
- **Jupyter:** cuadernos interactivos para explorar datos.

### Sobre machine learning
- **Modelo:** la "fórmula" con parámetros que hace predicciones.
- **Feature (característica):** variable de entrada (Elo, xG, valor, localía).
- **Parámetro:** número que el modelo **aprende** (α, β, μ…).
- **Hiperparámetro:** ajuste que **tú fijas** antes de entrenar (`ridge_lambda`, `decay_rate`).
- **Entrenar (fit):** ajustar los parámetros usando datos.
- **Función de pérdida / error:** lo que se minimiza al entrenar (aquí, −log-verosimilitud).
- **Overfitting (sobreajuste):** memorizar el ruido en vez del patrón; generaliza mal.
- **Regularización:** penalizar la complejidad para generalizar mejor (ridge/L2).
- **Validación cruzada:** evaluar el modelo en datos que no vio (tu LOTO-CV).
- **Aprendizaje supervisado:** aprender de ejemplos etiquetados (con la respuesta correcta).
- **Deep learning:** ML con redes neuronales profundas (tu modelo **no** es esto).
- **Interpretable:** modelo cuyos parámetros tienen significado humano (el tuyo lo es).

### Sobre tu modelo específico
- **Distribución de Poisson:** modela conteos de eventos raros (goles en un partido).
- **λ (lambda):** goles esperados (promedio) de un equipo en un partido.
- **Poisson bivariado:** modelar los goles de los dos equipos a la vez.
- **α / β (alpha/beta):** parámetros de fuerza de ataque / defensa, uno por selección.
- **μ, γ, δ, ε, ζ:** intercepto y coeficientes de local, Elo, xG y valor de plantilla.
- **Dixon-Coles / ρ (rho):** corrección (y su parámetro) para marcadores bajos frecuentes.
- **Elo:** puntuación dinámica de la fuerza de cada selección (viene del ajedrez).
- **Elo point-in-time:** el Elo que un equipo tenía **antes** de un partido (evita trampa).
- **xG (expected goals):** medida de la calidad de las ocasiones generadas.
- **L-BFGS-B:** el optimizador (de SciPy) que ajusta los parámetros minimizando el error.
- **Máxima verosimilitud (MLE):** el criterio de entrenamiento: maximizar la probabilidad
  que el modelo asigna a lo que realmente pasó.
- **Ridge (L2):** la regularización que evita el sobreajuste.
- **LOTO-CV:** *Leave-One-Tournament-Out*, tu validación cruzada dejando un torneo fuera.
- **Brier Score:** métrica de calidad de probabilidades (menor = mejor; naive ≈ 0.667).
- **Backtest temporal:** evaluar el modelo prediciendo el pasado sin mirar el futuro.
- **pickle (.pkl):** formato para guardar el modelo ya entrenado en disco.
- **1X2:** la triple resultado local / empate / visitante.
- **Props / over-under:** mercados de conteo (córners, tarjetas…) por encima/debajo de una línea.

---

## PARTE 2 · Banco de preguntas probables (con respuestas)

### Sobre Python
**P: ¿Por qué Python es lento y aun así se usa tanto?**
> R: Es lento en cálculo puro porque es interpretado, pero las librerías científicas (NumPy,
> pandas) están escritas por dentro en C. Python "orquesta" y el trabajo pesado corre a
> velocidad de C. Y el tiempo del programador vale más que unos milisegundos de CPU.

**P: ¿Compilado o interpretado?**
> R: Interpretado. Más en detalle: se compila a un *bytecode* intermedio que ejecuta una
> máquina virtual, pero no genera un ejecutable nativo como C.

**P: ¿Es Python de tipado fuerte o débil?**
> R: Fuerte (no mezcla tipos a escondidas) y a la vez dinámico (no declaras los tipos). Son
> dos ejes distintos.

**P: ¿Por qué la indentación es obligatoria?**
> R: Es una decisión de diseño para forzar código legible: los bloques se definen por
> sangría en vez de llaves, así todo el código luce ordenado.

### Sobre machine learning
**P: ¿Tu proyecto es inteligencia artificial / machine learning?**
> R: Es *machine learning interpretable*. Aprende parámetros de los datos como el ML (tiene
> features, función de pérdida, regularización, validación cruzada), pero es un modelo
> estadístico paramétrico, no una red neuronal. Cada parámetro significa algo real.

**P: ¿Por qué no usaste una red neuronal / deep learning?**
> R: Para este problema, con datos tabulares y relativamente pocos (miles de partidos, no
> millones), un modelo estadístico bien diseñado suele igualar o superar a una red neuronal,
> y encima es **interpretable** y no necesita GPUs. La red sería una caja negra sin ventaja
> clara aquí.

**P: ¿Qué es "entrenar" exactamente?**
> R: Buscar los valores de los parámetros que hacen que las predicciones se parezcan lo más
> posible a los resultados reales. Lo hace un optimizador (L-BFGS-B) minimizando una función
> de error (la verosimilitud negativa).

### Sobre el modelo
**P: ¿Por qué Poisson y no otra distribución?**
> R: Porque los goles son eventos discretos y raros a lo largo del partido, que es
> exactamente lo que modela la distribución de Poisson. Es el estándar en el modelado de
> fútbol desde los años 80 (Maher 1982).

**P: ¿Qué añade Dixon-Coles?**
> R: La Poisson pura subestima los empates apretados (0-0, 1-1). Dixon-Coles añade un solo
> parámetro (ρ) que reajusta esos cuatro marcadores bajos para pegar mejor con la realidad.

**P: ¿Cómo evitas que el modelo haga trampa mirando el futuro?**
> R: En el backtest entreno solo con partidos anteriores al torneo evaluado y uso el Elo
> *point-in-time* (el de aquel momento). Sin eso, las métricas serían mentira.

**P: ¿Qué tan bueno es? ¿Le atina a los resultados?**
> R: No predice el ganador exacto —eso es imposible en el fútbol—, predice **probabilidades**
> bien calibradas. Se mide con el Brier Score, y se compara contra un modelo Elo-puro y uno
> naive (1/3). Solo vale si les gana. Acertar el marcador exacto tiene un techo realista de
> ~9-12% incluso para el mejor marcador; eso es normal.

**P: ¿De dónde salen los datos?**
> R: De fuentes abiertas de fútbol: StatsBomb, openfootball, resultados internacionales de
> martj42, FBref, y estimaciones curadas de valor de plantilla. Se descargan y procesan con
> los scripts de `src/ingestion/`.

**P: ¿Puede predecir cualquier partido o solo del Mundial?**
> R: El modelo aprende de partidos internacionales de muchas selecciones, así que puede
> estimar cualquier cruce entre selecciones que conozca; la app se enfoca en el Mundial 2026.

**P: ¿Se actualiza con resultados nuevos?**
> R: Sí. Al registrar un resultado real, actualiza el Elo, guarda la predicción y re-entrena
> el modelo de goles. Es aprendizaje incremental durante el torneo.

### Preguntas "trampa" o difíciles
**P: Si es solo estadística, ¿qué mérito tiene?**
> R: El mérito está en el sistema completo y el rigor: ingeniería de datos, un modelo bien
> fundamentado con correcciones (Dixon-Coles, Elo, regularización), validación honesta sin
> look-ahead, y una app usable. Construir algo simple que **de verdad funciona y se puede
> auditar** es más difícil que apilar una red neuronal.

**P: ¿Podrías ganar dinero apostando con esto?**
> R: El modelo estima probabilidades "justas"; para ganar apostando tendrías que superar
> consistentemente el margen de las casas de apuestas, que también tienen modelos muy
> buenos. El objetivo aquí es académico y de modelado, no financiero.

**P: ¿Cuánto código escribiste tú y cuánto es librería?**
> R: Las librerías (SciPy, pandas) dan las piezas base, pero el **modelo** —la fórmula de λ,
> la función de verosimilitud, la corrección Dixon-Coles, el motor de torneo, la validación—
> está implementado a mano. No llamé a una caja negra de ML; programé el aprendizaje.

---

## PARTE 3 · Frases de rescate (si te bloqueas)
- "Buena pregunta — déjame mostrarte en el código / en la app." (y vuelves a terreno firme)
- "Eso lo verifico con el dato exacto y te lo confirmo después." (mejor que inventar)
- "En una frase: el modelo estima cuántos goles esperar de cada equipo, y de ahí salen todas
  las probabilidades." (tu resumen ancla, siempre válido)

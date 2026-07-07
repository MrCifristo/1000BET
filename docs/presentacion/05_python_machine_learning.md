# 05 · Python y el Machine Learning (deep dive)

> **Idea en una frase:** el machine learning es el arte de **hacer que un programa aprenda
> patrones de los datos en lugar de programarle las reglas a mano**, y Python es el idioma
> universal en el que hoy se hace ese aprendizaje. Tu proyecto es un ejemplo concreto y
> transparente de esta idea.

Esta es la sección más importante conceptualmente. Va de menos a más: qué es ML → tipos →
por qué Python domina → ecosistema → el puente hacia tu modelo.

---

## 1. ¿Qué es el Machine Learning? (la intuición central)

**Programación tradicional:** tú escribes las **reglas**, la computadora te da la
**respuesta**.
> Reglas + Datos → Respuestas

**Machine Learning:** tú le das **datos y respuestas (ejemplos)**, y la computadora
**descubre las reglas** sola.
> Datos + Respuestas → **Reglas (el modelo)**

**Analogía del niño y las manzanas:** no le enseñas a un niño a reconocer una manzana con
una lista de reglas ("si es roja y redonda y mide 8 cm..."). Le muestras **muchas
manzanas** y su cerebro **extrae el patrón**. El ML hace lo mismo con datos.

**Definición formal (memorizable):** un programa "aprende" de la experiencia **E** en una
tarea **T** medida por un desempeño **P**, si su desempeño en T (medido por P) mejora con
la experiencia E. *(Tom Mitchell, 1997.)*

- En **tu proyecto**: **T** = predecir el resultado de un partido; **E** = miles de
  partidos internacionales históricos; **P** = el *Brier Score* (qué tan buenas son tus
  probabilidades). El modelo ajusta sus parámetros para minimizar ese error.

---

## 2. Los tipos de Machine Learning

### 2.a. Aprendizaje supervisado (el más común)
Aprendes de ejemplos **etiquetados** (con la respuesta correcta).
- **Clasificación:** la respuesta es una categoría. *¿Este correo es spam o no?*
- **Regresión:** la respuesta es un número. *¿Cuántos goles marcará este equipo?*

> **Tu modelo es esencialmente aprendizaje supervisado de tipo regresión:** aprende de
> partidos con resultado conocido (etiqueta = goles reales) a predecir los goles esperados
> de partidos futuros.

### 2.b. Aprendizaje no supervisado
Aprendes de datos **sin etiquetas**; buscas estructura oculta.
- **Clustering:** agrupar clientes parecidos sin saber de antemano los grupos.

### 2.c. Aprendizaje por refuerzo
Un agente aprende por **prueba y error** con recompensas y castigos.
- **Ejemplo:** AlphaGo aprendiendo a jugar Go; un robot aprendiendo a caminar.

### 2.d. Deep Learning (aprendizaje profundo) — subconjunto transversal
Usa **redes neuronales** con muchas capas. Es lo que hay detrás de ChatGPT, el
reconocimiento facial y los coches autónomos. Necesita **muchísimos datos** y **mucho
cómputo** (GPUs).

> **Sitúa tu proyecto con honestidad:** tu modelo **no** es deep learning. Es un **modelo
> estadístico paramétrico** (Poisson) entrenado por máxima verosimilitud. Esto es una
> **fortaleza** para explicar en clase, no una debilidad: es **interpretable** (cada
> parámetro significa algo real, como "la fuerza de ataque de Brasil"), mientras que una
> red neuronal es una "caja negra". Ver el matiz en la sección 6.

---

## 3. El vocabulario esencial del ML (para que hables con propiedad)

| Término | Qué significa | En tu proyecto |
|---|---|---|
| **Modelo** | La "fórmula" con parámetros que hace predicciones | Tu Poisson bivariado |
| **Features** (características) | Las variables de entrada | Elo, xG, valor de plantilla, localía |
| **Parámetros** | Los números que el modelo aprende | α (ataque), β (defensa), μ, γ, δ… |
| **Hiperparámetros** | Ajustes que tú fijas antes de entrenar | `ridge_lambda`, `decay_rate` |
| **Entrenar (fit)** | Ajustar los parámetros con datos | `model.fit(...)` |
| **Función de pérdida** | El error que se minimiza | −log-verosimilitud + ridge |
| **Overfitting** | Memorizar el ruido en vez de aprender el patrón | Lo controlas con regularización |
| **Regularización** | Penalizar la complejidad para generalizar mejor | Ridge (L2) sobre α y β |
| **Validación cruzada** | Probar el modelo en datos que no vio | LOTO-CV |

Estos términos reaparecen en los archivos 07 y 08 aplicados a tu código.

---

## 4. ¿Por qué Python DOMINA el machine learning?

No fue casualidad. Convergieron varias razones:

1. **Legibilidad y velocidad de prototipado.** La investigación en ML es prueba y error
   constante. Python deja **iterar rápido** ideas matemáticas (ver archivo 01).
2. **El ecosistema numérico ya existía.** NumPy, pandas y SciPy (archivo 04) dieron los
   cimientos: las redes neuronales son, por dentro, multiplicaciones de matrices sobre
   arrays de NumPy.
3. **Las grandes librerías de ML se construyeron en Python.** scikit-learn, TensorFlow
   (Google) y PyTorch (Meta) tienen su interfaz principal en Python.
4. **"Python orquesta, C/CUDA ejecuta".** Escribes Python legible, pero el cálculo pesado
   corre en C optimizado o en la **GPU** (vía CUDA). Lo mejor de ambos mundos.
5. **Comunidad y datos.** Repositorios (Hugging Face), tutoriales, cursos y foros: la masa
   crítica atrae más masa crítica (efecto de red).

> **Frase para la diapositiva:** "Python ganó el ML no por ser el más rápido, sino por ser
> el más **fácil de investigar** — y el resto del mundo lo siguió."

---

## 5. El ecosistema de ML en Python (mapa rápido)

| Librería | Para qué sirve | Nivel |
|---|---|---|
| **scikit-learn** | ML "clásico": regresión, clasificación, clustering, validación | Ideal para empezar |
| **TensorFlow / Keras** | Deep learning (Google) | Producción a gran escala |
| **PyTorch** | Deep learning (Meta) | El favorito de la investigación |
| **Hugging Face** | Modelos pre-entrenados (lenguaje, visión) | IA moderna lista para usar |
| **XGBoost / LightGBM** | Árboles con *gradient boosting* (top en datos tabulares) | Competiciones (Kaggle) |
| **SciPy / statsmodels** | Estadística y optimización (la base) | Modelos estadísticos como el tuyo |

> **Nota honesta y útil para ti:** tu proyecto **no** usa scikit-learn ni PyTorch. Usa
> **SciPy** directamente porque construiste el modelo estadístico **a mano** (definiendo su
> verosimilitud y optimizándola). Eso es *más* impresionante para explicar en una clase de
> fundamentos: no llamaste a una caja negra, **programaste el aprendizaje desde cero**.

---

## 6. El puente hacia TU proyecto: ¿estadística clásica o machine learning?

Esta es una pregunta que puede surgir, y tienes una respuesta excelente:

> **La frontera entre "modelo estadístico" y "machine learning" es difusa, y tu proyecto
> vive justo encima de ella.**

- **Se parece al ML clásico** porque: aprende parámetros de datos (`fit`), tiene features,
  usa una función de pérdida, se regulariza para evitar overfitting y se valida con
  validación cruzada. Todo el *vocabulario* del ML aplica.
- **Se parece a la estadística clásica** porque: el modelo es **paramétrico e
  interpretable** (asume una distribución de Poisson y cada parámetro tiene un significado
  real), no es una red neuronal opaca.

**Cómo decirlo en clase (posición ganadora):**
> "Mi modelo es *machine learning interpretable*: aprende de los datos como un modelo de ML,
> pero cada número que aprende **significa algo** —la fuerza de ataque de un equipo, la
> ventaja de jugar en casa—. No es una caja negra; es un modelo que puedo explicar línea
> por línea. Y eso es exactamente lo que voy a hacer ahora."

Esa frase es la **transición perfecta** a la Parte C (tu proyecto).

---

## Errores comunes que conviene NO cometer al explicar ML
- ❌ "La IA piensa/entiende." → ✅ "Detecta patrones estadísticos en datos."
- ❌ "Más datos siempre es mejor." → ✅ "Mejores datos y evitar overfitting es lo clave."
- ❌ "El modelo acierta el resultado." → ✅ "El modelo estima **probabilidades**; en fútbol,
  el favorito pierde a menudo, y eso es correcto que ocurra."

## Micro-glosario de esta sección
- **Etiqueta (label):** la respuesta correcta de un ejemplo en aprendizaje supervisado.
- **Feature:** variable de entrada que describe cada caso.
- **Overfitting:** cuando el modelo memoriza el ruido y falla con datos nuevos.
- **Red neuronal:** modelo de ML inspirado en el cerebro, base del deep learning.
- **GPU/CUDA:** hardware y plataforma para acelerar el cálculo de ML en paralelo.
- **Interpretable:** un modelo cuyos parámetros tienen significado entendible por humanos.

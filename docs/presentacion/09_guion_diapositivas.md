# 09 · Guion de diapositivas (slide por slide)

> Estructura para ~15–20 min. Cada diapositiva trae: **título**, **qué mostrar en la
> diapo** y **notas del orador** (lo que dices). Ajusta el número de slides al tiempo real
> de tu clase. Los ⏱️ son tiempos aproximados acumulables.

**Regla de oro:** poco texto en la diapositiva, la explicación va en tu voz (estas notas).
Una idea por slide. Usa las tablas y diagramas de los archivos 01–08 como imágenes.

---

## SECCIÓN 0 — Apertura

### Slide 1 · Portada ⏱️ 0:30
- **Diapo:** Título "Python y la predicción del Mundial 2026", tu nombre, la clase. Una
  imagen del logo del proyecto / un balón / bandera de los 3 anfitriones.
- **Notas:** "Hoy les voy a mostrar qué es Python, por qué se comió el mundo de los datos y
  la IA, y cómo lo usé para construir un sistema que predice partidos del Mundial 2026. Al
  final, lo verán funcionando en vivo."

### Slide 2 · El gancho ⏱️ 0:45
- **Diapo:** una pregunta grande: "¿Se puede predecir un partido de fútbol con matemáticas?"
- **Notas:** "No con certeza —el fútbol es incierto, por eso nos gusta—, pero sí con
  **probabilidades**. Y la herramienta para hacerlo es Python. Empecemos por el lenguaje."

---

## SECCIÓN A — Python (lo general) · fuente: archivos 01–04

### Slide 3 · ¿Qué es Python? (ficha técnica) ⏱️ 2:00
- **Diapo:** la **tabla resumen** del archivo 01 (propósito, nivel, interpretado, tipado,
  paradigmas, memoria).
- **Notas:** recorre los términos con una analogía cada uno: alto nivel = "hablas humano,
  no máquina"; interpretado = "intérprete simultáneo, no traducir el libro entero"; tipado
  dinámico pero fuerte = "no declaras tipos, pero no mezcla peras con manzanas";
  multiparadigma = "estructurado **y** orientado a objetos". (Detalle en archivo 01.)

### Slide 4 · Historia ⏱️ 1:30
- **Diapo:** la **línea de tiempo** del archivo 02 (1989 → hoy).
- **Notas:** "Nació como un proyecto de Navidad de Guido van Rossum en 1989. Se llama así
  por Monty Python, no por la serpiente. Su superpoder no fue la velocidad: fue ser **fácil
  de leer**. Eso lo hizo perfecto para científicos, y así conquistó los datos y la IA."

### Slide 5 · ¿Para qué se usa? ⏱️ 1:15
- **Diapo:** la **tabla de dominios** del archivo 03 con casos reconocibles (Instagram,
  ChatGPT, Netflix, la imagen del agujero negro).
- **Notas:** "Está en todas partes: web, automatización, ciencia, finanzas y —sobre todo—
  inteligencia artificial. Ya lo usas todos los días sin saberlo."

### Slide 6 · Python + estadística ⏱️ 1:30
- **Diapo:** el **diagrama de flujo** del archivo 04 (pandas → NumPy → SciPy → visualización).
- **Notas:** "Python no es bueno en estadística por sí solo, sino por su **ecosistema**:
  pandas para las tablas, NumPy para los números rápidos, SciPy para la estadística de
  verdad. Estas mismas librerías son la base de mi proyecto."

---

## SECCIÓN B — Machine Learning · fuente: archivo 05

### Slide 7 · ¿Qué es el Machine Learning? ⏱️ 1:30
- **Diapo:** el contraste visual: "Programación clásica: Reglas + Datos → Respuestas" vs
  "ML: Datos + Respuestas → **Reglas**". La analogía del niño y las manzanas.
- **Notas:** "En la programación normal yo escribo las reglas. En machine learning le doy
  ejemplos a la máquina y ella **descubre las reglas sola**. Como un niño que aprende qué
  es una manzana viendo muchas, no leyendo una definición."

### Slide 8 · Por qué Python domina el ML ⏱️ 1:15
- **Diapo:** el **mapa del ecosistema** (scikit-learn, PyTorch, TensorFlow) + las 5 razones
  del archivo 05.
- **Notas:** "Python ganó el ML no por ser el más rápido, sino por ser el más **fácil de
  investigar**: el ecosistema numérico ya existía, y encima 'Python orquesta, la GPU
  ejecuta'. El mundo entero lo siguió."

### Slide 9 · ¿Mi modelo es ML? (el puente) ⏱️ 1:00
- **Diapo:** una balanza: "Estadística clásica ⟷ Machine Learning", con tu proyecto en el
  medio.
- **Notas:** "Mi modelo vive justo en la frontera: aprende de datos como el ML, pero cada
  parámetro **significa algo real**. Es *machine learning interpretable*, no una caja
  negra. Y ahora se los muestro."

---

## SECCIÓN C — Tu proyecto · fuente: archivos 06–08

### Slide 10 · Qué hace mi proyecto ⏱️ 1:00
- **Diapo:** captura de la app + bullets: probabilidades 1X2, goles esperados, marcador
  probable, props, simulación del torneo.
- **Notas:** guion de 30–45 s del final del archivo 06 ("no es solo una fórmula, es un
  sistema completo…").

### Slide 11 · Arquitectura / pipeline ⏱️ 1:00
- **Diapo:** el **diagrama del pipeline** del archivo 06 (ingestion → features → model →
  evaluation → tournament → UI).
- **Notas:** "Un solo lenguaje me lleva de los datos crudos a la app: descargo, limpio,
  entreno, evalúo y publico. Todo en Python."

### Slide 12 · Cómo funciona el modelo ⏱️ 2:00
- **Diapo:** la fórmula `log(λ) = μ + α − β + γ·host + δ·elo + ε·xg + ζ·valor` con cada
  término etiquetado (tabla del archivo 07). Y una frase sobre Poisson.
- **Notas:** guion de 60–90 s del archivo 07 ("los goles son eventos raros → Poisson →
  todo se reduce a estimar bien lambda → cada parámetro significa algo").

### Slide 13 · Cómo aprende / se entrena ⏱️ 2:00
- **Diapo:** el ciclo: "Datos históricos → función de error (verosimilitud) → optimizador
  L-BFGS-B baja el error → parámetros aprendidos". Menciona ridge + LOTO-CV + backtest.
- **Notas:** el párrafo "el cómo aprende en un párrafo" del archivo 08. Enfatiza:
  "lo que realmente aprende es una llamada a `minimize()` de SciPy".

### Slide 14 · ¿Funciona? (honestidad) ⏱️ 1:00
- **Diapo:** tabla del **backtest temporal**: Modelo vs Elo-puro vs Naive (Brier / log-loss
  / RPS). (Puedes generar los números reales corriendo `backtest_temporal.py`.)
- **Notas:** "No me creo mis predicciones: pruebo el modelo prediciendo Mundiales pasados
  con datos que no vio, y solo vale si le gana a métodos más simples."

---

## SECCIÓN D — Demo y cierre

### Slide 15 · DEMO EN VIVO ⏱️ 3:00–4:00
- **Diapo:** solo el título "Demo en vivo" (cambias a la app). Ten una **captura de
  respaldo** por si falla el Wi-Fi/entorno (plan B en archivo 10).
- **Notas:** sigue el **archivo 10** paso a paso.

### Slide 16 · Conclusiones ⏱️ 1:00
- **Diapo:** 3 bullets: (1) Python = un lenguaje para todo el recorrido de datos; (2) ML =
  aprender reglas de los datos; (3) mi proyecto = estadística interpretable de punta a
  punta.
- **Notas:** "Python me dejó ir de una idea matemática a una app funcional sin cambiar de
  herramienta. Eso es lo que lo hace el lenguaje de la ciencia de datos moderna."

### Slide 17 · Gracias + preguntas ⏱️ 0:30
- **Diapo:** "¿Preguntas?" + tu contacto / repo.
- **Notas:** ten a mano el **archivo 11** (banco de preguntas y respuestas).

---

## Checklist de tiempos (para no pasarte)

| Sección | Slides | Tiempo |
|---|---|---|
| Apertura | 1–2 | ~1:15 |
| A · Python general | 3–6 | ~6:15 |
| B · Machine Learning | 7–9 | ~3:45 |
| C · Tu proyecto | 10–14 | ~7:00 |
| D · Demo + cierre | 15–17 | ~5:00 |
| **Total** | 17 | **~23 min** (recorta A o C si necesitas 15) |

> **Si tienes solo 15 minutos:** funde los slides 5–6 en uno, y 8–9 en uno; recorta la demo
> a un solo partido. La Sección C y la demo son el corazón: no las sacrifiques.

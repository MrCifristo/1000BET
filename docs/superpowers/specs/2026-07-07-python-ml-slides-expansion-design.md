# Diseño — Expansión de las secciones Python y Machine Learning del deck

**Fecha:** 2026-07-07
**Autor:** Milton Beltrán (con Claude Code)
**Ámbito:** `docs/presentacion/deck-react/` (deck React) + `docs/presentacion/GUION_PRESENTADOR.md` (guion hablado)

## Objetivo

Convertir Python y Machine Learning en el núcleo expositivo de la presentación
"Evolution of Computing", agregando profundidad y contenido, y comprimir la parte de
proyecto porque se presenta como **demo en vivo**. El proyecto queda representado por una
slide de mapeo (concepto → repositorio) más la slide del modelo λ como pico técnico.

## Decisiones de alcance (acordadas con el usuario)

- **Registro:** universitario accesible, con **picos técnicos avanzados puntuales** (no como
  estándar). Se conservan las buenas analogías; se evita lo infantil y las definiciones obvias.
- **Superficies a modificar:** el **deck React** (`src/slides.jsx` + componentes) y el
  **guion** (`GUION_PRESENTADOR.md`), en lockstep. No se toca `presentacion.html` ni el banco
  de notas `01`–`12` en esta iteración.
- **Tiempo:** flexible (piso ~5 min de exposición, puede crecer a 8–12 si el contenido lo
  justifica). El proyecto es una demo presencial.
- **Temas nuevos de Python:** un fragmento de **código real** en pantalla.
- **Temas nuevos de ML:** tipos de aprendizaje, sobreajuste/generalización, y el espectro
  clásico → redes → LLMs.
- **Proyecto:** una sola slide de mapeo concepto→repo, **más** la slide del modelo λ
  (Poisson) conservada como pico técnico antes de la demo.

## Estructura final del deck (17 slides)

Leyenda: ⭐ nueva · ✎ reescrita/reencuadrada · · se mantiene (con ajustes de registro ya hechos).

```
APERTURA
 1 ·  Título
 2 ✎  Agenda (rebalanceada: Python · ML · demo)

ACTO I — PYTHON (6)
 3 ·  ¿Qué es Python?  (ficha técnica)
 4 ⭐ Código real en pantalla
 5 ·  Interpretado vs compilado
 6 ·  Historia
 7 ·  Usos en el mundo real
 8 ·  Su fuerza: el ecosistema

ACTO II — MACHINE LEARNING (5)
 9 ·  Aprender reglas, no programarlas
10 ·  ML en tu día a día
11 ⭐ Tipos de aprendizaje
12 ⭐ Sobreajuste y generalización
13 ⭐ Clásico vs. redes / LLMs

ACTO III — PROYECTO → DEMO (4)
14 ✎  El proyecto: qué es + cómo Python/ML viven en el repo (una slide)
15 ·  El modelo: estimar λ (Poisson)  ← pico técnico conservado
16 ·  Demo en vivo
17 ✎  Cierre (recap actualizado)
```

**Se eliminan** del deck original: `PipelineSlide`, `ProbabilitySlide` (¿cómo se lee una
predicción?) y `TrainingSlide` (backtest). Su esencia se absorbe en la slide de proyecto (14),
en la demo, y en la charla de ML (sobreajuste → #12).

## Componentes nuevos (en `src/components/`)

1. **`CodeBlock`** — bloque monoespaciado con coloreado sutil de sintaxis (por tokens, sin
   dependencias externas), soporte de resaltado de líneas y 2–3 anotaciones tipo callout.
   Reutiliza el estilo `glass` y la paleta existente (`text-py`, `text-goal`, `text-dim`).
2. **`FitCurves`** — SVG con tres mini-paneles (subajuste · buen ajuste · sobreajuste): puntos
   dispersos + una curva. Sin librerías; paths SVG calculados en `lib/math.js` o inline.
3. **`Spectrum`** — eje horizontal con marcadores posicionados y dos polos anotados
   (interpretable/pocos datos ↔ caja negra/millones de datos).

Los tres siguen el patrón de los componentes actuales (animación con `framer-motion`, clases
Tailwind del tema). No se agregan dependencias npm.

## Detalle por slide

### 2 ✎ Agenda
Tres bloques en lugar de cuatro:
- **01 · Python** — qué es, cómo se lee su código y por qué reina en datos.
- **02 · Machine Learning** — cómo una máquina aprende de los datos.
- **03 · El proyecto, en vivo** — predecir el Mundial 2026.

### 4 ⭐ Código real en pantalla
- **Kicker:** `01 · El lenguaje`. **Título:** "El código se lee casi solo".
- **Bajada:** "Un fragmento real de mi proyecto. Aunque no programes, casi se entiende qué hace."
- **Cuerpo:** excerpt fiel de `src/model/poisson_model.py::_lambda` (~10 líneas), recortado a
  las líneas más legibles. Anotaciones sobre:
  - `host_flag = 1.0 if iso_att == host_iso else 0.0` → "se lee casi como inglés".
  - la suma aditiva `log_lam = mu + alpha − beta + …` → "esto ES la fórmula del modelo".
- **Pico avanzado (nota al pie):** "Python traduce esto a un formato intermedio (*bytecode*)
  que ejecuta su máquina virtual, CPython — por eso corre al instante, sin compilar."
- **Componente:** `CodeBlock`.

### 11 ⭐ Tipos de aprendizaje
- **Kicker:** `04 · Machine Learning`. **Título:** "Tres formas de aprender".
- **Tres tarjetas** (reutiliza `Card`/`Panel`):
  - **Supervisado** — aprende de ejemplos con respuesta. Ej.: spam, precios. Badge:
    **"aquí cae mi modelo: partidos pasados con su marcador."**
  - **No supervisado** — halla patrones sin respuestas. Ej.: agrupar clientes.
  - **Por refuerzo** — aprende por premio/castigo. Ej.: AlphaGo, robots que caminan.
- **Remate:** resalta "supervisado" para ubicar el proyecto en el mapa.

### 12 ⭐ Sobreajuste y generalización
- **Kicker:** `04 ·`. **Título:** "Memorizar no es aprender".
- **Bajada:** "Un modelo que memoriza el pasado al pie de la letra falla con lo nuevo. La meta
  es **generalizar**."
- **Visual:** `FitCurves` — subajuste · buen ajuste · sobreajuste.
- **Conexión:** "Por eso separo los datos: entreno con unos partidos y pruebo con **otros que
  nunca vio**, y le pongo un freno (regularización)."

### 13 ⭐ Clásico vs. redes / LLMs
- **Kicker:** `04 ·`. **Título:** "Del modelo simple al LLM".
- **Visual:** `Spectrum` de *interpretable / pocos datos* → *caja negra / millones de datos*,
  con marcadores: clásicos (Poisson, regresión, árboles) · redes neuronales · deep learning ·
  **LLMs (ChatGPT)**.
- **Polos:** izquierda "cada número significa algo — **mi modelo vive aquí**"; derecha "enorme
  capacidad, caja negra — ChatGPT".
- **Remate (por qué Poisson y no una red):** "Con miles de partidos —no millones— un modelo
  interpretable rinde igual o mejor, y **puedo explicar cada número**. Una red sería una caja
  negra con más riesgo de sobreajuste."

### 14 ✎ El proyecto (una slide)
- **Kicker:** `05 · El proyecto`. **Título:** "Todo esto, en un solo repo".
- **Bajada:** "Un sistema que predice partidos del Mundial 2026 y simula el torneo. Aquí es
  donde el Python y el machine learning que vimos cobran vida."
- **Cuerpo — mapa concepto → archivo:**

  | Lo que presentamos | Dónde vive |
  |---|---|
  | pandas · numpy (datos y features) | `src/ingestion/` · `src/features/` |
  | scipy: Poisson + optimizador | `src/model/poisson_model.py` · `train.py` |
  | Aprendizaje supervisado | entrena con miles de partidos reales |
  | Generalización / no sobreajuste | `src/evaluation/backtest_temporal.py` |
  | ML interpretable (Poisson·Dixon-Coles·Elo) | `src/model/` |
  | Streamlit (la app de la demo) | `src/ui/app.py` |

- **Cierre:** "Y ahora lo vemos funcionando." → transición a modelo λ / demo.

### 15 · El modelo: estimar λ  (conservada)
Se mantiene `ModelSlide` tal cual (Poisson + `Formula` + `PoissonBars` + leyenda). Sirve de
pico técnico y conecta con el snippet de la slide 4 (misma fórmula).

### 17 ✎ Cierre
Recap actualizado al nuevo énfasis:
1. **Python** — un lenguaje legible que cubre todo el recorrido, de los datos a la app.
2. **Machine learning** — aprender reglas de los datos, no programarlas.
3. **Interpretabilidad** — cada número del modelo significa algo; no es una caja negra.

## Guion (`GUION_PRESENTADOR.md`)

Se actualiza en lockstep con el deck:
- Reescribir la sección de agenda (2) a tres bloques.
- Agregar guiones para las 4 slides nuevas (código real, tipos de aprendizaje, sobreajuste,
  espectro): qué se ve, qué decir, dato extra / si preguntan, transición.
- Eliminar los guiones de Pipeline, Probabilidad y Entrenamiento/backtest; reubicar sus datos
  útiles (backtest, calibración) al banco de "preguntas difíciles" al final del guion, para que
  no se pierdan como respaldo ante preguntas.
- Renumerar las secciones del guion para que coincidan con las 17 slides.

## No-objetivos (YAGNI)

- No se tocan `presentacion.html` ni los markdown `01`–`12` en esta iteración.
- No se agregan dependencias npm ni librerías de resaltado de sintaxis (el coloreado del
  `CodeBlock` se hace a mano por tokens).
- No se añaden los picos de CPython/GIL ni descenso de gradiente como slides propias; viven
  como notas al pie dentro de slides existentes.

## Criterio de éxito

- El deck compila (`vite build`) sin errores.
- Python + ML suman 11 de 17 slides; el proyecto ocupa 1 slide de mapeo + la del modelo λ.
- Las 4 slides nuevas usan datos/afirmaciones correctas y el mapeo concepto→repo apunta a
  archivos que existen de verdad.
- El guion queda coherente y renumerado con el nuevo orden.

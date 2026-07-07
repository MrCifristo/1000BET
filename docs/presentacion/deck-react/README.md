# Deck — Python y la predicción del Mundial 2026

Presentación interactiva (React + Vite + Tailwind + Framer Motion) para la clase
"Evolution of Computing". Look cinematográfico, transiciones dirigidas y gráficos
calculados con matemática real (Poisson, mapa de calor, backtest con cifras reales).

## Cómo correrla

```bash
cd docs/presentacion/deck-react
npm install
npm run dev
```

Abre la URL que imprime Vite (normalmente http://localhost:5173).

## Presentar en clase

- Navega con **← →**, **barra espaciadora**, los **puntos** de abajo, o **swipe** en móvil.
- **F** (o el botón ⛶) activa **pantalla completa** — aquí sí funciona, porque corre en una
  pestaña real del navegador y no dentro de un iframe restringido.
- Para proyector: entra en pantalla completa y, si quieres ocultar la barra del navegador, F11.

## Estructura

```
src/
  App.jsx              # orquesta slides + transiciones (AnimatePresence)
  slides.jsx           # las 10 diapositivas + registro SLIDES
  index.css            # fondo cinematográfico, grano, fuentes, glass
  hooks/useDeck.js     # navegación por teclado + pantalla completa
  lib/math.js          # Poisson, matriz de marcadores, escala de calor
  components/
    Chrome.jsx         # barra superior, progreso, dots, navegación
    ui.jsx             # primitivas (Kicker, Chip, Bullet, Panel, Stagger, contador)
    viz.jsx            # gráficos (Poisson, Heatmap, Timeline, Formula, Odds, Backtest)
```

## Editar contenido

Todo el texto y los datos viven en `src/slides.jsx` (arrays `SPEC`, `TL`, `BACKTEST`,
`ODDS`, `RECAP`). Los números del backtest (`BACKTEST`) salen de
`src/evaluation/backtest_temporal.py` del proyecto Python: 256 partidos, Brier ↓.

## Imágenes que puedes añadir
- **Demo (slide 9):** reemplaza el mock por un screenshot real de tu app Streamlit.
- **Historia (slide 3):** retrato de Guido van Rossum.
- **Proyecto (slide 6):** captura del bracket del torneo.

Coloca los PNG en `public/` e impórtalos con `<img src="/nombre.png" />`.

## Build / deploy

```bash
npm run build     # genera dist/ (estático, desplegable a Vercel/Netlify/GitHub Pages)
npm run preview   # sirve el build localmente
```

# Diseño — Navegación limpia + profundización de pantallas (UI Streamlit)

**Fecha:** 2026-06-25
**Estado:** aprobado (alcance: Nav A + ítems a, d, e, g, i)

## Objetivo

1. **Eliminar la navegación duplicada** que hoy muestra entradas auto-detectadas
   (`app / dashboard / model status / predict / tournament`) que llevan a páginas en
   blanco, además del radio propio de `app.py`.
2. **Profundizar el contenido** de las 4 pantallas existentes con vistas de alto
   valor apoyadas en lo que el modelo ya calcula.

Fuera de alcance: pantallas nuevas, rediseño estético total, refactor no relacionado.

---

## Parte 1 — Navegación (Enfoque A: `st.navigation` + `st.Page`)

### Causa raíz
Streamlit auto-detecta el directorio hermano del entrypoint llamado `pages/`
(`src/ui/pages/`) y lo lista como multipage. Esos archivos solo definen `show()`
sin invocarla, así que al navegar a `/dashboard`, `/tournament`, etc. el área
principal queda vacía. `app.py` además navega con un `st.radio` propio → doble nav.

### Cambios
- **Renombrar** `src/ui/pages/` → `src/ui/views/` para que Streamlit deje de
  auto-detectar el directorio. Mover los 4 módulos + `__init__.py`.
- **Reescribir `src/ui/app.py`** para usar la API moderna:
  ```python
  import streamlit as st
  # ... sys.path setup (se conserva) ...
  from src.ui.views import predict, tournament, dashboard, model_status

  pages = [
      st.Page(predict.show,      title="Predecir partido",     icon="🔮", url_path="predict",   default=True),
      st.Page(tournament.show,   title="Torneo",               icon="🏆", url_path="tournament"),
      st.Page(dashboard.show,    title="Fiabilidad del modelo",icon="📊", url_path="reliability"),
      st.Page(model_status.show, title="Estado del modelo",    icon="⚙️", url_path="status"),
  ]
  st.set_page_config(page_title="WC 2026 Predictor", page_icon="⚽", layout="wide")
  # branding del sidebar (título + caption) se mantiene
  st.navigation(pages).run()
  ```
- **Actualizar imports internos** que apuntan a `src.ui.pages.*`
  (p.ej. `tournament.py`: `from src.ui.pages.predict import ...` →
  `from src.ui.views.predict import ...`).
- `src/ui/components.py` no cambia de ubicación; sus imports siguen válidos.
- Eliminar el bloque `st.radio` + ramas `if page == ...` de `app.py`.

### Resultado
Un único menú con íconos al tope del sidebar; cero páginas en blanco; rutas
limpias (`/predict`, `/tournament`, `/reliability`, `/status`).

---

## Parte 2 — Profundización de contenido

### (a) 🔮 Predecir — Heatmap de marcadores
- En `views/predict.py`, tras el bloque 1X2, agregar un heatmap de la matriz de
  probabilidad conjunta P(goles_a, goles_b) usando
  `predictor.model_goals.predict_score_matrix(ia, ib, host)`.
- Recortar a 0–6 goles por eje (la cola es despreciable); renombrar ejes con los
  ISO. Render con `matplotlib` (imshow + anotaciones de probabilidad por celda)
  dentro de `st.pyplot` — `matplotlib` ya es dependencia del proyecto.
- Marcar/resaltar la celda del marcador más probable.

### (d) 🏆 Torneo — Simulación Monte Carlo
- **Nuevo módulo** `src/tournament/montecarlo.py` (lógica fuera de la UI):
  ```python
  def simulate_tournament(results, predictor, n_sims=2000, seed=0) -> dict
  ```
  Retorna por equipo: `p_advance` (sale de grupos), `p_r16`, `p_qf`, `p_sf`,
  `p_final`, `p_champion`.
- **Algoritmo por simulación:**
  1. Para cada partido de grupos **no jugado**, muestrear un marcador de su
     matriz `predict_score_matrix` (precomputada y cacheada por fixture).
  2. Combinar con los resultados reales ya cargados → `all_standings` +
     `group_qualifiers` + `rank_thirds` para obtener los 32 clasificados.
  3. Sembrar la Ronda de 32 (reusar `assign_thirds` / lógica de `bracket.py`) y
     simular cada llave. En eliminatorias no hay empate (prórroga/penales deciden):
     el ganador se muestrea con `p = P(home) / (P(home) + P(away))` (se descarta la
     masa del empate y se renormaliza). Cachear win-prob por par (iso_a, iso_b, host).
  4. Contar avances por ronda y campeón.
- **Rendimiento:** matrices y win-probs por par se cachean; muestreo vectorizado
  con `numpy.random.default_rng(seed)`. Objetivo < 5 s para n_sims=2000.
  Determinista dado `seed`.
- **UI** (`views/tournament.py`, nueva pestaña "🎲 Pronóstico"): botón "Simular",
  `st.slider` para n_sims (500–5000), tabla ordenada por `p_champion` con barras
  (`st.dataframe` + `column_config.ProgressColumn`). Cachear con `st.cache_data`
  por (hash de resultados, n_sims).

### (e) 🏆 Torneo — Bracket visual
- Reemplazar la lista de texto de `render_bracket` por columnas reales: una
  `st.columns` por ronda (R32 → Final), cada llave como una "tarjeta"
  (`st.container(border=True)`) con ambos equipos y el ganador resaltado.
- Mantener la lógica de datos existente (`resolve_bracket`); solo cambia el render.

### (g) 📊 Fiabilidad — Métricas extra
- **Nuevo módulo** `src/evaluation/metrics.py` con versiones vectorizadas y
  testeables: `brier_1x2(df)`, `logloss_1x2(df)`, `rps_1x2(df)`, `hit_rate(df)`
  (argmax de P(1X2) vs resultado real). (No se tocan los scripts de evaluación
  existentes; este módulo consolida fórmulas para uso de la UI/tests.)
- En `views/dashboard.py`: ampliar la fila de métricas a Brier, **Log-loss**,
  **RPS** y **% aciertos 1X2**; el resultado real se deriva de `goals_a/goals_b`.

### (i) ⚙️ Estado — Tabla completa buscable
- En `views/model_status.py`, debajo de los Top-10, agregar una tabla con los
  **48 equipos**: columnas `ISO`, `α (ataque)`, `β (defensa)`, `Elo`.
- `st.text_input` de filtro (por ISO) + `st.dataframe` ordenable. Elo desde
  `elo_ratings_rolling.csv`; α/β desde `model.params_`.

---

## Arquitectura y límites

- **Lógica de dominio fuera de la UI:** la simulación vive en
  `src/tournament/montecarlo.py` y las métricas en `src/evaluation/metrics.py`.
  Las vistas solo orquestan y renderizan. Esto las mantiene testeables sin
  Streamlit.
- **Caché:** predicciones y simulaciones via `st.cache_data`/`st.cache_resource`
  con claves explícitas (hash de resultados) para invalidar al registrar partidos.

## Testing

- `tests/test_montecarlo.py`: con `seed` fijo, (1) las prob. de campeón suman ≈ 1,
  (2) `p_advance ≥ p_r16 ≥ ... ≥ p_champion` por equipo (monotonía por ronda),
  (3) un equipo ya eliminado matemáticamente tiene `p_champion == 0`,
  (4) determinismo: misma seed → mismo resultado.
- `tests/test_metrics.py`: valores conocidos para brier/logloss/rps/hit_rate
  (casos a mano) y rangos válidos.
- **UI:** verificación manual con el navegador headless (selenium) ya usado:
  cargar las 4 vistas + heatmap + simulación sin errores y revisar screenshots.

## Plan de verificación (manual)
1. `pytest` verde (incluye los 2 nuevos archivos de test).
2. Lanzar la app; confirmar **una sola** navegación, sin páginas en blanco.
3. Screenshot de cada vista nueva: heatmap, bracket visual, pestaña de simulación,
   métricas extra, tabla buscable.

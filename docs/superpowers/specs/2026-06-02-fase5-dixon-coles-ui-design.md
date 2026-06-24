# Fase 5 — Diseño: Dixon-Coles + Elo Dinámico + UI Streamlit

**Fecha:** 2026-06-02  
**Estado:** Aprobado por usuario

---

## Decisiones clave

| Decisión | Elección |
|---|---|
| Corrección DC | ρ estimado conjuntamente con los demás parámetros del modelo |
| Elo dinámico | K=20, actualización inmediata tras cada resultado |
| Re-entrenamiento | Con mejores hiperparámetros ya encontrados (sin repetir grid search) |
| UI | Streamlit — 3 páginas: Predecir / Dashboard / Estado del Modelo |
| Fuentes de partidos | WC 2026 (fixture oficial) + amistosos libres |

---

## 1. Dixon-Coles

### 1.1 Factor de corrección τ

```
τ(0,0) = 1 − λ_a·λ_b·ρ
τ(1,0) = 1 + λ_b·ρ
τ(0,1) = 1 + λ_a·ρ
τ(1,1) = 1 − ρ
τ(g_a,g_b) = 1  para todo lo demás
```

ρ es negativo típicamente (−0.1 a −0.2). Infla P(0-0) y P(1-1), reduce P(1-0) y P(0-1) ligeramente.

### 1.2 Cambios al modelo

- `PoissonModel` añade parámetro `rho` al vector θ de optimización
- `predict_score_matrix()` aplica τ a la matriz 9×9 antes de retornar
- Solo aplica al modelo de **goles** — los submodelos de props no se modifican
- `MatchPredictor` no cambia su interfaz externa

### 1.3 Implementación

Agregar `rho` al final de θ: `θ = [μ, α_1…α_{N-1}, β_0…β_{N-1}, γ, δ, ε, ζ, ρ]`

La función `neg_ll` incluye el factor τ en la log-verosimilitud:

```
ll_k = w_k × [log(τ(g_h,g_a)) + g_h·log(λ_h) − λ_h + g_a·log(λ_a) − λ_a]
```

Restricción: τ debe ser positivo. Bound: `rho ∈ [−0.99/(λ_a·λ_b), 0]` implementado via bounds en L-BFGS-B (en la práctica: `rho ∈ [−1.0, 0.0]`).

---

## 2. Pipeline de actualización dinámica

### 2.1 Flujo tras ingestar un resultado

```
resultado_real → actualizar Elo → añadir partido al dataset → re-entrenar → guardar pkl
```

### 2.2 Actualización Elo (K=20)

```python
expected = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
elo_a_new = elo_a + K * (score_a - expected)
elo_b_new = elo_b + K * (score_b - expected)
```

Donde `score_a = 1` (victoria), `0.5` (empate), `0` (derrota).

### 2.3 Re-entrenamiento

- Leer mejores hiperparámetros desde `outputs/best_params.json` (generado por `train.py`)
- Añadir nuevo partido a `data/processed/results_log.csv`
- Concatenar con `matches_historical_v2.csv` para re-entrenar
- Serializar nuevo `MatchPredictor` en `outputs/match_predictor.pkl`
- Tarda ~30-60 segundos

### 2.4 `results_log.csv`

```
match_date, iso_a, iso_b, host_iso, goals_a, goals_b,
p_home_pred, p_draw_pred, p_away_pred, brier_score, source
```

`source` ∈ `{"wc2026", "friendly"}`

---

## 3. Streamlit UI

### 3.1 Estructura de archivos

```
src/ui/
  app.py              ← entrada: streamlit run src/ui/app.py
  pages/
    predict.py        ← página: predecir partido
    dashboard.py      ← página: fiabilidad acumulada
    model_status.py   ← página: estado del modelo
  components/
    prediction_card.py  ← componente de predicción (reutilizable)
    market_table.py     ← tabla de líneas over/under
```

### 3.2 Página: Predecir Partido

- Dropdowns para equipos A y B (48 del WC + cualquier otro con Elo)
- Toggle "Partido del Mundial 2026" — muestra fixture oficial si ON
- Selector host_iso (ninguno / USA / CAN / MEX)
- Botón **Predecir** → llama a `MatchPredictor.predict_match()`
- Output: tarjeta con resultado 1X2, expected score, likely score + 5 tablas de mercado
- Sección colapsable "Ingresar resultado real" con inputs de goles → dispara pipeline de actualización

### 3.3 Página: Dashboard de Fiabilidad

- Lee `results_log.csv`
- Métricas: BS acumulado, BS WC vs amistosos, partidos registrados
- Gráfica de línea: BS partido a partido (rolling average 5 partidos)
- Tabla: todos los partidos predichos vs real, ordenados por error
- Filtros: fuente (wc2026/friendly), rango de fechas

### 3.4 Página: Estado del Modelo

- Hiperparámetros: ridge_λ, decay_rate, ρ (Dixon-Coles)
- Fecha último re-entrenamiento
- Número de partidos en el dataset
- Top 10 selecciones por α (ataque) y por β (defensa)
- Botón "Re-entrenar ahora" manual

---

## 4. Archivos nuevos/modificados

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/model/poisson_model.py` | Modificar | Añadir ρ al vector θ y τ a predict_score_matrix |
| `src/model/updater.py` | Crear | Elo update + re-entrenamiento parcial |
| `src/model/train.py` | Modificar | Guardar best_params.json |
| `src/ui/app.py` | Crear | Entry point Streamlit |
| `src/ui/pages/predict.py` | Crear | Página de predicción |
| `src/ui/pages/dashboard.py` | Crear | Dashboard de fiabilidad |
| `src/ui/pages/model_status.py` | Crear | Estado del modelo |
| `src/ui/__init__.py` | Crear | Vacío |
| `data/processed/results_log.csv` | Crear | Log de resultados reales |
| `outputs/best_params.json` | Crear | Hiperparámetros óptimos persistidos |

---

## 5. Fuera de scope

- Bracket/simulación del torneo completo (Fase C compleja)
- Autenticación o multi-usuario
- Deploy en servidor remoto
- Notificaciones automáticas de partidos

# Fase 4 — Diseño: Poisson Bivariado con Covariables Regularizado

**Fecha:** 2026-06-02  
**Estado:** Aprobado por usuario

---

## Decisiones clave

| Decisión | Elección |
|---|---|
| Arquitectura del modelo | Poisson con covariables + regularización L2 |
| Datos de entrenamiento | Historia completa 1930–2022 con time_weight |
| Validación | Leave-one-tournament-out (LOTO-CV) |

---

## 1. Arquitectura del modelo

Para cada partido entre equipo i y equipo j:

```
λ_i = exp(μ + α_i − β_j + γ·host_i + δ·elo_diff_ij + ε·xg_diff_ij + ζ·value_ratio_ij)
λ_j = exp(μ + α_j − β_i + γ·host_j + δ·elo_diff_ji + ε·xg_diff_ji + ζ·value_ratio_ji)
```

**Parámetros:**
- `μ`: intercepto global (tasa base de goles)
- `α_i`, `β_i`: ataque y defensa por selección (96 params totales, regularizados con L2)
- `γ`: bonus de anfitrión — activo solo cuando `host_team_iso == equipo` (no "home" genérico)
- `δ·elo_diff`: diferencia de Elo normalizada
- `ε·xg_diff`: diferencia de xG actual entre equipos
- `ζ·value_ratio`: log(squad_value_i / squad_value_j)

**Restricción de identificabilidad:** `Σα_i = 0`

---

## 2. Features y preprocessing

### Jerarquía de fuentes para `xg_diff`

Prioridad descendente por confiabilidad:

1. `sb_xg_per90` — StatsBomb (torneos internacionales reales) → 40/48 equipos
2. `sq_npxg_per90` — Understat Big5 (club 2024-25) → 43/48 equipos
3. `fb_npgls_per90` — FBref intl (manual, 15 selecciones non-Big5)
4. Mediana del corpus → equipos restantes (nunca más de 5)

### Features con cobertura 100%

- `elo_rating`: 48/48 — ningún equipo queda sin señal de fuerza relativa
- `squad_value_m_eur`: 48/48

### Imputación

NaN residuales → mediana del corpus de 48 equipos. Equipos marcados con `is_debutant_2026=1` ya tienen imputación de Fase 2.

### `host_i` flag

Derivado de `host_team_iso` en `matches_historical_v2.csv`. En WC 2026: USA, CAN, MEX.

---

## 3. Entrenamiento

### Función objetivo

Log-verosimilitud negativa ponderada por tiempo + penalización ridge sobre parámetros por equipo:

```
L(θ) = −Σ_k time_weight_k · [g_ik·log(λ_ik) − λ_ik + h_jk·log(λ_jk) − λ_jk]
       + (ridge_λ/2) · Σ_i(α_i² + β_i²)
```

La penalización L2 **no** aplica a coeficientes globales (γ, δ, ε, ζ) — son señales con interpretación física.

### Optimización

`scipy.optimize.minimize(method='L-BFGS-B')` con gradiente analítico.

### Hiperparámetros a tunear (grid search)

| Hiperparámetro | Valores | Default |
|---|---|---|
| `ridge_λ` | 0.01, 0.05, 0.1, 0.5, 1.0 | 0.1 |
| `decay_rate` | 0.02, 0.05, 0.1 | 0.05 |

---

## 4. Validación: Leave-One-Tournament-Out (LOTO-CV)

Para cada torneo T en {1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022}:
1. Entrenar con todos los partidos excepto torneo T
2. Predecir los partidos de T con `teams_features_v2.csv` como features actuales
3. Calcular Brier Score multiclase

**Brier Score:**
```
BS = (1/N) Σ [(p_home − o_home)² + (p_draw − o_draw)² + (p_away − o_away)²]
```

Referencia: modelo naive (1/3 cada resultado) → BS ≈ 0.667. Target: BS < 0.60.

Usar **la combinación de hiperparámetros** con menor BS promedio en LOTO-CV para el modelo final.

---

## 5. Outputs y predicción

### Distribución de marcadores

```
P(g, h) = Poisson(g | λ_i) × Poisson(h | λ_j)     g, h ∈ [0, 8]
```

Matriz 9×9 de probabilidades exactas de marcador.

### Por partido

| Output | Cálculo |
|---|---|
| `p_home_win` | Σ P(g > h) |
| `p_draw` | Σ P(g = h) |
| `p_away_win` | Σ P(g < h) |
| `expected_score` | (E[λ_i], E[λ_j]) |
| `most_likely_score` | argmax de la matriz 9×9 |

### Interfaz

```python
model.predict_match("ARG", "FRA", host_iso=None)
# → {"p_home": 0.42, "p_draw": 0.24, "p_away": 0.34,
#    "expected": [1.6, 1.3], "likely_score": "2-1"}
```

---

## 6. Estructura de archivos

```
src/model/
  __init__.py
  poisson_model.py     ← clase PoissonModel: fit(), predict_match()
  features.py          ← build_xg_feature(), impute_features()
  validation.py        ← loto_cv(), brier_score()
```

Datos de entrada:
- `data/processed/matches_historical_v2.csv`
- `data/features/teams_features_v2.csv`

---

## 7. Fuera de scope (Fase 5)

- Corrección Dixon-Coles para marcadores bajos (0-0, 1-0, 0-1, 1-1)
- Integración de Elo como componente dinámico (se actualiza partido a partido)

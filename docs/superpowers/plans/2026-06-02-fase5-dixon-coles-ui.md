# Fase 5 — Dixon-Coles + Elo Dinámico + UI Streamlit: Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir corrección Dixon-Coles al modelo de goles, pipeline de actualización dinámica Elo + re-entrenamiento tras cada resultado real, y UI Streamlit con predicción, registro de resultados y dashboard de fiabilidad.

**Architecture:** `PoissonModel` añade parámetro ρ y factor τ al `predict_score_matrix`. `updater.py` gestiona Elo K=20 + re-entrenamiento con hiperparámetros óptimos persistidos en `best_params.json`. UI Streamlit de 3 páginas con navegación por sidebar.

**Tech Stack:** Python 3.12, scipy, pandas, streamlit, pytest

---

## Columnas y paths confirmados

- `data/features/elo_ratings.csv`: `iso_code, elo_rank, elo_rating, elo_peak`
- `data/processed/matches_2026_fixtures.csv`: `match_date, match_time, round, group, team1_name, team2_name, ground`
- `data/raw/reference/team_codes_mapping.csv`: `openfootball_name, iso_code, country_full, ...` — los `openfootball_name` coinciden exactamente con los nombres del fixture
- Host detection por `ground`: ciudades MX → MEX, Toronto/Vancouver → CAN, resto → USA
- `outputs/poisson_model.pkl` y `outputs/match_predictor.pkl` ya existen

---

## File Map

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/model/features.py` | Modificar | Skip de partidos completos cuando falta equipo |
| `src/model/poisson_model.py` | Modificar | ρ en θ, τ en neg_ll y predict_score_matrix |
| `src/model/train.py` | Modificar | Guardar `outputs/best_params.json` |
| `src/model/train_props.py` | Modificar | Guardar params de props en `best_params.json` |
| `src/model/updater.py` | Crear | Elo update, log result, retrain |
| `src/ui/__init__.py` | Crear | Vacío |
| `src/ui/app.py` | Crear | Entry point Streamlit + navegación |
| `src/ui/pages/__init__.py` | Crear | Vacío |
| `src/ui/pages/predict.py` | Crear | Página predicción + ingesta de resultado |
| `src/ui/pages/dashboard.py` | Crear | Dashboard de fiabilidad |
| `src/ui/pages/model_status.py` | Crear | Estado del modelo |
| `tests/model/test_dixon_coles.py` | Crear | Tests DC |
| `tests/model/test_updater.py` | Crear | Tests updater |

---

## Task 1: Corregir `build_match_rows` — skip a nivel de partido

El DC necesita filas en pares exactos. Actualmente si un equipo no está en `teams_df`, se omite solo ese equipo, rompiendo la paridad par/impar.

**Files:**
- Modify: `src/model/features.py`
- Modify: `tests/model/test_features.py`

- [ ] **Agregar test de paridad al final de `tests/model/test_features.py`**

```python
def test_build_match_rows_always_paired():
    """Cuando un equipo no está en teams_df, se omite el partido completo (ambas filas)."""
    matches = pd.DataFrame({
        "home_team_iso":   ["ARG", "BRA"],   # BRA no estará en teams_df
        "away_team_iso":   ["FRA", "DEU"],
        "home_team_score": [2, 1],
        "away_team_score": [1, 0],
        "year":            [2022, 2018],
        "host_team_iso":   [np.nan, np.nan],
    })
    teams_partial = _make_teams_df()[_make_teams_df()["iso_code"].isin(["ARG", "FRA"])]
    rows = build_match_rows(matches, teams_partial, year_ref=2026, decay_rate=0.05)
    # ARG vs FRA → 2 filas. BRA vs DEU → 0 filas (BRA y DEU no están en teams)
    assert len(rows) % 2 == 0
    assert len(rows) == 2
```

- [ ] **Verificar que falla**

```bash
source .venv/bin/activate && pytest tests/model/test_features.py::test_build_match_rows_always_paired -v 2>&1 | tail -5
```

Esperado: FAIL (actualmente el loop skipea equipos individuales, no el partido completo).

- [ ] **Modificar el loop en `build_match_rows` en `src/model/features.py`**

Reemplazar el bloque del loop interno:

```python
    rows = []
    for _, match in matches_df.iterrows():
        hi   = match["home_team_iso"]
        ai   = match["away_team_iso"]
        year = int(match["year"])
        host = match.get("host_team_iso", np.nan)
        host = None if pd.isna(host) else host
        tw   = float(np.exp(-decay_rate * (year_ref - year)))

        # Skip entire match if either team missing — ensures rows stay in pairs
        if hi not in t.index or ai not in t.index:
            continue

        pairs = [
            (hi, ai, int(match[home_score_col])),
            (ai, hi, int(match[away_score_col])),
        ]
        for att, dff, goals in pairs:
            rows.append({
                "iso_code":        att,
                "opp_iso":         dff,
                "goals_for":       goals,
                "time_weight":     tw,
                "host_flag":       1.0 if att == host else 0.0,
                "elo_diff":        float(elo[att] - elo[dff]),
                "xg_diff":         float(xg[att] - xg[dff]),
                "log_value_ratio": float(log_val[att] - log_val[dff]),
                "year":            year,
            })
```

- [ ] **Verificar que todos los tests de features pasan**

```bash
pytest tests/model/test_features.py -v 2>&1 | tail -8
```

Esperado: todos en PASS incluyendo el nuevo test.

---

## Task 2: Dixon-Coles — añadir ρ y τ a `PoissonModel`

**Files:**
- Modify: `src/model/poisson_model.py`
- Create: `tests/model/test_dixon_coles.py`

- [ ] **Crear `tests/model/test_dixon_coles.py`**

```python
import numpy as np
import pandas as pd
import pytest

from src.model.poisson_model import PoissonModel


def _matches():
    records = []
    for _ in range(40):
        records += [
            {"home_team_iso":"A","away_team_iso":"B","home_team_score":2,"away_team_score":1,
             "year":2022,"host_team_iso":np.nan},
            {"home_team_iso":"B","away_team_iso":"A","home_team_score":1,"away_team_score":2,
             "year":2022,"host_team_iso":np.nan},
        ]
    return pd.DataFrame(records)


def _teams():
    return pd.DataFrame({
        "iso_code":["A","B"],"elo_rating":[1800.0,1800.0],
        "squad_value_m_eur":[500.0,500.0],"sb_xg_per90":[1.0,1.0],
        "sq_npxg_per90":[np.nan,np.nan],"fb_npgls_per90":[np.nan,np.nan],
    })


def test_dc_model_has_rho_param():
    model = PoissonModel(use_dc=True).fit(_matches(), _teams(), year_ref=2022)
    assert "rho" in model.params_
    assert model.params_["rho"] <= 0.0   # ρ siempre negativo o cero


def test_dc_score_matrix_sums_to_one():
    model = PoissonModel(use_dc=True).fit(_matches(), _teams(), year_ref=2022)
    matrix = model.predict_score_matrix("A", "B")
    assert matrix.sum() == pytest.approx(1.0, abs=1e-3)


def test_dc_vs_standard_score_matrix_differs():
    """DC debe modificar P(0-0), P(1-0), P(0-1), P(1-1) respecto al Poisson puro."""
    m_dc  = PoissonModel(use_dc=True,  ridge_lambda=0.01).fit(_matches(), _teams(), year_ref=2022)
    m_std = PoissonModel(use_dc=False, ridge_lambda=0.01).fit(_matches(), _teams(), year_ref=2022)
    mat_dc  = m_dc.predict_score_matrix("A", "B")
    mat_std = m_std.predict_score_matrix("A", "B")
    # La corrección DC debe cambiar al menos una de las 4 celdas de bajo marcador
    low_score_cells = [(0,0),(1,0),(0,1),(1,1)]
    diffs = [abs(mat_dc[r,c] - mat_std[r,c]) for r,c in low_score_cells]
    assert max(diffs) > 1e-6


def test_dc_probabilities_sum_to_one():
    model = PoissonModel(use_dc=True).fit(_matches(), _teams(), year_ref=2022)
    result = model.predict_match("A", "B")
    assert abs(result["p_home"] + result["p_draw"] + result["p_away"] - 1.0) < 1e-3
```

- [ ] **Verificar que fallan**

```bash
pytest tests/model/test_dixon_coles.py -v 2>&1 | head -10
```

Esperado: `TypeError` — `use_dc` no existe aún.

- [ ] **Modificar `src/model/poisson_model.py` para añadir DC**

Reemplazar el archivo completo:

```python
"""
Modelo de Poisson bivariado con covariables regularizado (ridge L2) +
corrección Dixon-Coles para marcadores bajos.

Para un partido entre equipo i y equipo j:
  log(λ_i) = μ + α_i − β_j + γ·host_i + δ·elo_diff + ε·xg_diff + ζ·log_value_ratio

Corrección DC: P(g_h,g_a) *= τ(g_h,g_a,λ_h,λ_a,ρ) para (g_h,g_a) ∈ {(0,0),(1,0),(0,1),(1,1)}
Restricción de identificabilidad: Σ α_i = 0. Optimización: L-BFGS-B.
"""
import warnings
from typing import Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from src.model.features import build_match_rows, build_xg_priority, impute_to_median


class PoissonModel:
    def __init__(
        self,
        ridge_lambda: float = 0.1,
        decay_rate:   float = 0.05,
        max_goals:    int   = 8,
        use_dc:       bool  = True,
    ):
        self.ridge_lambda = ridge_lambda
        self.decay_rate   = decay_rate
        self.max_goals    = max_goals
        self.use_dc       = use_dc
        self.teams_:    Optional[list]  = None
        self.params_:   Optional[dict]  = None
        self._teams_df: Optional[pd.DataFrame] = None

    # ── Corrección DC ──────────────────────────────────────────────────────────

    @staticmethod
    def _tau(g_att: np.ndarray, g_opp: np.ndarray,
             lam_att: np.ndarray, lam_opp: np.ndarray, rho: float) -> np.ndarray:
        """
        Factor τ vectorizado para marcadores bajos.
        g_att/g_opp son arrays de int, lam_att/lam_opp arrays de float.
        Retorna array de τ (≥ 1e-10).
        """
        tau = np.ones(len(g_att), dtype=float)
        m00 = (g_att == 0) & (g_opp == 0)
        m10 = (g_att == 1) & (g_opp == 0)
        m01 = (g_att == 0) & (g_opp == 1)
        m11 = (g_att == 1) & (g_opp == 1)
        tau[m00] = 1.0 - lam_att[m00] * lam_opp[m00] * rho
        tau[m10] = 1.0 + lam_opp[m10] * rho
        tau[m01] = 1.0 + lam_att[m01] * rho
        tau[m11] = 1.0 - rho
        return np.maximum(tau, 1e-10)

    # ── Entrenamiento ──────────────────────────────────────────────────────────

    def fit(
        self,
        matches_df: pd.DataFrame,
        teams_df:   pd.DataFrame,
        year_ref:   int  = 2026,
        home_score_col: str = "home_team_score",
        away_score_col: str = "away_team_score",
    ) -> "PoissonModel":
        rows = build_match_rows(
            matches_df, teams_df,
            year_ref=year_ref, decay_rate=self.decay_rate,
            home_score_col=home_score_col, away_score_col=away_score_col,
        )
        self._teams_df = teams_df.copy()
        self.teams_    = sorted(rows["iso_code"].unique().tolist())
        N              = len(self.teams_)
        team_idx       = {t: i for i, t in enumerate(self.teams_)}

        att_idx = rows["iso_code"].map(team_idx).values
        def_idx = rows["opp_iso"].map(team_idx).values
        goals   = rows["goals_for"].values.astype(float)
        weights = rows["time_weight"].values
        host    = rows["host_flag"].values
        elo_d   = rows["elo_diff"].values / 100.0
        xg_d    = rows["xg_diff"].values
        val_r   = rows["log_value_ratio"].values
        ridge   = self.ridge_lambda

        def neg_ll(theta):
            mu          = theta[0]
            alphas_free = theta[1:N]
            alpha_0     = -alphas_free.sum()
            alphas      = np.concatenate([[alpha_0], alphas_free])
            betas       = theta[N:2 * N]
            gamma, delta, eps, zeta = theta[2 * N: 2 * N + 4]
            rho = theta[2 * N + 4] if self.use_dc else 0.0

            log_lam = (mu + alphas[att_idx] - betas[def_idx]
                       + gamma * host + delta * elo_d + eps * xg_d + zeta * val_r)
            lam = np.exp(log_lam)

            # Standard Poisson log-likelihood
            ll = (goals * log_lam - lam) * weights

            # Dixon-Coles correction — applied once per match (even rows = primary)
            if self.use_dc:
                n = len(ll)
                # Rows guaranteed in pairs: even=primary(home), odd=secondary(away)
                primary   = np.arange(0, n, 2)
                secondary = np.arange(1, n, 2)
                min_len   = min(len(primary), len(secondary))
                primary   = primary[:min_len]
                secondary = secondary[:min_len]

                g_att = goals[primary].astype(int)
                g_opp = goals[secondary].astype(int)
                tau   = self._tau(g_att, g_opp, lam[primary], lam[secondary], rho)
                ll[primary] += np.log(tau) * weights[primary]

            pen = (ridge / 2.0) * (np.sum(alphas ** 2) + np.sum(betas ** 2))
            return -ll.sum() + pen

        n_params = 1 + (N - 1) + N + 4 + (1 if self.use_dc else 0)
        theta0   = np.zeros(n_params)

        bounds = [(-np.inf, np.inf)] * (2 * N + 4)
        if self.use_dc:
            bounds.append((-1.0, 0.0))  # ρ ∈ [-1, 0]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = minimize(neg_ll, theta0, method="L-BFGS-B",
                              bounds=bounds,
                              options={"maxiter": 3000, "ftol": 1e-12})

        theta       = result.x
        alphas_free = theta[1:N]
        alpha_0     = -alphas_free.sum()
        alphas      = np.concatenate([[alpha_0], alphas_free])
        betas       = theta[N:2 * N]
        gamma, delta, eps, zeta = theta[2 * N: 2 * N + 4]
        rho = float(theta[2 * N + 4]) if self.use_dc else 0.0

        self.params_ = {
            "mu":    float(theta[0]),
            "alpha": {t: float(alphas[i]) for i, t in enumerate(self.teams_)},
            "beta":  {t: float(betas[i])  for i, t in enumerate(self.teams_)},
            "gamma": float(gamma),
            "delta": float(delta),
            "eps":   float(eps),
            "zeta":  float(zeta),
            "rho":   rho,
        }
        return self

    # ── Predicción ─────────────────────────────────────────────────────────────

    def _lambda(self, iso_att: str, iso_def: str, host_iso: Optional[str]) -> float:
        p      = self.params_
        t      = self._teams_df.set_index("iso_code")
        xg     = impute_to_median(build_xg_priority(t))
        elo    = impute_to_median(t["elo_rating"])
        logval = impute_to_median(np.log(t["squad_value_m_eur"]))

        alpha_att = p["alpha"].get(iso_att, 0.0)
        beta_def  = p["beta"].get(iso_def, 0.0)
        host_flag = 1.0 if iso_att == host_iso else 0.0
        elo_d     = (elo.get(iso_att, elo.median()) - elo.get(iso_def, elo.median())) / 100.0
        xg_d      = xg.get(iso_att, xg.median())    - xg.get(iso_def, xg.median())
        val_r     = logval.get(iso_att, logval.median()) - logval.get(iso_def, logval.median())

        log_lam = (p["mu"] + alpha_att - beta_def
                   + p["gamma"] * host_flag + p["delta"] * elo_d
                   + p["eps"] * xg_d + p["zeta"] * val_r)
        return float(np.exp(log_lam))

    def predict_score_matrix(
        self, iso_a: str, iso_b: str, host_iso: Optional[str] = None
    ) -> np.ndarray:
        """Matriz (max_goals+1)² con corrección Dixon-Coles."""
        lam_a = self._lambda(iso_a, iso_b, host_iso)
        lam_b = self._lambda(iso_b, iso_a, host_iso)
        g      = np.arange(self.max_goals + 1)
        matrix = np.outer(poisson.pmf(g, lam_a), poisson.pmf(g, lam_b))

        if self.use_dc and self.params_["rho"] != 0.0:
            rho = self.params_["rho"]
            matrix[0, 0] *= max(1.0 - lam_a * lam_b * rho, 1e-10)
            matrix[1, 0] *= max(1.0 + lam_b * rho,         1e-10)
            matrix[0, 1] *= max(1.0 + lam_a * rho,         1e-10)
            matrix[1, 1] *= max(1.0 - rho,                 1e-10)
            matrix /= matrix.sum()   # renormalizar

        return matrix

    def predict_match(
        self, iso_a: str, iso_b: str, host_iso: Optional[str] = None
    ) -> dict:
        matrix  = self.predict_score_matrix(iso_a, iso_b, host_iso)
        p_a_win = float(np.tril(matrix, -1).sum())
        p_draw  = float(np.trace(matrix))
        p_b_win = float(np.triu(matrix,  1).sum())
        lam_a   = self._lambda(iso_a, iso_b, host_iso)
        lam_b   = self._lambda(iso_b, iso_a, host_iso)
        idx     = np.unravel_index(matrix.argmax(), matrix.shape)
        return {
            "p_home":       round(p_a_win, 4),
            "p_draw":       round(p_draw,  4),
            "p_away":       round(p_b_win, 4),
            "expected":     [round(lam_a, 2), round(lam_b, 2)],
            "likely_score": f"{idx[0]}-{idx[1]}",
            "iso_home":     iso_a,
            "iso_away":     iso_b,
        }
```

- [ ] **Verificar tests DC + todos los tests del modelo**

```bash
pytest tests/model/test_dixon_coles.py tests/model/test_poisson_model.py -v 2>&1 | tail -15
```

Esperado: todos en PASS.

---

## Task 3: Actualizar `train.py` para guardar `best_params.json` + reentrenar con DC

**Files:**
- Modify: `src/model/train.py`
- Modify: `src/model/train_props.py`

- [ ] **Modificar `src/model/train.py`**: añadir guardado de `best_params.json` al final de `main()`

Reemplazar el bloque final de `main()` (después del print "Modelo guardado"):

```python
    # Guardar mejores hiperparámetros para re-entrenamiento futuro
    import json
    best_params = {
        "goals": {
            "ridge_lambda": best_ridge,
            "decay_rate":   best_decay,
        }
    }
    best_params_path = ROOT / "outputs/best_params.json"
    # Merge con params existentes si el archivo ya existe
    if best_params_path.exists():
        with open(best_params_path) as f:
            existing = json.load(f)
        existing.update(best_params)
        best_params = existing
    with open(best_params_path, "w") as f:
        json.dump(best_params, f, indent=2)
    print(f"Hiperparámetros guardados → {best_params_path.relative_to(ROOT)}")
```

También añadir `import json` al inicio del archivo si no está.

- [ ] **Modificar `src/model/train_props.py`**: guardar parámetros de props en `best_params.json`

Añadir al final de `main()`, después del guardado del pkl:

```python
    import json
    best_params_path = ROOT / "outputs/best_params.json"
    best_params = {}
    if best_params_path.exists():
        with open(best_params_path) as f:
            best_params = json.load(f)

    for market, model in [
        ("corners", trained["corners"]),
        ("cards",   trained["cards"]),
        ("shots",   trained["shots"]),
        ("fouls",   trained["fouls"]),
    ]:
        best_params[market] = {
            "ridge_lambda": model.ridge_lambda,
            "decay_rate":   model.decay_rate,
        }

    with open(best_params_path, "w") as f:
        json.dump(best_params, f, indent=2)
    print(f"Hiperparámetros de props guardados → {best_params_path.relative_to(ROOT)}")
```

- [ ] **Re-correr `train.py` para regenerar modelo con DC + best_params.json**

```bash
source .venv/bin/activate && python -m src.model.train 2>&1 | tail -20
```

Verificar:
- Output muestra `ρ` en los params del modelo
- `outputs/best_params.json` creado con sección `"goals"`
- Brier Score similar o mejor al anterior (≤ 0.602)

- [ ] **Re-correr `train_props.py` para actualizar best_params.json con props**

```bash
source .venv/bin/activate && python -m src.model.train_props 2>&1 | tail -10
```

Verificar: `outputs/best_params.json` contiene ahora sections `goals`, `corners`, `cards`, `shots`, `fouls`.

---

## Task 4: `updater.py` — Elo + log + re-entrenamiento

**Files:**
- Create: `src/model/updater.py`
- Create: `tests/model/test_updater.py`

- [ ] **Crear `tests/model/test_updater.py`**

```python
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.model.updater import update_elo, log_result, ELO_K


def _make_elo_df():
    return pd.DataFrame({
        "iso_code":   ["ARG", "FRA", "BRA"],
        "elo_rank":   [1,     2,     3    ],
        "elo_rating": [2100.0, 2080.0, 1980.0],
        "elo_peak":   [2172.0, 2135.0, 2050.0],
    })


def test_update_elo_winner_gains():
    elo = _make_elo_df()
    updated = update_elo(elo, "ARG", "FRA", goals_a=2, goals_b=0)
    assert updated.loc[updated["iso_code"]=="ARG","elo_rating"].values[0] > 2100.0
    assert updated.loc[updated["iso_code"]=="FRA","elo_rating"].values[0] < 2080.0


def test_update_elo_draw_near_equal_teams():
    elo = _make_elo_df()
    updated = update_elo(elo, "ARG", "FRA", goals_a=1, goals_b=1)
    # ARG (2100) vs FRA (2080): ARG expected to win, so ARG loses rating in draw
    arg_new = updated.loc[updated["iso_code"]=="ARG","elo_rating"].values[0]
    fra_new = updated.loc[updated["iso_code"]=="FRA","elo_rating"].values[0]
    assert arg_new < 2100.0
    assert fra_new > 2080.0


def test_update_elo_sum_preserved():
    """La suma de ratings debe conservarse (rating sale = rating entra)."""
    elo = _make_elo_df()
    updated = update_elo(elo, "ARG", "FRA", goals_a=3, goals_b=1)
    orig_sum = elo.loc[elo["iso_code"].isin(["ARG","FRA"]), "elo_rating"].sum()
    new_sum  = updated.loc[updated["iso_code"].isin(["ARG","FRA"]), "elo_rating"].sum()
    assert abs(orig_sum - new_sum) < 0.01


def test_update_elo_returns_copy():
    elo = _make_elo_df()
    updated = update_elo(elo, "ARG", "FRA", goals_a=1, goals_b=0)
    assert elo.loc[elo["iso_code"]=="ARG","elo_rating"].values[0] == 2100.0  # original unchanged


def test_log_result_creates_file(tmp_path):
    log_path = tmp_path / "results_log.csv"
    log_result(
        match_date="2026-06-15", iso_a="ARG", iso_b="FRA", host_iso=None,
        goals_a=2, goals_b=1,
        p_home=0.42, p_draw=0.24, p_away=0.34,
        source="wc2026", log_path=log_path,
    )
    assert log_path.exists()
    df = pd.read_csv(log_path)
    assert len(df) == 1
    assert df["iso_a"].iloc[0] == "ARG"
    assert df["brier_score"].iloc[0] == pytest.approx(0.0 + 0.24**2 + 0.34**2, abs=0.01)


def test_log_result_appends(tmp_path):
    log_path = tmp_path / "results_log.csv"
    for i in range(3):
        log_result(
            match_date=f"2026-06-{15+i}", iso_a="ARG", iso_b="FRA", host_iso=None,
            goals_a=1, goals_b=0,
            p_home=0.5, p_draw=0.25, p_away=0.25,
            source="friendly", log_path=log_path,
        )
    df = pd.read_csv(log_path)
    assert len(df) == 3
```

- [ ] **Verificar que fallan**

```bash
source .venv/bin/activate && pytest tests/model/test_updater.py -v 2>&1 | head -10
```

Esperado: `ImportError`.

- [ ] **Crear `src/model/updater.py`**

```python
"""
Pipeline de actualización dinámica del modelo.

- update_elo(): actualiza ratings Elo tras un resultado real (K=20)
- log_result(): guarda resultado en results_log.csv con Brier Score
- retrain_goals_model(): re-entrena PoissonModel de goles con mejores hiperparámetros
"""
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

ELO_K = 20.0   # K-factor estándar para internacionales

ROOT             = Path(__file__).resolve().parents[2]
ELO_CSV          = ROOT / "data/features/elo_ratings.csv"
TEAMS_CSV        = ROOT / "data/features/teams_features_v2.csv"
MATCHES_CSV      = ROOT / "data/processed/matches_historical_v2.csv"
RESULTS_LOG_CSV  = ROOT / "data/processed/results_log.csv"
BEST_PARAMS_JSON = ROOT / "outputs/best_params.json"
PREDICTOR_PKL    = ROOT / "outputs/match_predictor.pkl"


def update_elo(
    elo_df:  pd.DataFrame,
    iso_a:   str,
    iso_b:   str,
    goals_a: int,
    goals_b: int,
    k:       float = ELO_K,
) -> pd.DataFrame:
    """
    Actualiza ratings Elo tras el resultado iso_a goals_a — goals_b iso_b.
    Retorna una copia del DataFrame con los ratings actualizados.
    """
    elo_df = elo_df.copy()

    def _get(iso):
        mask = elo_df["iso_code"] == iso
        if not mask.any():
            raise ValueError(f"ISO {iso!r} no encontrado en elo_df")
        return float(elo_df.loc[mask, "elo_rating"].iloc[0])

    elo_a = _get(iso_a)
    elo_b = _get(iso_b)

    expected_a = 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))
    expected_b = 1.0 - expected_a

    if goals_a > goals_b:
        score_a, score_b = 1.0, 0.0
    elif goals_a == goals_b:
        score_a, score_b = 0.5, 0.5
    else:
        score_a, score_b = 0.0, 1.0

    new_elo_a = round(elo_a + k * (score_a - expected_a), 1)
    new_elo_b = round(elo_b + k * (score_b - expected_b), 1)

    elo_df.loc[elo_df["iso_code"] == iso_a, "elo_rating"] = new_elo_a
    elo_df.loc[elo_df["iso_code"] == iso_b, "elo_rating"] = new_elo_b
    return elo_df


def log_result(
    match_date: str,
    iso_a:      str,
    iso_b:      str,
    host_iso:   Optional[str],
    goals_a:    int,
    goals_b:    int,
    p_home:     float,
    p_draw:     float,
    p_away:     float,
    source:     str,
    log_path:   Path = RESULTS_LOG_CSV,
) -> float:
    """
    Guarda el resultado real en results_log.csv.
    Retorna el Brier Score del partido.
    """
    if goals_a > goals_b:
        o_home, o_draw, o_away = 1.0, 0.0, 0.0
    elif goals_a == goals_b:
        o_home, o_draw, o_away = 0.0, 1.0, 0.0
    else:
        o_home, o_draw, o_away = 0.0, 0.0, 1.0

    bs = (p_home - o_home)**2 + (p_draw - o_draw)**2 + (p_away - o_away)**2

    row = pd.DataFrame([{
        "match_date":  match_date,
        "iso_a":       iso_a,
        "iso_b":       iso_b,
        "host_iso":    host_iso if host_iso else "",
        "goals_a":     goals_a,
        "goals_b":     goals_b,
        "p_home_pred": round(p_home, 4),
        "p_draw_pred": round(p_draw, 4),
        "p_away_pred": round(p_away, 4),
        "brier_score": round(bs, 4),
        "source":      source,
    }])

    if log_path.exists():
        row.to_csv(log_path, mode="a", header=False, index=False)
    else:
        row.to_csv(log_path, mode="w", header=True, index=False)

    return bs


def retrain_goals_model(
    elo_df:          pd.DataFrame,
    teams_csv:       Path = TEAMS_CSV,
    matches_csv:     Path = MATCHES_CSV,
    results_log_csv: Path = RESULTS_LOG_CSV,
    best_params_json: Path = BEST_PARAMS_JSON,
    predictor_pkl:   Path = PREDICTOR_PKL,
) -> None:
    """
    Re-entrena el PoissonModel de goles con:
    1. Elo actualizado (pasado como elo_df)
    2. Partidos históricos + resultados reales registrados
    3. Mejores hiperparámetros de best_params.json (sin repetir grid search)

    Actualiza match_predictor.pkl in-place.
    """
    import pickle
    from src.model.poisson_model import PoissonModel

    # Cargar datos base
    teams    = pd.read_csv(teams_csv)
    matches  = pd.read_csv(matches_csv)

    # Actualizar Elo en teams_df
    teams = teams.drop(columns=["elo_rating"]).merge(
        elo_df[["iso_code","elo_rating"]], on="iso_code", how="left"
    )

    # Añadir resultados reales si existen
    if results_log_csv.exists():
        log = pd.read_csv(results_log_csv)
        if len(log) > 0:
            new_matches = pd.DataFrame({
                "home_team_iso":   log["iso_a"],
                "away_team_iso":   log["iso_b"],
                "home_team_score": log["goals_a"],
                "away_team_score": log["goals_b"],
                "year":            pd.to_datetime(log["match_date"]).dt.year,
                "host_team_iso":   log["host_iso"].replace("", np.nan),
                "neutral_venue":   True,
                "time_weight":     1.0,  # partidos recientes → peso máximo
            })
            matches = pd.concat([matches, new_matches], ignore_index=True)

    # Cargar mejores hiperparámetros
    with open(best_params_json) as f:
        best_params = json.load(f)
    gp = best_params["goals"]

    # Re-entrenar modelo de goles con DC
    print("Re-entrenando modelo de goles con Dixon-Coles ...")
    new_goals_model = PoissonModel(
        ridge_lambda=gp["ridge_lambda"],
        decay_rate=gp["decay_rate"],
        use_dc=True,
    ).fit(matches, teams, year_ref=2026)
    print(f"  ρ (Dixon-Coles): {new_goals_model.params_['rho']:.4f}")

    # Actualizar match_predictor.pkl manteniendo los submodelos de props
    with open(predictor_pkl, "rb") as f:
        predictor = pickle.load(f)
    predictor.model_goals = new_goals_model

    with open(predictor_pkl, "wb") as f:
        pickle.dump(predictor, f)
    print(f"  MatchPredictor actualizado → {predictor_pkl.name}")
```

- [ ] **Verificar que los tests de updater pasan**

```bash
pytest tests/model/test_updater.py -v 2>&1 | tail -12
```

Esperado: todos en PASS (8 tests).

---

## Task 5: Instalar Streamlit + `app.py` + `predict.py`

**Files:**
- Create: `src/ui/__init__.py`, `src/ui/pages/__init__.py`
- Create: `src/ui/app.py`
- Create: `src/ui/pages/predict.py`

- [ ] **Instalar streamlit**

```bash
source .venv/bin/activate && pip install streamlit -q && python -c "import streamlit; print('streamlit', streamlit.__version__)"
```

Esperado: versión impresa (≥ 1.30).

- [ ] **Crear ficheros vacíos de módulo**

```bash
touch src/ui/__init__.py src/ui/pages/__init__.py
mkdir -p src/ui/pages
```

- [ ] **Crear `src/ui/app.py`**

```python
"""
WC 2026 Predictor — UI Streamlit.
Lanzar con: streamlit run src/ui/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="WC 2026 Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

page = st.sidebar.radio(
    "Navegación",
    ["🔮 Predecir partido", "📊 Fiabilidad del modelo", "⚙️ Estado del modelo"],
)

if page == "🔮 Predecir partido":
    from src.ui.pages.predict import show
    show()
elif page == "📊 Fiabilidad del modelo":
    from src.ui.pages.dashboard import show
    show()
else:
    from src.ui.pages.model_status import show
    show()
```

- [ ] **Crear `src/ui/pages/predict.py`**

```python
"""Página de predicción de partidos y registro de resultados reales."""
import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]

# ── Helpers de fixture y host ──────────────────────────────────────────────────

@st.cache_data
def load_team_names() -> dict[str, str]:
    """Retorna dict openfootball_name → iso_code para los 48 equipos WC 2026."""
    ref = pd.read_csv(ROOT / "data/raw/reference/team_codes_mapping.csv")
    return dict(zip(ref["openfootball_name"], ref["iso_code"]))


@st.cache_data
def load_fixtures() -> pd.DataFrame:
    fix = pd.read_csv(ROOT / "data/processed/matches_2026_fixtures.csv")
    # Solo partidos con equipos reales (no placeholders de playoff)
    name_to_iso = load_team_names()
    fix = fix[fix["team1_name"].isin(name_to_iso) & fix["team2_name"].isin(name_to_iso)].copy()
    return fix


def ground_to_host(ground: str) -> Optional[str]:
    """Detecta si el partido se juega en México, Canadá o USA."""
    ground = ground.lower()
    if any(city in ground for city in ["mexico city","guadalajara","monterrey"]):
        return "MEX"
    if any(city in ground for city in ["toronto","vancouver"]):
        return "CAN"
    return "USA"   # resto de sedes son de USA


@st.cache_resource
def load_predictor():
    pkl = ROOT / "outputs/match_predictor.pkl"
    with open(pkl, "rb") as f:
        return pickle.load(f)


# ── UI ─────────────────────────────────────────────────────────────────────────

def show():
    st.title("🔮 Predecir partido")

    name_to_iso = load_team_names()
    teams = sorted(name_to_iso.keys())

    mode = st.radio("Tipo de partido", ["Mundial 2026 — fixture oficial", "Partido libre / Amistoso"],
                    horizontal=True)

    iso_a, iso_b, host_iso, match_date, ground_label = None, None, None, None, ""

    if mode == "Mundial 2026 — fixture oficial":
        fixtures = load_fixtures()
        fixture_options = [
            f"{row['match_date']} | {row['team1_name']} vs {row['team2_name']} ({row['round']})"
            for _, row in fixtures.iterrows()
        ]
        selected = st.selectbox("Seleccionar partido", fixture_options)
        idx = fixture_options.index(selected)
        row = fixtures.iloc[idx]
        iso_a  = name_to_iso[row["team1_name"]]
        iso_b  = name_to_iso[row["team2_name"]]
        host_iso = ground_to_host(row["ground"])
        match_date = row["match_date"]
        ground_label = row["ground"]
        st.caption(f"📍 Sede: {row['ground']} | Anfitrión detectado: {host_iso}")

    else:
        col1, col2 = st.columns(2)
        team_a_name = col1.selectbox("Equipo A", teams, index=teams.index("Argentina"))
        team_b_name = col2.selectbox("Equipo B", teams, index=teams.index("France"))
        iso_a = name_to_iso[team_a_name]
        iso_b = name_to_iso[team_b_name]
        host_iso = st.selectbox("Anfitrión", ["Ninguno", "MEX", "USA", "CAN"])
        host_iso = None if host_iso == "Ninguno" else host_iso
        match_date = str(st.date_input("Fecha del partido"))

    st.divider()

    if st.button("⚡ Predecir", type="primary", use_container_width=True):
        predictor = load_predictor()
        result = predictor.predict_match(iso_a, iso_b, host_iso=host_iso)
        st.session_state["last_prediction"] = {
            "result": result, "iso_a": iso_a, "iso_b": iso_b,
            "host_iso": host_iso, "match_date": match_date,
            "source": "wc2026" if mode.startswith("Mundial") else "friendly",
        }

    if "last_prediction" in st.session_state:
        pred = st.session_state["last_prediction"]
        r    = pred["result"]
        iso_a_p = pred["iso_a"]
        iso_b_p = pred["iso_b"]

        # ── Resultado 1X2 ────────────────────────────────────────────────────
        st.subheader(f"📊 {iso_a_p} vs {iso_b_p}")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"🏆 {iso_a_p} gana", f"{r['result']['p_home']:.1%}")
        c2.metric("🤝 Empate",           f"{r['result']['p_draw']:.1%}")
        c3.metric(f"🏆 {iso_b_p} gana", f"{r['result']['p_away']:.1%}")
        st.caption(f"Marcador esperado: **{r['result']['expected_score']}** | "
                   f"Más probable: **{r['result']['likely_score']}**")

        # ── Mercados ─────────────────────────────────────────────────────────
        st.subheader("📈 Mercados Over / Under")
        markets = {
            "⚽ Goles":       r["goals"],
            "🚩 Corners":    r["corners"],
            "🟨 Tarjetas":   r["cards"],
            "👟 Disparos":   r["shots"],
            "⚠️ Faltas":    r["fouls"],
        }
        cols = st.columns(len(markets))
        for col, (name, mkt) in zip(cols, markets.items()):
            col.markdown(f"**{name}**")
            col.metric("Expected", mkt["expected_total"])
            lines = {k: v for k, v in mkt.items() if k.startswith("over_")}
            for key, val in lines.items():
                line = key.replace("over_","").replace("_",".")
                under_key = f"under_{key.replace('over_','')}"
                under_val = mkt.get(under_key, 1 - val)
                col.write(f"O{line}: **{val:.0%}** | U{line}: **{under_val:.0%}**")

        # ── Ingresar resultado real ───────────────────────────────────────────
        with st.expander("📝 Ingresar resultado real (actualiza el modelo)"):
            col_g1, col_g2 = st.columns(2)
            goals_a = col_g1.number_input(f"Goles {iso_a_p}", min_value=0, max_value=20, value=0)
            goals_b = col_g2.number_input(f"Goles {iso_b_p}", min_value=0, max_value=20, value=0)

            if st.button("💾 Guardar resultado y actualizar modelo"):
                from src.model.updater import log_result, update_elo, retrain_goals_model
                elo_df = pd.read_csv(ROOT / "data/features/elo_ratings.csv")

                bs = log_result(
                    match_date=pred["match_date"],
                    iso_a=iso_a_p, iso_b=iso_b_p, host_iso=pred["host_iso"],
                    goals_a=goals_a, goals_b=goals_b,
                    p_home=r["result"]["p_home"], p_draw=r["result"]["p_draw"], p_away=r["result"]["p_away"],
                    source=pred["source"],
                )

                # Actualizar Elo
                elo_updated = update_elo(elo_df, iso_a_p, iso_b_p, goals_a, goals_b)
                elo_updated.to_csv(ROOT / "data/features/elo_ratings.csv", index=False)

                # Re-entrenar
                with st.spinner("Re-entrenando modelo con el nuevo resultado..."):
                    retrain_goals_model(elo_updated)

                st.success(f"✅ Resultado guardado. Brier Score de este partido: **{bs:.3f}**")
                st.cache_resource.clear()
                del st.session_state["last_prediction"]
                st.rerun()
```

- [ ] **Verificar que la app arranca sin errores de importación**

```bash
source .venv/bin/activate && python -c "
import sys; sys.argv = ['streamlit']
from src.ui.pages.predict import load_team_names, load_fixtures, ground_to_host
print('team names:', len(load_team_names()))
print('fixtures:', len(load_fixtures()))
print('host Mexico City:', ground_to_host('Mexico City'))
"
```

Esperado: `team names: 48`, `fixtures: ~48` (grupo), `host Mexico City: MEX`

---

## Task 6: `dashboard.py` — fiabilidad acumulada

**Files:**
- Create: `src/ui/pages/dashboard.py`

- [ ] **Crear `src/ui/pages/dashboard.py`**

```python
"""Página de fiabilidad acumulada del modelo."""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
LOG_CSV = ROOT / "data/processed/results_log.csv"


def show():
    st.title("📊 Fiabilidad del modelo")

    if not LOG_CSV.exists():
        st.info("Aún no hay resultados registrados. Predice un partido e ingresa el resultado real.")
        return

    df = pd.read_csv(LOG_CSV)
    if len(df) == 0:
        st.info("El log de resultados está vacío.")
        return

    df["match_date"] = pd.to_datetime(df["match_date"])

    # ── Filtros ──────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)
    sources   = ["Todos"] + df["source"].unique().tolist()
    src_filter = col_f1.selectbox("Fuente", sources)
    if src_filter != "Todos":
        df = df[df["source"] == src_filter]

    # ── Métricas clave ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Partidos registrados", len(df))
    m2.metric("BS acumulado",   f"{df['brier_score'].mean():.4f}")
    m3.metric("Referencia naive", "0.6667")
    mejora = (0.6667 - df["brier_score"].mean()) / 0.6667 * 100
    m4.metric("Mejora vs naive", f"{mejora:.1f}%")

    # ── Gráfica BS partido a partido ─────────────────────────────────────────
    st.subheader("Evolución Brier Score")
    df_sorted = df.sort_values("match_date").reset_index(drop=True)
    df_sorted["bs_rolling5"] = df_sorted["brier_score"].rolling(5, min_periods=1).mean()
    df_sorted["bs_acumulado"] = df_sorted["brier_score"].expanding().mean()

    chart_data = df_sorted[["match_date","brier_score","bs_rolling5","bs_acumulado"]].set_index("match_date")
    st.line_chart(chart_data, use_container_width=True)

    # ── Tabla de partidos ────────────────────────────────────────────────────
    st.subheader("Detalle de partidos")
    df_sorted["resultado"]   = df_sorted["goals_a"].astype(str) + " - " + df_sorted["goals_b"].astype(str)
    df_sorted["match_date_str"] = df_sorted["match_date"].dt.strftime("%Y-%m-%d")
    display_df = df_sorted[["match_date_str","iso_a","iso_b","resultado",
                             "p_home_pred","p_draw_pred","p_away_pred","brier_score","source"]].copy()
    display_df = display_df.rename(columns={"match_date_str": "match_date"})

    st.dataframe(
        display_df[["match_date","iso_a","iso_b","resultado","p_home_pred","p_draw_pred","p_away_pred","brier_score","source"]],
        use_container_width=True,
    )

    # ── Top/Bottom 5 ────────────────────────────────────────────────────────
    col_t, col_b = st.columns(2)
    with col_t:
        st.subheader("✅ Mejores predicciones (BS más bajo)")
        st.dataframe(df_sorted.nsmallest(5, "brier_score")[
            ["match_date","iso_a","iso_b","resultado","brier_score"]
        ], use_container_width=True)
    with col_b:
        st.subheader("❌ Peores predicciones (BS más alto)")
        st.dataframe(df_sorted.nlargest(5, "brier_score")[
            ["match_date","iso_a","iso_b","resultado","brier_score"]
        ], use_container_width=True)
```

---

## Task 7: `model_status.py` — estado del modelo

**Files:**
- Create: `src/ui/pages/model_status.py`

- [ ] **Crear `src/ui/pages/model_status.py`**

```python
"""Página de estado e información del modelo."""
import json
import pickle
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]


@st.cache_resource
def load_predictor():
    with open(ROOT / "outputs/match_predictor.pkl", "rb") as f:
        return pickle.load(f)


def show():
    st.title("⚙️ Estado del modelo")

    predictor = load_predictor()
    model     = predictor.model_goals

    # ── Hiperparámetros ──────────────────────────────────────────────────────
    st.subheader("Hiperparámetros del modelo de goles")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ridge_λ",    model.ridge_lambda)
    c2.metric("decay_rate", model.decay_rate)
    c3.metric("ρ (Dixon-Coles)", f"{model.params_['rho']:.4f}")
    c4.metric("Selecciones en modelo", len(model.teams_))

    # ── Best params de todos los modelos ────────────────────────────────────
    bp_path = ROOT / "outputs/best_params.json"
    if bp_path.exists():
        with open(bp_path) as f:
            best_params = json.load(f)
        st.subheader("Mejores hiperparámetros por mercado")
        bp_df = pd.DataFrame([
            {"mercado": k, **v} for k, v in best_params.items()
        ])
        st.dataframe(bp_df, use_container_width=True)

    # ── Dataset ──────────────────────────────────────────────────────────────
    st.subheader("Dataset de entrenamiento")
    matches = pd.read_csv(ROOT / "data/processed/matches_historical_v2.csv")
    results_log = ROOT / "data/processed/results_log.csv"
    n_log = len(pd.read_csv(results_log)) if results_log.exists() else 0
    col_a, col_b = st.columns(2)
    col_a.metric("Partidos históricos WC", len(matches))
    col_b.metric("Resultados reales ingresados", n_log)

    # ── Top 10 ataque y defensa ──────────────────────────────────────────────
    st.subheader("Top 10 — Parámetro de ataque (α)")
    alpha_sorted = sorted(model.params_["alpha"].items(), key=lambda x: x[1], reverse=True)
    alpha_df = pd.DataFrame(alpha_sorted[:10], columns=["ISO", "α"])
    alpha_df["α"] = alpha_df["α"].round(3)
    st.dataframe(alpha_df, use_container_width=True)

    st.subheader("Top 10 — Parámetro de defensa (β, mayor = peor defensa)")
    beta_sorted = sorted(model.params_["beta"].items(), key=lambda x: x[1], reverse=True)
    beta_df = pd.DataFrame(beta_sorted[:10], columns=["ISO", "β"])
    beta_df["β"] = beta_df["β"].round(3)
    st.dataframe(beta_df, use_container_width=True)

    # ── Re-entrenamiento manual ──────────────────────────────────────────────
    st.subheader("Re-entrenamiento manual")
    st.caption("Re-entrena el modelo de goles con Elo actual + todos los resultados registrados.")
    if st.button("🔄 Re-entrenar ahora", type="secondary"):
        from src.model.updater import retrain_goals_model
        elo_df = pd.read_csv(ROOT / "data/features/elo_ratings.csv")
        with st.spinner("Re-entrenando..."):
            retrain_goals_model(elo_df)
        st.success("✅ Modelo actualizado.")
        st.cache_resource.clear()
        st.rerun()
```

- [ ] **Verificar que la UI completa arranca sin error**

```bash
source .venv/bin/activate && python -c "
from src.ui.pages.predict import load_team_names, load_fixtures
from src.ui.pages.dashboard import LOG_CSV
from src.ui.pages.model_status import load_predictor
print('predict OK')
p = load_predictor()
print('predictor loaded, rho:', p.model_goals.params_.get('rho', 'NOT SET'))
"
```

Esperado: `predict OK`, `predictor loaded, rho: -0.XXXX` (ρ negativo).

- [ ] **Lanzar la UI y verificar manualmente**

```bash
source .venv/bin/activate && streamlit run src/ui/app.py
```

Verificar en el navegador (http://localhost:8501):
1. Página "Predecir": seleccionar ARG vs FRA, pulsar Predecir → ver predicciones con todos los mercados
2. Página "Fiabilidad": muestra mensaje "sin resultados aún"
3. Página "Estado": muestra hiperparámetros, ρ del modelo, top 10 equipos

- [ ] **Correr suite completa de tests**

```bash
pytest tests/ -v 2>&1 | tail -15
```

Esperado: todos en PASS (≥ 46 tests).

---

## Notas de debugging

**Si `test_dc_vs_standard_score_matrix_differs` falla:**
- Verificar que `use_dc=True` realmente añade ρ a θ (check `n_params = 2N+5` vs `2N+4`)
- Imprimir `model.params_["rho"]` — si es 0.0 exacto, el optimizador no movió ρ

**Si la UI no arranca por import error:**
- Asegurarse de lanzar desde el directorio del proyecto: `cd /Users/milton/GitHub/milbet/mundial2026-predictor && streamlit run src/ui/app.py`

**Si `retrain_goals_model` falla con KeyError en elo_rating:**
- `teams_features_v2.csv` puede tener `elo_rating` con otro nombre — verificar con `pd.read_csv(...).columns`

**Si streamlit no está instalado:**
```bash
source .venv/bin/activate && pip install streamlit
```

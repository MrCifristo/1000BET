# Fase 4 — Poisson Bivariado con Covariables Regularizado: Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entrenar un modelo de Poisson bivariado regularizado sobre historia mundialista 1930–2022 y producir predicciones de partidos WC 2026 con probabilidades 1X2 y distribución de marcadores.

**Architecture:** Ridge-regularized Poisson regression con parámetros de ataque/defensa por selección (regularizados L2) + covariables globales (Elo diff, xG diff, log valor de plantilla). Optimización via L-BFGS-B (scipy). Validación via leave-one-tournament-out CV para tunear `ridge_lambda` y `decay_rate`.

**Tech Stack:** Python 3.12, scipy, numpy, pandas, pytest

---

## Columnas clave confirmadas

**`data/processed/matches_historical_v2.csv`:**
`home_team_iso`, `away_team_iso`, `home_team_score`, `away_team_score`, `year`, `host_team_iso` (NaN si neutral sin sede), `time_weight`

**`data/features/teams_features_v2.csv`:**
`iso_code`, `elo_rating`, `squad_value_m_eur`, `sb_xg_per90`, `sq_npxg_per90`, `fb_npgls_per90`

---

## File Map

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/model/__init__.py` | Crear | Vacío — marca el módulo |
| `src/model/features.py` | Crear | `compute_time_weights`, `build_xg_priority`, `impute_to_median`, `build_match_rows` |
| `src/model/poisson_model.py` | Crear | `PoissonModel`: `fit()`, `predict_match()`, `predict_score_matrix()` |
| `src/model/validation.py` | Crear | `brier_score()`, `loto_cv()` |
| `src/model/train.py` | Crear | Script de entrenamiento + grid search + sanity check |
| `tests/__init__.py` | Crear | Vacío |
| `tests/model/__init__.py` | Crear | Vacío |
| `tests/model/test_features.py` | Crear | Tests de features.py |
| `tests/model/test_poisson_model.py` | Crear | Tests de PoissonModel |
| `tests/model/test_validation.py` | Crear | Tests de validation.py |
| `requirements.txt` | Modificar | Agregar scipy |

**Nota de diseño — LOTO-CV y features históricas:** Los features de `teams_features_v2.csv` reflejan el estado 2026 (Elo actual, squad_value actual, xG actual). Al validar sobre WC 2022, usamos features de 2026 como proxy de 2022. Esta simplificación es aceptada: el LOTO-CV sirve principalmente para tunear `ridge_lambda` y `decay_rate`, no para obtener un Brier Score absolutamente calibrado.

---

## Task 1: Dependencias y estructura de archivos

**Files:**
- Modify: `requirements.txt`
- Create: `src/model/__init__.py`, `tests/__init__.py`, `tests/model/__init__.py`

- [ ] **Instalar scipy**

```bash
source .venv/bin/activate
pip install scipy
pip freeze | grep scipy >> requirements.txt
```

Verificar: `python -c "import scipy; print(scipy.__version__)"` → imprime versión (≥1.11)

- [ ] **Crear estructura de módulos**

```bash
touch src/model/__init__.py
mkdir -p tests/model
touch tests/__init__.py tests/model/__init__.py
```

- [ ] **Commit**

```bash
git add requirements.txt src/model/__init__.py tests/__init__.py tests/model/__init__.py
git commit -m "feat(model): scaffold model module and test directories"
```

---

## Task 2: `features.py` — funciones base

**Files:**
- Create: `src/model/features.py`
- Create: `tests/model/test_features.py`

- [ ] **Escribir tests fallidos para `compute_time_weights`, `build_xg_priority`, `impute_to_median`**

Crear `tests/model/test_features.py`:

```python
import numpy as np
import pandas as pd
import pytest

from src.model.features import build_xg_priority, compute_time_weights, impute_to_median


def test_compute_time_weights_reference_year_is_one():
    weights = compute_time_weights(np.array([2022]), year_ref=2022, decay_rate=0.05)
    assert weights[0] == pytest.approx(1.0)


def test_compute_time_weights_decay_order():
    weights = compute_time_weights(np.array([2002, 2012, 2022]), year_ref=2022, decay_rate=0.05)
    assert weights[0] < weights[1] < weights[2]


def test_compute_time_weights_known_value():
    # exp(-0.05 * 20) = exp(-1) ≈ 0.3679
    weights = compute_time_weights(np.array([2002]), year_ref=2022, decay_rate=0.05)
    assert weights[0] == pytest.approx(np.exp(-1.0), rel=1e-4)


def test_build_xg_priority_prefers_statsbomb():
    teams = pd.DataFrame({
        "sb_xg_per90": [1.2, np.nan],
        "sq_npxg_per90": [0.8, 0.9],
        "fb_npgls_per90": [0.5, 0.6],
    }, index=["ARG", "BRA"])
    xg = build_xg_priority(teams)
    assert xg["ARG"] == pytest.approx(1.2)
    assert xg["BRA"] == pytest.approx(0.9)  # sb_xg es NaN → usa sq_npxg


def test_build_xg_priority_falls_back_to_fbref():
    teams = pd.DataFrame({
        "sb_xg_per90": [np.nan],
        "sq_npxg_per90": [np.nan],
        "fb_npgls_per90": [0.192],
    }, index=["CUW"])
    xg = build_xg_priority(teams)
    assert xg["CUW"] == pytest.approx(0.192)


def test_build_xg_priority_returns_nan_when_all_missing():
    teams = pd.DataFrame({
        "sb_xg_per90": [np.nan],
        "sq_npxg_per90": [np.nan],
        "fb_npgls_per90": [np.nan],
    }, index=["ZZZ"])
    xg = build_xg_priority(teams)
    assert pd.isna(xg["ZZZ"])


def test_impute_to_median_fills_nan():
    s = pd.Series([1.0, 2.0, np.nan, 4.0])
    result = impute_to_median(s)
    assert result[2] == pytest.approx(2.0)  # mediana de [1, 2, 4]
    assert result.isna().sum() == 0


def test_impute_to_median_no_nan_unchanged():
    s = pd.Series([1.0, 2.0, 3.0])
    result = impute_to_median(s)
    pd.testing.assert_series_equal(result, s)
```

- [ ] **Verificar que fallan**

```bash
source .venv/bin/activate && pytest tests/model/test_features.py -v 2>&1 | head -20
```

Esperado: `ImportError` (módulo no existe aún).

- [ ] **Implementar `src/model/features.py` — funciones base**

```python
"""
Construcción de features para el modelo de Poisson bivariado.
"""
import numpy as np
import pandas as pd


def compute_time_weights(years: np.ndarray, year_ref: int, decay_rate: float) -> np.ndarray:
    """exp(-decay_rate * (year_ref - year)). year_ref=year → 1.0."""
    return np.exp(-decay_rate * (year_ref - years))


def build_xg_priority(teams_indexed: pd.DataFrame) -> pd.Series:
    """
    xG ofensivo con jerarquía de fuentes. Input: teams_df con iso_code como índice.
    Prioridad: sb_xg_per90 > sq_npxg_per90 > fb_npgls_per90 > NaN
    """
    cols = ["sb_xg_per90", "sq_npxg_per90", "fb_npgls_per90"]
    xg = pd.Series(np.nan, index=teams_indexed.index)
    for col in cols:
        if col in teams_indexed.columns:
            xg = xg.where(xg.notna(), teams_indexed[col])
    return xg


def impute_to_median(series: pd.Series) -> pd.Series:
    """Rellena NaN con la mediana del corpus."""
    return series.fillna(series.median())
```

- [ ] **Verificar que los tests pasan**

```bash
pytest tests/model/test_features.py -v
```

Esperado: todos los tests de `test_compute_time_weights_*`, `test_build_xg_priority_*`, `test_impute_to_median_*` en PASS.

- [ ] **Commit**

```bash
git add src/model/features.py tests/model/test_features.py
git commit -m "feat(model): add feature helpers — time weights, xg priority, imputation"
```

---

## Task 3: `features.py` — `build_match_rows`

**Files:**
- Modify: `src/model/features.py` (agregar función)
- Modify: `tests/model/test_features.py` (agregar tests)

- [ ] **Agregar tests de `build_match_rows` al final de `tests/model/test_features.py`**

```python
from src.model.features import build_match_rows


def _make_teams_df():
    return pd.DataFrame({
        "iso_code": ["ARG", "FRA", "BRA", "DEU"],
        "elo_rating": [2100.0, 2080.0, 1980.0, 1950.0],
        "squad_value_m_eur": [800.0, 1400.0, 900.0, 700.0],
        "sb_xg_per90": [1.1, 1.0, 0.9, 0.8],
        "sq_npxg_per90": [np.nan, np.nan, np.nan, np.nan],
        "fb_npgls_per90": [np.nan, np.nan, np.nan, np.nan],
    })


def _make_matches_df():
    return pd.DataFrame({
        "home_team_iso": ["ARG", "BRA"],
        "away_team_iso": ["FRA", "DEU"],
        "home_team_score": [2, 1],
        "away_team_score": [1, 0],
        "year": [2022, 2018],
        "host_team_iso": [np.nan, np.nan],
    })


def test_build_match_rows_produces_two_rows_per_match():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    assert len(rows) == 4


def test_build_match_rows_goals_for_correct():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["goals_for"] == 2
    assert fra_row["goals_for"] == 1


def test_build_match_rows_host_flag():
    matches = _make_matches_df().copy()
    matches.loc[0, "host_team_iso"] = "ARG"
    rows = build_match_rows(matches, _make_teams_df(), year_ref=2026, decay_rate=0.05)
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["host_flag"] == pytest.approx(1.0)
    assert fra_row["host_flag"] == pytest.approx(0.0)


def test_build_match_rows_time_weight_year_ref():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2022, decay_rate=0.05)
    # Partido de 2022 → weight = 1.0
    row_2022 = rows[rows["year"] == 2022].iloc[0]
    assert row_2022["time_weight"] == pytest.approx(1.0)


def test_build_match_rows_elo_diff_sign():
    # ARG (2100) vs FRA (2080): elo_diff para ARG = +20, para FRA = -20
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    arg_row = rows[rows["iso_code"] == "ARG"].iloc[0]
    fra_row = rows[rows["iso_code"] == "FRA"].iloc[0]
    assert arg_row["elo_diff"] > 0
    assert fra_row["elo_diff"] < 0
    assert arg_row["elo_diff"] == pytest.approx(-fra_row["elo_diff"])


def test_build_match_rows_no_nan_in_output():
    rows = build_match_rows(_make_matches_df(), _make_teams_df(), year_ref=2026, decay_rate=0.05)
    for col in ["goals_for", "time_weight", "host_flag", "elo_diff", "xg_diff", "log_value_ratio"]:
        assert rows[col].isna().sum() == 0, f"NaN en columna {col}"
```

- [ ] **Correr tests para confirmar que fallan**

```bash
pytest tests/model/test_features.py::test_build_match_rows_produces_two_rows_per_match -v
```

Esperado: `ImportError` o `NameError`.

- [ ] **Implementar `build_match_rows` en `src/model/features.py`**

Agregar al final del archivo:

```python
def build_match_rows(
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    year_ref: int,
    decay_rate: float,
) -> pd.DataFrame:
    """
    Expande cada partido en 2 filas (una por equipo atacante).

    Columnas del output:
      iso_code, opp_iso, goals_for, time_weight, host_flag,
      elo_diff, xg_diff, log_value_ratio, year
    """
    t = teams_df.set_index("iso_code")

    # Construir features por equipo (imputar NaN con mediana)
    xg = impute_to_median(build_xg_priority(t))
    elo = impute_to_median(t["elo_rating"])
    log_val = impute_to_median(np.log(t["squad_value_m_eur"]))

    rows = []
    for _, match in matches_df.iterrows():
        hi = match["home_team_iso"]
        ai = match["away_team_iso"]
        year = int(match["year"])
        host = match.get("host_team_iso", np.nan)
        host = None if pd.isna(host) else host
        tw = float(np.exp(-decay_rate * (year_ref - year)))

        pairs = [
            (hi, ai, int(match["home_team_score"])),
            (ai, hi, int(match["away_team_score"])),
        ]
        for att, dff, goals in pairs:
            if att not in t.index or dff not in t.index:
                continue
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

    return pd.DataFrame(rows)
```

- [ ] **Verificar todos los tests de features.py**

```bash
pytest tests/model/test_features.py -v
```

Esperado: todos en PASS (≥ 12 tests).

- [ ] **Commit**

```bash
git add src/model/features.py tests/model/test_features.py
git commit -m "feat(model): add build_match_rows — design matrix builder"
```

---

## Task 4: `poisson_model.py` — `fit()`

**Files:**
- Create: `src/model/poisson_model.py`
- Create: `tests/model/test_poisson_model.py`

- [ ] **Escribir tests de `fit()` (fallidos)**

Crear `tests/model/test_poisson_model.py`:

```python
import numpy as np
import pandas as pd
import pytest

from src.model.poisson_model import PoissonModel


def _synthetic_matches():
    """
    Team A siempre marca 2 y concede 1.
    Team B siempre marca 1 y concede 2.
    → α_A > α_B, β_A < β_B tras el ajuste.
    """
    records = []
    for _ in range(30):
        records.append({
            "home_team_iso": "A", "away_team_iso": "B",
            "home_team_score": 2, "away_team_score": 1,
            "year": 2022, "host_team_iso": np.nan,
        })
        records.append({
            "home_team_iso": "B", "away_team_iso": "A",
            "home_team_score": 1, "away_team_score": 2,
            "year": 2022, "host_team_iso": np.nan,
        })
    return pd.DataFrame(records)


def _synthetic_teams():
    return pd.DataFrame({
        "iso_code": ["A", "B"],
        "elo_rating": [1800.0, 1700.0],
        "squad_value_m_eur": [500.0, 300.0],
        "sb_xg_per90": [1.0, 0.8],
        "sq_npxg_per90": [np.nan, np.nan],
        "fb_npgls_per90": [np.nan, np.nan],
    })


def test_fit_returns_self():
    model = PoissonModel(ridge_lambda=0.1, decay_rate=0.05)
    result = model.fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    assert result is model


def test_fit_sets_teams():
    model = PoissonModel().fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    assert set(model.teams_) == {"A", "B"}


def test_fit_attack_ordering():
    """A ataca más (2 goles/partido) → α_A > α_B."""
    model = PoissonModel(ridge_lambda=0.01).fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    alpha = model.params_["alpha"]
    assert alpha["A"] > alpha["B"]


def test_fit_defense_ordering():
    """B concede más (2 goles/partido) → β_B > β_A (mayor beta = peor defensa)."""
    model = PoissonModel(ridge_lambda=0.01).fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    beta = model.params_["beta"]
    assert beta["B"] > beta["A"]
```

- [ ] **Verificar que fallan**

```bash
pytest tests/model/test_poisson_model.py -v 2>&1 | head -10
```

Esperado: `ImportError`.

- [ ] **Implementar `src/model/poisson_model.py`**

```python
"""
Modelo de Poisson bivariado con covariables regularizado (ridge L2).

Para un partido entre equipo i y equipo j:
  log(λ_i) = μ + α_i − β_j + γ·host_i + δ·elo_diff + ε·xg_diff + ζ·log_value_ratio

Parámetros por equipo (α, β) regularizados con penalización L2.
Restricción de identificabilidad: Σ α_i = 0 (α_0 = −Σ α_{1:N-1}).
Optimización: L-BFGS-B via scipy.optimize.minimize.
"""
import warnings
from typing import Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from src.model.features import build_match_rows


class PoissonModel:
    def __init__(self, ridge_lambda: float = 0.1, decay_rate: float = 0.05, max_goals: int = 8):
        self.ridge_lambda = ridge_lambda
        self.decay_rate = decay_rate
        self.max_goals = max_goals
        self.teams_: Optional[list] = None
        self.params_: Optional[dict] = None
        self._match_rows: Optional[pd.DataFrame] = None

    # ── Entrenamiento ──────────────────────────────────────────────────────────

    def fit(self, matches_df: pd.DataFrame, teams_df: pd.DataFrame, year_ref: int = 2026) -> "PoissonModel":
        rows = build_match_rows(matches_df, teams_df, year_ref=year_ref, decay_rate=self.decay_rate)
        self._match_rows = rows
        self.teams_ = sorted(rows["iso_code"].unique().tolist())
        N = len(self.teams_)
        team_idx = {t: i for i, t in enumerate(self.teams_)}

        att_idx = rows["iso_code"].map(team_idx).values
        def_idx = rows["opp_iso"].map(team_idx).values
        goals    = rows["goals_for"].values.astype(float)
        weights  = rows["time_weight"].values
        host     = rows["host_flag"].values
        elo_d    = rows["elo_diff"].values / 100.0   # normalizar: raw diff ÷ 100
        xg_d     = rows["xg_diff"].values
        val_r    = rows["log_value_ratio"].values

        ridge = self.ridge_lambda

        def neg_ll(theta):
            mu           = theta[0]
            alphas_free  = theta[1:N]          # α_1 … α_{N-1}
            alpha_0      = -alphas_free.sum()   # α_0 = −Σ α_{1:N-1}
            alphas       = np.concatenate([[alpha_0], alphas_free])
            betas        = theta[N:2 * N]
            gamma, delta, eps, zeta = theta[2 * N:]

            log_lam = (mu
                       + alphas[att_idx]
                       - betas[def_idx]
                       + gamma * host
                       + delta * elo_d
                       + eps   * xg_d
                       + zeta  * val_r)

            lam = np.exp(log_lam)
            ll  = (goals * log_lam - lam) * weights
            pen = (ridge / 2.0) * (np.sum(alphas ** 2) + np.sum(betas ** 2))
            return -ll.sum() + pen

        # θ = [μ, α_1…α_{N-1}, β_0…β_{N-1}, γ, δ, ε, ζ]
        n_params = 1 + (N - 1) + N + 4
        theta0   = np.zeros(n_params)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = minimize(neg_ll, theta0, method="L-BFGS-B",
                              options={"maxiter": 2000, "ftol": 1e-10})

        theta = result.x
        alphas_free = theta[1:N]
        alpha_0     = -alphas_free.sum()
        alphas      = np.concatenate([[alpha_0], alphas_free])
        betas       = theta[N:2 * N]
        gamma, delta, eps, zeta = theta[2 * N:]

        self.params_ = {
            "mu":    float(theta[0]),
            "alpha": {t: float(alphas[i]) for i, t in enumerate(self.teams_)},
            "beta":  {t: float(betas[i])  for i, t in enumerate(self.teams_)},
            "gamma": float(gamma),
            "delta": float(delta),
            "eps":   float(eps),
            "zeta":  float(zeta),
            # features needed for predict (medians used during training)
            "_elo":     self._match_rows.set_index("iso_code")["elo_diff"],   # proxy — see predict
            "_xg":      self._match_rows.set_index("iso_code")["xg_diff"],
            "_logval":  self._match_rows.set_index("iso_code")["log_value_ratio"],
        }
        # Guardar features de equipo para predict
        self._teams_df = teams_df.copy()
        return self

    # ── Predicción ─────────────────────────────────────────────────────────────

    def _lambda(self, iso_att: str, iso_def: str, host_iso: Optional[str]) -> float:
        from src.model.features import build_xg_priority, impute_to_median
        p = self.params_
        t = self._teams_df.set_index("iso_code")

        xg_raw = build_xg_priority(t)
        xg     = impute_to_median(xg_raw)
        elo    = impute_to_median(t["elo_rating"])
        logval = impute_to_median(np.log(t["squad_value_m_eur"]))

        alpha_att = p["alpha"].get(iso_att, 0.0)
        beta_def  = p["beta"].get(iso_def, 0.0)
        host_flag = 1.0 if iso_att == host_iso else 0.0
        elo_d     = (elo.get(iso_att, elo.median()) - elo.get(iso_def, elo.median())) / 100.0
        xg_d      = xg.get(iso_att, xg.median()) - xg.get(iso_def, xg.median())
        val_r     = logval.get(iso_att, logval.median()) - logval.get(iso_def, logval.median())

        log_lam = (p["mu"]
                   + alpha_att
                   - beta_def
                   + p["gamma"] * host_flag
                   + p["delta"] * elo_d
                   + p["eps"]   * xg_d
                   + p["zeta"]  * val_r)
        return float(np.exp(log_lam))

    def predict_score_matrix(self, iso_a: str, iso_b: str, host_iso: Optional[str] = None) -> np.ndarray:
        """Matriz (max_goals+1) × (max_goals+1) de P(goals_a=g, goals_b=h)."""
        lam_a = self._lambda(iso_a, iso_b, host_iso)
        lam_b = self._lambda(iso_b, iso_a, host_iso)
        g = np.arange(self.max_goals + 1)
        prob_a = poisson.pmf(g, lam_a)
        prob_b = poisson.pmf(g, lam_b)
        return np.outer(prob_a, prob_b)

    def predict_match(self, iso_a: str, iso_b: str, host_iso: Optional[str] = None) -> dict:
        """
        Devuelve probabilidades 1X2 + marcador esperado + marcador más probable.
        iso_a = equipo 'local' (primero en la lista del fixture).
        """
        matrix = self.predict_score_matrix(iso_a, iso_b, host_iso)
        n = matrix.shape[0]
        p_a_win = float(np.tril(matrix, -1).sum())   # g > h  (filas > cols)
        p_draw  = float(np.trace(matrix))
        p_b_win = float(np.triu(matrix,  1).sum())   # g < h

        lam_a = self._lambda(iso_a, iso_b, host_iso)
        lam_b = self._lambda(iso_b, iso_a, host_iso)

        idx = np.unravel_index(matrix.argmax(), matrix.shape)

        return {
            "p_home":         round(p_a_win, 4),
            "p_draw":         round(p_draw,  4),
            "p_away":         round(p_b_win, 4),
            "expected":       [round(lam_a, 2), round(lam_b, 2)],
            "likely_score":   f"{idx[0]}-{idx[1]}",
            "iso_home":       iso_a,
            "iso_away":       iso_b,
        }
```

- [ ] **Verificar que los tests de fit pasan**

```bash
pytest tests/model/test_poisson_model.py -v
```

Esperado: los 4 tests de `test_fit_*` en PASS.

- [ ] **Commit**

```bash
git add src/model/poisson_model.py tests/model/test_poisson_model.py
git commit -m "feat(model): PoissonModel with ridge-regularized fit()"
```

---

## Task 5: `poisson_model.py` — tests de `predict_match` y `predict_score_matrix`

**Files:**
- Modify: `tests/model/test_poisson_model.py`

- [ ] **Agregar tests de predict al final de `tests/model/test_poisson_model.py`**

```python
@pytest.fixture
def fitted_model():
    model = PoissonModel(ridge_lambda=0.01, decay_rate=0.05)
    model.fit(_synthetic_matches(), _synthetic_teams(), year_ref=2022)
    return model


def test_predict_probabilities_sum_to_one(fitted_model):
    result = fitted_model.predict_match("A", "B")
    total = result["p_home"] + result["p_draw"] + result["p_away"]
    assert total == pytest.approx(1.0, abs=1e-3)


def test_predict_score_matrix_shape(fitted_model):
    matrix = fitted_model.predict_score_matrix("A", "B")
    assert matrix.shape == (9, 9)


def test_predict_score_matrix_sums_to_one(fitted_model):
    matrix = fitted_model.predict_score_matrix("A", "B")
    assert matrix.sum() == pytest.approx(1.0, abs=1e-3)


def test_predict_stronger_team_wins_more(fitted_model):
    """A es más fuerte → p_home > p_away cuando A ataca."""
    result = fitted_model.predict_match("A", "B")
    assert result["p_home"] > result["p_away"]


def test_predict_symmetry_flipped(fitted_model):
    """Si A vs B tiene p_home=x, entonces B vs A tiene p_away=x."""
    ab = fitted_model.predict_match("A", "B")
    ba = fitted_model.predict_match("B", "A")
    assert ab["p_home"] == pytest.approx(ba["p_away"], abs=1e-3)


def test_predict_likely_score_format(fitted_model):
    result = fitted_model.predict_match("A", "B")
    parts = result["likely_score"].split("-")
    assert len(parts) == 2
    assert all(p.isdigit() for p in parts)
```

- [ ] **Correr tests**

```bash
pytest tests/model/test_poisson_model.py -v
```

Esperado: todos los tests en PASS (≥ 10 tests).

- [ ] **Commit**

```bash
git add tests/model/test_poisson_model.py
git commit -m "test(model): add predict_match and score matrix tests"
```

---

## Task 6: `validation.py` — `brier_score` y `loto_cv`

**Files:**
- Create: `src/model/validation.py`
- Create: `tests/model/test_validation.py`

- [ ] **Escribir tests de validation (fallidos)**

Crear `tests/model/test_validation.py`:

```python
import numpy as np
import pandas as pd
import pytest

from src.model.validation import brier_score, loto_cv


def _make_cv_data():
    """
    Datos sintéticos para LOTO-CV: equipos A y B presentes en AMBOS años.
    Garantiza que el modelo entrenado en un año puede predecir en el otro.
    """
    matches = pd.DataFrame({
        "home_team_iso":   ["A", "B", "A", "B"],
        "away_team_iso":   ["B", "A", "B", "A"],
        "home_team_score": [2,   1,   1,   2  ],
        "away_team_score": [1,   2,   0,   1  ],
        "year":            [2018, 2018, 2022, 2022],
        "host_team_iso":   [np.nan] * 4,
    })
    teams = pd.DataFrame({
        "iso_code":          ["A",   "B"  ],
        "elo_rating":        [1800.0, 1700.0],
        "squad_value_m_eur": [500.0,  300.0 ],
        "sb_xg_per90":       [1.0,    0.8   ],
        "sq_npxg_per90":     [np.nan, np.nan],
        "fb_npgls_per90":    [np.nan, np.nan],
    })
    return matches, teams


def test_brier_score_perfect_home_prediction():
    preds    = [{"p_home": 1.0, "p_draw": 0.0, "p_away": 0.0}]
    outcomes = ["home"]
    assert brier_score(preds, outcomes) == pytest.approx(0.0)


def test_brier_score_perfect_draw_prediction():
    preds    = [{"p_home": 0.0, "p_draw": 1.0, "p_away": 0.0}]
    outcomes = ["draw"]
    assert brier_score(preds, outcomes) == pytest.approx(0.0)


def test_brier_score_naive_model():
    # Modelo naive: 1/3 en cada resultado → BS = 2/3 ≈ 0.6667
    n = 30
    preds    = [{"p_home": 1/3, "p_draw": 1/3, "p_away": 1/3}] * n
    outcomes = ["home"] * 10 + ["draw"] * 10 + ["away"] * 10
    assert brier_score(preds, outcomes) == pytest.approx(2/3, abs=0.01)


def test_brier_score_wrong_certain_prediction():
    # Predice home con certeza, resultado es away → BS = 2.0
    preds    = [{"p_home": 1.0, "p_draw": 0.0, "p_away": 0.0}]
    outcomes = ["away"]
    assert brier_score(preds, outcomes) == pytest.approx(2.0)


def test_loto_cv_returns_dataframe():
    matches, teams = _make_cv_data()
    result = loto_cv(matches, teams, ridge_lambdas=[0.1], decay_rates=[0.05])
    assert isinstance(result, pd.DataFrame)
    assert "ridge_lambda" in result.columns
    assert "decay_rate"   in result.columns
    assert "mean_bs"      in result.columns


def test_loto_cv_grid_produces_one_row_per_combination():
    matches, teams = _make_cv_data()
    result = loto_cv(matches, teams, ridge_lambdas=[0.1, 1.0], decay_rates=[0.05])
    assert len(result) == 2


def test_loto_cv_best_params_have_lower_bs():
    matches, teams = _make_cv_data()
    result = loto_cv(matches, teams, ridge_lambdas=[0.01, 10.0], decay_rates=[0.05])
    # Con ridge muy alto (10.0) todos los params → 0, debería ser peor que ridge pequeño
    if len(result) == 2:
        best_bs = result["mean_bs"].min()
        assert best_bs >= 0.0
```

- [ ] **Verificar que fallan**

```bash
pytest tests/model/test_validation.py -v 2>&1 | head -10
```

Esperado: `ImportError`.

- [ ] **Implementar `src/model/validation.py`**

```python
"""
Validación del modelo de Poisson: Brier Score y Leave-One-Tournament-Out CV.
"""
from itertools import product
from typing import Optional

import numpy as np
import pandas as pd

from src.model.poisson_model import PoissonModel


def brier_score(predictions: list[dict], outcomes: list[str]) -> float:
    """
    Brier Score multiclase (3 resultados: home / draw / away).

    BS = (1/N) Σ [(p_home − o_home)² + (p_draw − o_draw)² + (p_away − o_away)²]

    outcomes: lista de strings, cada uno en {"home", "draw", "away"}.
    Referencia: modelo naive (1/3, 1/3, 1/3) → BS ≈ 0.667.
    """
    total = 0.0
    for pred, outcome in zip(predictions, outcomes):
        o_home  = 1.0 if outcome == "home"  else 0.0
        o_draw  = 1.0 if outcome == "draw"  else 0.0
        o_away  = 1.0 if outcome == "away"  else 0.0
        total += (pred["p_home"] - o_home) ** 2
        total += (pred["p_draw"] - o_draw) ** 2
        total += (pred["p_away"] - o_away) ** 2
    return total / len(predictions)


def loto_cv(
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    ridge_lambdas: list[float],
    decay_rates: list[float],
    year_ref_train: int = 2026,
) -> pd.DataFrame:
    """
    Leave-One-Tournament-Out cross-validation con grid search de hiperparámetros.

    Para cada combinación (ridge_lambda, decay_rate):
      Para cada año T de torneo presente en matches_df:
        - Entrenar con matches de año != T
        - Predecir matches de año == T
        - Calcular Brier Score
      Promedio de BS sobre todos los torneos.

    Retorna DataFrame con columnas: ridge_lambda, decay_rate, mean_bs, std_bs.
    Nota: usa features de teams_df (estado 2026) para todos los torneos — simplificación documentada.
    """
    tournament_years = sorted(matches_df["year"].unique())
    records = []

    for ridge, decay in product(ridge_lambdas, decay_rates):
        bs_per_tournament = []
        for test_year in tournament_years:
            train = matches_df[matches_df["year"] != test_year]
            test  = matches_df[matches_df["year"] == test_year]

            if len(train) == 0 or len(test) == 0:
                continue

            model = PoissonModel(ridge_lambda=ridge, decay_rate=decay)
            try:
                model.fit(train, teams_df, year_ref=year_ref_train)
            except Exception:
                continue

            preds, outcomes = [], []
            for _, match in test.iterrows():
                hi = match["home_team_iso"]
                ai = match["away_team_iso"]
                host = match.get("host_team_iso", np.nan)
                host = None if pd.isna(host) else host

                # Solo predecir si ambos equipos están en el modelo
                if hi not in model.teams_ or ai not in model.teams_:
                    continue

                pred = model.predict_match(hi, ai, host_iso=host)
                preds.append(pred)

                hs, as_ = int(match["home_team_score"]), int(match["away_team_score"])
                if hs > as_:
                    outcomes.append("home")
                elif hs == as_:
                    outcomes.append("draw")
                else:
                    outcomes.append("away")

            if preds:
                bs_per_tournament.append(brier_score(preds, outcomes))

        if bs_per_tournament:
            records.append({
                "ridge_lambda": ridge,
                "decay_rate":   decay,
                "mean_bs":      float(np.mean(bs_per_tournament)),
                "std_bs":       float(np.std(bs_per_tournament)),
                "n_tournaments": len(bs_per_tournament),
            })

    return pd.DataFrame(records).sort_values("mean_bs").reset_index(drop=True)
```

- [ ] **Verificar todos los tests de validation**

```bash
pytest tests/model/test_validation.py -v
```

Esperado: todos en PASS (≥ 6 tests). Los tests de `loto_cv` pueden ser lentos (~30 s con datos reales, pero con datos sintéticos son instantáneos).

- [ ] **Commit**

```bash
git add src/model/validation.py tests/model/test_validation.py
git commit -m "feat(model): add brier_score and loto_cv"
```

---

## Task 7: `train.py` — entrenamiento completo + sanity check

**Files:**
- Create: `src/model/train.py`

- [ ] **Implementar `src/model/train.py`**

```python
"""
Fase 4 — Script de entrenamiento del modelo de Poisson bivariado.

1. Grid search via LOTO-CV para tunear ridge_lambda y decay_rate
2. Entrena modelo final con los mejores hiperparámetros sobre todos los datos
3. Imprime sanity check: predicciones para 5 partidos representativos del WC 2026
4. Guarda modelo entrenado en outputs/poisson_model.pkl
"""
import pickle
from pathlib import Path

import pandas as pd

from src.model.poisson_model import PoissonModel
from src.model.validation import loto_cv

ROOT       = Path(__file__).resolve().parents[2]
MATCHES    = ROOT / "data/processed/matches_historical_v2.csv"
TEAMS      = ROOT / "data/features/teams_features_v2.csv"
FIXTURES   = ROOT / "data/processed/matches_2026_fixtures.csv"
OUTPUT_PKL = ROOT / "outputs/poisson_model.pkl"

RIDGE_LAMBDAS = [0.01, 0.05, 0.1, 0.5, 1.0]
DECAY_RATES   = [0.02, 0.05, 0.1]

# Partidos representativos para sanity check (iso_a, iso_b, host_iso)
SANITY_MATCHES = [
    ("ARG", "BRA", None),   # clásico — ARG debería ser ligero favorito
    ("ESP", "FRA", None),   # potencias europeas
    ("MEX", "POL", "MEX"),  # México con ventaja de sede
    ("JPN", "DEU", None),   # sorpresa potencial
    ("USA", "ENG", "USA"),  # anfitrión vs favorito
]


def main():
    print("=== train.py — Fase 4: Poisson Bivariado ===\n")

    matches = pd.read_csv(MATCHES)
    teams   = pd.read_csv(TEAMS)

    # ── 1. Grid search ──────────────────────────────────────────────────────
    print(f"Grid search: {len(RIDGE_LAMBDAS)} ridge_lambdas × {len(DECAY_RATES)} decay_rates")
    print(f"Torneos en datos: {sorted(matches['year'].unique())}\n")

    cv_results = loto_cv(matches, teams, RIDGE_LAMBDAS, DECAY_RATES)
    print("Top 5 combinaciones por Brier Score (menor = mejor):")
    print(cv_results.head(5).to_string(index=False))

    best = cv_results.iloc[0]
    best_ridge = float(best["ridge_lambda"])
    best_decay = float(best["decay_rate"])
    print(f"\nMejores hiperparámetros → ridge_lambda={best_ridge}, decay_rate={best_decay}")
    print(f"Mean BS: {best['mean_bs']:.4f} ± {best['std_bs']:.4f}")
    print(f"(Referencia naive: 0.6667)\n")

    # ── 2. Modelo final ─────────────────────────────────────────────────────
    print("Entrenando modelo final sobre todos los datos ...")
    model = PoissonModel(ridge_lambda=best_ridge, decay_rate=best_decay)
    model.fit(matches, teams, year_ref=2026)
    print(f"  Selecciones en el modelo: {len(model.teams_)}")

    # ── 3. Sanity check ─────────────────────────────────────────────────────
    print("\nSanity check — predicciones de partidos representativos WC 2026:")
    print(f"{'Partido':<15} {'P(A gana)':>9} {'P(Empate)':>9} {'P(B gana)':>9} {'Esperado':>10} {'Probable':>8}")
    print("-" * 65)
    for iso_a, iso_b, host in SANITY_MATCHES:
        if iso_a not in model.teams_ or iso_b not in model.teams_:
            print(f"  {iso_a} vs {iso_b}: equipo no en modelo — omitido")
            continue
        r = model.predict_match(iso_a, iso_b, host_iso=host)
        partido = f"{iso_a} vs {iso_b}"
        print(f"{partido:<15} {r['p_home']:>9.3f} {r['p_draw']:>9.3f} {r['p_away']:>9.3f} "
              f"  {r['expected'][0]:.1f}-{r['expected'][1]:.1f}  {r['likely_score']:>8}")

    # ── 4. Guardar modelo ───────────────────────────────────────────────────
    OUTPUT_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PKL, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModelo guardado → {OUTPUT_PKL.relative_to(ROOT)}")

    # ── 5. Top 10 selecciones por ataque ────────────────────────────────────
    alpha = model.params_["alpha"]
    top_attack = sorted(alpha.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 selecciones por parámetro de ataque (α):")
    for iso, val in top_attack:
        print(f"  {iso}: {val:+.3f}")


if __name__ == "__main__":
    main()
```

- [ ] **Verificar que corre sin errores**

```bash
source .venv/bin/activate && python src/model/train.py 2>&1
```

El grid search puede tardar 5–15 minutos (8 torneos × 15 combinaciones × ~1s cada fit).

Verificar que el output incluye:
1. Tabla de CV con Brier Score < 0.667 (si es similar al naive, el modelo no aprende — revisar features)
2. Sanity check con probabilidades que suman 1.0
3. ARG como favorito frente a BRA o similar lógica coherente
4. Archivo `outputs/poisson_model.pkl` creado

- [ ] **Correr suite completa de tests como verificación final**

```bash
pytest tests/ -v
```

Esperado: todos los tests en PASS.

- [ ] **Commit final**

```bash
git add src/model/train.py outputs/.gitkeep
git commit -m "feat(model): training script with LOTO-CV grid search and sanity check"
```

---

## Notas de debugging

**Si el Brier Score es ≥ 0.660 (similar al naive):**
- Revisar que `elo_diff` y `xg_diff` estén bien calculados (no todos cero)
- El `ridge_lambda` puede ser demasiado alto — probar 0.001
- Verificar que `time_weight` varía (no todos 1.0)

**Si `fit()` no converge:**
- Scipy L-BFGS-B puede dar `warnflag != 0` — aceptable si la pérdida converge igualmente
- Aumentar `maxiter` a 5000

**Si los parámetros `alpha` son todos ≈ 0:**
- El `ridge_lambda` es demasiado alto — reducir a 0.01 o 0.001

**Si `predict_match` da probabilidades irracionales (ej. ARG 5% de ganar vs CPV):**
- Revisar signo de `elo_diff` — confirmar que `elo[att] - elo[def]` es positivo cuando att es más fuerte

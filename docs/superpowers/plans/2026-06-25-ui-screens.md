# UI Screens: Clean Navigation + Deepened Content — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the duplicated/broken Streamlit navigation with a single `st.navigation` menu, and deepen four existing screens with a score heatmap, Monte Carlo tournament forecast, visual bracket, extra reliability metrics, and a searchable ratings table.

**Architecture:** Domain logic (Monte Carlo simulation, evaluation metrics) lives in pure modules under `src/` that are unit-tested without Streamlit. The Streamlit views under `src/ui/views/` only orchestrate and render. The entrypoint `src/ui/app.py` declares pages via `st.navigation`/`st.Page`.

**Tech Stack:** Python 3.12, Streamlit 1.58, pandas, numpy, scipy, matplotlib, pytest. Virtualenv at `.venv` (activate with `source .venv/bin/activate`).

## Global Constraints

- Column names `snake_case`, English. Teams identified by 3-letter codes; the project uses **ISO-3166 alpha-3** (Portugal=`PRT`, Croatia=`HRV`, South Korea=`KOR`).
- Domain logic must NOT import `streamlit`. Views may.
- Keep `matplotlib` as the heatmap renderer — already a dependency.
- All shell commands run from repo root `/Users/milton/GitHub/1000BET` with `.venv` activated.
- Do not commit the pre-existing uncommitted data/model/deploy changes as part of these tasks — `git add` only the exact files each step lists.

---

### Task 1: Migrate navigation to `st.navigation` (rename `pages/` → `views/`)

**Files:**
- Rename: `src/ui/pages/` → `src/ui/views/` (git mv, includes `__init__.py`, `predict.py`, `tournament.py`, `dashboard.py`, `model_status.py`)
- Modify: `src/ui/app.py` (full rewrite)
- Modify: `src/ui/views/tournament.py:21` (import path)

**Interfaces:**
- Consumes: `predict.show`, `tournament.show`, `dashboard.show`, `model_status.show` (each a no-arg function rendering a page).
- Produces: a working single-nav app. No new symbols.

- [ ] **Step 1: Rename the directory (preserves history)**

```bash
git mv src/ui/pages src/ui/views
rm -rf src/ui/views/__pycache__
```

- [ ] **Step 2: Fix the internal import in tournament.py**

In `src/ui/views/tournament.py`, change the line:
```python
from src.ui.pages.predict import load_team_names, ground_to_host
```
to:
```python
from src.ui.views.predict import load_team_names, ground_to_host
```

- [ ] **Step 3: Rewrite the entrypoint `src/ui/app.py`**

Replace the entire file with:
```python
"""
WC 2026 Predictor — UI Streamlit.
Lanzar con: streamlit run src/ui/app.py
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from src.ui.views import predict, tournament, dashboard, model_status

st.set_page_config(
    page_title="WC 2026 Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page(predict.show,      title="Predecir partido",      icon="🔮",
            url_path="predict", default=True),
    st.Page(tournament.show,   title="Torneo",                icon="🏆",
            url_path="tournament"),
    st.Page(dashboard.show,    title="Fiabilidad del modelo", icon="📊",
            url_path="reliability"),
    st.Page(model_status.show, title="Estado del modelo",     icon="⚙️",
            url_path="status"),
]

st.sidebar.title("⚽ WC 2026 Predictor")
st.sidebar.caption("Modelo Poisson bivariado + Dixon-Coles")
st.sidebar.divider()

st.navigation(pages).run()
```

- [ ] **Step 4: Launch the app and verify a single nav with no blank pages**

```bash
source .venv/bin/activate
pkill -f "streamlit run src/ui/app.py" 2>/dev/null; sleep 2
nohup streamlit run src/ui/app.py --server.port 8780 > /tmp/st_nav.log 2>&1 &
for i in $(seq 1 25); do curl -sf http://localhost:8780/_stcore/health >/dev/null 2>&1 && break; sleep 1; done
python - <<'PY'
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
o=Options(); o.binary_location="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
o.add_argument("--headless=new"); o.add_argument("--window-size=1300,900")
d=webdriver.Chrome(options=o)
for path in ["predict","tournament","reliability","status"]:
    d.get(f"http://localhost:8780/{path}"); time.sleep(6)
    main=d.find_element(By.XPATH,"//section[@tabindex='0']").text
    print(path, "LEN", len(main.strip()), "OK" if len(main.strip())>50 else "BLANK!")
d.quit()
PY
```
Expected: each of `predict/tournament/reliability/status` prints `OK` with non-trivial length; no `BLANK!`.

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py src/ui/views
git commit -m "refactor(ui): single st.navigation menu, rename pages->views"
```

---

### Task 2: Evaluation metrics module (`src/evaluation/metrics.py`)

**Files:**
- Create: `src/evaluation/metrics.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Produces:
  - `outcome(goals_a, goals_b) -> str` returns `"home"|"draw"|"away"`.
  - `brier_1x2(df) -> float`, `logloss_1x2(df) -> float`, `rps_1x2(df) -> float`, `hit_rate(df) -> float`.
  - Each takes a DataFrame with columns `goals_a, goals_b, p_home_pred, p_draw_pred, p_away_pred` and returns the mean metric over rows.

- [ ] **Step 1: Write the failing test**

Create `tests/test_metrics.py`:
```python
import numpy as np
import pandas as pd
import pytest

from src.evaluation.metrics import outcome, brier_1x2, logloss_1x2, rps_1x2, hit_rate


def _df(rows):
    return pd.DataFrame(rows, columns=[
        "goals_a", "goals_b", "p_home_pred", "p_draw_pred", "p_away_pred"])


def test_outcome():
    assert outcome(2, 0) == "home"
    assert outcome(1, 1) == "draw"
    assert outcome(0, 3) == "away"


def test_perfect_prediction_scores_zero_brier_and_logloss():
    df = _df([[2, 0, 1.0, 0.0, 0.0]])
    assert brier_1x2(df) == pytest.approx(0.0)
    assert logloss_1x2(df) == pytest.approx(0.0, abs=1e-9)
    assert rps_1x2(df) == pytest.approx(0.0)
    assert hit_rate(df) == pytest.approx(1.0)


def test_naive_third_brier_matches_reference():
    df = _df([[2, 0, 1/3, 1/3, 1/3]])
    # (1/3-1)^2 + (1/3)^2 + (1/3)^2 = 0.6667
    assert brier_1x2(df) == pytest.approx(0.6667, abs=1e-4)


def test_rps_penalizes_distant_errors_more():
    # actual = home; predicting all-away is worse than all-draw
    away = _df([[2, 0, 0.0, 0.0, 1.0]])
    draw = _df([[2, 0, 0.0, 1.0, 0.0]])
    assert rps_1x2(away) > rps_1x2(draw)


def test_hit_rate_counts_argmax_matches():
    df = _df([[2, 0, 0.6, 0.3, 0.1],   # argmax home, actual home -> hit
              [0, 1, 0.6, 0.3, 0.1]])  # argmax home, actual away -> miss
    assert hit_rate(df) == pytest.approx(0.5)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_metrics.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.evaluation.metrics'`

- [ ] **Step 3: Write the implementation**

Create `src/evaluation/metrics.py`:
```python
"""Métricas 1X2 vectorizadas para la UI de fiabilidad. Sin dependencias de UI."""
import numpy as np
import pandas as pd

EPS = 1e-15
_P = ["p_home_pred", "p_draw_pred", "p_away_pred"]


def outcome(goals_a, goals_b) -> str:
    if goals_a > goals_b:
        return "home"
    if goals_a < goals_b:
        return "away"
    return "draw"


def _onehot(df: pd.DataFrame) -> np.ndarray:
    """(n,3) one-hot del resultado real en orden [home, draw, away]."""
    o = np.where(df["goals_a"].values > df["goals_b"].values, 0,
                 np.where(df["goals_a"].values < df["goals_b"].values, 2, 1))
    oh = np.zeros((len(df), 3))
    oh[np.arange(len(df)), o] = 1.0
    return oh


def brier_1x2(df: pd.DataFrame) -> float:
    p = df[_P].values
    return float(((p - _onehot(df)) ** 2).sum(axis=1).mean())


def logloss_1x2(df: pd.DataFrame) -> float:
    p = np.clip(df[_P].values, EPS, 1.0)
    return float((-np.log((p * _onehot(df)).sum(axis=1))).mean())


def rps_1x2(df: pd.DataFrame) -> float:
    p = np.cumsum(df[_P].values, axis=1)[:, :2]
    o = np.cumsum(_onehot(df), axis=1)[:, :2]
    return float(((p - o) ** 2).sum(axis=1).mean())


def hit_rate(df: pd.DataFrame) -> float:
    pred = np.argmax(df[_P].values, axis=1)
    actual = np.argmax(_onehot(df), axis=1)
    return float((pred == actual).mean())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_metrics.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/evaluation/metrics.py tests/test_metrics.py
git commit -m "feat(eval): vectorized 1X2 metrics module (brier/logloss/rps/hit-rate)"
```

---

### Task 3: Deepen Fiabilidad page with extra metrics

**Files:**
- Modify: `src/ui/views/dashboard.py` (metrics row, after line 41)

**Interfaces:**
- Consumes: `src.evaluation.metrics.{brier_1x2, logloss_1x2, rps_1x2, hit_rate}`.

- [ ] **Step 1: Add the import**

At the top of `src/ui/views/dashboard.py`, after `import streamlit as st`, add:
```python
from src.evaluation.metrics import logloss_1x2, rps_1x2, hit_rate
```

- [ ] **Step 2: Add a second metrics row**

In `show()`, immediately after the existing `m4.metric(...)` line (currently line 41) and before `st.divider()`, insert:
```python
    n1, n2, n3, n4 = st.columns(4)
    n1.metric("Aciertos 1X2", f"{hit_rate(df):.0%}")
    n2.metric("Log-loss",     f"{logloss_1x2(df):.4f}")
    n3.metric("RPS",          f"{rps_1x2(df):.4f}")
    n4.metric("Naive RPS",    "0.2222")
```

- [ ] **Step 3: Launch and verify the metrics render**

```bash
source .venv/bin/activate
pkill -f "streamlit run src/ui/app.py" 2>/dev/null; sleep 2
nohup streamlit run src/ui/app.py --server.port 8780 > /tmp/st_rel.log 2>&1 &
for i in $(seq 1 25); do curl -sf http://localhost:8780/_stcore/health >/dev/null 2>&1 && break; sleep 1; done
python - <<'PY'
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
o=Options(); o.binary_location="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
o.add_argument("--headless=new"); o.add_argument("--window-size=1300,1000")
d=webdriver.Chrome(options=o); d.get("http://localhost:8780/reliability"); time.sleep(7)
body=d.find_element(By.TAG_NAME,"body").text
for kw in ["Aciertos 1X2","Log-loss","RPS"]:
    print(kw, "FOUND" if kw in body else "MISSING")
print("errors:", [l for l in body.splitlines() if "Traceback" in l][:2])
d.save_screenshot("/tmp/reliability.png"); d.quit()
PY
```
Expected: `Aciertos 1X2 FOUND`, `Log-loss FOUND`, `RPS FOUND`, no errors. Open `/tmp/reliability.png` to eyeball.

- [ ] **Step 4: Commit**

```bash
git add src/ui/views/dashboard.py
git commit -m "feat(ui): extra reliability metrics (hit-rate, log-loss, RPS)"
```

---

### Task 4: Score matrix heatmap on Predecir page

**Files:**
- Modify: `src/ui/views/predict.py` (imports + after the 1X2 block, ~line 114)

**Interfaces:**
- Consumes: `predictor.model_goals.predict_score_matrix(iso_a, iso_b, host_iso) -> np.ndarray`.

- [ ] **Step 1: Add imports**

At the top of `src/ui/views/predict.py`, add after the existing imports:
```python
import numpy as np
import matplotlib.pyplot as plt
```

- [ ] **Step 2: Add a heatmap helper at module level**

Add this function near the top of `src/ui/views/predict.py` (after `load_predictor`):
```python
def render_score_heatmap(predictor, ia: str, ib: str, host_iso, max_g: int = 6):
    """Heatmap de P(marcador) recortado a [0, max_g] goles por equipo."""
    matrix = predictor.model_goals.predict_score_matrix(ia, ib, host_iso)
    m = matrix[: max_g + 1, : max_g + 1]
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    im = ax.imshow(m, cmap="YlOrRd", origin="upper")
    ax.set_xticks(range(max_g + 1)); ax.set_yticks(range(max_g + 1))
    ax.set_xlabel(f"Goles {ib}"); ax.set_ylabel(f"Goles {ia}")
    bi, bj = np.unravel_index(m.argmax(), m.shape)
    for i in range(max_g + 1):
        for j in range(max_g + 1):
            ax.text(j, i, f"{m[i, j]*100:.0f}", ha="center", va="center",
                    fontsize=7, color="black")
    ax.add_patch(plt.Rectangle((bj - 0.5, bi - 0.5), 1, 1, fill=False,
                               edgecolor="#1f77b4", lw=2.5))
    ax.set_title("Probabilidad por marcador (%)", fontsize=10)
    fig.tight_layout()
    return fig
```

- [ ] **Step 3: Call it after the 1X2 block**

In `show()`, immediately after `render_score_forecast(r["result"])` (currently line 114), insert:
```python
    with st.expander("🔥 Mapa de calor de marcadores", expanded=False):
        predictor = load_predictor()
        st.pyplot(render_score_heatmap(predictor, ia, ib, pred["host_iso"]))
```

- [ ] **Step 4: Launch and verify the heatmap renders**

```bash
source .venv/bin/activate
pkill -f "streamlit run src/ui/app.py" 2>/dev/null; sleep 2
nohup streamlit run src/ui/app.py --server.port 8780 > /tmp/st_pred.log 2>&1 &
for i in $(seq 1 25); do curl -sf http://localhost:8780/_stcore/health >/dev/null 2>&1 && break; sleep 1; done
python - <<'PY'
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
o=Options(); o.binary_location="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
o.add_argument("--headless=new"); o.add_argument("--window-size=1300,1100")
d=webdriver.Chrome(options=o); d.get("http://localhost:8780/predict"); time.sleep(7)
d.find_element(By.XPATH,"//button[.//p[contains(text(),'Predecir')]]").click(); time.sleep(7)
# expand heatmap
try:
    d.find_element(By.XPATH,"//summary[contains(.,'Mapa de calor')]").click(); time.sleep(3)
except Exception as e: print("expander:", repr(e)[:120])
body=d.find_element(By.TAG_NAME,"body").text
print("heatmap title", "FOUND" if "Probabilidad por marcador" in body or "Mapa de calor" in body else "MISSING")
print("img count", len(d.find_elements(By.TAG_NAME,"img")))
print("errors:", [l for l in body.splitlines() if "Traceback" in l][:2])
d.save_screenshot("/tmp/predict_heatmap.png"); d.quit()
PY
```
Expected: heatmap label found, at least one `img`, no errors. Eyeball `/tmp/predict_heatmap.png`.

- [ ] **Step 5: Commit**

```bash
git add src/ui/views/predict.py
git commit -m "feat(ui): score-matrix heatmap on predict page"
```

---

### Task 5: Searchable full ratings table on Estado page

**Files:**
- Modify: `src/ui/views/model_status.py` (after the Top-10 block, before the retrain section ~line 75)

**Interfaces:**
- Consumes: `model.params_["alpha"]`, `model.params_["beta"]` (dict iso→float); `elo_ratings_rolling.csv` cols `iso_code, elo_rating`.

- [ ] **Step 1: Add the searchable table**

In `src/ui/views/model_status.py`, after the `with col_def:` block ends and before the `st.divider()` that precedes "Re-entrenamiento manual" (currently line 75), insert:
```python
    st.divider()
    st.subheader("Ratings por selección (buscable)")
    alpha = model.params_["alpha"]
    beta  = model.params_["beta"]
    elo   = pd.read_csv(ROOT / "data/features/elo_ratings_rolling.csv")
    elo_map = dict(zip(elo["iso_code"], elo["elo_rating"]))
    ratings = pd.DataFrame({
        "ISO":          list(alpha.keys()),
        "α (ataque)":   [round(alpha[k], 3) for k in alpha],
        "β (defensa)":  [round(beta.get(k, float("nan")), 3) for k in alpha],
        "Elo":          [round(elo_map.get(k, float("nan")), 1) for k in alpha],
    }).sort_values("α (ataque)", ascending=False)
    q = st.text_input("Filtrar por ISO (p.ej. ARG, BRA, ESP)", "").strip().upper()
    if q:
        ratings = ratings[ratings["ISO"].str.contains(q, na=False)]
    st.dataframe(ratings, hide_index=True, use_container_width=True)
```

- [ ] **Step 2: Launch and verify the table + filter**

```bash
source .venv/bin/activate
pkill -f "streamlit run src/ui/app.py" 2>/dev/null; sleep 2
nohup streamlit run src/ui/app.py --server.port 8780 > /tmp/st_stat.log 2>&1 &
for i in $(seq 1 25); do curl -sf http://localhost:8780/_stcore/health >/dev/null 2>&1 && break; sleep 1; done
python - <<'PY'
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
o=Options(); o.binary_location="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
o.add_argument("--headless=new"); o.add_argument("--window-size=1300,1100")
d=webdriver.Chrome(options=o); d.get("http://localhost:8780/status"); time.sleep(7)
body=d.find_element(By.TAG_NAME,"body").text
print("table heading", "FOUND" if "Ratings por selección" in body else "MISSING")
print("filter input", "FOUND" if "Filtrar por ISO" in body else "MISSING")
print("errors:", [l for l in body.splitlines() if "Traceback" in l][:2])
d.save_screenshot("/tmp/status_table.png"); d.quit()
PY
```
Expected: both `FOUND`, no errors. Eyeball `/tmp/status_table.png`.

- [ ] **Step 3: Commit**

```bash
git add src/ui/views/model_status.py
git commit -m "feat(ui): searchable per-team ratings table on status page"
```

---

### Task 6: Monte Carlo tournament simulation module

**Files:**
- Create: `src/tournament/montecarlo.py`
- Test: `tests/test_montecarlo.py`

**Interfaces:**
- Consumes: `src.tournament.standings.{load_groups, _elo_lookup, compute_group_table, group_qualifiers, rank_thirds}`, `src.tournament.bracket.{parse_knockout, assign_thirds}`, `predictor.predict_match`, `predictor.model_goals.predict_score_matrix`.
- Produces: `simulate_tournament(results, predictor, n_sims=2000, seed=0) -> pandas.DataFrame` with columns `ISO, p_advance, p_r16, p_qf, p_sf, p_final, p_champion`, one row per team that appears in the bracket, sorted by `p_champion` desc. Probabilities are fractions in `[0,1]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_montecarlo.py`:
```python
import pickle
from pathlib import Path

import pandas as pd
import pytest

from src.tournament.montecarlo import simulate_tournament

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def predictor():
    with open(ROOT / "outputs/match_predictor.pkl", "rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="module")
def results():
    return pd.read_csv(ROOT / "data/processed/wc2026_actual_results.csv")


def test_returns_expected_columns(predictor, results):
    out = simulate_tournament(results, predictor, n_sims=50, seed=0)
    assert list(out.columns) == [
        "ISO", "p_advance", "p_r16", "p_qf", "p_sf", "p_final", "p_champion"]
    assert len(out) > 0


def test_champion_probs_sum_to_one(predictor, results):
    out = simulate_tournament(results, predictor, n_sims=200, seed=0)
    assert out["p_champion"].sum() == pytest.approx(1.0, abs=1e-9)


def test_round_probabilities_are_monotonic(predictor, results):
    out = simulate_tournament(results, predictor, n_sims=200, seed=0)
    for _, r in out.iterrows():
        assert r.p_advance >= r.p_r16 >= r.p_qf >= r.p_sf >= r.p_final >= r.p_champion - 1e-9


def test_deterministic_with_seed(predictor, results):
    a = simulate_tournament(results, predictor, n_sims=100, seed=7)
    b = simulate_tournament(results, predictor, n_sims=100, seed=7)
    pd.testing.assert_frame_equal(a, b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_montecarlo.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.tournament.montecarlo'`

- [ ] **Step 3: Write the implementation**

Create `src/tournament/montecarlo.py`:
```python
"""Monte Carlo del Mundial 2026: probabilidades de avance por ronda y de campeón.

Sin dependencias de Streamlit. Reusa el motor de standings y la estructura del
cuadro KO; simula los partidos de grupos no jugados muestreando un marcador de la
matriz Dixon-Coles, y las eliminatorias muestreando el ganador con la win-prob del
modelo (sin empate: p = P(home)/(P(home)+P(away))).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.tournament.standings import (
    load_groups, _elo_lookup, compute_group_table, group_qualifiers,
)
from src.tournament.bracket import parse_knockout, assign_thirds

ROOT      = Path(__file__).resolve().parents[2]
FIXTURES  = ROOT / "data/processed/matches_2026_fixtures.csv"
MAPPING   = ROOT / "data/raw/reference/team_codes_mapping.csv"

# Rondas del camino principal (excluye "Match for third place").
_ROUND_KEY = {
    "Round of 32": "p_advance",
    "Round of 16": "p_r16",
    "Quarter-final": "p_qf",
    "Semi-final": "p_sf",
    "Final": "p_final",
}
_COLS = ["ISO", "p_advance", "p_r16", "p_qf", "p_sf", "p_final", "p_champion"]


def _ground_host(ground: str) -> str:
    g = str(ground).lower()
    if any(c in g for c in ["mexico city", "guadalajara", "monterrey"]):
        return "MEX"
    if any(c in g for c in ["toronto", "vancouver"]):
        return "CAN"
    return "USA"


def _name_to_iso() -> dict:
    ref = pd.read_csv(MAPPING)
    return dict(zip(ref["openfootball_name"], ref["iso_code"]))


def _unplayed_group_fixtures(results, team_to_group):
    """Lista de (ia, ib, host) de partidos de grupos aún no jugados."""
    name_to_iso = _name_to_iso()
    played = set()
    done = results.dropna(subset=["goals_a", "goals_b"])
    for r in done.itertuples(index=False):
        played.add(frozenset((r.iso_a, r.iso_b)))
    fix = pd.read_csv(FIXTURES)
    md = fix[fix["round"].astype(str).str.startswith("Matchday")]
    out = []
    for r in md.itertuples(index=False):
        ia, ib = name_to_iso.get(r.team1_name), name_to_iso.get(r.team2_name)
        if not ia or not ib:
            continue
        if team_to_group.get(ia) is None or team_to_group.get(ia) != team_to_group.get(ib):
            continue
        if frozenset((ia, ib)) in played:
            continue
        out.append((ia, ib, _ground_host(r.ground)))
    return out


def _played_group_results(results, team_to_group):
    done = results.dropna(subset=["goals_a", "goals_b"]).copy()
    done["goals_a"] = done["goals_a"].astype(int)
    done["goals_b"] = done["goals_b"].astype(int)
    mask = done.apply(
        lambda r: team_to_group.get(r["iso_a"]) is not None
        and team_to_group.get(r["iso_a"]) == team_to_group.get(r["iso_b"]), axis=1)
    return done[mask][["iso_a", "iso_b", "goals_a", "goals_b"]] if mask.any() \
        else done.iloc[0:0][["iso_a", "iso_b", "goals_a", "goals_b"]]


def _resolve_slot(slot, match_no, quals, thirds_map, winners, losers):
    s = str(slot)
    if re.fullmatch(r"[12][A-L]", s):
        return quals.get(s)
    if re.fullmatch(r"3[A-L/]+", s):
        return thirds_map.get(match_no)
    m = re.fullmatch(r"([WL])(\d+)", s)
    if m:
        kind, num = m.group(1), int(m.group(2))
        return winners.get(num) if kind == "W" else losers.get(num)
    return None


def simulate_tournament(results, predictor, n_sims=2000, seed=0):
    rng = np.random.default_rng(seed)
    team_to_group, group_to_teams = load_groups()
    elo = _elo_lookup()
    ko = parse_knockout()

    base_group = _played_group_results(results, team_to_group)
    unplayed = _unplayed_group_fixtures(results, team_to_group)

    # Precompute flattened score-prob vectors for each unplayed group fixture.
    fixture_draws = []
    for ia, ib, host in unplayed:
        mat = predictor.model_goals.predict_score_matrix(ia, ib, host)
        ncol = mat.shape[1]
        fixture_draws.append((ia, ib, mat.ravel(), ncol))

    win_cache = {}

    def win_prob(a, b, host):
        key = (a, b, host)
        if key not in win_cache:
            r = predictor.predict_match(a, b, host_iso=host)["result"]
            ph, pa = r["p_home"], r["p_away"]
            win_cache[key] = ph / (ph + pa) if (ph + pa) > 0 else 0.5
        return win_cache[key]

    ko_rows = list(ko.itertuples(index=False))
    counts = {}  # iso -> {col: int}

    def bump(iso, col):
        counts.setdefault(iso, {c: 0 for c in _COLS[1:]})[col] += 1

    for _ in range(n_sims):
        # 1) sample unplayed group matches
        sampled = []
        for ia, ib, flat, ncol in fixture_draws:
            idx = rng.choice(len(flat), p=flat)
            ga, gb = divmod(int(idx), ncol)
            sampled.append((ia, ib, ga, gb))
        sim_results = pd.concat(
            [base_group, pd.DataFrame(sampled, columns=["iso_a", "iso_b", "goals_a", "goals_b"])],
            ignore_index=True) if sampled else base_group

        # 2) group tables -> qualifiers + thirds
        tables = {grp: compute_group_table(group_to_teams[grp],
                                           sim_results[sim_results["iso_a"].map(team_to_group) == grp],
                                           elo)
                  for grp in group_to_teams}
        quals = group_qualifiers(tables)
        thirds_map = assign_thirds(ko, tables)   # top-8 third seeding (authority)

        # 3) simulate knockout
        winners, losers = {}, {}
        champion = None
        for r in ko_rows:
            ta = _resolve_slot(r.slot_a, r.match_no, quals, thirds_map, winners, losers)
            tb = _resolve_slot(r.slot_b, r.match_no, quals, thirds_map, winners, losers)
            if ta is None or tb is None:
                continue
            col = _ROUND_KEY.get(r.round)
            if col:
                bump(ta, col); bump(tb, col)
            host = _ground_host(r.ground)
            p = win_prob(ta, tb, host)
            if rng.random() < p:
                winners[r.match_no], losers[r.match_no] = ta, tb
            else:
                winners[r.match_no], losers[r.match_no] = tb, ta
            if r.round == "Final":
                champion = winners[r.match_no]
        if champion is not None:
            bump(champion, "p_champion")

    rows = [{"ISO": iso, **{c: counts[iso][c] / n_sims for c in _COLS[1:]}}
            for iso in counts]
    df = pd.DataFrame(rows, columns=_COLS)
    return df.sort_values("p_champion", ascending=False).reset_index(drop=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_montecarlo.py -q`
Expected: PASS (4 passed). If `test_champion_probs_sum_to_one` fails because some sims produce no champion (unresolved Final), inspect `parse_knockout` round names; the Final round label must equal `"Final"`.

- [ ] **Step 5: Commit**

```bash
git add src/tournament/montecarlo.py tests/test_montecarlo.py
git commit -m "feat(tournament): Monte Carlo simulation of advance/champion probabilities"
```

---

### Task 7: Monte Carlo forecast tab on Torneo page

**Files:**
- Modify: `src/ui/views/tournament.py` (imports + add a 4th tab in `show()` ~line 219)

**Interfaces:**
- Consumes: `src.tournament.montecarlo.simulate_tournament`.

- [ ] **Step 1: Add the import**

In `src/ui/views/tournament.py`, after the existing `from src.tournament.bracket import resolve_bracket`, add:
```python
from src.tournament.montecarlo import simulate_tournament
```

- [ ] **Step 2: Add a cached wrapper near the top (after `load_predictor`)**

```python
@st.cache_data(show_spinner=False)
def _simulate(results_csv_mtime: float, n_sims: int):
    """Cacheado por (mtime del CSV de resultados, n_sims) para invalidar al registrar."""
    results = load_results()
    return simulate_tournament(results, load_predictor(), n_sims=n_sims, seed=0)
```

- [ ] **Step 3: Add the tab**

In `show()`, change the tabs line (currently line 219) from:
```python
    tab_g, tab_t, tab_k = st.tabs(["📋 Grupos", "🥉 Terceros", "🗺️ Cuadro KO"])
```
to:
```python
    tab_g, tab_t, tab_k, tab_s = st.tabs(
        ["📋 Grupos", "🥉 Terceros", "🗺️ Cuadro KO", "🎲 Pronóstico"])
```
and after the existing `with tab_k:` block, add:
```python
    with tab_s:
        st.caption("Simulación Monte Carlo del resto del torneo (muestrea marcadores "
                   "de grupos y ganadores de eliminatorias con el modelo).")
        n_sims = st.slider("Número de simulaciones", 500, 5000, 2000, step=500)
        if st.button("🎲 Simular", type="primary"):
            mtime = RESULTS_CSV.stat().st_mtime if RESULTS_CSV.exists() else 0.0
            with st.spinner(f"Simulando {n_sims} torneos..."):
                sim = _simulate(mtime, n_sims)
            st.dataframe(
                sim, hide_index=True, use_container_width=True,
                column_config={
                    c: st.column_config.ProgressColumn(c, format="%.0f%%", min_value=0, max_value=1)
                    for c in ["p_advance", "p_r16", "p_qf", "p_sf", "p_final", "p_champion"]
                },
            )
```

- [ ] **Step 4: Launch and verify the simulation tab**

```bash
source .venv/bin/activate
pkill -f "streamlit run src/ui/app.py" 2>/dev/null; sleep 2
nohup streamlit run src/ui/app.py --server.port 8780 > /tmp/st_sim.log 2>&1 &
for i in $(seq 1 25); do curl -sf http://localhost:8780/_stcore/health >/dev/null 2>&1 && break; sleep 1; done
python - <<'PY'
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
o=Options(); o.binary_location="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
o.add_argument("--headless=new"); o.add_argument("--window-size=1300,1100")
d=webdriver.Chrome(options=o); d.get("http://localhost:8780/tournament"); time.sleep(8)
d.find_element(By.XPATH,"//button[.//p[contains(text(),'Pronóstico')]]").click(); time.sleep(2)
d.find_element(By.XPATH,"//button[.//p[contains(text(),'Simular')]]").click(); time.sleep(12)
body=d.find_element(By.TAG_NAME,"body").text
print("p_champion col", "FOUND" if "p_champion" in body else "MISSING")
print("errors:", [l for l in body.splitlines() if "Traceback" in l][:2])
d.save_screenshot("/tmp/tournament_sim.png"); d.quit()
PY
```
Expected: `p_champion FOUND`, no errors. Eyeball `/tmp/tournament_sim.png` — table sorted by champion probability.

- [ ] **Step 5: Commit**

```bash
git add src/ui/views/tournament.py
git commit -m "feat(ui): Monte Carlo forecast tab on tournament page"
```

---

### Task 8: Visual bracket on Torneo page

**Files:**
- Modify: `src/ui/views/tournament.py` (`render_bracket`, lines 182-204)

**Interfaces:**
- Consumes: the same `bracket` DataFrame (`round, match_no, team_a, team_b, winner, slot_a, slot_b, match_date`).

- [ ] **Step 1: Replace `render_bracket` with a column layout**

In `src/ui/views/tournament.py`, replace the entire `render_bracket` function (lines 182-204) with:
```python
def render_bracket(bracket: pd.DataFrame) -> None:
    name = {v: k for k, v in load_team_names().items()}
    rounds = ["Round of 32", "Round of 16", "Quarter-final",
              "Semi-final", "Match for third place", "Final"]
    es = {"Round of 32": "Ronda de 32", "Round of 16": "Octavos",
          "Quarter-final": "Cuartos", "Semi-final": "Semifinales",
          "Match for third place": "3er puesto", "Final": "Final"}
    present = [r for r in rounds if not bracket[bracket["round"] == r].empty]
    if not present:
        st.info("El cuadro aún no tiene partidos resueltos.")
        return
    cols = st.columns(len(present))
    for col, rnd in zip(cols, present):
        with col:
            st.markdown(f"**{es[rnd]}**")
            for r in bracket[bracket["round"] == rnd].itertuples(index=False):
                a = name.get(r.team_a, r.slot_a) if r.team_a else r.slot_a
                b = name.get(r.team_b, r.slot_b) if r.team_b else r.slot_b
                with st.container(border=True):
                    if r.winner:
                        w = name.get(r.winner, r.winner)
                        st.markdown(f"{'**'+a+'**' if r.winner==r.team_a else a}")
                        st.markdown(f"{'**'+b+'**' if r.winner==r.team_b else b}")
                        st.caption(f"🏆 {w}")
                    else:
                        st.markdown(a); st.markdown(b)
                        st.caption(f"#{r.match_no} · {r.match_date}")
```

- [ ] **Step 2: Launch and verify the visual bracket**

```bash
source .venv/bin/activate
pkill -f "streamlit run src/ui/app.py" 2>/dev/null; sleep 2
nohup streamlit run src/ui/app.py --server.port 8780 > /tmp/st_brk.log 2>&1 &
for i in $(seq 1 25); do curl -sf http://localhost:8780/_stcore/health >/dev/null 2>&1 && break; sleep 1; done
python - <<'PY'
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
o=Options(); o.binary_location="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
o.add_argument("--headless=new"); o.add_argument("--window-size=1500,1000")
d=webdriver.Chrome(options=o); d.get("http://localhost:8780/tournament"); time.sleep(8)
d.find_element(By.XPATH,"//button[.//p[contains(text(),'Cuadro KO')]]").click(); time.sleep(4)
body=d.find_element(By.TAG_NAME,"body").text
print("bracket round", "FOUND" if "Ronda de 32" in body else "MISSING")
print("errors:", [l for l in body.splitlines() if "Traceback" in l][:2])
d.save_screenshot("/tmp/tournament_bracket.png"); d.quit()
PY
```
Expected: `Ronda de 32 FOUND`, no errors. Eyeball `/tmp/tournament_bracket.png` — rounds laid out in columns with bordered cards.

- [ ] **Step 3: Run the full test suite**

Run: `pytest -q`
Expected: PASS (all existing tests + `test_metrics.py` + `test_montecarlo.py`).

- [ ] **Step 4: Commit**

```bash
git add src/ui/views/tournament.py
git commit -m "feat(ui): visual column-based knockout bracket"
```

---

## Self-Review

**Spec coverage:**
- Nav A (rename + st.navigation + import fix) → Task 1 ✓
- (a) heatmap → Task 4 ✓
- (d) Monte Carlo module → Task 6; UI tab → Task 7 ✓
- (e) visual bracket → Task 8 ✓
- (g) metrics module → Task 2; UI display → Task 3 ✓
- (i) searchable ratings table → Task 5 ✓
- Tests `test_montecarlo.py`, `test_metrics.py` → Tasks 6, 2 ✓
- Logic outside UI (montecarlo, metrics) → Tasks 6, 2 ✓

**Placeholder scan:** No TBD/TODO; every code step has full code; every verify step has exact commands + expected output.

**Type consistency:** `simulate_tournament(results, predictor, n_sims, seed) -> DataFrame[_COLS]` defined in Task 6 and consumed identically in Task 7. Metric functions `brier_1x2/logloss_1x2/rps_1x2/hit_rate(df)->float` defined in Task 2, consumed in Task 3. `render_score_heatmap(predictor, ia, ib, host_iso)` self-contained in Task 4. Column names `p_advance/p_r16/p_qf/p_sf/p_final/p_champion` consistent across Tasks 6–7.

**Known risk:** Third-place seeding into the Round of 32 is delegated entirely to `assign_thirds(ko, tables)` (the authority), which selects the best 8 thirds from the full `tables` internally — no extra wiring needed. Verify in Task 6 Step 4 that `assign_thirds` returns a non-empty `{match_no: iso}` once all groups are complete; if empty, the R32 third slots resolve to `None` and those teams won't advance in the sim.

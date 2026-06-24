"""
Banco de experimentos para el rediseño del modelo de goles.

Corre un backtest temporal honesto (sin leakage) sobre los Mundiales 2010–2022 y
compara variantes del PoissonModel y mezclas (blends) con Elo puro, todo contra
las mismas particiones. Cada variante entrena 4 modelos (uno por Mundial,
con cutoff temporal) y se evalúa en Brier multiclase + log-loss.

Uso:
    python -m src.evaluation.experiments            # corre la batería completa
    python -m src.evaluation.experiments --quick    # solo 2018+2022 (rápido)

Filosofía: cada cambio estructural se justifica con números aquí antes de
promoverlo al modelo de producción (train_goals_intl.py).
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.model.poisson_model import PoissonModel
from src.model.features import TOURNAMENT_IMPORTANCE as IMP

ROOT    = Path(__file__).resolve().parents[2]
MATCHES = ROOT / "data/processed/matches_intl_v3.csv"
TEAMS   = ROOT / "data/features/teams_features_v3.csv"

WC_YEARS_FULL  = [2010, 2014, 2018, 2022]
WC_YEARS_QUICK = [2018, 2022]
EPS = 1e-12


# ── Métricas ────────────────────────────────────────────────────────────────

def outcome_of(hs, as_):
    return "home" if hs > as_ else ("draw" if hs == as_ else "away")


def brier_row(ph, pd_, pa, o):
    return ((ph - (o == "home")) ** 2
            + (pd_ - (o == "draw")) ** 2
            + (pa - (o == "away")) ** 2)


def logloss_row(ph, pd_, pa, o):
    p = {"home": ph, "draw": pd_, "away": pa}[o]
    return -np.log(max(p, EPS))


def elo_pure_probs(elo_a, elo_b, draw_rate):
    exp_a = 1.0 / (1.0 + 10.0 ** (-(elo_a - elo_b) / 400.0))
    ph = max(exp_a - 0.5 * draw_rate, 0.0)
    pa = max((1 - exp_a) - 0.5 * draw_rate, 0.0)
    s = ph + draw_rate + pa
    return ph / s, draw_rate / s, pa / s


# ── Backtest por variante ───────────────────────────────────────────────────

def run_variant(model_kwargs: dict, df: pd.DataFrame, teams: pd.DataFrame,
                wc_years: list) -> pd.DataFrame:
    """
    Entrena un modelo por Mundial (cutoff temporal) y devuelve un DataFrame con
    una fila por partido: probs del modelo, probs Elo-puro y el resultado real.
    Las probs de Elo no dependen de la variante, pero se recomputan por fold para
    usar el draw_rate del corpus previo.
    """
    records = []
    for wc_year in wc_years:
        wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"].dt.year == wc_year)]
        if wc.empty:
            continue
        cutoff = wc["date"].min()
        train = df[df["date"] < cutoff]
        draw_rate = float((train["home_team_score"] == train["away_team_score"]).mean())

        model = PoissonModel(**model_kwargs)
        model.fit(train, teams, year_ref=wc_year, impute_missing=True)

        for m in wc.itertuples(index=False):
            hi, ai = m.home_team_iso, m.away_team_iso
            host = None if pd.isna(m.host_team_iso) else m.host_team_iso
            o = outcome_of(int(m.home_team_score), int(m.away_team_score))
            ovr = {hi: float(m.elo_home_pre), ai: float(m.elo_away_pre)}

            pm = model.predict_match(hi, ai, host_iso=host, elo_override=ovr)

            eh = m.elo_home_pre + (100 if host == hi else 0)
            ea = m.elo_away_pre + (100 if host == ai else 0)
            eph, epd, epa = elo_pure_probs(eh, ea, draw_rate)

            records.append({
                "wc_year": wc_year, "outcome": o,
                "m_home": pm["p_home"], "m_draw": pm["p_draw"], "m_away": pm["p_away"],
                "e_home": eph, "e_draw": epd, "e_away": epa,
            })
    return pd.DataFrame(records)


def score(df: pd.DataFrame, ph, pdc, pa) -> tuple[float, float]:
    """Brier y log-loss medios dados arrays de probabilidad alineados con df."""
    bs = [brier_row(a, b, c, o) for a, b, c, o in zip(ph, pdc, pa, df["outcome"])]
    ll = [logloss_row(a, b, c, o) for a, b, c, o in zip(ph, pdc, pa, df["outcome"])]
    return float(np.mean(bs)), float(np.mean(ll))


def blend(df: pd.DataFrame, w: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mezcla log-lineal (log opinion pool): p ∝ p_model^w · p_elo^(1-w)."""
    lm = np.log(np.clip(df[["m_home", "m_draw", "m_away"]].values, EPS, 1))
    le = np.log(np.clip(df[["e_home", "e_draw", "e_away"]].values, EPS, 1))
    z = np.exp(w * lm + (1 - w) * le)
    z /= z.sum(axis=1, keepdims=True)
    return z[:, 0], z[:, 1], z[:, 2]


def best_blend(df: pd.DataFrame) -> tuple[float, float, float]:
    """Barre w∈[0,1] y devuelve (w*, brier*, logloss*) minimizando Brier."""
    best = (None, np.inf, np.inf)
    for w in np.linspace(0, 1, 21):
        ph, pdc, pa = blend(df, w)
        bs, ll = score(df, ph, pdc, pa)
        if bs < best[1]:
            best = (float(w), bs, ll)
    return best


# ── Batería de variantes ────────────────────────────────────────────────────

def round2(df, teams, wc_years):
    """Barrido de ridge (con covariables, sin importancia) + frontera Pareto del
    blend para la mejor config. Objetivo: separar la decisión Brier vs calibración."""
    print(f"RONDA 2 — Barrido de ridge | Mundiales {wc_years}\n")
    ridges = [0.1, 0.3, 0.5, 1.0, 2.0, 5.0]
    results = {}
    print(f"{'ridge (α/β)':<16}{'Brier':>9}{'LogLoss':>9}")
    print("-" * 34)
    for r in ridges:
        res = run_variant(dict(ridge_lambda=r, decay_rate=0.05, use_dc=True,
                               importance_map={}), df, teams, wc_years)
        bs, ll = score(res, res["m_home"], res["m_draw"], res["m_away"])
        results[r] = (res, bs, ll)
        print(f"{r:<16}{bs:>9.4f}{ll:>9.4f}")

    # Mejor por log-loss (objetivo betting) y mejor por Brier
    best_ll = min(results, key=lambda r: results[r][2])
    print(f"\nMejor ridge por log-loss (calibración): {best_ll}")

    res = results[best_ll][0]
    print(f"\nFrontera del blend con Elo (ridge={best_ll}): w=peso del modelo")
    print(f"{'w':>6}{'Brier':>10}{'LogLoss':>10}")
    print("-" * 26)
    for w in [1.0, 0.95, 0.9, 0.85, 0.8, 0.7, 0.5, 0.3, 0.0]:
        ph, pdc, pa = blend(res, w)
        bs, ll = score(res, ph, pdc, pa)
        print(f"{w:>6.2f}{bs:>10.4f}{ll:>10.4f}")
    ebs, ell = score(res, res["e_home"], res["e_draw"], res["e_away"])
    print(f"\nElo puro: Brier {ebs:.4f}  LogLoss {ell:.4f}")


def apply_temperature(probs: np.ndarray, T: float) -> np.ndarray:
    """Temperature scaling: p ∝ p^(1/T). T>1 aplana (menos confiado), T<1 afila."""
    z = np.clip(probs, EPS, 1) ** (1.0 / T)
    return z / z.sum(axis=1, keepdims=True)


def fit_temperature(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Busca T que minimiza log-loss sobre (probs, outcomes). outcomes ∈ {0,1,2}."""
    best_T, best_ll = 1.0, np.inf
    for T in np.linspace(0.5, 3.0, 51):
        cal = apply_temperature(probs, T)
        ll = -np.mean(np.log(np.clip(cal[np.arange(len(cal)), outcomes], EPS, 1)))
        if ll < best_ll:
            best_T, best_ll = float(T), ll
    return best_T


def round3(df, teams, wc_years):
    """Barrido de decay a ridge=1.0 + calibración temperature-scaling honesta
    (leave-one-WC-out: T se ajusta en los otros Mundiales, se aplica al de test)."""
    print(f"RONDA 3 — decay @ ridge=1.0 + calibración | Mundiales {wc_years}\n")
    decays = [0.02, 0.035, 0.05, 0.075, 0.10]
    cache = {}
    print(f"{'decay':<10}{'Brier':>9}{'LogLoss':>9}")
    print("-" * 28)
    for d in decays:
        res = run_variant(dict(ridge_lambda=1.0, decay_rate=d, use_dc=True,
                               importance_map={}), df, teams, wc_years)
        bs, ll = score(res, res["m_home"], res["m_draw"], res["m_away"])
        cache[d] = (res, bs, ll)
        print(f"{d:<10}{bs:>9.4f}{ll:>9.4f}")

    best_d = min(cache, key=lambda d: cache[d][2])
    res = cache[best_d][0].copy()
    print(f"\nMejor decay por log-loss: {best_d}")

    # ── Calibración honesta leave-one-WC-out ────────────────────────────────
    o_map = {"home": 0, "draw": 1, "away": 2}
    res["o_idx"] = res["outcome"].map(o_map)
    probs_all = res[["m_home", "m_draw", "m_away"]].values
    cal_probs = np.zeros_like(probs_all)
    for wc in res["wc_year"].unique():
        te = res["wc_year"] == wc
        tr = ~te
        T = fit_temperature(probs_all[tr.values], res.loc[tr, "o_idx"].values)
        cal_probs[te.values] = apply_temperature(probs_all[te.values], T)

    bs_raw, ll_raw = score(res, probs_all[:, 0], probs_all[:, 1], probs_all[:, 2])
    bs_cal, ll_cal = score(res, cal_probs[:, 0], cal_probs[:, 1], cal_probs[:, 2])
    print(f"\n{'':<22}{'Brier':>9}{'LogLoss':>9}")
    print("-" * 40)
    print(f"{'Sin calibrar':<22}{bs_raw:>9.4f}{ll_raw:>9.4f}")
    print(f"{'Temperature scaling':<22}{bs_cal:>9.4f}{ll_cal:>9.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="solo 2018+2022")
    ap.add_argument("--round2", action="store_true", help="barrido ridge + pareto blend")
    ap.add_argument("--round3", action="store_true", help="decay sweep + calibración")
    args = ap.parse_args()
    wc_years = WC_YEARS_QUICK if args.quick else WC_YEARS_FULL

    if args.round2:
        df = pd.read_csv(MATCHES, parse_dates=["date"])
        teams = pd.read_csv(TEAMS)
        round2(df, teams, wc_years)
        return

    if args.round3:
        df = pd.read_csv(MATCHES, parse_dates=["date"])
        teams = pd.read_csv(TEAMS)
        round3(df, teams, wc_years)
        return

    df = pd.read_csv(MATCHES, parse_dates=["date"])
    teams = pd.read_csv(TEAMS)

    # Variantes a comparar. Cada una es un dict de kwargs de PoissonModel.
    variants = {
        "Baseline (producción actual)":        dict(ridge_lambda=0.1, decay_rate=0.05, use_dc=True),
        "Sin covariables anacrónicas (xg/val)": dict(ridge_lambda=0.1, decay_rate=0.05, use_dc=True,
                                                     use_xg=False, use_value=False),
        "Ridge fuerte α/β (1.0)":               dict(ridge_lambda=1.0, decay_rate=0.05, use_dc=True),
        "Peso por importancia":                 dict(ridge_lambda=0.1, decay_rate=0.05, use_dc=True,
                                                     importance_map=IMP),
        "Combo (sin cov + ridge1 + import)":    dict(ridge_lambda=1.0, decay_rate=0.05, use_dc=True,
                                                     use_xg=False, use_value=False, importance_map=IMP),
    }
    # importance_map default (None) = SIN peso; para activar la tabla se pasa IMP.

    print(f"Backtest temporal — Mundiales {wc_years}\n")
    rows = []
    elo_done = False
    for name, kw in variants.items():
        res = run_variant(kw, df, teams, wc_years)
        bs, ll = score(res, res["m_home"], res["m_draw"], res["m_away"])
        wb, bbs, bll = best_blend(res)
        rows.append((name, bs, ll, wb, bbs, bll))
        if not elo_done:
            ebs, ell = score(res, res["e_home"], res["e_draw"], res["e_away"])
            naive = score(res, [1/3]*len(res), [1/3]*len(res), [1/3]*len(res))
            elo_done = True
        print(f"  ✓ {name}")

    print("\n" + "=" * 92)
    print(f"{'Variante':<38}{'Brier':>9}{'LogLoss':>9}{'  | blend w*':>12}{'Brier*':>9}{'LL*':>9}")
    print("-" * 92)
    for name, bs, ll, wb, bbs, bll in rows:
        print(f"{name:<38}{bs:>9.4f}{ll:>9.4f}{wb:>12.2f}{bbs:>9.4f}{bll:>9.4f}")
    print("-" * 92)
    print(f"{'Elo puro (referencia)':<38}{ebs:>9.4f}{ell:>9.4f}")
    print(f"{'Naive 1/3 (referencia)':<38}{naive[0]:>9.4f}{naive[1]:>9.4f}")
    print("=" * 92)
    print("blend w*: peso del modelo en la mezcla log-lineal con Elo (1.0=solo modelo, 0.0=solo Elo).")
    print("Brier*/LL*: métricas de la mejor mezcla. Menor = mejor en todo.")


if __name__ == "__main__":
    main()

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
        ridge_lambda:   float = 0.1,
        decay_rate:     float = 0.05,
        max_goals:      int   = 8,
        use_dc:         bool  = True,
        use_xg:         bool  = True,
        use_value:      bool  = True,
        importance_map: dict  = None,
    ):
        self.ridge_lambda   = ridge_lambda
        self.decay_rate     = decay_rate
        self.max_goals      = max_goals
        self.use_dc         = use_dc
        self.use_xg         = use_xg
        self.use_value      = use_value
        self.importance_map = importance_map
        self.teams_:    Optional[list]         = None
        self.params_:   Optional[dict]         = None
        self._teams_df: Optional[pd.DataFrame] = None

    # ── Corrección DC ──────────────────────────────────────────────────────────

    @staticmethod
    def _tau(
        g_att:   np.ndarray,
        g_opp:   np.ndarray,
        lam_att: np.ndarray,
        lam_opp: np.ndarray,
        rho:     float,
    ) -> np.ndarray:
        """Factor τ vectorizado para marcadores bajos (≥ 1e-10)."""
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
        matches_df:     pd.DataFrame,
        teams_df:       pd.DataFrame,
        year_ref:       int  = 2026,
        home_score_col: str  = "home_team_score",
        away_score_col: str  = "away_team_score",
        impute_missing: bool = False,
    ) -> "PoissonModel":
        rows = build_match_rows(
            matches_df, teams_df,
            year_ref=year_ref, decay_rate=self.decay_rate,
            home_score_col=home_score_col, away_score_col=away_score_col,
            impute_missing=impute_missing, importance_map=self.importance_map,
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
            betas       = theta[N: 2 * N]
            gamma, delta, eps, zeta = theta[2 * N: 2 * N + 4]
            rho = theta[2 * N + 4] if self.use_dc else 0.0

            log_lam = (mu + alphas[att_idx] - betas[def_idx]
                       + gamma * host + delta * elo_d + eps * xg_d + zeta * val_r)
            lam = np.exp(log_lam)

            ll = (goals * log_lam - lam) * weights

            if self.use_dc:
                n         = len(ll)
                primary   = np.arange(0, n, 2)
                secondary = np.arange(1, n, 2)
                min_len   = min(len(primary), len(secondary))
                primary   = primary[:min_len]
                secondary = secondary[:min_len]

                tau = self._tau(
                    goals[primary].astype(int),
                    goals[secondary].astype(int),
                    lam[primary],
                    lam[secondary],
                    rho,
                )
                ll[primary] += np.log(tau) * weights[primary]

            pen = (ridge / 2.0) * (np.sum(alphas ** 2) + np.sum(betas ** 2))
            return -ll.sum() + pen

        n_params = 1 + (N - 1) + N + 4 + (1 if self.use_dc else 0)
        theta0   = np.zeros(n_params)

        bounds = [(-np.inf, np.inf)] * (2 * N + 4)
        # Ablación de covariables: fijar eps(xg)/zeta(val) a 0 vía bounds degenerados
        # mantiene intacto el indexado de theta. gamma(host) y delta(elo) siempre activos.
        if not self.use_xg:
            bounds[2 * N + 2] = (0.0, 0.0)
        if not self.use_value:
            bounds[2 * N + 3] = (0.0, 0.0)
        if self.use_dc:
            bounds.append((-1.0, 0.0))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = minimize(
                neg_ll, theta0, method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 3000, "ftol": 1e-12},
            )

        theta       = result.x
        alphas_free = theta[1:N]
        alpha_0     = -alphas_free.sum()
        alphas      = np.concatenate([[alpha_0], alphas_free])
        betas       = theta[N: 2 * N]
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

    def _lambda(
        self, iso_att: str, iso_def: str, host_iso: Optional[str],
        elo_override: Optional[dict] = None,
    ) -> float:
        p      = self.params_
        t      = self._teams_df.set_index("iso_code")
        xg     = impute_to_median(build_xg_priority(t))
        elo    = impute_to_median(t["elo_rating"])
        logval = impute_to_median(np.log(t["squad_value_m_eur"]))

        # Elo: por defecto el estático actual de teams_df; si se pasa elo_override
        # (Elo point-in-time para backtest honesto), tiene prioridad.
        def _elo(iso):
            if elo_override is not None and iso in elo_override:
                return elo_override[iso]
            return elo.get(iso, elo.median())

        alpha_att = p["alpha"].get(iso_att, 0.0)
        beta_def  = p["beta"].get(iso_def,  0.0)
        host_flag = 1.0 if iso_att == host_iso else 0.0
        elo_d     = (_elo(iso_att) - _elo(iso_def)) / 100.0
        xg_d      = xg.get(iso_att, xg.median())     - xg.get(iso_def, xg.median())
        val_r     = logval.get(iso_att, logval.median()) - logval.get(iso_def, logval.median())

        log_lam = (p["mu"] + alpha_att - beta_def
                   + p["gamma"] * host_flag + p["delta"] * elo_d
                   + p["eps"] * xg_d + p["zeta"] * val_r)
        return float(np.exp(log_lam))

    def predict_score_matrix(
        self, iso_a: str, iso_b: str, host_iso: Optional[str] = None,
        elo_override: Optional[dict] = None,
    ) -> np.ndarray:
        """Matriz (max_goals+1)² con corrección Dixon-Coles si use_dc=True."""
        lam_a = self._lambda(iso_a, iso_b, host_iso, elo_override)
        lam_b = self._lambda(iso_b, iso_a, host_iso, elo_override)
        g      = np.arange(self.max_goals + 1)
        matrix = np.outer(poisson.pmf(g, lam_a), poisson.pmf(g, lam_b))

        rho = self.params_["rho"]
        if self.use_dc and rho != 0.0:
            matrix[0, 0] *= max(1.0 - lam_a * lam_b * rho, 1e-10)
            matrix[1, 0] *= max(1.0 + lam_b * rho,         1e-10)
            matrix[0, 1] *= max(1.0 + lam_a * rho,         1e-10)
            matrix[1, 1] *= max(1.0 - rho,                 1e-10)
            matrix /= matrix.sum()

        return matrix

    @staticmethod
    def _top_scores(matrix: np.ndarray, k: int = 3) -> list:
        """Top-k marcadores (a-b) por probabilidad, descendente: [(\"2-1\", p), ...]."""
        flat = np.argsort(matrix, axis=None)[::-1][:k]
        out = []
        for f in flat:
            i, j = np.unravel_index(f, matrix.shape)
            out.append((f"{i}-{j}", round(float(matrix[i, j]), 4)))
        return out

    @staticmethod
    def _coherent_score(matrix: np.ndarray, outcome: str) -> str:
        """Marcador más probable RESTRINGIDO al resultado 1X2 `outcome`
        ('home'/'draw'/'away'). Garantiza coherencia entre el 1X2 modal y el
        marcador mostrado (un empate modal → un marcador de empate)."""
        n = matrix.shape[0]
        ii, jj = np.indices(matrix.shape)
        if outcome == "home":
            mask = ii > jj
        elif outcome == "away":
            mask = ii < jj
        else:
            mask = ii == jj
        masked = np.where(mask, matrix, -1.0)
        i, j = np.unravel_index(masked.argmax(), matrix.shape)
        return f"{i}-{j}"

    def predict_match(
        self, iso_a: str, iso_b: str, host_iso: Optional[str] = None,
        elo_override: Optional[dict] = None,
    ) -> dict:
        """Probabilidades 1X2 + goles esperados (λ) + marcadores más probables.

        `likely_score` es el argmax global de la matriz (marcador entero más
        probable, sin restricción). `coherent_score` es el marcador más probable
        DENTRO del resultado 1X2 modal — evita la incoherencia de mostrar p.ej.
        "2-1" cuando el empate es el resultado más probable. `top_scores` lista
        los 3 marcadores más probables con su probabilidad.
        """
        matrix  = self.predict_score_matrix(iso_a, iso_b, host_iso, elo_override)
        p_a_win = float(np.tril(matrix, -1).sum())
        p_draw  = float(np.trace(matrix))
        p_b_win = float(np.triu(matrix,  1).sum())
        lam_a   = self._lambda(iso_a, iso_b, host_iso, elo_override)
        lam_b   = self._lambda(iso_b, iso_a, host_iso, elo_override)

        top     = self._top_scores(matrix, k=3)
        modal   = max((p_a_win, "home"), (p_draw, "draw"), (p_b_win, "away"))[1]
        return {
            "p_home":            round(p_a_win, 4),
            "p_draw":            round(p_draw,  4),
            "p_away":            round(p_b_win, 4),
            "expected":          [round(lam_a, 2), round(lam_b, 2)],
            "likely_score":      top[0][0],
            "likely_score_prob": top[0][1],
            "top_scores":        top,
            "coherent_score":    self._coherent_score(matrix, modal),
            "modal_outcome":     modal,
            "iso_home":          iso_a,
            "iso_away":          iso_b,
        }

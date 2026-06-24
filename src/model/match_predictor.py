"""
MatchPredictor — envuelve 5 PoissonModel (goals, corners, cards, shots, fouls)
y produce el output unificado de predicción para todos los mercados de apuestas.
"""
from typing import Optional

import numpy as np
from scipy.stats import poisson

from src.model.poisson_model import PoissonModel


LINES = {
    "goals":   [1.5, 2.5, 3.5],
    "corners": [8.5, 9.5, 10.5, 11.5],
    "cards":   [2.5, 3.5, 4.5],
    "shots":   [21.5, 24.5, 27.5],
    "fouls":   [19.5, 22.5, 25.5],
}


def _over_under(lam_total: float, line: float) -> tuple[float, float]:
    """P(X > line) y P(X <= line) donde X ~ Poisson(lam_total), line es X.5."""
    k       = int(line)
    p_over  = float(1.0 - poisson.cdf(k, lam_total))
    p_under = float(1.0 - p_over)
    return round(p_over, 4), round(p_under, 4)


def _line_key(line: float) -> str:
    """1.5 → '1_5', 10.5 → '10_5'"""
    return str(line).replace(".", "_")


class MatchPredictor:
    """
    Wrapper sobre 5 PoissonModel independientes.

    Uso:
        predictor = MatchPredictor(model_goals, model_corners, model_cards,
                                   model_shots, model_fouls)
        result = predictor.predict_match("ARG", "FRA", host_iso=None)
    """

    def __init__(
        self,
        model_goals:   PoissonModel,
        model_corners: PoissonModel,
        model_cards:   PoissonModel,
        model_shots:   PoissonModel,
        model_fouls:   PoissonModel,
    ):
        self.model_goals   = model_goals
        self.model_corners = model_corners
        self.model_cards   = model_cards
        self.model_shots   = model_shots
        self.model_fouls   = model_fouls

    def predict_match(
        self,
        iso_a: str,
        iso_b: str,
        host_iso: Optional[str] = None,
    ) -> dict:
        """
        Predice todos los mercados para un partido entre iso_a e iso_b.
        iso_a = equipo listado primero (p_home en result).
        """
        output = {}

        # ── Resultado ─────────────────────────────────────────────────────
        goals_pred = self.model_goals.predict_match(iso_a, iso_b, host_iso)
        output["result"] = {
            "p_home":            goals_pred["p_home"],
            "p_draw":            goals_pred["p_draw"],
            "p_away":            goals_pred["p_away"],
            # Goles esperados (λ de cada equipo), NO un marcador entero.
            "expected_goals":    [goals_pred["expected"][0], goals_pred["expected"][1]],
            "expected_score":    f"{goals_pred['expected'][0]} - {goals_pred['expected'][1]}",
            # Marcador entero más probable (argmax global) con su probabilidad.
            "likely_score":      goals_pred["likely_score"],
            "likely_score_prob": goals_pred["likely_score_prob"],
            "top_scores":        goals_pred["top_scores"],
            # Marcador coherente con el resultado 1X2 modal (empate→empate, etc).
            "coherent_score":    goals_pred["coherent_score"],
            "modal_outcome":     goals_pred["modal_outcome"],
        }

        # ── Goles ─────────────────────────────────────────────────────────
        lam_a     = self.model_goals._lambda(iso_a, iso_b, host_iso)
        lam_b     = self.model_goals._lambda(iso_b, iso_a, host_iso)
        lam_total = lam_a + lam_b

        goals_market: dict = {"expected_total": round(lam_total, 2)}
        for line in LINES["goals"]:
            key = _line_key(line)
            over, under = _over_under(lam_total, line)
            goals_market[f"over_{key}"]  = over
            goals_market[f"under_{key}"] = under

        p_a_scores = float(1.0 - poisson.pmf(0, lam_a))
        p_b_scores = float(1.0 - poisson.pmf(0, lam_b))
        goals_market["btts"] = round(p_a_scores * p_b_scores, 4)
        output["goals"] = goals_market

        # ── Props ─────────────────────────────────────────────────────────
        for market, model in [
            ("corners", self.model_corners),
            ("cards",   self.model_cards),
            ("shots",   self.model_shots),
            ("fouls",   self.model_fouls),
        ]:
            lam_x_a = model._lambda(iso_a, iso_b, host_iso)
            lam_x_b = model._lambda(iso_b, iso_a, host_iso)
            lam_x   = lam_x_a + lam_x_b

            market_dict: dict = {"expected_total": round(lam_x, 2)}
            for line in LINES[market]:
                key = _line_key(line)
                over, under = _over_under(lam_x, line)
                market_dict[f"over_{key}"]  = over
                market_dict[f"under_{key}"] = under

            output[market] = market_dict

        return output

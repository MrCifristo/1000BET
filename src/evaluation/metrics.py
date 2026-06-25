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

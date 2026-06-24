"""
Construcción de features para el modelo de Poisson bivariado.
"""
import numpy as np
import pandas as pd


def compute_time_weights(years: np.ndarray, year_ref: int, decay_rate: float) -> np.ndarray:
    """exp(-decay_rate * (year_ref - year)). year_ref == year → 1.0."""
    return np.exp(-decay_rate * (year_ref - years))


# Peso por importancia de partido (señal predictiva). Los amistosos son ruido
# de baja señal; los torneos competitivos pesan más. Escala inspirada en los K
# de World Football Elo, normalizada a friendly=1.0.
TOURNAMENT_IMPORTANCE = {
    "FIFA World Cup":               3.0,
    "FIFA World Cup qualification": 2.0,
    "UEFA Euro":                    2.5,
    "UEFA Euro qualification":      1.75,
    "Copa América":                 2.5,
    "Copa America":                 2.5,
    "African Cup of Nations":       2.0,
    "AFC Asian Cup":                2.0,
    "Gold Cup":                     1.75,
    "UEFA Nations League":          1.75,
    "CONCACAF Nations League":      1.5,
    "Confederations Cup":           2.0,
    "Friendly":                     1.0,
}
DEFAULT_IMPORTANCE = 1.5  # otras competencias (quals continentales, copas regionales)


def importance_weight(tournament, importance_map=None) -> float:
    """Factor de importancia para un torneo.

    None o {} → SIN peso por importancia (1.0). Es el default deliberado: el banco
    de experimentos mostró que ponderar por importancia EMPEORA el backtest, así que
    producción no lo usa. Para activarlo (p.ej. experimentar) hay que pasar la tabla
    explícita: importance_map=TOURNAMENT_IMPORTANCE."""
    if not importance_map:
        return 1.0
    return float(importance_map.get(tournament, DEFAULT_IMPORTANCE))


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


def build_match_rows(
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    year_ref: int,
    decay_rate: float,
    home_score_col: str = "home_team_score",
    away_score_col: str = "away_team_score",
    impute_missing: bool = False,
    importance_map: dict = None,
) -> pd.DataFrame:
    """
    Expande cada partido en 2 filas (una por equipo atacante).

    Columnas del output:
      iso_code, opp_iso, goals_for, time_weight, host_flag,
      elo_diff, xg_diff, log_value_ratio, year

    importance_map: None → tabla por defecto (amistosos pesan menos que torneos);
    {} (dict vacío) → desactiva el peso por importancia (comportamiento histórico).
    El peso final de cada fila es time_weight = exp(-decay·Δaños) · importancia.

    Elo point-in-time: si matches_df trae las columnas `elo_home_pre`/`elo_away_pre`
    (Elo PRE-partido del corpus internacional, sin leakage), se usan para elo_diff.
    Si no, se cae al Elo estático de teams_df (comportamiento histórico).

    impute_missing=True: para equipos fuera de teams_df (rivales no-WC del corpus
    ampliado) se imputan xg/elo/valor a la mediana en vez de descartar el partido.
    Necesario para el corpus internacional completo (234 selecciones).
    """
    t = teams_df.set_index("iso_code")

    xg      = impute_to_median(build_xg_priority(t))
    elo     = impute_to_median(t["elo_rating"])
    log_val = impute_to_median(np.log(t["squad_value_m_eur"]))
    xg_med, elo_med, val_med = xg.median(), elo.median(), log_val.median()

    has_pit_elo = ("elo_home_pre" in matches_df.columns
                   and "elo_away_pre" in matches_df.columns)

    rows = []
    for _, match in matches_df.iterrows():
        hi   = match["home_team_iso"]
        ai   = match["away_team_iso"]
        year = int(match["year"])
        host = match.get("host_team_iso", np.nan)
        host = None if pd.isna(host) else host
        imp  = importance_weight(match.get("tournament", None), importance_map)
        tw   = float(np.exp(-decay_rate * (year_ref - year))) * imp

        if not impute_missing and (hi not in t.index or ai not in t.index):
            continue

        # Elo point-in-time orientado por equipo local/visitante
        if has_pit_elo:
            elo_h = float(match["elo_home_pre"])
            elo_a = float(match["elo_away_pre"])
        else:
            elo_h = float(elo.get(hi, elo_med))
            elo_a = float(elo.get(ai, elo_med))

        pairs = [
            (hi, ai, int(match[home_score_col]), elo_h, elo_a),
            (ai, hi, int(match[away_score_col]), elo_a, elo_h),
        ]
        for att, dff, goals, elo_att, elo_dff in pairs:
            rows.append({
                "iso_code":        att,
                "opp_iso":         dff,
                "goals_for":       goals,
                "time_weight":     tw,
                "host_flag":       1.0 if att == host else 0.0,
                "elo_diff":        elo_att - elo_dff,
                "xg_diff":         float(xg.get(att, xg_med) - xg.get(dff, xg_med)),
                "log_value_ratio": float(log_val.get(att, val_med) - log_val.get(dff, val_med)),
                "year":            year,
            })

    return pd.DataFrame(rows)

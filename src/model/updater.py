"""
Pipeline de actualización dinámica del modelo (online learning).

- update_elo():          actualiza el Elo rodante tras un resultado real
                         (World Football Elo: K por torneo, margen de gol, localía)
- log_result():          guarda el resultado en results_log.csv con Brier Score
- retrain_goals_model(): re-entrena el modelo de goles con el corpus internacional
                         ampliado (matches_intl_v3) + los resultados registrados
"""
import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

HFA = 100.0  # ventaja de localía en puntos Elo (consistente con 11_elo_rolling.py)

ROOT             = Path(__file__).resolve().parents[2]
ELO_CSV          = ROOT / "data/features/elo_ratings_rolling.csv"
TEAMS_CSV        = ROOT / "data/features/teams_features_v3.csv"
MATCHES_CSV      = ROOT / "data/processed/matches_intl_v3.csv"
RESULTS_LOG_CSV  = ROOT / "data/processed/results_log.csv"
SB_PROPS_CSV     = ROOT / "data/processed/statsbomb_match_props.csv"
PROP_STATS_CSV   = ROOT / "data/features/prop_team_stats.csv"
BEST_PARAMS_JSON = ROOT / "outputs/best_params.json"
PREDICTOR_PKL    = ROOT / "outputs/match_predictor.pkl"

# Mercado de props → (columna home, columna away) en results_log/statsbomb_match_props.
# El nombre del mercado coincide con el atributo model_<mercado> de MatchPredictor.
PROP_COLS = {
    "corners": ("home_corners", "away_corners"),
    "cards":   ("home_yellow",  "away_yellow"),
    "shots":   ("home_shots",   "away_shots"),
    "fouls":   ("home_fouls",   "away_fouls"),
}


def k_for_source(source: str) -> float:
    """K del sistema Elo según el tipo de partido."""
    return 60.0 if source == "wc2026" else 20.0  # mundial vs amistoso


def _g_for(margin: int) -> float:
    """Factor de margen de gol (World Football Elo)."""
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11.0 + margin) / 8.0


def update_elo(
    elo_df:   pd.DataFrame,
    iso_a:    str,
    iso_b:    str,
    goals_a:  int,
    goals_b:  int,
    k:        float = 20.0,
    host_iso: Optional[str] = None,
) -> pd.DataFrame:
    """
    Actualiza el Elo rodante tras el resultado iso_a goals_a — goals_b iso_b.
    Sistema World Football Elo (zero-sum). Retorna una copia del DataFrame.
    elo_df debe tener columnas iso_code, elo_rating (float).
    """
    elo_df = elo_df.copy()
    elo_df["elo_rating"] = elo_df["elo_rating"].astype(float)

    def _get(iso: str) -> float:
        mask = elo_df["iso_code"] == iso
        if not mask.any():
            raise ValueError(f"ISO {iso!r} no encontrado en elo_df")
        return float(elo_df.loc[mask, "elo_rating"].iloc[0])

    elo_a = _get(iso_a)
    elo_b = _get(iso_b)

    # ventaja de localía si alguno es anfitrión
    adj_a = elo_a + (HFA if iso_a == host_iso else 0.0)
    adj_b = elo_b + (HFA if iso_b == host_iso else 0.0)
    expected_a = 1.0 / (1.0 + 10.0 ** ((adj_b - adj_a) / 400.0))

    if goals_a > goals_b:
        score_a = 1.0
    elif goals_a == goals_b:
        score_a = 0.5
    else:
        score_a = 0.0

    g     = _g_for(abs(goals_a - goals_b))
    delta = k * g * (score_a - expected_a)

    elo_df.loc[elo_df["iso_code"] == iso_a, "elo_rating"] = round(elo_a + delta, 1)
    elo_df.loc[elo_df["iso_code"] == iso_b, "elo_rating"] = round(elo_b - delta, 1)
    return elo_df


def log_result(
    match_date:  str,
    iso_a:       str,
    iso_b:       str,
    host_iso:    Optional[str],
    goals_a:     int,
    goals_b:     int,
    p_home:      float,
    p_draw:      float,
    p_away:      float,
    source:      str,
    elo_a_pre:   float,
    elo_b_pre:   float,
    props_real:  Optional[dict] = None,
    log_path:    Path = RESULTS_LOG_CSV,
) -> float:
    """
    Guarda el resultado real en results_log.csv (Elo pre-partido + props reales
    opcionales). Retorna el Brier Score del resultado 1X2.

    props_real: dict {mercado: (valor_iso_a, valor_iso_b)} con mercado ∈
    {"corners","cards","shots","fouls"}. Los mercados ausentes se guardan como NaN.
    """
    if goals_a > goals_b:
        o_home, o_draw, o_away = 1.0, 0.0, 0.0
    elif goals_a == goals_b:
        o_home, o_draw, o_away = 0.0, 1.0, 0.0
    else:
        o_home, o_draw, o_away = 0.0, 0.0, 1.0

    bs = (p_home - o_home)**2 + (p_draw - o_draw)**2 + (p_away - o_away)**2

    record = {
        "match_date":  match_date,
        "iso_a":       iso_a,
        "iso_b":       iso_b,
        "host_iso":    host_iso if host_iso else "",
        "goals_a":     goals_a,
        "goals_b":     goals_b,
        "elo_a_pre":   round(elo_a_pre, 1),
        "elo_b_pre":   round(elo_b_pre, 1),
        "p_home_pred": round(p_home, 4),
        "p_draw_pred": round(p_draw, 4),
        "p_away_pred": round(p_away, 4),
        "brier_score": round(bs, 4),
        "source":      source,
    }
    # Columnas de props (NaN si el mercado no se registró)
    props_real = props_real or {}
    for market, (home_col, away_col) in PROP_COLS.items():
        val = props_real.get(market)
        record[home_col] = val[0] if val is not None else np.nan
        record[away_col] = val[1] if val is not None else np.nan

    row = pd.DataFrame([record])
    if log_path.exists():
        # Leer-concatenar-reescribir: pandas alinea por nombre de columna y rellena
        # NaN, migrando filas antiguas si el esquema evolucionó (p.ej. añadir props).
        existing = pd.read_csv(log_path)
        combined = pd.concat([existing, row], ignore_index=True)
        combined.to_csv(log_path, index=False)
    else:
        row.to_csv(log_path, index=False)
    return bs


def retrain_goals_model(
    elo_df:           pd.DataFrame,
    teams_csv:        Path = TEAMS_CSV,
    matches_csv:      Path = MATCHES_CSV,
    results_log_csv:  Path = RESULTS_LOG_CSV,
    best_params_json: Path = BEST_PARAMS_JSON,
    predictor_pkl:    Path = PREDICTOR_PKL,
) -> None:
    """
    Re-entrena el modelo de goles con:
    1. Elo rodante actualizado (elo_df) → escrito en teams_df
    2. Corpus internacional (matches_intl_v3) + resultados reales registrados
    3. Mejores hiperparámetros de best_params.json

    Actualiza match_predictor.pkl in-place conservando los submodelos de props.
    """
    from src.model.poisson_model import PoissonModel

    teams   = pd.read_csv(teams_csv)
    matches = pd.read_csv(matches_csv)

    # Inyectar el Elo rodante actualizado en teams_df (para predicción 2026)
    teams = teams.drop(columns=["elo_rating"]).merge(
        elo_df[["iso_code", "elo_rating"]], on="iso_code", how="left"
    )

    # Añadir resultados reales registrados al corpus (con elo point-in-time)
    if results_log_csv.exists():
        log = pd.read_csv(results_log_csv)
        if len(log) > 0:
            new_matches = pd.DataFrame({
                "date":            log["match_date"],
                "year":            pd.to_datetime(log["match_date"]).dt.year,
                "tournament":      np.where(log["source"] == "wc2026",
                                            "FIFA World Cup", "Friendly"),
                "home_team_iso":   log["iso_a"],
                "away_team_iso":   log["iso_b"],
                "home_team_score": log["goals_a"],
                "away_team_score": log["goals_b"],
                "neutral_venue":   log["host_iso"].isna() | (log["host_iso"] == ""),
                "host_team_iso":   log["host_iso"].replace("", np.nan),
                "elo_home_pre":    log["elo_a_pre"],
                "elo_away_pre":    log["elo_b_pre"],
            })
            matches = pd.concat([matches, new_matches], ignore_index=True)

    gp = json.load(open(best_params_json))["goals"]
    print("Re-entrenando modelo de goles (corpus internacional) ...")
    new_goals_model = PoissonModel(
        ridge_lambda=gp["ridge_lambda"],
        decay_rate=gp["decay_rate"],
        use_dc=True,
    ).fit(matches, teams, year_ref=2026, impute_missing=True)
    print(f"  ρ (Dixon-Coles): {new_goals_model.params_['rho']:.4f} | "
          f"selecciones: {len(new_goals_model.teams_)}")

    predictor = pickle.load(open(predictor_pkl, "rb"))
    predictor.model_goals = new_goals_model
    with open(predictor_pkl, "wb") as f:
        pickle.dump(predictor, f)
    print(f"  MatchPredictor actualizado → {predictor_pkl.name}")


def retrain_props_models(
    markets:          Optional[list] = None,
    teams_csv:        Path = TEAMS_CSV,
    sb_props_csv:     Path = SB_PROPS_CSV,
    prop_stats_csv:   Path = PROP_STATS_CSV,
    results_log_csv:  Path = RESULTS_LOG_CSV,
    best_params_json: Path = BEST_PARAMS_JSON,
    predictor_pkl:    Path = PREDICTOR_PKL,
) -> list:
    """
    Re-entrena los submodelos de props (corners/cards/shots/fouls) incorporando
    los resultados reales registrados en results_log.csv al corpus StatsBomb.

    markets: lista de mercados a reentrenar (∈ PROP_COLS). None = todos los que
    tengan al menos un dato real nuevo. Retorna la lista de mercados reentrenados.
    """
    from src.model.poisson_model import PoissonModel

    teams = pd.read_csv(teams_csv)
    prop_stats = pd.read_csv(prop_stats_csv)
    teams_df = teams.merge(
        prop_stats[["iso_code", "prop_corners_per90", "prop_yellow_per90",
                    "prop_shots_per90", "prop_fouls_per90"]],
        on="iso_code", how="left",
    )
    sb  = pd.read_csv(sb_props_csv)
    log = pd.read_csv(results_log_csv) if results_log_csv.exists() else None
    bp  = json.load(open(best_params_json))
    predictor = pickle.load(open(predictor_pkl, "rb"))

    targets = markets if markets is not None else list(PROP_COLS)
    retrained = []

    for market in targets:
        home_col, away_col = PROP_COLS[market]

        corpus = sb.copy()
        if log is not None and home_col in log.columns and away_col in log.columns:
            real = log[log[home_col].notna() & log[away_col].notna()]
            if len(real) > 0:
                new = pd.DataFrame({
                    "year":            pd.to_datetime(real["match_date"]).dt.year,
                    "home_team_iso":   real["iso_a"],
                    "away_team_iso":   real["iso_b"],
                    "host_team_iso":   real["host_iso"].replace("", np.nan),
                    home_col:          real[home_col].astype(int),
                    away_col:          real[away_col].astype(int),
                })
                corpus = pd.concat([corpus, new], ignore_index=True)

        gp = bp[market]
        model = PoissonModel(ridge_lambda=gp["ridge_lambda"], decay_rate=gp["decay_rate"])
        model.fit(corpus, teams_df, year_ref=2026,
                  home_score_col=home_col, away_score_col=away_col)
        setattr(predictor, f"model_{market}", model)
        retrained.append(market)

    with open(predictor_pkl, "wb") as f:
        pickle.dump(predictor, f)
    print(f"  Submodelos de props reentrenados: {retrained}")
    return retrained

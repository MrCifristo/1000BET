"""
Carga por lotes de resultados reales del Mundial 2026 al modelo.

Replica EXACTAMENTE el flujo de la app (src/ui/views/predict.py) para cada
partido, en orden cronológico:
  1. Predice con el estado ACTUAL del modelo (captura P(1X2), marcador esperado).
  2. Registra el resultado real en results_log.csv (con Elo pre-partido).
  3. Actualiza el Elo rodante (World Football Elo, K mundial=60, localía).
  4. Reentrena el modelo de goles (el siguiente partido ya aprende del anterior).

Lee data/processed/wc2026_actual_results.csv (solo filas con goles llenos).
Idempotente: salta partidos ya presentes en results_log.csv.

Al final imprime predicción vs realidad + Brier de cada uno y un resumen, para
ver el desempeño del modelo en tiempo real sobre los partidos del torneo.

Uso:
    python -m src.model.load_results
    python -m src.model.load_results --no-retrain   # carga sin reentrenar (rápido)
"""
import argparse
import pickle
from pathlib import Path

import pandas as pd

from src.model.updater import (
    log_result, update_elo, retrain_goals_model, k_for_source,
)

ROOT          = Path(__file__).resolve().parents[2]
RESULTS_CSV   = ROOT / "data/processed/wc2026_actual_results.csv"
RESULTS_LOG   = ROOT / "data/processed/results_log.csv"
ELO_CSV       = ROOT / "data/features/elo_ratings_rolling.csv"
PREDICTOR_PKL = ROOT / "outputs/match_predictor.pkl"


def already_logged(log_df, date, ia, ib) -> bool:
    if log_df is None or len(log_df) == 0:
        return False
    m = ((log_df["match_date"].astype(str) == str(date))
         & (log_df["iso_a"] == ia) & (log_df["iso_b"] == ib))
    return bool(m.any())


def outcome(ga, gb):
    return "home" if ga > gb else ("draw" if ga == gb else "away")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-retrain", action="store_true",
                    help="no reentrena tras cada partido (solo registra + Elo)")
    ap.add_argument("--source", default="wc2026", help="wc2026 | friendly")
    args = ap.parse_args()

    df = pd.read_csv(RESULTS_CSV)
    df = df[df["goals_a"].notna() & df["goals_b"].notna()].copy()
    df["goals_a"] = df["goals_a"].astype(int)
    df["goals_b"] = df["goals_b"].astype(int)
    df = df.sort_values("match_date", kind="stable").reset_index(drop=True)

    print(f"Resultados a cargar: {len(df)} ({RESULTS_CSV.name})\n")

    rows = []
    for r in df.itertuples(index=False):
        ia, ib, host = r.iso_a, r.iso_b, (None if pd.isna(r.host_iso) else r.host_iso)
        ga, gb = int(r.goals_a), int(r.goals_b)

        log_df = pd.read_csv(RESULTS_LOG) if RESULTS_LOG.exists() else None
        if already_logged(log_df, r.match_date, ia, ib):
            print(f"  ⏭  {r.match_date} {ia}-{ib} ya estaba registrado, salto.")
            continue

        # 1. Predicción con el estado actual del modelo
        predictor = pickle.load(open(PREDICTOR_PKL, "rb"))
        pr = predictor.predict_match(ia, ib, host_iso=host)["result"]
        ph, pdr, pa = pr["p_home"], pr["p_draw"], pr["p_away"]
        pred_out = ["home", "draw", "away"][[ph, pdr, pa].index(max(ph, pdr, pa))]

        # 2. Elo pre-partido (point-in-time) + registro
        elo_df    = pd.read_csv(ELO_CSV)
        elo_look  = elo_df.set_index("iso_code")["elo_rating"].astype(float)
        elo_a_pre = float(elo_look.get(ia, elo_look.median()))
        elo_b_pre = float(elo_look.get(ib, elo_look.median()))

        bs = log_result(
            match_date=str(r.match_date), iso_a=ia, iso_b=ib, host_iso=host,
            goals_a=ga, goals_b=gb, p_home=ph, p_draw=pdr, p_away=pa,
            source=args.source, elo_a_pre=elo_a_pre, elo_b_pre=elo_b_pre,
        )

        # 3. Actualiza Elo rodante
        elo_updated = update_elo(elo_df, ia, ib, ga, gb,
                                 k=k_for_source(args.source), host_iso=host)
        elo_updated.to_csv(ELO_CSV, index=False)

        # 4. Reentrena goles (el siguiente partido aprende de este)
        if not args.no_retrain:
            retrain_goals_model(elo_updated)

        act_out = outcome(ga, gb)
        rows.append({
            "date": r.match_date, "match": f"{ia} {ga}-{gb} {ib}",
            "P_home": ph, "P_draw": pdr, "P_away": pa,
            "esperado": f"{pr['expected_score']}", "likely": pr["likely_score"],
            "pred": pred_out, "real": act_out,
            "acierto": pred_out == act_out, "brier": round(bs, 3),
        })
        hit = "✅" if pred_out == act_out else "❌"
        print(f"  {hit} {r.match_date} {ia} {ga}-{gb} {ib:<4} | "
              f"P({ia})={ph:.0%} X={pdr:.0%} P({ib})={pa:.0%} | "
              f"esp {pr['expected_score']} | Brier {bs:.3f}")

    if not rows:
        print("\nNada nuevo que cargar.")
        return

    res = pd.DataFrame(rows)
    print("\n" + "=" * 60)
    print(f"RESUMEN — {len(res)} partidos cargados")
    print("=" * 60)
    print(f"Aciertos 1X2 (argmax):  {res['acierto'].sum()}/{len(res)} "
          f"({res['acierto'].mean():.0%})")
    print(f"Brier medio:            {res['brier'].mean():.4f}")
    print(f"  (referencia: naive 1/3 ≈ 0.667, modelo en backtest ≈ 0.593)")


if __name__ == "__main__":
    main()

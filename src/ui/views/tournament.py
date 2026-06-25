"""
Página 🏆 Torneo — estado del Mundial 2026 (tablas + terceros + cuadro KO) con
interacción todo-en-uno: elegir un fixture jugable → predecir → registrar el
resultado real → el motor recalcula tablas y avanza el cuadro, y el modelo
reentrena.

Fuente de verdad del torneo: data/processed/wc2026_actual_results.csv (lo lee el
motor de standings/bracket). Registrar aquí escribe en ese CSV Y corre el flujo de
aprendizaje (results_log + Elo rodante + reentreno), igual que la página Predecir.
"""
import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from src.tournament.standings import all_standings, rank_thirds
from src.tournament.bracket import resolve_bracket
from src.ui.components import render_score_forecast
from src.ui.views.predict import load_team_names, ground_to_host

ROOT        = Path(__file__).resolve().parents[3]
RESULTS_CSV = ROOT / "data/processed/wc2026_actual_results.csv"
ELO_CSV     = ROOT / "data/features/elo_ratings_rolling.csv"
FIXTURES    = ROOT / "data/processed/matches_2026_fixtures.csv"
PREDICTOR   = ROOT / "outputs/match_predictor.pkl"


# ── Carga de datos ───────────────────────────────────────────────────────────

def load_results() -> pd.DataFrame:
    cols = ["match_date", "team1_name", "team2_name",
            "iso_a", "iso_b", "host_iso", "goals_a", "goals_b"]
    if not RESULTS_CSV.exists():
        return pd.DataFrame(columns=cols)
    return pd.read_csv(RESULTS_CSV)


@st.cache_resource
def load_predictor():
    with open(PREDICTOR, "rb") as f:
        return pickle.load(f)


def _played_keys(results: pd.DataFrame) -> set:
    """Conjunto de {frozenset(iso_a, iso_b)} ya jugados (con goles)."""
    out = set()
    done = results.dropna(subset=["goals_a", "goals_b"])
    for r in done.itertuples(index=False):
        out.add(frozenset((r.iso_a, r.iso_b)))
    return out


# ── Fixtures jugables (grupos pendientes + KO resueltos pendientes) ───────────

def playable_fixtures(results: pd.DataFrame, bracket: pd.DataFrame) -> list[dict]:
    """Lista de partidos predecibles aún no jugados: fase de grupos con equipos
    conocidos + partidos KO con ambos equipos ya resueltos."""
    name_to_iso = load_team_names()
    iso_to_name = {v: k for k, v in name_to_iso.items()}
    played = _played_keys(results)
    out: list[dict] = []

    # Fase de grupos
    fix = pd.read_csv(FIXTURES)
    md  = fix[fix["round"].astype(str).str.startswith("Matchday")]
    for r in md.itertuples(index=False):
        ia, ib = name_to_iso.get(r.team1_name), name_to_iso.get(r.team2_name)
        if not ia or not ib or frozenset((ia, ib)) in played:
            continue
        out.append({
            "label": f"[{r.group}] {r.team1_name} vs {r.team2_name}  ({r.match_date})",
            "iso_a": ia, "iso_b": ib, "host_iso": ground_to_host(str(r.ground)),
            "match_date": str(r.match_date), "ground": str(r.ground),
        })

    # Eliminatorias resueltas pendientes
    for r in bracket.itertuples(index=False):
        if not r.team_a or not r.team_b or r.winner:
            continue
        a_nm, b_nm = iso_to_name.get(r.team_a, r.team_a), iso_to_name.get(r.team_b, r.team_b)
        out.append({
            "label": f"[{r.round} #{r.match_no}] {a_nm} vs {b_nm}  ({r.match_date})",
            "iso_a": r.team_a, "iso_b": r.team_b,
            "host_iso": ground_to_host(str(r.ground)),
            "match_date": str(r.match_date), "ground": str(r.ground),
        })
    return out


# ── Registro de resultado (CSV de torneo + flujo de aprendizaje) ─────────────

def record_result(fx: dict, goals_a: int, goals_b: int) -> float:
    """Persiste el resultado en wc2026_actual_results.csv (idempotente) y corre el
    flujo de aprendizaje (results_log + Elo + reentreno). Devuelve el Brier 1X2."""
    from src.model.updater import (
        log_result, update_elo, retrain_goals_model, k_for_source,
    )
    name_to_iso = load_team_names()
    iso_to_name = {v: k for k, v in name_to_iso.items()}
    ia, ib, host = fx["iso_a"], fx["iso_b"], fx["host_iso"]

    # Predicción actual (para registrar P(1X2) ANTES de reentrenar)
    predictor = load_predictor()
    pr = predictor.predict_match(ia, ib, host_iso=host)["result"]

    # 1. Upsert en el CSV de resultados del torneo
    results = load_results()
    mask = (results["iso_a"] == ia) & (results["iso_b"] == ib)
    row = {
        "match_date": fx["match_date"],
        "team1_name": iso_to_name.get(ia, ia), "team2_name": iso_to_name.get(ib, ib),
        "iso_a": ia, "iso_b": ib, "host_iso": host,
        "goals_a": int(goals_a), "goals_b": int(goals_b),
    }
    results = results[~mask]
    results = pd.concat([results, pd.DataFrame([row])], ignore_index=True)
    results.to_csv(RESULTS_CSV, index=False)

    # 2. Flujo de aprendizaje (igual que predict.py)
    elo_df    = pd.read_csv(ELO_CSV)
    elo_look  = elo_df.set_index("iso_code")["elo_rating"].astype(float)
    elo_a_pre = float(elo_look.get(ia, elo_look.median()))
    elo_b_pre = float(elo_look.get(ib, elo_look.median()))

    bs = log_result(
        match_date=fx["match_date"], iso_a=ia, iso_b=ib, host_iso=host,
        goals_a=int(goals_a), goals_b=int(goals_b),
        p_home=pr["p_home"], p_draw=pr["p_draw"], p_away=pr["p_away"],
        source="wc2026", elo_a_pre=elo_a_pre, elo_b_pre=elo_b_pre,
    )
    elo_updated = update_elo(elo_df, ia, ib, int(goals_a), int(goals_b),
                             k=k_for_source("wc2026"), host_iso=host)
    elo_updated.to_csv(ELO_CSV, index=False)
    retrain_goals_model(elo_updated)
    return bs


# ── Render ───────────────────────────────────────────────────────────────────

_GROUP_COLS = {"team": "Equipo", "Pld": "PJ", "W": "G", "D": "E", "L": "P",
               "GF": "GF", "GA": "GC", "GD": "DG", "Pts": "Pts"}


def render_groups(tables: dict) -> None:
    st.caption("🟢 1º–2º clasifican directo · 🟡 3º (mejores 8 clasifican)")
    groups = sorted(tables)
    for i in range(0, len(groups), 3):
        cols = st.columns(3)
        for col, grp in zip(cols, groups[i:i + 3]):
            with col:
                st.markdown(f"**Grupo {grp}**")
                df = pd.DataFrame(tables[grp])
                disp = df.rename(columns=_GROUP_COLS)[["rank"] + list(_GROUP_COLS.values())]

                def color(row, _df=df):
                    rk = _df.iloc[row.name]["rank"]
                    c = ("rgba(33,195,84,0.18)" if rk <= 2
                         else "rgba(255,193,7,0.18)" if rk == 3 else "")
                    return [f"background-color: {c}"] * len(row)

                st.dataframe(
                    disp.drop(columns=["rank"]).style.apply(color, axis=1),
                    hide_index=True, use_container_width=True,
                )


def render_thirds(tables: dict) -> None:
    thirds = rank_thirds(tables)
    if not any(t["Pld"] > 0 for t in thirds):
        st.info("Aún no hay partidos suficientes para rankear terceros.")
        return
    st.caption("Los **8 mejores terceros** avanzan a la Ronda de 32.")
    rows = [{"Pos": i, "Clasifica": "✅" if i <= 8 else "❌", "Equipo": t["team"],
             "Grupo": t["group"], "Pts": t["Pts"], "DG": t["GD"], "GF": t["GF"],
             "PJ": t["Pld"]}
            for i, t in enumerate(thirds, 1)]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_bracket(bracket: pd.DataFrame) -> None:
    name = {v: k for k, v in load_team_names().items()}
    rounds = ["Round of 32", "Round of 16", "Quarter-final",
              "Semi-final", "Match for third place", "Final"]
    es = {"Round of 32": "Ronda de 32", "Round of 16": "Octavos",
          "Quarter-final": "Cuartos", "Semi-final": "Semifinales",
          "Match for third place": "3er puesto", "Final": "Final"}
    for rnd in rounds:
        sub = bracket[bracket["round"] == rnd]
        if sub.empty:
            continue
        st.markdown(f"**{es[rnd]}**")
        for r in sub.itertuples(index=False):
            a = name.get(r.team_a, r.slot_a) if r.team_a else r.slot_a
            b = name.get(r.team_b, r.slot_b) if r.team_b else r.slot_b
            if r.winner:
                w = name.get(r.winner, r.winner)
                line = f"#{r.match_no} · {a}  vs  {b}  → 🏆 **{w}**"
            elif r.team_a and r.team_b:
                line = f"#{r.match_no} · **{a}**  vs  **{b}**  · _{r.match_date}_ (jugable)"
            else:
                line = f"#{r.match_no} · {a}  vs  {b}  · _{r.match_date}_"
            st.write(line)


# ── Página ───────────────────────────────────────────────────────────────────

def show():
    st.title("🏆 Torneo — Mundial 2026")

    results = load_results()
    tables  = all_standings(results)
    bracket = resolve_bracket(results)

    n_played = int(results.dropna(subset=["goals_a", "goals_b"]).shape[0])
    st.caption(f"Partidos cargados: **{n_played}** / 104")

    tab_g, tab_t, tab_k = st.tabs(["📋 Grupos", "🥉 Terceros", "🗺️ Cuadro KO"])
    with tab_g:
        render_groups(tables)
    with tab_t:
        render_thirds(tables)
    with tab_k:
        render_bracket(bracket)

    # ── Interacción: predecir + registrar un fixture jugable ─────────────────
    st.divider()
    st.subheader("🔮 Predecir y registrar un partido")

    fixtures = playable_fixtures(results, bracket)
    if not fixtures:
        st.success("No hay fixtures jugables pendientes con equipos resueltos.")
        return

    labels = [f["label"] for f in fixtures]
    sel    = st.selectbox("Fixture jugable", labels)
    fx     = fixtures[labels.index(sel)]
    st.caption(f"📍 {fx['ground']} · Anfitrión detectado: **{fx['host_iso']}**")

    if st.button("⚡ Predecir", type="primary"):
        predictor = load_predictor()
        st.session_state["tourney_pred"] = {
            "fx": fx,
            "result": predictor.predict_match(
                fx["iso_a"], fx["iso_b"], host_iso=fx["host_iso"])["result"],
        }

    pred = st.session_state.get("tourney_pred")
    if not pred or pred["fx"]["label"] != fx["label"]:
        return

    r  = pred["result"]
    ia, ib = fx["iso_a"], fx["iso_b"]
    c1, c2, c3 = st.columns(3)
    c1.metric(f"🏆 {ia}", f"{r['p_home']:.1%}")
    c2.metric("🤝 Empate", f"{r['p_draw']:.1%}")
    c3.metric(f"🏆 {ib}", f"{r['p_away']:.1%}")
    render_score_forecast(r)

    with st.expander("📝 Registrar resultado real (avanza el cuadro + reentrena)"):
        g1, g2 = st.columns(2)
        ga = g1.number_input(f"Goles {ia}", 0, 20, 0, key="t_ga")
        gb = g2.number_input(f"Goles {ib}", 0, 20, 0, key="t_gb")
        if st.button("💾 Guardar y actualizar torneo", type="secondary"):
            with st.spinner("Registrando y reentrenando... (~15-30s)"):
                bs = record_result(fx, int(ga), int(gb))
            st.success(f"✅ Guardado. Brier 1X2 de la predicción: **{bs:.3f}**")
            st.cache_resource.clear()
            st.session_state.pop("tourney_pred", None)
            st.rerun()

"""Componentes de UI reutilizables entre páginas (predicción + torneo)."""
import streamlit as st

_OUTCOME_ES = {"home": "victoria local", "draw": "empate", "away": "victoria visitante"}


def render_score_forecast(result: dict) -> None:
    """Muestra el forecast de marcador de forma honesta y coherente.

    `result` es el dict output["result"] de MatchPredictor: trae goles esperados
    (λ), el marcador entero más probable con su probabilidad, el marcador
    coherente con el 1X2 modal, y el top-3 de marcadores.

    Distinción clave (motivo: ver review de forecasting):
      - `expected_goals` (λ) = goles esperados, NO un marcador. Es un valor medio.
      - `likely_score` = marcador entero más probable (argmax global).
      - `coherent_score` = marcador más probable DENTRO del 1X2 modal — evita
        mostrar "2-1" cuando lo más probable es un empate.
    """
    eg = result.get("expected_goals")
    lam_txt = f"{eg[0]:.2f} – {eg[1]:.2f}" if eg else result.get("expected_score", "")

    likely      = result["likely_score"]
    likely_p    = result.get("likely_score_prob")
    coherent    = result.get("coherent_score", likely)
    modal       = _OUTCOME_ES.get(result.get("modal_outcome", ""), "")

    parts = [f"⚽ **Goles esperados (λ):** {lam_txt}"]
    if likely_p is not None:
        parts.append(f"🎯 **Marcador más probable:** {likely} ({likely_p:.0%})")
    else:
        parts.append(f"🎯 **Marcador más probable:** {likely}")
    st.caption("  |  ".join(parts))

    # Solo destacamos el marcador coherente si difiere del argmax global: ahí es
    # donde el argmax engaña (p.ej. el favorito empata pero el modo es 2-1).
    if coherent != likely:
        st.caption(
            f"↳ Coherente con el resultado más probable ({modal}): **{coherent}** "
            f"— el argmax global puede contradecir al 1X2."
        )

    top = result.get("top_scores")
    if top:
        chips = "   ".join(f"`{s}` {p:.0%}" for s, p in top)
        st.caption(f"Top-3 marcadores: {chips}")

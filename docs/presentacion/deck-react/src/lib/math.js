// Utilidades estadísticas reales (Poisson + matriz de marcadores).
// Mismo motor conceptual que src/model/poisson_model.py del proyecto.

export function factorial(n) {
  let f = 1
  for (let k = 2; k <= n; k++) f *= k
  return f
}

export function poissonPmf(k, lambda) {
  return (Math.exp(-lambda) * Math.pow(lambda, k)) / factorial(k)
}

// Distribución de goles P(0..max) para un lambda dado.
export function poissonDist(lambda, max = 6) {
  const out = []
  for (let k = 0; k <= max; k++) out.push(poissonPmf(k, lambda))
  return out
}

// Matriz de marcadores + 1X2, a partir de dos lambdas (ilustrativo del formato de salida).
export function scoreMatrix(lambdaA, lambdaB, G = 6) {
  const m = []
  let total = 0
  let best = 0
  let peak = [0, 0]
  let pHome = 0
  let pDraw = 0
  let pAway = 0
  for (let a = 0; a <= G; a++) {
    m[a] = []
    for (let b = 0; b <= G; b++) {
      const p = poissonPmf(a, lambdaA) * poissonPmf(b, lambdaB)
      m[a][b] = p
      total += p
      if (a > b) pHome += p
      else if (a === b) pDraw += p
      else pAway += p
      if (p > best) {
        best = p
        peak = [a, b]
      }
    }
  }
  return {
    matrix: m,
    total,
    best,
    peak,
    pHome: pHome / total,
    pDraw: pDraw / total,
    pAway: pAway / total,
  }
}

// Escala de calor YlOrRd (la misma del heatmap de la UI Streamlit).
const YLORRD = [
  [255, 255, 178],
  [254, 217, 118],
  [254, 178, 76],
  [253, 141, 60],
  [240, 59, 32],
  [189, 0, 38],
]
export function heatColor(t) {
  const x = Math.max(0, Math.min(1, t)) * (YLORRD.length - 1)
  const lo = Math.floor(x)
  const hi = Math.min(lo + 1, YLORRD.length - 1)
  const f = x - lo
  const c = YLORRD[lo]
  const d = YLORRD[hi]
  const r = Math.round(c[0] + (d[0] - c[0]) * f)
  const g = Math.round(c[1] + (d[1] - c[1]) * f)
  const b = Math.round(c[2] + (d[2] - c[2]) * f)
  return `rgb(${r}, ${g}, ${b})`
}

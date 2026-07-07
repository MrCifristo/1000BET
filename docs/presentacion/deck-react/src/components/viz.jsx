import { Fragment } from 'react'
import { motion } from 'framer-motion'
import { poissonDist, scoreMatrix, heatColor } from '../lib/math.js'
import { AnimatedNumber } from './ui.jsx'

// ============ Pipeline (flujo de pasos) ============
export function Pipeline({ steps }) {
  return (
    <div className="flex flex-col md:flex-row items-stretch gap-2 md:gap-1.5">
      {steps.map((s, i) => (
        <Fragment key={i}>
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 + i * 0.12, type: 'spring', stiffness: 120, damping: 18 }}
            className="glass p-4 md:p-5 flex-1"
          >
            <div className="font-mono text-[12px] md:text-[14px] tracking-[0.12em] uppercase text-pitch">
              {s.tag}
            </div>
            <div className="font-display font-bold text-xl md:text-2xl tracking-tight mt-1">
              {s.title}
            </div>
            <p className="text-ink/70 text-[14px] md:text-[17px] leading-snug mt-1.5">{s.desc}</p>
          </motion.div>
          {i < steps.length - 1 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.32 + i * 0.12 }}
              className="grid place-items-center text-dim text-2xl md:text-xl md:px-1 rotate-90 md:rotate-0"
            >
              →
            </motion.div>
          )}
        </Fragment>
      ))}
    </div>
  )
}

// ============ Poisson bar chart ============
export function PoissonBars({ lambda = 1.8, max = 6 }) {
  const vals = poissonDist(lambda, max)
  const peak = Math.max(...vals)
  return (
    <div>
      <div className="flex items-end gap-2 md:gap-3.5 h-[170px] md:h-[260px]">
        {vals.map((v, k) => (
          <div key={k} className="flex-1 flex flex-col items-center justify-end h-full">
            <span className="font-mono text-[12px] md:text-[15px] text-dim mb-1.5">
              {Math.round(v * 100)}%
            </span>
            <motion.div
              className="w-full bg-gradient-to-t from-goal/40 to-goal"
              initial={{ height: 0 }}
              animate={{ height: `${(v / peak) * 100}%` }}
              transition={{ delay: 0.2 + k * 0.06, type: 'spring', stiffness: 90, damping: 16 }}
            />
            <span className="font-mono text-[13px] md:text-[16px] text-ink/70 mt-2">{k}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============ Score heatmap ============
export function Heatmap({ lambdaA = 1.9, lambdaB = 1.05, G = 6 }) {
  const { matrix, total, best, peak } = scoreMatrix(lambdaA, lambdaB, G)
  return (
    <div
      className="inline-grid gap-[4px]"
      style={{ gridTemplateColumns: `repeat(${G + 1}, minmax(0, 1fr))` }}
    >
      {matrix.flatMap((row, a) =>
        row.map((p, b) => {
          const isPeak = a === peak[0] && b === peak[1]
          const pct = Math.round((p / total) * 100)
          return (
            <motion.div
              key={`${a}-${b}`}
              initial={{ opacity: 0, scale: 0.4 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.25 + (a + b) * 0.03, type: 'spring', stiffness: 200, damping: 18 }}
              className={`grid place-items-center font-mono text-[11px] md:text-[15px] font-semibold w-[30px] h-[30px] md:w-[54px] md:h-[54px] ${
                isPeak ? 'ring-2 ring-pitch ring-offset-1 ring-offset-base' : ''
              }`}
              style={{ background: heatColor(p / best), color: '#10202B' }}
            >
              {pct >= 4 ? pct : ''}
            </motion.div>
          )
        }),
      )}
    </div>
  )
}

// ============ 1X2 odds bars ============
export function Odds({ rows }) {
  return (
    <div className="grid gap-3">
      {rows.map((r, i) => (
        <div key={i} className="grid grid-cols-[86px_1fr_60px] items-center gap-3">
          <span className="font-mono text-[15px] md:text-[18px] text-ink/80">{r.name}</span>
          <div className="h-5 bg-ink/10 overflow-hidden">
            <motion.div
              className="h-full"
              style={{ background: r.color }}
              initial={{ width: 0 }}
              animate={{ width: `${r.value * 100}%` }}
              transition={{ delay: 0.3 + i * 0.1, type: 'spring', stiffness: 90, damping: 18 }}
            />
          </div>
          <span
            className="font-mono font-bold text-right tabnum text-lg md:text-xl"
            style={{ color: r.color }}
          >
            {Math.round(r.value * 100)}%
          </span>
        </div>
      ))}
    </div>
  )
}

// ============ Backtest bars (real numbers) ============
export function BacktestBars({ data, maxV = 0.72 }) {
  return (
    <div className="grid gap-3">
      {data.map((r, i) => (
        <div key={i} className="grid grid-cols-[116px_1fr_70px] items-center gap-3">
          <span className="font-mono text-[14px] md:text-[16px] text-ink/80">{r.name}</span>
          <div className="h-5 bg-ink/10 overflow-hidden">
            <motion.div
              className="h-full"
              style={{ background: r.color }}
              initial={{ width: 0 }}
              animate={{ width: `${(r.value / maxV) * 100}%` }}
              transition={{ delay: 0.35 + i * 0.12, type: 'spring', stiffness: 80, damping: 18 }}
            />
          </div>
          <span
            className="font-mono font-bold text-right tabnum text-[15px] md:text-[18px]"
            style={{ color: r.color }}
          >
            <AnimatedNumber value={r.value} decimals={3} />
          </span>
        </div>
      ))}
    </div>
  )
}

// ============ Timeline ============
export function Timeline({ nodes }) {
  return (
    <div className="relative mt-6 md:mt-10">
      <div className="absolute left-0 right-0 top-[7px] h-0.5 bg-ink/10 overflow-hidden hidden md:block">
        <motion.div
          className="h-full origin-left"
          style={{ background: 'linear-gradient(90deg, #e8b23a, #d8452a)' }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: 0.3, duration: 1, ease: [0.2, 0.7, 0.2, 1] }}
        />
      </div>
      <div className="grid grid-cols-3 md:grid-cols-6 gap-x-4 gap-y-6 relative">
        {nodes.map((n, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.11, type: 'spring', stiffness: 130, damping: 18 }}
          >
            <span
              className="block w-4 h-4 bg-base mb-4"
              style={{ border: `3px solid ${i < 3 ? '#e8b23a' : '#d8452a'}` }}
            />
            <div className="font-mono font-bold text-2xl md:text-4xl text-ink tracking-tight">{n.year}</div>
            <div className="text-[14px] md:text-[17px] text-dim leading-snug mt-1.5 max-w-[16ch]">{n.label}</div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

// ============ Formula (color-coded) ============
const tk = {
  l: 'bg-pitch/12 text-pitch',
  a: 'bg-goal/12 text-goal',
  b: 'bg-py/12 text-py',
  mu: 'bg-gold/15 text-gold',
}
function Tk({ tone, children }) {
  return <span className={`px-1.5 py-0.5 font-semibold ${tk[tone]}`}>{children}</span>
}
export function Formula() {
  return (
    <div className="glass p-6 md:p-9 overflow-x-auto">
      <div className="font-mono text-[18px] md:text-[32px] whitespace-nowrap leading-loose">
        log(<Tk tone="a">λ</Tk>) = <Tk tone="mu">μ</Tk> + <Tk tone="l">α</Tk> − <Tk tone="l">β</Tk> +{' '}
        <Tk tone="a">host</Tk> + <Tk tone="b">elo</Tk> + <Tk tone="b">xg</Tk> + <Tk tone="b">valor</Tk>
      </div>
    </div>
  )
}

// (CodeBlock / FitCurves / Spectrum added for the expanded Python + ML sections)
// ============ Code block (syntax-tinted, no deps) ============
const CODE_RULES = [
  [/^#.*/, 'text-dim italic'],
  [/^("[^"]*"|'[^']*')/, 'text-pitch'],
  [/^\b(def|return|if|elif|else|for|in|is|not|and|or|None|True|False|import|from|as|self|lambda)\b/, 'text-py font-semibold'],
  [/^\b(np|exp|log)\b/, 'text-goal'],
  [/^\d+\.?\d*/, 'text-gold'],
]
function tokenizeLine(line) {
  const out = []
  let i = 0,
    plain = '',
    guard = 0
  const flush = () => {
    if (plain) {
      out.push({ t: plain, cls: '' })
      plain = ''
    }
  }
  while (i < line.length && guard++ < 2000) {
    const rest = line.slice(i)
    let hit = null
    for (const [re, cls] of CODE_RULES) {
      const m = rest.match(re)
      if (m && m.index === 0) {
        hit = [m[0], cls]
        break
      }
    }
    if (hit) {
      flush()
      out.push({ t: hit[0], cls: hit[1] })
      i += hit[0].length
    } else {
      plain += line[i]
      i += 1
    }
  }
  flush()
  return out
}
export function CodeBlock({ code, emphasize = [], annotations = [] }) {
  const lines = code.replace(/\n$/, '').split('\n')
  return (
    <div className="glass p-5 md:p-7 overflow-x-auto">
      <div className="font-mono text-[13px] md:text-[19px] leading-relaxed">
        {lines.map((ln, i) => {
          const hot = emphasize.includes(i)
          return (
            <div
              key={i}
              className={`whitespace-pre px-3 -mx-1 ${
                hot ? 'bg-pitch/10 border-l-2 border-pitch' : 'border-l-2 border-transparent'
              }`}
            >
              {ln === ''
                ? ' '
                : tokenizeLine(ln).map((tok, j) => (
                    <span key={j} className={tok.cls}>
                      {tok.t}
                    </span>
                  ))}
            </div>
          )
        })}
      </div>
      {annotations.length > 0 && (
        <div className="mt-5 grid gap-2 border-t border-white/[0.06] pt-4">
          {annotations.map((a, i) => (
            <p key={i} className="font-mono text-[13px] md:text-[16px] text-dim leading-snug">
              <span className="text-pitch">▸</span> {a}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

// ============ Fit curves (underfit / good / overfit) ============
export function FitCurves() {
  const pts = [
    [10, 50], [22, 40], [34, 45], [46, 30],
    [58, 39], [70, 27], [82, 35], [92, 24],
  ]
  const panels = [
    { title: 'Subajuste', sub: 'demasiado simple', tone: '#A99A80', d: 'M6,50 L94,32' },
    { title: 'Buen ajuste', sub: 'aprende el patrón', tone: '#E8B23A', d: 'M6,54 Q50,14 94,28' },
    {
      title: 'Sobreajuste',
      sub: 'memoriza el ruido',
      tone: '#D8452A',
      d: 'M10,50 L22,40 L34,45 L46,30 L58,39 L70,27 L82,35 L92,24',
    },
  ]
  return (
    <div className="grid grid-cols-3 gap-3 md:gap-5">
      {panels.map((p, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 + i * 0.13, type: 'spring', stiffness: 120, damping: 18 }}
          className="glass p-3 md:p-5"
        >
          <svg viewBox="0 0 100 64" className="w-full">
            {pts.map(([x, y], k) => (
              <circle key={k} cx={x} cy={y} r="2.4" fill="#A99A80" opacity="0.5" />
            ))}
            <path
              d={p.d}
              fill="none"
              stroke={p.tone}
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div
            className="mt-2 font-display font-bold text-lg md:text-2xl tracking-tight"
            style={{ color: p.tone }}
          >
            {p.title}
          </div>
          <div className="font-mono text-[12px] md:text-[14px] text-dim">{p.sub}</div>
        </motion.div>
      ))}
    </div>
  )
}

// ============ Spectrum (interpretable ↔ black box) ============
export function Spectrum({ items, left, right }) {
  return (
    <div>
      <div className="flex justify-between font-mono text-[11px] md:text-[15px] uppercase tracking-[0.1em] mb-4">
        <span className="text-py">{left}</span>
        <span className="text-goal text-right">{right}</span>
      </div>
      <div className="relative pt-1">
        <div
          className="absolute left-2 right-2 top-[9px] h-1"
          style={{ background: 'linear-gradient(90deg,#4FB0A3,#E8B23A,#D8452A)' }}
        />
        <div className="grid grid-cols-5 relative">
          {items.map((it, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.1, type: 'spring', stiffness: 140, damping: 18 }}
              className="flex flex-col items-center text-center px-1"
            >
              <span
                className={`w-4 h-4 rounded-full border-2 ${
                  it.mine ? 'bg-pitch border-pitch' : 'bg-base border-ink/40'
                }`}
              />
              <span
                className={`mt-3 font-mono text-[11px] md:text-[15px] leading-tight ${
                  it.mine ? 'text-pitch font-bold' : 'text-ink/80'
                }`}
              >
                {it.label}
              </span>
              {it.mine && (
                <span className="mt-1 font-mono text-[10px] md:text-[12px] text-pitch uppercase tracking-wide">
                  mi modelo
                </span>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ============ ML equation blocks ============
export function EqBlock({ label, parts, tone = 'l', note }) {
  const outTone = tone === 'a' ? 'bg-goal/15 text-goal' : 'bg-pitch/15 text-pitch'
  return (
    <div className="p-5 md:p-7 border border-dashed border-ink/15 bg-ink/[0.03] h-full">
      <div
        className="font-mono text-[13px] md:text-[15px] tracking-[0.14em] uppercase mb-3"
        style={{ color: tone === 'a' ? '#d8452a' : '#a99a80' }}
      >
        {label}
      </div>
      <div className="flex flex-wrap items-center gap-2.5 font-display font-semibold uppercase text-2xl md:text-4xl tracking-tight">
        {parts.map((p, i) =>
          p.op ? (
            <span key={i} className="font-mono font-normal text-dim normal-case">
              {p.op}
            </span>
          ) : (
            <span key={i} className={`px-3 py-1 ${p.out ? outTone : 'bg-ink/[0.06]'}`}>
              {p.t}
            </span>
          ),
        )}
      </div>
      {note && <p className="mt-4 text-ink/75 text-[16px] md:text-[19px] leading-snug">{note}</p>}
    </div>
  )
}

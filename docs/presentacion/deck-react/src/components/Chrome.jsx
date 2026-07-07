import { motion } from 'framer-motion'
import { toggleFullscreen } from '../hooks/useDeck.js'

const pad = (n) => String(n).padStart(2, '0')

export function Chrome({ index, total, section, onGo, onPrev, onNext }) {
  return (
    <>
      {/* progress */}
      <motion.div
        className="fixed top-0 left-0 h-[3px] z-40 bg-pitch"
        style={{ boxShadow: '0 0 12px #e8b23a' }}
        initial={false}
        animate={{ width: `${(index / (total - 1)) * 100}%` }}
        transition={{ type: 'spring', stiffness: 120, damping: 22 }}
      />

      {/* top bar */}
      <div className="fixed top-0 inset-x-0 h-[52px] md:h-[60px] flex items-center justify-between px-6 md:px-11 z-30 pointer-events-none">
        <div className="flex items-center gap-2.5 font-mono text-[11px] md:text-[13px] tracking-[0.18em] uppercase text-dim">
          <span className="w-2.5 h-2.5 bg-goal" />
          <b className="text-ink font-normal tracking-[0.2em]">WC·2026</b>
          <span className="text-pitch">/ {section}</span>
        </div>
        <div className="font-mono text-[11px] md:text-[13px] tracking-[0.18em] uppercase text-dim tabnum">
          SESSION {pad(index + 1)}—{pad(total)}
        </div>
      </div>

      {/* fullscreen */}
      <div className="fixed top-3 md:top-3.5 right-6 md:right-11 z-40 pointer-events-auto">
        <button
          onClick={toggleFullscreen}
          aria-label="Pantalla completa (F)"
          title="Pantalla completa (F)"
          className="grid place-items-center w-9 h-8 glass text-ink hover:text-pitch hover:border-pitch/60 transition-colors"
        >
          ⛶
        </button>
      </div>

      {/* bottom bar */}
      <div className="fixed bottom-0 inset-x-0 h-[54px] md:h-16 flex items-center justify-between px-6 md:px-11 z-30">
        <div className="flex gap-2">
          {Array.from({ length: total }).map((_, i) => (
            <button
              key={i}
              onClick={() => onGo(i)}
              aria-label={`Ir a la diapositiva ${i + 1}`}
              className="transition-all"
              style={{
                width: i === index ? 20 : 8,
                height: 8,
                background: i === index ? '#e8b23a' : 'rgba(239,231,212,0.16)',
              }}
            />
          ))}
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden md:inline font-mono text-[11px] text-dim tracking-[0.08em] uppercase">
            ← → · space · F fullscreen
          </span>
          <div className="flex gap-2">
            <button
              onClick={onPrev}
              disabled={index === 0}
              aria-label="Anterior"
              className="grid place-items-center w-10 h-9 glass text-ink hover:text-pitch hover:border-pitch/60 transition-colors disabled:opacity-30 disabled:hover:text-ink"
            >
              ←
            </button>
            <button
              onClick={onNext}
              disabled={index === total - 1}
              aria-label="Siguiente"
              className="grid place-items-center w-10 h-9 glass text-ink hover:text-pitch hover:border-pitch/60 transition-colors disabled:opacity-30 disabled:hover:text-ink"
            >
              →
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

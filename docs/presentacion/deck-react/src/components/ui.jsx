import { motion, useInView, animate } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'

// ---- reveal / stagger variants ----
export const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.09, delayChildren: 0.12 },
  },
}
export const item = {
  hidden: { opacity: 0, y: 22, filter: 'blur(4px)' },
  show: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { type: 'spring', stiffness: 120, damping: 20 },
  },
}

export function Stagger({ children, className = '' }) {
  return (
    <motion.div variants={container} initial="hidden" animate="show" className={className}>
      {children}
    </motion.div>
  )
}
export function Item({ children, className = '', as = 'div' }) {
  const M = motion[as] || motion.div
  return (
    <M variants={item} className={className}>
      {children}
    </M>
  )
}

// ---- kicker / eyebrow (terminal / title-card style) ----
export function Kicker({ num, children }) {
  return (
    <Item>
      <div className="flex items-center gap-3 mb-6 md:mb-8">
        <span className="w-3 h-3 bg-goal" />
        <span className="font-mono text-sm md:text-lg tracking-[0.24em] uppercase text-dim tabnum">
          {num}
        </span>
        <span className="h-px w-10 md:w-16 hairline" />
        <span className="font-mono text-sm md:text-lg tracking-[0.24em] uppercase text-pitch">
          {children}
        </span>
      </div>
    </Item>
  )
}

// ---- tag (flat, squared — NOT a bubble) ----
const chipTone = {
  default: 'text-dim border-ink/20',
  pitch: 'text-pitch border-pitch/45',
  goal: 'text-goal border-goal/45',
  py: 'text-py border-py/45',
}
export function Chip({ children, tone = 'default' }) {
  return (
    <span
      className={`inline-flex items-center gap-2 font-mono text-[13px] md:text-[16px] uppercase tracking-[0.08em] px-3.5 py-2 border ${chipTone[tone]}`}
    >
      <span className="w-1.5 h-1.5 bg-current opacity-70" />
      {children}
    </span>
  )
}

// ---- bullet list item ----
export function Bullet({ children }) {
  return (
    <Item>
      <li className="grid grid-cols-[auto_1fr] gap-4 items-start text-xl md:text-[27px] leading-snug text-ink/85">
        <span className="mt-[0.5em] w-3.5 h-3.5 bg-pitch shrink-0" />
        <span>{children}</span>
      </li>
    </Item>
  )
}

// ---- flat panel with hover lift ----
export function Panel({ children, className = '', hover = false }) {
  return (
    <motion.div
      whileHover={
        hover ? { y: -5, transition: { type: 'spring', stiffness: 300, damping: 20 } } : undefined
      }
      className={`glass ${className}`}
    >
      {children}
    </motion.div>
  )
}

// ---- animated number counter ----
export function AnimatedNumber({ value, decimals = 0, prefix = '', suffix = '', className = '' }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    if (!inView) return
    const controls = animate(0, value, {
      duration: 1.1,
      ease: [0.2, 0.7, 0.2, 1],
      onUpdate: (v) => setDisplay(v),
    })
    return () => controls.stop()
  }, [inView, value])

  return (
    <span ref={ref} className={`tabnum ${className}`}>
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  )
}

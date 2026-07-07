import { useCallback, useEffect, useRef, useState } from 'react'

export function useDeck(total) {
  const [index, setIndex] = useState(0)
  const [dir, setDir] = useState(0)
  const idxRef = useRef(0)

  const go = useCallback(
    (n) => {
      const cur = idxRef.current
      const target = typeof n === 'function' ? n(cur) : n
      const nextIdx = Math.max(0, Math.min(total - 1, target))
      if (nextIdx === cur) return
      setDir(nextIdx > cur ? 1 : -1)
      idxRef.current = nextIdx
      setIndex(nextIdx)
    },
    [total],
  )
  const next = useCallback(() => go((c) => c + 1), [go])
  const prev = useCallback(() => go((c) => c - 1), [go])

  useEffect(() => {
    const onKey = (e) => {
      if (['ArrowRight', 'PageDown', ' '].includes(e.key)) {
        e.preventDefault()
        next()
      } else if (['ArrowLeft', 'PageUp'].includes(e.key)) {
        e.preventDefault()
        prev()
      } else if (e.key === 'Home') {
        e.preventDefault()
        go(0)
      } else if (e.key === 'End') {
        e.preventDefault()
        go(total - 1)
      } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault()
        toggleFullscreen()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [total, go, next, prev])

  return { index, dir, go, next, prev }
}

export function toggleFullscreen() {
  const el = document.documentElement
  const isFs = document.fullscreenElement || document.webkitFullscreenElement
  if (isFs) {
    ;(document.exitFullscreen || document.webkitExitFullscreen)?.call(document)
    return
  }
  const req = el.requestFullscreen || el.webkitRequestFullscreen
  try {
    const p = req?.call(el)
    if (p && p.catch) p.catch(() => {})
  } catch (_) {
    /* blocked by environment */
  }
}

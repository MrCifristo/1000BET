import { AnimatePresence, motion } from 'framer-motion'
import { SLIDES } from './slides.jsx'
import { Chrome } from './components/Chrome.jsx'
import { useDeck } from './hooks/useDeck.js'

const slideVariants = {
  enter: (dir) => ({ opacity: 0, x: dir > 0 ? 70 : -70, filter: 'blur(8px)' }),
  center: { opacity: 1, x: 0, filter: 'blur(0px)' },
  exit: (dir) => ({ opacity: 0, x: dir > 0 ? -70 : 70, filter: 'blur(8px)' }),
}

export default function App() {
  const total = SLIDES.length
  const { index, dir, go, next, prev } = useDeck(total)
  const { Comp, section } = SLIDES[index]

  return (
    <div className="relative h-full w-full overflow-hidden">
      <div className="stage-bg" aria-hidden="true" />
      <div className="vignette" aria-hidden="true" />
      <div className="scanlines" aria-hidden="true" />

      <Chrome
        index={index}
        total={total}
        section={section}
        onGo={go}
        onPrev={prev}
        onNext={next}
      />

      <div className="relative z-10 h-full">
        <AnimatePresence mode="wait" custom={dir} initial={false}>
          <motion.section
            key={index}
            custom={dir}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: 'spring', stiffness: 90, damping: 20, mass: 0.9 }}
            className="absolute inset-0 flex flex-col justify-center px-6 sm:px-10 md:px-16 pt-14 pb-16 md:pt-20 md:pb-20 overflow-y-auto"
          >
            <Comp />
          </motion.section>
        </AnimatePresence>
      </div>
    </div>
  )
}

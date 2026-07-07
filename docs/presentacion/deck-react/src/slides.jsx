import { Kicker, Item, Chip, Panel, Stagger } from './components/ui.jsx'
import {
  PoissonBars,
  Heatmap,
  Odds,
  Timeline,
  Formula,
  EqBlock,
  CodeBlock,
  FitCurves,
  Spectrum,
} from './components/viz.jsx'

// shared bits ---------------------------------------------------------------
function H1({ children }) {
  return (
    <Item>
      <h1 className="font-display font-bold uppercase tracking-tight leading-[1.0] text-[54px] sm:text-7xl md:text-[7.5rem] text-white text-balance">
        {children}
      </h1>
    </Item>
  )
}
function H2({ children }) {
  return (
    <Item>
      <h2 className="font-display font-semibold uppercase tracking-tight leading-[1.04] text-[42px] sm:text-6xl md:text-7xl mb-5 md:mb-7 text-white text-balance">
        {children}
      </h2>
    </Item>
  )
}
function Lede({ children }) {
  return (
    <Item>
      <p className="text-2xl md:text-[33px] leading-relaxed text-ink/85 max-w-[42ch]">{children}</p>
    </Item>
  )
}
function Card({ tag, title, children }) {
  return (
    <Item>
      <Panel hover className="p-6 md:p-8 h-full">
        <div className="font-mono text-[13px] md:text-[15px] tracking-[0.12em] uppercase text-goal">
          {tag}
        </div>
        <h3 className="font-display font-bold text-2xl md:text-3xl mt-2 mb-2 tracking-tight">
          {title}
        </h3>
        <p className="text-ink/75 text-[17px] md:text-[21px] leading-snug">{children}</p>
      </Panel>
    </Item>
  )
}

// 1 · TITLE -----------------------------------------------------------------
export function TitleSlide() {
  return (
    <Stagger className="max-w-5xl mx-auto w-full">
      <Item>
        <div className="flex items-center gap-3 font-mono text-[13px] md:text-base tracking-[0.22em] uppercase mb-7 md:mb-10">
          <span className="w-8 h-px bg-goal" />
          <span className="text-pitch">Evolution of Computing</span>
          <span className="text-dim">— Session 01</span>
        </div>
      </Item>
      <H1>
        Python y la predicción
        <br />
        del <span className="text-grad">Mundial 2026</span>
      </H1>
      <Item>
        <p className="mt-6 md:mt-8 text-2xl md:text-4xl text-ink/80 max-w-[38ch] leading-relaxed">
          ¿Se puede predecir un partido de fútbol? No con certeza — pero sí con{' '}
          <b className="text-white">probabilidades</b>. Y la herramienta es Python.
        </p>
      </Item>
      <Item>
        <div className="mt-8 md:mt-12 flex items-center gap-4 flex-wrap">
          <span className="font-bold text-white text-xl md:text-2xl">Milton Beltrán</span>
          <span className="font-mono text-[14px] md:text-[16px] text-dim tracking-[0.08em]">
            MODELO POISSON · DIXON-COLES · ELO
          </span>
        </div>
      </Item>
    </Stagger>
  )
}

// 2 · AGENDA ----------------------------------------------------------------
const AGENDA = [
  ['01', 'Python', 'Qué es, cómo se lee su código y por qué reina en datos e IA.'],
  ['02', 'Machine Learning', 'Cómo una máquina aprende reglas a partir de los datos, no programándolas.'],
  ['03', 'El proyecto, en vivo', 'Un sistema que predice el Mundial 2026 — visto en una demostración real.'],
]
export function AgendaSlide() {
  return (
    <Stagger className="w-full max-w-5xl mx-auto">
      <Kicker num="—">El plan de hoy</Kicker>
      <H2>De qué vamos a hablar</H2>
      <div className="grid sm:grid-cols-2 gap-4 md:gap-5 mt-2">
        {AGENDA.map(([n, t, d]) => (
          <Item key={n}>
            <Panel hover className="p-6 md:p-8 flex gap-5 items-start">
              <span className="font-display font-bold text-4xl md:text-6xl text-grad leading-none tabnum">
                {n}
              </span>
              <div>
                <h3 className="font-display font-bold text-2xl md:text-3xl tracking-tight mb-1.5">
                  {t}
                </h3>
                <p className="text-ink/75 text-[17px] md:text-[21px] leading-snug">{d}</p>
              </div>
            </Panel>
          </Item>
        ))}
      </div>
    </Stagger>
  )
}

// 3 · PYTHON — WHAT ---------------------------------------------------------
const SPEC = [
  ['Nivel', 'Alto', 'escribes pensando en el problema, no en el hardware'],
  ['Ejecución', 'Interpretado', 'se ejecuta al instante, sin compilación previa'],
  ['Tipado', 'Dinámico y fuerte', 'no declaras el tipo, pero tampoco lo convierte por su cuenta'],
  ['Memoria', 'Automática', 'gestiona sola la memoria que deja de usarse'],
]
export function PythonSpec() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="01">El lenguaje</Kicker>
      <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
        <div>
          <H2>¿Qué es Python?</H2>
          <Lede>
            Uno de los lenguajes más usados del mundo. Su rasgo distintivo es la{' '}
            <b className="text-ink">legibilidad</b>: el código se lee casi como inglés, y eso acorta
            la distancia entre pensar una idea y ejecutarla.
          </Lede>
          <Item>
            <div className="flex flex-wrap gap-2.5 mt-6">
              <Chip tone="pitch">legible</Chip>
              <Chip tone="pitch">multiparadigma</Chip>
              <Chip tone="py">#1 en ciencia de datos</Chip>
            </div>
          </Item>
        </div>
        <Item>
          <Panel className="overflow-hidden">
            {SPEC.map(([k, v, s], i) => (
              <div
                key={k}
                className={`grid grid-cols-[34%_1fr] items-center px-5 md:px-7 py-4 md:py-5 ${
                  i > 0 ? 'border-t border-white/[0.06]' : ''
                }`}
              >
                <span className="font-mono text-[12px] md:text-[14px] tracking-[0.1em] uppercase text-dim">
                  {k}
                </span>
                <span className="text-[17px] md:text-[21px] font-semibold text-ink">
                  {v}
                  <small className="block font-normal text-dim text-[13px] md:text-[15px] mt-0.5">
                    {s}
                  </small>
                </span>
              </div>
            ))}
          </Panel>
        </Item>
      </div>
    </Stagger>
  )
}

// 3b · REAL CODE ON SCREEN --------------------------------------------------
const LAMBDA_CODE = `def _lambda(self, iso_att, iso_def, host_iso):
    p = self.params_                      # parámetros ya aprendidos
    host = 1.0 if iso_att == host_iso else 0.0

    log_lam = (p["mu"] + p["alpha"][iso_att] - p["beta"][iso_def]
               + p["gamma"] * host + p["delta"] * elo_diff
               + p["eps"] * xg_diff)
    return np.exp(log_lam)                # goles esperados del equipo`
export function CodeSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="01 ·">El lenguaje</Kicker>
      <H2>El código se lee casi solo</H2>
      <Lede>
        Un fragmento <b className="text-ink">real</b> de mi proyecto: calcula los goles esperados de
        un equipo. Aunque no programes, casi se entiende qué hace.
      </Lede>
      <Item>
        <div className="mt-6">
          <CodeBlock
            code={LAMBDA_CODE}
            emphasize={[2, 4]}
            annotations={[
              'host = 1.0 si el equipo juega en casa, si no 0.0 — se lee casi como en inglés.',
              'log_lam suma ataque, defensa, localía y ranking: es exactamente la fórmula del modelo que veremos.',
            ]}
          />
        </div>
      </Item>
      <Item>
        <p className="font-mono text-[14px] md:text-[16px] text-dim mt-5 leading-relaxed">
          Por dentro, Python traduce esto a un formato intermedio (<b className="text-ink">bytecode</b>
          ) que ejecuta su máquina virtual, CPython — por eso corre al instante, sin compilar.
        </p>
      </Item>
    </Stagger>
  )
}

// 4 · INTERPRETED vs COMPILED ----------------------------------------------
export function InterpretedSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="01 ·">Una idea clave</Kicker>
      <H2>Interpretado, no compilado</H2>
      <Lede>Es la forma en que la máquina traduce y ejecuta tu código — y explica por qué Python es tan ágil para experimentar.</Lede>
      <div className="grid md:grid-cols-2 gap-5 md:gap-7 mt-7">
        <Item>
          <Panel className="p-6 md:p-8 h-full">
            <div className="font-display font-bold text-6xl md:text-7xl leading-none text-py/35 mb-3">
              01
            </div>
            <div className="font-mono text-[13px] md:text-[15px] tracking-[0.12em] uppercase text-py mb-2">
              Compilado (C, Rust)
            </div>
            <h3 className="font-display font-bold text-2xl md:text-3xl tracking-tight mb-2">
              Traducir el libro entero
            </h3>
            <p className="text-ink/75 text-[17px] md:text-[21px] leading-snug">
              Todo el programa se traduce a código de máquina <b className="text-ink">antes</b> de
              ejecutarse. Muy veloz al correr, a cambio de un paso previo y menos flexibilidad.
            </p>
          </Panel>
        </Item>
        <Item>
          <Panel className="p-6 md:p-8 h-full">
            <div className="font-display font-bold text-6xl md:text-7xl leading-none text-pitch/50 mb-3">
              02
            </div>
            <div className="font-mono text-[13px] md:text-[15px] tracking-[0.12em] uppercase text-pitch mb-2">
              Interpretado (Python)
            </div>
            <h3 className="font-display font-bold text-2xl md:text-3xl tracking-tight mb-2">
              Un intérprete simultáneo
            </h3>
            <p className="text-ink/75 text-[17px] md:text-[21px] leading-snug">
              Traduce y ejecuta <b className="text-ink">instrucción por instrucción</b>, sobre la
              marcha. Escribes y ves el resultado de inmediato: ideal para iterar.
            </p>
          </Panel>
        </Item>
      </div>
      <Item>
        <p className="font-mono text-[15px] md:text-[17px] text-dim mt-6 leading-relaxed">
          Ese ciclo inmediato de escribir, ejecutar y ajustar es exactamente el que exige{' '}
          <b className="text-ink">construir un modelo estadístico</b>.
        </p>
      </Item>
    </Stagger>
  )
}

// 5 · HISTORY ---------------------------------------------------------------
const TL = [
  { year: '1989', label: 'Guido van Rossum lo empieza en Ámsterdam' },
  { year: '1991', label: 'Primera versión pública (0.9.0)' },
  { year: '2000', label: 'Python 2 — se populariza' },
  { year: '2008', label: 'Python 3 mejora rompiendo compatibilidad' },
  { year: '2018', label: 'Guido deja de ser "dictador benévolo"' },
  { year: '2020', label: 'Fin de Python 2 — hoy "Python" es Python 3' },
]
export function HistorySlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="02">Historia</Kicker>
      <H2>Un proyecto de Navidad que conquistó la IA</H2>
      <Lede>
        Nació como el proyecto personal de una sola persona. Su ventaja decisiva nunca fue la
        velocidad, sino la <b className="text-ink">legibilidad</b>.
      </Lede>
      <Item>
        <Timeline nodes={TL} />
      </Item>
      <Item>
        <p className="font-mono text-[15px] md:text-[17px] text-dim mt-8">
          Se llama Python por <b className="text-ink">Monty Python</b>, no por la serpiente.
        </p>
      </Item>
    </Stagger>
  )
}

// 6 · PYTHON IS EVERYWHERE --------------------------------------------------
export function UsesSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="03">Usos en el mundo real</Kicker>
      <H2>Python está en lo que usas a diario</H2>
      <Lede>Aunque no se note, es muy probable que ya hayas usado Python varias veces hoy.</Lede>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5 mt-7">
        <Card tag="streaming" title="Netflix">
          Decide qué series recomendarte según lo que ves.
        </Card>
        <Card tag="redes" title="Instagram">
          Buena parte de su servidor está escrito en Python.
        </Card>
        <Card tag="inteligencia artificial" title="ChatGPT">
          Se entrena y funciona mayormente con Python.
        </Card>
        <Card tag="ciencia" title="Agujero negro">
          La 1ª foto de uno (2019) se procesó con Python.
        </Card>
      </div>
      <Item>
        <div className="flex flex-wrap gap-2.5 mt-7">
          <Chip>web</Chip>
          <Chip>automatización</Chip>
          <Chip>finanzas</Chip>
          <Chip tone="goal">ciencia de datos</Chip>
          <Chip tone="py">inteligencia artificial</Chip>
        </div>
      </Item>
    </Stagger>
  )
}

// 7 · ECOSYSTEM -------------------------------------------------------------
export function EcosystemSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="03 ·">Datos y estadística</Kicker>
      <H2>Su fuerza es el ecosistema</H2>
      <Lede>
        El verdadero motor de Python son sus <b className="text-ink">librerías</b>: colecciones de
        herramientas listas para el cálculo. Mi proyecto se apoya en estas cuatro.
      </Lede>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5 mt-7">
        <Card tag="tablas" title="pandas">
          Organiza grandes volúmenes de datos en tablas, como una hoja de cálculo programable.
        </Card>
        <Card tag="números" title="NumPy">
          Ejecuta millones de operaciones numéricas de una sola vez, a gran velocidad.
        </Card>
        <Card tag="matemática" title="SciPy">
          Trae la distribución de Poisson y el motor que <b className="text-ink">entrena</b> el
          modelo.
        </Card>
        <Card tag="visual" title="matplotlib">
          Convierte los números en gráficas y mapas de calor.
        </Card>
      </div>
    </Stagger>
  )
}

// 8 · MACHINE LEARNING — WHAT ----------------------------------------------
export function MLSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="04">Machine Learning</Kicker>
      <H2>Aprender reglas, no programarlas</H2>
      <Lede>
        La idea central del machine learning, con una analogía: es como aprende un niño.
      </Lede>
      <div className="grid md:grid-cols-2 gap-5 md:gap-7 items-stretch mt-6">
        <Item>
          <EqBlock
            label="Programación clásica"
            tone="l"
            parts={[{ t: 'Reglas' }, { op: '+' }, { t: 'Datos' }, { op: '→' }, { t: 'Respuestas', out: true }]}
            note="Yo escribo todas las reglas a mano."
          />
        </Item>
        <Item>
          <EqBlock
            label="Machine Learning"
            tone="a"
            parts={[{ t: 'Datos' }, { op: '+' }, { t: 'Respuestas' }, { op: '→' }, { t: 'Reglas', out: true }]}
            note="La máquina descubre las reglas sola — como un niño que aprende qué es una manzana viendo muchas, no leyendo una definición."
          />
        </Item>
      </div>
    </Stagger>
  )
}

// 9 · ML IN DAILY LIFE ------------------------------------------------------
export function MLDailySlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="04 ·">Lo usas sin saberlo</Kicker>
      <H2>Machine learning en tu día a día</H2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5 mt-4">
        <Card tag="recomendar" title="Sugerencias">
          "Porque viste…" en Netflix, Spotify o YouTube.
        </Card>
        <Card tag="clasificar" title="Filtro de spam">
          Tu correo aprende a separar lo relevante del correo no deseado.
        </Card>
        <Card tag="reconocer" title="Desbloqueo facial">
          Tu teléfono aprende a reconocer tu rostro.
        </Card>
        <Card tag="predecir" title="Autocorrector">
          Predice la siguiente palabra que vas a escribir.
        </Card>
      </div>
      <Item>
        <p className="font-mono text-[15px] md:text-[17px] text-dim mt-7 mb-3">
          Y por qué Python domina este campo:
        </p>
      </Item>
      <Item>
        <div className="flex flex-wrap gap-2.5">
          <Chip tone="pitch">el ecosistema numérico ya existía</Chip>
          <Chip tone="py">scikit-learn · TensorFlow · PyTorch</Chip>
          <Chip tone="goal">fácil de investigar</Chip>
        </div>
      </Item>
    </Stagger>
  )
}

// 11 · LEARNING TYPES -------------------------------------------------------
export function LearningTypesSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="04 ·">Machine Learning</Kicker>
      <H2>Tres formas de aprender</H2>
      <Lede>No todo el aprendizaje automático es igual. Se agrupa en tres grandes familias.</Lede>
      <div className="grid md:grid-cols-3 gap-4 md:gap-5 mt-7 items-stretch">
        <Item>
          <Panel className="p-6 md:p-8 h-full border-t-2 border-pitch">
            <div className="font-mono text-[13px] md:text-[15px] tracking-[0.12em] uppercase text-pitch">
              supervisado
            </div>
            <h3 className="font-display font-bold text-2xl md:text-3xl mt-2 mb-2 tracking-tight">
              Aprende de ejemplos con respuesta
            </h3>
            <p className="text-ink/75 text-[16px] md:text-[20px] leading-snug">
              Se le dan datos <b className="text-ink">y</b> la respuesta correcta de cada uno. Filtrar
              spam, predecir precios.
            </p>
            <p className="font-mono text-[13px] md:text-[15px] text-pitch mt-4 leading-snug">
              ▸ aquí cae mi modelo: partidos pasados con su marcador real.
            </p>
          </Panel>
        </Item>
        <Card tag="no supervisado" title="Encuentra patrones solo">
          Solo recibe datos, sin respuestas, y descubre estructura oculta. Agrupar clientes
          parecidos, detectar anomalías.
        </Card>
        <Card tag="por refuerzo" title="Aprende probando">
          Actúa, recibe premio o castigo, y ajusta su estrategia. Así aprenden AlphaGo o un robot a
          caminar.
        </Card>
      </div>
    </Stagger>
  )
}

// 12 · OVERFITTING ----------------------------------------------------------
export function OverfittingSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="04 ·">El reto central</Kicker>
      <H2>Memorizar no es aprender</H2>
      <Lede>
        Un modelo que memoriza el pasado al pie de la letra falla con lo nuevo. La meta real es{' '}
        <b className="text-ink">generalizar</b>.
      </Lede>
      <Item>
        <div className="mt-7">
          <FitCurves />
        </div>
      </Item>
      <Item>
        <p className="font-mono text-[15px] md:text-[17px] text-dim mt-7 leading-relaxed">
          Por eso <b className="text-ink">separo los datos</b>: entreno con unos partidos y evalúo con
          otros que el modelo nunca vio. Y le pongo un freno —la regularización— para que no se
          aferre a las casualidades.
        </p>
      </Item>
    </Stagger>
  )
}

// 13 · CLASSIC vs NEURAL vs LLM ---------------------------------------------
const SPECTRUM = [
  { label: 'Poisson · regresión', mine: true },
  { label: 'Árboles · bosques' },
  { label: 'Redes neuronales' },
  { label: 'Deep learning' },
  { label: 'LLMs · ChatGPT' },
]
export function SpectrumSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="04 ·">El mapa del ML</Kicker>
      <H2>Del modelo simple al LLM</H2>
      <Lede>
        No todo el machine learning es una red neuronal. Hay un espectro, y cada extremo sirve para
        cosas distintas.
      </Lede>
      <Item>
        <div className="mt-9 mb-7">
          <Spectrum
            items={SPECTRUM}
            left="Interpretable · pocos datos"
            right="Caja negra · millones de datos"
          />
        </div>
      </Item>
      <Item>
        <p className="text-xl md:text-[26px] text-ink/85 leading-relaxed max-w-[62ch]">
          <b className="text-white">¿Por qué Poisson y no una red?</b> Con miles de partidos —no
          millones— un modelo interpretable rinde igual o mejor, y puedo{' '}
          <b className="text-white">explicar cada número</b>. Una red sería una caja negra con más
          riesgo de sobreajuste.
        </p>
      </Item>
    </Stagger>
  )
}

// 14 · PROJECT (repo mapping) -----------------------------------------------
const REPO_MAP = [
  ['pandas · numpy', 'datos y características', 'src/ingestion/ · src/features/'],
  ['scipy', 'Poisson + optimizador', 'src/model/poisson_model.py · train.py'],
  ['aprendizaje supervisado', 'miles de partidos reales', 'src/model/train.py'],
  ['generalización', 'prueba sin look-ahead', 'src/evaluation/backtest_temporal.py'],
  ['ML interpretable', 'Poisson · Dixon-Coles · Elo', 'src/model/'],
  ['Streamlit', 'la app de la demo', 'src/ui/app.py'],
]
export function ProjectSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="05">El proyecto</Kicker>
      <H2>Todo esto, en un solo repo</H2>
      <Lede>
        Un sistema que predice partidos del Mundial 2026 y simula el torneo. Aquí es donde el Python
        y el machine learning que vimos <b className="text-ink">cobran vida</b>.
      </Lede>
      <Item>
        <Panel className="mt-7 overflow-hidden">
          {REPO_MAP.map(([concept, what, path], i) => (
            <div
              key={concept}
              className={`grid grid-cols-[1fr] md:grid-cols-[minmax(0,42%)_1fr] items-baseline gap-1 md:gap-6 px-5 md:px-7 py-3.5 md:py-4 ${
                i > 0 ? 'border-t border-white/[0.06]' : ''
              }`}
            >
              <div>
                <span className="font-semibold text-ink text-[17px] md:text-[22px]">{concept}</span>
                <span className="text-dim text-[14px] md:text-[17px]"> — {what}</span>
              </div>
              <span className="font-mono text-py text-[13px] md:text-[17px] break-all md:text-right">
                {path}
              </span>
            </div>
          ))}
        </Panel>
      </Item>
      <Item>
        <p className="font-mono text-[15px] md:text-[18px] text-pitch mt-6">
          ▶ Y ahora lo vemos funcionando.
        </p>
      </Item>
    </Stagger>
  )
}

// 15 · MODEL ----------------------------------------------------------------
export function ModelSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="06">Cómo funciona el modelo</Kicker>
      <H2>
        Todo se reduce a estimar <span className="text-goal">λ</span>
      </H2>
      <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-start">
        <div>
          <Lede>
            Los goles son <b className="text-ink">eventos raros</b>: eso lo describe la distribución
            de Poisson. <b className="text-ink">λ</b> = los goles que esperamos de un equipo.
          </Lede>
          <Item>
            <div className="mt-6">
              <PoissonBars lambda={1.8} />
              <p className="font-mono text-[15px] md:text-[17px] text-dim mt-4">
                P(goles) para λ = 1.8 · distribución de Poisson
              </p>
            </div>
          </Item>
        </div>
        <div>
          <Item>
            <Formula />
          </Item>
          <Item>
            <div className="grid gap-2.5 mt-5">
              <Legend sw="α − β" tone="l">
                ataque del equipo menos defensa del rival
              </Legend>
              <Legend sw="host" tone="a">
                ventaja de jugar como anfitrión
              </Legend>
              <Legend sw="elo·xg·valor" tone="b">
                ranking, calidad de ocasiones y valor de plantilla
              </Legend>
            </div>
          </Item>
          <Item>
            <p className="font-mono text-[15px] md:text-[17px] text-dim mt-5 leading-relaxed">
              <b className="text-ink">Interpretable:</b> ordenar equipos por α da un ranking real de
              delanteras.
            </p>
          </Item>
        </div>
      </div>
    </Stagger>
  )
}
function Legend({ sw, tone, children }) {
  const c = { l: 'bg-pitch/12 text-pitch', a: 'bg-goal/12 text-goal', b: 'bg-py/12 text-py' }[tone]
  return (
    <div className="flex items-baseline gap-3 text-[17px] md:text-[21px] text-ink/85">
      <span className={`font-mono font-bold px-2.5 py-0.5 shrink-0 ${c}`}>{sw}</span>
      {children}
    </div>
  )
}

// 16 · DEMO -----------------------------------------------------------------
export function DemoSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="07">Demostración en vivo</Kicker>
      <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
        <div>
          <H2>
            Elige dos equipos.
            <br />
            Lee la predicción.
          </H2>
          <Lede>
            La app convierte todo el modelo en una pantalla simple: probabilidades, goles esperados y
            un mapa de calor de marcadores.
          </Lede>
          <Item>
            <p className="font-display font-bold uppercase tracking-tight text-3xl md:text-5xl text-pitch mt-7">
              ▶ Cambiar a la app en vivo
            </p>
          </Item>
          <Item>
            <p className="font-mono text-[15px] md:text-[17px] text-dim mt-3">
              ARG vs BRA · ejemplo del formato de salida
            </p>
          </Item>
        </div>
        <Item>
          <Panel className="p-6 md:p-8 grid gap-6">
            <div>
              <div className="flex justify-between font-mono text-[12px] text-dim mb-3">
                <span>ARG · BRA</span>
                <span>P(marcador)</span>
              </div>
              <Odds
                rows={[
                  { name: 'ARG', value: 0.63, color: '#e8b23a' },
                  { name: 'Empate', value: 0.22, color: '#a99a80' },
                  { name: 'BRA', value: 0.15, color: '#d8452a' },
                ]}
              />
            </div>
            <div>
              <div className="font-mono text-[12px] text-dim mb-2">Probabilidad por marcador →</div>
              <Heatmap lambdaA={1.9} lambdaB={1.05} />
            </div>
          </Panel>
        </Item>
      </div>
    </Stagger>
  )
}

// 16 · CLOSING --------------------------------------------------------------
const RECAP = [
  { n: '01', h: 'Un lenguaje para todo', p: 'Python cubre el recorrido completo de los datos, sin cambiar de herramienta.', c: '#e8b23a' },
  { n: '02', h: 'Aprender de los datos', p: 'El machine learning descubre las reglas; no se las programa a mano.', c: '#d8452a' },
  { n: '03', h: 'Estadística interpretable', p: 'Cada número del modelo significa algo real — no es una caja negra.', c: '#4fb0a3' },
]
export function ClosingSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="08">Conclusiones</Kicker>
      <H2>
        De una idea matemática
        <br />a una app que funciona
      </H2>
      <div className="grid md:grid-cols-3 gap-6 md:gap-8 my-7 md:my-10">
        {RECAP.map((r) => (
          <Item key={r.n}>
            <div className="pt-4 border-t-2" style={{ borderColor: r.c }}>
              <div className="font-mono text-[15px] md:text-[17px] tracking-[0.1em]" style={{ color: r.c }}>
                {r.n}
              </div>
              <h4 className="font-display font-bold text-2xl md:text-3xl mt-2 mb-2 tracking-tight">
                {r.h}
              </h4>
              <p className="text-ink/75 text-[17px] md:text-[20px] leading-snug">{r.p}</p>
            </div>
          </Item>
        ))}
      </div>
      <Item>
        <div className="flex items-center gap-4 flex-wrap">
          <span className="font-display font-extrabold text-2xl md:text-4xl tracking-tightest">
            ¡Gracias! ¿Preguntas?
          </span>
          <span className="font-mono text-[13px] md:text-[15px] text-goal tracking-[0.08em]">
            MILTON BELTRÁN · EVOLUTION OF COMPUTING
          </span>
        </div>
      </Item>
    </Stagger>
  )
}

// registry ------------------------------------------------------------------
export const SLIDES = [
  { section: 'Apertura', Comp: TitleSlide },
  { section: 'El plan', Comp: AgendaSlide },
  { section: 'El lenguaje', Comp: PythonSpec },
  { section: 'El lenguaje', Comp: CodeSlide },
  { section: 'El lenguaje', Comp: InterpretedSlide },
  { section: 'Historia', Comp: HistorySlide },
  { section: 'Usos reales', Comp: UsesSlide },
  { section: 'Datos y estadística', Comp: EcosystemSlide },
  { section: 'Machine Learning', Comp: MLSlide },
  { section: 'Machine Learning', Comp: MLDailySlide },
  { section: 'Machine Learning', Comp: LearningTypesSlide },
  { section: 'Machine Learning', Comp: OverfittingSlide },
  { section: 'Machine Learning', Comp: SpectrumSlide },
  { section: 'El proyecto', Comp: ProjectSlide },
  { section: 'El modelo', Comp: ModelSlide },
  { section: 'Demostración', Comp: DemoSlide },
  { section: 'Cierre', Comp: ClosingSlide },
]

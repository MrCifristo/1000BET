import { Kicker, Item, Chip, Bullet, Panel, Stagger } from './components/ui.jsx'
import {
  PoissonBars,
  Heatmap,
  Odds,
  BacktestBars,
  Timeline,
  Formula,
  EqBlock,
  Pipeline,
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
  ['01', 'Qué es Python', 'Qué tipo de lenguaje es, de dónde viene y por qué importa.'],
  ['02', 'Por qué reina en datos e IA', 'Cómo Python se volvió el idioma de la ciencia y el machine learning.'],
  ['03', 'Mi proyecto', 'Un sistema que predice partidos del Mundial 2026 con matemáticas.'],
  ['04', 'Demostración en vivo', 'Elegimos dos equipos y vemos la predicción al instante.'],
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
  ['Nivel', 'Alto', 'hablas "humano", no el idioma de la máquina'],
  ['Ejecución', 'Interpretado', 'se corre al momento — no hay que compilarlo primero'],
  ['Tipado', 'Dinámico y fuerte', 'no declaras tipos, pero no los mezcla a escondidas'],
  ['Memoria', 'Automática', 'limpia sola lo que ya no se usa'],
]
export function PythonSpec() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="01">El lenguaje</Kicker>
      <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
        <div>
          <H2>¿Qué es Python?</H2>
          <Lede>
            Un <b className="text-ink">lenguaje de programación</b>: el idioma con el que le damos
            órdenes a una computadora. Python es uno de los más populares del mundo, famoso por ser{' '}
            <b className="text-ink">fácil de leer</b>.
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

// 4 · INTERPRETED vs COMPILED ----------------------------------------------
export function InterpretedSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="01 ·">Una idea clave</Kicker>
      <H2>Interpretado, no compilado</H2>
      <Lede>La diferencia, sin tecnicismos: es la forma en que la computadora "entiende" tu código.</Lede>
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
              Se traduce todo el programa a idioma de máquina <b className="text-ink">antes</b> de
              usarlo. Muy rápido después, pero rígido y con un paso extra.
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
              Traduce y ejecuta <b className="text-ink">frase por frase</b>, al momento. Escribes y
              corres al instante — ideal para probar ideas rápido.
            </p>
          </Panel>
        </Item>
      </div>
      <Item>
        <p className="font-mono text-[15px] md:text-[17px] text-dim mt-6 leading-relaxed">
          Por eso Python es perfecto para <b className="text-ink">experimentar</b> — justo lo que se
          hace al construir un modelo estadístico.
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
        Empezó como el pasatiempo de una sola persona. Su superpoder nunca fue la velocidad, sino
        ser <b className="text-ink">fácil de leer</b>.
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
      <Lede>Aunque no lo veas, probablemente ya interactuaste con Python hoy varias veces.</Lede>
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
        Python trae "cajas de herramientas" (librerías) listas para los números.{' '}
        <b className="text-ink">Mi proyecto se construye sobre estas cuatro.</b>
      </Lede>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5 mt-7">
        <Card tag="tablas" title="pandas">
          Maneja datos gigantes como una hoja de Excel programable.
        </Card>
        <Card tag="números" title="NumPy">
          Hace millones de cálculos de golpe, a gran velocidad.
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
          Tu correo aprende a separar lo importante de la basura.
        </Card>
        <Card tag="reconocer" title="Desbloqueo facial">
          Tu teléfono aprende a reconocer tu cara.
        </Card>
        <Card tag="predecir" title="Autocorrector">
          Adivina la siguiente palabra que vas a escribir.
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

// 10 · PROJECT --------------------------------------------------------------
export function ProjectSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="05">El proyecto</Kicker>
      <H2>Predictor del Mundial 2026</H2>
      <Lede>
        Eliges dos selecciones y el sistema calcula la predicción en un instante — y simula el
        torneo completo. Todo en Python, de los datos a la app.
      </Lede>
      <div className="grid md:grid-cols-3 gap-4 md:gap-5 mt-7">
        <Card tag="predicción" title="1X2 + goles">
          Probabilidad de que gane uno, empate o gane el otro, y los goles esperados de cada equipo.
        </Card>
        <Card tag="marcador" title="Score probable">
          El marcador más probable, un top-3 y mercados como córners y tarjetas.
        </Card>
        <Card tag="torneo" title="Simulación">
          Arma los grupos con las reglas oficiales de la FIFA y avanza el cuadro final.
        </Card>
      </div>
      <Item>
        <div className="flex flex-wrap gap-2.5 mt-7">
          <Chip tone="pitch">Python 3.12</Chip>
          <Chip>pandas · numpy · scipy</Chip>
          <Chip tone="py">Streamlit</Chip>
          <Chip>pytest</Chip>
        </div>
      </Item>
    </Stagger>
  )
}

// 11 · PIPELINE -------------------------------------------------------------
const STEPS = [
  { tag: '1 · datos', title: 'Historial', desc: 'Miles de partidos internacionales reales.' },
  { tag: '2 · features', title: 'Características', desc: 'Fuerza, ranking, valor de cada selección.' },
  { tag: '3 · modelo', title: 'Aprende', desc: 'Ajusta sus parámetros con los datos.' },
  { tag: '4 · predice', title: 'Probabilidades', desc: 'Calcula el resultado más probable.' },
  { tag: '5 · app', title: 'Streamlit', desc: 'Lo muestra en una pantalla simple.' },
]
export function PipelineSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="05 ·">Cómo encaja todo</Kicker>
      <H2>De los datos a la predicción</H2>
      <Lede>Un solo lenguaje recorre todo el camino, paso a paso.</Lede>
      <Item>
        <div className="mt-7">
          <Pipeline steps={STEPS} />
        </div>
      </Item>
      <Item>
        <p className="font-mono text-[15px] md:text-[17px] text-dim mt-7 leading-relaxed">
          <b className="text-ink">Los datos vienen de fuentes abiertas</b> de fútbol (StatsBomb,
          FBref, resultados internacionales). Nada es inventado: todo se aprende del historial real.
        </p>
      </Item>
    </Stagger>
  )
}

// 12 · HOW TO READ A PREDICTION --------------------------------------------
export function ProbabilitySlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="06">Antes del modelo</Kicker>
      <H2>¿Cómo se lee una predicción?</H2>
      <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
        <div>
          <Lede>
            El modelo no dice "ganará Argentina". Dice{' '}
            <b className="text-ink">"Argentina tiene 63% de probabilidad"</b>.
          </Lede>
          <Item>
            <p className="text-xl md:text-[28px] text-ink/80 leading-relaxed mt-5 max-w-[40ch]">
              Es decir: si el partido se jugara <b className="text-white">100 veces</b>, ganaría unas
              63. El favorito <b className="text-white">pierde a menudo</b> — y que eso pase es
              justamente lo que hace emocionante al fútbol.
            </p>
          </Item>
        </div>
        <Item>
          <Panel className="p-6 md:p-8">
            <div className="font-mono text-[12px] tracking-[0.12em] uppercase text-dim mb-4">
              Ejemplo · ARG vs BRA
            </div>
            <Odds
              rows={[
                { name: 'Gana ARG', value: 0.63, color: '#e8b23a' },
                { name: 'Empate', value: 0.22, color: '#a99a80' },
                { name: 'Gana BRA', value: 0.15, color: '#d8452a' },
              ]}
            />
            <p className="font-mono text-[14px] md:text-[16px] text-dim mt-5 leading-relaxed">
              Las tres probabilidades siempre suman 100%.
            </p>
          </Panel>
        </Item>
      </div>
    </Stagger>
  )
}

// 13 · MODEL ----------------------------------------------------------------
export function ModelSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="07">Cómo funciona el modelo</Kicker>
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

// 14 · TRAINING -------------------------------------------------------------
const BACKTEST = [
  { name: 'Modelo', value: 0.593, color: '#e8b23a' },
  { name: 'Elo-puro', value: 0.588, color: '#4fb0a3' },
  { name: 'Naive (azar)', value: 0.667, color: '#d8452a' },
]
export function TrainingSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="08">Cómo aprende y se entrena</Kicker>
      <H2>Ajustar hasta explicar el pasado</H2>
      <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-start">
        <ul className="grid gap-4 md:gap-5">
          <Bullet>
            <b className="text-ink">Aprender</b> = ajustar los números del modelo hasta explicar bien
            miles de partidos reales.
          </Bullet>
          <Bullet>
            Un <b className="text-ink">optimizador</b> baja el error "cuesta abajo" hasta el mínimo.
          </Bullet>
          <Bullet>
            Se le pone un <b className="text-ink">freno</b> para que no memorice rarezas, y se prueba
            en partidos que no vio.
          </Bullet>
          <Bullet>
            No es una caja negra: es <b className="text-ink">machine learning interpretable</b>.
          </Bullet>
        </ul>
        <Item>
          <Panel className="p-6 md:p-8">
            <div className="font-mono text-[12px] tracking-[0.12em] uppercase text-goal">
              la prueba honesta · 256 partidos · menor = mejor
            </div>
            <h3 className="font-display font-bold text-2xl mt-2 mb-1.5 tracking-tightest">
              ¿De verdad funciona?
            </h3>
            <p className="text-ink/75 text-[17px] md:text-[20px] leading-snug mb-5">
              Se prueba prediciendo Mundiales pasados con datos que el modelo no había visto.
            </p>
            <BacktestBars data={BACKTEST} />
            <p className="font-mono text-[14px] md:text-[16px] text-dim mt-5 leading-relaxed">
              Le gana al azar en todas las métricas · acierta el{' '}
              <b className="text-ink">marcador exacto 14.5%</b> de las veces.
            </p>
          </Panel>
        </Item>
      </div>
    </Stagger>
  )
}

// 15 · DEMO -----------------------------------------------------------------
export function DemoSlide() {
  return (
    <Stagger className="w-full max-w-6xl mx-auto">
      <Kicker num="09">Demostración en vivo</Kicker>
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
      <Kicker num="10">Conclusiones</Kicker>
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
  { section: 'El lenguaje', Comp: InterpretedSlide },
  { section: 'Historia', Comp: HistorySlide },
  { section: 'Usos reales', Comp: UsesSlide },
  { section: 'Datos y estadística', Comp: EcosystemSlide },
  { section: 'Machine Learning', Comp: MLSlide },
  { section: 'Machine Learning', Comp: MLDailySlide },
  { section: 'El proyecto', Comp: ProjectSlide },
  { section: 'El proyecto', Comp: PipelineSlide },
  { section: 'Probabilidades', Comp: ProbabilitySlide },
  { section: 'El modelo', Comp: ModelSlide },
  { section: 'Entrenamiento', Comp: TrainingSlide },
  { section: 'Demostración', Comp: DemoSlide },
  { section: 'Cierre', Comp: ClosingSlide },
]

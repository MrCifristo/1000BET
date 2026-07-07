# Guión del presentador — *Python y la predicción del Mundial 2026*

> Clase **Evolution of Computing**. Deck de 16 diapositivas.
> Este guión te da, por cada slide: **qué se ve**, **qué decir** (más de lo que está en pantalla),
> un **dato extra / si preguntan**, y la **transición** a la siguiente.
> No hace falta leerlo palabra por palabra: son apoyos para que hables con seguridad.
>
> **Duración objetivo:** ~12–15 min de charla + demo en vivo. Ritmo: ~45–60 s por slide de contenido.
> **Regla de oro:** la pantalla es el titular; tú eres la explicación. No leas los slides — amplíalos.

---

## 1 · Apertura — «Python y la predicción del Mundial 2026»

**En pantalla:** título, tu nombre, y el subtítulo "¿Se puede predecir un partido? No con certeza, pero sí con probabilidades".

**Qué decir:**
- Arranca con la pregunta, no con tu nombre: *"¿Se puede predecir quién gana un partido de fútbol?"* Deja un segundo de silencio.
- *"La respuesta honesta es: no con certeza. Si se pudiera, no habría apuestas ni sorpresas. Pero sí se puede poner un número a cada resultado — una probabilidad. Y la herramienta con la que se hace eso hoy, en la ciencia y en la industria, es Python."*
- *"Hoy les voy a contar dos cosas a la vez: qué es Python y por qué se volvió tan importante, y un proyecto real que construí con él para predecir el Mundial 2026."*

**Dato extra / si preguntan:** el hilo conductor de toda la charla es que **el mismo lenguaje** hace todo el recorrido: bajar datos, limpiarlos, entrenar un modelo matemático y publicarlo como app. Esa es la idea que quieres que se lleven.

**Transición:** *"Antes de meternos, esto es lo que veremos."*

---

## 2 · El plan de hoy (Agenda)

**En pantalla:** 4 bloques — (1) Qué es Python, (2) Por qué reina en datos e IA, (3) Mi proyecto, (4) Demo en vivo.

**Qué decir:**
- Recorre los 4 puntos en 15 segundos. *"Primero, qué tipo de herramienta es Python y de dónde viene. Segundo, por qué se volvió el idioma de la ciencia de datos y la inteligencia artificial. Tercero, mi proyecto: un sistema que predice partidos del Mundial. Y cerramos con una demostración en vivo."*
- Marca expectativa: *"La parte final es interactiva — vamos a elegir dos equipos y ver la predicción al instante."*

**Transición:** *"Empecemos por lo básico: ¿qué es exactamente Python?"*

---

## 3 · El lenguaje — «¿Qué es Python?»

**En pantalla:** definición + ficha técnica (Nivel: Alto · Ejecución: Interpretado · Tipado: Dinámico y fuerte · Memoria: Automática).

**Qué decir:**
- *"Python es de los lenguajes más usados del mundo, y su fama viene de un rasgo concreto: la legibilidad. El código se lee casi como inglés, y eso acorta la distancia entre pensar una idea y ejecutarla."*
- Traduce la ficha técnica, término por término:
  - **Alto nivel** → *"escribes pensando en el problema, no en cómo funciona el hardware por dentro. El lenguaje se encarga de los detalles de bajo nivel."*
  - **Interpretado** → *"se ejecuta al instante, sin un paso de compilación previo; lo vemos con calma en el siguiente slide."*
  - **Tipado dinámico y fuerte** → *"no declaras de antemano si algo es un número o un texto —eso es lo dinámico—, pero el lenguaje tampoco convierte entre tipos por su cuenta: si intentas sumar un número con un texto, avisa con un error en vez de improvisar. Eso es lo fuerte."*
  - **Memoria automática** → *"no reservas ni liberas memoria a mano; Python gestiona solo la que deja de usarse. En lenguajes como C eso corre por cuenta del programador, y es una fuente clásica de errores."*

**Dato extra / si preguntan:** "multiparadigma" significa que admite varios estilos de programación —estructurado, orientado a objetos y funcional—, de modo que se adapta a proyectos muy distintos.

**Transición:** *"De todas estas, hay una que vale la pena entender bien porque explica por qué Python es tan cómodo para experimentar: que es interpretado."*

---

## 4 · Una idea clave — «Interpretado, no compilado»

**En pantalla:** dos tarjetas — Compilado (C, Rust): "traducir el libro entero"; Interpretado (Python): "un intérprete simultáneo".

**Qué decir:**
- Usa la analogía tal cual, que es muy buena: *"Imaginen que tienen un libro en otro idioma. Un lenguaje **compilado** es como contratar a un traductor que traduce el libro entero antes de que puedan leer una sola página: hay una espera al inicio, pero después la lectura es rapidísima. Un lenguaje **interpretado** como Python es un **intérprete simultáneo**: traduce frase por frase a medida que avanzan. Empiezan de inmediato."*
- El *por qué importa*: *"Para construir un modelo estadístico uno prueba una idea, ve el resultado, la ajusta, prueba otra… decenas de veces. Con Python ese ciclo es instantáneo: escribes y corres. Esa agilidad para experimentar es justo lo que se necesita en ciencia de datos."*

**Dato extra / si preguntan:** técnicamente Python primero se traduce a un lenguaje intermedio llamado **bytecode** y lo ejecuta una **máquina virtual** (la CPython). No es "línea de texto directo a la CPU", pero para la analogía basta con "traduce y ejecuta al momento". El precio de esta comodidad es velocidad — y por eso el siguiente punto: las librerías pesadas están escritas en C por dentro.

**Transición:** *"¿Y de dónde salió este lenguaje? Su historia explica mucho de su personalidad."*

---

## 5 · Historia — «Un proyecto de Navidad que conquistó la IA»

**En pantalla:** línea de tiempo 1989 → 2020 y la nota "se llama por Monty Python, no por la serpiente".

**Qué decir:**
- *"Python lo empezó **Guido van Rossum** en 1989, en Ámsterdam, como un proyecto personal durante las vacaciones de Navidad — literalmente para no aburrirse."*
- *"El nombre no viene de la serpiente, sino del grupo de comedia británico **Monty Python**. Por eso mucha documentación tiene chistes escondidos."*
- Recorre la línea: 1991 primera versión pública; 2000 Python 2 y se populariza; 2008 Python 3, que mejoró el lenguaje **rompiendo compatibilidad** con la 2 (una decisión valiente y polémica); 2020 se apaga oficialmente Python 2 — hoy cuando alguien dice "Python" habla de Python 3.
- Remata con la tesis del slide: *"Su ventaja decisiva nunca fue la velocidad, sino la **legibilidad**. Y resultó que eso — que un científico pudiera escribir y entender el código sin ser ingeniero de software — fue exactamente lo que lo convirtió en el idioma de la ciencia de datos y la IA."*

**Dato extra / si preguntan:** a Guido se le conocía como el *"BDFL" (Benevolent Dictator For Life / dictador benévolo de por vida)* — tenía la última palabra en el diseño del lenguaje. En 2018 renunció a ese rol y hoy Python se gobierna por un comité (el *Steering Council*) y propuestas abiertas llamadas **PEP**.

**Transición:** *"Y hoy, aunque no lo veas, Python está por todos lados."*

---

## 6 · Usos reales — «Python está en lo que usas a diario»

**En pantalla:** 4 tarjetas — Netflix, Instagram, ChatGPT, la primera foto de un agujero negro.

**Qué decir:**
- *"Probablemente ya usaste Python varias veces hoy sin saberlo."*
  - **Netflix:** su sistema de recomendaciones — el "porque viste tal serie" — corre en gran parte sobre Python.
  - **Instagram:** una de las mayores aplicaciones del mundo; buena parte de su servidor está escrito en Python.
  - **ChatGPT:** los modelos de IA se entrenan y sirven mayormente con Python.
  - **Agujero negro:** la primera imagen de uno, en 2019, se procesó con librerías científicas de Python.
- Cierra: *"Web, automatización, finanzas, ciencia, inteligencia artificial… es un lenguaje de propósito general. Pero donde de verdad domina es en los datos. ¿Por qué?"*

**Dato extra / si preguntan:** el caso del agujero negro es potente porque fueron ~5 petabytes de datos de telescopios de todo el mundo; el software de reconstrucción de imagen (proyecto EHT) es abierto y en Python.

**Transición:** *"La respuesta a ese 'por qué' es una sola palabra: ecosistema."*

---

## 7 · Datos y estadística — «Su fuerza es el ecosistema»

**En pantalla:** 4 librerías — pandas, NumPy, SciPy, matplotlib — y la frase "mi proyecto se construye sobre estas cuatro".

**Qué decir:**
- *"Python por sí solo es cómodo pero lento. Su verdadera fuerza son las **librerías**: colecciones de herramientas ya construidas que amplían lo que puede hacer. Y aquí está la clave: por dentro están escritas en C, un lenguaje rapidísimo. Tú escribes código simple y legible, y el trabajo numérico pesado corre por debajo a toda velocidad."*
- Presenta las cuatro con su rol en TU proyecto:
  - **pandas** → *"maneja tablas de datos gigantes como una hoja de Excel programable. Aquí guardo el historial de partidos."*
  - **NumPy** → *"ejecuta millones de operaciones matemáticas de una sola vez, de forma vectorizada."*
  - **SciPy** → *"la más importante para mí: trae la **distribución de Poisson** y el **optimizador** que entrena mi modelo."*
  - **matplotlib** → *"convierte los números en gráficas y mapas de calor para poder leerlos."*
- Subraya: *"Estas cuatro no son teoría — son literalmente las piezas sobre las que está construido mi predictor."*

**Dato extra / si preguntan:** pandas lo creó Wes McKinney en 2008 para análisis financiero. "Vectorizado" (NumPy) quiere decir que aplica una operación a un arreglo entero de una sola vez, en vez de recorrerlo elemento por elemento — por eso es cientos de veces más rápido que un bucle en Python puro.

**Transición:** *"Con estas herramientas se hace ciencia de datos. Pero hay una idea todavía más grande encima: el machine learning."*

---

## 8 · Machine Learning — «Aprender reglas, no programarlas»

**En pantalla:** dos ecuaciones. Clásica: Reglas + Datos → Respuestas. ML: Datos + Respuestas → Reglas.

**Qué decir:**
- *"Esta es la idea más importante de toda la charla, y cabe en dos líneas."*
- *"En la **programación clásica**, yo escribo las reglas a mano: 'si pasa esto, haz aquello'. Le doy reglas y datos, y me devuelve respuestas."*
- *"El **machine learning** le da la vuelta: le doy **datos y respuestas** — muchos ejemplos del pasado — y la máquina **descubre las reglas sola**."*
- Analogía del slide, dila con calma: *"Es como aprende un niño qué es una manzana. No le lees una definición botánica. Le muestras muchas manzanas y su cerebro extrae el patrón solo. El machine learning hace exactamente eso, pero con datos."*
- Conecta con tu proyecto (importante): *"En mi caso, los 'ejemplos' son miles de partidos reales con su marcador. El modelo aprende de ahí qué tan fuerte ataca y defiende cada selección — yo nunca le digo 'Brasil es bueno'; lo deduce de los resultados."*

**Dato extra / si preguntan:** tu modelo es un tipo de ML **interpretable** — no una caja negra. Lo retomas en el slide del modelo. Distinción útil: la programación clásica es determinista; el ML es estadístico, trabaja con probabilidades y con incertidumbre.

**Transición:** *"Y al igual que Python, el machine learning ya está en tu bolsillo."*

---

## 9 · ML en tu día a día

**En pantalla:** 4 tarjetas — recomendaciones, filtro de spam, desbloqueo facial, autocorrector — y por qué Python domina el campo.

**Qué decir:**
- Recorre rápido los ejemplos, todos cotidianos: *"El 'porque viste…' de Netflix o Spotify; el filtro de spam que aprende a separar lo importante de la basura; el desbloqueo facial de tu teléfono que aprende tu cara; el autocorrector que adivina la siguiente palabra. Todo eso es machine learning."*
- Cierra el arco Python + ML: *"¿Y por qué Python domina este campo? Porque cuando llegó el boom de la IA, el ecosistema numérico — NumPy, SciPy — **ya existía**. Encima se construyeron las grandes librerías de ML: scikit-learn, TensorFlow, PyTorch. Y como es fácil de leer, es ideal para investigar y probar ideas nuevas."*

**Dato extra / si preguntan:** frase útil — *"Python orquesta, la GPU ejecuta"*: en el deep learning, Python coordina y las operaciones pesadas corren en tarjetas gráficas por debajo. Otra vez el patrón "lenguaje cómodo arriba, motor rápido abajo".

**Transición:** *"Con esto ya tenemos las dos piezas: Python y machine learning. Ahora sí — mi proyecto."*

---

## 10 · El proyecto — «Predictor del Mundial 2026»

**En pantalla:** 3 tarjetas (1X2 + goles · Score probable · Simulación del torneo) y el stack (Python 3.12 · pandas·numpy·scipy · Streamlit · pytest).

**Qué decir:**
- *"Construí un sistema que predice partidos del Mundial 2026 — el que se juega en Canadá, Estados Unidos y México."*
- Explica las tres capacidades:
  - **Predicción 1X2 + goles:** *"eliges dos selecciones y te da la probabilidad de que gane una, empate o gane la otra, más los goles esperados de cada equipo."*
  - **Marcador probable:** *"el resultado más probable, un top-3 de marcadores, e incluso mercados como córners, tarjetas, tiros y faltas."*
  - **Simulación del torneo:** *"arma los grupos con las reglas oficiales de desempate de la FIFA y avanza el cuadro completo, de la fase de grupos a la final, actualizándose con resultados reales."*
- Sobre el stack: *"Y fíjense — todo es Python: pandas y numpy para los datos, scipy para la matemática, Streamlit para la app, pytest para las pruebas. Un solo lenguaje de principio a fin."*

**Dato extra / si preguntan:** el Mundial 2026 es el primero con **48 selecciones** (antes 32), lo que cambia el formato de grupos y el cuadro — por eso el motor de torneo tuvo que programarse con la numeración nueva de la FIFA. "Coherente" en el marcador significa que el marcador que muestro nunca contradice al favorito del 1X2 (si digo que gana ARG, el marcador sugerido no será una derrota de ARG).

**Transición:** *"¿Y cómo encaja todo eso? Es una tubería de datos, paso a paso."*

---

## 11 · El proyecto — «De los datos a la predicción» (Pipeline)

**En pantalla:** 5 pasos — Datos → Características → Aprende → Predice → App — y la nota de que los datos son de fuentes abiertas.

**Qué decir:**
- Recorre la tubería como una historia: *"Paso 1, **datos**: miles de partidos internacionales reales. Paso 2, **características**: de cada selección calculo su fuerza, su ranking, el valor de su plantilla. Paso 3, el **modelo aprende**: ajusta sus números con esos datos. Paso 4, **predice**: calcula las probabilidades. Paso 5, la **app**: lo muestra en una pantalla simple con Streamlit."*
- Punto de credibilidad, dilo con énfasis: *"Algo importante: **nada de esto es inventado**. Los datos vienen de fuentes abiertas de fútbol — StatsBomb, FBref, bases de resultados internacionales. Todo lo que predice el modelo lo aprendió del historial real."*

**Dato extra / si preguntan:** en el repo esta tubería son scripts numerados `01_…` a `12_…` que se corren en orden; cada uno produce un archivo de datos que el siguiente consume. Esa disciplina hace el proyecto **reproducible**: cualquiera puede regenerar todo desde cero.

**Transición:** *"Antes de abrir el modelo, aclaremos qué significa realmente una predicción — porque no es lo que la gente cree."*

---

## 12 · Antes del modelo — «¿Cómo se lee una predicción?»

**En pantalla:** ejemplo ARG vs BRA — Gana ARG 63% · Empate 22% · Gana BRA 15% — y "siempre suman 100%".

**Qué decir:**
- Corrige la intuición común: *"El modelo **no dice** 'ganará Argentina'. Dice 'Argentina tiene 63% de probabilidad'. Son cosas distintas."*
- La frase clave: *"Piénsenlo así: si este partido se jugara **100 veces**, Argentina ganaría unas 63. Pero eso significa que **37 veces no gana**. El favorito pierde a menudo — y que eso pase es justamente lo que hace emocionante al fútbol."*
- *"Las tres probabilidades — gana, empata, pierde — siempre suman 100%. El modelo reparte esa certeza total entre los tres resultados posibles."*

**Dato extra / si preguntan:** esta es la diferencia entre un modelo **honesto** y uno que "las adivina". Un buen modelo probabilístico se juzga no por si acertó el ganador, sino por si sus probabilidades están **bien calibradas**: cuando dice 63%, ¿acierta ~63% de las veces? Eso es lo que mide el backtest (slide 14).

**Transición:** *"Ahora sí, abramos la caja: ¿cómo calcula ese 63%?"*

---

## 13 · El modelo — «Todo se reduce a estimar λ»

**En pantalla:** barras de Poisson para λ=1.8, la fórmula de log(λ), y la leyenda (α−β, host, elo·xg·valor).

**Qué decir:**
- Empieza por la intuición de Poisson: *"Los goles son **eventos raros y separados** en el tiempo — pasan pocos por partido y en momentos impredecibles. Hay una fórmula matemática hecha justo para contar eventos raros: la **distribución de Poisson**. Con un solo número, la **λ** (lambda), te dice la probabilidad de que haya 0 goles, 1, 2, 3…"*
- Señala las barras: *"Esto es Poisson para λ=1.8 goles esperados: lo más probable son 1 o 2 goles, y cada vez menos probable ir subiendo. Suena abstracto, pero es literalmente la forma de los goles en el fútbol real."*
- Ahora la fórmula, sin asustar a nadie: *"Entonces **todo el modelo se reduce a una pregunta**: ¿cuál es la λ de cada equipo en este partido? Y eso lo calculo sumando factores:"*
  - **α − β:** *"el ataque de mi equipo menos la defensa del rival — lo esencial."*
  - **host:** *"la ventaja de jugar como anfitrión."*
  - **elo · xg · valor:** *"el ranking Elo, la calidad de las ocasiones (xG) y el valor de mercado de la plantilla."*
- Remata con la joya del proyecto: *"Y lo mejor: es **interpretable**. Cada número significa algo real. Si ordeno los equipos por su α, obtengo un **ranking de verdad de las mejores delanteras del mundo**. No es una caja negra."*

**Dato extra / si preguntan:**
- La fórmula completa: `log(λ_i) = μ + α_i − β_j + γ·host + δ·elo_diff + ε·xg_diff + ζ·log(valor_i/valor_j)`. Se modela `log(λ)` y no `λ` directamente para que el resultado nunca sea negativo (no existen goles negativos).
- **Dixon-Coles:** Poisson simple subestima los empates bajos (0-0, 1-1). Dixon y Coles (1997) añadieron un factor de corrección τ que ajusta solo esos marcadores bajos. Mi modelo lo incluye. Por eso es "Poisson bivariado + corrección Dixon-Coles".
- **Bivariado** = modela los goles de **ambos** equipos, no de uno solo.

**Transición:** *"Pero, ¿de dónde salen esos números — las α, las β? Ahí entra el aprendizaje."*

---

## 14 · Entrenamiento — «Ajustar hasta explicar el pasado»

**En pantalla:** 4 bullets (aprender = ajustar; optimizador; freno/validación; ML interpretable) y el recuadro de backtest (Modelo 0.593 · Elo-puro 0.588 · Naive 0.667 · 256 partidos · marcador exacto 14.5%).

**Qué decir:**
- Define "aprender" en concreto: *"'Aprender' aquí no es magia. Es **ajustar los números del modelo** — las α, las β, los pesos — hasta que expliquen lo mejor posible miles de partidos reales que sí sabemos cómo terminaron."*
- El optimizador: *"De eso se encarga un **optimizador**. Imaginen un valle: el 'error' del modelo es la altura, y el optimizador baja 'cuesta abajo' hasta el punto más bajo — el mínimo error. Ese proceso, repetido, es el entrenamiento."*
- El freno (muy importante para sonar riguroso): *"Le pongo un **freno** llamado regularización para que no **memorice** rarezas del pasado, y luego lo pruebo en partidos que **nunca vio**. Un modelo que solo memoriza es inútil; uno que generaliza sirve."*
- El backtest: *"¿Y de verdad funciona? Lo probé prediciendo Mundiales **pasados** con datos que el modelo no había visto — una prueba honesta, 256 partidos. Se mide con el **Brier score**, donde **menos es mejor**."*
  - *"El azar puro (1/3 a cada resultado) saca 0.667. Mi modelo saca 0.593 — claramente mejor que tirar una moneda. Y acierta el **marcador exacto un 14.5%** de las veces, que para fútbol es bastante."*

**Dato extra / si preguntan (¡prepárate esta!):**
- Alguien observador notará que el **Elo puro (0.588) sale marginalmente mejor que mi modelo (0.593) en Brier**. Respuesta honesta y fuerte: *"Buena observación. En Brier están empatados prácticamente; pero en **log-loss** —una métrica que castiga más la sobre-confianza— mi modelo gana claro, 1.00 contra 1.28. Además mi modelo da mucho más que un 1X2: da goles esperados, marcador probable y mercados, cosa que el Elo solo no hace."* Nunca escondas esto; reconocerlo te hace ver riguroso.
- **Point-in-time / sin look-ahead:** al backtestear, solo uso el Elo y los datos que existían **antes** de cada partido. Si usara datos del futuro para "predecir" el pasado, haría trampa y los números serían mentira. Esa disciplina es lo que hace el backtest creíble.
- **Brier score** = promedio del error cuadrático entre la probabilidad que dije y lo que pasó (1 si ocurrió, 0 si no). **Log-loss** castiga fuerte estar muy seguro y equivocarte. **RPS** tiene en cuenta el orden (ganar/empatar/perder no son categorías sueltas).

**Transición:** *"Suficiente teoría. Veámoslo funcionando."*

---

## 15 · Demostración en vivo

**En pantalla:** "Elige dos equipos. Lee la predicción." + un mock de ARG vs BRA con mapa de calor de marcadores.

**Qué decir / hacer:**
- **Aquí cambias a la app real de Streamlit.** (Ver checklist de demo abajo.)
- Narra mientras operas: *"Elijo dos selecciones… y en un instante el modelo me da las probabilidades, los goles esperados de cada uno, y este **mapa de calor**: cada casilla es un marcador posible y el color es su probabilidad. La casilla más caliente es el resultado más probable."*
- Si hay tiempo, muestra el torneo: *"Y aquí puedo simular el Mundial completo — los grupos se ordenan con los desempates oficiales de la FIFA y el cuadro avanza hasta la final."*
- Conecta con la teoría: *"Todo lo que ven en esta pantalla es la fórmula λ y la Poisson del slide anterior — solo que envuelto en algo que cualquiera puede usar sin saber matemáticas."*

**Dato extra / si preguntan:** Streamlit convierte un script de Python en una app web sin escribir nada de HTML ni JavaScript — por eso un proyecto de ciencia de datos puede volverse una app usable en pocas líneas.

**Transición:** *"Y con eso cerramos el círculo."*

---

## 16 · Cierre — «De una idea matemática a una app que funciona»

**En pantalla:** 3 conclusiones (un lenguaje para todo · aprender de los datos · estadística interpretable) + "¡Gracias! ¿Preguntas?".

**Qué decir:**
- Recapitula las tres ideas con las que quieres que se queden:
  1. *"**Un solo lenguaje para todo.** Python me llevó de los datos crudos hasta una app, sin cambiar de herramienta en el camino."*
  2. *"**Aprender de los datos.** El machine learning descubre las reglas a partir de ejemplos; no se las programa a mano."*
  3. *"**Estadística interpretable.** Cada número de mi modelo significa algo real. No es una caja negra: es matemática que se puede leer y explicar."*
- Cierre personal: *"Empezó como una idea matemática — contar goles con una fórmula del siglo XIX — y terminó como una app que predice el Mundial. Ese recorrido completo es lo que Python hace posible."*
- *"Gracias. ¿Preguntas?"*

---

## Checklist para la demo en vivo (slide 15)

- [ ] **Antes de empezar la charla**, deja la app ya corriendo en otra pestaña: `streamlit run src/ui/app.py`. No la arranques en vivo.
- [ ] Ten elegido de antemano un partido con buen contraste (p. ej. **ARG vs BRA**, o anfitrión vs. debutante) para que las probabilidades se vean interesantes.
- [ ] Ten un **plan B**: si la app falla, el slide 15 ya trae un mock con el mapa de calor. Puedes explicar sobre él sin drama.
- [ ] Zoom del navegador al 110–125% para que se lea desde el fondo del salón.
- [ ] Practica el recorrido una vez: elegir equipos → leer 1X2 → señalar goles esperados → señalar la casilla más caliente del mapa → (opcional) pestaña de torneo.

## Preguntas difíciles — respuestas de bolsillo

- **"¿Entonces vas a acertar quién gana el Mundial?"** → *"No, y ese no es el objetivo. Doy probabilidades, no certezas. El valor está en cuantificar la incertidumbre, no en eliminarla."*
- **"¿Esto sirve para apostar?"** → *"El modelo estima probabilidades 'justas'; una casa de apuestas te gana por el margen que cobra. Es un ejercicio estadístico, no un esquema para hacer dinero."*
- **"¿Por qué Poisson y no una red neuronal / IA moderna?"** → *"Porque con los datos que hay (miles, no millones de partidos) un modelo interpretable rinde igual o mejor y, sobre todo, **puedo explicar cada número**. Una red neuronal sería una caja negra con más riesgo de sobreajuste."*
- **"¿De dónde sacas los datos?"** → *"Fuentes abiertas: StatsBomb, FBref, bases de resultados internacionales. Todo público y reproducible."*
- **"¿Y si un equipo cambió mucho (lesiones, nuevo técnico)?"** → *"El modelo usa forma reciente vía Elo y valor de plantilla actual, pero no lee noticias — esa es una limitación honesta y una línea de mejora futura."*

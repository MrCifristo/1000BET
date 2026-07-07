# Guión del presentador — *Python y la predicción del Mundial 2026*

> Clase **Evolution of Computing**. Deck de 17 diapositivas.
> Este guión te da, por cada slide: **qué se ve**, **qué decir** (más de lo que está en pantalla),
> un **dato extra / si preguntan**, y la **transición** a la siguiente.
> No hace falta leerlo palabra por palabra: son apoyos para que hables con seguridad.
>
> **Estructura:** Python y Machine Learning son el núcleo expositivo (slides 3–13); el proyecto se
> presenta como **demo en vivo** (slides 14–16). Duración flexible: ~8–12 min de charla + demo.
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

**En pantalla:** 3 bloques — (1) Python, (2) Machine Learning, (3) El proyecto, en vivo.

**Qué decir:**
- Recorre los 3 puntos en 15 segundos. *"Primero, Python: qué es, cómo se ve su código y por qué se volvió el idioma de la ciencia de datos. Segundo, el machine learning: cómo una máquina aprende reglas a partir de los datos, en vez de que uno se las programe. Y tercero, mi proyecto — un sistema que predice el Mundial — que veremos funcionando en vivo."*
- Marca expectativa: *"Las dos primeras partes son las importantes; el proyecto es la demostración de que todo eso junto funciona."*

**Transición:** *"Empecemos por lo básico: ¿qué es exactamente Python?"*

---

## 3 · El lenguaje — «¿Qué es Python?»

**En pantalla:** definición + ficha técnica (Nivel: Alto · Ejecución: Interpretado · Tipado: Dinámico y fuerte · Memoria: Automática).

**Qué decir:**
- *"Python es de los lenguajes más usados del mundo, y su fama viene de un rasgo concreto: la legibilidad. El código se lee casi como inglés, y eso acorta la distancia entre pensar una idea y ejecutarla."*
- Traduce la ficha técnica, término por término:
  - **Alto nivel** → *"escribes pensando en el problema, no en cómo funciona el hardware por dentro. El lenguaje se encarga de los detalles de bajo nivel."*
  - **Interpretado** → *"se ejecuta al instante, sin un paso de compilación previo; lo vemos con calma en un par de slides."*
  - **Tipado dinámico y fuerte** → *"no declaras de antemano si algo es un número o un texto —eso es lo dinámico—, pero el lenguaje tampoco convierte entre tipos por su cuenta: si intentas sumar un número con un texto, avisa con un error en vez de improvisar. Eso es lo fuerte."*
  - **Memoria automática** → *"no reservas ni liberas memoria a mano; Python gestiona solo la que deja de usarse. En lenguajes como C eso corre por cuenta del programador, y es una fuente clásica de errores."*

**Dato extra / si preguntan:** "multiparadigma" significa que admite varios estilos de programación —estructurado, orientado a objetos y funcional—, de modo que se adapta a proyectos muy distintos.

**Transición:** *"Y esto no es abstracto — miremos un pedazo de código real de mi proyecto."*

---

## 4 · El lenguaje — «El código se lee casi solo» (código real)

**En pantalla:** un fragmento real de `poisson_model.py`: la función que calcula los goles esperados de un equipo. Dos líneas resaltadas y anotaciones.

**Qué decir:**
- *"Esto es código real de mi proyecto, no un ejemplo de juguete. Calcula los goles que esperamos de un equipo en un partido. Y fíjense: aunque no sepan programar, casi se entiende."*
- Señala la línea del `host`: *"Esta línea dice, literalmente, 'host vale 1 si el equipo juega en casa, si no vale 0'. Se lee casi como una frase en inglés — ese es el punto de Python."*
- Señala el bloque de `log_lam`: *"Y esta suma de aquí —ataque, menos defensa del rival, más la ventaja de local, más el ranking— es exactamente la fórmula del modelo que veremos más adelante. El código y la matemática son casi la misma cosa."*
- Remata sin tecnicismos: *"La idea que quiero que se lleven es que en Python el código se parece al problema que resuelve. Eso es lo que lo hace ideal para la ciencia."*

**Dato extra / si preguntan (pico técnico):** por dentro, Python no ejecuta ese texto directamente: lo traduce a un formato intermedio llamado **bytecode**, que corre sobre una **máquina virtual** (CPython). Por eso "se ejecuta al instante" sin un paso de compilación visible. El precio de esa comodidad es velocidad — y por eso las librerías pesadas están escritas en C por dentro (lo vemos en el ecosistema).

**Transición:** *"Dije 'se ejecuta al instante'. Esa es una idea clave que vale la pena entender bien."*

---

## 5 · Una idea clave — «Interpretado, no compilado»

**En pantalla:** dos tarjetas — Compilado (C, Rust): "traducir el libro entero"; Interpretado (Python): "un intérprete simultáneo".

**Qué decir:**
- Usa la analogía tal cual, que es muy buena: *"Imaginen que tienen un libro en otro idioma. Un lenguaje **compilado** es como contratar a un traductor que traduce el libro entero antes de que puedan leer una sola página: hay una espera al inicio, pero después la lectura es rapidísima. Un lenguaje **interpretado** como Python es un **intérprete simultáneo**: traduce frase por frase a medida que avanzan. Empiezan de inmediato."*
- El *por qué importa*: *"Para construir un modelo estadístico uno prueba una idea, ve el resultado, la ajusta, prueba otra… decenas de veces. Con Python ese ciclo es instantáneo: escribes y corres. Esa agilidad para experimentar es justo lo que se necesita en ciencia de datos."*

**Dato extra / si preguntan:** el precio de esta comodidad es velocidad. Por eso el patrón de la ciencia de datos en Python es "lenguaje cómodo arriba, motor rápido abajo": tú escribes Python legible y las operaciones pesadas corren en C por debajo. Es el mismo patrón que veremos con las librerías.

**Transición:** *"¿Y de dónde salió este lenguaje? Su historia explica mucho de su personalidad."*

---

## 6 · Historia — «Un proyecto de Navidad que conquistó la IA»

**En pantalla:** línea de tiempo 1989 → 2020 y la nota "se llama por Monty Python, no por la serpiente".

**Qué decir:**
- *"Python lo empezó **Guido van Rossum** en 1989, en Ámsterdam, como un proyecto personal durante las vacaciones de Navidad — literalmente para no aburrirse."*
- *"El nombre no viene de la serpiente, sino del grupo de comedia británico **Monty Python**. Por eso mucha documentación tiene chistes escondidos."*
- Recorre la línea: 1991 primera versión pública; 2000 Python 2 y se populariza; 2008 Python 3, que mejoró el lenguaje **rompiendo compatibilidad** con la 2 (una decisión valiente y polémica); 2020 se apaga oficialmente Python 2 — hoy cuando alguien dice "Python" habla de Python 3.
- Remata con la tesis del slide: *"Su ventaja decisiva nunca fue la velocidad, sino ser **fácil de leer**. Y resultó que eso — que un científico pudiera escribir y entender el código sin ser ingeniero de software — fue exactamente lo que lo convirtió en el idioma de la ciencia de datos y la IA."*

**Dato extra / si preguntan:** a Guido se le conocía como el *"BDFL" (Benevolent Dictator For Life / dictador benévolo de por vida)* — tenía la última palabra en el diseño del lenguaje. En 2018 renunció a ese rol y hoy Python se gobierna por un comité (el *Steering Council*) y propuestas abiertas llamadas **PEP**.

**Transición:** *"Y hoy, aunque no lo veas, Python está por todos lados."*

---

## 7 · Usos reales — «Python está en lo que usas a diario»

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

## 8 · Datos y estadística — «Su fuerza es el ecosistema»

**En pantalla:** 4 librerías — pandas, NumPy, SciPy, matplotlib — y la frase "mi proyecto se construye sobre estas cuatro".

**Qué decir:**
- *"Python por sí solo es cómodo pero lento. Su verdadera fuerza son las **librerías**: colecciones de herramientas ya construidas que amplían lo que puede hacer. Y aquí está la clave: por dentro están escritas en C, un lenguaje rapidísimo. Tú escribes código simple y legible, y el trabajo numérico pesado corre por debajo a toda velocidad."*
- Presenta las cuatro con su rol en TU proyecto:
  - **pandas** → *"maneja tablas de datos gigantes como una hoja de cálculo programable. Aquí guardo el historial de partidos."*
  - **NumPy** → *"ejecuta millones de operaciones matemáticas de una sola vez, de forma vectorizada."*
  - **SciPy** → *"la más importante para mí: trae la **distribución de Poisson** y el **optimizador** que entrena mi modelo."*
  - **matplotlib** → *"convierte los números en gráficas y mapas de calor para poder leerlos."*
- Subraya: *"Estas cuatro no son teoría — son literalmente las piezas sobre las que está construido mi predictor."*

**Dato extra / si preguntan:** pandas lo creó Wes McKinney en 2008 para análisis financiero. "Vectorizado" (NumPy) quiere decir que aplica una operación a un arreglo entero de una sola vez, en vez de recorrerlo elemento por elemento — por eso es cientos de veces más rápido que un bucle en Python puro.

**Transición:** *"Con estas herramientas se hace ciencia de datos. Pero hay una idea todavía más grande encima: el machine learning."*

---

## 9 · Machine Learning — «Aprender reglas, no programarlas»

**En pantalla:** dos ecuaciones. Clásica: Reglas + Datos → Respuestas. ML: Datos + Respuestas → Reglas.

**Qué decir:**
- *"Esta es la idea más importante de toda la charla, y cabe en dos líneas."*
- *"En la **programación clásica**, yo escribo las reglas a mano: 'si pasa esto, haz aquello'. Le doy reglas y datos, y me devuelve respuestas."*
- *"El **machine learning** le da la vuelta: le doy **datos y respuestas** — muchos ejemplos del pasado — y la máquina **descubre las reglas sola**."*
- Analogía del slide, dila con calma: *"Es como aprende un niño qué es una manzana. No le lees una definición botánica. Le muestras muchas manzanas y su cerebro extrae el patrón solo. El machine learning hace exactamente eso, pero con datos."*
- Conecta con tu proyecto (importante): *"En mi caso, los 'ejemplos' son miles de partidos reales con su marcador. El modelo aprende de ahí qué tan fuerte ataca y defiende cada selección — yo nunca le digo 'Brasil es bueno'; lo deduce de los resultados."*

**Dato extra / si preguntan:** distinción útil: la programación clásica es determinista; el ML es estadístico, trabaja con probabilidades y con incertidumbre.

**Transición:** *"Y al igual que Python, el machine learning ya está en tu bolsillo."*

---

## 10 · ML en tu día a día

**En pantalla:** 4 tarjetas — recomendaciones, filtro de spam, desbloqueo facial, autocorrector — y por qué Python domina el campo.

**Qué decir:**
- Recorre rápido los ejemplos, todos cotidianos: *"El 'porque viste…' de Netflix o Spotify; el filtro de spam que aprende a separar lo relevante del correo no deseado; el desbloqueo facial de tu teléfono que aprende tu rostro; el autocorrector que predice la siguiente palabra. Todo eso es machine learning."*
- Cierra el arco Python + ML: *"¿Y por qué Python domina este campo? Porque cuando llegó el boom de la IA, el ecosistema numérico — NumPy, SciPy — **ya existía**. Encima se construyeron las grandes librerías de ML: scikit-learn, TensorFlow, PyTorch. Y como es fácil de leer, es ideal para investigar y probar ideas nuevas."*

**Dato extra / si preguntan:** frase útil — *"Python orquesta, la GPU ejecuta"*: en el deep learning, Python coordina y las operaciones pesadas corren en tarjetas gráficas por debajo. Otra vez el patrón "lenguaje cómodo arriba, motor rápido abajo".

**Transición:** *"Ahora que sabemos qué es, veamos que no todo el machine learning es igual: hay varias formas de aprender."*

---

## 11 · Tipos de aprendizaje — «Tres formas de aprender»

**En pantalla:** tres tarjetas — supervisado, no supervisado, por refuerzo — con "supervisado" resaltado como el tipo de tu modelo.

**Qué decir:**
- *"El machine learning se agrupa en tres grandes familias, según qué información recibe la máquina."*
- **Supervisado** → *"aprende de ejemplos que ya traen la respuesta correcta. Le muestras miles de correos etiquetados como 'spam' o 'no spam', o casas con su precio real, y aprende a predecir casos nuevos. Es el más común."*
- **No supervisado** → *"solo recibe datos, sin respuestas, y su tarea es encontrar estructura oculta: agrupar clientes que se parecen, detectar transacciones anómalas. Nadie le dijo cuáles son los grupos; los descubre."*
- **Por refuerzo** → *"aprende probando: actúa, recibe un premio o un castigo, y ajusta su estrategia. Así aprendió AlphaGo a ganar al Go, y así aprende un robot a caminar sin caerse."*
- Ancla tu proyecto: *"El mío es **aprendizaje supervisado**: mis 'ejemplos con respuesta' son partidos del pasado con su marcador. Por eso puede aprender a predecir partidos futuros."*

**Dato extra / si preguntan:** hay familias intermedias (semi-supervisado, auto-supervisado). Los LLM como ChatGPT se entrenan sobre todo de forma **auto-supervisada**: la 'respuesta' es la siguiente palabra del propio texto, así que no hace falta etiquetar a mano.

**Transición:** *"Sea cual sea el tipo, todo modelo enfrenta el mismo peligro: memorizar en vez de aprender."*

---

## 12 · Sobreajuste y generalización — «Memorizar no es aprender»

**En pantalla:** tres paneles — subajuste, buen ajuste, sobreajuste — con puntos y una curva.

**Qué decir:**
- *"Este es el reto central de todo el machine learning, y lo resume esta imagen."*
- Recorre los tres paneles: *"A la izquierda, **subajuste**: un modelo demasiado simple que ni siquiera captó la tendencia. En medio, **buen ajuste**: sigue el patrón general sin obsesionarse con cada punto. A la derecha, **sobreajuste**: un modelo tan complejo que pasa por todos y cada uno de los puntos del pasado."*
- El giro clave: *"El de la derecha parece el mejor — acierta el pasado perfecto. Pero es el peor: memorizó hasta el ruido, las casualidades. Y con datos nuevos, falla. Memorizar el pasado no es lo mismo que aprender."*
- Conecta con tu disciplina: *"La meta real es **generalizar**: acertar con lo que nunca vio. Por eso separo mis datos — entreno con unos partidos y evalúo con otros que el modelo no vio jamás — y le pongo un freno, la **regularización**, para que no se aferre a las casualidades."*

**Dato extra / si preguntan:** el sobreajuste es exactamente por lo que en el proyecto uso **regularización ridge** y una prueba honesta sin mirar el futuro (backtest point-in-time). Si dejara al modelo memorizar, en la prueba se vería perfecto y en el Mundial real fallaría.

**Transición:** *"Y con esto entendemos una última pregunta importante: ¿por qué no usé una red neuronal gigante como ChatGPT?"*

---

## 13 · Clásico vs. redes / LLMs — «Del modelo simple al LLM»

**En pantalla:** un espectro de "interpretable / pocos datos" a "caja negra / millones de datos", con marcadores: modelos clásicos (Poisson), redes neuronales, deep learning, LLMs (ChatGPT).

**Qué decir:**
- *"No todo el machine learning es una red neuronal. Hay un espectro completo."*
- Recórrelo de izquierda a derecha: *"A la izquierda, los **modelos clásicos** — como el mío, un Poisson, o una regresión, o los árboles de decisión: necesitan pocos datos y cada número que producen significa algo, se puede explicar. A la derecha, las **redes neuronales**, el **deep learning** y los **LLM como ChatGPT**: tienen una capacidad enorme, pero necesitan millones de ejemplos y son cajas negras — aciertan, pero no puedes explicar por qué."*
- La pregunta que todos se hacen (dila tú antes que ellos): *"¿Y por qué elegí Poisson y no una red neuronal, que suena más moderno? Por dos razones. Primero, los datos: tengo **miles** de partidos, no millones — y con pocos datos un modelo interpretable rinde igual o mejor y se sobreajusta menos. Segundo, y más importante: **puedo explicar cada número**. Sé por qué el modelo cree que un equipo va a ganar. Una red me daría el mismo pronóstico sin poder justificarlo."*

**Dato extra / si preguntan:** no es que las redes sean "mejores" o "peores" — sirven para problemas distintos. Con imágenes o lenguaje, donde hay millones de ejemplos y las reglas son imposibles de escribir a mano, las redes ganan sin discusión. Para predecir goles con datos tabulares y limitados, un modelo estadístico interpretable es la herramienta correcta.

**Transición:** *"Con esto ya tenemos las dos piezas: Python y machine learning. Veámoslas juntas en mi proyecto."*

---

## 14 · El proyecto — «Todo esto, en un solo repo»

**En pantalla:** una tabla que mapea cada concepto presentado (pandas/numpy, scipy, aprendizaje supervisado, generalización, ML interpretable, Streamlit) con el archivo del repositorio donde vive.

**Qué decir:**
- *"Construí un sistema que predice partidos del Mundial 2026 — el que se juega en Canadá, Estados Unidos y México — y que simula el torneo completo. Pero más que enumerar funciones, quiero mostrarles **dónde vive en el código todo lo que acabamos de ver**."*
- Recorre el mapa, conectando teoría con repo: *"Los datos y las características, con pandas y numpy, están en las carpetas de ingestión y features. La distribución de Poisson y el optimizador que entrena el modelo, con scipy, están en `poisson_model.py` y `train.py`. El aprendizaje supervisado del que hablamos es literalmente entrenar con miles de partidos reales. La generalización — no sobreajustar — es esa prueba honesta en `backtest_temporal.py`. Y la app que verán ahora está hecha con Streamlit."*
- Remata: *"Nada de esto es inventado: los datos son de fuentes abiertas —StatsBomb, FBref, resultados internacionales— y todo el pipeline es reproducible. Y ahora lo vemos funcionando."*

**Dato extra / si preguntan:** el Mundial 2026 es el primero con **48 selecciones** (antes 32), lo que cambia el formato de grupos y el cuadro; por eso el motor de torneo (`src/tournament/`) tuvo que programarse con la numeración nueva de la FIFA. El pipeline son scripts numerados `01_…` a `12_…` que se corren en orden; cada uno produce un archivo que el siguiente consume.

**Transición:** *"Antes de la demo, un vistazo de 30 segundos al corazón matemático del modelo."*

---

## 15 · El modelo — «Todo se reduce a estimar λ»

**En pantalla:** barras de Poisson para λ=1.8, la fórmula de log(λ), y la leyenda (α−β, host, elo·xg·valor).

**Qué decir:**
- Empieza por la intuición de Poisson: *"Los goles son **eventos raros y separados** en el tiempo — pasan pocos por partido y en momentos impredecibles. Hay una fórmula matemática hecha justo para contar eventos raros: la **distribución de Poisson**. Con un solo número, la **λ** (lambda), te dice la probabilidad de que haya 0 goles, 1, 2, 3…"*
- Señala las barras: *"Esto es Poisson para λ=1.8 goles esperados: lo más probable son 1 o 2 goles, y cada vez menos probable ir subiendo. Suena abstracto, pero es literalmente la forma de los goles en el fútbol real."*
- Ahora la fórmula, sin asustar a nadie (y recuerda que ya la vieron en el código): *"Todo el modelo se reduce a una pregunta: ¿cuál es la λ de cada equipo? Y eso lo calculo sumando factores — **α menos β**, el ataque de mi equipo menos la defensa del rival; la ventaja de **local**; y el ranking **Elo**, la calidad de las ocasiones (**xG**) y el **valor** de la plantilla. Esta es la misma suma que vimos en el código."*
- Remata con la joya del proyecto: *"Y lo mejor: es **interpretable**. Cada número significa algo real. Si ordeno los equipos por su α, obtengo un **ranking de verdad de las mejores delanteras del mundo**. No es una caja negra."*

**Dato extra / si preguntan:**
- La fórmula completa: `log(λ_i) = μ + α_i − β_j + γ·host + δ·elo_diff + ε·xg_diff + ζ·log(valor_i/valor_j)`. Se modela `log(λ)` y no `λ` directamente para que el resultado nunca sea negativo (no existen goles negativos).
- **Dixon-Coles:** Poisson simple subestima los empates bajos (0-0, 1-1). Dixon y Coles (1997) añadieron un factor de corrección τ que ajusta solo esos marcadores. Por eso el modelo es "Poisson bivariado + corrección Dixon-Coles".
- **Bivariado** = modela los goles de **ambos** equipos, no de uno solo.

**Transición:** *"Suficiente teoría. Veámoslo funcionando."*

---

## 16 · Demostración en vivo

**En pantalla:** "Elige dos equipos. Lee la predicción." + un mock de ARG vs BRA con mapa de calor de marcadores.

**Qué decir / hacer:**
- **Aquí cambias a la app real de Streamlit.** (Ver checklist de demo abajo.)
- Narra mientras operas: *"Elijo dos selecciones… y en un instante el modelo me da las probabilidades, los goles esperados de cada uno, y este **mapa de calor**: cada casilla es un marcador posible y el color es su probabilidad. La casilla más caliente es el resultado más probable."*
- Corrige la intuición común mientras muestras el 1X2: *"Ojo: el modelo **no dice** 'ganará Argentina'. Dice 'Argentina tiene 63% de probabilidad'. Si el partido se jugara 100 veces, ganaría unas 63 — pero 37 veces no. El favorito pierde a menudo, y eso es justo lo que hace emocionante al fútbol."*
- Si hay tiempo, muestra el torneo: *"Y aquí puedo simular el Mundial completo — los grupos se ordenan con los desempates oficiales de la FIFA y el cuadro avanza hasta la final."*
- Conecta con la teoría: *"Todo lo que ven en esta pantalla es la fórmula λ y la Poisson de hace un momento — solo que envuelto en algo que cualquiera puede usar sin saber matemáticas."*

**Dato extra / si preguntan:** Streamlit convierte un script de Python en una app web sin escribir nada de HTML ni JavaScript — por eso un proyecto de ciencia de datos puede volverse una app usable en pocas líneas.

**Transición:** *"Y con eso cerramos el círculo."*

---

## 17 · Cierre — «De una idea matemática a una app que funciona»

**En pantalla:** 3 conclusiones (un lenguaje para todo · aprender de los datos · estadística interpretable) + "¡Gracias! ¿Preguntas?".

**Qué decir:**
- Recapitula las tres ideas con las que quieres que se queden:
  1. *"**Un solo lenguaje para todo.** Python me llevó de los datos crudos hasta una app, sin cambiar de herramienta en el camino."*
  2. *"**Aprender de los datos.** El machine learning descubre las reglas a partir de ejemplos; no se las programa a mano."*
  3. *"**Estadística interpretable.** Cada número de mi modelo significa algo real. No es una caja negra: es matemática que se puede leer y explicar."*
- Cierre personal: *"Empezó como una idea matemática — contar goles con una fórmula del siglo XIX — y terminó como una app que predice el Mundial. Ese recorrido completo es lo que Python hace posible."*
- *"Gracias. ¿Preguntas?"*

---

## Checklist para la demo en vivo (slide 16)

- [ ] **Antes de empezar la charla**, deja la app ya corriendo en otra pestaña: `streamlit run src/ui/app.py`. No la arranques en vivo.
- [ ] Ten elegido de antemano un partido con buen contraste (p. ej. **ARG vs BRA**, o anfitrión vs. debutante) para que las probabilidades se vean interesantes.
- [ ] Ten un **plan B**: si la app falla, el slide 16 ya trae un mock con el mapa de calor. Puedes explicar sobre él sin drama.
- [ ] Zoom del navegador al 110–125% para que se lea desde el fondo del salón.
- [ ] Practica el recorrido una vez: elegir equipos → leer 1X2 → señalar goles esperados → señalar la casilla más caliente del mapa → (opcional) pestaña de torneo.

## Preguntas difíciles — respuestas de bolsillo

- **"¿Entonces vas a acertar quién gana el Mundial?"** → *"No, y ese no es el objetivo. Doy probabilidades, no certezas. El valor está en cuantificar la incertidumbre, no en eliminarla."*
- **"¿De verdad funciona? ¿Cómo lo sabes?"** → *"Lo probé prediciendo Mundiales pasados con datos que el modelo no había visto — una prueba honesta, 256 partidos. Se mide con el **Brier score**, donde menos es mejor: el azar puro saca 0.667 y mi modelo 0.593, claramente mejor que tirar una moneda. Y acierta el **marcador exacto un 14.5%** de las veces, que para fútbol es bastante."*
- **"El Elo solo saca 0.588, mejor que tu 0.593 en Brier…"** → *"Buena observación. En Brier están prácticamente empatados; pero en **log-loss** —una métrica que castiga más la sobre-confianza— mi modelo gana claro, 1.00 contra 1.28. Y además da mucho más que un 1X2: goles esperados, marcador probable y mercados, cosa que el Elo solo no hace."* Nunca escondas esto; reconocerlo te hace ver riguroso.
- **"¿Cómo evitas hacer trampa al probar con el pasado?"** → *"Con una prueba **point-in-time**: para cada partido solo uso el Elo y los datos que existían **antes** de jugarse. Si usara datos del futuro para 'predecir' el pasado, los números serían mentira. Esa disciplina es lo que hace creíble el backtest — y es la defensa contra el sobreajuste del que hablé."*
- **"¿Esto sirve para apostar?"** → *"El modelo estima probabilidades 'justas'; una casa de apuestas te gana por el margen que cobra. Es un ejercicio estadístico, no un esquema para hacer dinero."*
- **"¿Por qué Poisson y no una red neuronal / IA moderna?"** → *"Porque con los datos que hay (miles, no millones de partidos) un modelo interpretable rinde igual o mejor y, sobre todo, **puedo explicar cada número**. Una red neuronal sería una caja negra con más riesgo de sobreajuste."*
- **"¿De dónde sacas los datos?"** → *"Fuentes abiertas: StatsBomb, FBref, bases de resultados internacionales. Todo público y reproducible."*
- **"¿Y si un equipo cambió mucho (lesiones, nuevo técnico)?"** → *"El modelo usa forma reciente vía Elo y valor de plantilla actual, pero no lee noticias — esa es una limitación honesta y una línea de mejora futura."*

# 02 · Historia de Python

> **Idea en una frase:** Python nació en 1989 como un proyecto navideño de un solo
> programador holandés que quería un lenguaje **legible y agradable de usar**, y esa
> obsesión por la simplicidad lo convirtió, 30 años después, en el lenguaje número uno
> del mundo para ciencia de datos e inteligencia artificial.

Encaja perfecto en una clase de "Evolution of Computing": es un caso de estudio de cómo
las **decisiones de diseño** de un lenguaje determinan su destino.

---

## 1. El origen (1989–1991): un proyecto de Navidad

- A finales de **diciembre de 1989**, **Guido van Rossum**, un programador holandés del
  instituto de investigación **CWI** en Ámsterdam, empezó Python como un **proyecto
  personal para las vacaciones de Navidad**. Quería un lenguaje para "mantener la mente
  ocupada" y mejorar las carencias de un lenguaje anterior llamado **ABC**.
- **El nombre no viene de la serpiente.** Viene del grupo de comedia británico **"Monty
  Python's Flying Circus"**, del que Guido era fan. Quería un nombre "corto, único y un
  poco misterioso". (El logo de la serpiente vino mucho después, por marketing.)
- La **primera versión pública, Python 0.9.0**, se publicó en **febrero de 1991**. Ya
  incluía ideas modernas: funciones, manejo de excepciones y tipos de datos como listas y
  diccionarios.

**Historia para contar en clase:** que el lenguaje #1 en IA del mundo naciera como un
pasatiempo de Navidad es un gancho memorable. Refuerza la idea de que las buenas ideas de
diseño valen más que los recursos.

---

## 2. La filosofía: legibilidad ante todo

Desde el inicio, Guido tomó una decisión de diseño radical que define a Python: **el
código se lee muchas más veces de las que se escribe**, así que debe ser **legible**.

- **La indentación (sangría) es obligatoria y es parte de la sintaxis.** En la mayoría de
  lenguajes usas llaves `{ }` para delimitar bloques; en Python usas **espacios**. Esto
  obliga a que todo el código luzca ordenado.
  ```python
  if temperatura > 30:
      print("Hace calor")   # este bloque pertenece al if por la sangría
  ```
- Esta filosofía se cristalizó en el **"Zen of Python"** (PEP 20), escrito por Tim Peters:
  un poema de 19 aforismos que puedes ver escribiendo `import this` en cualquier Python.
  Los más citables:
  > - "Beautiful is better than ugly." (Lo bello es mejor que lo feo.)
  > - "Simple is better than complex." (Lo simple es mejor que lo complejo.)
  > - "Readability counts." (La legibilidad cuenta.)
  > - "There should be one—and preferably only one—obvious way to do it."

> **Tip de demo:** Abrir una terminal y escribir `import this` en vivo es un mini-truco
> que sorprende y refuerza el punto de la filosofía. (Está en el guion de la demo, 10.)

---

## 3. Las grandes eras: Python 2 vs Python 3

Este es el episodio más importante de la evolución del lenguaje, y un ejemplo clásico de
los **costes de romper la compatibilidad**.

- **Python 2.0 (2000):** trajo cosas hoy fundamentales, como el *garbage collector* de
  ciclos y las *list comprehensions*. Fue la versión que popularizó el lenguaje.
- **Python 3.0 (2008):** una revisión que **rompió la compatibilidad** con Python 2 a
  propósito, para arreglar inconsistencias de diseño acumuladas (por ejemplo, cómo se
  maneja el texto Unicode, o que `print` pasara de ser una instrucción a ser una función).
- **La "gran migración":** durante años convivieron ambas versiones y dividieron a la
  comunidad, porque el código de Python 2 no corría tal cual en Python 3. Fue un debate
  enorme sobre el precio de la mejora frente a la estabilidad.
- **Fin de Python 2:** el **1 de enero de 2020**, Python 2 dejó oficialmente de recibir
  soporte. Hoy, "Python" significa **Python 3**. *Tu proyecto usa Python 3.12.*

> **Lección para "Evolution of Computing":** Python 3 muestra la tensión eterna de la
> ingeniería de software: mejorar el diseño casi siempre exige romper cosas, y eso tiene
> un coste social y técnico enorme.

---

## 4. Gobernanza: del "dictador benévolo" a un consejo

- Durante décadas, Guido van Rossum fue el **BDFL** — *Benevolent Dictator For Life*
  (Dictador Benévolo Vitalicio): tenía la última palabra en las decisiones del lenguaje.
  El término es un cargo semi-en-broma pero real en el mundo del open source.
- En **2018**, tras el desgaste de un debate técnico, Guido **renunció** a ese rol. Desde
  entonces Python se gobierna mediante un **Steering Council** (consejo directivo) elegido
  por la comunidad. Es un ejemplo de cómo un proyecto madura de "un líder" a "una
  institución".
- Los cambios al lenguaje se proponen mediante documentos llamados **PEP** (*Python
  Enhancement Proposal*). El "Zen of Python" es el PEP 20; el estilo de código es el PEP 8.

---

## 5. Por qué explotó en ciencia de datos e IA (2010s–hoy)

La legibilidad y el ecosistema abierto crearon un círculo virtuoso:

1. Científicos e investigadores (que **no** son programadores profesionales) podían
   aprenderlo rápido.
2. Eso atrajo a que escribieran **librerías** para sus campos (NumPy 2006, pandas 2008,
   scikit-learn 2007, TensorFlow 2015, PyTorch 2016).
3. Esas librerías atrajeron a más usuarios, que escribieron más librerías.

Resultado: hoy Python es el idioma de facto de la **ciencia de datos, el machine learning
y la IA**. Es también, consistentemente, uno de los lenguajes **más populares del mundo**
en los rankings (TIOBE, Stack Overflow, GitHub Octoverse).

> Nota de trayectoria personal, por si sale en preguntas: Guido van Rossum trabajó luego
> en **Google** y **Dropbox**, y más recientemente en **Microsoft**, siempre cerca del
> desarrollo de Python.

---

## Línea de tiempo (ideal para una diapositiva)

| Año | Hito |
|---|---|
| 1989 (dic.) | Guido van Rossum empieza Python como proyecto de Navidad en el CWI (Ámsterdam). |
| 1991 (feb.) | Primera versión pública: **Python 0.9.0**. |
| 2000 | **Python 2.0** — se populariza. |
| 2001 | Se funda la **Python Software Foundation**. |
| 2008 | **Python 3.0** — mejora rompiendo compatibilidad con Python 2. |
| 2018 | Guido deja de ser **BDFL**; nace el Steering Council. |
| 2020 (ene.) | **Fin de soporte de Python 2**. "Python" = Python 3. |
| 2020s | Python, líder indiscutido en ciencia de datos e IA. Tu proyecto usa **Python 3.12**. |

---

## Frases-gancho para abrir o cerrar la sección
- "El lenguaje más importante de la IA moderna empezó como un pasatiempo navideño."
- "Se llama Python por Monty Python, no por la serpiente."
- "Su superpoder no fue la velocidad: fue ser fácil de leer."

## Micro-glosario de esta sección
- **BDFL:** *Benevolent Dictator For Life*, el rol histórico de Guido en Python.
- **PEP:** *Python Enhancement Proposal*, documento formal para proponer cambios.
- **Zen of Python:** los 19 principios de diseño (PEP 20); pruébalo con `import this`.
- **CWI:** instituto de investigación en Ámsterdam donde nació Python.

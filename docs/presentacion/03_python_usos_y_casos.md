# 03 · Usos comunes de Python y casos aplicados

> **Idea en una frase:** por ser de propósito general y tener un ecosistema gigantesco,
> Python está prácticamente en todas partes — desde la web que visitas hasta la nave
> espacial, pasando por la IA que usas a diario.

Esta sección te da **dominios + ejemplos reconocibles** para que la audiencia sienta que
Python no es abstracto: ya lo usan todos los días sin saberlo.

---

## 1. Ciencia de datos y análisis (el uso estrella)

**Qué se hace:** limpiar datos, analizarlos, visualizarlos y sacar conclusiones.
**Herramientas:** `pandas`, `NumPy`, `matplotlib`, `seaborn`, `Jupyter`.
**Por qué Python:** convierte tablas gigantes en respuestas con pocas líneas de código.

- **Casos reales:** casi todas las empresas basadas en datos (Netflix, Spotify, bancos)
  usan Python para analizar comportamiento de usuarios, detectar fraude y tomar
  decisiones.
- **Conexión con tu charla:** este es exactamente el terreno de tu proyecto (ver 04 y 06).

---

## 2. Machine Learning e Inteligencia Artificial (el que más crece)

**Qué se hace:** entrenar modelos que aprenden de datos: recomendaciones, reconocimiento
de imágenes, chatbots, coches autónomos.
**Herramientas:** `scikit-learn`, `TensorFlow`, `PyTorch`, `Keras`, `Hugging Face`.
**Por qué Python:** es el idioma común de toda la investigación y la industria de IA.

- **Casos reales:**
  - **ChatGPT y los grandes modelos de lenguaje** se entrenan y sirven mayormente con
    Python (PyTorch).
  - **Netflix / Spotify / YouTube:** sus sistemas de recomendación.
  - **Tesla:** parte de su pipeline de visión por computadora.
- Este dominio tiene su propio archivo dedicado: **05_python_machine_learning.md**.

---

## 3. Desarrollo web (backend)

**Qué se hace:** la lógica del servidor detrás de sitios y apps (bases de datos, cuentas,
APIs).
**Herramientas:** `Django`, `Flask`, `FastAPI`.
**Por qué Python:** desarrollo rápido y seguro.

- **Casos reales:** **Instagram** (uno de los mayores despliegues de Django del mundo),
  **Spotify**, **Pinterest**, **Reddit** (originalmente) y **Dropbox** usan Python en el
  backend.

---

## 4. Automatización y scripting ("las tareas aburridas")

**Qué se hace:** automatizar tareas repetitivas: renombrar miles de archivos, enviar
correos, rellenar formularios, mover datos entre sistemas (*web scraping*).
**Herramientas:** `os`, `requests`, `BeautifulSoup`, `Selenium`.
**Por qué Python:** es el "pegamento" (glue language) ideal: pocas líneas, resultado
inmediato.

- **Referencia cultural:** existe un libro famoso, *"Automate the Boring Stuff with
  Python"*, que resume este uso perfectamente.
- **Conexión con tu proyecto:** tus scripts `src/ingestion/01…12` son exactamente esto —
  automatizan la descarga y el parsing de datos de fútbol.

---

## 5. Cálculo científico e ingeniería

**Qué se hace:** simulaciones, física, química, bioinformática, astronomía.
**Herramientas:** `SciPy`, `NumPy`, `SymPy`, `Astropy`.

- **Caso real emblemático:** la **primera imagen de un agujero negro** (2019, proyecto
  Event Horizon Telescope) se procesó con un pipeline en gran parte en Python.
- **Caso real:** la NASA y muchos laboratorios usan Python para análisis científico.

---

## 6. Finanzas y economía (fintech, cuantitativo)

**Qué se hace:** modelos de riesgo, trading algorítmico, análisis cuantitativo.
**Herramientas:** `pandas` (¡creado originalmente en un fondo de inversión!), `NumPy`,
`statsmodels`.

- **Dato curioso:** `pandas` lo creó **Wes McKinney** mientras trabajaba en la gestora de
  inversión **AQR Capital**, precisamente para analizar datos financieros.

---

## 7. Educación y prototipado

- Python es hoy el **primer lenguaje** que se enseña en muchísimas universidades, porque
  su sintaxis limpia deja al alumno concentrarse en **resolver problemas**, no en pelear
  con la sintaxis. Este es, de hecho, el motivo por el que probablemente lo ves en tu
  clase.

---

## 8. Otros dominios (para redondear)

- **Videojuegos / gráficos:** `pygame` (prototipos, educación).
- **Internet de las cosas (IoT):** MicroPython corre en microcontroladores.
- **DevOps / infraestructura:** Ansible y muchas herramientas de nube están en Python.

---

## Tabla resumen (para una diapositiva)

| Dominio | Herramientas típicas | Caso reconocible |
|---|---|---|
| Ciencia de datos | pandas, NumPy, matplotlib | Netflix, bancos |
| Machine Learning / IA | scikit-learn, PyTorch, TensorFlow | ChatGPT, recomendaciones |
| Web backend | Django, Flask, FastAPI | Instagram, Spotify |
| Automatización | requests, BeautifulSoup, Selenium | Web scraping, bots |
| Cálculo científico | SciPy, NumPy, Astropy | Imagen del agujero negro |
| Finanzas | pandas, statsmodels | Trading cuantitativo |
| Educación | (el lenguaje mismo) | Primer lenguaje en la universidad |

---

## El punto que amarra todo (dilo así en clase)

> "Un solo lenguaje me deja **descargar** los datos (automatización), **analizarlos**
> (ciencia de datos), **construir un modelo que aprende** (machine learning) y
> **enseñarlo en una app** (web). Eso es exactamente lo que hace mi proyecto del Mundial,
> y por eso está escrito en Python de principio a fin."

Esta frase es el puente natural hacia la Parte C (tu proyecto).

## ¿La debilidad de Python? (para honestidad y posibles preguntas)
- **Velocidad de ejecución:** al ser interpretado, Python es **más lento** que C o Rust en
  cálculo puro. La solución del ecosistema científico: las librerías pesadas (NumPy,
  pandas) están escritas **por dentro en C/Fortran**, así que Python "orquesta" y el
  trabajo duro corre a velocidad de C. Tú escribes código simple y legible; la máquina
  hace los números rápido. (Esto conecta con el archivo 04.)

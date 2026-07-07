# 10 · Guion de la demostración en vivo

> Objetivo: que la clase **vea el modelo funcionando** — elegir dos selecciones y leer la
> predicción — en 3–4 minutos, con confianza y sin sustos. Incluye preparación, guion
> paso a paso, opción de mostrar código, y un **plan B** por si algo falla.

---

## 0. Antes de la clase (preparación — hazlo la noche anterior Y 10 min antes)

**La regla número uno de toda demo: tenla ya corriendo antes de empezar a hablar.**

### Checklist de preparación
- [ ] Entorno listo:
  ```bash
  cd /Users/milton/GitHub/1000BET
  python3 -m venv .venv          # si no existe
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- [ ] Verifica que los artefactos entrenados existen (la app los necesita):
  ```bash
  ls outputs/*.pkl               # debe listar match_predictor.pkl y poisson_model.pkl
  ```
- [ ] Lanza la app y confirma que abre:
  ```bash
  streamlit run src/ui/app.py
  ```
  Abre en el navegador (normalmente `http://localhost:8501`).
- [ ] **Prueba la predicción que vas a mostrar** (ej. ARG vs BRA) para no llevarte sorpresas.
- [ ] Sube el **zoom del navegador** (Cmd/Ctrl +) para que se lea desde el fondo del aula.
- [ ] **Captura de pantalla de respaldo** de la predicción, guardada como imagen (PLAN B).
- [ ] Silencia notificaciones, cierra pestañas y apps que distraigan.
- [ ] Ten dos terminales abiertas: una con la app corriendo, otra libre para comandos.

---

## 1. Guion paso a paso de la demo (3–4 min)

### Paso 1 — Presenta la app (20 s)
- Cambia de las diapositivas al navegador con la app ya abierta.
- **Di:** "Esto es una app web hecha en Python con **Streamlit**. En la barra lateral hay
  cuatro páginas: predecir un partido, el torneo completo, la fiabilidad del modelo y el
  estado del modelo. Empecemos prediciendo un partido."

### Paso 2 — Predice un partido con "gancho" (60–90 s)
- En la página **🔮 Predecir partido**, elige dos selecciones potentes y conocidas
  (sugerencia: **Argentina vs Brasil**, o **España vs Francia**).
- **Mientras cargas, di:** "Elijo dos equipos y el modelo, en milisegundos, calcula las
  probabilidades a partir de todo lo que aprendió de miles de partidos históricos."
- **Lee los resultados en voz alta y conéctalos con la teoría:**
  - Las **probabilidades 1X2**: "63% Argentina, 22% empate, 15% Brasil, por ejemplo. Fíjense
    que **no** dice quién gana: da **probabilidades**. Así piensa un buen modelo."
  - Los **goles esperados (λ)**: "Aquí están los lambda de los que hablé: los goles
    esperados de cada equipo. Todo el modelo se reduce a estimar bien estos dos números."
  - El **marcador más probable** y el **top-3**.
  - El **mapa de calor de marcadores** (si lo muestras): "Cada celda es la probabilidad de
    un marcador exacto; la más caliente es la más probable. Esto sale de la distribución de
    Poisson más la corrección Dixon-Coles."

### Paso 3 — (Opcional) Muestra los mercados extra / props (30 s)
- Señala córners, tarjetas, tiros, faltas over/under.
- **Di:** "Lo bonito es que es el **mismo motor** matemático reutilizado cinco veces: goles,
  córners, tarjetas, tiros y faltas. Programé el modelo una vez y respondo cinco preguntas."

### Paso 4 — Muestra el torneo (30–45 s)
- Ve a la página **🏆 Torneo**.
- **Di:** "El sistema no solo predice un partido: simula el Mundial completo. Arma las tablas
  de grupos con los **desempates oficiales de la FIFA** y avanza el cuadro eliminatorio a
  medida que se registran resultados reales." (Muestra el bracket visual.)

### Paso 5 — (Opcional, muy recomendable) Muestra la fiabilidad (30 s)
- Ve a la página **📊 Fiabilidad del modelo**.
- **Di:** "Y aquí está la parte honesta: métricas que miden qué tan buenas son las
  probabilidades del modelo comparadas con la realidad. No basta con que sea bonito: tiene
  que estar **bien calibrado**."

---

## 2. (Opcional avanzado) Mostrar el código — solo si tu audiencia lo pide

Si el profesor o la clase quieren "ver el código", ten estos dos archivos abiertos en el
editor y muestra **una sola cosa** de cada uno (no scrollees sin rumbo):

1. **`src/model/poisson_model.py`** — muestra la fórmula del λ en `_lambda` (líneas ~200) y
   di: "Aquí está la ecuación de la que hablé, tal cual, en Python: `mu + alpha − beta +
   gamma·host + …`."
2. **`src/model/poisson_model.py` → `fit`** — muestra la línea `minimize(neg_ll, theta0,
   method="L-BFGS-B", …)` y di: "Y aquí, literalmente, es donde el modelo **aprende**: una
   llamada al optimizador de SciPy que ajusta los parámetros minimizando el error."

> No intentes explicar el archivo entero. Un vistazo a la fórmula y a `minimize()` es
> suficiente para demostrar que "esto es real y lo entiendo".

### (Opcional) El truco del "Zen of Python"
Si quieres un momento ligero que refuerza la Sección de historia, en una terminal:
```bash
python -c "import this"
```
- **Di:** "Esta es la filosofía de Python, escrita dentro del propio lenguaje: 'lo simple es
  mejor que lo complejo', 'la legibilidad cuenta'. Eso resume por qué conquistó la ciencia."

---

## 3. Plan B — si algo falla (mantén la calma)

| Si falla… | Haz esto |
|---|---|
| La app no arranca / error al lanzar | Muestra la **captura de respaldo** de la predicción y explícala igual. Nadie notará la diferencia. |
| No hay internet / entorno roto | Igual: captura de respaldo. Por eso la preparaste. |
| Una selección no aparece | Elige otra: usa dos de las grandes (ARG, BRA, ESP, FRA, DEU, POR) que seguro están. |
| Se ve muy pequeño | Cmd/Ctrl + para ampliar el navegador (ensáyalo antes). |
| Te preguntan algo que no sabes | "Buena pregunta, lo verifico y te respondo" — y usa el archivo 11. |

> **Mentalidad:** una demo con captura de respaldo bien explicada es 100% exitosa. Lo que
> se recuerda es tu claridad, no si el servidor arrancó.

---

## 4. Comandos de referencia rápida (chuleta)

```bash
# Activar entorno
source .venv/bin/activate

# Lanzar la app (LA DEMO)
streamlit run src/ui/app.py

# (Opcional) correr los tests en vivo para mostrar rigor
pytest -q

# (Opcional) mostrar la filosofía de Python
python -c "import this"

# (Opcional, NO en vivo — tarda minutos) re-entrenar el modelo
python src/model/train.py

# (Opcional) el backtest honesto que respalda el slide 14
python -m src.evaluation.backtest_temporal
```

> ⚠️ **No corras `train.py` ni el backtest en vivo:** tardan minutos. Si quieres mostrar sus
> resultados, córrelos **antes** y lleva una captura de la salida.

---

## 5. Guion de cierre de la demo (para volver a las diapositivas)
> "Y eso es todo: elegí dos equipos y, detrás de esa pantalla tan simple, hay un modelo
> estadístico entrenado con miles de partidos, todo escrito en Python. Volvamos para
> cerrar."

→ Regresa al **Slide 16 (Conclusiones)**.

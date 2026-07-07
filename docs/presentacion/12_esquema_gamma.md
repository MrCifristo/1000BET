# 12 · Esquema para pegar en Gamma AI (10 módulos)

> **Instrucciones de uso:**
> 1. En Gamma → "Pegar texto" → tipo **Presentación**.
> 2. Marca la opción **"Genera a partir de notas o un esquema"** (NO "Resume").
> 3. Copia TODO el bloque de abajo (10 diapositivas, separadas por `---`) y pégalo.
> 4. En el siguiente paso: idioma **Español**, **10 tarjetas**, tono **educativo**, audiencia **estudiantes**.
> 5. NO subas los archivos `.md`; solo pega este esquema.
>
> Nota: las **notas del orador** de cada slide están en `09_guion_diapositivas.md` y
> `10_guion_demo_en_vivo.md`. Gamma no las genera; llévalas aparte para ensayar.

Mapa de fusiones (18 → 10): portada+gancho / Python ficha (con interpretado) / historia /
usos+estadística / ML qué es + por qué domina / proyecto qué hace + por qué Python /
modelo cómo funciona / cómo aprende + prueba honesta / demo / conclusiones+gracias.

---
--- ⬇️ COPIA DESDE AQUÍ ⬇️ ---

Python y la predicción del Mundial 2026
- ¿Se puede predecir un partido de fútbol? No con certeza, pero sí con probabilidades
- La herramienta: Python, el lenguaje que domina la ciencia de datos y la IA
- De la teoría a un modelo estadístico real, con demostración en vivo al final
- Milton Beltrán — clase "Evolution of Computing"

---

¿Qué es Python? Ficha técnica
- Propósito general: sirve para casi todo (web, datos, IA, automatización)
- Alto nivel: hablas "humano", no el idioma de la máquina
- Interpretado: se ejecuta al momento, no se compila a un .exe (usa un bytecode intermedio)
- Tipado dinámico pero fuerte: no declaras tipos, pero no los mezcla a escondidas
- Multiparadigma: estructurado + orientado a objetos + funcional
- Memoria automática y multiplataforma

---

Historia de Python
- 1989: Guido van Rossum lo empieza como un proyecto de Navidad en Ámsterdam
- El nombre viene de "Monty Python", no de la serpiente
- 1991: primera versión pública. 2008: Python 3. 2020: fin de Python 2
- Su superpoder no fue la velocidad, sino ser fácil de leer
- Esa legibilidad lo convirtió en el lenguaje #1 de ciencia de datos e IA

---

Python en los datos y la estadística
- Usado por todos: Netflix, Instagram, ChatGPT, bancos; hasta la 1ª imagen de un agujero negro
- Su fuerza son sus librerías (escritas por dentro en C, así que son rápidas)
- pandas: tablas de datos gigantes (como Excel programable)
- NumPy: números rápidos y vectorizados
- SciPy: estadística y optimización de verdad (distribuciones, optimizadores)
- Mi proyecto está construido sobre exactamente estas librerías

---

Machine Learning: qué es y por qué Python
- Programación clásica: yo escribo las reglas. Machine Learning: la máquina las descubre de los datos
- Analogía: un niño aprende qué es una manzana viendo muchas, no leyendo una definición
- Python domina el ML: el ecosistema ya existía (scikit-learn, TensorFlow, PyTorch)
- "Python orquesta, la GPU ejecuta": código simple, cálculo ultrarrápido
- Ganó por ser el más fácil de investigar, no el más rápido

---

Mi proyecto: predictor del Mundial 2026
- Elige dos selecciones y calcula probabilidades de victoria, empate y derrota
- Estima los goles esperados y el marcador más probable; simula el torneo completo
- Modelo: Poisson bivariado + corrección Dixon-Coles + componente Elo
- Todo en Python, en una app web interactiva (Streamlit)
- ¿Por qué Python? Un solo lenguaje para descargar, limpiar, entrenar, evaluar y publicar

---

Cómo funciona el modelo
- Los goles son eventos raros: eso lo describe la distribución de Poisson
- Todo se reduce a estimar "lambda": los goles esperados de cada equipo
- Fórmula: log(λ) = base + ataque − defensa_rival + local + Elo + xG + valor_plantilla
- Cada parámetro significa algo real: ordenar por "ataque" da un ranking de delanteras
- Dixon-Coles añade un ajuste fino para los empates apretados (0-0, 1-1)

---

Cómo aprende y se entrena
- Aprender = ajustar los parámetros hasta explicar bien miles de partidos reales
- Un optimizador (L-BFGS-B de SciPy) baja el error "cuesta abajo" hasta el mínimo
- Regularización para que no memorice rarezas; validación cruzada para elegir lo mejor
- La prueba honesta: predecir Mundiales pasados con datos que no había visto
- Le tiene que ganar al azar y a métodos simples. No es una caja negra: es interpretable

---

Demostración en vivo
- Elegir dos selecciones y leer la predicción al instante
- Probabilidades 1X2, goles esperados y mapa de calor de marcadores
- Los mismos modelos predicen córners, tarjetas, tiros y faltas
- El motor del torneo y el cuadro eliminatorio que avanza con resultados reales

---

Conclusiones
- Python permite todo el recorrido de datos en un solo lenguaje
- El Machine Learning es aprender reglas a partir de los datos, no programarlas
- Mi proyecto es estadística interpretable de punta a punta
- De una idea matemática a una app funcional, sin cambiar de herramienta
- ¡Gracias! ¿Preguntas?

--- ⬆️ COPIA HASTA AQUÍ ⬆️ ---

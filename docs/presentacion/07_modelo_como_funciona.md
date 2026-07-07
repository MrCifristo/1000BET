# 07 · Cómo funciona el modelo (de la intuición a la fórmula)

> **Idea en una frase:** el modelo estima **cuántos goles se espera que marque cada
> equipo** (un número llamado λ, "lambda") a partir de la fuerza de ataque y defensa de los
> equipos y algunas ventajas contextuales; y con esos λ y la **distribución de Poisson**
> calcula la probabilidad de cada marcador posible, y de ahí las probabilidades de
> victoria, empate y derrota.

Esta sección desglosa el corazón matemático **término por término**. Va de intuición a
fórmula, para una audiencia mixta. El código vive en `src/model/poisson_model.py`.

---

## 1. La pieza base: la distribución de Poisson

**El problema:** ¿cómo modelas los goles de un equipo en un partido?

**La observación clave:** los goles son **eventos raros** que ocurren a lo largo de 90
minutos. La rama de la probabilidad que describe "cuántas veces ocurre un evento raro en un
intervalo de tiempo" es la **distribución de Poisson**.

**Intuición:** si sabes que un equipo marca **en promedio** 1.8 goles por partido (ese
promedio se llama **λ, lambda**), la Poisson te dice qué tan probable es que marque
exactamente 0, 1, 2, 3… goles en un partido concreto.

- λ = 1.8 → lo más probable es 1 o 2 goles, pero a veces 0, y de vez en cuando 4.
- **Todo el trabajo del modelo se reduce a estimar bien el λ de cada equipo en cada
  partido.** Con un buen λ, la Poisson hace el resto.

En tu código: `from scipy.stats import poisson` y `poisson.pmf(g, lam)` = probabilidad de
marcar exactamente `g` goles cuando esperas `lam`.

---

## 2. "Bivariado": dos equipos a la vez

Un partido tiene **dos** equipos marcando. El modelo estima **dos lambdas**:
- **λ_A** = goles esperados del equipo A.
- **λ_B** = goles esperados del equipo B.

La probabilidad de un marcador concreto (digamos 2-1) es, en primera aproximación, la
probabilidad de que A marque 2 **por** la de que B marque 1:

```
P(marcador a-b) = poisson.pmf(a, λ_A) × poisson.pmf(b, λ_B)
```

En tu código esto es una **matriz de marcadores** construida con `np.outer(...)`: una
tabla de (0-0, 1-0, 0-1, 1-1, 2-0, …) con la probabilidad de cada uno. De esa matriz sale
todo lo demás.

---

## 3. El corazón: ¿cómo se calcula λ? (la fórmula)

Aquí está la ecuación central de tu modelo. Para un partido del equipo *i* atacando contra
el equipo *j*:

```
log(λ_i) = μ + α_i − β_j + γ·host_i + δ·elo_diff + ε·xg_diff + ζ·log_value_ratio
```

Se calcula en **escala logarítmica** (por eso el `log`) para garantizar que λ nunca sea
negativo (un número de goles negativo no tiene sentido); al final se aplica `exp(...)` para
volver a goles. Desglose **término por término**:

| Término | Nombre | Qué significa (intuición) |
|---|---|---|
| **μ** (mu) | Intercepto | El nivel base de goles de un partido "promedio". |
| **α_i** (alpha) | **Fuerza de ataque** del equipo *i* | Cuánto marca *i* por encima/debajo del promedio. Brasil tiene α alto. |
| **−β_j** (beta) | **Fuerza defensiva** del rival *j* | Una buena defensa (β alto) **resta** goles al atacante. |
| **γ·host_i** (gamma) | Ventaja de local | Si *i* es anfitrión del Mundial, un empujón extra. |
| **δ·elo_diff** (delta) | Diferencia de **Elo** | Qué tan mejor/peor es *i* según su ranking histórico. |
| **ε·xg_diff** (eps) | Diferencia de **xG** | Diferencia en calidad de ocasiones generadas (goles esperados). |
| **ζ·log_value_ratio** (zeta) | Diferencia de **valor de plantilla** | Qué tan más cara/talentosa es la plantilla de *i* vs *j*. |

**Cómo explicarlo en una frase:**
> "Los goles esperados de un equipo suben con su fuerza de ataque, su ventaja de local, su
> superioridad en el ranking Elo, en calidad de ocasiones (xG) y en valor de plantilla; y
> bajan con lo buena que sea la defensa rival."

- **α (ataque) y β (defensa)** son los parámetros que hacen el peso: hay **uno por
  selección**, y son los que el modelo **aprende** de los datos.
- **μ, γ, δ, ε, ζ** son coeficientes globales, también aprendidos.
- Las **features** (host, elo_diff, xg_diff, log_value_ratio) se construyen en
  `src/model/features.py` para cada partido (ver archivo 04 y 08).

> **Punto de venta (interpretabilidad):** a diferencia de una red neuronal, aquí **cada
> número tiene nombre y significado**. Puedes ordenar los equipos por su α y obtienes,
> literalmente, un ranking de las mejores delanteras del mundo. Tu `train.py` de hecho
> imprime el "Top 10 por parámetro de ataque (α)".

---

## 4. La corrección Dixon-Coles (el detalle fino)

**El problema:** el modelo Poisson simple **subestima** ciertos marcadores bajos y
frecuentes, sobre todo los empates 0-0 y 1-1. En el fútbol real, los marcadores cerrados
ocurren un poco más de lo que predice la Poisson pura (los equipos ajustan su juego).

**La solución (Maher 1982 / Dixon-Coles 1997):** aplicar un **factor de ajuste τ (tau)**
solo a los cuatro marcadores bajos: **{0-0, 1-0, 0-1, 1-1}**. Un único parámetro extra,
**ρ (rho)**, gobierna cuánto se corrigen esas celdas.

En tu código (`_tau` y `predict_score_matrix`):
```
τ(0,0) = 1 − λ_A·λ_B·ρ
τ(1,0) = 1 + λ_B·ρ
τ(0,1) = 1 + λ_A·ρ
τ(1,1) = 1 − ρ
```
Luego se re-normaliza la matriz para que todas las probabilidades vuelvan a sumar 1.

**Cómo explicarlo:** "La Poisson pura es un poco ingenua con los empates apretados. La
corrección Dixon-Coles añade un solo parámetro, ρ, que reajusta finamente esos cuatro
marcadores para que el modelo pegue mejor con la realidad del fútbol."

---

## 5. El componente Elo (el ranking dinámico)

**Qué es Elo:** el mismo sistema de rating del ajedrez, adaptado al fútbol (World Football
Elo). Cada selección tiene una **puntuación**; ganar a un rival fuerte suma muchos puntos,
perder contra uno débil resta muchos. Es una medida **dinámica** de la fuerza actual.

**Cómo entra en tu modelo:** como la feature `elo_diff` (la diferencia de Elo entre los dos
equipos, dividida por 100), multiplicada por el coeficiente δ. Así, dos equipos con
historial y plantilla parecidos se diferencian por su **forma reciente** capturada en el
Elo.

**Detalle importante (honestidad):** para no "hacer trampa", en el backtesting usas el
**Elo point-in-time** (`elo_home_pre` / `elo_away_pre`): el Elo que cada equipo tenía
**justo antes** del partido, no el de hoy. Esto evita el *look-ahead* (mirar el futuro).
Se explica en el archivo 08.

---

## 6. De los λ a la predicción final (lo que ve el usuario)

Una vez calculada la matriz de marcadores (con Poisson + Dixon-Coles), sacar todo lo demás
es sumar celdas de esa tabla (en tu código, `predict_match`):

- **P(gana A)** = suma del triángulo inferior de la matriz (A marca más que B) → `np.tril`.
- **P(empate)** = suma de la diagonal (mismos goles) → `np.trace`.
- **P(gana B)** = suma del triángulo superior → `np.triu`.
- **Marcador más probable (`likely_score`)** = la celda con mayor probabilidad (argmax).
- **Top-3 de marcadores** = las 3 celdas más altas.
- **Marcador coherente (`coherent_score`)** = el marcador más probable **restringido** al
  resultado 1X2 más probable. *Ejemplo:* si lo más probable es el empate, muestra el empate
  más probable (p. ej. 1-1) en vez de un 2-1 que contradiría el mensaje.

> **Detalle de calidad que puedes presumir:** el `coherent_score` resuelve una incoherencia
> real: a veces el resultado 1X2 más probable es "empate" pero el marcador entero más
> probable es una victoria. Mostrar ambos confundiría al usuario, así que fuerzas que el
> marcador mostrado concuerde con el 1X2 modal.

---

## 7. Los mercados extra (props): el mismo motor, reutilizado

`match_predictor.py` envuelve **cinco** modelos Poisson idénticos en estructura, uno por
mercado: **goles, córners, tarjetas, tiros y faltas**. Para cada uno calcula un **total
esperado** (λ_A + λ_B) y las probabilidades **over/under** de las líneas típicas de
apuestas (p. ej. más/menos de 2.5 goles) con la Poisson. También el **BTTS** ("ambos
equipos marcan"). Es una demostración elegante de **reutilización**: el mismo modelo
matemático sirve para cinco preguntas distintas.

---

## Diagrama mental (para una diapositiva)

```
  Features del partido (Elo, xG, valor, local)
        │
        ▼
  Fórmula:  log(λ) = μ + α − β + γ·host + δ·elo + ε·xg + ζ·valor
        │
        ▼
  λ_A , λ_B  (goles esperados de cada equipo)
        │  Poisson  → matriz de marcadores
        │  + Dixon-Coles (ajuste marcadores bajos, parámetro ρ)
        ▼
  Matriz de probabilidades de todos los marcadores
        │  sumar celdas
        ▼
  P(A) · P(empate) · P(B) · marcador probable · top-3 · props
```

---

## Cómo presentar esta sección (guion de ~60–90 s)
> "El modelo se basa en una idea simple: los goles son eventos raros, y eso lo describe la
> **distribución de Poisson**. Todo se reduce a estimar bien cuántos goles esperar de cada
> equipo, un número que llamo **lambda**. Y lambda sale de esta fórmula: sube con el ataque
> del equipo, su ventaja de local, su ranking Elo, su calidad de ocasiones y el valor de su
> plantilla; y baja con la defensa del rival. Lo bonito es que **cada parámetro significa
> algo**: si ordeno los equipos por su parámetro de ataque, obtengo un ranking real de las
> mejores delanteras. Le añado un ajuste fino (Dixon-Coles) para los empates apretados, y
> con eso calculo la probabilidad de cada marcador posible."

→ Falta lo esencial: ¿cómo **aprende** esos parámetros? Eso es **08_entrenamiento_como_aprende.md**.

## Micro-glosario de esta sección
- **λ (lambda):** goles esperados (promedio) de un equipo en un partido.
- **Poisson:** distribución de probabilidad para conteos de eventos raros.
- **α / β:** parámetros de ataque / defensa, uno por selección.
- **Dixon-Coles / ρ:** corrección (y su parámetro) para marcadores bajos.
- **Elo:** puntuación dinámica de fuerza de cada selección.
- **xG (goles esperados):** medida de la calidad de las ocasiones generadas.
- **argmax:** la posición del valor máximo (aquí, el marcador más probable).

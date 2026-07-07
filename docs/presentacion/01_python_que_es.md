# 01 · ¿Qué es Python? — Ficha técnica del lenguaje

> **Idea en una frase:** Python es un lenguaje de programación **de alto nivel,
> interpretado, de propósito general y multiparadigma**, diseñado para que el código
> sea fácil de leer y escribir por humanos.

Esta sección responde, término por término, a "¿qué tipo de lenguaje es Python?".
Cada concepto va con una **intuición/analogía** primero y luego el detalle técnico,
para que puedas explicarlo a una audiencia mixta.

---

## 1. Lenguaje de programación de "propósito general"

**Intuición:** un lenguaje de propósito general es como un **cuchillo suizo**: no está
hecho para una sola tarea. Con Python puedes hacer una página web, analizar datos,
entrenar una IA, automatizar tareas aburridas o controlar un robot.

Se contrapone a los lenguajes de *dominio específico* (DSL), como SQL (solo bases de
datos) o HTML (solo estructurar páginas), que hacen una cosa muy bien y nada más.

---

## 2. De alto nivel (vs bajo nivel)

**Intuición:** "nivel" mide **qué tan cerca estás de la máquina**. Un lenguaje de bajo
nivel te hace hablar el idioma del procesador (registros, direcciones de memoria). Uno
de alto nivel te deja hablar en algo mucho más parecido al idioma humano.

- **Bajo nivel** (ej. Assembly, C): tú gestionas la memoria, los punteros, los detalles
  del hardware. Máximo control y velocidad, pero mucho esfuerzo y muchos errores.
- **Alto nivel** (Python): escribes `total = sum(precios)` y el lenguaje se encarga de
  todo lo de abajo. Priorizas **expresar la idea**, no pelear con la máquina.

**Ejemplo comparativo — sumar dos números e imprimirlos:**

En C tienes que declarar tipos, gestionar el `main`, incluir librerías:
```c
#include <stdio.h>
int main() {
    int a = 3, b = 4;
    printf("%d\n", a + b);
    return 0;
}
```

En Python es literalmente:
```python
print(3 + 4)
```

Python es de **muy alto nivel**: te abstrae incluso de la gestión de memoria.

---

## 3. Interpretado (vs compilado)

**Intuición:** un lenguaje **compilado** es como **traducir un libro completo** al
idioma de la máquina antes de publicarlo (compilas una vez, luego se ejecuta muy rápido).
Un lenguaje **interpretado** es como un **intérprete simultáneo** que traduce frase por
frase mientras hablas: más flexible e inmediato, pero con algo de sobrecoste en velocidad.

- **Compilado** (C, C++, Rust, Go): un *compilador* convierte todo tu código a código
  máquina (un ejecutable) **antes** de correrlo. Rápido en ejecución, pero hay un paso
  de compilación y el binario depende de la plataforma.
- **Interpretado** (Python): un programa llamado **intérprete** lee y ejecuta tu código
  **directamente**, línea a línea, en el momento. No hay paso previo visible: escribes y
  corres.

**Matiz importante que te hará quedar bien:** Python en realidad hace un paso intermedio.
Cuando ejecutas un `.py`, el intérprete de referencia (**CPython**) primero lo **compila
a *bytecode*** (un código intermedio, los archivos `.pyc`) y luego una **máquina virtual
de Python (PVM)** ejecuta ese bytecode. Así que la frase precisa es: *"Python se compila a
bytecode y ese bytecode se interpreta"*. No es un binario nativo como en C.

> **Frase para la diapositiva:** "Python es interpretado: no lo compilas a un `.exe`, lo
> ejecutas al momento. Por dentro pasa por un bytecode intermedio que ejecuta una máquina
> virtual."

---

## 4. Tipado: dinámico y fuerte

Aquí hay **dos ejes distintos** que la gente suele confundir. Explícalos por separado.

### 4.a. Dinámico vs estático (¿*cuándo* se revisan los tipos?)

**Intuición:** ¿tienes que decir de antemano de qué "tipo" es cada caja (número, texto,
lista), o el lenguaje lo averigua solo mientras corre?

- **Tipado estático** (C, Java): declaras el tipo por adelantado (`int edad = 30;`) y se
  verifica **al compilar**. Más ceremonia, pero atrapa errores antes.
- **Tipado dinámico** (Python): no declaras tipos; la variable **toma el tipo del valor**
  que le asignas, y se verifica **en tiempo de ejecución**.

```python
x = 30        # x es un entero (int)
x = "hola"    # ahora x es un texto (str) — perfectamente válido en Python
```

> Python soporta *type hints* opcionales (`edad: int = 30`) que se usan como
> documentación y para herramientas, pero **no cambian** que el lenguaje es dinámico.

### 4.b. Fuerte vs débil (¿*cuánto* respeta los tipos?)

**Intuición:** ¿el lenguaje te deja mezclar peras con manzanas a escondidas?

- **Tipado fuerte** (Python): **no** mezcla tipos sin permiso. `"3" + 5` da **error**,
  porque uno es texto y otro número. Te obliga a ser explícito.
- **Tipado débil** (ej. JavaScript): `"3" + 5` da `"35"` porque convierte a la callada.

```python
"3" + 5      # ❌ TypeError: can only concatenate str to str
"3" + str(5) # ✅ "35"  — conversión explícita
3 + 5        # ✅ 8
```

> **Resumen para la diapositiva:** Python es **dinámicamente tipado** (no declaras tipos)
> pero **fuertemente tipado** (no mezcla tipos incompatibles a escondidas).

---

## 5. Multiparadigma (incluye programación estructurada)

Tu profesor probablemente pregunta específicamente por "estructurado". Aquí va claro:

Un **paradigma** es un estilo/filosofía de organizar el código. Python es
**multiparadigma**: soporta varios y puedes mezclarlos.

- **Programación estructurada / imperativa:** el código es una **secuencia de pasos** con
  estructuras de control ordenadas: secuencia, condicionales (`if`) y bucles (`for`,
  `while`), evitando saltos caóticos (`goto`). Python es plenamente estructurado.
  ```python
  total = 0
  for precio in [10, 20, 30]:   # bucle
      if precio > 15:           # condicional
          total += precio
  ```
- **Programación orientada a objetos (POO):** organizas el código en **objetos** que
  agrupan datos y comportamiento (clases). *Tu proyecto usa esto:* `class PoissonModel`.
  ```python
  class Perro:
      def __init__(self, nombre):
          self.nombre = nombre
      def ladrar(self):
          return f"{self.nombre} dice guau"
  ```
- **Programación funcional:** tratas las funciones como valores, usas `map`, `filter`,
  `lambda`, funciones puras. Python lo soporta parcialmente.

> **Frase para la diapositiva:** "Python es estructurado **y** orientado a objetos **y**
> algo funcional: tú eliges el estilo según el problema."

---

## 6. Gestión automática de memoria (garbage collection)

**Intuición:** en C tú "pides" y "devuelves" memoria a mano (y si olvidas devolverla,
tienes una *fuga de memoria*). En Python hay un **recolector de basura (garbage
collector)** que limpia automáticamente lo que ya no se usa. Menos control, muchísimos
menos errores.

---

## 7. Multiplataforma y de código abierto

- **Multiplataforma:** el mismo `.py` corre en Windows, macOS y Linux sin cambios,
  porque lo que cambia es el intérprete, no tu código.
- **Open source:** Python es libre y gratuito, mantenido por la **Python Software
  Foundation** y una comunidad enorme. Esto explica por qué existe una librería para casi
  todo (el "ecosistema", ver archivos 04 y 05).

---

## Tabla resumen (ideal para una diapositiva única)

| Característica | Python | Analogía / contraste |
|---|---|---|
| Propósito | General | Cuchillo suizo (vs SQL = destornillador) |
| Nivel | Alto (muy alto) | Hablas "humano", no "máquina" (vs C) |
| Ejecución | Interpretado (bytecode + PVM) | Intérprete simultáneo (vs C = traducir el libro entero) |
| Tipado (cuándo) | Dinámico | La caja toma el tipo del contenido |
| Tipado (cuánto) | Fuerte | No mezcla peras con manzanas (vs JS) |
| Paradigmas | Multi: estructurado + POO + funcional | Eliges el estilo |
| Memoria | Automática (garbage collector) | No limpias a mano (vs C) |
| Portabilidad | Multiplataforma, open source | Mismo código en todos lados |

---

## Puntos de conexión con el resto de la charla

- El hecho de ser **de alto nivel y legible** es lo que lo hizo perfecto para científicos
  que no son programadores profesionales → lleva a los archivos **04 (estadística)** y
  **05 (ML)**.
- El ser **interpretado + tipado dinámico** lo hace ideal para **prototipar rápido**, que
  es exactamente cómo se explora un modelo estadístico como el tuyo → archivo **06**.

## Micro-glosario de esta sección
- **Intérprete:** programa que ejecuta tu código directamente.
- **Bytecode:** código intermedio (ni tu texto ni código máquina) que ejecuta la PVM.
- **CPython:** la implementación estándar de Python, escrita en C.
- **Type hints:** anotaciones de tipo opcionales, para documentación y herramientas.
- **Garbage collector:** el "recolector de basura" que libera memoria no usada.

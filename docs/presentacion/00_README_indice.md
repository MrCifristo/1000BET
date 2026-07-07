# Presentación — "Evolution of Computing": Python y el predictor del Mundial 2026

Este es el **banco de información** para tu presentación. Está segmentado por temas para
que puedas profundizar en cada uno, preparar tus diapositivas y ensayar el guion.

## Cómo usar esta carpeta

- Lee primero los archivos de la **Parte A** (Python en general) para dominar el "qué es".
- La **Parte B** es el corazón conceptual: por qué Python domina el machine learning.
- La **Parte C** conecta todo con **tu proyecto** (aquí está el material para explicar tu código).
- La **Parte D** es lo operativo: guion de diapositivas, guion de la demo en vivo y banco de preguntas.

## Índice de archivos

### Parte A — Python (lo general)
| Archivo | Contenido |
|---|---|
| `01_python_que_es.md` | Qué es Python y su "ficha técnica": interpretado, alto nivel, tipado, paradigmas, memoria. |
| `02_python_historia.md` | Historia: Guido van Rossum, 1989–hoy, Python 2 vs 3, el "Zen of Python", línea de tiempo. |
| `03_python_usos_y_casos.md` | Usos comunes y casos reales por dominio, con ejemplos de empresas reconocibles. |
| `04_python_estadistica.md` | Por qué Python es clave en estadística: NumPy, pandas, SciPy, statsmodels, matplotlib. |

### Parte B — Machine Learning (el deep dive)
| Archivo | Contenido |
|---|---|
| `05_python_machine_learning.md` | Qué es ML, tipos, por qué Python domina, ecosistema, y el puente hacia tu modelo. |

### Parte C — Tu proyecto
| Archivo | Contenido |
|---|---|
| `06_proyecto_vision_general.md` | Qué hace tu sistema, por qué Python, arquitectura completa. |
| `07_modelo_como_funciona.md` | El modelo: Poisson bivariado, Dixon-Coles, Elo, covariables, la fórmula desglosada. |
| `08_entrenamiento_como_aprende.md` | Cómo aprende/se entrena: verosimilitud, L-BFGS-B, ridge, LOTO-CV, backtesting, updater. |

### Parte D — Presentación y demo
| Archivo | Contenido |
|---|---|
| `09_guion_diapositivas.md` | Guion slide-por-slide con notas del orador y tiempos. |
| `10_guion_demo_en_vivo.md` | Paso a paso de la demostración: comandos, qué mostrar, qué código abrir, plan B. |
| `11_glosario_y_preguntas.md` | Glosario de términos + banco de preguntas probables con respuestas. |

## Arco narrativo sugerido (≈ 15–20 min)

1. **Gancho** (1 min): "Voy a predecir partidos del Mundial con matemáticas y Python."
2. **Python: qué es y de dónde viene** (4 min): ficha técnica + historia.
3. **Por qué Python conquistó la ciencia y el ML** (4 min): estadística → machine learning.
4. **Mi proyecto** (5 min): qué hace, cómo funciona el modelo, cómo aprende.
5. **Demo en vivo** (3–4 min): la UI de Streamlit prediciendo un partido real.
6. **Cierre + preguntas** (1–2 min).

> Nota de precisión: todo lo que dice sobre tu código en las Partes C y D fue escrito
> leyendo tus archivos reales (`poisson_model.py`, `train.py`, `match_predictor.py`,
> `validation.py`, `features.py`, `updater.py`, `backtest_temporal.py`, `metrics.py`).

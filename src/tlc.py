"""
tlc.py
------
Demostración por simulación del Teorema del Límite Central (TLC).

Idea (la misma de la guía del profesor en Excel):
    1. Se toman muestras de tamaño n de una distribución cualquiera.
    2. A cada muestra se le calcula su media  X̄ = (X1 + ... + Xn) / n.
    3. Se repite muchas veces y se estudian TODAS esas medias.

El TLC predice que esas medias:
    (1) se centran en μ,
    (2) tienen desviación estándar σ / √n,
    (3) forman una campana normal cuando n es grande
        (su asimetría baja como γ / √n),
aunque la distribución original NO sea normal.
"""

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy import stats


@dataclass
class Distribucion:
    nombre: str
    descripcion: str
    formula: str                       # fórmula en LaTeX para mostrar en la app
    parametros: dict                   # parámetros por defecto
    generar: Callable                  # (rng, parametros, tamaño) -> números aleatorios
    media: Callable                    # parametros -> μ teórica
    desviacion: Callable               # parametros -> σ teórica
    asimetria: Callable                # parametros -> coeficiente de asimetría γ de X
    discreta: bool


# ---------------------------------------------------------------------------
# Catálogo de distribuciones vistas en el curso
# ---------------------------------------------------------------------------
DISTRIBUCIONES: dict[str, Distribucion] = {
    "Poisson": Distribucion(
        nombre="Poisson",
        descripcion="Número de eventos en un intervalo (llegadas, fallas, defectos). "
                    "Es la que usa la guía del profesor con λ = 4.",
        formula=r"P(X=k)=\dfrac{e^{-\lambda}\lambda^{k}}{k!},\qquad \mu=\lambda,\quad \sigma=\sqrt{\lambda}",
        parametros={"lambda": 4.0},
        generar=lambda rng, p, size: rng.poisson(p["lambda"], size),
        media=lambda p: p["lambda"],
        desviacion=lambda p: np.sqrt(p["lambda"]),
        asimetria=lambda p: 1 / np.sqrt(p["lambda"]),
        discreta=True,
    ),
    "Binomial": Distribucion(
        nombre="Binomial",
        descripcion="Número de éxitos en m ensayos independientes con probabilidad p.",
        formula=r"P(X=k)=\binom{m}{k}p^{k}(1-p)^{m-k},\qquad \mu=mp,\quad \sigma=\sqrt{mp(1-p)}",
        parametros={"m": 10, "p": 0.2},
        generar=lambda rng, p, size: rng.binomial(int(p["m"]), p["p"], size),
        media=lambda p: p["m"] * p["p"],
        desviacion=lambda p: np.sqrt(p["m"] * p["p"] * (1 - p["p"])),
        asimetria=lambda p: (1 - 2 * p["p"]) / np.sqrt(p["m"] * p["p"] * (1 - p["p"])),
        discreta=True,
    ),
    "Geométrica": Distribucion(
        nombre="Geométrica",
        descripcion="Número de ensayos hasta obtener el primer éxito. Muy asimétrica.",
        formula=r"P(X=k)=(1-p)^{k-1}p,\qquad \mu=\dfrac{1}{p},\quad \sigma=\dfrac{\sqrt{1-p}}{p}",
        parametros={"p": 0.25},
        generar=lambda rng, p, size: rng.geometric(p["p"], size),
        media=lambda p: 1 / p["p"],
        desviacion=lambda p: np.sqrt(1 - p["p"]) / p["p"],
        asimetria=lambda p: (2 - p["p"]) / np.sqrt(1 - p["p"]),
        discreta=True,
    ),
    "Dado (uniforme discreta)": Distribucion(
        nombre="Dado (uniforme discreta)",
        descripcion="Lanzar un dado: cada cara del 1 al 6 tiene la misma probabilidad. "
                    "Su gráfica es plana, nada parecida a una campana.",
        formula=r"P(X=k)=\dfrac{1}{6},\ k=1,\dots,6,\qquad \mu=3.5,\quad \sigma=\sqrt{\tfrac{35}{12}}\approx1.708",
        parametros={},
        generar=lambda rng, p, size: rng.integers(1, 7, size),
        media=lambda p: 3.5,
        desviacion=lambda p: np.sqrt(35 / 12),
        asimetria=lambda p: 0.0,
        discreta=True,
    ),
    "Uniforme continua": Distribucion(
        nombre="Uniforme continua",
        descripcion="Cualquier valor entre a y b es igual de probable (como ALEATORIO() de Excel).",
        formula=r"f(x)=\dfrac{1}{b-a},\ a\le x\le b,\qquad \mu=\dfrac{a+b}{2},\quad \sigma=\dfrac{b-a}{\sqrt{12}}",
        parametros={"a": 0.0, "b": 10.0},
        generar=lambda rng, p, size: rng.uniform(p["a"], p["b"], size),
        media=lambda p: (p["a"] + p["b"]) / 2,
        desviacion=lambda p: (p["b"] - p["a"]) / np.sqrt(12),
        asimetria=lambda p: 0.0,
        discreta=False,
    ),
    "Exponencial": Distribucion(
        nombre="Exponencial",
        descripcion="Tiempo entre eventos (tiempo de respuesta de un servidor, vida de un componente). "
                    "Es muy asimétrica (cola larga a la derecha): una prueba difícil para el TLC.",
        formula=r"f(x)=\dfrac{1}{\beta}e^{-x/\beta},\ x\ge0,\qquad \mu=\beta,\quad \sigma=\beta",
        parametros={"beta": 2.0},
        generar=lambda rng, p, size: rng.exponential(p["beta"], size),
        media=lambda p: p["beta"],
        desviacion=lambda p: p["beta"],
        asimetria=lambda p: 2.0,
        discreta=False,
    ),
}


# ---------------------------------------------------------------------------
# Simulación
# ---------------------------------------------------------------------------
def simular_medias(dist: Distribucion, parametros: dict, n: int,
                   repeticiones: int = 200, semilla: int | None = None):
    """
    Equivale a la hoja de Excel de la guía:
        - 'muestras' es la tabla A2:E201 (cada FILA es una muestra de tamaño n)
        - 'medias'   es la columna F  (=PROMEDIO(A2:E2) en cada fila)
    """
    rng = np.random.default_rng(semilla)
    muestras = dist.generar(rng, parametros, (repeticiones, n))
    medias = muestras.mean(axis=1)
    return muestras, medias


def resumen(medias: np.ndarray, dist: Distribucion, parametros: dict, n: int) -> dict:
    """Compara lo que se observó en la simulación con lo que predice el TLC."""
    mu = dist.media(parametros)
    sigma = dist.desviacion(parametros)
    sigma_xbarra = sigma / np.sqrt(n)

    media_obs = float(np.mean(medias))
    desv_obs = float(np.std(medias, ddof=1))          # ddof=1 -> igual a DESVEST de Excel

    # Regla empírica de la normal: si las medias son normales, deben quedar
    # ~68.27 % dentro de μ ± 1σ_X̄  y  ~95.45 % dentro de μ ± 2σ_X̄
    dentro_1 = float(np.mean(np.abs(medias - mu) <= sigma_xbarra) * 100)
    dentro_2 = float(np.mean(np.abs(medias - mu) <= 2 * sigma_xbarra) * 100)

    return {
        "mu": mu,
        "sigma": sigma,
        "sigma_xbarra": sigma_xbarra,
        "media_obs": media_obs,
        "desv_obs": desv_obs,
        "error_media_pct": abs(media_obs - mu) / mu * 100,
        "error_desv_pct": abs(desv_obs - sigma_xbarra) / sigma_xbarra * 100,
        "asimetria": float(stats.skew(medias)),
        "asimetria_teorica": dist.asimetria(parametros) / np.sqrt(n),   # γ / √n
        "dentro_1sigma_pct": dentro_1,
        "dentro_2sigma_pct": dentro_2,
    }


def tabla_varios_n(dist: Distribucion, parametros: dict, valores_n=(1, 2, 5, 10, 30, 50),
                   repeticiones: int = 200, semilla: int = 2026):
    """Repite la simulación para varios tamaños de muestra (para ver la tendencia)."""
    filas = []
    for n in valores_n:
        _, medias = simular_medias(dist, parametros, n, repeticiones, semilla + n)
        r = resumen(medias, dist, parametros, n)
        filas.append({"n": n, **r})
    return filas
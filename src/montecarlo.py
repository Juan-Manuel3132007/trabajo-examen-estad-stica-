"""
montecarlo.py
-------------
Simulación de Monte Carlo del costo de una operación de Ingeniería,
siguiendo la guía del profesor:

        Costo = Variable incierta × Costo unitario        (en la guía: Demanda × Costo unitario)

Cada iteración:
    1. U  = número aleatorio uniforme entre 0 y 1         -> =ALEATORIO()
    2. X  = F⁻¹(U)   (transformada inversa)               -> =INV.NORM(U; μ; σ) si F es normal
    3. C  = X × c                                          -> =G2*C2
Se repite N veces y se analizan media, desviación y percentiles.

La variable incierta puede modelarse con cuatro distribuciones. Todas se construyen
con la MISMA media μ y la MISMA desviación σ de los datos, de modo que lo único que
cambia entre ellas es la FORMA (simétrica, sesgada, plana o en pico).
"""

import numpy as np
import pandas as pd
from scipy import stats

DISTRIBUCIONES_MC = ["Normal (como la guía)", "Lognormal", "Uniforme", "Triangular"]


# ---------------------------------------------------------------------------
# 1. Parámetros estimados a partir de los datos
# ---------------------------------------------------------------------------
def estimar_parametros(tabla: pd.DataFrame, col_variable: str = "Demanda",
                       col_costo: str | None = "CostoUnitario") -> dict:
    """
    Estima μ y σ de la variable incierta y, si existe, del costo unitario.
    Con los datos de la guía equivale a:
        =PROMEDIO(B2:B41)   =DESVEST.M(B2:B41)   =PROMEDIO(C2:C41)   =COEF.DE.CORREL(B2:B41;C2:C41)
    """
    if col_costo:
        pares = tabla[[col_variable, col_costo]].dropna()
        d, c = pares[col_variable].to_numpy(float), pares[col_costo].to_numpy(float)
    else:
        d, c = tabla[col_variable].dropna().to_numpy(float), None

    resultado = {
        "n_datos": len(d),
        "media_demanda": float(d.mean()),
        "desv_demanda": float(d.std(ddof=1)),
        "minimo": float(d.min()),
        "maximo": float(d.max()),
        "son_enteros": bool(np.all(np.isclose(d, np.round(d)))),
        "p_shapiro_demanda": float(stats.shapiro(d).pvalue) if 3 <= len(d) <= 5000 else float("nan"),
        "media_costo_unit": None, "desv_costo_unit": None, "correlacion": None,
        "media_costo_hist": None, "desv_costo_hist": None,
    }
    if c is not None and len(c) >= 3:
        resultado.update({
            "media_costo_unit": float(c.mean()),
            "desv_costo_unit": float(c.std(ddof=1)),
            "media_costo_hist": float((d * c).mean()),
            "desv_costo_hist": float((d * c).std(ddof=1)),
        })
        # La correlación solo existe si ninguna de las dos columnas es constante
        if np.std(d) > 0 and np.std(c) > 0:
            resultado["correlacion"] = float(np.corrcoef(d, c)[0, 1])
    return resultado


# ---------------------------------------------------------------------------
# 2. Distribuciones para la variable incierta (todas con la misma μ y σ)
# ---------------------------------------------------------------------------
def construir_distribucion(nombre: str, mu: float, sigma: float):
    """
    Devuelve (distribución de SciPy, explicación en LaTeX).

    Normal      : N(μ, σ)                                    simétrica, colas infinitas
    Lognormal   : ln X ~ N(m, s),  s² = ln(1 + σ²/μ²),
                  m = ln μ − s²/2                            sesgada a la derecha, siempre > 0
    Uniforme    : U(μ − √3σ,  μ + √3σ)                       todos los valores igual de probables
    Triangular  : T(a = μ − √6σ,  moda = μ,  b = μ + √6σ)    acotada, con pico en la media
    """
    if nombre.startswith("Normal"):
        return (stats.norm(loc=mu, scale=sigma),
                rf"X\sim N(\mu,\sigma)=N({mu:.2f},\ {sigma:.2f})")
    if nombre == "Lognormal":
        if mu <= 0:
            raise ValueError("La lognormal necesita una media positiva.")
        s2 = np.log(1 + sigma ** 2 / mu ** 2)
        m = np.log(mu) - s2 / 2
        return (stats.lognorm(s=np.sqrt(s2), scale=np.exp(m)),
                rf"\ln X\sim N(m,s),\quad s=\sqrt{{\ln\!\left(1+\tfrac{{\sigma^2}}{{\mu^2}}\right)}}={np.sqrt(s2):.4f},"
                rf"\quad m=\ln\mu-\tfrac{{s^2}}{{2}}={m:.4f}")
    if nombre == "Uniforme":
        a, b = mu - np.sqrt(3) * sigma, mu + np.sqrt(3) * sigma
        return (stats.uniform(loc=a, scale=b - a),
                rf"X\sim U(\mu-\sqrt3\,\sigma,\ \mu+\sqrt3\,\sigma)=U({a:.2f},\ {b:.2f})")
    if nombre == "Triangular":
        a, b = mu - np.sqrt(6) * sigma, mu + np.sqrt(6) * sigma
        return (stats.triang(c=0.5, loc=a, scale=b - a),
                rf"X\sim T(a=\mu-\sqrt6\,\sigma,\ \text{{moda}}=\mu,\ b=\mu+\sqrt6\,\sigma)=T({a:.2f},\ {mu:.2f},\ {b:.2f})")
    raise ValueError(f"Distribución desconocida: {nombre}")


def simular_costo(dist, costo_unit: float, iteraciones: int, semilla: int | None = None,
                  redondear: bool = True) -> pd.DataFrame:
    """Monte Carlo general: X = F⁻¹(U) con cualquier distribución, y C = X · c."""
    rng = np.random.default_rng(semilla)
    U = rng.random(iteraciones)                       # ALEATORIO()
    x = dist.ppf(U)                                   # transformada inversa F⁻¹(U)
    if redondear:
        x = np.round(x)                               # REDONDEAR(...;0)
    return pd.DataFrame({"Iteracion": np.arange(1, iteraciones + 1),
                         "Aleatorio": U, "Variable": x, "Costo": x * costo_unit})


def teoricos_distribucion(dist, costo_unit: float) -> dict:
    """Valores exactos del costo C = c·X: media, desviación y percentiles."""
    return {"media": float(costo_unit * dist.mean()),
            "desv": float(costo_unit * dist.std()),
            "p5": float(costo_unit * dist.ppf(0.05)),
            "p50": float(costo_unit * dist.ppf(0.50)),
            "p95": float(costo_unit * dist.ppf(0.95))}


def curva_costo(dist, costo_unit: float, puntos: int = 400) -> tuple[np.ndarray, np.ndarray]:
    """Densidad teórica del costo: si C = c·X entonces f_C(x) = f_X(x/c) / c."""
    lo, hi = dist.ppf(0.0005), dist.ppf(0.9995)
    x = np.linspace(lo, hi, puntos) * costo_unit
    return x, dist.pdf(x / costo_unit) / costo_unit


# ---------------------------------------------------------------------------
# 3. Una iteración explicada paso a paso (para la pestaña didáctica)
# ---------------------------------------------------------------------------
def una_iteracion(U: float, mu: float, sigma: float, costo_unit: float, dist=None,
                  redondear: bool = True) -> dict:
    z = stats.norm.ppf(U)                         # valor z que deja un área U a la izquierda
    demanda = mu + z * sigma if dist is None else float(dist.ppf(U))   # INV.NORM(U; μ; σ) en la normal
    demanda_red = round(demanda) if redondear else demanda
    costo = demanda_red * costo_unit
    return {"U": U, "z": z, "demanda": demanda, "demanda_red": demanda_red, "costo": costo}


# ---------------------------------------------------------------------------
# 4. Modelo de la guía (demanda normal, costo unitario fijo = promedio)
# ---------------------------------------------------------------------------
def simular_modelo_guia(mu: float, sigma: float, costo_unit: float, iteraciones: int,
                        semilla: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    U = rng.random(iteraciones)                                   # ALEATORIO()
    demanda = np.round(stats.norm.ppf(U, loc=mu, scale=sigma))    # REDONDEAR(INV.NORM(...);0)
    costo = demanda * costo_unit
    return pd.DataFrame({"Iteracion": np.arange(1, iteraciones + 1),
                         "Aleatorio": U, "Demanda": demanda, "Costo": costo})


# ---------------------------------------------------------------------------
# 5. Modelo mejorado: variable y costo unitario CORRELACIONADOS
#    (la guía, sección 11, recomienda no asumir independencia)
# ---------------------------------------------------------------------------
def simular_modelo_correlacionado(mu_d: float, s_d: float, mu_c: float, s_c: float,
                                  rho: float, iteraciones: int,
                                  semilla: int | None = None, redondear: bool = True) -> pd.DataFrame:
    """
    Se generan dos normales estándar independientes Z1 y Z2 y se combinan así:
        D = μ_D + σ_D · Z1
        c = μ_c + σ_c · ( ρ·Z1 + √(1-ρ²)·Z2 )
    Así D y c quedan con correlación exactamente ρ.
    """
    rng = np.random.default_rng(semilla)
    z1 = rng.standard_normal(iteraciones)
    z2 = rng.standard_normal(iteraciones)
    demanda = mu_d + s_d * z1
    if redondear:
        demanda = np.round(demanda)
    costo_unit = mu_c + s_c * (rho * z1 + np.sqrt(1 - rho ** 2) * z2)
    costo = demanda * costo_unit
    return pd.DataFrame({"Iteracion": np.arange(1, iteraciones + 1),
                         "Demanda": demanda, "CostoUnitario": costo_unit, "Costo": costo})


# ---------------------------------------------------------------------------
# 6. Réplica EXACTA de la fórmula que trae el Excel (columna G)
#    =REDONDEAR(MIN(B2; MAX(80; REDONDEAR(INV.NORM(F2;μ;σ);0)));0)
#    El MIN(B2; ...) impide que la demanda simulada supere la demanda histórica
#    de esa misma fila  ->  sesgo hacia abajo.
# ---------------------------------------------------------------------------
def simular_formula_excel(tabla: pd.DataFrame, mu: float, sigma: float,
                          recalculos: int = 10_000, semilla: int | None = None) -> np.ndarray:
    """Devuelve el promedio de la columna G en cada recálculo (cada F9)."""
    rng = np.random.default_rng(semilla)
    B = tabla["Demanda"].to_numpy()
    U = rng.random((recalculos, len(B)))
    inv = np.round(stats.norm.ppf(U, mu, sigma))
    G = np.minimum(B, np.maximum(80, inv))
    return G.mean(axis=1)


# ---------------------------------------------------------------------------
# 7. Análisis de resultados
# ---------------------------------------------------------------------------
def resumen_resultados(costos: np.ndarray) -> dict:
    p5, p50, p95 = np.percentile(costos, [5, 50, 95])
    return {
        "media": float(np.mean(costos)),
        "desv": float(np.std(costos, ddof=1)),
        "minimo": float(np.min(costos)),
        "maximo": float(np.max(costos)),
        "p5": float(p5), "p50": float(p50), "p95": float(p95),
    }


def resultados_teoricos(mu: float, sigma: float, costo_unit: float) -> dict:
    """Modelo de la guía: C = D·c con c constante y D normal  ->  C ~ N(μ·c, σ·c)."""
    return teoricos_distribucion(stats.norm(mu, sigma), costo_unit)


def convergencia(costos: np.ndarray) -> pd.DataFrame:
    """
    Promedio acumulado después de k iteraciones y su banda de error ±1.96·s/√k.
    Por el TLC el promedio de k simulaciones es aprox. normal con desviación s/√k.
    """
    k = np.arange(1, len(costos) + 1)
    promedio = np.cumsum(costos) / k
    s = np.std(costos, ddof=1)
    return pd.DataFrame({"k": k, "promedio": promedio,
                         "inferior": promedio - 1.96 * s / np.sqrt(k),
                         "superior": promedio + 1.96 * s / np.sqrt(k)})


def sensibilidad_costo_unitario(mu: float, sigma: float, costos_unit, iteraciones: int = 10_000,
                                semilla: int = 2026, dist=None, redondear: bool = True) -> pd.DataFrame:
    """Ejercicio (e) de la guía: cambiar el costo unitario y ver cómo cambia el resultado."""
    dist = dist if dist is not None else stats.norm(mu, sigma)
    filas = []
    for c in costos_unit:
        sim = simular_costo(dist, c, iteraciones, semilla, redondear)
        r = resumen_resultados(sim["Costo"].to_numpy())
        filas.append({"CostoUnitario": c, **r})
    return pd.DataFrame(filas)
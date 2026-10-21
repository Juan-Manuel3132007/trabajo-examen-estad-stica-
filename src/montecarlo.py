"""
montecarlo.py
-------------
Simulación de Monte Carlo del costo de una operación de Ingeniería,
siguiendo la guía del profesor:

        Costo = Demanda × Costo unitario

La demanda es incierta y se modela como Normal(μ, σ) usando los 40 datos.
Cada iteración:
    1. U  = número aleatorio uniforme entre 0 y 1         -> =ALEATORIO()
    2. D  = F⁻¹(U; μ, σ)   (transformada inversa)         -> =INV.NORM(U; μ; σ)
    3. C  = D × c                                          -> =G2*C2
Se repite N veces y se analizan media, desviación y percentiles.
"""

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# 1. Parámetros estimados a partir de los 40 datos
# ---------------------------------------------------------------------------
def estimar_parametros(tabla: pd.DataFrame) -> dict:
    d = tabla["Demanda"].to_numpy()
    c = tabla["CostoUnitario"].to_numpy()
    return {
        "n_datos": len(d),
        "media_demanda": float(d.mean()),                 # =PROMEDIO(B2:B41)
        "desv_demanda": float(d.std(ddof=1)),             # =DESVEST.M(B2:B41)
        "media_costo_unit": float(c.mean()),              # =PROMEDIO(C2:C41)
        "desv_costo_unit": float(c.std(ddof=1)),
        "correlacion": float(np.corrcoef(d, c)[0, 1]),    # =COEF.DE.CORREL(B2:B41;C2:C41)
        "p_shapiro_demanda": float(stats.shapiro(d).pvalue),
        "media_costo_hist": float((d * c).mean()),
        "desv_costo_hist": float((d * c).std(ddof=1)),
    }


# ---------------------------------------------------------------------------
# 2. Una iteración explicada paso a paso (para la pestaña didáctica)
# ---------------------------------------------------------------------------
def una_iteracion(U: float, mu: float, sigma: float, costo_unit: float) -> dict:
    z = stats.norm.ppf(U)                         # valor z que deja un área U a la izquierda
    demanda = mu + z * sigma                      # es lo mismo que INV.NORM(U; μ; σ)
    demanda_red = round(demanda)                  # =REDONDEAR(...;0)
    costo = demanda_red * costo_unit
    return {"U": U, "z": z, "demanda": demanda, "demanda_red": demanda_red, "costo": costo}


# ---------------------------------------------------------------------------
# 3. Modelo de la guía (demanda normal, costo unitario fijo = promedio)
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
# 4. Modelo mejorado: demanda y costo unitario CORRELACIONADOS
#    (la guía, sección 11, recomienda no asumir independencia)
# ---------------------------------------------------------------------------
def simular_modelo_correlacionado(mu_d: float, s_d: float, mu_c: float, s_c: float,
                                  rho: float, iteraciones: int,
                                  semilla: int | None = None) -> pd.DataFrame:
    """
    Se generan dos normales estándar independientes Z1 y Z2 y se combinan así:
        D = μ_D + σ_D · Z1
        c = μ_c + σ_c · ( ρ·Z1 + √(1-ρ²)·Z2 )
    Así D y c quedan con correlación exactamente ρ.
    """
    rng = np.random.default_rng(semilla)
    z1 = rng.standard_normal(iteraciones)
    z2 = rng.standard_normal(iteraciones)
    demanda = np.round(mu_d + s_d * z1)
    costo_unit = mu_c + s_c * (rho * z1 + np.sqrt(1 - rho ** 2) * z2)
    costo = demanda * costo_unit
    return pd.DataFrame({"Iteracion": np.arange(1, iteraciones + 1),
                         "Demanda": demanda, "CostoUnitario": costo_unit, "Costo": costo})


# ---------------------------------------------------------------------------
# 5. Réplica EXACTA de la fórmula que trae el Excel (columna G)
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
# 6. Análisis de resultados
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
    """Como C = D·c con c constante y D normal, C también es normal: N(μ·c, σ·c)."""
    mu_c, s_c = mu * costo_unit, sigma * costo_unit
    return {"media": mu_c, "desv": s_c,
            "p5": mu_c + stats.norm.ppf(0.05) * s_c,
            "p50": mu_c,
            "p95": mu_c + stats.norm.ppf(0.95) * s_c}


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
                                semilla: int = 2026) -> pd.DataFrame:
    """Ejercicio (e) de la guía: cambiar el costo unitario y ver cómo cambia el resultado."""
    filas = []
    for c in costos_unit:
        sim = simular_modelo_guia(mu, sigma, c, iteraciones, semilla)
        r = resumen_resultados(sim["Costo"].to_numpy())
        filas.append({"CostoUnitario": c, **r})
    return pd.DataFrame(filas)
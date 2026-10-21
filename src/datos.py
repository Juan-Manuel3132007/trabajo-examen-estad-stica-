"""
datos.py
--------
Carga los 40 datos hipotéticos de la guía "Simulación de Montecarlo"
(Prof. Horacio Fernández C.).

Primero intenta leer el archivo Excel original del profesor que está en la
carpeta data/. Si no lo encuentra, usa una copia de los mismos 40 datos
escrita en este archivo, para que la aplicación funcione siempre.
"""

from pathlib import Path

import pandas as pd

RUTA_EXCEL = Path(__file__).resolve().parent.parent / "data" / "Simulacion_Montecarlo_40_datos.xlsx"

# Copia exacta de las columnas B, C y D de la hoja "Datos y Simulación"
_DEMANDA = [120, 135, 128, 150, 142, 160, 155, 138, 170, 148,
            132, 158, 145, 175, 162, 130, 152, 168, 140, 180,
            125, 147, 159, 172, 136, 154, 165, 143, 178, 150,
            134, 161, 149, 173, 157, 129, 166, 141, 176, 153]

_COSTO_UNITARIO = [18.0, 17.5, 18.2, 17.0, 17.8, 16.9, 17.2, 18.1, 16.5, 17.6,
                   18.4, 17.1, 17.9, 16.3, 16.8, 18.0, 17.4, 16.6, 18.3, 16.1,
                   18.5, 17.7, 17.0, 16.4, 18.1, 17.3, 16.7, 17.8, 16.2, 17.5,
                   18.2, 16.9, 17.6, 16.3, 17.1, 18.4, 16.6, 18.0, 16.2, 17.4]

_TIEMPO = [6.2, 6.8, 6.5, 7.1, 6.9, 7.4, 7.0, 6.6, 7.8, 6.9,
           6.3, 7.2, 6.7, 8.0, 7.5, 6.4, 7.0, 7.6, 6.7, 8.2,
           6.1, 6.8, 7.3, 7.9, 6.5, 7.1, 7.5, 6.8, 8.1, 7.0,
           6.4, 7.4, 6.9, 7.9, 7.2, 6.3, 7.6, 6.7, 8.0, 7.1]


def cargar_datos() -> tuple[pd.DataFrame, str]:
    """
    Devuelve (tabla, origen).
    tabla  -> DataFrame con columnas: N, Demanda, CostoUnitario, Tiempo, CostoTotal
    origen -> texto que indica de dónde salieron los datos
    """
    try:
        crudo = pd.read_excel(RUTA_EXCEL, sheet_name="Datos y Simulación",
                              usecols="A:D", nrows=40)
        crudo.columns = ["N", "Demanda", "CostoUnitario", "Tiempo"]
        tabla = crudo.astype({"N": int, "Demanda": float,
                              "CostoUnitario": float, "Tiempo": float})
        origen = "Archivo Excel del profesor (data/Simulacion_Montecarlo_40_datos.xlsx)"
    except Exception:
        tabla = pd.DataFrame({
            "N": range(1, 41),
            "Demanda": [float(x) for x in _DEMANDA],
            "CostoUnitario": _COSTO_UNITARIO,
            "Tiempo": _TIEMPO,
        })
        origen = "Copia interna de los 40 datos de la guía"

    # Paso 2 de la guía: Costo histórico = Demanda × Costo unitario  (columna E)
    tabla["CostoTotal"] = tabla["Demanda"] * tabla["CostoUnitario"]
    return tabla, origen
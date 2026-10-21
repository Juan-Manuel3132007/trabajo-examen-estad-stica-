# Teorema del Límite Central y Simulación de Monte Carlo

**Demostración por simulación con Python** · Estadística para Ingeniería · Universidad de Medellín

| | |
|---|---|
| **Profesor** | Horacio Fernández C. |
| **Integrantes** | Juan Manuel Moreno Muñoz · David Restrepo · Juan Fernando |
| **Entregables** | Aplicación web interactiva (Streamlit) + informe PDF (`informe/informe.pdf`) |

---

##  ¿Qué hace este proyecto?

Las guías del curso demuestran dos temas en Excel. Este proyecto hace **exactamente el mismo procedimiento en Python**, pero:

- lo repite **10 000 veces en menos de un segundo** (en Excel, 200 repeticiones ya son pesadas),
- lo aplica a **seis distribuciones** distintas, no solo a una,
- **compara automáticamente** cada resultado con su valor teórico,
- muestra todo en una **aplicación web interactiva** con gráficas, deslizadores y un botón que hace lo mismo que la tecla **F9**.

> **¿Qué significa "demostrar" aquí?** No es una prueba matemática formal, sino una **demostración por simulación**: se generan miles de datos aleatorios y se comprueba con números que lo que predice la teoría efectivamente ocurre.

---

## 📁 Estructura del repositorio

```
simulacion-tlc-montecarlo/
├── app.py                      # Aplicación web (interfaz)
├── requirements.txt            # Librerías necesarias
├── README.md                   # Este archivo
├── .gitignore
├── .streamlit/
│   └── config.toml             # Colores y tema de la app
├── data/
│   └── Simulacion_Montecarlo_40_datos.xlsx   # Excel original del profesor
├── src/                        # Lógica del proyecto (separada de la interfaz)
│   ├── __init__.py
│   ├── datos.py                # Carga los 40 datos del Excel
│   ├── tlc.py                  # Simulación del Teorema del Límite Central
│   ├── montecarlo.py           # Simulación de Monte Carlo
│   └── graficos.py             # Gráficas interactivas (Plotly)
├── scripts/
│   └── generar_figuras.py      # Genera las figuras y TODOS los números del informe
├── figuras/                    # Figuras generadas (PDF y PNG)
└── informe/
    ├── informe.tex             # Código fuente del informe (LaTeX)
    ├── valores.tex             # Números generados automáticamente por el script
    ├── tabla_*.tex             # Tablas generadas automáticamente
    └── informe.pdf             # 📄 Informe final para imprimir
```

---

##  Cómo ejecutarlo

Requiere **Python 3.10 o superior**.

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd simulacion-tlc-montecarlo

# 2. (Recomendado) Crear un entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Instalar las librerías
pip install -r requirements.txt

# 4. Abrir la aplicación (se abre sola en el navegador en http://localhost:8501)
streamlit run app.py
```

Para **regenerar las figuras y los números del informe**:

```bash
python scripts/generar_figuras.py
```

Para **recompilar el PDF** (opcional, requiere una distribución de LaTeX con XeLaTeX):

```bash
cd informe
xelatex informe.tex
xelatex informe.tex     # segunda vez para el índice
```

---

##  La aplicación

| Pestaña | Qué contiene |
|---|---|
|  **Inicio** | Qué significa demostrar por simulación y tabla de equivalencias **Excel ↔ Python**. |
|  **Teorema del Límite Central** | Laboratorio con 6 distribuciones, deslizadores para *n* y repeticiones, verificación automática de las 3 predicciones, animación de la campana, gráficos Q-Q y **réplica exacta de la guía**. |
|  **Simulación de Monte Carlo** | Una iteración paso a paso, simulación de 40 a 100 000 iteraciones, percentiles, convergencia, **puntos (d), (e) y (f)** y los **3 hallazgos** del Excel. |
|  **Conexión entre los dos temas** | Experimento que muestra que el error de Monte Carlo es σ/√N. |
|  **Datos** | Los 40 datos, estadísticas descriptivas y descarga de la simulación en CSV. |

---

##  Tema 1 — Teorema del Límite Central

**Teorema.** Si $X_1, \dots, X_n$ son independientes, con la misma distribución (cualquiera), media $\mu$ y varianza $\sigma^2$, entonces para $n$ grande:

$$\bar X \;\approx\; N\!\left(\mu,\ \frac{\sigma}{\sqrt n}\right)$$

El teorema hace **tres predicciones**, y el programa verifica las tres:

| Predicción | Qué dice | Cómo se verifica |
|---|---|---|
| ① Centro | El promedio de las medias es $\mu$ | Comparar con $\mu$ |
| ② Dispersión | La desviación de las medias es $\sigma/\sqrt n$ | Comparar con $\sigma/\sqrt n$ |
| ③ Forma | Las medias forman una campana normal | Asimetría $\gamma/\sqrt n$ → 0, regla 68–95, gráfico Q-Q |

**Ejemplo de la guía (Poisson, λ = 4):** $\mu = 4$, $\sigma = 2$.

| | Teoría | Simulación (200 muestras) |
|---|---|---|
| $n = 5$: desviación de las medias | $2/\sqrt5 = 0.8944$ | 0.8122 |
| $n = 30$: desviación de las medias | $2/\sqrt{30} = 0.3651$ | 0.3889 |

Con 10 000 repeticiones las diferencias bajan a la tercera cifra decimal. **Extensión:** se repitió con las distribuciones exponencial, geométrica, binomial y dado. Incluso con poblaciones muy asimétricas (exponencial: asimetría 2), con $n = 30$ las medias son normales (asimetría $2/\sqrt{30} = 0.365$).

```python
muestras = rng.poisson(4, size=(200, 5))   # tabla A2:E201 de la guía
medias   = muestras.mean(axis=1)           # columna F: =PROMEDIO(A2:E2)
medias.mean()          # G2 -> teoría: 4
medias.std(ddof=1)     # H2 -> teoría: 2/√5 = 0.8944
```

---

##  Tema 2 — Simulación de Monte Carlo

**Modelo de la guía:** $C = D \times \bar c$, con $D \sim N(151.4,\ 16.07)$ y $\bar c = 17.34$ USD.

**Teorema (transformada inversa).** Si $U \sim \text{Uniforme}(0,1)$, entonces $X = F^{-1}(U)$ tiene distribución $F$. Esto es lo que hace `=INV.NORM(ALEATORIO(); μ; σ)` en Excel.

**Una iteración con U = 0.83:**

| Paso | Cálculo | Excel |
|---|---|---|
| 1 | $U = 0.83$ | `=ALEATORIO()` |
| 2 | $z = \Phi^{-1}(0.83) = 0.9542$ | `=INV.NORM.ESTAND(0,83)` |
| 3 | $D = 151.4 + 0.9542 \times 16.07 = 166.73 \approx 167$ | `=INV.NORM(...)` |
| 4 | $C = 167 \times 17.34 = 2\,895.78$ USD | `=G2*C2` |

**Resultados (10 000 iteraciones) contra la teoría:**

| Medida (USD) | Simulación | Teoría |
|---|---|---|
| Promedio | 2 631.9 | 2 625.3 |
| Desviación | 277.0 | 278.6 |
| P5 | 2 184.8 | 2 167.1 |
| P95 | 3 086.5 | 3 083.5 |

```python
U = rng.random(N)                                    # =ALEATORIO()
demanda = np.round(stats.norm.ppf(U, mu, s))         # =REDONDEAR(INV.NORM(U; μ; σ); 0)
costo = demanda * c                                  # Costo = Demanda × Costo unitario
np.percentile(costo, [5, 50, 95])
```

###  Tres hallazgos en el archivo Excel

1. **Tope oculto en la demanda simulada.** La columna G usa `MIN(B2; …)`, que impide que la demanda simulada supere la histórica de esa fila. Resultado: la demanda promedio sale **142.3** en lugar de **151.4** (sesgo de −6 %).
2. **Plantilla incompleta.** La columna C de la hoja *Plantilla Monte Carlo* está vacía, así que el costo simulado da 0.
3. **Correlación ignorada.** La demanda y el costo unitario tienen **r = −0.958** (economía de escala). Un modelo con correlación (normal bivariada) reproduce la variabilidad real (desviación 178 vs. 177 de los datos) y muestra que el modelo de la guía **sobrestima el P95 en USD 197**.

---

##  La conexión entre los dos temas

El promedio de una simulación de $N$ iteraciones **es una media muestral**, así que por el TLC:

$$\text{error de Monte Carlo} = \frac{\sigma_C}{\sqrt N}$$

| N | Error teórico | Error observado |
|---|---|---|
| 100 | 27.86 | 28.79 |
| 10 000 | 2.79 | 2.62 |

**Regla práctica:** para reducir el error a la mitad hay que cuadruplicar las iteraciones. **El TLC es la garantía matemática de que Monte Carlo funciona.**

---

##  Reproducibilidad

Todas las simulaciones usan **semillas fijas** (`2026`). Cada número del informe PDF sale de `scripts/generar_figuras.py`, que escribe `informe/valores.tex`: ningún número se copió a mano. En la aplicación, el botón **🎲 Nueva simulación (F9)** cambia la semilla para ver nuevos resultados.

##  Tecnologías

Python · NumPy · SciPy · Pandas · Matplotlib · Plotly · Streamlit · LaTeX (XeLaTeX)

##  Referencias

- Fernández C., H. *El Teorema del Límite Central* y *Simulación de Montecarlo*. Guías del curso, Universidad de Medellín.
- Montgomery, D. C. y Runger, G. C. *Applied Statistics and Probability for Engineers*. Wiley.
- Walpole, R. E. et al. *Probabilidad y estadística para ingeniería y ciencias*. Pearson.
- Ross, S. M. *Simulation*. Academic Press.
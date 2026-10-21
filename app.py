"""
app.py — Demostración por simulación del Teorema del Límite Central
         y de la Simulación de Monte Carlo.

Estadística para Ingeniería · Universidad de Medellín
Profesor: Horacio Fernández C.
Integrantes: Juan Manuel Moreno Muñoz, David Restrepo, Juan Fernando

Ejecutar con:   python -m streamlit run app.py
"""

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

from src import graficos as g
from src import montecarlo as mc
from src import tlc
from src.datos import cargar_datos, columnas_numericas, hojas_excel, leer_archivo_usuario, plantilla_csv

# =============================================================================
# Configuración general y estilos
# =============================================================================
st.set_page_config(page_title="TLC y Monte Carlo · Estadística UdM", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Source Serif 4', Georgia, serif !important; color: #1E3A5F !important; }
.block-container { padding-top: 2rem; max-width: 1250px; }

.hero {
  background: linear-gradient(120deg, #1E3A5F 0%, #0F766E 100%);
  color: white; padding: 2.2rem 2.4rem; border-radius: 18px; margin-bottom: 1.4rem;
}
.hero h1 { color: white !important; margin: 0 0 .4rem 0; font-size: 2.3rem; }
.hero p  { color: #E2E8F0; margin: 0; font-size: 1.05rem; }
.hero .chip { display:inline-block; background: rgba(255,255,255,.16); padding: .25rem .75rem;
              border-radius: 999px; font-size: .82rem; margin: .8rem .4rem 0 0; }

.tarjeta { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 1.1rem 1.2rem;
           height: 100%; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.tarjeta h4 { margin: 0 0 .35rem 0; color: #1E3A5F; font-size: 1.02rem; }
.tarjeta p  { margin: 0; color: #334155; font-size: .93rem; line-height: 1.5; }

.verif { border-radius: 14px; padding: 1rem 1.1rem; border: 1px solid; height: 100%; }
.verif.ok   { background: #F0FDF4; border-color: #86EFAC; }
.verif.casi { background: #FFFBEB; border-color: #FCD34D; }
.verif .t  { font-weight: 700; color: #1E3A5F; margin-bottom: .4rem; }
.verif .fila { display:flex; justify-content: space-between; font-size: .92rem; color:#334155; }
.verif .v  { font-weight: 600; font-variant-numeric: tabular-nums; }
.verif .nota { font-size: .82rem; color: #475569; margin-top: .45rem; }

.paso { background:#F8FAFC; border-left: 4px solid #0F766E; border-radius: 10px; padding: .8rem 1rem; height:100%; }
.paso .num { font-size:.78rem; font-weight:700; color:#0F766E; text-transform: uppercase; letter-spacing:.04em; }
.paso .val { font-size: 1.35rem; font-weight: 700; color:#1E3A5F; font-variant-numeric: tabular-nums; }
.paso .exc { font-size: .8rem; color:#64748B; font-family: monospace; }

.alerta { background:#FEF2F2; border:1px solid #FCA5A5; border-radius: 12px; padding: .9rem 1.1rem; color:#7F1D1D; }
.idea   { background:#EFF6FF; border:1px solid #93C5FD; border-radius: 12px; padding: .9rem 1.1rem; color:#1E3A8A; }
.conclusion { background:#F0FDFA; border:1px solid #5EEAD4; border-radius: 12px; padding: 1rem 1.2rem; color:#134E4A; }
div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; color: #1E3A5F; }
</style>
""", unsafe_allow_html=True)


def tarjeta(titulo: str, texto: str):
    st.markdown(f'<div class="tarjeta"><h4>{titulo}</h4><p>{texto}</p></div>', unsafe_allow_html=True)


def verificacion(titulo, etiqueta_teo, teo, etiqueta_obs, obs, ok, nota, fmt="{:.4f}"):
    clase = "ok" if ok else "casi"
    icono = "✅" if ok else "⚠️"
    st.markdown(f"""
    <div class="verif {clase}">
      <div class="t">{icono} {titulo}</div>
      <div class="fila"><span>{etiqueta_teo}</span><span class="v">{fmt.format(teo)}</span></div>
      <div class="fila"><span>{etiqueta_obs}</span><span class="v">{fmt.format(obs)}</span></div>
      <div class="nota">{nota}</div>
    </div>""", unsafe_allow_html=True)


def dinero(valor: float, referencia: float | None = None) -> str:
    """Formato de dinero: sin decimales si los valores son grandes, con decimales si son pequeños."""
    escala = abs(referencia if referencia is not None else valor)
    decimales = 0 if escala >= 1000 else (1 if escala >= 100 else 2 if escala >= 1 else 4)
    return f"{valor:,.{decimales}f}"


def paso(numero, titulo, valor, excel):
    st.markdown(f"""<div class="paso"><div class="num">Paso {numero} · {titulo}</div>
    <div class="val">{valor}</div><div class="exc">{excel}</div></div>""", unsafe_allow_html=True)


# =============================================================================
# Estado (semillas para el botón "F9")
# =============================================================================
st.session_state.setdefault("semilla_tlc", 2026)
st.session_state.setdefault("semilla_mc", 2026)

# =============================================================================
# Barra lateral
# =============================================================================
with st.sidebar:
    st.markdown("### 🎓 Universidad de Medellín")
    st.markdown("**Facultad de Ingenierías**  \nEstadística para Ingeniería")
    st.markdown("**Profesor:** Horacio Fernández C.")
    st.divider()
    st.markdown("**Integrantes**")
    st.markdown("- Juan Manuel Moreno Muñoz\n- David Restrepo\n- Juan Fernando")
    st.divider()
    st.markdown("**Cómo usar la app**")
    st.caption("Cada pestaña tiene controles (listas, deslizadores y botones). "
               "El botón **🎲 Nueva simulación** hace lo mismo que presionar **F9** en Excel: "
               "genera nuevos números aleatorios.")

# =============================================================================
# Encabezado
# =============================================================================
st.markdown("""
<div class="hero">
  <h1>Teorema del Límite Central y Simulación de Monte Carlo</h1>
  <p>Demostración por simulación con Python: repetimos miles de veces lo que la guía hace en Excel y
  comprobamos con números y gráficas que la teoría se cumple.</p>
  <span class="chip">📘 Estadística para Ingeniería</span>
  <span class="chip">🐍 Python · NumPy · SciPy · Plotly · Streamlit</span>
  <span class="chip">👥 Moreno · Restrepo · Juan Fernando</span>
</div>
""", unsafe_allow_html=True)

tab_inicio, tab_tlc, tab_mc, tab_conexion, tab_datos = st.tabs(
    ["🏠 Inicio", "📊 Teorema del Límite Central", "🎲 Simulación de Monte Carlo",
     "🔗 Conexión entre los dos temas", "📋 Datos"])

tabla, origen_datos = cargar_datos()
P = mc.estimar_parametros(tabla)

# =============================================================================
# PESTAÑA 0 — INICIO
# =============================================================================
with tab_inicio:
    st.markdown("## ¿Qué significa *demostrar* en este trabajo?")
    st.markdown(
        "No se trata de una prueba matemática formal, sino de una **demostración por simulación**: "
        "generamos miles de datos aleatorios en el computador y **comprobamos con números que lo que "
        "predice la teoría efectivamente ocurre**. Es exactamente el procedimiento de las guías del "
        "profesor en Excel, pero automatizado, con más repeticiones, más distribuciones y gráficas interactivas.")

    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta("📊 Teorema del Límite Central",
                "Mostramos que las <b>medias</b> de muestras de cualquier distribución (Poisson, exponencial, "
                "dado…) forman una campana normal centrada en μ y con desviación σ/√n.")
    with c2:
        tarjeta("🎲 Simulación de Monte Carlo",
                "Con los 40 datos de la guía (o con <b>tus propios datos</b>) estimamos el costo de la operación: "
                "promedio, desviación y percentiles P5, P50 y P95, con cuatro distribuciones posibles. "
                "Además resolvemos los puntos a–f del ejercicio propuesto.")
    with c3:
        tarjeta("🔗 La conexión",
                "Monte Carlo funciona <b>gracias</b> al TLC: el promedio de N simulaciones es una media "
                "muestral y su error baja como σ/√N.")

    st.markdown("### Equivalencia entre Excel y Python")
    st.markdown("Cada paso de las guías tiene su equivalente directo en el código:")
    st.dataframe(pd.DataFrame({
        "Qué se hace": ["Número aleatorio entre 0 y 1", "Muestras Poisson (λ = 4)", "Media de cada muestra",
                        "Media de las medias", "Desviación estándar muestral", "Demanda simulada (normal)",
                        "Percentil 95", "Recalcular", "Histograma"],
        "Excel (guía del profesor)": ["=ALEATORIO()", "Análisis de datos → Generación de números aleatorios",
                                      "=PROMEDIO(A2:E2)", "=PROMEDIO(F2:F201)", "=DESVEST.M(B2:B41)",
                                      "=INV.NORM(F2; μ; σ)", "=PERCENTIL.INC(rango; 0,95)", "Tecla F9",
                                      "Análisis de datos → Histograma"],
        "Python (este proyecto)": ["rng.random()", "rng.poisson(4, size=(200, n))", "muestras.mean(axis=1)",
                                   "medias.mean()", "np.std(x, ddof=1)", "stats.norm.ppf(U, μ, σ)",
                                   "np.percentile(costos, 95)", "Botón 🎲 Nueva simulación",
                                   "Plotly (automático e interactivo)"],
    }), hide_index=True, width="stretch")

    st.markdown('<div class="idea">💡 <b>¿Por qué Python y no solo Excel?</b> En Excel cada experimento '
                'se arma a mano (generar, promediar, hacer el histograma) y 200 repeticiones ya son pesadas. '
                'En Python el mismo experimento se repite <b>10.000 veces en menos de un segundo</b>, para '
                'cualquier distribución y cualquier tamaño de muestra, y la comparación con la teoría es '
                'automática.</div>', unsafe_allow_html=True)

# =============================================================================
# PESTAÑA 1 — TEOREMA DEL LÍMITE CENTRAL
# =============================================================================
with tab_tlc:
    st.markdown("## Teorema del Límite Central")

    with st.container(border=True):
        st.markdown("**Definición (media muestral).** Si $X_1, X_2, \\dots, X_n$ es una muestra aleatoria, "
                    "su media muestral es")
        st.latex(r"\bar X=\frac{1}{n}\sum_{i=1}^{n}X_i")
        st.markdown("**Teorema (TLC).** Sean $X_1,\\dots,X_n$ variables aleatorias **independientes** y con "
                    "**la misma distribución** (cualquiera), con media $\\mu$ y varianza $\\sigma^2$ finita. "
                    "Entonces, cuando $n$ es grande,")
        st.latex(r"\bar X \;\overset{\text{aprox.}}{\sim}\; N\!\left(\mu,\ \frac{\sigma}{\sqrt n}\right)"
                 r"\qquad\Longleftrightarrow\qquad Z=\frac{\bar X-\mu}{\sigma/\sqrt n}\;\xrightarrow{\;n\to\infty\;}\;N(0,1)")
        st.caption("En la práctica, n ≥ 30 suele ser suficiente; si la población ya es simétrica, basta con menos.")

    st.markdown("#### El teorema hace tres predicciones que vamos a verificar")
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta("① Centro", "El promedio de todas las medias muestrales es igual a la media de la población: "
                "E[X̄] = μ.")
    with c2:
        tarjeta("② Dispersión", "La desviación estándar de las medias es σ/√n. Con muestras más grandes "
                "las medias se concentran más.")
    with c3:
        tarjeta("③ Forma", "El histograma de las medias se vuelve una campana normal, <b>aunque la "
                "población original no lo sea</b>.")

    st.markdown("### 🔬 Laboratorio interactivo")
    with st.container(border=True):
        cc1, cc2, cc3, cc4 = st.columns([1.4, 1.4, 1.2, 1])
        with cc1:
            nombre = st.selectbox("Distribución de la población", list(tlc.DISTRIBUCIONES), index=0)
        dist = tlc.DISTRIBUCIONES[nombre]
        params = dict(dist.parametros)
        with cc2:
            if nombre == "Poisson":
                params["lambda"] = st.slider("λ (lambda)", 0.5, 15.0, 4.0, 0.5)
            elif nombre == "Binomial":
                params["m"] = st.slider("m (ensayos)", 1, 50, 10)
                params["p"] = st.slider("p (probabilidad de éxito)", 0.05, 0.95, 0.2, 0.05)
            elif nombre == "Geométrica":
                params["p"] = st.slider("p (probabilidad de éxito)", 0.05, 0.95, 0.25, 0.05)
            elif nombre == "Uniforme continua":
                params["a"], params["b"] = st.slider("Intervalo [a, b]", 0.0, 20.0, (0.0, 10.0), 0.5)
            elif nombre == "Exponencial":
                params["beta"] = st.slider("β (media)", 0.5, 10.0, 2.0, 0.5)
            else:
                st.markdown("<br>Sin parámetros: caras 1 a 6", unsafe_allow_html=True)
        with cc3:
            n = st.slider("Tamaño de cada muestra  n", 1, 100, 5)
            repeticiones = st.select_slider("Número de muestras (repeticiones)",
                                            options=[200, 500, 1000, 5000, 10000], value=200)
        with cc4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎲 Nueva simulación (F9)", width="stretch", key="f9_tlc"):
                st.session_state.semilla_tlc += 1
            st.caption(f"Semilla: {st.session_state.semilla_tlc}")
        st.markdown(f"**{dist.nombre}.** {dist.descripcion}")
        st.latex(dist.formula)

    muestras, medias = tlc.simular_medias(dist, params, n, repeticiones, st.session_state.semilla_tlc)
    R = tlc.resumen(medias, dist, params, n)
    rng_pob = np.random.default_rng(1)
    pob = dist.generar(rng_pob, params, 20000)

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(g.poblacion(pob, dist.discreta,
                                    f"Población original: {dist.nombre} (μ = {R['mu']:.3f}, σ = {R['sigma']:.3f})"),
                        width="stretch")
    with col_b:
        st.plotly_chart(g.histograma_medias(medias, R["mu"], R["sigma_xbarra"], n,
                                            f"{repeticiones} medias muestrales con n = {n}"),
                        width="stretch")

    st.markdown("#### Verificación: teoría contra simulación")
    v1, v2, v3 = st.columns(3)
    # Tolerancias basadas en el error de muestreo (3 errores estándar): con pocas
    # repeticiones es normal que la simulación se aleje un poco de la teoría.
    tol_media = 3 * R["sigma_xbarra"] / np.sqrt(repeticiones)
    tol_desv = 3 / np.sqrt(2 * (repeticiones - 1)) * 100
    tol_cob = 3 * np.sqrt(0.0455 * 0.9545 / repeticiones) * 100
    tol_asim = 3 * np.sqrt(6 / repeticiones)
    with v1:
        verificacion("① Centro", "Teoría:  μ", R["mu"], "Simulación:  promedio de las medias", R["media_obs"],
                     abs(R["media_obs"] - R["mu"]) <= tol_media,
                     f"Diferencia: {R['error_media_pct']:.2f} % · margen por azar con {repeticiones} muestras: "
                     f"±{tol_media:.4f}")
    with v2:
        verificacion("② Dispersión", "Teoría:  σ/√n", R["sigma_xbarra"], "Simulación:  desv. de las medias",
                     R["desv_obs"], R["error_desv_pct"] <= tol_desv,
                     f"σ/√n = {R['sigma']:.4f}/√{n} = {R['sigma_xbarra']:.4f} · diferencia {R['error_desv_pct']:.2f} % "
                     f"(margen por azar ±{tol_desv:.1f} %)")
    with v3:
        verificacion("③ Forma (regla 68-95)", "Normal: dentro de μ ± 2σ/√n", 95.45,
                     "Simulación: dentro de μ ± 2σ/√n", R["dentro_2sigma_pct"],
                     abs(R["dentro_2sigma_pct"] - 95.45) <= tol_cob and abs(R["asimetria"] - R["asimetria_teorica"]) <= tol_asim,
                     f"Dentro de ±1σ/√n: {R['dentro_1sigma_pct']:.1f} % (normal: 68.27 %) · "
                     f"asimetría {R['asimetria']:.3f} (teoría γ/√n = {R['asimetria_teorica']:.3f})",
                     fmt="{:.2f} %")

    with st.expander("👀 Ver las primeras muestras, como en la hoja de Excel"):
        cols = min(n, 10)
        vista = pd.DataFrame(muestras[:10, :cols], columns=[f"X{i + 1}" for i in range(cols)])
        if n > 10:
            vista["…"] = "…"
        vista["Media x̄"] = medias[:10].round(4)
        vista.index = [f"Muestra {i + 1}" for i in range(10)]
        st.dataframe(vista, width="stretch")
        x0 = muestras[0]
        st.markdown(f"Ejemplo con la muestra 1:  x̄ = ({' + '.join(f'{v:g}' for v in x0[:6])}"
                    f"{' + …' if n > 6 else ''}) / {n} = **{x0.mean():.4f}**")

    st.markdown("### 🎬 La campana aparece al aumentar n")
    st.caption("Las medias se estandarizan con Z = (x̄ − μ)/(σ/√n) para comparar todas contra la misma curva N(0,1). "
               "Presione ▶ Reproducir.")
    st.plotly_chart(g.animacion_tlc(dist.generar, params, R["mu"], R["sigma"],
                                    [1, 2, 3, 5, 8, 12, 20, 30, 50, 100]), width="stretch")

    valores_n = (1, 2, 5, 10, 30, 50)
    filas = tlc.tabla_varios_n(dist, params, valores_n, repeticiones=max(repeticiones, 5000),
                               semilla=st.session_state.semilla_tlc)
    mosaico = []
    for nn in valores_n:
        _, m_ = tlc.simular_medias(dist, params, nn, max(repeticiones, 5000), st.session_state.semilla_tlc + nn)
        mosaico.append((nn, m_, R["mu"], R["sigma"] / np.sqrt(nn)))
    st.plotly_chart(g.mosaico_n(mosaico, f"{dist.nombre}: histograma de las medias para distintos n"),
                    width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(g.desviacion_vs_n(filas), width="stretch")
    with c2:
        st.plotly_chart(g.asimetria_vs_n(filas), width="stretch")

    st.dataframe(pd.DataFrame([{
        "n": f["n"],
        "μ teórica": round(f["mu"], 4), "Promedio de medias": round(f["media_obs"], 4),
        "σ/√n teórica": round(f["sigma_xbarra"], 4), "Desv. observada": round(f["desv_obs"], 4),
        "Asimetría teórica γ/√n": round(f["asimetria_teorica"], 3), "Asimetría observada": round(f["asimetria"], 3),
        "% en μ±1σ/√n (68.27)": round(f["dentro_1sigma_pct"], 1),
        "% en μ±2σ/√n (95.45)": round(f["dentro_2sigma_pct"], 1)} for f in filas]),
        hide_index=True, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        _, m1 = tlc.simular_medias(dist, params, 1, 1000, 11)
        st.plotly_chart(g.qq_plot(m1, "Gráfico Q-Q con n = 1 (la población misma)"), width="stretch")
    with c2:
        _, m30 = tlc.simular_medias(dist, params, 30, 1000, 12)
        st.plotly_chart(g.qq_plot(m30, "Gráfico Q-Q con n = 30"), width="stretch")
    st.caption("Si los puntos caen sobre la recta, los datos son normales. Con n = 1 se curvan; con n = 30 se alinean.")

    st.markdown("### 📄 Réplica exacta de la guía del profesor")
    st.markdown("Poisson con λ = 4, **200 muestras**, tamaños **n = 5** y **n = 30**, histograma con clases de "
                "ancho 0.2 entre 1.0 y 7.0 (columna *Bin* de la guía).")
    poisson = tlc.DISTRIBUCIONES["Poisson"]
    c1, c2 = st.columns(2)
    for col, nn in [(c1, 5), (c2, 30)]:
        _, m_g = tlc.simular_medias(poisson, {"lambda": 4.0}, nn, 200, st.session_state.semilla_tlc)
        r_g = tlc.resumen(m_g, poisson, {"lambda": 4.0}, nn)
        with col:
            st.plotly_chart(g.histograma_medias(m_g, 4.0, 2 / np.sqrt(nn), nn,
                                                f"Guía: Poisson(4), n = {nn}", ancho_clase=0.2), width="stretch")
            st.markdown(f"""
| Celda de la guía | Fórmula | Valor teórico | Simulación |
|---|---|---|---|
| G2 | `=PROMEDIO(F2:F201)` | μ = 4 | **{r_g['media_obs']:.4f}** |
| H2 | `=DESVEST(F2:F201)` | 2/√{nn} = {2 / np.sqrt(nn):.4f} | **{r_g['desv_obs']:.4f}** |
""")

    st.markdown("""<div class="conclusion"><b>Conclusión.</b> Para todas las distribuciones las tres
    predicciones se cumplen: (1) las medias se centran en μ; (2) su desviación coincide con σ/√n;
    (3) su forma se vuelve normal al crecer n, con una asimetría que cae como γ/√n. Mientras más
    asimétrica es la población (exponencial, geométrica), más grande debe ser n para que la campana aparezca;
    para poblaciones simétricas (dado, uniforme) basta con n ≈ 5.</div>""", unsafe_allow_html=True)


# =============================================================================
# PESTAÑA 2 — MONTE CARLO
# =============================================================================
with tab_mc:
    st.markdown("## Simulación de Monte Carlo")

    with st.container(border=True):
        st.markdown("**Definición.** La simulación de Monte Carlo estudia un problema con incertidumbre "
                    "generando **muchos escenarios aleatorios**, calculando el resultado en cada uno y "
                    "analizando la distribución de todos esos resultados.")
        st.markdown("**Modelo:** el costo es la variable incierta $X$ por el costo unitario $c$ "
                    "(en la guía, $X$ es la demanda $D$):")
        st.latex(r"C = X \times c \qquad\text{con}\qquad X\sim F\ \ \text{(normal en la guía)},"
                 r"\quad c=\bar c\ \text{(costo unitario promedio)}")
        st.markdown("**Teorema (transformada inversa).** Si $U\\sim\\text{Uniforme}(0,1)$ y $F$ es una función "
                    "de distribución acumulada continua y creciente, entonces $X=F^{-1}(U)$ tiene distribución $F$.")
        st.latex(r"P\big(X\le x\big)=P\big(F^{-1}(U)\le x\big)=P\big(U\le F(x)\big)=F(x)")
        st.caption("La última igualdad se cumple porque, para una uniforme, P(U ≤ u) = u. "
                   "Esto es lo que hace INV.NORM(ALEATORIO(); μ; σ) en Excel.")

    # -------------------------------------------------------------------------
    # 1. Fuente de los datos
    # -------------------------------------------------------------------------
    st.markdown("### 1. ¿Con qué datos simular?")
    with st.container(border=True):
        fuente = st.radio("Fuente de los datos",
                          ["📘 Datos de la guía (40 datos)", "📂 Subir mi propio archivo (CSV o Excel)",
                           "✏️ Escribir los parámetros a mano"], horizontal=True)

        # Valores por defecto: los datos de la guía
        modo, datos_mc, col_var, col_costo = "guia", tabla, "Demanda", "CostoUnitario"
        etiqueta, origen_mc, c_fijo = "Demanda", origen_datos, None

        if fuente.startswith("📂"):
            a1, a2 = st.columns([2, 1])
            with a1:
                archivo = st.file_uploader("Archivo con tus datos: una columna por variable y una fila por "
                                           "observación (la primera fila son los nombres de las columnas)",
                                           type=["csv", "xlsx", "xls"])
            with a2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button("⬇️ Descargar plantilla de ejemplo (CSV)", plantilla_csv(),
                                   "plantilla_montecarlo.csv", "text/csv", width="stretch")
                st.caption("Acepta CSV con coma o con punto y coma, y archivos de Excel.")
            if archivo is None:
                st.info("Sube un archivo para usar tus datos. Mientras tanto se muestran los datos de la guía.")
            else:
                try:
                    hoja = None
                    if archivo.name.lower().endswith((".xlsx", ".xls")):
                        hojas = hojas_excel(archivo)
                        # Por defecto se abre la primera hoja que tenga columnas numéricas
                        inicial = next((i for i, h in enumerate(hojas)
                                        if columnas_numericas(leer_archivo_usuario(archivo, h))), 0)
                        hoja = (st.selectbox("Hoja del Excel", hojas, index=inicial) if len(hojas) > 1
                                else hojas[0])
                    df_usuario = leer_archivo_usuario(archivo, hoja)
                    numericas = columnas_numericas(df_usuario)
                    if not numericas:
                        st.error("Esta hoja o archivo no tiene columnas numéricas con al menos 3 datos. "
                                 "Elige otra hoja (si es un Excel) o revisa el formato con la plantilla de ejemplo.")
                    else:
                        s1, s2, s3 = st.columns(3)
                        col_var = s1.selectbox("Variable incierta a simular", numericas)
                        opciones = ["— Ninguna: usar un costo unitario fijo —"] + [c for c in numericas if c != col_var]
                        eleccion = s2.selectbox("Columna del costo unitario (opcional)", opciones)
                        col_costo = None if eleccion.startswith("—") else eleccion
                        if col_costo is None:
                            c_fijo = s3.number_input("Costo unitario fijo (USD por unidad)", value=1.0,
                                                     min_value=0.0001, format="%.4f")
                        modo, datos_mc, etiqueta = "archivo", df_usuario, col_var
                        origen_mc = f"Archivo subido: {archivo.name}"
                        with st.expander(f"👀 Vista previa del archivo ({len(df_usuario)} filas)"):
                            st.dataframe(df_usuario.head(20), width="stretch")
                except Exception as error:
                    st.error(f"No se pudo leer el archivo ({error}). Revisa el formato con la plantilla de ejemplo.")
                    modo, datos_mc, col_var, col_costo = "guia", tabla, "Demanda", "CostoUnitario"

        elif fuente.startswith("✏️"):
            e1, e2, e3, e4 = st.columns(4)
            etiqueta = e1.text_input("Nombre de la variable", "Demanda")
            mu_manual = e2.number_input("Media μ", value=151.4, format="%.4f")
            sd_manual = e3.number_input("Desviación estándar σ", value=16.07, min_value=0.0001, format="%.4f")
            c_manual = e4.number_input("Costo unitario c (USD)", value=17.34, min_value=0.0001, format="%.4f")
            modo, datos_mc, col_var, col_costo, origen_mc = "manual", None, None, None, "Parámetros escritos a mano"

    # Parámetros del modelo según la fuente elegida
    if modo == "manual":
        P = {"n_datos": 0, "media_demanda": mu_manual, "desv_demanda": sd_manual, "son_enteros": False,
             "p_shapiro_demanda": float("nan"), "media_costo_unit": c_manual, "desv_costo_unit": None,
             "correlacion": None, "media_costo_hist": None, "desv_costo_hist": None}
    else:
        P = mc.estimar_parametros(datos_mc, col_var, col_costo)
        if not P["desv_demanda"] > 0:
            st.error(f"La columna «{col_var}» no tiene variación (todos los valores son iguales o hay menos de "
                     "2 datos), así que no hay incertidumbre que simular. Se usan los datos de la guía.")
            modo, datos_mc, col_var, col_costo, c_fijo = "guia", tabla, "Demanda", "CostoUnitario", None
            etiqueta, origen_mc = "Demanda", origen_datos
            P = mc.estimar_parametros(datos_mc, col_var, col_costo)
    mu_d, s_d = P["media_demanda"], P["desv_demanda"]
    c_bar = c_fijo if c_fijo is not None else P["media_costo_unit"]
    tiene_correlacion = P["correlacion"] is not None

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Número de datos", f"{P['n_datos']}" if P["n_datos"] else "—")
    m2.metric(f"Media μ̂ de {etiqueta}", f"{mu_d:,.2f}")
    m3.metric("Desviación s", f"{s_d:,.2f}")
    m4.metric("Costo unitario c (USD)", f"{c_bar:,.2f}")
    m5.metric("Correlación r", f"{P['correlacion']:.3f}" if tiene_correlacion else "—")
    if P["n_datos"]:
        p_sw = P["p_shapiro_demanda"]
        veredicto = ("no hay evidencia en contra de la normalidad" if p_sw > 0.05
                     else "los datos NO parecen normales: conviene probar otra distribución")
        st.caption(f"Fuente: {origen_mc}. Prueba de Shapiro-Wilk (H₀: los datos son normales): "
                   f"valor-p = {p_sw:.3f} → {veredicto}.")
    else:
        st.caption(f"Fuente: {origen_mc}.")

    # -------------------------------------------------------------------------
    # 2. Distribución de la variable incierta
    # -------------------------------------------------------------------------
    st.markdown(f"### 2. Distribución de {etiqueta}")
    d1, d2 = st.columns([3, 1])
    with d1:
        nombre_dist = st.radio("Distribución", mc.DISTRIBUCIONES_MC, horizontal=True,
                               help="Todas tienen la misma media y desviación que los datos; solo cambia la forma.")
    with d2:
        redondear = st.checkbox("Redondear a enteros (unidades)", value=P["son_enteros"],
                                key=f"red_{modo}_{col_var}",
                                help="Como =REDONDEAR(...;0) de la guía. Úsalo si la variable se cuenta en unidades.")
    try:
        dist, dist_latex = mc.construir_distribucion(nombre_dist, mu_d, s_d)
    except ValueError as error:
        st.warning(f"{error} Se usa la distribución normal.")
        nombre_dist = mc.DISTRIBUCIONES_MC[0]
        dist, dist_latex = mc.construir_distribucion(nombre_dist, mu_d, s_d)
    st.latex(dist_latex)

    dists_todas = {}
    for nom in mc.DISTRIBUCIONES_MC:
        try:
            dists_todas[nom] = mc.construir_distribucion(nom, mu_d, s_d)[0]
        except ValueError:
            pass
    st.plotly_chart(g.comparar_distribuciones(dists_todas, c_bar,
                                              "Las cuatro distribuciones del costo: misma media y desviación, distinta forma"),
                    width="stretch")
    st.caption("La normal es simétrica; la lognormal tiene cola larga a la derecha (nunca es negativa); "
               "la uniforme hace igual de probables todos los valores; la triangular es acotada y con pico en la media.")

    # -------------------------------------------------------------------------
    # 3. Una iteración, paso a paso
    # -------------------------------------------------------------------------
    st.markdown("### 3. Una iteración, paso a paso")
    U = st.slider("Número aleatorio U (en Excel lo da ALEATORIO())", 0.01, 0.99, 0.83, 0.01)
    it = mc.una_iteracion(U, mu_d, s_d, c_bar, dist, redondear)
    es_normal = nombre_dist.startswith("Normal")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        paso(1, "Aleatorio", f"U = {U:.2f}", "=ALEATORIO()")
    with p2:
        if es_normal:
            paso(2, "Valor z", f"z = {it['z']:.4f}", f"=INV.NORM.ESTAND({U:.2f})")
        else:
            paso(2, "Inversa", f"F⁻¹({U:.2f})", f"{nombre_dist}")
    with p3:
        valor = f"{it['demanda']:,.2f} ≈ {it['demanda_red']:,.0f}" if redondear else f"{it['demanda']:,.4f}"
        detalle = f"{mu_d:.1f} + ({it['z']:.4f})({s_d:.2f})" if es_normal else "valor que acumula U"
        paso(3, etiqueta[:18], valor, detalle)
    with p4:
        paso(4, "Costo", f"C = {it['costo']:,.2f}",
             f"{it['demanda_red']:,.2f} × {c_bar:.2f}".replace(".00 ×", " ×"))
    st.plotly_chart(g.transformada_inversa(U, dist, it["demanda"], etiqueta), width="stretch")
    st.caption(f"Interpretación: la probabilidad de que {etiqueta} sea menor o igual al valor obtenido es exactamente U.")

    # -------------------------------------------------------------------------
    # 4. Simulación completa
    # -------------------------------------------------------------------------
    st.markdown("### 4. La simulación completa")
    with st.container(border=True):
        k1, k2, k3 = st.columns([2, 1.3, 1])
        with k1:
            N = st.select_slider("Número de iteraciones", options=[40, 100, 1000, 10000, 100000], value=10000)
        with k2:
            c_usuario = st.number_input("Costo unitario (USD) — punto (e)", min_value=0.0001,
                                        value=float(round(c_bar, 4)), step=0.1, format="%.2f",
                                        key=f"c_{modo}_{col_var}_{round(c_bar, 4)}")
        with k3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎲 Nueva simulación (F9)", width="stretch", key="f9_mc"):
                st.session_state.semilla_mc += 1

    sim = mc.simular_costo(dist, c_usuario, N, st.session_state.semilla_mc, redondear)
    Rm = mc.resumen_resultados(sim["Costo"].to_numpy())
    T = mc.teoricos_distribucion(dist, c_usuario)

    r1, r2, r3, r4, r5 = st.columns(5)
    ref = T["media"]
    r1.metric("Costo promedio", dinero(Rm["media"], ref / 10), f"teoría {dinero(T['media'], ref / 10)}", delta_color="off")
    r2.metric("Desviación estándar", dinero(Rm["desv"], ref / 10), f"teoría {dinero(T['desv'], ref / 10)}", delta_color="off")
    r3.metric("Percentil 5 %", dinero(Rm["p5"], ref), f"teoría {dinero(T['p5'], ref)}", delta_color="off")
    r4.metric("Percentil 50 % (mediana)", dinero(Rm["p50"], ref), f"teoría {dinero(T['p50'], ref)}", delta_color="off")
    r5.metric("Percentil 95 %", dinero(Rm["p95"], ref), f"teoría {dinero(T['p95'], ref)}", delta_color="off")
    st.caption("Valores teóricos exactos: si C = c·X, entonces E[C] = c·E[X], σ_C = c·σ_X y cada percentil "
               "del costo es c por el percentil de X. Para la normal, P95 = μ·c + 1.645·σ·c.")

    st.plotly_chart(g.histograma_costos(sim["Costo"].to_numpy(), Rm["p5"], Rm["p50"], Rm["p95"],
                                        mc.curva_costo(dist, c_usuario),
                                        f"Distribución del costo simulado ({N:,} iteraciones, {nombre_dist})"),
                    width="stretch")

    c1, c2 = st.columns([1, 1.6])
    with c1:
        st.markdown("**Primeras iteraciones** (como la hoja *Plantilla Monte Carlo*)")
        vista = sim.head(10).copy()
        vista["Aleatorio"] = vista["Aleatorio"].round(4)
        vista["Variable"] = vista["Variable"].round(2)
        vista["Costo"] = vista["Costo"].round(2)
        st.dataframe(vista.rename(columns={"Iteracion": "Iter.", "Variable": etiqueta[:14]}),
                     hide_index=True, width="stretch")
        st.caption(f"Costo = {etiqueta} × {c_usuario:.2f}")
    with c2:
        st.plotly_chart(g.grafico_convergencia(mc.convergencia(sim["Costo"].to_numpy()), T["media"]),
                        width="stretch")

    # -------------------------------------------------------------------------
    # 5. Interpretación del P95 — punto (d)
    # -------------------------------------------------------------------------
    st.markdown("### 5. ¿Qué significa el percentil 95 para un gerente? — punto (d)")
    st.markdown(f"""<div class="idea">Con {N:,} escenarios, el <b>95 %</b> de los costos simulados quedó por debajo de
    <b>USD {dinero(Rm['p95'])}</b>. Dicho de otra forma: si el gerente presupuesta USD {dinero(Rm['p95'])}, bajo este
    modelo sólo en <b>1 de cada 20</b> escenarios el costo real superaría ese presupuesto. El escenario central
    (mediana) es USD {dinero(Rm['p50'])} y la diferencia, USD {dinero(Rm['p95'] - Rm['p50'], Rm['p95'])}, es una referencia para
    la <b>reserva de contingencia</b>. Como advierte la guía, el P95 no se debe convertir automáticamente en
    presupuesto: depende del riesgo que la empresa acepte, de los contratos y del juicio técnico.</div>""",
                unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 6. Sensibilidad — punto (e)
    # -------------------------------------------------------------------------
    st.markdown("### 6. Sensibilidad al costo unitario — punto (e)")
    base = round(c_bar, 2)
    valores_c = sorted({round(base * f, 2) for f in (0.90, 0.95, 1.0, 1.05, 1.10)})
    sens = mc.sensibilidad_costo_unitario(mu_d, s_d, valores_c, dist=dist, redondear=redondear)
    st.dataframe(sens.rename(columns={"CostoUnitario": "Costo unitario", "media": "Promedio", "desv": "Desviación",
                                      "minimo": "Mínimo", "maximo": "Máximo", "p5": "P5", "p50": "P50",
                                      "p95": "P95"}).round(1), hide_index=True, width="stretch",
                 column_config={"Costo unitario": st.column_config.NumberColumn(format="%.2f")})
    st.caption(f"Costo unitario base ±5 % y ±10 %. Cada dólar adicional en el costo unitario sube el costo promedio "
               f"en ≈ μ = {dist.mean():,.1f} USD y la desviación en ≈ σ = {dist.std():,.2f} USD: el costo es "
               "proporcional a c.")

    # -------------------------------------------------------------------------
    # 7. Supuestos — punto (f)
    # -------------------------------------------------------------------------
    st.markdown("### 7. Supuestos que pueden dar resultados poco realistas — punto (f)")
    if modo == "guia":
        st.markdown("Al revisar el archivo Excel de la guía encontramos tres situaciones importantes:")

        st.markdown("#### Hallazgo 1 · La fórmula de la demanda simulada tiene un tope oculto")
        st.markdown('<div class="alerta">La columna G del Excel no usa sólo INV.NORM, sino:<br>'
                    '<code>=REDONDEAR(MIN(B2; MAX(80; REDONDEAR(INV.NORM(F2; μ; σ);0)));0)</code><br>'
                    'El <code>MIN(B2; …)</code> impide que la demanda simulada supere la demanda histórica de esa '
                    'misma fila. Por ejemplo, en la fila 1 (demanda 120) la simulación nunca puede pasar de 120, '
                    'aunque la media sea 151.4. Resultado: la demanda simulada queda <b>sesgada hacia abajo</b>.</div>',
                    unsafe_allow_html=True)
        prom_g = mc.simular_formula_excel(tabla, mu_d, s_d, 10_000, 3)
        st.plotly_chart(g.sesgo_excel(prom_g, mu_d), width="stretch")
        st.markdown(f"Al simular 10.000 veces la tecla F9, el promedio de la columna G fue **{prom_g.mean():.1f}** "
                    f"unidades en lugar de **{mu_d:.1f}**: un sesgo de **{prom_g.mean() - mu_d:.1f} unidades "
                    f"({(prom_g.mean() / mu_d - 1) * 100:.1f} %)**. Ningún recálculo superó {prom_g.max():.1f}. "
                    "**Corrección:** usar `=REDONDEAR(INV.NORM(F2; μ; σ); 0)` (opcionalmente con `MAX(0; …)` para "
                    "evitar demandas negativas).")

        st.markdown("#### Hallazgo 2 · La hoja *Plantilla Monte Carlo* está incompleta")
        st.markdown("La columna C (*Demanda simulada*) de las 1.000 iteraciones está vacía, así que el costo simulado "
                    "da 0. **Corrección:** en C2 escribir `=REDONDEAR(INV.NORM(B2; PROMEDIO('Datos y Simulación'!$B$2:$B$41); "
                    "DESVEST.M('Datos y Simulación'!$B$2:$B$41)); 0)` y copiar hasta C1001. "
                    "Esta aplicación hace exactamente ese cálculo.")
    else:
        st.markdown(f"""Supuestos del modelo que conviene revisar con estos datos:
- **Forma de la distribución:** se eligió *{nombre_dist}*. Compare el resultado con las otras tres distribuciones;
  si el P95 cambia mucho, la decisión depende de esa elección.
- **Costo unitario fijo:** {'se usa el promedio de la columna de costo, ignorando su variabilidad.' if tiene_correlacion else 'se usa un único valor fijo.'}
- **Tamaño de la muestra:** {'con ' + str(P['n_datos']) + ' datos, μ y σ son estimaciones con error.' if P['n_datos'] else 'los parámetros se escribieron a mano: su calidad depende de la fuente.'}
- **Independencia entre variables:** se revisa abajo cuando hay una columna de costo unitario.""")

    if tiene_correlacion:
        titulo_h = "Hallazgo 3 · " if modo == "guia" else ""
        st.markdown(f"#### {titulo_h}¿{etiqueta} y el costo unitario son independientes?")
        c1, c2 = st.columns([1, 1.25])
        with c1:
            pares = datos_mc[[col_var, col_costo]].dropna()
            st.plotly_chart(g.dispersion_datos(pares[col_var].to_numpy(), pares[col_costo].to_numpy(),
                                               P["correlacion"],
                                               "Demanda (unidades)" if modo == "guia" else etiqueta,
                                               "Costo unitario (USD)" if modo == "guia" else col_costo),
                            width="stretch")
        with c2:
            r = P["correlacion"]
            fuerza = "fuerte" if abs(r) >= 0.7 else ("moderada" if abs(r) >= 0.4 else "débil")
            sentido = "negativa: cuando una sube, la otra baja" if r < 0 else "positiva: suben juntas"
            st.markdown(f"""La correlación es **r = {r:.3f}** (relación {fuerza} y {sentido}). El modelo básico usa un
            costo unitario fijo e ignora esta relación, aunque la sección 11 de la guía recomienda *no asumir
            independencia sin justificación*.

**Modelo mejorado** (normal bivariada). Con $Z_1, Z_2 \\sim N(0,1)$ independientes:""")
            st.latex(r"X=\mu_X+\sigma_X Z_1,\qquad c=\mu_c+\sigma_c\big(\rho Z_1+\sqrt{1-\rho^2}\,Z_2\big)")
            st.markdown("Así $X$ y $c$ quedan con correlación exactamente $\\rho$.")

        guia = mc.simular_modelo_guia(mu_d, s_d, P["media_costo_unit"], 100_000, 2026)["Costo"].to_numpy()
        if not redondear:
            guia = mc.simular_costo(mc.construir_distribucion("Normal", mu_d, s_d)[0], P["media_costo_unit"],
                                    100_000, 2026, False)["Costo"].to_numpy()
        corr = mc.simular_modelo_correlacionado(mu_d, s_d, P["media_costo_unit"], P["desv_costo_unit"], r,
                                                100_000, 2026, redondear)["Costo"].to_numpy()
        Rg, Rc = mc.resumen_resultados(guia), mc.resumen_resultados(corr)
        st.plotly_chart(g.comparar_modelos(guia, corr, Rg["p95"], Rc["p95"]), width="stretch")
        st.dataframe(pd.DataFrame({
            "Modelo": ["Costo unitario fijo (independiente)", "Con correlación (mejorado)", "Datos históricos reales"],
            "Promedio": [dinero(Rg["media"], Rg["p95"] / 10), dinero(Rc["media"], Rg["p95"] / 10),
                         dinero(P["media_costo_hist"], Rg["p95"] / 10)],
            "Desviación": [dinero(Rg["desv"], Rg["p95"] / 10), dinero(Rc["desv"], Rg["p95"] / 10),
                           dinero(P["desv_costo_hist"], Rg["p95"] / 10)],
            "P5": [dinero(Rg["p5"], Rg["p95"] / 10), dinero(Rc["p5"], Rg["p95"] / 10), "—"],
            "P95": [dinero(Rg["p95"], Rg["p95"] / 10), dinero(Rc["p95"], Rg["p95"] / 10), "—"],
        }), hide_index=True, width="stretch")
        dif = Rg["p95"] - Rc["p95"]
        st.markdown(f"""<div class="conclusion"><b>Conclusión.</b> La desviación real del costo en los datos es
        {dinero(P['desv_costo_hist'], Rg['p95'] / 10)}. El modelo de costo fijo da {dinero(Rg['desv'], Rg['p95'] / 10)} y el
        modelo con correlación {dinero(Rc['desv'], Rg['p95'] / 10)}: el que más se acerque al valor real es el que mejor
        representa el riesgo. Entre ambos modelos el P95 cambia en <b>USD {dinero(abs(dif), Rg['p95'])}</b> ({'el modelo fijo lo sobrestima' if dif > 0 else 'el modelo fijo lo subestima'}).
        Otros supuestos: el tamaño de la muestra (μ y σ tienen error de estimación) y que el modelo no incluye otras
        fuentes de costo.</div>""", unsafe_allow_html=True)

# =============================================================================
# PESTAÑA 3 — CONEXIÓN ENTRE LOS DOS TEMAS
# =============================================================================
with tab_conexion:
    st.markdown("## ¿Por qué funciona Monte Carlo? Por el Teorema del Límite Central")
    st.markdown("El costo promedio que entrega una simulación de $N$ iteraciones es")
    st.latex(r"\bar C_N=\frac{1}{N}\sum_{k=1}^{N}C_k")
    st.markdown("Pero eso es **una media muestral** de $N$ costos independientes. Por lo tanto, el TLC se aplica "
                "directamente:")
    st.latex(r"\bar C_N\;\overset{\text{aprox.}}{\sim}\;N\!\left(\mu_C,\ \frac{\sigma_C}{\sqrt N}\right)"
             r"\qquad\Longrightarrow\qquad \text{error típico}=\frac{\sigma_C}{\sqrt N}")
    st.markdown(f"**Experimento** (con la configuración actual de la pestaña Monte Carlo: {nombre_dist}, "
                f"c = {c_bar:.2f}): repetimos la simulación completa 500 veces para cada valor de N y medimos "
                "cuánto varía el promedio de una simulación a otra.")

    sigma_C = c_bar * dist.std()
    mu_C = c_bar * dist.mean()
    rng_x = np.random.default_rng(99)
    filas_N, prom_por_N = [], {}
    for NN in [10, 100, 1000, 10000]:
        X_ = dist.ppf(rng_x.random((500, NN)))
        if redondear:
            X_ = np.round(X_)
        prom = (X_ * c_bar).mean(axis=1)
        prom_por_N[NN] = prom
        filas_N.append({"N": NN, "sigma": sigma_C, "teo": sigma_C / np.sqrt(NN), "desv_obs": prom.std(ddof=1)})

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.plotly_chart(g.error_vs_N(filas_N), width="stretch")
    with c2:
        st.dataframe(pd.DataFrame({
            "Iteraciones N": [f["N"] for f in filas_N],
            "Error teórico σ/√N": [round(f["teo"], 2) for f in filas_N],
            "Error observado": [round(f["desv_obs"], 2) for f in filas_N],
        }), hide_index=True, width="stretch")
        st.markdown(f"Con $\\sigma_C = c\\cdot\\sigma_X = {c_bar:.2f}\\times{dist.std():.2f} = {sigma_C:,.1f}$ USD:")
        st.latex(rf"N=100:\quad \frac{{{sigma_C:.1f}}}{{\sqrt{{100}}}}={sigma_C / 10:.2f}\ \text{{USD}}")
        st.latex(rf"N=10\,000:\quad \frac{{{sigma_C:.1f}}}{{\sqrt{{10\,000}}}}={sigma_C / 100:.2f}\ \text{{USD}}")
    st.plotly_chart(g.histograma_medias(prom_por_N[100], mu_C, sigma_C / 10, 100,
                                        "Los 500 promedios de simulaciones con N = 100 forman una campana"),
                    width="stretch")
    st.markdown("""<div class="conclusion"><b>Regla práctica.</b> Para reducir el error de una simulación a la mitad
    hay que <b>cuadruplicar</b> las iteraciones; para dividirlo por 10, multiplicarlas por 100. Por eso la guía
    recomienda "un número adecuado de iteraciones": con 40 el resultado cambia mucho en cada F9; con 10.000 queda
    estable. Esto se cumple aunque la variable no sea normal (pruebe con la lognormal): <b>el TLC es la garantía
    matemática de que Monte Carlo funciona</b>.</div>""", unsafe_allow_html=True)

# =============================================================================
# PESTAÑA 4 — DATOS
# =============================================================================
with tab_datos:
    if modo == "manual":
        st.markdown("## Datos")
        st.info("En la pestaña Monte Carlo se eligió escribir los parámetros a mano, así que no hay una tabla de datos. "
                "Abajo se muestran los 40 datos de la guía como referencia.")
        datos_vista, origen_vista = tabla, origen_datos
    else:
        datos_vista, origen_vista = datos_mc, origen_mc
        st.markdown("## Los 40 datos hipotéticos de la guía" if modo == "guia" else "## Tus datos")
    st.caption(f"Fuente: {origen_vista}")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.dataframe(datos_vista, hide_index=True, width="stretch", height=560)
    with c2:
        st.markdown("**Estadísticos descriptivos**")
        st.dataframe(datos_vista.select_dtypes("number").describe().round(3), width="stretch")
        st.download_button("⬇️ Descargar la simulación actual (CSV)",
                           sim.to_csv(index=False).encode("utf-8"), "simulacion_montecarlo.csv", "text/csv",
                           width="stretch")
"""
app.py — Demostración por simulación del Teorema del Límite Central
         y de la Simulación de Monte Carlo.

Estadística para Ingeniería · Universidad de Medellín
Profesor: Horacio Fernández C.
Integrantes: Juan Manuel Moreno Muñoz, David Restrepo, Juan Fernando

Ejecutar con:   streamlit run app.py
"""

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

from src import graficos as g
from src import montecarlo as mc
from src import tlc
from src.datos import cargar_datos

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
                "Con los 40 datos de la guía estimamos el costo de la operación: promedio, desviación y "
                "percentiles P5, P50 y P95. Además resolvemos los puntos a–f del ejercicio propuesto.")
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
        st.markdown("**Modelo de la guía:**")
        st.latex(r"C = D \times c \qquad\text{con}\qquad D\sim N(\mu_D,\ \sigma_D),\quad c=\bar c\ \text{(costo unitario promedio)}")
        st.markdown("**Teorema (transformada inversa).** Si $U\\sim\\text{Uniforme}(0,1)$ y $F$ es una función "
                    "de distribución acumulada continua y creciente, entonces $X=F^{-1}(U)$ tiene distribución $F$.")
        st.latex(r"P\big(X\le x\big)=P\big(F^{-1}(U)\le x\big)=P\big(U\le F(x)\big)=F(x)")
        st.caption("La última igualdad se cumple porque, para una uniforme, P(U ≤ u) = u. "
                   "Esto es lo que hace INV.NORM(ALEATORIO(); μ; σ) en Excel.")

    st.markdown("### 1. Los 40 datos de la guía")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Demanda media μ̂ (und)", f"{P['media_demanda']:.2f}")
    m2.metric("Desviación s (und)", f"{P['desv_demanda']:.2f}")
    m3.metric("Costo unitario c̄ (USD)", f"{P['media_costo_unit']:.2f}")
    m4.metric("Costo histórico (USD)", f"{P['media_costo_hist']:,.0f}")
    m5.metric("Correlación r", f"{P['correlacion']:.3f}")
    st.caption(f"Fuente: {origen_datos}. ¿Es razonable suponer que la demanda es normal? "
               f"Prueba de Shapiro-Wilk sobre los 40 datos: valor-p = {P['p_shapiro_demanda']:.3f} > 0.05, "
               "así que no hay evidencia en contra de la normalidad.")

    mu_d, s_d, c_bar = P["media_demanda"], P["desv_demanda"], P["media_costo_unit"]

    st.markdown("### 2. Una iteración, paso a paso")
    U = st.slider("Número aleatorio U (en Excel lo da ALEATORIO())", 0.01, 0.99, 0.83, 0.01)
    it = mc.una_iteracion(U, mu_d, s_d, c_bar)
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        paso(1, "Aleatorio", f"U = {U:.2f}", "=ALEATORIO()")
    with p2:
        paso(2, "Valor z", f"z = {it['z']:.4f}", f"=INV.NORM.ESTAND({U:.2f})")
    with p3:
        paso(3, "Demanda", f"D = {it['demanda']:.2f} ≈ {it['demanda_red']}",
             f"{mu_d:.1f} + ({it['z']:.4f})({s_d:.2f})")
    with p4:
        paso(4, "Costo", f"C = {it['costo']:,.2f} USD", f"{it['demanda_red']} × {c_bar:.2f}")
    st.plotly_chart(g.transformada_inversa(U, mu_d, s_d, it["demanda"]), width="stretch")
    st.caption("Interpretación: la probabilidad de que la demanda sea menor o igual al valor obtenido es exactamente U.")

    st.markdown("### 3. La simulación completa")
    with st.container(border=True):
        k1, k2, k3 = st.columns([2, 1.3, 1])
        with k1:
            N = st.select_slider("Número de iteraciones", options=[40, 100, 1000, 10000, 100000], value=10000)
        with k2:
            c_usuario = st.number_input("Costo unitario (USD) — punto (e)", 10.0, 30.0, round(c_bar, 2), 0.1)
        with k3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎲 Nueva simulación (F9)", width="stretch", key="f9_mc"):
                st.session_state.semilla_mc += 1

    sim = mc.simular_modelo_guia(mu_d, s_d, c_usuario, N, st.session_state.semilla_mc)
    Rm = mc.resumen_resultados(sim["Costo"].to_numpy())
    T = mc.resultados_teoricos(mu_d, s_d, c_usuario)

    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Costo promedio", f"{Rm['media']:,.1f}", f"teoría {T['media']:,.1f}", delta_color="off")
    r2.metric("Desviación estándar", f"{Rm['desv']:,.1f}", f"teoría {T['desv']:,.1f}", delta_color="off")
    r3.metric("Percentil 5 %", f"{Rm['p5']:,.0f}", f"teoría {T['p5']:,.0f}", delta_color="off")
    r4.metric("Percentil 50 % (mediana)", f"{Rm['p50']:,.0f}", f"teoría {T['p50']:,.0f}", delta_color="off")
    r5.metric("Percentil 95 %", f"{Rm['p95']:,.0f}", f"teoría {T['p95']:,.0f}", delta_color="off")
    st.caption("Valores teóricos: como c es constante y D es normal, C = D·c también es normal con media μ·c y "
               "desviación σ·c, y P95 = μ·c + 1.645·σ·c.")

    st.plotly_chart(g.histograma_costos(sim["Costo"].to_numpy(), Rm["p5"], Rm["p50"], Rm["p95"],
                                        (T["media"], T["desv"]), f"Distribución del costo simulado ({N:,} iteraciones)"),
                    width="stretch")

    c1, c2 = st.columns([1, 1.6])
    with c1:
        st.markdown("**Primeras iteraciones** (como la hoja *Plantilla Monte Carlo*)")
        vista = sim.head(10).copy()
        vista["Aleatorio"] = vista["Aleatorio"].round(4)
        vista["Costo"] = vista["Costo"].round(2)
        st.dataframe(vista.rename(columns={"Iteracion": "Iter."}), hide_index=True, width="stretch")
        st.caption(f"Costo = Demanda × {c_usuario:.2f}")
    with c2:
        st.plotly_chart(g.grafico_convergencia(mc.convergencia(sim["Costo"].to_numpy()), T["media"]),
                        width="stretch")

    st.markdown("### 4. ¿Qué significa el percentil 95 para un gerente? — punto (d)")
    st.markdown(f"""<div class="idea">Con {N:,} escenarios, el <b>95 %</b> de los costos simulados quedó por debajo de
    <b>USD {Rm['p95']:,.0f}</b>. Dicho de otra forma: si el gerente presupuesta USD {Rm['p95']:,.0f}, bajo este
    modelo sólo en <b>1 de cada 20</b> escenarios el costo real superaría ese presupuesto. El escenario central
    (mediana) es USD {Rm['p50']:,.0f} y la diferencia, USD {Rm['p95'] - Rm['p50']:,.0f}, es una referencia para
    la <b>reserva de contingencia</b>. Como advierte la guía, el P95 no se debe convertir automáticamente en
    presupuesto: depende del riesgo que la empresa acepte, de los contratos y del juicio técnico.</div>""",
                unsafe_allow_html=True)

    st.markdown("### 5. Sensibilidad al costo unitario — punto (e)")
    sens = mc.sensibilidad_costo_unitario(mu_d, s_d, [16.0, 16.5, 17.0, round(c_bar, 2), 18.0, 18.5, 19.0])
    st.dataframe(sens.rename(columns={"CostoUnitario": "Costo unitario", "media": "Promedio", "desv": "Desviación",
                                      "minimo": "Mínimo", "maximo": "Máximo", "p5": "P5", "p50": "P50",
                                      "p95": "P95"}).round(1), hide_index=True, width="stretch",
                 column_config={"Costo unitario": st.column_config.NumberColumn(format="%.2f")})
    st.caption(f"Cada dólar adicional en el costo unitario sube el costo promedio en ≈ μ_D = {mu_d:.1f} USD y "
               f"la desviación en ≈ σ_D = {s_d:.1f} USD: el costo es proporcional a c.")

    st.markdown("### 6. Supuestos que pueden dar resultados poco realistas — punto (f)")
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
    st.markdown("La columna C (*Demanda simulada*) de las 1.000 iteraciones está vacía, así que el costo simulado da 0. "
                "**Corrección:** en C2 escribir `=REDONDEAR(INV.NORM(B2; PROMEDIO('Datos y Simulación'!$B$2:$B$41); "
                "DESVEST.M('Datos y Simulación'!$B$2:$B$41)); 0)` y copiar hasta C1001. "
                "Esta aplicación hace exactamente ese cálculo.")

    st.markdown("#### Hallazgo 3 · La demanda y el costo unitario NO son independientes")
    c1, c2 = st.columns([1, 1.25])
    with c1:
        st.plotly_chart(g.dispersion_datos(tabla["Demanda"], tabla["CostoUnitario"], P["correlacion"]),
                        width="stretch")
    with c2:
        st.markdown(f"""La correlación entre demanda y costo unitario es **r = {P['correlacion']:.3f}**: cuando se
        compra más, el precio por unidad baja (economía de escala). El modelo de la guía usa un costo unitario fijo e
        ignora esta relación, aunque la sección 11 de la misma guía recomienda *no asumir independencia sin
        justificación*.

**Modelo mejorado** (normal bivariada). Con $Z_1, Z_2 \\sim N(0,1)$ independientes:""")
        st.latex(r"D=\mu_D+\sigma_D Z_1,\qquad c=\mu_c+\sigma_c\big(\rho Z_1+\sqrt{1-\rho^2}\,Z_2\big)")
        st.markdown("Así $D$ y $c$ quedan con correlación exactamente $\\rho$.")

    guia = mc.simular_modelo_guia(mu_d, s_d, c_bar, 100_000, 2026)["Costo"].to_numpy()
    corr = mc.simular_modelo_correlacionado(mu_d, s_d, c_bar, P["desv_costo_unit"], P["correlacion"],
                                            100_000, 2026)["Costo"].to_numpy()
    Rg, Rc = mc.resumen_resultados(guia), mc.resumen_resultados(corr)
    st.plotly_chart(g.comparar_modelos(guia, corr, Rg["p95"], Rc["p95"]), width="stretch")
    st.dataframe(pd.DataFrame({
        "Modelo": ["Guía (costo unitario fijo)", "Con correlación (mejorado)", "Datos históricos reales (40)"],
        "Promedio": [Rg["media"], Rc["media"], P["media_costo_hist"]],
        "Desviación": [Rg["desv"], Rc["desv"], P["desv_costo_hist"]],
        "P5": [f"{Rg['p5']:,.1f}", f"{Rc['p5']:,.1f}", "—"], "P95": [f"{Rg['p95']:,.1f}", f"{Rc['p95']:,.1f}", "—"],
    }).round(1), hide_index=True, width="stretch")
    st.markdown(f"""<div class="conclusion"><b>Conclusión.</b> Los dos modelos tienen casi el mismo promedio, pero el
    modelo de la guía <b>exagera la variabilidad</b>: su desviación ({Rg['desv']:,.0f}) es mucho mayor que la real
    ({P['desv_costo_hist']:,.0f}), mientras que el modelo con correlación ({Rc['desv']:,.0f}) la reproduce casi
    exacta. En consecuencia, el P95 de la guía sobreestima el escenario alto en
    <b>USD {Rg['p95'] - Rc['p95']:,.0f}</b>. Otros supuestos a tener en cuenta: sólo 40 datos (los parámetros μ y σ
    tienen error de estimación), la normal permite en teoría demandas negativas, y el modelo no incluye otras
    fuentes de costo (mano de obra, tiempo de operación).</div>""", unsafe_allow_html=True)

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
    st.markdown("**Experimento:** repetimos la simulación completa 500 veces para cada valor de N y medimos cuánto "
                "varía el promedio de una simulación a otra.")

    sigma_C = s_d * c_bar
    rng_x = np.random.default_rng(99)
    filas_N, prom_por_N = [], {}
    for NN in [10, 100, 1000, 10000]:
        U_ = rng_x.random((500, NN))
        prom = (np.round(stats.norm.ppf(U_, mu_d, s_d)) * c_bar).mean(axis=1)
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
        st.markdown(f"Con $\\sigma_C = {s_d:.2f}\\times{c_bar:.2f} = {sigma_C:.1f}$ USD:")
        st.latex(rf"N=100:\quad \frac{{{sigma_C:.1f}}}{{\sqrt{{100}}}}={sigma_C / 10:.2f}\ \text{{USD}}")
        st.latex(rf"N=10\,000:\quad \frac{{{sigma_C:.1f}}}{{\sqrt{{10\,000}}}}={sigma_C / 100:.2f}\ \text{{USD}}")
    st.plotly_chart(g.histograma_medias(prom_por_N[100], mu_d * c_bar, sigma_C / 10, 100,
                                        "Los 500 promedios de simulaciones con N = 100 forman una campana"),
                    width="stretch")
    st.markdown("""<div class="conclusion"><b>Regla práctica.</b> Para reducir el error de una simulación a la mitad
    hay que <b>cuadruplicar</b> las iteraciones; para dividirlo por 10, multiplicarlas por 100. Por eso la guía
    recomienda "un número adecuado de iteraciones": con 40 el resultado cambia mucho en cada F9; con 10.000 queda
    estable al dólar. Los dos temas no son independientes: <b>el TLC es la garantía matemática de que Monte Carlo
    funciona</b>.</div>""", unsafe_allow_html=True)

# =============================================================================
# PESTAÑA 4 — DATOS
# =============================================================================
with tab_datos:
    st.markdown("## Los 40 datos hipotéticos de la guía")
    st.caption(f"Fuente: {origen_datos}")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.dataframe(tabla.rename(columns={"Demanda": "Demanda (und)", "CostoUnitario": "Costo unitario (USD)",
                                           "Tiempo": "Tiempo (h)", "CostoTotal": "Costo total (USD)"}),
                     hide_index=True, width="stretch", height=560)
    with c2:
        st.markdown("**Estadísticos descriptivos**")
        st.dataframe(tabla[["Demanda", "CostoUnitario", "Tiempo", "CostoTotal"]].describe().round(3),
                     width="stretch")
        st.download_button("⬇️ Descargar la simulación actual (CSV)",
                           sim.to_csv(index=False).encode("utf-8"), "simulacion_montecarlo.csv", "text/csv",
                           width="stretch")
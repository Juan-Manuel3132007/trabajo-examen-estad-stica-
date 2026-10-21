"""
graficos.py
-----------
Todas las gráficas interactivas (Plotly) de la aplicación.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

# Paleta de colores de la app
AZUL = "#1E3A5F"
VERDE = "#0F766E"
AMBAR = "#D97706"
ROJO = "#B91C1C"
GRIS = "#64748B"
FONDO = "#FFFFFF"


def _estilo(fig: go.Figure, titulo: str = "", alto: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15, color=AZUL), x=0.01),
        height=alto,
        margin=dict(l=10, r=10, t=50 if titulo else 20, b=10),
        paper_bgcolor=FONDO,
        plot_bgcolor=FONDO,
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#0F172A"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)"),
        bargap=0.04,
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EEF2F6", zeroline=False, linecolor="#CBD5E1")
    fig.update_yaxes(showgrid=True, gridcolor="#EEF2F6", zeroline=False, linecolor="#CBD5E1")
    return fig


def _clases(valores: np.ndarray, objetivo: int = 45) -> dict | None:
    """
    Si los valores son discretos (p. ej. demanda entera × costo fijo = saltos de 17.34 USD),
    usa clases que sean múltiplo exacto del salto, para que el histograma no tenga 'huecos' falsos.
    """
    unicos = np.unique(valores)
    if len(unicos) > len(valores) / 5 or len(unicos) < 3:
        return None
    paso = float(np.min(np.diff(unicos)))
    k = max(1, round((unicos[-1] - unicos[0]) / paso / objetivo))
    return dict(start=unicos[0] - paso / 2, end=unicos[-1] + paso, size=paso * k)


# ---------------------------------------------------------------------------
# TEOREMA DEL LÍMITE CENTRAL
# ---------------------------------------------------------------------------
def poblacion(datos: np.ndarray, discreta: bool, titulo: str) -> go.Figure:
    """Histograma de la población original (cómo se ve UNA observación X)."""
    fig = go.Figure()
    if discreta:
        valores, cuentas = np.unique(datos, return_counts=True)
        fig.add_bar(x=valores, y=cuentas / cuentas.sum(), marker_color=GRIS,
                    name="Población", hovertemplate="x = %{x}<br>proporción = %{y:.3f}<extra></extra>")
    else:
        fig.add_histogram(x=datos, histnorm="probability density", nbinsx=50,
                          marker_color=GRIS, name="Población")
    fig.update_yaxes(title="Proporción" if discreta else "Densidad")
    fig.update_xaxes(title="Valor de X")
    return _estilo(fig, titulo, 340)


def histograma_medias(medias: np.ndarray, mu: float, sigma_xbarra: float, n: int,
                      titulo: str, ancho_clase: float | None = None) -> go.Figure:
    """Histograma de las medias muestrales con la curva normal que predice el TLC."""
    fig = go.Figure()
    xbins = None
    if ancho_clase:
        xbins = dict(start=np.floor(medias.min()) - ancho_clase / 2,
                     end=np.ceil(medias.max()) + ancho_clase, size=ancho_clase)
    fig.add_histogram(x=medias, histnorm="probability density", xbins=xbins,
                      nbinsx=None if ancho_clase else 35,
                      marker_color=VERDE, opacity=0.85, name=f"Medias simuladas (n = {n})")
    x = np.linspace(mu - 4.2 * sigma_xbarra, mu + 4.2 * sigma_xbarra, 400)
    fig.add_scatter(x=x, y=stats.norm.pdf(x, mu, sigma_xbarra), mode="lines",
                    line=dict(color=AMBAR, width=3),
                    name=f"Normal teórica N(μ = {mu:,.4g}; σ/√n = {sigma_xbarra:.4g})")
    fig.add_vline(x=mu, line=dict(color=AZUL, dash="dash", width=1.5))
    fig.update_xaxes(title="Media muestral  x̄")
    fig.update_yaxes(title="Densidad")
    return _estilo(fig, titulo, 380)


def mosaico_n(resultados: list[tuple[int, np.ndarray, float, float]], titulo: str) -> go.Figure:
    """Varios histogramas para ver cómo aparece la campana al crecer n."""
    columnas = 3
    filas = int(np.ceil(len(resultados) / columnas))
    fig = make_subplots(rows=filas, cols=columnas,
                        subplot_titles=[f"n = {n}" for n, *_ in resultados],
                        horizontal_spacing=0.06, vertical_spacing=0.14)
    for i, (n, medias, mu, sxb) in enumerate(resultados):
        f, c = i // columnas + 1, i % columnas + 1
        fig.add_histogram(x=medias, histnorm="probability density", nbinsx=30,
                          marker_color=VERDE, opacity=0.85, showlegend=False, row=f, col=c)
        x = np.linspace(mu - 4 * sxb, mu + 4 * sxb, 200)
        fig.add_scatter(x=x, y=stats.norm.pdf(x, mu, sxb), mode="lines",
                        line=dict(color=AMBAR, width=2.5), showlegend=False, row=f, col=c)
    return _estilo(fig, titulo, 300 * filas)


def desviacion_vs_n(filas: list[dict]) -> go.Figure:
    """σ_X̄ observada contra la curva teórica σ/√n."""
    n = np.array([f["n"] for f in filas])
    sigma = filas[0]["sigma"]
    nn = np.linspace(1, n.max(), 300)
    fig = go.Figure()
    fig.add_scatter(x=nn, y=sigma / np.sqrt(nn), mode="lines", line=dict(color=AMBAR, width=3),
                    name="Teoría: σ / √n")
    fig.add_scatter(x=n, y=[f["desv_obs"] for f in filas], mode="markers",
                    marker=dict(color=VERDE, size=11, line=dict(color="white", width=1.5)),
                    name="Observado en la simulación")
    fig.update_xaxes(title="Tamaño de muestra n")
    fig.update_yaxes(title="Desviación estándar de las medias")
    return _estilo(fig, "② La dispersión de las medias cae como σ/√n", 360)


def asimetria_vs_n(filas: list[dict]) -> go.Figure:
    n = np.array([f["n"] for f in filas])
    gamma = filas[0]["asimetria_teorica"] * np.sqrt(filas[0]["n"])
    nn = np.linspace(1, n.max(), 300)
    fig = go.Figure()
    fig.add_scatter(x=nn, y=gamma / np.sqrt(nn), mode="lines", line=dict(color=AMBAR, width=3),
                    name="Teoría: γ / √n")
    fig.add_scatter(x=n, y=[f["asimetria"] for f in filas], mode="markers",
                    marker=dict(color=VERDE, size=11, line=dict(color="white", width=1.5)),
                    name="Observado")
    fig.add_hline(y=0, line=dict(color=GRIS, dash="dot"))
    fig.update_xaxes(title="Tamaño de muestra n")
    fig.update_yaxes(title="Coeficiente de asimetría")
    return _estilo(fig, "③ La asimetría cae como γ/√n (la normal tiene 0)", 360)


def qq_plot(medias: np.ndarray, titulo: str) -> go.Figure:
    """Gráfico Q-Q: si los puntos caen sobre la recta, los datos son normales."""
    (teo, obs), (pendiente, intercepto, _) = stats.probplot(medias, dist="norm")
    fig = go.Figure()
    fig.add_scatter(x=teo, y=obs, mode="markers", marker=dict(color=VERDE, size=5, opacity=0.6),
                    name="Medias simuladas")
    fig.add_scatter(x=teo, y=pendiente * teo + intercepto, mode="lines",
                    line=dict(color=AMBAR, width=2.5), name="Recta de la normal")
    fig.update_xaxes(title="Cuantiles teóricos de la normal estándar")
    fig.update_yaxes(title="Cuantiles observados")
    return _estilo(fig, titulo, 360)


def animacion_tlc(generar, parametros, mu, sigma, valores_n, repeticiones=3000, semilla=7):
    """Animación: el histograma de las medias se convierte en campana al aumentar n."""
    rng = np.random.default_rng(semilla)
    cuadros = []
    for n in valores_n:
        medias = generar(rng, parametros, (repeticiones, n)).mean(axis=1)
        z = (medias - mu) / (sigma / np.sqrt(n))          # estandarizadas para ver la forma
        cuentas, bordes = np.histogram(z, bins=np.linspace(-4, 4, 49), density=True)
        centros = (bordes[:-1] + bordes[1:]) / 2
        cuadros.append((n, centros, cuentas))
    x = np.linspace(-4, 4, 300)
    curva = go.Scatter(x=x, y=stats.norm.pdf(x), mode="lines", line=dict(color=AMBAR, width=3),
                       name="Normal estándar N(0,1)")
    n0, c0, h0 = cuadros[0]
    fig = go.Figure(
        data=[go.Bar(x=c0, y=h0, marker_color=VERDE, name="Medias estandarizadas", width=8 / 48), curva],
        frames=[go.Frame(data=[go.Bar(x=c, y=h, marker_color=VERDE, width=8 / 48), curva],
                         name=str(n), layout=go.Layout(title_text=f"n = {n}"))
                for n, c, h in cuadros],
    )
    fig.update_layout(
        updatemenus=[dict(type="buttons", showactive=False, x=0.0, y=-0.18, xanchor="left",
                          buttons=[dict(label="▶  Reproducir", method="animate",
                                        args=[None, dict(frame=dict(duration=900, redraw=True),
                                                         transition=dict(duration=300), fromcurrent=True)]),
                                   dict(label="⏸  Pausa", method="animate",
                                        args=[[None], dict(mode="immediate", frame=dict(duration=0))])])],
        sliders=[dict(active=0, x=0.22, len=0.78, y=-0.12, currentvalue=dict(prefix="Tamaño de muestra n = "),
                      steps=[dict(label=str(n), method="animate",
                                  args=[[str(n)], dict(mode="immediate", frame=dict(duration=0, redraw=True))])
                             for n, *_ in cuadros])],
    )
    fig.update_xaxes(title="Media estandarizada  Z = (x̄ − μ) / (σ/√n)", range=[-4, 4])
    fig.update_yaxes(title="Densidad", range=[0, max(0.75, max(h.max() for *_, h in cuadros) * 1.05)])
    fig = _estilo(fig, f"n = {n0}", 470)
    fig.update_layout(margin=dict(b=110))
    return fig


# ---------------------------------------------------------------------------
# MONTE CARLO
# ---------------------------------------------------------------------------
def transformada_inversa(U: float, dist, x_resultado: float, etiqueta: str = "Demanda") -> go.Figure:
    """Muestra cómo un U uniforme 'rebota' en la curva acumulada F y se vuelve un valor de la variable."""
    lo, hi = dist.ppf(0.0002), dist.ppf(0.9998)
    margen = 0.08 * (hi - lo)
    x = np.linspace(lo - margen, hi + margen, 500)
    fig = go.Figure()
    fig.add_scatter(x=x, y=dist.cdf(x), mode="lines",
                    line=dict(color=AZUL, width=3), name="F(x): función de distribución acumulada")
    fig.add_scatter(x=[x[0], x_resultado], y=[U, U], mode="lines",
                    line=dict(color=AMBAR, width=2.5, dash="dash"), name=f"① U = {U:.2f}")
    fig.add_scatter(x=[x_resultado, x_resultado], y=[U, 0], mode="lines",
                    line=dict(color=VERDE, width=2.5, dash="dash"),
                    name=f"② {etiqueta} = F⁻¹(U) = {x_resultado:,.2f}")
    fig.add_scatter(x=[x_resultado], y=[U], mode="markers",
                    marker=dict(color=ROJO, size=12), showlegend=False)
    fig.update_xaxes(title=etiqueta)
    fig.update_yaxes(title="Probabilidad acumulada", range=[0, 1.02])
    fig = _estilo(fig, f"Transformada inversa: de un número aleatorio U a un valor de {etiqueta}", 400)
    fig.update_layout(legend=dict(orientation="v", y=0.05, x=0.99, xanchor="right", yanchor="bottom",
                                  bgcolor="rgba(255,255,255,0.85)"))
    return fig


def histograma_costos(costos: np.ndarray, p5: float, p50: float, p95: float,
                      curva: tuple[np.ndarray, np.ndarray] | None = None, titulo: str = "") -> go.Figure:
    """Histograma del costo simulado con la densidad teórica exacta (x, y) y los percentiles."""
    fig = go.Figure()
    fig.add_histogram(x=costos, histnorm="probability density", nbinsx=60, xbins=_clases(costos),
                      marker_color=VERDE, opacity=0.85, name="Costo simulado")
    if curva is not None:
        x, y = curva
        fig.add_scatter(x=x, y=y, mode="lines", line=dict(color=AMBAR, width=3),
                        name="Distribución teórica")
    for valor, etiqueta, color in [(p5, "P5", AZUL), (p50, "P50 (mediana)", GRIS), (p95, "P95", ROJO)]:
        fig.add_vline(x=valor, line=dict(color=color, width=2, dash="dash"),
                      annotation_text=f"{etiqueta}: {valor:,.0f}", annotation_position="top",
                      annotation_font_color=color)
    fig.update_xaxes(title="Costo (USD)")
    fig.update_yaxes(title="Densidad")
    fig = _estilo(fig, titulo, 460)
    fig.update_layout(margin=dict(t=70, b=90), legend=dict(y=-0.2, yanchor="top", x=0.5, xanchor="center"))
    return fig


def grafico_convergencia(conv, valor_teorico: float) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=conv["k"], y=conv["superior"], mode="lines", line=dict(width=0),
                    showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=conv["k"], y=conv["inferior"], mode="lines", line=dict(width=0),
                    fill="tonexty", fillcolor="rgba(15,118,110,0.15)",
                    name="Banda ±1.96·s/√k (por el TLC)", hoverinfo="skip")
    fig.add_scatter(x=conv["k"], y=conv["promedio"], mode="lines", line=dict(color=VERDE, width=2),
                    name="Promedio acumulado")
    fig.add_hline(y=valor_teorico, line=dict(color=AMBAR, width=2, dash="dash"),
                  annotation_text=f"Valor teórico {valor_teorico:,.1f}", annotation_font_color=AMBAR,
                  annotation_position="bottom right")
    fig.update_xaxes(title="Número de iteraciones k", type="log")
    fig.update_yaxes(title="Costo promedio (USD)")
    return _estilo(fig, "Convergencia: el promedio se estabiliza al aumentar las iteraciones", 400)


def dispersion_datos(demanda, costo_unit, r: float, etiqueta_x: str = "Demanda (unidades)",
                     etiqueta_y: str = "Costo unitario (USD)") -> go.Figure:
    pendiente, intercepto = np.polyfit(demanda, costo_unit, 1)
    x = np.linspace(min(demanda), max(demanda), 50)
    fig = go.Figure()
    fig.add_scatter(x=demanda, y=costo_unit, mode="markers",
                    marker=dict(color=AZUL, size=10, opacity=0.8, line=dict(color="white", width=1)),
                    name=f"{len(demanda)} datos")
    fig.add_scatter(x=x, y=pendiente * x + intercepto, mode="lines", line=dict(color=ROJO, width=2.5),
                    name=f"Tendencia (r = {r:.3f})")
    fig.update_xaxes(title=etiqueta_x)
    fig.update_yaxes(title=etiqueta_y)
    return _estilo(fig, f"{etiqueta_x} vs. {etiqueta_y}", 380)


def comparar_modelos(costos_guia, costos_corr, p95_guia, p95_corr) -> go.Figure:
    fig = go.Figure()
    fig.add_histogram(x=costos_guia, histnorm="probability density", nbinsx=70, xbins=_clases(costos_guia, 60),
                      marker_color=GRIS, opacity=0.55, name="Modelo de la guía (independiente)")
    fig.add_histogram(x=costos_corr, histnorm="probability density", nbinsx=70,
                      marker_color=VERDE, opacity=0.7, name="Modelo con correlación")
    fig.add_vline(x=p95_guia, line=dict(color=GRIS, dash="dash", width=2),
                  annotation_text=f"P95 guía: {p95_guia:,.0f}", annotation_position="top right")
    fig.add_vline(x=p95_corr, line=dict(color=VERDE, dash="dash", width=2),
                  annotation_text=f"P95 correlación: {p95_corr:,.0f}", annotation_position="top left")
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Costo (USD)")
    fig.update_yaxes(title="Densidad")
    return _estilo(fig, "Ignorar la correlación exagera la incertidumbre del costo", 420)


def comparar_distribuciones(dists: dict, costo_unit: float, titulo: str) -> go.Figure:
    """Densidad del costo con cada distribución (misma media y desviación, distinta forma)."""
    colores = [AZUL, VERDE, AMBAR, ROJO]
    fig = go.Figure()
    for (nombre, dist), color in zip(dists.items(), colores):
        lo, hi = dist.ppf(0.001), dist.ppf(0.999)
        x = np.linspace(lo, hi, 400)
        fig.add_scatter(x=x * costo_unit, y=dist.pdf(x) / costo_unit, mode="lines",
                        line=dict(color=color, width=2.6), name=nombre)
    fig.update_xaxes(title="Costo (USD)")
    fig.update_yaxes(title="Densidad")
    return _estilo(fig, titulo, 400)


def sesgo_excel(promedios_g: np.ndarray, media_hist: float) -> go.Figure:
    fig = go.Figure()
    fig.add_histogram(x=promedios_g, nbinsx=40, marker_color=ROJO, opacity=0.75,
                      name="Promedio de la columna G en cada F9")
    fig.add_vline(x=media_hist, line=dict(color=AZUL, width=3),
                  annotation_text=f"Media histórica real: {media_hist:.1f}", annotation_font_color=AZUL)
    fig.add_vline(x=float(np.mean(promedios_g)), line=dict(color=ROJO, width=2, dash="dash"),
                  annotation_text=f"Promedio con la fórmula del Excel: {np.mean(promedios_g):.1f}",
                  annotation_position="top left", annotation_font_color=ROJO)
    fig.update_xaxes(title="Demanda simulada promedio (unidades)")
    fig.update_yaxes(title="Frecuencia")
    return _estilo(fig, "La fórmula del Excel subestima la demanda en TODOS los recálculos", 380)


def error_vs_N(filas) -> go.Figure:
    N = np.array([f["N"] for f in filas])
    fig = go.Figure()
    NN = np.logspace(np.log10(N.min()), np.log10(N.max()), 200)
    s = filas[0]["sigma"]
    fig.add_scatter(x=NN, y=s / np.sqrt(NN), mode="lines", line=dict(color=AMBAR, width=3),
                    name="Teoría (TLC): σ / √N")
    fig.add_scatter(x=N, y=[f["desv_obs"] for f in filas], mode="markers",
                    marker=dict(color=VERDE, size=12, line=dict(color="white", width=1.5)),
                    name="Observado: desviación de los promedios")
    fig.update_xaxes(title="Iteraciones por simulación N", type="log")
    fig.update_yaxes(title="Error típico del promedio (USD)", type="log")
    return _estilo(fig, "El error de Monte Carlo baja exactamente como predice el TLC", 400)
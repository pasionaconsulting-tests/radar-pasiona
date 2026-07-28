# -*- coding: utf-8 -*-
"""
Radar de Licitaciones · Demo en vivo
Pasiona Consulting · Comunicación y Marketing

Esta demo se CONECTA EN VIVO a fuentes oficiales de contratación pública:
  - Catalunya  -> Datos Abiertos Generalitat (Plataforma de Serveis de
                  Contractació Pública, PSCP)  [API Socrata, JSON]
  - Estado      -> PLACSP (nota: la sindicación estatal se sirve en ZIP/ATOM
                  anuales; en esta demo se documenta y se deja preparada la vía,
                  priorizando la fuente catalana que permite consulta en vivo)

No usa datos ficticios: todo lo que se muestra viene de la fuente oficial en
el momento de abrir la app.

Coste de infraestructura: 0 €  (Streamlit Community Cloud + API pública)

Autora: Dori Portales · Julio 2026
"""

import datetime as dt
import requests
import pandas as pd
import streamlit as st

# ────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Radar de Licitaciones · Pasiona",
    page_icon="🛰️",
    layout="wide",
)

# Endpoint oficial · Datos Abiertos de Catalunya (dataset PSCP: ybgg-dgi6)
# Formato Socrata -> admite filtros SoQL en vivo ($where, $q, $order, $limit)
API_PSCP = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"

# Página pública del expediente (Catalunya) para construir el enlace clicable
DETALLE_PSCP = "https://contractaciopublica.cat/ca/detall-publicacio/{}"

# ── Criterios Pasiona ────────────────────────────────────────────────────────
# CPVs del sector TIC donde Pasiona tiene equipo real (prefijos).
# 72 = Servicios TI; 48 = Paquetes de software; 71356 = servicios técnicos
CPV_PASIONA = ("72", "48", "71356")

# Importe mínimo (sin IVA) para que una licitación resulte interesante.
IMPORTE_MIN_DEFECTO = 30000

# Tipos de contrato que encajan con el modelo (talento IT / servicios).
TIPOS_OK = ("serv",)  # "serveis" / "servicios"

# Posibles nombres de campo en el dataset (defensivo: el esquema puede variar).
CAMPOS_IMPORTE = [
    "pressupost_licitacio_sense", "pressupost_base_licitacio_sense_iva",
    "pressupost_licitacio_amb", "valor_estimat_contracte", "import_adjudicacio_sense",
    "pressupost", "import",
]
CAMPOS_CPV = ["codi_cpv", "cpv", "codis_cpv"]
CAMPOS_OBJETO = ["denominacio", "objecte_contracte", "objecte"]
CAMPOS_ORGANO = ["nom_organ", "nom_departament_ens", "nom_ambit"]
CAMPOS_FECHA = [
    "data_publicacio_anunci", "data_publicacio", "data_publicacio_anunci_licitacio",
]
CAMPOS_PLAZO = [
    "termini_presentacio_ofertes", "data_fi_presentacio_ofertes",
    "data_limit_presentacio", "termini",
]
CAMPOS_URL = ["enllac_publicacio", "enllac", "url_publicacio"]
CAMPOS_EXPEDIENTE = ["codi_expedient", "expedient"]
CAMPO_FASE = "fase_publicacio"
CAMPO_TIPUS = "tipus_contracte"


# ────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ────────────────────────────────────────────────────────────────────────────

def primer_campo(fila: dict, candidatos) -> str:
    """Devuelve el nombre del primer campo existente en la fila."""
    for c in candidatos:
        if c in fila:
            return c
    return ""


@st.cache_data(ttl=1800, show_spinner=False)
def cargar_licitaciones(limit: int = 400) -> pd.DataFrame:
    """
    Descarga EN VIVO las últimas publicaciones de la PSCP (Catalunya).
    Prioriza anuncios de licitación de tipo 'servicios', que son los que
    encajan con el modelo de Pasiona.
    """
    # SoQL: pedimos los registros más recientes que sean anuncios de licitación.
    params = {
        "$limit": limit,
        "$order": ":id DESC",
        # Filtro amplio para no quedarnos sin resultados si cambia la fase.
        "$q": "licitaci",
    }
    r = requests.get(API_PSCP, params=params, timeout=30,
                     headers={"User-Agent": "RadarPasiona/1.0 (demo)"})
    r.raise_for_status()
    datos = r.json()
    if not datos:
        return pd.DataFrame()
    return pd.DataFrame(datos)


def clasificar(fila: dict, campo_cpv: str, campo_importe: str,
               importe_min: float) -> str:
    """Semáforo Pasiona: 🟢 Presentar / 🟡 Dudoso / 🔴 Descartar."""
    cpv = str(fila.get(campo_cpv, "") or "")
    tipus = str(fila.get(CAMPO_TIPUS, "") or "").lower()

    try:
        importe = float(fila.get(campo_importe, 0) or 0)
    except (ValueError, TypeError):
        importe = 0.0

    cpv_ok = cpv.startswith(CPV_PASIONA)
    tipus_ok = any(t in tipus for t in TIPOS_OK)
    importe_ok = importe >= importe_min

    if cpv_ok and tipus_ok and importe_ok:
        return "🟢 Presentar"
    if cpv_ok or (tipus_ok and importe_ok):
        return "🟡 Dudoso"
    return "🔴 Descartar"


def fmt_euro(v) -> str:
    try:
        return f"{float(v):,.0f} €".replace(",", ".")
    except (ValueError, TypeError):
        return "—"


# ────────────────────────────────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────────────────────────────────

st.title("🛰️ Radar de Licitaciones")
st.caption(
    "Demo conectada **en vivo** a fuentes oficiales de contratación pública · "
    "Pasiona Consulting · Coste de infraestructura: 0 €"
)

with st.sidebar:
    st.header("⚙️ Filtros")
    importe_min = st.number_input(
        "Importe mínimo (sin IVA, €)",
        min_value=0, value=IMPORTE_MIN_DEFECTO, step=5000,
    )
    palabra = st.text_input("Buscar por palabra clave (objeto)", "")
    solo_verdes = st.checkbox("Mostrar solo 🟢 Presentar", value=False)
    n_registros = st.slider("Registros a analizar", 100, 1000, 400, step=100)
    st.divider()
    st.markdown(
        "**Fuente oficial**\n\n"
        "Datos Abiertos de la Generalitat de Catalunya · "
        "Plataforma de Serveis de Contractació Pública (PSCP). "
        "Actualización diaria."
    )

# ── Carga en vivo ────────────────────────────────────────────────────────────
try:
    with st.spinner("Conectando con la fuente oficial y descargando licitaciones…"):
        df = cargar_licitaciones(limit=n_registros)
except Exception as e:  # noqa: BLE001
    st.error(
        "No se ha podido conectar con la fuente oficial en este momento. "
        "El servicio de datos abiertos puede estar en mantenimiento. "
        f"\n\nDetalle técnico: {e}"
    )
    st.stop()

if df.empty:
    st.warning("La fuente oficial no ha devuelto registros ahora mismo. "
               "Prueba de nuevo en unos minutos.")
    st.stop()

# ── Detección dinámica de columnas ───────────────────────────────────────────
muestra = df.iloc[0].to_dict()
c_importe = primer_campo(muestra, CAMPOS_IMPORTE)
c_cpv = primer_campo(muestra, CAMPOS_CPV)
c_objeto = primer_campo(muestra, CAMPOS_OBJETO)
c_organo = primer_campo(muestra, CAMPOS_ORGANO)
c_fecha = primer_campo(muestra, CAMPOS_FECHA)
c_plazo = primer_campo(muestra, CAMPOS_PLAZO)
c_url = primer_campo(muestra, CAMPOS_URL)
c_exp = primer_campo(muestra, CAMPOS_EXPEDIENTE)

# ── Clasificación semáforo ───────────────────────────────────────────────────
df["Clasificación"] = df.apply(
    lambda f: clasificar(f, c_cpv, c_importe, importe_min), axis=1
)

# ── Filtros de interfaz ──────────────────────────────────────────────────────
vista = df.copy()
if palabra and c_objeto:
    vista = vista[vista[c_objeto].astype(str).str.contains(palabra, case=False, na=False)]
if solo_verdes:
    vista = vista[vista["Clasificación"] == "🟢 Presentar"]

# ── Métricas ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Analizadas", len(df))
col2.metric("🟢 Presentar", int((df["Clasificación"] == "🟢 Presentar").sum()))
col3.metric("🟡 Dudosas", int((df["Clasificación"] == "🟡 Dudoso").sum()))
col4.metric("🔴 Descartar", int((df["Clasificación"] == "🔴 Descartar").sum()))

st.caption(
    f"Última consulta: {dt.datetime.now():%d/%m/%Y %H:%M} · "
    f"{len(vista)} licitaciones mostradas tras aplicar filtros."
)

# ── Tabla de resultados ──────────────────────────────────────────────────────
columnas_mostrar = {}
if c_objeto:
    columnas_mostrar[c_objeto] = "Objeto del contrato"
if c_organo:
    columnas_mostrar[c_organo] = "Organismo"
if CAMPO_TIPUS in vista.columns:
    columnas_mostrar[CAMPO_TIPUS] = "Tipo"
if c_cpv:
    columnas_mostrar[c_cpv] = "CPV"
if c_importe:
    columnas_mostrar[c_importe] = "Importe (sin IVA)"
if c_fecha:
    columnas_mostrar[c_fecha] = "Publicación"
if c_plazo:
    columnas_mostrar[c_plazo] = "Plazo"

tabla = vista[["Clasificación"] + list(columnas_mostrar.keys())].copy()
tabla = tabla.rename(columns=columnas_mostrar)

if "Importe (sin IVA)" in tabla.columns:
    tabla["Importe (sin IVA)"] = tabla["Importe (sin IVA)"].apply(fmt_euro)

# Enlace clicable al expediente oficial
if c_url and c_url in vista.columns:
    tabla["Expediente"] = vista[c_url].astype(str)
elif c_exp and c_exp in vista.columns:
    tabla["Expediente"] = vista[c_exp].astype(str).apply(
        lambda x: DETALLE_PSCP.format(x)
    )

st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Expediente": st.column_config.LinkColumn("Expediente", display_text="Abrir ↗"),
    },
)

# ── Descarga ─────────────────────────────────────────────────────────────────
st.download_button(
    "⬇️ Descargar resultados (CSV)",
    data=tabla.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"radar_licitaciones_{dt.date.today():%Y%m%d}.csv",
    mime="text/csv",
)

with st.expander("ℹ️ Sobre esta demo y su hoja de ruta"):
    st.markdown(
        """
        **Qué SÍ hace esta demo (en vivo, coste 0 €):**
        - Se conecta a la fuente oficial (Datos Abiertos Generalitat · PSCP) y
          descarga licitaciones reales en el momento.
        - Filtra por los criterios de Pasiona (CPV del sector TIC, tipo de
          contrato e importe mínimo).
        - Clasifica cada licitación en semáforo 🟢 / 🟡 / 🔴.
        - Permite buscar, filtrar y descargar los resultados.

        **Qué NO hace todavía (fase de producto):**
        - Valoración "inteligente" con criterio experto de cada pliego (IA).
        - Lectura y análisis de los documentos técnicos (PCAP/PPT).
        - Memoria de decisiones previas de Dirección.
        - Cobertura completa del Estado (PLACSP se sirve en ZIP/ATOM anuales;
          se integra en la siguiente fase).
        - Generación automática de informe y correo para Dirección.
        """
    )

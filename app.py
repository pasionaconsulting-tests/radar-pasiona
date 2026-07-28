# -*- coding: utf-8 -*-
"""
🛰️ RADAR DE LICITACIONES AAPP · PASIONA
Demo conectada EN VIVO a la fuente oficial de contratación pública de Catalunya
(Datos Abiertos Generalitat · Plataforma de Serveis de Contractació Pública).

FILTROS PASIONA (definidos por Dirección y Talent):
  · Umbral económico (Ernest Pagès): mínimo 50.000 € · techo 300.000 € / SARA
  · Capacidades reales (Txema Salabert): LISTA BLANCA de 5 áreas
       1. Desarrollo con IA (Claude, GitHub)
       2. Desarrollo .NET
       3. Servicios UX
       4. Servicios Agile
       5. Consultoría IA
    Todo lo que quede fuera de estas capacidades → FUERA DE RADAR.

Clasificación en 4 categorías CON MOTIVO:
   🟢 PRESENTAR · 🟡 DUDOSO · ⚪ DESCARTAR · 🔴 FUERA DE RADAR

Coste de infraestructura: 0 €
Autora: Dori Portales · Pasiona Consulting · 2026
"""

import datetime as dt
import requests
import pandas as pd
import streamlit as st

# ────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Radar de Licitaciones · Pasiona",
                   page_icon="🛰️", layout="wide")

API_PSCP = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
DETALLE_PSCP = "https://contractaciopublica.cat/ca/detall-publicacio/{}"

# ── FILTROS PASIONA · Umbral económico (Ernest Pagès, 06/07/2026) ────────────
IMPORTE_MIN = 50000       # < 50k € → FUERA (poco margen, mucho trabajo)
IMPORTE_MAX = 300000      # > 300k € → DUDOSO (suelen estar preasignadas)
SARA_SERVICIOS = 221000   # umbral SARA de servicios

# ── FILTROS PASIONA · Capacidades reales (Txema Salabert, 06/07/2026) ────────
# LISTA BLANCA: palabras clave de las 5 áreas donde Pasiona SÍ tiene capacidad.
LISTA_BLANCA = {
    "Desarrollo con IA": [
        "intel·ligència artificial", "inteligencia artificial", " ia ", "ia)",
        "machine learning", "aprenentatge automàtic", "llm", "gpt", "copilot",
        "claude", "github", "generativa", "generatiu", "chatbot", "agents inteligentes",
        "agents intel", "rag ",
    ],
    "Desarrollo .NET": [
        ".net", "dotnet", "c#", "asp.net", "blazor", "desenvolupament d'aplicacions",
        "desarrollo de aplicaciones", "desenvolupament de programari",
        "desarrollo de software", "aplicació web", "aplicación web",
        "aplicacions a mida", "aplicaciones a medida", "desenvolupament web",
        "desarrollo web", "api", "microserv",
    ],
    "Servicios UX": [
        "ux", "ui", "experiència d'usuari", "experiencia de usuario",
        "usabilitat", "usabilidad", "disseny centrat", "diseño centrado",
        "accessibilitat", "accesibilidad", "prototip", "prototipo",
        "disseny de servei", "diseño de servicio",
    ],
    "Servicios Agile": [
        "agile", "àgil", "ágil", "scrum", "kanban", "safe", "less",
        "transformació àgil", "transformación ágil", "coaching", "facilitació",
        "metodologia àgil", "metodología ágil",
    ],
    "Consultoría IA": [
        "consultoria", "consultoría", "assessorament", "asesoramiento",
        "estratègia digital", "estrategia digital", "transformació digital",
        "transformación digital", "adopció", "adopción", "governança",
        "gobernanza", "maduresa", "madurez", "roadmap", "diagnòstic", "diagnóstico",
    ],
}

# ── Tecnologías / ámbitos DESCARTADOS por Dirección (→ FUERA) ─────────────────
DESCARTADAS = {
    "Oracle": ["oracle", "rac", "data guard"],
    "Java/Spring": ["java", "spring", "j2ee", "jakarta"],
    "SAP": ["sap", "s/4hana", "abap"],
    "Cloud/Infra con partnership": ["azure", "aws", "cloud microsoft", "office 365",
                                     "microsoft 365", "m365", "vmware", "citrix"],
    "Producto cerrado sin partnership": ["dspace", "trustedx", "jira", "atlassian",
                                         "confluence", "sharepoint", "liferay",
                                         "drupal", "wordpress", "sitecore"],
    "Microinformática/Helpdesk": ["microinformàtica", "microinformatica", "helpdesk",
                                   "help desk", "cau ", "suport a usuari", "soporte a usuario",
                                   "parc informàtic", "parque informático", "puestos de trabajo"],
    "Infraestructura/Redes/Seguridad ops": ["xarxa", "red de comunicaciones", "cablejat",
                                            "cableado", "electrònica de xarxa", "firewall",
                                            "servidors", "servidores", "datacenter",
                                            "cpd", "backup", "còpies de seguretat"],
    "ERP/Business Central/Dynamics": ["business central", "dynamics", "navision", "erp",
                                      "sage", "a3"],
}

# ── Patrones NO-TIC (→ FUERA por sector) ─────────────────────────────────────
NO_TIC = {
    "Obra civil / arquitectura": ["obra", "obres", "edifici", "edificio", "construcció",
                                  "construcción", "arquitect", "enginyeria civil",
                                  "ingeniería civil", "urbanització", "pont", "puente",
                                  "carretera", "paviment", "estació regeneradora",
                                  "estación regeneradora", "clavegueram", "sanejament"],
    "Suministro / material": ["subministrament", "suministro", "adquisició", "adquisición",
                              "compra de", "mobiliari", "mobiliario", "vehicle", "vehículo"],
    "Servicios no técnicos": ["neteja", "limpieza", "vigilància", "vigilancia", "seguretat privada",
                             "seguridad privada", "catering", "restauració", "jardineria",
                             "jardinería", "transport", "transporte", "assegurança", "seguro",
                             "mostreig", "muestreo", "anàlisi de laboratori", "laboratorio",
                             "formació no", "protecció de dades", "protección de datos",
                             "delegat de protecció", "delegado de protección"],
}


# ────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ────────────────────────────────────────────────────────────────────────────
def primer_campo(fila: dict, candidatos) -> str:
    for c in candidatos:
        if c in fila:
            return c
    return ""


CAMPOS_IMPORTE = ["pressupost_licitacio_sense", "pressupost_base_licitacio_sense_iva",
                  "valor_estimat_contracte", "pressupost_licitacio_amb", "pressupost", "import"]
CAMPOS_OBJETO = ["objecte_contracte", "denominacio", "objecte"]
CAMPOS_ORGANO = ["nom_organ", "nom_departament_ens", "nom_ambit"]
CAMPOS_FECHA = ["data_publicacio_anunci", "data_publicacio"]
CAMPOS_PLAZO = ["termini_presentacio_ofertes", "data_fi_presentacio_ofertes"]
CAMPOS_URL = ["enllac_publicacio", "enllac", "url_publicacio"]
CAMPOS_EXP = ["codi_expedient", "expedient"]
CAMPOS_CPV = ["codi_cpv", "cpv"]
CAMPO_TIPUS = "tipus_contracte"


@st.cache_data(ttl=1800, show_spinner=False)
def cargar(limite: int) -> pd.DataFrame:
    """
    Descarga robusta desde la fuente oficial (PSCP Catalunya).
    Prueba varias estrategias de consulta y se queda con la primera que
    devuelva registros, para no quedarse nunca en blanco.
    """
    headers = {"User-Agent": "RadarPasiona/2.1"}
    intentos = [
        {"$limit": limite, "$order": ":id DESC"},                       # 1) últimas publicaciones
        {"$limit": limite},                                              # 2) sin orden (más permisiva)
        {"$limit": limite, "$order": "data_publicacio_anunci DESC"},     # 3) por fecha de anuncio
    ]
    ultimo_error = None
    for params in intentos:
        try:
            r = requests.get(API_PSCP, params=params, timeout=45, headers=headers)
            r.raise_for_status()
            datos = r.json()
            if datos:
                return pd.DataFrame(datos)
        except Exception as e:  # noqa: BLE001
            ultimo_error = e
            continue
    if ultimo_error:
        raise ultimo_error
    return pd.DataFrame()


def num(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def detecta(texto: str, grupos: dict):
    """Devuelve (nombre_grupo, palabra) del primer grupo que aparezca en el texto."""
    t = f" {texto.lower()} "
    for nombre, palabras in grupos.items():
        for p in palabras:
            if p in t:
                return nombre, p
    return None, None


def clasificar(fila: dict, c_obj: str, c_imp: str) -> tuple[str, str, str]:
    """
    Aplica los FILTROS PASIONA.
    Devuelve: (categoría, área/motivo-capacidad, motivo-detallado)
    """
    objeto = str(fila.get(c_obj, "") or "")
    importe = num(fila.get(c_imp, 0))

    # 1) ¿Es de un ámbito NO-TIC? → FUERA por sector
    sector, _ = detecta(objeto, NO_TIC)
    if sector:
        return "🔴 FUERA", "—", f"No-TIC · {sector}"

    # 2) ¿Tecnología descartada por Dirección? → FUERA por capacidad
    desc, palabra = detecta(objeto, DESCARTADAS)
    if desc:
        return "🔴 FUERA", "—", f"Fuera de capacidades Pasiona · {desc}"

    # 3) ¿Encaja en la LISTA BLANCA de capacidades? (Filtro Pasiona · Txema)
    area, _ = detecta(objeto, LISTA_BLANCA)

    # 4) Filtro económico (Filtro Pasiona · Ernest)
    if importe and importe < IMPORTE_MIN:
        motivo = f"Importe {importe:,.0f}€ < mínimo 50.000€ (poco margen)".replace(",", ".")
        return "⚪ DESCARTAR", (area or "—"), motivo
    if importe > IMPORTE_MAX:
        motivo = f"Importe {importe:,.0f}€ > 300.000€ (suelen ir a grandes)".replace(",", ".")
        cat = "🟡 DUDOSO" if area else "🔴 FUERA"
        return cat, (area or "—"), motivo

    # 5) Decisión según capacidad + economía
    if area:
        if importe == 0:
            return "🟡 DUDOSO", area, f"Encaja en {area}, pero sin importe publicado (verificar)"
        franja = "A" if importe < 80000 else ("B" if importe < 150000 else "C")
        if importe >= SARA_SERVICIOS:
            return "🟡 DUDOSO", area, f"Encaja en {area} · zona SARA ({importe:,.0f}€): verificar".replace(",", ".")
        return "🟢 PRESENTAR", area, f"Capacidad Pasiona: {area} · franja {franja} ({importe:,.0f}€)".replace(",", ".")

    # 6) No encaja en ninguna capacidad Pasiona
    return "🔴 FUERA", "—", "No encaja en las 5 capacidades Pasiona (lista blanca)"


def fmt_eur(v) -> str:
    n = num(v)
    return f"{n:,.0f} €".replace(",", ".") if n else "—"


# ────────────────────────────────────────────────────────────────────────────
# CABECERA
# ────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:#EA7600;padding:22px 28px;border-radius:10px;margin-bottom:6px;">
      <div style="color:white;font-size:30px;font-weight:800;">🛰️ Radar de Licitaciones AAPP · Pasiona</div>
      <div style="color:white;font-size:14px;margin-top:6px;">
        Conectado <b>en vivo</b> a la fuente oficial · Plataforma de Serveis de Contractació Pública
        (Generalitat de Catalunya) · Coste de infraestructura: 0 €
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Parámetros del barrido")
    n_reg = st.slider("Publicaciones a analizar", 100, 1000, 400, step=100)
    st.divider()
    st.subheader("🔍 Filtros de vista")
    palabra = st.text_input("Buscar en el objeto del contrato", "")
    cats_sel = st.multiselect(
        "Mostrar categorías",
        ["🟢 PRESENTAR", "🟡 DUDOSO", "⚪ DESCARTAR", "🔴 FUERA"],
        default=["🟢 PRESENTAR", "🟡 DUDOSO"],
    )
    st.divider()
    st.markdown(
        "**FILTROS PASIONA aplicados**\n\n"
        "**Económico (Ernest Pagès):** mínimo **50.000 €**, techo 300.000 € / SARA.\n\n"
        "**Capacidades (Txema Salabert):** solo estas 5 áreas —\n"
        "1. Desarrollo con IA (Claude, GitHub)\n"
        "2. Desarrollo .NET\n"
        "3. Servicios UX\n"
        "4. Servicios Agile\n"
        "5. Consultoría IA\n\n"
        "_El resto queda FUERA (sin capacidad para abordarlo)._\n\n"
        "**Fuente oficial:** Datos Abiertos Generalitat · PSCP. Ámbito: Catalunya. "
        "El Estado (PLACSP) se integra en la siguiente fase."
    )

# ── Carga ────────────────────────────────────────────────────────────────────
try:
    with st.spinner("Conectando con la fuente oficial y aplicando Filtros Pasiona…"):
        df = cargar(n_reg)
except Exception as e:  # noqa: BLE001
    st.error(f"No se ha podido conectar con la fuente oficial ahora mismo. Detalle: {e}")
    st.stop()

if df.empty:
    st.warning("La fuente oficial no ha devuelto registros. Prueba de nuevo en unos minutos.")
    st.stop()

muestra = df.iloc[0].to_dict()
c_imp = primer_campo(muestra, CAMPOS_IMPORTE)
c_obj = primer_campo(muestra, CAMPOS_OBJETO)
c_org = primer_campo(muestra, CAMPOS_ORGANO)
c_fec = primer_campo(muestra, CAMPOS_FECHA)
c_pla = primer_campo(muestra, CAMPOS_PLAZO)
c_url = primer_campo(muestra, CAMPOS_URL)
c_exp = primer_campo(muestra, CAMPOS_EXP)
c_cpv = primer_campo(muestra, CAMPOS_CPV)

res = df.apply(lambda f: clasificar(f, c_obj, c_imp), axis=1, result_type="expand")
df["Categoría"] = res[0]
df["Capacidad"] = res[1]
df["Motivo"] = res[2]

# ── Métricas ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
tot = len(df)
for col, etiqueta, cat, color in [
    (c1, "Publicaciones", None, "#252525"),
    (c2, "🟢 Presentar", "🟢 PRESENTAR", "#28a745"),
    (c3, "🟡 Dudoso", "🟡 DUDOSO", "#f0a500"),
    (c4, "⚪ Descartar", "⚪ DESCARTAR", "#8a8d91"),
    (c5, "🔴 Fuera", "🔴 FUERA", "#dc3545"),
]:
    valor = tot if cat is None else int((df["Categoría"] == cat).sum())
    col.markdown(
        f"""<div style="background:{color};padding:16px;border-radius:10px;text-align:center;">
        <div style="color:white;font-size:28px;font-weight:800;">{valor}</div>
        <div style="color:white;font-size:12px;">{etiqueta}</div></div>""",
        unsafe_allow_html=True,
    )

st.caption(
    f"Barrido en vivo · {dt.datetime.now():%d/%m/%Y %H:%M} · fuente oficial PSCP Catalunya · "
    "clasificación según Filtros Pasiona (Ernest + Txema)"
)

# ── Filtros de vista ─────────────────────────────────────────────────────────
vista = df[df["Categoría"].isin(cats_sel)].copy()
if palabra and c_obj:
    vista = vista[vista[c_obj].astype(str).str.contains(palabra, case=False, na=False)]

# ── Tabla ────────────────────────────────────────────────────────────────────
cols = {"Categoría": "Categoría", "Capacidad": "Capacidad Pasiona", "Motivo": "Motivo"}
if c_obj:
    cols[c_obj] = "Objeto del contrato"
if c_org:
    cols[c_org] = "Organismo"
if c_imp:
    cols[c_imp] = "Importe (sin IVA)"
if c_pla:
    cols[c_pla] = "Plazo"

tabla = vista[list(cols.keys())].rename(columns=cols)
if "Importe (sin IVA)" in tabla.columns:
    tabla["Importe (sin IVA)"] = tabla["Importe (sin IVA)"].apply(fmt_eur)

if c_url and c_url in vista.columns:
    tabla["Expediente"] = vista[c_url].astype(str)
elif c_exp and c_exp in vista.columns:
    tabla["Expediente"] = vista[c_exp].astype(str).apply(lambda x: DETALLE_PSCP.format(x))

st.dataframe(
    tabla, use_container_width=True, hide_index=True,
    column_config={"Expediente": st.column_config.LinkColumn("Expediente", display_text="Abrir ↗")},
)

st.download_button(
    "⬇️ Descargar (CSV)",
    data=tabla.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"radar_pasiona_{dt.date.today():%Y%m%d}.csv",
    mime="text/csv",
)

# ── Explicación ──────────────────────────────────────────────────────────────
with st.expander("ℹ️ Qué hace y qué no hace esta demo"):
    st.markdown(
        """
        **Filtros Pasiona aplicados (definidos por Dirección y Talent):**

        - **Umbral económico (Ernest Pagès):** se descartan las licitaciones por debajo de
          **50.000 €** (poco margen, mucho trabajo) y se marcan como dudosas las que superan
          los 300.000 € (suelen ir a grandes proveedores).
        - **Capacidades reales (Txema Salabert):** solo pasan a PRESENTAR/DUDOSO las
          licitaciones de las **5 áreas** donde Pasiona tiene capacidad real —
          Desarrollo con IA, Desarrollo .NET, Servicios UX, Servicios Agile y Consultoría IA.
          Todo lo demás queda **FUERA**, con su motivo.

        **Categorías:** 🟢 PRESENTAR · 🟡 DUDOSO · ⚪ DESCARTAR · 🔴 FUERA — cada una con
        el motivo por el que se ha clasificado así.

        **Qué NO hace todavía (fase de producto):**
        - Leer el pliego completo (PCAP/PPT) para el matiz fino (perfiles vs proyecto,
          bolsa de horas, solvencia, partnerships exigidos).
        - Memoria de decisiones previas de Dirección.
        - Cobertura del Estado (PLACSP) y otras fuentes.
        - Valoración con IA de cada caso frontera.

        La clasificación se basa en el **objeto del contrato** publicado por la fuente
        oficial. Los casos límite conviene revisarlos con criterio experto.
        """
    )

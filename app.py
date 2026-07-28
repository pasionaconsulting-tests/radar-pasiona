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

Categorías CON MOTIVO:
   🟢 PRESENTAR · 🟡 DUDOSO · 🔵 TIC (bajo importe) · ⚪ DESCARTAR · 🔴 FUERA

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
IMPORTE_MIN = 50000
IMPORTE_MAX = 300000
SARA_SERVICIOS = 221000

# ── FILTROS PASIONA · Capacidades reales (Txema Salabert, 06/07/2026) ────────
LISTA_BLANCA = {
    "Desarrollo con IA": [
        "intel·ligència artificial", "inteligencia artificial",
        "machine learning", "aprenentatge automàtic", "aprendizaje automático",
        "model de llenguatge", "modelo de lenguaje", "llm",
        "copilot", "github copilot", "anthropic", "openai", "chatgpt",
        "ia generativa", "ia generatia", "intel·ligència generativa",
        "generative ai", "chatbot", "agent conversacional",
        "assistent virtual", "asistente virtual",
    ],
    "Desarrollo .NET": [
        ".net", "dotnet", " c# ", "asp.net", "blazor", "entity framework",
        "desenvolupament d'aplicacions", "desarrollo de aplicaciones",
        "desenvolupament de programari", "desarrollo de software",
        "aplicació web", "aplicación web", "aplicacions a mida", "aplicaciones a medida",
        "desenvolupament a mida", "desarrollo a medida",
        "microserveis", "microservicios", "desenvolupament d'api", "desarrollo de api",
    ],
    "Servicios UX": [
        "experiència d'usuari", "experiencia de usuario", " ux ", " ux/ui", "ux/ui",
        "usabilitat", "usabilidad", "disseny centrat en l'usuari",
        "diseño centrado en el usuario", "disseny de serveis digitals",
        "diseño de servicios digitales", "prototipatge", "prototipado",
        "accessibilitat web", "accesibilidad web", "arquitectura de la informació",
    ],
    "Servicios Agile": [
        " agile", "àgil", "ágil", "scrum", "kanban", " safe ", "less framework",
        "transformació àgil", "transformación ágil", "coaching àgil", "coaching ágil",
        "facilitació àgil", "metodologia àgil", "metodología ágil",
        "gestió àgil de projectes", "gestión ágil de proyectos",
    ],
    "Consultoría IA": [
        "consultoria en intel·ligència", "consultoría en inteligencia",
        "estratègia d'intel·ligència artificial", "estrategia de inteligencia artificial",
        "adopció d'ia", "adopción de ia", "governança de dades", "gobernanza de datos",
        "maduresa digital", "madurez digital", "estratègia de dades",
        "estrategia de datos", "roadmap d'ia", "diagnòstic d'ia", "diagnóstico de ia",
    ],
}

# ── Software / TIC genérico (encaja pero sin área concreta) ──────────────────
# Se evalúa DESPUÉS de descartadas/no-tic: captura mantenimientos y plataformas
# digitales que son claramente TIC aunque no se sepa la tecnología exacta.
TIC_GENERICO = [
    "programari", "software", "aplicació", "aplicación", "aplicacions", "aplicaciones",
    "aplicatiu", "aplicativo", "plataforma digital", "portal web", "seu electrònica",
    "sede electrónica", "sistema d'informació", "sistema de información",
    "solució digital", "solución digital", "eina digital", "herramienta digital",
    "manteniment informàtic", "mantenimiento informático", "evolutiu", "evolutivo",
    "digitalització", "digitalización", "transformació digital", "transformación digital",
    "administració electrònica", "administración electrónica",
]

# ── Ámbitos DESCARTADOS por Dirección (→ FUERA) ──────────────────────────────
DESCARTADAS = {
    "Oracle": ["oracle", "data guard", "exadata"],
    "Java/Spring": [" java", "spring boot", "j2ee", "jakarta ee"],
    "SAP": [" sap ", "s/4hana", " abap"],
    "Cloud/Infra con partnership": ["migració a azure", "migración a azure",
                                    "entorn azure", "entorno azure", "amazon web services",
                                    "vmware", "citrix", "nutanix"],
    "Producto cerrado / licencias": ["dspace", "trustedx", " jira", "atlassian",
                                     "confluence", "burp suite", "liferay", "sitecore",
                                     "veeam", "fortinet", "palo alto"],
    "Microinformática/Helpdesk": ["microinformàtica", "microinformatica", "helpdesk",
                                  "help desk", "suport a usuari", "soporte a usuario",
                                  "parc informàtic", "parque informático",
                                  "llocs de treball", "puestos de trabajo",
                                  "equips informàtics", "equipos informáticos"],
    "Infraestructura/Redes/Seguridad ops": ["cablejat", "cableado", "electrònica de xarxa",
                                            "firewall", "servidors físics", "servidores físicos",
                                            "datacenter", "centre de dades", " cpd ",
                                            "còpies de seguretat", "copias de seguridad",
                                            "videovigilància", "videovigilancia"],
    "ERP/Business Central/Dynamics": ["business central", "dynamics", "navision",
                                      " erp ", " sage ", "gestió comptable",
                                      "gestión contable"],
}

# ── Patrones NO-TIC (→ FUERA por sector) ─────────────────────────────────────
NO_TIC = {
    "Obra civil / arquitectura": ["obres ", " obra ", "edifici", "edificio", "construcció",
                                  "construcción", "arquitect", "enginyeria civil",
                                  "ingeniería civil", "urbanitzaci", " pont ", "puente",
                                  "carretera", "paviment", "estació regeneradora",
                                  "estación regeneradora", "clavegueram", "sanejament",
                                  "reparació, conservació", "conservació i manteniment d'element"],
    "Suministro / material": ["subministrament", "suministro", "adquisició de",
                              "adquisición de", "compra de", "mobiliari", "mobiliario",
                              "vehicle", "vehículo", "combustible", "material d'oficina",
                              "adquisició de la pintura", "obra d'art"],
    "Servicios no técnicos": ["neteja", "limpieza", "vigilància", "vigilancia",
                             "seguretat privada", "seguridad privada", "catering",
                             "restauració", "jardineria", "jardinería", "transport de",
                             "transporte de", "assegurança", "seguro de", "mostreig",
                             "muestreo", "anàlisi de laboratori", "laboratori",
                             "protecció de dades", "protección de datos",
                             "delegat de protecció", "delegado de protección",
                             "manteniment dels pianos", "piano", "actuacions forestals",
                             "forestal", "dinamització comunitària", "casal de barri"],
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
CAMPOS_PLAZO = ["termini_presentacio_ofertes", "data_fi_presentacio_ofertes"]
CAMPOS_URL = ["enllac_publicacio", "enllac", "url_publicacio"]
CAMPOS_EXP = ["codi_expedient", "expedient"]


@st.cache_data(ttl=1800, show_spinner=False)
def cargar(limite: int) -> pd.DataFrame:
    headers = {"User-Agent": "RadarPasiona/2.3"}
    intentos = [
        {"$limit": limite, "$order": ":id DESC"},
        {"$limit": limite},
        {"$limit": limite, "$order": "data_publicacio_anunci DESC"},
    ]
    ultimo = None
    for params in intentos:
        try:
            r = requests.get(API_PSCP, params=params, timeout=45, headers=headers)
            r.raise_for_status()
            datos = r.json()
            if datos:
                return pd.DataFrame(datos)
        except Exception as e:  # noqa: BLE001
            ultimo = e
            continue
    if ultimo:
        raise ultimo
    return pd.DataFrame()


def num(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def detecta(texto: str, grupos: dict):
    t = f" {texto.lower()} "
    for nombre, palabras in grupos.items():
        for p in palabras:
            if p in t:
                return nombre, p
    return None, None


def detecta_lista(texto: str, palabras) -> bool:
    t = f" {texto.lower()} "
    return any(p in t for p in palabras)


def clasificar(fila: dict, c_obj: str, c_imp: str) -> tuple[str, str, str]:
    """
    Aplica los FILTROS PASIONA.
    Categorías: 🟢 PRESENTAR · 🟡 DUDOSO · 🔵 TIC (bajo importe) · ⚪ DESCARTAR · 🔴 FUERA
    """
    objeto = str(fila.get(c_obj, "") or "")
    importe = num(fila.get(c_imp, 0))

    # 1) NO-TIC por sector → FUERA
    sector, _ = detecta(objeto, NO_TIC)
    if sector:
        return "🔴 FUERA", "—", f"No-TIC · {sector}"

    # 2) Tecnología descartada por Dirección → FUERA
    desc, _ = detecta(objeto, DESCARTADAS)
    if desc:
        return "🔴 FUERA", "—", f"Fuera de capacidades Pasiona · {desc}"

    # 3) ¿Encaja en una de las 5 áreas de la LISTA BLANCA?
    area, _ = detecta(objeto, LISTA_BLANCA)

    # 3b) Si no encaja en un área concreta, ¿es TIC genérico (software/plataforma)?
    if not area and detecta_lista(objeto, TIC_GENERICO):
        area = "TIC (software/plataforma)"

    if area:
        if importe == 0:
            return "🟡 DUDOSO", area, f"Encaja en {area}, pero sin importe publicado (verificar)"
        if importe < IMPORTE_MIN:
            return "🔵 TIC (bajo importe)", area, \
                f"{area} · importe {importe:,.0f}€ < mínimo 50.000€".replace(",", ".")
        if importe > IMPORTE_MAX:
            return "🟡 DUDOSO", area, \
                f"{area} · importe {importe:,.0f}€ supera 300.000€ (suele ir a grandes)".replace(",", ".")
        if importe >= SARA_SERVICIOS:
            return "🟡 DUDOSO", area, \
                f"{area} · zona SARA ({importe:,.0f}€): verificar PCAP".replace(",", ".")
        franja = "A" if importe < 80000 else ("B" if importe < 150000 else "C")
        return "🟢 PRESENTAR", area, \
            f"Capacidad Pasiona: {area} · franja {franja} ({importe:,.0f}€)".replace(",", ".")

    # 4) No encaja en ninguna capacidad Pasiona
    return "🔴 FUERA", "—", "No encaja en las 5 capacidades Pasiona (lista blanca)"


def fmt_eur(v) -> str:
    n = num(v)
    return f"{n:,.0f} €".replace(",", ".") if n else "—"


def fmt_fecha(v) -> str:
    """Convierte 2026-09-21T14:00:00.000 en 21/09/2026. Vacío/nan → —."""
    s = str(v or "").strip()
    if not s or s.lower() == "nan" or s.lower() == "none":
        return "—"
    if len(s) >= 10 and s[4:5] == "-":
        try:
            return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
        except Exception:  # noqa: BLE001
            return s
    return s


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

with st.sidebar:
    st.header("⚙️ Parámetros del barrido")
    n_reg = st.slider("Publicaciones a analizar", 100, 1000, 400, step=100)
    st.divider()
    st.subheader("🔍 Filtros de vista")
    palabra = st.text_input("Buscar en el objeto del contrato", "")
    cats_sel = st.multiselect(
        "Mostrar categorías",
        ["🟢 PRESENTAR", "🟡 DUDOSO", "🔵 TIC (bajo importe)", "⚪ DESCARTAR", "🔴 FUERA"],
        default=["🟢 PRESENTAR", "🟡 DUDOSO", "🔵 TIC (bajo importe)"],
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
c_pla = primer_campo(muestra, CAMPOS_PLAZO)
c_url = primer_campo(muestra, CAMPOS_URL)
c_exp = primer_campo(muestra, CAMPOS_EXP)

res = df.apply(lambda f: clasificar(f, c_obj, c_imp), axis=1, result_type="expand")
df["Categoría"] = res[0]
df["Capacidad"] = res[1]
df["Motivo"] = res[2]

cols = st.columns(6)
tot = len(df)
metricas = [
    ("Publicaciones", None, "#252525"),
    ("🟢 Presentar", "🟢 PRESENTAR", "#28a745"),
    ("🟡 Dudoso", "🟡 DUDOSO", "#f0a500"),
    ("🔵 TIC baja", "🔵 TIC (bajo importe)", "#2b7de9"),
    ("⚪ Descartar", "⚪ DESCARTAR", "#8a8d91"),
    ("🔴 Fuera", "🔴 FUERA", "#dc3545"),
]
for col, (etq, cat, color) in zip(cols, metricas):
    valor = tot if cat is None else int((df["Categoría"] == cat).sum())
    col.markdown(
        f"""<div style="background:{color};padding:14px;border-radius:10px;text-align:center;">
        <div style="color:white;font-size:26px;font-weight:800;">{valor}</div>
        <div style="color:white;font-size:11px;">{etq}</div></div>""",
        unsafe_allow_html=True,
    )

st.caption(
    f"Barrido en vivo · {dt.datetime.now():%d/%m/%Y %H:%M} · fuente oficial PSCP Catalunya · "
    "clasificación según Filtros Pasiona (Ernest + Txema)"
)

n_verde = int((df["Categoría"] == "🟢 PRESENTAR").sum())
n_tic = int((df["Categoría"] == "🔵 TIC (bajo importe)").sum())
if n_verde == 0:
    st.info(
        f"ℹ️ Hoy no hay licitaciones **🟢 PRESENTAR** en Catalunya que cumplan capacidad Pasiona "
        f"**y** importe ≥ 50.000 €. Se han detectado **{n_tic}** licitaciones TIC de nuestras "
        f"áreas por debajo del mínimo económico (categoría 🔵). El radar ha cribado {tot} "
        f"publicaciones en segundos."
    )

vista = df[df["Categoría"].isin(cats_sel)].copy()
if palabra and c_obj:
    vista = vista[vista[c_obj].astype(str).str.contains(palabra, case=False, na=False)]

cols_map = {"Categoría": "Categoría", "Capacidad": "Capacidad Pasiona", "Motivo": "Motivo"}
if c_obj:
    cols_map[c_obj] = "Objeto del contrato"
if c_org:
    cols_map[c_org] = "Organismo"
if c_imp:
    cols_map[c_imp] = "Importe (sin IVA)"
if c_pla:
    cols_map[c_pla] = "Plazo"

tabla = vista[list(cols_map.keys())].rename(columns=cols_map)
if "Importe (sin IVA)" in tabla.columns:
    tabla["Importe (sin IVA)"] = tabla["Importe (sin IVA)"].apply(fmt_eur)
if "Plazo" in tabla.columns:
    tabla["Plazo"] = tabla["Plazo"].apply(fmt_fecha)

if c_url and c_url in vista.columns:
    tabla["Expediente"] = vista[c_url].astype(str)
elif c_exp and c_exp in vista.columns:
    tabla["Expediente"] = vista[c_exp].astype(str).apply(lambda x: DETALLE_PSCP.format(x))

if vista.empty:
    st.success("✅ No hay licitaciones en las categorías seleccionadas con los filtros actuales. "
               "Prueba a marcar también ⚪ DESCARTAR y 🔴 FUERA para ver todo lo cribado.")
else:
    st.dataframe(
        tabla, use_container_width=True, hide_index=True,
        column_config={
            "Objeto del contrato": st.column_config.TextColumn("Objeto del contrato", width="large"),
            "Motivo": st.column_config.TextColumn("Motivo", width="medium"),
            "Expediente": st.column_config.LinkColumn("Expediente", display_text="Abrir ↗"),
        },
    )

st.download_button(
    "⬇️ Descargar (CSV)",
    data=tabla.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"radar_pasiona_{dt.date.today():%Y%m%d}.csv",
    mime="text/csv",
)

with st.expander("ℹ️ Qué hace y qué no hace esta demo"):
    st.markdown(
        """
        **Filtros Pasiona aplicados (definidos por Dirección y Talent):**

        - **Umbral económico (Ernest Pagès):** por debajo de **50.000 €** no resulta rentable;
          por encima de 300.000 € suele ir a grandes proveedores.
        - **Capacidades reales (Txema Salabert):** solo pasan a 🟢/🟡 las licitaciones de las
          **5 áreas** donde Pasiona tiene capacidad real (Desarrollo con IA, Desarrollo .NET,
          Servicios UX, Servicios Agile y Consultoría IA). El resto queda 🔴 FUERA.

        **Las 5 categorías:**
        - 🟢 **PRESENTAR** — encaja en capacidad e importe.
        - 🟡 **DUDOSO** — encaja, pero hay que verificar (importe alto/SARA o sin importe).
        - 🔵 **TIC (bajo importe)** — es de nuestras áreas o software genérico, pero por
          debajo de 50.000 €.
        - ⚪ **DESCARTAR** — cae por importe u otro filtro.
        - 🔴 **FUERA** — no-TIC o tecnología fuera de las capacidades Pasiona.

        **Qué NO hace todavía (fase de producto):**
        - Leer el pliego completo (PCAP/PPT) para el matiz fino.
        - Memoria de decisiones previas de Dirección.
        - Cobertura del Estado (PLACSP) y otras fuentes.
        - Valoración con IA de cada caso frontera.

        La clasificación se basa en el **objeto del contrato** publicado por la fuente oficial;
        los casos límite conviene revisarlos con criterio experto.
        """
    )

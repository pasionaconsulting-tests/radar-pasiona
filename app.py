# -*- coding: utf-8 -*-
"""
RADAR DE LICITACIONES AAPP - PASIONA
4 pestañas: Radar (funcional) + Analista de pliegos, Redacción y Avisos (fase 2).
FILTROS PASIONA: umbral económico (Ernest) + capacidades (Txema).
Coste 0 EUR. Autora: Dori Portales - 2026.
"""

import datetime as dt
from pathlib import Path

import requests
import pandas as pd
import streamlit as st

NARANJA = "#EA7600"
GRIS = "#97999B"

st.set_page_config(page_title="Radar de Licitaciones - Pasiona",
                   page_icon="🛰️", layout="wide")

# CSS en una sola linea. line-height amplio para que NO se corten las letras.
_CSS = (
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');"
    "html,body,[class*='css'],.stMarkdown,.stDataFrame{font-family:'Open Sans',sans-serif;color:#252525;}"
    ".block-container{padding-top:2.5rem;max-width:1600px;}"
    "#MainMenu,footer{visibility:hidden;}"
    ".htit{font-size:24px;font-weight:700;color:#252525;line-height:1.6;margin:0;padding:4px 0;overflow:visible;}"
    ".hsub{font-size:12.5px;color:#515151;line-height:1.7;margin-top:2px;padding-bottom:4px;overflow:visible;}"
    ".hline{border-bottom:3px solid #EA7600;margin:16px 0 22px 0;}"
    "div[data-testid='stImage']{overflow:visible;}"
    "div[data-testid='stImage'] img{overflow:visible;max-width:100%;height:auto;object-fit:contain;padding-left:6px;}"
    "div[data-testid='stHorizontalBlock']:first-of-type{gap:0.5rem;}"
    ".cap{color:#97999B;font-size:12px;margin:2px 2px 18px 2px;line-height:1.6;}"
    ".pie{margin-top:40px;padding-top:18px;border-top:1px solid #E6E6E8;color:#97999B;font-size:11.5px;text-align:center;line-height:1.8;}"
    ".pie b{color:#EA7600;font-weight:700;}"
    ".fase2{background:#FFF6ED;border:1px solid #F3C892;border-left:4px solid #EA7600;border-radius:10px;padding:16px 20px;margin:10px 0 18px 0;line-height:1.7;}"
    ".fase2 b{color:#EA7600;}"
    ".ej{background:#F7F7F8;border:1px solid #E6E6E8;border-radius:10px;padding:16px 20px;margin-top:12px;line-height:1.7;}"
    "div[data-testid='stAlert']{border-radius:10px;}"
    "section[data-testid='stSidebar']{background:#F4F4F5;}"
    "div[data-testid='stMetric']{background:#fff;border:1px solid #E6E6E8;border-radius:10px;padding:14px 16px;}"
    "div[data-testid='stMetricValue']{font-size:28px;font-weight:700;color:#252525;line-height:1.4;}"
    "div[data-testid='stMetricLabel'] p{font-size:11.5px;color:#515151;font-weight:600;line-height:1.5;}"
    ".stTabs [data-baseweb='tab-list']{gap:6px;}"
    ".stTabs [data-baseweb='tab']{font-weight:600;}"
    "</style>"
)
st.markdown(_CSS, unsafe_allow_html=True)

API_PSCP = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
BUSCADOR_PSCP = "https://contractaciopublica.cat/ca/inici"

IMPORTE_MIN = 50000
IMPORTE_MAX = 300000
SARA_SERVICIOS = 221000

LISTA_BLANCA = {
    "Desarrollo con IA": [
        "intel·ligència artificial", "inteligencia artificial", "machine learning",
        "aprenentatge automàtic", "aprendizaje automático", "model de llenguatge",
        "modelo de lenguaje", "llm", "copilot", "github copilot", "anthropic",
        "openai", "chatgpt", "ia generativa", "intel·ligència generativa",
        "generative ai", "chatbot", "agent conversacional", "assistent virtual",
        "asistente virtual",
    ],
    "Desarrollo .NET": [
        ".net", "dotnet", " c# ", "asp.net", "blazor", "entity framework",
        "desenvolupament d'aplicacions", "desarrollo de aplicaciones",
        "desenvolupament de programari", "desarrollo de software",
        "aplicació web", "aplicación web", "aplicacions a mida", "aplicaciones a medida",
        "desenvolupament a mida", "desarrollo a medida", "microserveis",
        "microservicios", "desenvolupament d'api", "desarrollo de api",
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

TIC_GENERICO = [
    "programari", "software", "aplicació", "aplicación", "aplicacions", "aplicaciones",
    "aplicatiu", "aplicativo", "app ", "plataforma digital", "portal web",
    "seu electrònica", "sede electrónica", "sistema d'informació", "sistema de información",
    "solució digital", "solución digital", "eina digital", "herramienta digital",
    "manteniment informàtic", "mantenimiento informático", "evolutiu", "evolutivo",
    "digitalització", "digitalización", "transformació digital", "transformación digital",
    "administració electrònica", "administración electrónica",
]

DESCARTADAS = {
    "Oracle": ["oracle", "data guard", "exadata"],
    "Java/Spring": [" java", "spring boot", "j2ee", "jakarta ee"],
    "SAP": [" sap ", "s/4hana", " abap"],
    "Cloud/Infra con partnership": ["migració a azure", "migración a azure",
                                    "entorn azure", "entorno azure", "amazon web services",
                                    "vmware", "citrix", "nutanix"],
    "Producto cerrado / licencias": ["dspace", "trustedx", " jira", "atlassian",
                                     "confluence", "burp suite", "liferay", "sitecore",
                                     "veeam", "fortinet", "palo alto", "creative cloud",
                                     "adobe", "maxqda"],
    "Microinformática/Helpdesk": ["microinformàtica", "microinformatica", "helpdesk",
                                  "help desk", "suport a usuari", "soporte a usuario",
                                  "parc informàtic", "parque informático",
                                  "llocs de treball", "puestos de trabajo",
                                  "equips informàtics", "equipos informáticos"],
    "Infraestructura/Redes": ["cablejat", "cableado", "electrònica de xarxa",
                              "firewall", "servidors físics", "servidores físicos",
                              "datacenter", "centre de dades", " cpd ",
                              "còpies de seguretat", "copias de seguridad",
                              "allotjament al núvol", "alojamiento en la nube",
                              "videovigilància", "videovigilancia"],
    "ERP/Business Central/Dynamics": ["business central", "dynamics", "navision",
                                      " erp ", " sage ", "gestió comptable",
                                      "gestión contable"],
}

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
                              "adquisició de la pintura", "obra d'art", "reactiu", "reactivo",
                              "plasma membrane", "stain"],
    "Servicios no técnicos": ["neteja", "limpieza", "vigilància", "vigilancia",
                             "seguretat privada", "seguridad privada", "catering",
                             "restauració", "jardineria", "jardinería", "transport de",
                             "transporte de", "assegurança", "seguro de", "mostreig",
                             "muestreo", "anàlisi de laboratori", "laboratori",
                             "protecció de dades", "protección de datos",
                             "delegat de protecció", "delegado de protección",
                             "manteniment dels pianos", "piano", "actuacions forestals",
                             "forestal", "dinamització comunitària", "casal de barri",
                             "imatge gràfica", "imagen gráfica", "disseny gràfic",
                             "diseño gráfico"],
}


def primer_campo(fila, candidatos):
    for c in candidatos:
        if c in fila:
            return c
    return ""


CAMPOS_IMPORTE = ["pressupost_licitacio_sense", "pressupost_base_licitacio_sense_iva",
                  "valor_estimat_contracte", "pressupost_licitacio_amb", "pressupost", "import"]
CAMPOS_OBJETO = ["objecte_contracte", "denominacio", "objecte"]
CAMPOS_ORGANO = ["nom_organ", "nom_departament_ens", "nom_ambit"]
CAMPOS_PLAZO = ["termini_presentacio_ofertes", "data_fi_presentacio_ofertes"]
CAMPOS_URL = ["enllac_publicacio", "enllac_stcp", "enllac", "url_publicacio",
              "url", "enllac_web", "enllac_perfil"]
CAMPOS_EXP = ["codi_expedient", "expedient", "codi_expedient_contractacio"]


def ruta_logo():
    for n in ["Logo_Pasiona.png", "logo_pasiona.png", "Logo_RGB.png", "logo_rgb.png",
              "logo_pasiona_blanco.png", "Logo_Pasiona_Blanco.png"]:
        p = Path(n)
        if p.exists():
            return str(p)
    return ""


@st.cache_data(ttl=1800, show_spinner=False)
def cargar(limite):
    headers = {"User-Agent": "RadarPasiona/4.3"}
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


def num(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def detecta(texto, grupos):
    t = f" {texto.lower()} "
    for nombre, palabras in grupos.items():
        for p in palabras:
            if p in t:
                return nombre, p
    return None, None


def detecta_lista(texto, palabras):
    t = f" {texto.lower()} "
    return any(p in t for p in palabras)


def clasificar(fila, c_obj, c_imp):
    objeto = str(fila.get(c_obj, "") or "")
    importe = num(fila.get(c_imp, 0))
    sector, _ = detecta(objeto, NO_TIC)
    if sector:
        return "🔴 FUERA", f"No-TIC · {sector}"
    desc, _ = detecta(objeto, DESCARTADAS)
    if desc:
        return "🔴 FUERA", f"Fuera de capacidades · {desc}"
    area, _ = detecta(objeto, LISTA_BLANCA)
    if not area and detecta_lista(objeto, TIC_GENERICO):
        area = "Software / plataforma"
    if area:
        if importe == 0:
            return "🟡 DUDOSO", f"{area} · sin importe publicado"
        if importe < IMPORTE_MIN:
            return "🔵 TIC (bajo importe)", f"{area} · por debajo de 50.000 €"
        if importe > IMPORTE_MAX:
            return "🟡 DUDOSO", f"{area} · supera 300.000 €"
        if importe >= SARA_SERVICIOS:
            return "🟡 DUDOSO", f"{area} · zona SARA: verificar"
        franja = "A" if importe < 80000 else ("B" if importe < 150000 else "C")
        return "🟢 PRESENTAR", f"{area} · franja {franja}"
    return "🔴 FUERA", "No encaja en las 5 capacidades"


def fmt_eur(v):
    n = num(v)
    return f"{n:,.0f} €".replace(",", ".") if n else "—"


def fmt_fecha(v):
    s = str(v or "").strip()
    if not s or s.lower() in ("nan", "none"):
        return "—"
    if len(s) >= 10 and s[4:5] == "-":
        try:
            return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
        except Exception:  # noqa: BLE001
            return s
    return s


def url_valida(v):
    s = str(v or "").strip()
    return s if s.lower().startswith("http") else ""


# ── CABECERA: columnas nativas + line-height amplio (sin cortes) ─────────────
_logo = ruta_logo()
hc1, hc2 = st.columns([1, 6], vertical_alignment="center", gap="small")
with hc1:
    if _logo:
        st.image(_logo, width=135)
    else:
        st.markdown(
            f"<div style='font-size:26px;font-weight:700;color:{GRIS};line-height:1.8;'>"
            f"pasiona<span style='color:{NARANJA};'>●</span></div>",
            unsafe_allow_html=True,
        )
with hc2:
    st.markdown('<div class="htit">Radar de Licitaciones AAPP</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hsub">Conectado en vivo a la fuente oficial · Plataforma de Serveis de '
        'Contractació Pública (Generalitat de Catalunya) · Coste de infraestructura: 0 €</div>',
        unsafe_allow_html=True,
    )
st.markdown('<div class="hline"></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🛰️  Radar de licitaciones",
    "📊  Analista de pliegos",
    "📝  Redacción asistida",
    "📧  Avisos por email",
])

# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA 1 · RADAR (FUNCIONAL)
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    with st.sidebar:
        st.header("Parámetros del barrido")
        n_reg = st.slider("Publicaciones a analizar", 100, 1000, 400, step=100)
        st.divider()
        st.subheader("Filtros de vista")
        palabra = st.text_input("Buscar en el objeto del contrato", "")
        cats_sel = st.multiselect(
            "Mostrar categorías",
            ["🟢 PRESENTAR", "🟡 DUDOSO", "🔵 TIC (bajo importe)", "⚪ DESCARTAR", "🔴 FUERA"],
            default=["🟢 PRESENTAR", "🟡 DUDOSO", "🔵 TIC (bajo importe)"],
        )
        st.divider()
        st.markdown(f"<b style='color:{NARANJA}'>Filtros Pasiona aplicados</b>",
                    unsafe_allow_html=True)
        st.markdown(
            "**Económico (Ernest Pagès):** mínimo 50.000 €, techo 300.000 € / SARA.\n\n"
            "**Capacidades (Txema Salabert):**\n"
            "1. Desarrollo con IA (Claude, GitHub)\n2. Desarrollo .NET\n3. Servicios UX\n"
            "4. Servicios Agile\n5. Consultoría IA\n\n"
            "_El resto queda fuera de radar._\n\n"
            "**Fuente oficial:** Datos Abiertos Generalitat · PSCP. Ámbito: Catalunya."
        )

    try:
        with st.spinner("Conectando con la fuente oficial…"):
            df = cargar(n_reg)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se ha podido conectar con la fuente oficial. Detalle: {e}")
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
    df["Motivo"] = res[1]

    tot = len(df)
    n_pres = int((df["Categoría"] == "🟢 PRESENTAR").sum())
    n_dud = int((df["Categoría"] == "🟡 DUDOSO").sum())
    n_tic = int((df["Categoría"] == "🔵 TIC (bajo importe)").sum())
    n_desc = int((df["Categoría"] == "⚪ DESCARTAR").sum())
    n_fuera = int((df["Categoría"] == "🔴 FUERA").sum())

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Publicaciones", tot)
    m2.metric("🟢 Presentar", n_pres)
    m3.metric("🟡 Dudoso", n_dud)
    m4.metric("🔵 TIC bajo importe", n_tic)
    m5.metric("⚪ Descartar", n_desc)
    m6.metric("🔴 Fuera de radar", n_fuera)

    st.markdown(
        f'<div class="cap">Barrido en vivo · {dt.datetime.now():%d/%m/%Y %H:%M} · '
        f'fuente oficial PSCP Catalunya · clasificación según Filtros Pasiona (Ernest + Txema)</div>',
        unsafe_allow_html=True,
    )

    if n_pres == 0:
        st.info(
            f"Hoy no hay licitaciones **Presentar** en Catalunya que cumplan capacidad Pasiona "
            f"y importe ≥ 50.000 €. Se han detectado **{n_tic}** licitaciones TIC de nuestras áreas "
            f"por debajo del mínimo económico. El radar ha cribado {tot} publicaciones en segundos."
        )

    vista = df[df["Categoría"].isin(cats_sel)].copy()
    if palabra and c_obj:
        vista = vista[vista[c_obj].astype(str).str.contains(palabra, case=False, na=False)]

    tabla = pd.DataFrame()
    tabla["Categoría"] = vista["Categoría"]
    if c_exp:
        tabla["Cód. expediente"] = vista[c_exp].astype(str).replace(
            {"nan": "—", "None": "—", "": "—"})
    if c_obj:
        tabla["Objeto del contrato"] = vista[c_obj].astype(str)
    if c_imp:
        tabla["Importe"] = vista[c_imp].apply(fmt_eur)
    if c_pla:
        tabla["Plazo"] = vista[c_pla].apply(fmt_fecha)
    tabla["Motivo"] = vista["Motivo"]
    if c_org:
        tabla["Organismo"] = vista[c_org].astype(str)

    def construir_enlace(fila):
        if c_url:
            u = url_valida(fila.get(c_url, ""))
            if u:
                return u
        return BUSCADOR_PSCP

    tabla["Buscar"] = vista.apply(construir_enlace, axis=1)

    if vista.empty:
        st.success("No hay licitaciones en las categorías seleccionadas. "
                   "Marca también Descartar y Fuera para ver todo lo cribado.")
    else:
        colcfg = {
            "Categoría": st.column_config.TextColumn("Categoría", width="small"),
            "Cód. expediente": st.column_config.TextColumn("Cód. expediente", width="small"),
            "Objeto del contrato": st.column_config.TextColumn("Objeto del contrato", width="large"),
            "Importe": st.column_config.TextColumn("Importe", width="small"),
            "Plazo": st.column_config.TextColumn("Plazo", width="small"),
            "Motivo": st.column_config.TextColumn("Motivo", width="medium"),
            "Organismo": st.column_config.TextColumn("Organismo", width="medium"),
            "Buscar": st.column_config.LinkColumn("Buscar", display_text="Abrir buscador ↗"),
        }
        st.dataframe(tabla, use_container_width=True, hide_index=True,
                     column_config=colcfg, height=460)

    st.download_button(
        "Descargar (CSV)",
        data=tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"radar_pasiona_{dt.date.today():%Y%m%d}.csv",
        mime="text/csv",
    )

# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA 2 · ANALISTA DE PLIEGOS
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📊 Analista de pliegos")
    st.markdown(
        "Sube el PDF de un pliego (PCAP/PPT) descargado del expediente y obtén "
        "automáticamente una **checklist de requisitos**, un **resumen ejecutivo** y "
        "**alertas** (por ejemplo, si exige una tecnología o certificación que no tenemos)."
    )
    st.file_uploader("Arrastra aquí el pliego en PDF", type=["pdf"], key="up_pliego")
    st.button("Analizar pliego", type="primary", key="btn_pliego")
    st.markdown(
        '<div class="fase2">🔒 <b>Función configurada · pendiente de conexión con la API de IA '
        '(fase 2 del proyecto).</b><br>La interfaz ya está lista. Al conectar el motor de IA, '
        'el análisis se generará automáticamente. Mientras tanto, este análisis se realiza de '
        'forma manual con el asistente de IA corporativo. Ver documento de configuración adjunto.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ej"><b>Ejemplo de resultado (simulado)</b><br><br>'
        '<b>Resumen ejecutivo</b><br>'
        'Servicio de desarrollo y mantenimiento evolutivo de aplicación web a medida. '
        'Importe 96.000 € · Duración 24 meses · Procedimiento abierto.<br><br>'
        '<b>Checklist de requisitos</b><br>'
        '✅ Solvencia técnica: 2 proyectos similares en 3 años → <i>cumplimos</i><br>'
        '✅ Solvencia económica: volumen ≥ 150.000 € → <i>cumplimos</i><br>'
        '⚠️ Certificación ENS nivel medio → <i>verificar</i><br>'
        '✅ Equipo: 1 arquitecto .NET + 2 desarrolladores → <i>disponible</i><br><br>'
        '<b>Dictamen sugerido</b> · 🟢 GO — encaja con capacidad .NET, importe en franja B, '
        'plazo asumible.</div>',
        unsafe_allow_html=True,
    )

# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA 3 · REDACCIÓN ASISTIDA
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("📝 Redacción asistida de la documentación")
    st.markdown(
        "A partir del pliego analizado, genera **borradores** de la documentación a presentar "
        "(memoria técnica, declaraciones, índices de sobres). Se revisan y ajustan antes de enviar."
    )
    st.selectbox("Tipo de documento a redactar",
                 ["Memoria técnica", "Declaración responsable", "Índice de sobre técnico",
                  "Carta de presentación"], key="tipo_doc")
    st.text_area("Notas o instrucciones para el borrador (opcional)", key="notas_doc",
                 placeholder="Ej.: destacar experiencia en sector público y proyectos .NET…")
    st.button("Generar borrador", type="primary", key="btn_doc")
    st.markdown(
        '<div class="fase2">🔒 <b>Función configurada · pendiente de conexión con la API de IA '
        '(fase 2 del proyecto).</b><br>La interfaz ya está lista. Actualmente esta redacción se '
        'realiza de forma manual con el asistente de IA corporativo. Ver documento de '
        'configuración adjunto.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ej"><b>Ejemplo de borrador (simulado) · Memoria técnica</b><br><br>'
        '<b>1. Presentación de la empresa</b><br>'
        'Pasiona Consulting es una consultora tecnológica especializada en desarrollo de '
        'software a medida, con foco en .NET, IA aplicada y metodologías ágiles…<br><br>'
        '<b>2. Metodología propuesta</b><br>'
        'Se plantea un enfoque ágil (Scrum) con entregas incrementales cada 2 semanas…<br><br>'
        '<b>3. Equipo asignado</b><br>'
        '1 Arquitecto de software .NET, 2 desarrolladores senior, 1 perfil UX…<br><br>'
        '<i>[Borrador generado por IA · requiere revisión y validación experta antes de presentar]</i></div>',
        unsafe_allow_html=True,
    )

# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA 4 · AVISOS POR EMAIL
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📧 Avisos por email")
    st.markdown(
        "Recibe un correo automático **solo cuando el radar detecte una licitación "
        "🟢 Presentar o 🟡 Dudoso**, para no tener que entrar a revisar cada día."
    )
    st.text_input("Correo donde recibir los avisos",
                  placeholder="nombre@pasiona.com", key="email_aviso")
    st.selectbox("Frecuencia del barrido automático",
                 ["Cada día laborable (mañana)", "Lunes y jueves", "Solo lunes"],
                 key="frec_aviso")
    st.button("Activar avisos", type="primary", key="btn_email")
    st.markdown(
        '<div class="fase2">🔒 <b>Función configurada · se activa con una automatización externa '
        '(GitHub Actions, gratuita).</b><br>El radar se ejecutaría solo a la hora fijada y, si hay '
        'algún resultado 🟢/🟡, enviaría el correo con la lista. Requiere una configuración inicial '
        'de credencial de envío. Ver documento de configuración adjunto.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ej"><b>Ejemplo de email (simulado)</b><br><br>'
        '<b>Asunto:</b> 🛰️ Radar Pasiona · 1 licitación para presentar<br><br>'
        'Buenos días,<br>El radar ha detectado hoy <b>1 licitación 🟢 Presentar</b>:<br><br>'
        '• <b>Desarrollo de aplicación web a medida</b> · 96.000 € · Universitat de Barcelona · '
        'plazo 21/09/2026 · Cód. 2026/90<br><br>'
        'Puedes revisarla en el Radar. — Sistema automático Pasiona</div>',
        unsafe_allow_html=True,
    )

with st.expander("ℹ️ Qué hace y qué no hace esta demo"):
    st.markdown(
        "**Pestaña 1 · Radar (funcional):** se conecta en vivo a la fuente oficial (PSCP Catalunya), "
        "aplica los Filtros Pasiona (económico de Ernest + capacidades de Txema) y clasifica cada "
        "licitación en 5 categorías con su motivo.\n\n"
        "**Pestañas 2, 3 y 4 (configuradas · fase 2):** la interfaz está lista, pero requieren "
        "conexión con una API de IA o una automatización externa. Se muestran ejemplos de cómo "
        "se verá el resultado.\n\n"
        "**Manual en esta fase:** descargar el PDF del pliego desde el expediente oficial y la "
        "decisión final de presentarse."
    )

st.markdown(
    '<div class="pie"><b>pasiona</b> &nbsp;·&nbsp; Radar de Licitaciones AAPP &nbsp;·&nbsp; '
    f'Demo {dt.date.today():%Y}<br>Fuente oficial: Datos Abiertos de la Generalitat de '
    'Catalunya (PSCP)</div>',
    unsafe_allow_html=True,
)

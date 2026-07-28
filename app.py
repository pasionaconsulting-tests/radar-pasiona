# -*- coding: utf-8 -*-
"""
🛰️ RADAR DE LICITACIONES AAPP · PASIONA
Demo conectada EN VIVO a la fuente oficial de contratación pública de Catalunya
(Datos Abiertos Generalitat · Plataforma de Serveis de Contractació Pública).

Aplica los criterios REALES del Radar Pasiona:
  · 4 filtros Pasiona (perfiles/horas, franjas de importe, tipo de servicio, alcance)
  · Línea roja SARA
  · 11 CPVs validados
  · Clasificación en 4 categorías CON MOTIVO:
       🟢 PRESENTAR · 🟡 DUDOSO · ⚪ DESCARTAR · 🔴 FUERA DE RADAR

Coste de infraestructura: 0 €
Autora: Dori Portales · Pasiona Consulting · 2026
"""

import datetime as dt
import requests
import pandas as pd
import streamlit as st

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Radar de Licitaciones · Pasiona",
                   page_icon="🛰️", layout="wide")

API_PSCP = "https://analisi.transparenciacatalunya.cat/resource/ybgg-dgi6.json"
DETALLE = "https://contractaciopublica.cat/ca/detall-publicacio/{}"

# ── Criterios REALES del Radar Pasiona ──────────────────────────────────────
CPVS_VALIDOS = [
    "72212900", "72240000", "72250000", "72260000", "72262000",
    "72267000", "72267100", "72600000", "72611000", "72810000", "71356200",
]
# Prefijos amplios para captar familias completas (72=Serveis TI, 48=software)
CPV_PREFIJOS = ("72", "48", "71356")

# Franjas de importe (sin IVA)
FRANJA_A = (20000, 80000)
FRANJA_B = (80000, 150000)
FRANJA_C = (150000, 300000)
TOPE_ABSOLUTO = 300000

# Línea roja SARA
SARA_FUERA = 220000       # > 220k € → FUERA DE RADAR
SARA_DUDOSO = 120000      # 120k-220k € → DUDOSO (verificar PCAP)

# Paleta Pasiona
NARANJA = "#EA7600"
CARBON = "#252525"

# ════════════════════════════════════════════════════════════════════════════
# ESTILO (aspecto Pasiona)
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
    .stApp {{ background: #ffffff; }}
    h1, h2, h3 {{ color: {CARBON}; }}
    .kpi {{ border-radius: 10px; padding: 16px 12px; text-align: center; color: white; }}
    .kpi .n {{ font-size: 30px; font-weight: 800; line-height: 1; }}
    .kpi .t {{ font-size: 12px; font-weight: 600; margin-top: 4px; }}
    .pill {{ padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }}
    .cab {{ background: {NARANJA}; color: white; padding: 18px 22px; border-radius: 10px;
            margin-bottom: 10px; }}
    .cab h1 {{ color: white; margin: 0; font-size: 26px; }}
    .cab p {{ color: white; margin: 4px 0 0 0; font-size: 13px; opacity: .95; }}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS · consulta ligera y filtrada en el SERVIDOR (evita cuelgues)
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800, show_spinner=False)
def cargar(dias: int, limite: int) -> pd.DataFrame:
    """
    Trae SOLO anuncios de licitación de tipo Serveis, recientes.
    Filtra en el servidor (SoQL) para que la consulta sea rápida y no agote
    el tiempo de espera.
    """
    desde = (dt.date.today() - dt.timedelta(days=dias)).isoformat()

    # Selección de columnas mínimas -> respuesta mucho más ligera
    select = ",".join([
        "codi_expedient", "denominacio", "objecte_contracte", "tipus_contracte",
        "codi_cpv", "nom_organ", "nom_departament_ens",
        "pressupost_licitacio_sense", "valor_estimat_contracte",
        "data_publicacio_anunci", "termini_presentacio_ofertes",
        "enllac_publicacio", "fase_publicacio", "procediment",
    ])
    where = (
        "tipus_contracte='Serveis' "
        f"AND data_publicacio_anunci > '{desde}'"
    )
    params = {
        "$select": select,
        "$where": where,
        "$order": "data_publicacio_anunci DESC",
        "$limit": limite,
    }
    r = requests.get(API_PSCP, params=params, timeout=45,
                     headers={"User-Agent": "RadarPasiona/2.0"})
    r.raise_for_status()
    return pd.DataFrame(r.json())


def num(v) -> float:
    try:
        return float(str(v).replace(",", ".")) if v not in (None, "") else 0.0
    except (ValueError, TypeError):
        return 0.0


def clasificar(fila: dict) -> tuple[str, str]:
    """
    Devuelve (categoría, motivo) según los criterios reales del Radar Pasiona.
    Categorías: PRESENTAR / DUDOSO / DESCARTAR / FUERA
    """
    cpv = str(fila.get("codi_cpv", "") or "")
    importe = num(fila.get("pressupost_licitacio_sense"))
    if importe == 0:
        importe = num(fila.get("valor_estimat_contracte"))

    cpv_ok = cpv.startswith(CPV_PREFIJOS)

    # ── FUERA DE RADAR ──────────────────────────────────────────────────
    if importe > SARA_FUERA:
        return "🔴 FUERA", f"SARA: importe {importe:,.0f}€ supera 220.000€"
    if not cpv_ok:
        return "🔴 FUERA", f"CPV {cpv[:8] or '—'} fuera del ámbito TIC de Pasiona"

    # ── DUDOSO ──────────────────────────────────────────────────────────
    if importe > TOPE_ABSOLUTO:
        return "🟡 DUDOSO", f"Importe {importe:,.0f}€ supera tope de 300.000€"
    if SARA_DUDOSO <= importe <= SARA_FUERA:
        return "🟡 DUDOSO", f"Zona SARA ({importe:,.0f}€): verificar PCAP"
    if importe == 0:
        return "🟡 DUDOSO", "Sin importe publicado: verificar en el expediente"

    # ── PRESENTAR ───────────────────────────────────────────────────────
    if FRANJA_A[0] <= importe <= FRANJA_C[1] and cpv in CPVS_VALIDOS:
        franja = ("A" if importe <= FRANJA_A[1]
                  else "B" if importe <= FRANJA_B[1] else "C")
        return "🟢 PRESENTAR", f"CPV validado · franja {franja} ({importe:,.0f}€)"
    if FRANJA_A[0] <= importe <= FRANJA_C[1] and cpv_ok:
        return "🟢 PRESENTAR", f"CPV TIC · importe en rango ({importe:,.0f}€)"

    # ── DESCARTAR ───────────────────────────────────────────────────────
    if importe < FRANJA_A[0]:
        return "⚪ DESCARTAR", f"Importe bajo ({importe:,.0f}€), fuera de franja A"
    return "⚪ DESCARTAR", "No cumple todos los filtros Pasiona"


# ════════════════════════════════════════════════════════════════════════════
# CABECERA
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="cab">
  <h1>🛰️ Radar de Licitaciones AAPP · Pasiona</h1>
  <p>Conectado <b>en vivo</b> a la fuente oficial · Plataforma de Serveis de
     Contractació Pública (Generalitat de Catalunya) · Coste de infraestructura: 0 €</p>
</div>
""", unsafe_allow_html=True)

# ── Controles ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Parámetros del barrido")
    dias = st.select_slider("Período (días hacia atrás)",
                            options=[7, 15, 30, 60, 90], value=30)
    limite = st.select_slider("Máximo de publicaciones",
                              options=[50, 100, 200, 300], value=100)
    st.divider()
    st.subheader("🔎 Filtros de vista")
    palabra = st.text_input("Buscar en el objeto del contrato", "")
    cats = st.multiselect(
        "Mostrar categorías",
        ["🟢 PRESENTAR", "🟡 DUDOSO", "⚪ DESCARTAR", "🔴 FUERA"],
        default=["🟢 PRESENTAR", "🟡 DUDOSO", "⚪ DESCARTAR", "🔴 FUERA"],
    )
    st.divider()
    st.caption(
        "**Criterios Pasiona aplicados:** 11 CPVs validados · franjas A/B/C · "
        "tope 300.000€ · línea roja SARA 220.000€ · solo servicios (no llave "
        "en mano). Ámbito: Catalunya. El Estado (PLACSP) se integra en la "
        "siguiente fase."
    )

# ── Carga ────────────────────────────────────────────────────────────────────
try:
    with st.spinner("Conectando con la fuente oficial…"):
        df = cargar(dias, limite)
except Exception as e:  # noqa: BLE001
    st.error("No se ha podido conectar con la fuente oficial ahora mismo "
             "(puede estar en mantenimiento). Prueba a reducir el período o "
             f"reintenta en unos minutos.\n\nDetalle técnico: {e}")
    st.stop()

if df.empty:
    st.warning("La fuente no ha devuelto publicaciones para ese período. "
               "Amplía el número de días en el panel izquierdo.")
    st.stop()

# ── Clasificación ─────────────────────────────────────────────────────────────
clas = df.apply(lambda f: clasificar(f.to_dict()), axis=1)
df["Categoría"] = [c[0] for c in clas]
df["Motivo"] = [c[1] for c in clas]

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (c1, "Publicaciones", len(df), CARBON),
    (c2, "🟢 Presentar", int((df["Categoría"] == "🟢 PRESENTAR").sum()), "#28a745"),
    (c3, "🟡 Dudoso", int((df["Categoría"] == "🟡 DUDOSO").sum()), "#f0a500"),
    (c4, "⚪ Descartar", int((df["Categoría"] == "⚪ DESCARTAR").sum()), "#8a8d91"),
    (c5, "🔴 Fuera", int((df["Categoría"] == "🔴 FUERA").sum()), "#dc3545"),
]
for col, titulo, valor, color in kpis:
    col.markdown(
        f'<div class="kpi" style="background:{color}">'
        f'<div class="n">{valor}</div><div class="t">{titulo}</div></div>',
        unsafe_allow_html=True,
    )

st.caption(f"Barrido en vivo · {dt.datetime.now():%d/%m/%Y %H:%M} · "
           f"últimos {dias} días · fuente oficial PSCP Catalunya")

# ── Filtros de vista ──────────────────────────────────────────────────────────
vista = df[df["Categoría"].isin(cats)].copy()
col_obj = "denominacio" if "denominacio" in vista.columns else "objecte_contracte"
if palabra and col_obj in vista.columns:
    vista = vista[vista[col_obj].astype(str).str.contains(palabra, case=False, na=False)]

# ── Tabla ─────────────────────────────────────────────────────────────────────
def fmt_eur(v):
    n = num(v)
    return f"{n:,.0f} €".replace(",", ".") if n else "—"

tabla = pd.DataFrame({
    "Categoría": vista["Categoría"],
    "Motivo": vista["Motivo"],
    "Objeto": vista.get(col_obj, ""),
    "Organismo": vista.get("nom_organ", vista.get("nom_departament_ens", "")),
    "CPV": vista.get("codi_cpv", ""),
    "Importe (sin IVA)": vista.get("pressupost_licitacio_sense", "").apply(fmt_eur),
    "Publicación": vista.get("data_publicacio_anunci", ""),
    "Plazo": vista.get("termini_presentacio_ofertes", ""),
})
if "enllac_publicacio" in vista.columns:
    tabla["Expediente"] = vista["enllac_publicacio"].astype(str)
elif "codi_expedient" in vista.columns:
    tabla["Expediente"] = vista["codi_expedient"].astype(str).apply(DETALLE.format)

st.dataframe(
    tabla, use_container_width=True, hide_index=True,
    column_config={
        "Expediente": st.column_config.LinkColumn("Expediente", display_text="Abrir ↗"),
        "Motivo": st.column_config.TextColumn("Motivo", width="medium"),
        "Objeto": st.column_config.TextColumn("Objeto", width="large"),
    },
)

st.download_button(
    "⬇️ Descargar (CSV)",
    tabla.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"radar_pasiona_{dt.date.today():%Y%m%d}.csv",
    mime="text/csv",
)

with st.expander("ℹ️ Qué hace y qué no hace esta demo"):
    st.markdown(
        """
        **SÍ hace (en vivo, coste 0 €):** barrido de la fuente oficial,
        aplicación de los criterios reales de Pasiona (11 CPVs, franjas de
        importe, línea roja SARA, tipo de contrato) y clasificación en las 4
        categorías **con el motivo** de cada decisión.

        **Todavía NO hace (fase de producto):** análisis de los pliegos
        completos (PCAP/PPT), valoración con IA del encaje real, memoria de
        decisiones previas de Dirección, cobertura del Estado (PLACSP) y
        generación automática del informe/correo. Todo ello está en la hoja
        de ruta del documento de acompañamiento.
        """
    )

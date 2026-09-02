from pathlib import Path
from datetime import datetime
from io import BytesIO
import json
import re

import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "informes_temporales"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "historial_informes.json"
LATEST_FILE = DATA_DIR / "ultimo_informe.json"

st.set_page_config(
    page_title="Sartore · Informes",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { color-scheme: dark !important; }
    html, body, [class*="css"] { color: #f3ede0; }
    .stApp { background: radial-gradient(circle at 5% 0%, rgba(180,135,48,.14), transparent 28%), linear-gradient(135deg,#070707,#11100d 55%,#080808) !important; color:#f3ede0 !important; }
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: transparent !important; }
    .block-container { max-width:1180px; padding:1.1rem .9rem 3rem; }
    h1,h2,h3,h4,p,label,span,li { color:#f3ede0 !important; }
    .hero { background:linear-gradient(135deg,rgba(45,36,19,.98),rgba(18,17,14,.98)); border:1px solid #806127; border-top:2px solid #d2aa55; border-radius:20px; padding:1.25rem 1.4rem; margin-bottom:1.1rem; box-shadow:0 20px 50px rgba(0,0,0,.4); }
    .kicker { color:#d7b263 !important; font-size:.75rem; font-weight:800; letter-spacing:.15em; }
    .hero-title { color:#fffaf0 !important; font-size:clamp(1.75rem,4.5vw,2.8rem); font-weight:800; line-height:1.08; margin:.35rem 0; }
    .hero-subtitle { color:#cfc3aa !important; margin:0; line-height:1.5; }
    [data-testid="stMetric"] { background:linear-gradient(145deg,#252118,#171612); border:1px solid #624d28; border-radius:15px; padding:.85rem; }
    [data-testid="stMetricLabel"] { color:#cdbb95 !important; }
    [data-testid="stMetricValue"] { color:#f1c566 !important; font-weight:800; }
    .stTabs [data-baseweb="tab-list"] { gap:.4rem; border-bottom:1px solid #5e4928; }
    .stTabs [data-baseweb="tab"] { color:#cbbd9e !important; font-weight:700; }
    .stTabs [aria-selected="true"] { color:#fff8e7 !important; background:linear-gradient(135deg,#805d20,#503a19) !important; border-radius:10px 10px 0 0; }
    [data-testid="stFileUploader"] { background:#1c1a15; border:1px dashed #bd9140; border-radius:16px; padding:.75rem; }
    .stButton > button, .stDownloadButton > button { width:100%; min-height:42px; border-radius:10px; border:1px solid #d3a94f !important; background:linear-gradient(135deg,#b6852d,#735018) !important; color:#fffaf0 !important; font-weight:800; }
    .stButton > button:hover, .stDownloadButton > button:hover { background:linear-gradient(135deg,#c99c43,#8a6222) !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea { background:#171613 !important; color:#f5eddd !important; border-color:#69542d !important; }
    [data-testid="stDataFrame"] { border:1px solid #594629; border-radius:12px; overflow:hidden; }
    [data-testid="stExpander"] { border:1px solid #594629; background:rgba(28,26,21,.78); border-radius:12px; }
    @media (max-width:700px) { .hero { padding:1rem; border-radius:16px; } .hero-title { font-size:1.85rem; } .block-container { padding:.75rem .7rem 2rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def history():
    return read_json(HISTORY_FILE, [])


def event(kind, filename, note=""):
    rows = history()
    rows.insert(0, {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "tipo": kind,
        "archivo": filename,
        "detalle": note,
    })
    write_json(HISTORY_FILE, rows)


def save_uploaded(filename, content, extension):
    destination = DATA_DIR / f"ultimo_informe{extension}"
    destination.write_bytes(content)
    write_json(LATEST_FILE, {
        "nombre": filename,
        "ruta": str(destination),
        "extension": extension,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })


def latest():
    value = read_json(LATEST_FILE, None)
    if value and Path(value.get("ruta", "")).exists():
        return value
    return None


def excel_or_csv(content, extension):
    if extension == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return pd.read_csv(BytesIO(content), encoding=encoding)
            except Exception:
                pass
        raise ValueError("No se pudo leer el CSV.")
    return pd.read_excel(BytesIO(content))


def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip())


def norm(value):
    return re.sub(r"[^a-z0-9áéíóúüñ ]", "", clean_name(value).lower())


def find_col(df, terms):
    for col in df.columns:
        key = norm(col)
        if any(term in key for term in terms):
            return col
    return None


def first_number(value):
    if pd.isna(value):
        return None
    text = str(value).replace("$", "").replace("%", "").replace(".", "").replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def detect_barber(df):
    col = find_col(df, ["barbero", "barber", "profesional", "colaborador", "atendio", "atendió"])
    if col:
        return col
    return None


def report_data(df):
    result = {}
    mapping = {
        "Ticket promedio": ["ticket promedio", "ticket", "promedio venta"],
        "Tasa de ocupación": ["ocupacion", "ocupación"],
        "Servicios y productos": ["servicios y productos", "servicios registrados", "total registrado"],
        "Tasa de fidelización": ["fidelizacion", "fidelización"],
        "Clientes nuevos": ["clientes nuevos"],
        "Clientes antiguos": ["clientes antiguos"],
        "Clientes reales": ["clientes reales", "total de clientes"],
        "Encuestas respondidas": ["encuestas respondidas", "respuestas"],
        "Promedio recomendación": ["promedio de recomendacion", "promedio de recomendación", "nps", "recomendacion"],
    }
    text = " ".join(norm(x) for x in df.columns)
    for label, terms in mapping.items():
        col = find_col(df, terms)
        if col:
            value = df[col].dropna().iloc[0] if len(df[col].dropna()) else None
            result[label] = value
    return result


def cards(data):
    if not data:
        st.info("No se detectaron indicadores resumidos en este archivo.")
        return
    labels = list(data)
    for start in range(0, len(labels), 4):
        cols = st.columns(min(4, len(labels) - start))
        for col, label in zip(cols, labels[start:start + 4]):
            with col:
                st.metric(label, str(data[label]))


def chart_barber(df, barber_col):
    names = sorted([clean_name(x) for x in df[barber_col].dropna().unique() if clean_name(x)])
    if not names:
        st.info("La columna de barbero no contiene nombres válidos.")
        return
    selected = st.selectbox("Pantalla individual", names)
    individual = df[df[barber_col].astype(str).map(clean_name) == selected].copy()
    st.markdown(f"### {selected}")
    cards(report_data(individual))

    numeric = individual.select_dtypes(include="number")
    if not numeric.empty:
        st.bar_chart(numeric.sum().sort_values(ascending=False).head(12))
    else:
        categorical = [c for c in individual.columns if c != barber_col]
        if categorical:
            col = st.selectbox("Gráfico de distribución", categorical, key=f"chart_{selected}")
            counts = individual[col].fillna("Sin dato").astype(str).value_counts().head(10)
            st.bar_chart(counts)

    st.dataframe(individual.head(100), use_container_width=True, hide_index=True)


def show_summary(df, filename):
    st.markdown(f"### Informe: {filename}")
    st.caption("La vista intenta convertir el archivo cargado en indicadores y pantallas individuales.")
    cards(report_data(df))
    barber_col = detect_barber(df)
    if barber_col:
        st.markdown("### Pantallas por barbero")
        chart_barber(df, barber_col)
    else:
        st.warning("No se encontró una columna de barbero. Para separar pantallas, agrega una columna llamada Barbero.")
        st.dataframe(df.head(100), use_container_width=True, hide_index=True)


def main():
    st.markdown(
        """
        <div class="hero">
          <div class="kicker">SARTORE · INFORMES INDIVIDUALES</div>
          <div class="hero-title">Panel de barberos</div>
          <div class="hero-subtitle">Carga un informe con la columna Barbero y revisa una pantalla, métricas y gráficos para cada profesional.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    h = history()
    last = latest()
    a, b, c = st.columns(3)
    a.metric("Actualizaciones", len(h))
    b.metric("Informe actual", last["fecha"] if last else "Sin datos")
    c.metric("Tema", "Negro · Dorado")

    tab_report, tab_history, tab_help = st.tabs(["Informes", "Historial", "Estructura"])

    with tab_report:
        upload = st.file_uploader("Cargar informe Excel, CSV o PDF", type=["xlsx", "xls", "csv", "pdf"])
        note = st.text_input("Nota del cambio", placeholder="Ejemplo: Informe de agosto actualizado")
        if upload:
            extension = Path(upload.name).suffix.lower()
            content = upload.getvalue()
            if extension in (".xlsx", ".xls", ".csv"):
                try:
                    df = excel_or_csv(content, extension)
                    show_summary(df, upload.name)
                except Exception as error:
                    st.error(f"No se pudo analizar el archivo: {error}")
            else:
                st.info("El PDF se puede guardar y descargar; el análisis automático de PDF se agregará después.")
            if st.button("Guardar informe temporal", type="primary"):
                save_uploaded(upload.name, content, extension)
                event("Informe cargado", upload.name, note or "Archivo actualizado")
                st.success("Informe guardado temporalmente.")
                st.rerun()
        elif last:
            path = Path(last["ruta"])
            content = path.read_bytes()
            st.info(f"Último informe: {last['nombre']} · {last['fecha']}")
            st.download_button("Descargar informe", content, file_name=last["nombre"])
            if last["extension"] in (".xlsx", ".xls", ".csv"):
                try:
                    show_summary(excel_or_csv(content, last["extension"]), last["nombre"])
                except Exception as error:
                    st.warning(f"No se pudo mostrar el último informe: {error}")
        else:
            st.info("Carga un informe para comenzar.")

    with tab_history:
        st.subheader("Historial de cambios")
        if h:
            hist = pd.DataFrame(h)
            st.dataframe(hist, use_container_width=True, hide_index=True)
            st.download_button("Descargar historial", hist.to_csv(index=False).encode("utf-8-sig"), "historial_informes.csv", "text/csv")
        else:
            st.info("Todavía no hay cambios registrados.")
        note = st.text_area("Agregar información al historial")
        if st.button("Registrar nota"):
            if note.strip():
                event("Nota agregada", "Sin archivo", note.strip())
                st.success("Nota registrada.")
                st.rerun()
            else:
                st.warning("Escribe una nota primero.")

    with tab_help:
        st.subheader("Estructura recomendada")
        st.markdown("""
        Para crear una pantalla por barbero, el Excel o CSV debe tener una columna llamada **Barbero**.

        Ejemplo:

        | Barbero | Ticket promedio | Ocupación | Servicios | Encuestas |
        |---|---:|---:|---:|---:|
        | Armin Scott | 26105 | 69% | 378 | 32 |
        | Barbero 2 | 24000 | 64% | 310 | 28 |

        Si cada fila es un servicio o atención, la app puede agrupar los registros por barbero y calcular totales y promedios.
        """)

    st.caption("Versión temporal · almacenamiento local de la instancia de Streamlit")


main()

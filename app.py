from pathlib import Path
from datetime import datetime
from io import BytesIO
import hashlib
import json
import re

import pandas as pd
import streamlit as st

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

try:
    from mailer import enviar_correo, crear_borrador, probar_conexion_gmail
except Exception:
    enviar_correo = crear_borrador = probar_conexion_gmail = None

BASE = Path(__file__).resolve().parent
CLIENTES_FILE = BASE / "clientes_actual.xlsx"
PLANTILLAS_FILE = BASE / "plantillas.json"
HISTORIAL_FILE = BASE / "historial_envios.csv"
SURVEY_DIR = BASE / "encuestas"
LAST_SURVEY = SURVEY_DIR / "ultima_encuesta.csv"
SURVEY_META = SURVEY_DIR / "ultima_encuesta.json"
SURVEY_DIR.mkdir(exist_ok=True)
PASSWORD_HASH = hashlib.sha256("Gael77928".encode()).hexdigest()
EMAIL_REGEX = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

st.set_page_config(page_title="Sartore · Gestor", page_icon="✉", layout="wide")
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#080d13,#101a22);color:#eee8df}
.block-container{max-width:1450px;padding:1.5rem 3rem 4rem}
section[data-testid="stSidebar"]{background:#0b1219;border-right:1px solid #293b49}
h1,h2,h3{font-family:Georgia,serif!important}
.stButton>button{border:1px solid #b99a63;background:transparent;color:#dec48f;border-radius:8px}
[data-testid="stMetric"]{background:#111a23;border:1px solid #293b49;border-radius:10px;padding:12px}
</style>
""", unsafe_allow_html=True)


def valid_email(value):
    return bool(EMAIL_REGEX.fullmatch(str(value).strip()))


def extract_email(row):
    for value in row:
        if not pd.isna(value):
            match = EMAIL_REGEX.search(str(value))
            if match:
                return match.group(0).lower()
    return ""


def email_source(row):
    for column, value in row.items():
        if not pd.isna(value) and EMAIL_REGEX.search(str(value)):
            return str(column)
    return ""


def find_column(data, terms):
    return next((c for c in data.columns if any(term in c.lower() for term in terms)), None)


def cell(row, column):
    if not column or column not in row.index:
        return ""
    value = row.get(column, "")
    return "" if pd.isna(value) else str(value).strip()


def render(text, row):
    return re.sub(r"\{([^{}]+)\}", lambda m: cell(row, m.group(1).strip()), str(text))


def save_log(recipient, subject, status, detail="", template=""):
    row = pd.DataFrame([{"fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "destinatario": recipient, "asunto": subject, "plantilla": template, "estado": status, "detalle": detail}])
    if HISTORIAL_FILE.exists():
        row = pd.concat([pd.read_csv(HISTORIAL_FILE), row], ignore_index=True)
    row.to_csv(HISTORIAL_FILE, index=False, encoding="utf-8-sig")


def load_templates():
    if PLANTILLAS_FILE.exists():
        try:
            return json.loads(PLANTILLAS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_survey(uploaded):
    LAST_SURVEY.write_bytes(uploaded.getvalue())
    SURVEY_META.write_text(json.dumps({"nombre": uploaded.name, "guardado": datetime.now().strftime("%d/%m/%Y %H:%M")}, ensure_ascii=False, indent=2), encoding="utf-8")


def load_meta():
    if SURVEY_META.exists():
        try:
            return json.loads(SURVEY_META.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def parse_date(series):
    text = series.astype(str).str.replace(r"\s+GMT[+-]\d+", "", regex=True).str.replace("a.m.", "AM", regex=False).str.replace("p.m.", "PM", regex=False)
    try:
        return pd.to_datetime(text, format="mixed", errors="coerce")
    except TypeError:
        return pd.to_datetime(text, errors="coerce")


def useful_columns(data):
    result = []
    for column in data.columns:
        if column.startswith("_"):
            continue
        text = data[column].fillna("").astype(str).str.replace(" ", "", regex=False).str.lower()
        if "[puntuación]" in column.lower() and text.isin(["", "--/0", "0/0", "0.00/0", "nan"]).all():
            continue
        if column.lower() == "puntuación total" and text.isin(["", "--/0", "0/0", "0.00/0", "nan"]).all():
            continue
        result.append(column)
    return result


def login():
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h1 style='text-align:center;letter-spacing:7px'>SARTORE</h1><p style='text-align:center;color:#9daab3'>LA BARBERÍA · ACCESO PRIVADO</p>", unsafe_allow_html=True)
        with st.form("login"):
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ENTRAR", width="stretch"):
                if hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")


if not st.session_state.get("auth"):
    login()
    st.stop()

if "clients" not in st.session_state:
    st.session_state.clients = pd.read_excel(CLIENTES_FILE) if CLIENTES_FILE.exists() else pd.DataFrame()
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = set()

clients = st.session_state.clients
with st.sidebar:
    st.markdown("## SARTORE")
    st.caption("GESTOR DE CORREOS")
    page = st.radio("Secciones", ["Correo", "Clientes", "Encuestas", "Plantillas", "Historial", "Configuración"], label_visibility="collapsed")
    st.divider()
    st.caption(f"Clientes: {len(clients):,}")
    if st.button("Cerrar sesión", width="stretch"):
        st.session_state.auth = False
        st.rerun()

if page == "Configuración":
    st.title("Configuración")
    st.subheader("Conexión Gmail")
    if probar_conexion_gmail is None:
        st.error("No se pudo importar mailer.py o gmail_auth.py.")
    elif st.button("Probar conexión Gmail", type="primary"):
        try:
            st.success(f"Gmail conectado: {probar_conexion_gmail()}")
        except Exception as error:
            st.error(f"Gmail no está conectado: {error}")
    st.info("Mantén credentials.json y token.json en la carpeta del proyecto.")
    st.stop()

if page == "Encuestas":
    st.title("Encuestas")
    st.caption("Vista limpia de respuestas, correos y calidad de datos.")
    uploaded = st.file_uploader("Cargar CSV de encuestas", type=["csv"], key="survey_upload")
    encoding = st.selectbox("Codificación", ["utf-8-sig", "utf-8", "latin-1"])
    meta = load_meta()
    if uploaded is not None:
        save_survey(uploaded)
        source = LAST_SURVEY
        st.success(f"Archivo guardado: {uploaded.name}")
    elif LAST_SURVEY.exists():
        source = LAST_SURVEY
        st.info(f"Último archivo: {meta.get('nombre', 'ultima_encuesta.csv')} · guardado {meta.get('guardado', '')}")
    else:
        st.info("Carga manualmente un CSV para comenzar.")
        st.stop()
    try:
        data = pd.read_csv(source, encoding=encoding)
    except Exception as error:
        st.error(f"No se pudo leer el CSV: {error}")
        st.stop()
    data.columns = [str(c).strip() for c in data.columns]
    date_col = find_column(data, ["marca temporal", "fecha"])
    data["_fecha"] = parse_date(data[date_col]) if date_col else pd.NaT
    data["_correo"] = data.apply(extract_email, axis=1)
    data["_origen_correo"] = data.apply(email_source, axis=1)
    columns = useful_columns(data)
    min_date = data["_fecha"].min().date() if data["_fecha"].notna().any() else None
    max_date = data["_fecha"].max().date() if data["_fecha"].notna().any() else None
    f1, f2, f3 = st.columns([2, 1, 1])
    search = f1.text_input("Buscar en cualquier dato o correo")
    dates = f2.date_input("Rango de fechas", value=(min_date, max_date), min_value=min_date, max_value=max_date, format="DD/MM/YYYY") if min_date and max_date else None
    only_email = f3.checkbox("Solo respuestas con correo", False)
    filtered = data.copy()
    if search:
        filtered = filtered[filtered.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)]
    if dates and isinstance(dates, tuple) and len(dates) == 2:
        filtered = filtered[(filtered["_fecha"].dt.date >= dates[0]) & (filtered["_fecha"].dt.date <= dates[1])]
    if only_email:
        filtered = filtered[filtered["_correo"].apply(valid_email)]
    email_rows = filtered[filtered["_correo"].apply(valid_email)]
    if len(email_rows):
        emails = email_rows.groupby("_correo", as_index=False).agg(Respuestas=("_correo", "size"), Primera_respuesta=("_fecha", "min"), Ultima_respuesta=("_fecha", "max"), Origen=("_origen_correo", "first")).rename(columns={"_correo": "Correo"})
        emails["Primera_respuesta"] = emails["Primera_respuesta"].dt.strftime("%d/%m/%Y %H:%M")
        emails["Ultima_respuesta"] = emails["Ultima_respuesta"].dt.strftime("%d/%m/%Y %H:%M")
        emails["Válido"] = True
    else:
        emails = pd.DataFrame(columns=["Correo", "Respuestas", "Primera_respuesta", "Ultima_respuesta", "Origen", "Válido"])
    completeness = pd.DataFrame({"Campo": columns, "Respuestas": [int(filtered[c].fillna("").astype(str).str.strip().ne("").sum()) for c in columns]})
    completeness["Porcentaje"] = (completeness["Respuestas"] / max(len(filtered), 1) * 100).round(1)
    daily = filtered.dropna(subset=["_fecha"]).assign(Fecha=lambda x: x["_fecha"].dt.date).groupby("Fecha").size().reset_index(name="Respuestas")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Respuestas", len(filtered))
    m2.metric("Correos únicos", len(emails))
    m3.metric("Correos válidos", len(emails))
    m4.metric("Campos visibles", len(columns))
    tabs = st.tabs(["Resumen", "Correos", "Respuestas", "Calidad"])
    with tabs[0]:
        left, right = st.columns(2)
        with left:
            st.markdown("**Respuestas por fecha**")
            if len(daily):
                st.line_chart(daily.set_index("Fecha"), height=280)
            else:
                st.info("No hay fechas válidas.")
        with right:
            st.markdown("**Respuestas con correo**")
            if MATPLOTLIB_OK and len(filtered):
                with_mail = int(filtered["_correo"].apply(valid_email).sum())
                without_mail = len(filtered) - with_mail
                fig, ax = plt.subplots(figsize=(5, 4))
                ax.pie([with_mail, without_mail], labels=["Con correo", "Sin correo"], autopct="%1.0f%%", startangle=90, colors=["#58d681", "#536273"], wedgeprops={"width": .42, "edgecolor": "#101a22"})
                ax.text(0, 0, f"{len(filtered)}\nrespuestas", ha="center", va="center", color="#eee8df", fontsize=12, fontweight="bold")
                fig.patch.set_facecolor("#101a22")
                st.pyplot(fig, clear_figure=True)
            else:
                st.info("Instala matplotlib para mostrar la torta.")
        st.bar_chart(completeness.sort_values("Respuestas", ascending=False).head(12).set_index("Campo")["Respuestas"], height=260)
    with tabs[1]:
        st.subheader("Correos detectados")
        if len(emails):
            st.dataframe(emails, width="stretch", hide_index=True)
            st.download_button("Descargar correos", emails.to_csv(index=False).encode("utf-8-sig"), "correos_encuestas.csv", "text/csv")
        else:
            st.warning("No se detectaron correos.")
    with tabs[2]:
        st.dataframe(filtered[columns], width="stretch", hide_index=True)
    with tabs[3]:
        st.caption("Se ocultan automáticamente las columnas de puntuación vacías o con 0.00 / 0.")
        st.dataframe(completeness.sort_values("Respuestas", ascending=False), width="stretch", hide_index=True)
    st.stop()

if page == "Clientes":
    st.title("Clientes")
    upload = st.file_uploader("Cargar Excel de clientes", type=["xlsx", "xls"])
    if upload and st.button("Aplicar Excel", type="primary"):
        new_clients = pd.read_excel(upload)
        new_clients.to_excel(CLIENTES_FILE, index=False)
        st.session_state.clients = new_clients
        st.session_state.selected_ids = set()
        st.success("Clientes actualizados.")
        st.rerun()
    if not clients.empty:
        mail_col = find_column(clients, ["email", "correo", "mail"])
        a, b, c = st.columns(3)
        a.metric("Registros", len(clients))
        b.metric("Correos válidos", int(clients[mail_col].apply(valid_email).sum()) if mail_col else 0)
        c.metric("Duplicados", int(clients.duplicated().sum()))
        st.dataframe(clients, width="stretch", hide_index=True)
    st.stop()

if page == "Plantillas":
    st.title("Plantillas")
    templates = load_templates()
    chosen = st.selectbox("Plantilla", ["Nueva plantilla"] + list(templates))
    previous = templates.get(chosen, {})
    name = st.text_input("Nombre", "" if chosen == "Nueva plantilla" else chosen)
    subject = st.text_input("Asunto", previous.get("asunto", ""))
    body = st.text_area("Cuerpo", previous.get("cuerpo", ""), height=240)
    if st.button("Guardar plantilla", type="primary") and name.strip():
        templates[name.strip()] = {"asunto": subject, "cuerpo": body}
        PLANTILLAS_FILE.write_text(json.dumps(templates, ensure_ascii=False, indent=2), encoding="utf-8")
        st.success("Plantilla guardada.")
    st.stop()

if page == "Historial":
    st.title("Historial")
    if HISTORIAL_FILE.exists():
        history = pd.read_csv(HISTORIAL_FILE)
        st.dataframe(history, width="stretch", hide_index=True)
        st.download_button("Descargar historial", history.to_csv(index=False).encode("utf-8-sig"), "historial_envios.csv", "text/csv")
    else:
        st.info("Aún no hay envíos registrados.")
    st.stop()

st.title("Correo")
if clients.empty:
    st.warning("Carga primero el Excel desde Clientes.")
    st.stop()
clients = clients.reset_index(drop=True)
clients["_id"] = clients.index
mail_col = find_column(clients, ["email", "correo", "mail"])
if not mail_col:
    st.error("El Excel debe tener una columna Email, Correo o Mail.")
    st.stop()
search = st.text_input("Buscar cliente")
visible = clients.copy()
if search:
    visible = visible[visible.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)]
shown = [c for c in ["Nombres", "Apellidos", mail_col, "Teléfono", "Ciudad", "comuna"] if c in visible.columns]
table = visible[["_id"] + shown].copy()
table.insert(0, "Enviar", table["_id"].isin(st.session_state.selected_ids))
edited = st.data_editor(table.drop(columns=["_id"]), width="stretch", hide_index=True, disabled=[c for c in table.columns if c not in ["Enviar", "_id"]], key="client_table")
ids = visible["_id"].tolist()
st.session_state.selected_ids.difference_update(ids)
st.session_state.selected_ids.update([ids[i] for i, checked in enumerate(edited["Enviar"]) if checked])

st.subheader("Destinatarios manuales")
manual = st.text_area("Correos no registrados en el Excel", placeholder="persona@ejemplo.com\notra@ejemplo.com")
manual_emails = list(dict.fromkeys(x.strip() for x in re.split(r"[,;\n]+", manual) if valid_email(x.strip())))
selected_clients = clients[clients["_id"].isin(st.session_state.selected_ids)]
recipients = list(dict.fromkeys([cell(row, mail_col) for _, row in selected_clients.iterrows() if valid_email(cell(row, mail_col))] + manual_emails))
st.info(f"Destinatarios totales: {len(recipients)}")

templates = load_templates()
template_choice = st.selectbox("Selecciona la plantilla", ["Mensaje nuevo"] + list(templates))
subject_default = "Información importante" if template_choice == "Mensaje nuevo" else templates[template_choice].get("asunto", "")
body_default = "Estimado/a {Nombres} {Apellidos}:\n\nEscribe aquí tu mensaje.\n\nSaludos cordiales." if template_choice == "Mensaje nuevo" else templates[template_choice].get("cuerpo", "")
subject = st.text_input("Asunto", subject_default, key=f"subject_{template_choice}")
body = st.text_area("Mensaje", body_default, height=220, key=f"body_{template_choice}")
action = st.radio("Acción", ["Guardar borradores", "Enviar directamente"], horizontal=True)

if st.button("Ejecutar", type="primary"):
    function = crear_borrador if action.startswith("Guardar") else enviar_correo
    if not recipients:
        st.error("Selecciona clientes o agrega correos manuales.")
    elif function is None:
        st.error("No se pudo cargar mailer.py. Revisa también gmail_auth.py.")
    else:
        total = len(recipients)
        correctos = 0
        errores = 0
        results = []
        progress = st.progress(0, text="Preparando proceso...")
        current = st.empty()
        counters = st.empty()
        with st.expander("Detalle del proceso", expanded=True):
            details = st.empty()
        for position, recipient in enumerate(recipients, 1):
            current.info(f"Procesando {position} de {total}: {recipient}")
            match = selected_clients[selected_clients[mail_col].astype(str).str.strip() == recipient]
            row = match.iloc[0] if len(match) else pd.Series(dtype=object)
            final_subject = render(subject, row)
            final_body = render(body, row)
            try:
                result = function(recipient, final_subject, final_body)
                status = "enviado" if action.startswith("Enviar") else "borrador"
                save_log(recipient, final_subject, status, str(result or "OK"), template_choice)
                correctos += 1
                results.append({"destinatario": recipient, "estado": status, "detalle": str(result or "OK")})
                details.success(f"✅ {recipient} · {status}")
            except Exception as error:
                errores += 1
                save_log(recipient, final_subject, "error", str(error), template_choice)
                results.append({"destinatario": recipient, "estado": "error", "detalle": str(error)})
                details.error(f"❌ {recipient} · {error}")
            percent = position / total
            progress.progress(percent, text=f"Progreso: {position}/{total} ({percent:.0%})")
            counters.write(f"Correctos: {correctos} · Errores: {errores} · Pendientes: {total - position}")
        current.success("Proceso finalizado.")
        progress.progress(1.0, text="Proceso completado")
        st.success(f"Finalizado: {correctos} correctos y {errores} errores.")
        st.download_button("Descargar resultado del envío", pd.DataFrame(results).to_csv(index=False).encode("utf-8-sig"), "resultado_envio.csv", "text/csv")

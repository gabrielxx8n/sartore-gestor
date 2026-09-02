from pathlib import Path
from datetime import datetime
from io import BytesIO
import json

import pandas as pd
import streamlit as st


BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "informes_temporales"
DATA_DIR.mkdir(exist_ok=True)

HISTORIAL_FILE = DATA_DIR / "historial_informes.json"
ULTIMO_ARCHIVO_FILE = DATA_DIR / "ultimo_informe.json"

st.set_page_config(
    page_title="Sartore · Informes",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        /* Fuerza interfaz oscura, independiente del modo del sistema */
        :root {
            color-scheme: dark !important;
        }

        html,
        body,
        [class*="css"] {
            color: #f4efe3;
        }

        .stApp {
            background:
                radial-gradient(circle at 4% 0%, rgba(166, 124, 42, .16), transparent 28%),
                radial-gradient(circle at 100% 0%, rgba(116, 83, 22, .12), transparent 30%),
                linear-gradient(135deg, #070707 0%, #10100e 52%, #090909 100%) !important;
            color: #f4efe3 !important;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }

        [data-testid="stHeader"] {
            background: rgba(7, 7, 7, 0) !important;
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4, p, label, span, li {
            color: #f4efe3 !important;
        }

        .hero {
            background:
                linear-gradient(135deg, rgba(42, 35, 20, .98), rgba(19, 18, 15, .98));
            border: 1px solid #7e5c22;
            border-top: 2px solid #d1a54b;
            border-radius: 20px;
            padding: 1.35rem 1.5rem;
            margin: .15rem 0 1.2rem 0;
            box-shadow: 0 20px 50px rgba(0, 0, 0, .38);
        }

        .hero-kicker {
            color: #d7af5a !important;
            font-size: .76rem;
            font-weight: 800;
            letter-spacing: .16em;
            margin-bottom: .4rem;
        }

        .hero-title {
            color: #fffaf0 !important;
            font-size: clamp(1.8rem, 4.6vw, 2.85rem);
            line-height: 1.08;
            font-weight: 800;
            margin: 0;
        }

        .hero-subtitle {
            color: #cfc5af !important;
            font-size: 1rem;
            margin: .7rem 0 0 0;
            line-height: 1.55;
        }

        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(34, 31, 24, .96), rgba(20, 19, 16, .96));
            border: 1px solid #5f4a25;
            border-radius: 15px;
            padding: .9rem;
            box-shadow: 0 10px 25px rgba(0, 0, 0, .2);
        }

        [data-testid="stMetricLabel"] {
            color: #cdbd9a !important;
            font-size: .83rem;
        }

        [data-testid="stMetricValue"] {
            color: #f1c566 !important;
            font-weight: 800;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: .45rem;
            border-bottom: 1px solid #5f4a25;
        }

        .stTabs [data-baseweb="tab"] {
            color: #c8baa0 !important;
            font-weight: 700;
            padding: .65rem .95rem;
            background: transparent;
        }

        .stTabs [aria-selected="true"] {
            color: #fff8e7 !important;
            background: linear-gradient(135deg, #7c591e, #4f3918) !important;
            border-radius: 10px 10px 0 0;
        }

        [data-testid="stFileUploader"] {
            background: rgba(30, 27, 21, .85);
            border: 1px dashed #b88b38;
            border-radius: 16px;
            padding: .85rem;
        }

        [data-testid="stFileUploader"] section {
            background: transparent !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            min-height: 43px;
            border-radius: 10px;
            border: 1px solid #d4a94f !important;
            background: linear-gradient(135deg, #b8862f, #735018) !important;
            color: #fffaf0 !important;
            font-weight: 800;
            letter-spacing: .01em;
            box-shadow: 0 7px 18px rgba(0, 0, 0, .26);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: #f0ce7a !important;
            background: linear-gradient(135deg, #c99c43, #875f20) !important;
            color: #ffffff !important;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid #594629;
            border-radius: 12px;
            overflow: hidden;
        }

        [data-testid="stDataFrame"] * {
            color: #efe8d9 !important;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        textarea {
            background: #171613 !important;
            color: #f5eddd !important;
            border-color: #69542d !important;
        }

        [data-testid="stExpander"] {
            border: 1px solid #594629;
            background: rgba(28, 26, 21, .78);
            border-radius: 12px;
        }

        [data-testid="stCaptionContainer"] p {
            color: #bdb199 !important;
        }

        @media (max-width: 700px) {
            .block-container {
                padding: .85rem .8rem 2.4rem .8rem;
            }

            .hero {
                padding: 1.05rem;
                border-radius: 16px;
            }

            .hero-title {
                font-size: 1.85rem;
            }

            [data-testid="stMetric"] {
                padding: .72rem;
                border-radius: 12px;
            }

            .stTabs [data-baseweb="tab"] {
                font-size: .88rem;
                padding: .6rem .65rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def cargar_historial():
    if not HISTORIAL_FILE.exists():
        return []

    try:
        return json.loads(HISTORIAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def guardar_historial(historial):
    HISTORIAL_FILE.write_text(
        json.dumps(historial, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def registrar_evento(tipo, archivo, detalle=""):
    historial = cargar_historial()

    historial.insert(
        0,
        {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tipo": tipo,
            "archivo": archivo,
            "detalle": detalle,
        },
    )

    guardar_historial(historial)


def guardar_ultimo_informe(nombre, contenido, extension):
    ruta = DATA_DIR / f"ultimo_informe{extension}"
    ruta.write_bytes(contenido)

    datos = {
        "nombre": nombre,
        "ruta": str(ruta),
        "extension": extension,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    ULTIMO_ARCHIVO_FILE.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return ruta


def cargar_ultimo_informe():
    if not ULTIMO_ARCHIVO_FILE.exists():
        return None

    try:
        datos = json.loads(ULTIMO_ARCHIVO_FILE.read_text(encoding="utf-8"))
        if Path(datos["ruta"]).exists():
            return datos
    except Exception:
        pass

    return None


def leer_tabla(contenido, extension):
    if extension == ".csv":
        for codificacion in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return pd.read_csv(BytesIO(contenido), encoding=codificacion), codificacion

            except Exception:
                continue

        raise ValueError("No fue posible leer el archivo CSV.")

    if extension in (".xlsx", ".xls"):
        return pd.read_excel(BytesIO(contenido)), "Excel"

    return None, ""


def mostrar_inicio():
    ultimo = cargar_ultimo_informe()
    historial = cargar_historial()

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">SARTORE · INFORMES</div>
            <div class="hero-title">Panel de información</div>
            <div class="hero-subtitle">
                Sube, consulta y descarga informes desde cualquier dispositivo.
                La interfaz usa modo oscuro permanente.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uno, dos, tres = st.columns(3)

    uno.metric("Cambios registrados", len(historial))
    dos.metric("Última actualización", ultimo["fecha"] if ultimo else "Sin datos")
    tres.metric("Tema", "Negro · Dorado")

    if ultimo:
        st.success(f"Último informe disponible: {ultimo['nombre']}")
    else:
        st.info("Aún no hay informes guardados. Carga uno en la pestaña Informes.")


def mostrar_informes():
    st.subheader("Cargar informe")
    st.caption(
        "Formatos permitidos: Excel, CSV y PDF. Por ahora, el guardado es temporal "
        "mientras desarrollamos la versión con almacenamiento permanente."
    )

    archivo = st.file_uploader(
        "Selecciona un archivo",
        type=["xlsx", "xls", "csv", "pdf"],
        help="El último archivo guardado reemplaza el informe temporal anterior.",
    )

    nota = st.text_input(
        "Nota o descripción del cambio",
        placeholder="Ejemplo: Se actualizó el informe semanal con nuevos datos.",
    )

    if archivo is not None:
        extension = Path(archivo.name).suffix.lower()
        contenido = archivo.getvalue()

        st.write(f"**Archivo seleccionado:** {archivo.name}")

        if extension in (".xlsx", ".xls", ".csv"):
            try:
                tabla, formato = leer_tabla(contenido, extension)

                filas = len(tabla)
                columnas = len(tabla.columns)
                vacios = int(tabla.isna().sum().sum())
                duplicados = int(tabla.duplicated().sum())

                uno, dos, tres, cuatro = st.columns(4)
                uno.metric("Filas", f"{filas:,}")
                dos.metric("Columnas", columnas)
                tres.metric("Celdas vacías", f"{vacios:,}")
                cuatro.metric("Duplicados", f"{duplicados:,}")

                st.markdown("### Vista previa")
                st.dataframe(
                    tabla.head(100),
                    use_container_width=True,
                    hide_index=True,
                )

                with st.expander("Resumen del archivo"):
                    resumen = pd.DataFrame(
                        {
                            "Columna": tabla.columns.astype(str),
                            "Tipo": tabla.dtypes.astype(str).values,
                            "Vacíos": tabla.isna().sum().values,
                            "Valores únicos": [
                                tabla[columna].nunique(dropna=True)
                                for columna in tabla.columns
                            ],
                        }
                    )

                    st.dataframe(
                        resumen,
                        use_container_width=True,
                        hide_index=True,
                    )

                if len(tabla.columns):
                    columna = st.selectbox(
                        "Gráfico rápido",
                        ["No mostrar gráfico"] + list(tabla.columns),
                    )

                    if columna != "No mostrar gráfico":
                        conteo = (
                            tabla[columna]
                            .fillna("Sin dato")
                            .astype(str)
                            .value_counts()
                            .head(10)
                        )
                        st.bar_chart(conteo)

            except Exception as error:
                st.error(f"No se pudo analizar el archivo: {error}")

        else:
            st.info(
                "El PDF puede guardarse y descargarse. El análisis de contenido "
                "se agregará en una etapa posterior."
            )

        if st.button(
            "Guardar informe temporal",
            type="primary",
            use_container_width=True,
        ):
            guardar_ultimo_informe(archivo.name, contenido, extension)

            registrar_evento(
                "Informe cargado",
                archivo.name,
                nota.strip() or "Archivo actualizado desde la aplicación.",
            )

            st.success(
                "Informe guardado temporalmente. Puedes revisarlo desde otro dispositivo."
            )
            st.rerun()

    st.divider()
    st.subheader("Último informe guardado")

    ultimo = cargar_ultimo_informe()

    if not ultimo:
        st.info("No hay ningún informe temporal guardado.")
        return

    ruta = Path(ultimo["ruta"])

    if not ruta.exists():
        st.warning("El archivo temporal ya no está disponible. Súbelo nuevamente.")
        return

    contenido = ruta.read_bytes()

    izquierda, derecha = st.columns([2, 1])

    with izquierda:
        st.write(f"**{ultimo['nombre']}**")
        st.caption(f"Actualizado: {ultimo['fecha']}")

    with derecha:
        st.download_button(
            "Descargar informe",
            data=contenido,
            file_name=ultimo["nombre"],
            use_container_width=True,
        )

    extension = ultimo["extension"]

    if extension in (".xlsx", ".xls", ".csv"):
        try:
            tabla, _ = leer_tabla(contenido, extension)
            st.dataframe(
                tabla.head(100),
                use_container_width=True,
                hide_index=True,
            )
        except Exception as error:
            st.warning(f"No se pudo mostrar la vista previa: {error}")

    elif extension == ".pdf":
        st.info("El informe PDF está guardado y listo para descargar.")


def mostrar_historial():
    st.subheader("Historial")
    st.caption(
        "Registro de archivos cargados, notas y cambios agregados a esta versión."
    )

    historial = cargar_historial()

    if historial:
        tabla = pd.DataFrame(historial)

        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "fecha": "Fecha",
                "tipo": "Tipo",
                "archivo": "Archivo",
                "detalle": "Detalle",
            },
        )

        st.download_button(
            "Descargar historial CSV",
            data=tabla.to_csv(index=False).encode("utf-8-sig"),
            file_name="historial_informes.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:
        st.info("Aún no hay cambios registrados.")

    st.divider()
    st.subheader("Agregar información")

    nota = st.text_area(
        "Nota para el historial",
        placeholder="Ejemplo: Se revisó el informe de ventas y se agregaron nuevos registros.",
    )

    if st.button("Registrar nota", use_container_width=True):
        if nota.strip():
            registrar_evento(
                "Nota agregada",
                "Sin archivo",
                nota.strip(),
            )
            st.success("Nota agregada correctamente.")
            st.rerun()

        else:
            st.warning("Escribe una nota antes de registrarla.")


mostrar_inicio()

tab_informes, tab_historial = st.tabs(["Informes", "Historial"])

with tab_informes:
    mostrar_informes()

with tab_historial:
    mostrar_historial()

st.caption(
    "Versión temporal de desarrollo · Los archivos se mantienen mientras la instancia "
    "de Streamlit esté disponible."
)

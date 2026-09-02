from pathlib import Path
from datetime import datetime
from io import BytesIO
import json

import pandas as pd
import streamlit as st

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "informes_temporales"
DATA_DIR.mkdir(exist_ok=True)

HISTORIAL_FILE = DATA_DIR / "historial_informes.json"
ULTIMO_ARCHIVO_FILE = DATA_DIR / "ultimo_informe.json"

st.set_page_config(
    page_title="Sartore · Informes",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        :root {
            color-scheme: dark;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 0%, #173b64 0%, transparent 30%),
                radial-gradient(circle at 100% 10%, #16263f 0%, transparent 32%),
                #08111e;
            color: #eaf2ff;
        }

        [data-testid="stHeader"] {
            background: rgba(8, 17, 30, 0);
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, p, label, span {
            color: #eaf2ff !important;
        }

        .hero {
            background: linear-gradient(135deg, #0d2745, #10233b);
            border: 1px solid #285783;
            border-radius: 22px;
            padding: 1.35rem 1.5rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 18px 45px rgba(0, 0, 0, .24);
        }

        .hero-kicker {
            color: #85c7ff !important;
            font-size: .76rem;
            font-weight: 700;
            letter-spacing: .12em;
            margin-bottom: .35rem;
        }

        .hero-title {
            color: #ffffff !important;
            font-size: clamp(1.7rem, 4vw, 2.7rem);
            line-height: 1.1;
            font-weight: 800;
            margin: 0;
        }

        .hero-subtitle {
            color: #b6c9df !important;
            margin: .65rem 0 0 0;
            font-size: 1rem;
        }

        [data-testid="stMetric"] {
            background: rgba(15, 37, 62, .88);
            border: 1px solid #264d75;
            border-radius: 16px;
            padding: .9rem;
        }

        [data-testid="stMetricLabel"] {
            color: #9eb7d1 !important;
        }

        [data-testid="stMetricValue"] {
            color: #f5fbff !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: .4rem;
            border-bottom: 1px solid #28445f;
        }

        .stTabs [data-baseweb="tab"] {
            color: #abc3db !important;
            font-weight: 700;
            padding: .6rem .9rem;
        }

        .stTabs [aria-selected="true"] {
            color: #ffffff !important;
            background: #174a78;
            border-radius: 10px 10px 0 0;
        }

        [data-testid="stFileUploader"] {
            background: rgba(15, 37, 62, .75);
            border: 1px dashed #4788c2;
            border-radius: 16px;
            padding: .7rem;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 10px;
            border: 1px solid #4388c5;
            background: linear-gradient(135deg, #1769aa, #0c4e85);
            color: white;
            font-weight: 700;
            min-height: 42px;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: #8bc8ff;
            background: linear-gradient(135deg, #237dc0, #155f9e);
            color: white;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid #264d75;
            border-radius: 12px;
            overflow: hidden;
        }

        @media (max-width: 700px) {
            .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
                padding-top: .8rem;
            }

            .hero {
                border-radius: 16px;
                padding: 1rem;
            }

            [data-testid="stMetric"] {
                padding: .7rem;
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


def registrar_evento(tipo, nombre, detalle=""):
    historial = cargar_historial()

    historial.insert(
        0,
        {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tipo": tipo,
            "archivo": nombre,
            "detalle": detalle,
        },
    )

    guardar_historial(historial)


def guardar_ultimo_archivo(nombre, contenido, extension):
    ruta = DATA_DIR / f"ultimo_informe{extension}"
    ruta.write_bytes(contenido)

    ULTIMO_ARCHIVO_FILE.write_text(
        json.dumps(
            {
                "nombre": nombre,
                "ruta": str(ruta),
                "extension": extension,
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return ruta


def cargar_ultimo_archivo():
    if not ULTIMO_ARCHIVO_FILE.exists():
        return None

    try:
        datos = json.loads(ULTIMO_ARCHIVO_FILE.read_text(encoding="utf-8"))
        ruta = Path(datos["ruta"])

        if not ruta.exists():
            return None

        return datos
    except Exception:
        return None


def leer_tabla(contenido, extension):
    if extension == ".csv":
        errores = []

        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return pd.read_csv(BytesIO(contenido), encoding=encoding), encoding
            except Exception as error:
                errores.append(str(error))

        raise ValueError("No fue posible leer el CSV con codificaciones comunes.")

    if extension in (".xlsx", ".xls"):
        return pd.read_excel(BytesIO(contenido)), "Excel"

    return None, ""


def estadisticas_tabla(tabla):
    total = len(tabla)
    columnas = len(tabla.columns)
    vacios = int(tabla.isna().sum().sum())
    duplicados = int(tabla.duplicated().sum())

    return total, columnas, vacios, duplicados


def pantalla_inicio():
    ultimo = cargar_ultimo_archivo()
    historial = cargar_historial()

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">SARTORE · PANEL MÓVIL</div>
            <div class="hero-title">Informes y actualizaciones</div>
            <div class="hero-subtitle">
                Carga archivos, revisa información y consulta el registro de cambios
                desde computador o celular.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)
    a.metric("Archivos registrados", len(historial))
    b.metric("Última actualización", ultimo["fecha"] if ultimo else "Sin datos")
    c.metric("Modo", "Oscuro")

    if ultimo:
        st.success(f"Último informe disponible: {ultimo['nombre']}")
    else:
        st.info("Aún no hay un informe cargado. Ve a la pestaña Informes para comenzar.")


def pantalla_informes():
    st.subheader("Cargar informe")
    st.caption(
        "Puedes cargar archivos Excel, CSV o PDF. Esta etapa guarda los archivos "
        "temporalmente mientras construimos el almacenamiento definitivo."
    )

    archivo = st.file_uploader(
        "Selecciona un informe",
        type=["xlsx", "xls", "csv", "pdf"],
        help="El archivo reemplaza el informe temporal actual.",
    )

    nota = st.text_input(
        "Nota del cambio",
        placeholder="Ejemplo: Informe mensual actualizado con datos de agosto",
    )

    if archivo is not None:
        extension = Path(archivo.name).suffix.lower()
        contenido = archivo.getvalue()

        st.write(f"**Archivo seleccionado:** {archivo.name}")

        if extension in (".xlsx", ".xls", ".csv"):
            try:
                tabla, formato = leer_tabla(contenido, extension)
                filas, columnas, vacios, duplicados = estadisticas_tabla(tabla)

                a, b, c, d = st.columns(4)
                a.metric("Filas", f"{filas:,}")
                b.metric("Columnas", columnas)
                c.metric("Celdas vacías", f"{vacios:,}")
                d.metric("Duplicados", f"{duplicados:,}")

                st.markdown("### Vista previa")
                st.dataframe(tabla.head(100), use_container_width=True, hide_index=True)

                with st.expander("Resumen por columna"):
                    resumen = pd.DataFrame(
                        {
                            "Columna": tabla.columns.astype(str),
                            "Tipo": tabla.dtypes.astype(str).values,
                            "Valores vacíos": tabla.isna().sum().values,
                            "Valores únicos": [
                                tabla[col].nunique(dropna=True) for col in tabla.columns
                            ],
                        }
                    )
                    st.dataframe(resumen, use_container_width=True, hide_index=True)

                if len(tabla.columns) > 0:
                    seleccion = st.selectbox(
                        "Gráfico rápido",
                        ["No mostrar gráfico"] + list(tabla.columns),
                    )

                    if seleccion != "No mostrar gráfico":
                        valores = (
                            tabla[seleccion]
                            .fillna("Sin dato")
                            .astype(str)
                            .value_counts()
                            .head(10)
                        )

                        st.bar_chart(valores)

            except Exception as error:
                st.error(f"No se pudo leer el archivo: {error}")

        elif extension == ".pdf":
            st.info(
                "El PDF está listo para guardarse. En esta versión se registra y "
                "se puede descargar, pero no se analiza su contenido."
            )

        if st.button("Guardar informe temporal", type="primary", use_container_width=True):
            ruta = guardar_ultimo_archivo(archivo.name, contenido, extension)
            registrar_evento(
                "Informe cargado",
                archivo.name,
                nota.strip() or f"Guardado temporalmente en {ruta.name}",
            )
            st.success("Informe guardado temporalmente. Ya puedes revisarlo desde otro dispositivo.")
            st.rerun()

    st.divider()
    st.subheader("Último informe guardado")

    ultimo = cargar_ultimo_archivo()

    if not ultimo:
        st.info("No hay ningún informe temporal guardado.")
        return

    ruta = Path(ultimo["ruta"])
    contenido = ruta.read_bytes()

    x, y = st.columns([2, 1])

    with x:
        st.write(f"**{ultimo['nombre']}**")
        st.caption(f"Actualizado: {ultimo['fecha']}")

    with y:
        st.download_button(
            "Descargar",
            data=contenido,
            file_name=ultimo["nombre"],
            use_container_width=True,
        )

    extension = ultimo["extension"]

    if extension in (".xlsx", ".xls", ".csv"):
        try:
            tabla, _ = leer_tabla(contenido, extension)
            st.dataframe(tabla.head(100), use_container_width=True, hide_index=True)
        except Exception as error:
            st.warning(f"No se pudo mostrar la vista previa: {error}")

    elif extension == ".pdf":
        st.info("Informe PDF guardado. Puedes descargarlo con el botón anterior.")


def pantalla_historial():
    st.subheader("Historial de cambios")
    st.caption(
        "Registro de informes subidos y notas agregadas durante la etapa de pruebas."
    )

    historial = cargar_historial()

    if not historial:
        st.info("Aún no existen cambios registrados.")
        return

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

    st.divider()

    st.subheader("Agregar nota al historial")
    nueva_nota = st.text_area(
        "Detalle",
        placeholder="Ejemplo: Se corrigieron los datos del informe semanal.",
    )

    if st.button("Registrar nota", use_container_width=True):
        if nueva_nota.strip():
            registrar_evento("Nota agregada", "Sin archivo", nueva_nota.strip())
            st.success("Nota registrada correctamente.")
            st.rerun()
        else:
            st.warning("Escribe una nota antes de registrarla.")


pantalla_inicio()

tab_informes, tab_historial = st.tabs(["Informes", "Historial"])

with tab_informes:
    pantalla_informes()

with tab_historial:
    pantalla_historial()

st.caption(
    "Versión temporal: los archivos se guardan en el servidor de Streamlit mientras "
    "desarrollamos el almacenamiento permanente."
)

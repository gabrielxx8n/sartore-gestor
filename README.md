# Sartore · Gestor de correos y encuestas

Aplicación interna construida con Streamlit para gestionar clientes, redactar correos personalizados con Gmail y analizar encuestas CSV de Sartore La Barbería.

## Funciones

- Carga de clientes desde Excel.
- Búsqueda y selección de clientes.
- Correos manuales que no existen en el Excel.
- Plantillas de correo reutilizables.
- Personalización mediante campos como `{Nombres}`, `{Apellidos}`, `{Email}` y `{Ciudad}`.
- Envío directo mediante Gmail API o creación de borradores.
- Barra de progreso y detalle por destinatario.
- Historial de envíos.
- Carga manual de CSV de encuestas.
- Filtros de encuestas por texto, fecha y presencia de correo.
- Detección automática de correos en cualquier columna del CSV.
- Gráficos de respuestas y exportación de datos.
- Ocultamiento de columnas de puntuación vacías o con valores como `0.00 / 0` y `-- / 0`.

## Requisitos

- Python 3.10 o superior.
- Una cuenta de Google con Gmail API configurada.
- Archivo OAuth de Google llamado `credentials.json` para ejecución local.

## Instalación local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecutar localmente

```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

## Archivos privados

No subas estos archivos a GitHub:

- `credentials.json`
- `token.json`
- `.env`
- `.streamlit/secrets.toml`
- `clientes_actual.xlsx`
- `historial_envios.csv`
- Archivos CSV dentro de `encuestas/`

El archivo `.gitignore` del proyecto ya está preparado para excluirlos.

## Preparar GitHub

1. Crea un repositorio privado en GitHub, por ejemplo `sartore-gestor`.
2. Abre PowerShell dentro de la carpeta del proyecto.
3. Ejecuta:

```powershell
git init
git branch -M main
git add .
git commit -m "Primera versión de Sartore Gestor"
git remote add origin https://github.com/TU_USUARIO/sartore-gestor.git
git push -u origin main
```

Antes de `git add .`, revisa que `.gitignore` esté en la misma carpeta que `app.py`.

## Despliegue en Streamlit Community Cloud

1. Entra a https://share.streamlit.io/ e inicia sesión con GitHub.
2. Selecciona **Create app**.
3. Elige el repositorio `sartore-gestor`, rama `main` y archivo principal `app.py`.
4. Instala dependencias desde `requirements.txt` automáticamente.
5. Carga secretos desde la sección **Settings → Secrets**.

> Importante: la autenticación actual basada en `credentials.json` y `token.json` funciona mejor en ejecución local. Para alojar la aplicación de forma estable en la nube, debes adaptar `gmail_auth.py` para leer credenciales desde secretos de Streamlit y guardar clientes, encuestas e historial en una base de datos o almacenamiento externo.

## Estructura esperada

```text
correo_gmail/
├── app.py
├── mailer.py
├── gmail_auth.py
├── requirements.txt
├── .gitignore
├── README.md
├── credentials.json        # Privado, solo local
├── token.json              # Privado, se crea al autorizar Gmail
├── clientes_actual.xlsx    # Privado, solo local
├── historial_envios.csv    # Privado, se crea al usar la app
├── encuestas/
│   └── .gitkeep
└── .venv/                  # Privado, solo local
```

## Seguridad

- Mantén el repositorio como privado.
- No compartas tus credenciales OAuth ni tu token de Gmail.
- Antes de hacer envíos a clientes, realiza siempre una prueba con tu propio correo.
- Revisa el historial después de cada campaña.

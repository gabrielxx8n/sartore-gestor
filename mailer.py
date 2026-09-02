import base64
import html
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.errors import HttpError

from gmail_auth import obtener_servicio_gmail

MARKDOWN_LINK_REGEX = re.compile(
    r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
    re.IGNORECASE,
)
URL_REGEX = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)


def markdown_a_html(cuerpo):
    enlaces = []

    def proteger_enlace(match):
        etiqueta = html.escape(match.group(1).strip())
        url = html.escape(match.group(2).strip(), quote=True)
        marcador = f"%%LINK_SARTORE_{len(enlaces)}%%"
        enlaces.append(
            f'<a href="{url}" '
            'style="color:#a47b38;text-decoration:underline;font-weight:bold;">'
            f"{etiqueta}</a>"
        )
        return marcador

    contenido = MARKDOWN_LINK_REGEX.sub(proteger_enlace, str(cuerpo))
    contenido = html.escape(contenido)

    def convertir_url(match):
        url = match.group(0)
        return (
            f'<a href="{url}" '
            'style="color:#a47b38;text-decoration:underline;">'
            f"{url}</a>"
        )

    contenido = URL_REGEX.sub(convertir_url, contenido)

    for indice, enlace in enumerate(enlaces):
        contenido = contenido.replace(f"%%LINK_SARTORE_{indice}%%", enlace)

    contenido = contenido.replace("\n", "<br>")

    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,Helvetica,sans-serif;color:#202020;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f5f3ef;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="620" cellspacing="0" cellpadding="0" border="0" style="max-width:620px;width:100%;background:#ffffff;border:1px solid #e3ddd3;">
          <tr>
            <td style="background:#101820;padding:22px 30px;text-align:center;">
              <div style="color:#dec48f;font-family:Georgia,serif;font-size:26px;letter-spacing:5px;font-weight:bold;">SARTORE</div>
              <div style="color:#d7d7d7;font-size:10px;letter-spacing:2px;margin-top:6px;">LA BARBERÍA</div>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 30px;font-size:16px;line-height:1.65;color:#282828;">
              {contenido}
            </td>
          </tr>
          <tr>
            <td style="padding:16px 30px;background:#f6f2eb;color:#777777;text-align:center;font-size:11px;line-height:1.5;">
              Sartore La Barbería<br>
              Este correo fue enviado de forma personalizada.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def markdown_a_texto_plano(cuerpo):
    return MARKDOWN_LINK_REGEX.sub(
        lambda match: f"{match.group(1)}: {match.group(2)}",
        str(cuerpo),
    )


def construir_mensaje(destinatario, asunto, cuerpo):
    mensaje = MIMEMultipart("alternative")
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto

    mensaje.attach(MIMEText(markdown_a_texto_plano(cuerpo), "plain", "utf-8"))
    mensaje.attach(MIMEText(markdown_a_html(cuerpo), "html", "utf-8"))

    raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode("utf-8")
    return {"raw": raw}


def enviar_correo(destinatario, asunto, cuerpo):
    servicio = obtener_servicio_gmail()
    mensaje = construir_mensaje(destinatario, asunto, cuerpo)

    try:
        respuesta = (
            servicio.users()
            .messages()
            .send(userId="me", body=mensaje)
            .execute()
        )
        return respuesta.get("id", "Enviado correctamente")
    except HttpError as error:
        raise RuntimeError(
            f"Gmail no pudo enviar el correo a {destinatario}: {error}"
        ) from error


def crear_borrador(destinatario, asunto, cuerpo):
    servicio = obtener_servicio_gmail()
    mensaje = construir_mensaje(destinatario, asunto, cuerpo)

    try:
        respuesta = (
            servicio.users()
            .drafts()
            .create(userId="me", body={"message": mensaje})
            .execute()
        )
        return respuesta.get("id", "Borrador creado correctamente")
    except HttpError as error:
        raise RuntimeError(
            f"Gmail no pudo crear el borrador para {destinatario}: {error}"
        ) from error


def probar_conexion_gmail():
    servicio = obtener_servicio_gmail()
    perfil = servicio.users().getProfile(userId="me").execute()
    return perfil.get("emailAddress", "Gmail conectado")

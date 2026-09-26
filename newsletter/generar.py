#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Palabras con historia — generador del newsletter y de las páginas estáticas.

Uso:
  python newsletter/generar.py            # genera páginas (docs/) y vista previa del correo (salida/)
  python newsletter/generar.py --enviar   # además, envía el correo por SMTP
"""

import argparse
import html
import json
import os
import smtplib
import unicodedata
from datetime import date
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = json.loads((RAIZ / "newsletter" / "palabras.json").read_text(encoding="utf-8"))
PALABRAS = DATOS["palabras"]

DOCS = RAIZ / "docs"
SALIDA = RAIZ / "salida"

SITE_URL = os.environ.get("SITE_URL", "https://TU-USUARIO.github.io/palabras-con-historia/").rstrip("/")
TITULO = "Palabras con historia"
LEMA = "El origen y significado de palabras que no son tan conocidas, pero que son útiles."

CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #f6f4ef;
  color: #1c1b19;
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.7;
}
.contenedor { max-width: 640px; margin: 0 auto; padding: 64px 24px 80px; }
.cabecera { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #d8d4cc; padding-bottom: 16px; }
.cabecera .marca { letter-spacing: .22em; text-transform: uppercase; font-size: 11px; color: #8a857c; font-family: Helvetica, Arial, sans-serif; }
.cabecera .numero { font-size: 12px; color: #8a857c; font-family: Helvetica, Arial, sans-serif; }
.palabra { font-size: 64px; font-weight: normal; margin: 48px 0 4px; letter-spacing: .01em; }
.premisa { font-size: 19px; color: #4a463f; margin: 8px 0 40px; font-style: italic; }
h2 { font-size: 13px; letter-spacing: .18em; text-transform: uppercase; color: #8a857c; font-family: Helvetica, Arial, sans-serif; margin: 36px 0 6px; font-weight: normal; }
p { margin: 0 0 18px; font-size: 16.5px; }
.boton {
  display: inline-block; margin-top: 12px; padding: 14px 30px;
  background: #1c1b19; color: #f6f4ef; text-decoration: none;
  font-family: Helvetica, Arial, sans-serif; font-size: 12px;
  letter-spacing: .14em; text-transform: uppercase;
}
.boton:hover { background: #3a362f; }
.indice { margin-top: 56px; border-top: 1px solid #d8d4cc; padding-top: 20px; }
.indice p { font-family: Helvetica, Arial, sans-serif; font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: #8a857c; margin-bottom: 10px; }
.indice a { display: inline-block; margin: 0 14px 8px 0; color: #1c1b19; text-decoration: none; border-bottom: 1px solid #c9c4ba; font-size: 15px; }
.indice a:hover { border-color: #1c1b19; }
.pie { margin-top: 56px; font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #a09a8f; letter-spacing: .05em; }
"""


def dia_de_hoy():
    hoy = date.today()
    numero = (hoy.year - 2026) * 52 + hoy.isocalendar()[1]
    indice = (hoy.timetuple().tm_yday - 1) % len(PALABRAS)
    return PALABRAS[indice], numero


def pagina(palabra, numero, es_portada=False):
    palabras = html.escape(palabra["palabra"])
    premisa = html.escape(palabra["premisa"])
    significado = html.escape(palabra["significado"])
    origen = html.escape(palabra["origen"])
    detalle = html.escape(palabra["detalle"])
    url = f"{SITE_URL}/palabras/{palabra['slug']}.html"
    nav = ""
    if not es_portada:
        nav = f'<p style="margin-top:48px"><a class="boton" href="{SITE_URL}/">Todas las palabras</a></p>'
    indice = "".join(
        f'<a href="{SITE_URL}/palabras/{p["slug"]}.html">{html.escape(p["palabra"])}</a>'
        for p in PALABRAS
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{palabras} — {TITULO}</title>
<link rel="stylesheet" href="{SITE_URL}/estilos.css">
</head>
<body>
<div class="contenedor">
  <header class="cabecera">
    <span class="marca">{TITULO}</span>
    <span class="numero">Nº {numero}</span>
  </header>
  <h1 class="palabra">{palabras}</h1>
  <p class="premisa">{premisa}</p>

  <h2>Significado</h2>
  <p>{significado}</p>

  <h2>Origen</h2>
  <p>{origen}</p>

  <h2>En detalle</h2>
  <p>{detalle}</p>

  {nav}

  <div class="indice">
    <p>Ediciones anteriores y futuras</p>
    {indice}
  </div>

  <footer class="pie">{TITULO} · {LEMA}</footer>
</div>
</body>
</html>
"""


def correo(palabra, numero):
    palabras = html.escape(palabra["palabra"])
    premisa = html.escape(palabra["premisa"])
    url = f"{SITE_URL}/palabras/{palabra['slug']}.html"
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{palabras}</title></head>
<body style="margin:0;padding:0;background:#f6f4ef;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f4ef;">
    <tr><td align="center" style="padding:48px 24px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        <tr>
          <td style="border-bottom:1px solid #d8d4cc;padding-bottom:16px;">
            <span style="font-family:Helvetica,Arial,sans-serif;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#8a857c;">Palabras con historia</span>
            <span style="font-family:Helvetica,Arial,sans-serif;font-size:12px;color:#8a857c;float:right;">Nº {numero}</span>
          </td>
        </tr>
        <tr><td style="padding-top:40px;">
          <h1 style="margin:0 0 12px;font-family:Georgia,serif;font-size:52px;font-weight:normal;color:#1c1b19;">{palabras}</h1>
          <p style="margin:0 0 28px;font-family:Georgia,serif;font-size:19px;font-style:italic;line-height:1.6;color:#4a463f;">{premisa}</p>
          <a href="{url}" style="display:inline-block;padding:14px 30px;background:#1c1b19;color:#f6f4ef;text-decoration:none;font-family:Helvetica,Arial,sans-serif;font-size:12px;letter-spacing:.14em;text-transform:uppercase;">Descubrir el significado</a>
        </td></tr>
        <tr><td style="padding-top:48px;border-top:1px solid #d8d4cc;">
          <p style="margin:0;font-family:Helvetica,Arial,sans-serif;font-size:11px;color:#a09a8f;">El origen y significado de palabras que no son tan conocidas, pero que son útiles.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def generar_paginas(palabra_hoy, numero):
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "palabras").mkdir(parents=True, exist_ok=True)
    (DOCS / "estilos.css").write_text(CSS, encoding="utf-8")
    for palabra in PALABRAS:
        (DOCS / "palabras" / f"{palabra['slug']}.html").write_text(
            pagina(palabra, numero), encoding="utf-8"
        )
    (DOCS / "index.html").write_text(
        pagina(palabra_hoy, numero, es_portada=True), encoding="utf-8"
    )


def generar_preview(palabra, numero):
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"email_{palabra['slug']}.html"
    ruta.write_text(correo(palabra, numero), encoding="utf-8")
    return ruta


def enviar(palabra, numero):
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    puerto = int(os.environ.get("SMTP_PORT", "465"))
    usuario = os.environ["SMTP_USER"]
    clave = os.environ["SMTP_PASS"]
    destino = os.environ["TO_EMAIL"]
    asunto = f"{palabra['palabra']} — Nº {numero}"

    msg = MIMEText(correo(palabra, numero), "html", "utf-8")
    msg["Subject"] = asunto
    msg["From"] = formataddr(("Palabras con historia", usuario))
    msg["To"] = destino

    with smtplib.SMTP_SSL(host, puerto, timeout=60) as smtp:
        smtp.login(usuario, clave)
        smtp.sendmail(usuario, [destino], msg.as_string())
    print(f"[+] Enviado a {destino}: {asunto}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--enviar", action="store_true", help="enviar el correo además de generar")
    args = parser.parse_args()

    palabra, numero = dia_de_hoy()
    generar_paginas(palabra, numero)
    preview = generar_preview(palabra, numero)

    print(f"[i] Palabra de hoy: {palabra['palabra']} (Nº {numero})")
    print(f"[i] Páginas generadas en: {DOCS}")
    print(f"[i] Vista previa del correo: {preview}")

    if args.enviar:
        enviar(palabra, numero)
    else:
        print("[i] Para enviar: python newsletter/generar.py --enviar")


if __name__ == "__main__":
    main()
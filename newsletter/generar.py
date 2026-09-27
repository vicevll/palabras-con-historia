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
import shutil
import smtplib
import unicodedata
from datetime import date
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

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
.pie { margin-top: 56px; font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #a09a8f; letter-spacing: .05em; }
"""


EDICION_INICIO = date(2026, 9, 26)


def dia_de_hoy():
    hoy = date.today()
    numero = (hoy - EDICION_INICIO).days + 1
    indice = (hoy.timetuple().tm_yday - 1) % len(PALABRAS)
    return PALABRAS[indice], numero


def pagina(palabra, numero):
    palabras = html.escape(palabra["palabra"])
    premisa = html.escape(palabra["premisa"])
    significado = html.escape(palabra["significado"])
    origen = html.escape(palabra["origen"])
    detalle = html.escape(palabra["detalle"])
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

  <footer class="pie">{TITULO} · {LEMA}</footer>
</div>
</body>
</html>
"""


def _fuente(serif, tam):
    candidatos = []
    if os.name == "nt":
        base = Path("C:/Windows/Fonts")
        if serif:
            candidatos = [base / "georgia.ttf", base / "times.ttf"]
        else:
            candidatos = [base / "arial.ttf", base / "segoeui.ttf"]
    else:
        if serif:
            candidatos = [Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")]
        else:
            candidatos = [Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for c in candidatos:
        if c.exists():
            return ImageFont.truetype(str(c), tam)
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:
        return ImageFont.load_default()


def _texto_ajustado(draw, texto, fuente, ancho_max):
    lineas = []
    for parrafo in texto.split("\n"):
        palabras_linea = []
        for p in parrafo.split(" "):
            prueba = " ".join(palabras_linea + [p])
            if draw.textlength(prueba, font=fuente) <= ancho_max:
                palabras_linea.append(p)
            else:
                if palabras_linea:
                    lineas.append(" ".join(palabras_linea))
                palabras_linea = [p]
        if palabras_linea:
            lineas.append(" ".join(palabras_linea))
    return lineas


def imagen_story(palabra, numero, ruta):
    """Imagen 1080x1920 lista para publicar como historia de Instagram."""
    ancho, alto = 1080, 1920
    img = Image.new("RGB", (ancho, alto), "#f6f4ef")
    draw = ImageDraw.Draw(img)
    tinta, gris, cuerpo = "#1c1b19", "#8a857c", "#4a463f"
    margen = 90
    ancho_util = ancho - 2 * margen

    fuente_marca = _fuente(serif=False, tam=34)
    draw.text((margen, 300), "PALABRAS CON HISTORIA", font=fuente_marca, fill=gris)
    draw.text((margen, 362), f"EDICIÓN Nº {numero}", font=fuente_marca, fill=gris)

    tam = 230
    fuente = _fuente(serif=True, tam=tam)
    while tam > 40 and draw.textlength(palabra["palabra"], font=fuente) > ancho_util:
        tam -= 10
        fuente = _fuente(serif=True, tam=tam)
    draw.text((margen, 580), palabra["palabra"], font=fuente, fill=tinta)

    y_linea = 580 + tam + 44
    draw.line([(margen, y_linea), (ancho - margen, y_linea)], fill="#d8d4cc", width=3)

    tam_prem = 54
    fuente_prem = _fuente(serif=True, tam=tam_prem)
    lineas = _texto_ajustado(draw, palabra["premisa"], fuente_prem, ancho_util)
    while len(lineas) > 6 and tam_prem > 34:
        tam_prem -= 4
        fuente_prem = _fuente(serif=True, tam=tam_prem)
        lineas = _texto_ajustado(draw, palabra["premisa"], fuente_prem, ancho_util)
    y = y_linea + 56
    for ln in lineas:
        draw.text((margen, y), ln, font=fuente_prem, fill=cuerpo)
        y += tam_prem + 26

    fuente_pie = _fuente(serif=False, tam=30)
    draw.text((margen, alto - 150), "Palabras con historia", font=fuente_pie, fill=gris)

    img.save(ruta, "PNG")
    return ruta


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
          <p style="margin:28px 0 0;font-family:Helvetica,Arial,sans-serif;font-size:12px;color:#a09a8f;">📸 Adjunta va una imagen en formato historia de Instagram (1080×1920): guárdala en tu teléfono y publícala como story.</p>
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
        pagina(palabra_hoy, numero), encoding="utf-8"
    )


def generar_preview(palabra, numero):
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"email_{palabra['slug']}.html"
    ruta.write_text(correo(palabra, numero), encoding="utf-8")
    return ruta


def enviar(palabra, numero):
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    puerto = int(os.environ.get("SMTP_PORT", "465"))
    usuario = os.environ.get("SMTP_USER", "")
    clave = os.environ.get("SMTP_PASS", "")
    destino = os.environ.get("TO_EMAIL", "")
    if not (usuario and clave and destino):
        print("[!] Sin secretos SMTP configurados; se omite el envío.")
        return
    asunto = f"{palabra['palabra']} — Nº {numero}"

    msg = MIMEMultipart()
    msg.attach(MIMEText(correo(palabra, numero), "html", "utf-8"))
    ruta_imagen = DOCS / "palabras" / f"{palabra['slug']}_historia.png"
    if ruta_imagen.exists():
        with ruta_imagen.open("rb") as f:
            adjunto = MIMEImage(f.read(), _subtype="png")
        adjunto.add_header("Content-Disposition", "attachment", filename=f"{palabra['slug']}_historia.png")
        msg.attach(adjunto)
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

    img_docs = DOCS / "palabras" / f"{palabra['slug']}_historia.png"
    img_salida = SALIDA / f"story_{palabra['slug']}.png"
    if PIL_DISPONIBLE:
        imagen_story(palabra, numero, img_docs)
        SALIDA.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(img_docs, img_salida)
    else:
        print("[!] Pillow no está instalado; se omite la imagen para Instagram. Instala con: pip install Pillow")

    print(f"[i] Palabra de hoy: {palabra['palabra']} (Nº {numero})")
    print(f"[i] Páginas generadas en: {DOCS}")
    print(f"[i] Vista previa del correo: {preview}")
    if PIL_DISPONIBLE:
        print(f"[i] Imagen para Instagram: {img_salida}")

    if args.enviar:
        enviar(palabra, numero)
    else:
        print("[i] Para enviar: python newsletter/generar.py --enviar")


if __name__ == "__main__":
    main()
# Palabras con historia

Newsletter semanal sobre el **origen y significado de palabras** poco conocidas pero útiles.
El correo es una premisa minimalista con un botón que lleva a una página donde se explica en detalle.
Todo corre gratis en GitHub Actions + GitHub Pages.

## Cómo funciona

- `newsletter/palabras.json` — banco de palabras (premisa, significado, origen, detalle).
- `newsletter/generar.py` — elige la palabra de la semana, genera el correo HTML y las páginas estáticas en `docs/`, y envía por SMTP.
- `.github/workflows/newsletter.yml` — dispara el envío cada lunes (08:30 UTC) y publica las páginas.
- `docs/` — sitio en GitHub Pages con la explicación completa de cada palabra.

## Configuración (una vez)

1. Sube este repositorio a GitHub.
2. Activa GitHub Pages:
   - Repo → **Settings → Pages → Source: Deploy from a branch**.
   - Rama `main`, carpeta `/docs`. Guarda.
3. Crea los secretos en **Settings → Secrets and variables → Actions**:
   - `SMTP_USER` — tu correo Gmail (ej. `tucorreo@gmail.com`).
   - `SMTP_PASS` — [contraseña de aplicación de Google](https://myaccount.google.com/apppasswords) (activa antes la verificación en 2 pasos).
   - `TO_EMAIL` — correo que recibirá el newsletter (puede ser el mismo).
4. En **Actions**, ejecuta manualmente el workflow *newsletter* (botón *Run workflow*) para probar.

> Para no recibir el correo y solo publicar la página, el workflow se puede editar quitando `--enviar` de la línea `run:`.

## Probar en local

```bash
python newsletter/generar.py            # genera docs/ y la vista previa del correo en salida/
python newsletter/generar.py --enviar   # además envía por SMTP (requiere las variables SMTP_* y TO_EMAIL)
```

## Añadir palabras

Añade una entrada a `newsletter/palabras.json`:

```json
{
  "slug": "mi-palabra",
  "palabra": "Mi palabra",
  "premisa": "Frases corta y curiosa que engancha (es lo que se ve en el correo).",
  "significado": "Definición breve.",
  "origen": "Etimología y su recorrido histórico.",
  "detalle": "Párrafo más largo para la página."
}
```

El slug debe usar solo letras ASCII (sin tildes ni ñ). El calendario elige la palabra según el día del año, así que no hace falta programar nada.
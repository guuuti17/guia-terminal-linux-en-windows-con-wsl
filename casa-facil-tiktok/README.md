# Casa Fácil Trucos · Generador automático de vídeos

Convierte los guiones de `guiones/semana1.yaml` en vídeos de TikTok listos para subir:

```
guion ──► voz (ElevenLabs) ──► clips (Kling o Pexels) ──► vídeo 1080x1920 con gancho + subtítulos
```

Por cada vídeo crea `salida/semana1/<id>/FINAL.mp4` y `descripcion.txt`, y un `PUBLICAR.md` con el día, la hora y el texto de cada publicación.
Lo que ya se ha generado se reutiliza: si algo falla y lo vuelves a lanzar, **no pagas dos veces**.

---

## 1. Instalación (una sola vez)

Funciona en Linux, Mac o **Windows con WSL** (mira `../guia-wsl.md`). En la terminal de Ubuntu:

```bash
sudo apt update && sudo apt install -y ffmpeg python3-venv git
git clone <url-de-este-repositorio>
cd guia-terminal-linux-en-windows-con-wsl/casa-facil-tiktok
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.ejemplo .env
```

### Prueba gratis (sin claves ni gastos)

```bash
python generar.py guiones/semana1.yaml --simular
```

Genera los 14 vídeos con fondos de color y audio en silencio en `salida/semana1-simulado/`. Así compruebas que todo está bien instalado.

## 2. Claves de API (rellénalas en el archivo `.env`)

| Servicio | Dónde se consigue | Variable |
|---|---|---|
| **ElevenLabs** | elevenlabs.io → *Developers / API Keys* → crear clave | `ELEVENLABS_API_KEY` |
| Voz de ElevenLabs | *Voices* → elige una voz en **español de España** → copia su *Voice ID* | `ELEVENLABS_VOICE_ID` |
| **Kling** | Plataforma de desarrolladores de Kling AI → *API Keys* (Access Key + Secret Key) | `KLING_ACCESS_KEY`, `KLING_SECRET_KEY` |
| **Pexels** (opcional, gratis) | pexels.com/api → crear clave | `PEXELS_API_KEY` |

> ⚠️ **La API de Kling se paga aparte** de la suscripción de la web (paquetes de créditos de API). Comprueba los precios antes. Si cambian la dirección o el nombre del modelo, edita `KLING_API_BASE` y `KLING_MODEL` en el `.env`.
>
> El archivo `.env` contiene tus claves: no lo compartas ni lo subas a internet (ya está en `.gitignore`).

## 3. Uso

```bash
source .venv/bin/activate

# Toda la semana con Kling
python generar.py guiones/semana1.yaml

# Toda la semana con vídeos de stock gratis (Pexels) en lugar de Kling
python generar.py guiones/semana1.yaml --fuente pexels

# Solo un vídeo (recomendado la primera vez, para ver cómo queda)
python generar.py guiones/semana1.yaml --solo d1-principal
```

Coste aproximado por semana con Kling: 14 vídeos ≈ 37 clips de 5 s + unos 3.000 caracteres de voz.
**Truco para ahorrar:** usa Kling en los vídeos principales y Pexels en la serie de noche.

### Cambiar un clip que no te gusta
Borra ese archivo (por ejemplo, `salida/semana1/d1-principal/clip2.mp4`) y vuelve a ejecutar con `--solo d1-principal`. Solo se regenera ese clip.
También puedes poner ahí **tu propio vídeo** con ese mismo nombre y se usará en lugar del generado.

### Música
Crea una carpeta `musica/` y mete algún mp3 libre de derechos: se elige uno al azar a volumen bajo.
**Mejor todavía:** deja el vídeo sin música y añade un sonido en tendencia desde la app de TikTok al subirlo, porque eso ayuda al alcance.

## 4. Publicar

1. Abre `salida/semana1/PUBLICAR.md`.
2. En el ordenador, entra en TikTok Studio → **Subir** → elige `FINAL.mp4` → pega la descripción → **Programar** para el día y la hora indicados.
3. Activa siempre **"Contenido generado por IA"** en los ajustes de la publicación.
4. Cada día, dedica 15 minutos a contestar comentarios.

## 5. Nuevas semanas

Copia `guiones/semana1.yaml` como `semana2.yaml` y cambia los textos (o pídeselos a Claude con el mismo formato). Después:

```bash
python generar.py guiones/semana2.yaml
```

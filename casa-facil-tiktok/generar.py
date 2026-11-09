#!/usr/bin/env python3
"""
Casa Fácil Trucos - generador automático de vídeos para TikTok.

A partir de un archivo de guiones (YAML) genera, para cada vídeo:
  1. La voz en off con ElevenLabs (con marcas de tiempo para subtítulos).
  2. Los clips de vídeo con Kling (o vídeos de stock gratis de Pexels).
  3. El vídeo final 1080x1920 con gancho arriba, subtítulos y voz (ffmpeg).
  4. Un archivo PUBLICAR.md con el día, la hora y la descripción de cada vídeo.

Lo ya generado se reutiliza: si lo vuelves a ejecutar no se paga dos veces.

Uso:
  python generar.py guiones/semana1.yaml               # todo
  python generar.py guiones/semana1.yaml --solo d1-principal
  python generar.py guiones/semana1.yaml --fuente pexels
  python generar.py guiones/semana1.yaml --simular     # prueba gratis, sin APIs
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    import requests
    import yaml
except ImportError:
    sys.exit("Faltan dependencias. Ejecuta: pip install -r requirements.txt")

BASE_DIR = Path(__file__).resolve().parent
ANCHO, ALTO, FPS = 1080, 1920, 30


# ---------------------------------------------------------------- utilidades

def cargar_env(ruta: Path) -> None:
    """Carga un archivo .env sencillo (CLAVE=valor) sin dependencias extra."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def env(clave: str, defecto: str | None = None, obligatoria: bool = False) -> str | None:
    valor = os.environ.get(clave, defecto)
    if obligatoria and not valor:
        sys.exit(f"Falta {clave} en el archivo .env (mira .env.ejemplo).")
    return valor


def log(msg: str) -> None:
    print(msg, flush=True)


def ejecutar(cmd: list[str], cwd: Path | None = None) -> None:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"Error ejecutando ffmpeg:\n{' '.join(cmd)}\n\n{res.stderr[-2000:]}")


def duracion(ruta: Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(ruta)],
        capture_output=True, text=True,
    )
    return float(res.stdout.strip())


def quitar_emojis(texto: str) -> str:
    """Los emojis no se ven en el texto quemado del vídeo, así que se quitan."""
    limpio = re.sub(
        r"[\U0001F000-\U0001FAFF☀-➿️‍←-⇿⬀-⯿]",
        "", texto)
    return re.sub(r"\s+", " ", limpio).strip()


def descargar(url: str, destino: Path) -> None:
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        tmp = destino.with_suffix(".part")
        with open(tmp, "wb") as f:
            for trozo in r.iter_content(1 << 16):
                f.write(trozo)
        tmp.rename(destino)


# ----------------------------------------------------------------- ElevenLabs

def generar_voz(texto: str, carpeta: Path) -> tuple[Path, dict]:
    """Devuelve (mp3, alineación por caracteres)."""
    mp3, ali = carpeta / "voz.mp3", carpeta / "alineacion.json"
    if mp3.exists() and ali.exists():
        log("   · voz: ya existe, se reutiliza")
        return mp3, json.loads(ali.read_text(encoding="utf-8"))

    clave = env("ELEVENLABS_API_KEY", obligatoria=True)
    voz = env("ELEVENLABS_VOICE_ID", obligatoria=True)
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps"
           "?output_format=mp3_44100_128")
    cuerpo = {
        "text": texto,
        "model_id": env("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        "voice_settings": {
            "stability": float(env("ELEVENLABS_STABILITY", "0.45")),
            "similarity_boost": 0.75,
            "style": 0.15,
            "use_speaker_boost": True,
            "speed": float(env("ELEVENLABS_SPEED", "1.05")),
        },
    }
    log("   · voz: generando con ElevenLabs…")
    r = requests.post(url, json=cuerpo, headers={"xi-api-key": clave}, timeout=180)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs respondió {r.status_code}: {r.text[:500]}")
    datos = r.json()
    mp3.write_bytes(base64.b64decode(datos["audio_base64"]))
    alineacion = datos.get("alignment") or datos.get("normalized_alignment")
    ali.write_text(json.dumps(alineacion, ensure_ascii=False), encoding="utf-8")
    return mp3, alineacion


def simular_voz(texto: str, carpeta: Path) -> tuple[Path, dict]:
    """Audio en silencio + tiempos estimados, para probar sin gastar."""
    mp3, ali = carpeta / "voz.mp3", carpeta / "alineacion.json"
    seg_por_caracter = 0.062
    chars, ini, fin = [], [], []
    t = 0.2
    for c in texto:
        chars.append(c)
        ini.append(t)
        t += seg_por_caracter * (4 if c in ".,:" else 1)
        fin.append(t)
    total = t + 0.3
    ejecutar(["ffmpeg", "-y", "-f", "lavfi", "-i",
              "anullsrc=r=44100:cl=stereo", "-t", f"{total:.2f}",
              "-c:a", "libmp3lame", "-b:a", "128k", str(mp3)])
    alineacion = {"characters": chars, "character_start_times_seconds": ini,
                  "character_end_times_seconds": fin}
    ali.write_text(json.dumps(alineacion, ensure_ascii=False), encoding="utf-8")
    return mp3, alineacion


# ---------------------------------------------------------------------- Kling

def _b64url(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def token_kling() -> str:
    """JWT HS256 que pide la API de Kling (access key + secret key)."""
    ak = env("KLING_ACCESS_KEY", obligatoria=True)
    sk = env("KLING_SECRET_KEY", obligatoria=True)
    ahora = int(time.time())
    cab = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    carga = _b64url(json.dumps({"iss": ak, "exp": ahora + 1800, "nbf": ahora - 5}).encode())
    firma = hmac.new(sk.encode(), f"{cab}.{carga}".encode(), hashlib.sha256).digest()
    return f"{cab}.{carga}.{_b64url(firma)}"


def clip_kling(prompt: str, negativo: str, destino: Path) -> None:
    base = env("KLING_API_BASE", "https://api-singapore.klingai.com").rstrip("/")
    cabeceras = {"Authorization": f"Bearer {token_kling()}",
                 "Content-Type": "application/json"}
    cuerpo = {
        "model_name": env("KLING_MODEL", "kling-v2-1-master"),
        "prompt": prompt,
        "negative_prompt": negativo,
        "mode": env("KLING_MODE", "std"),
        "aspect_ratio": "9:16",
        "duration": env("KLING_DURATION", "5"),
    }
    r = requests.post(f"{base}/v1/videos/text2video", json=cuerpo,
                      headers=cabeceras, timeout=60)
    datos = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or datos.get("code") != 0:
        sys.exit(f"Kling respondió {r.status_code}: {r.text[:500]}")
    tarea = datos["data"]["task_id"]

    inicio = time.time()
    while True:
        time.sleep(15)
        cabeceras["Authorization"] = f"Bearer {token_kling()}"
        r = requests.get(f"{base}/v1/videos/text2video/{tarea}",
                         headers=cabeceras, timeout=60)
        d = r.json().get("data", {})
        estado = d.get("task_status")
        if estado == "succeed":
            url = d["task_result"]["videos"][0]["url"]
            descargar(url, destino)
            return
        if estado == "failed":
            sys.exit(f"Kling no pudo generar el clip: {d.get('task_status_msg')}")
        if time.time() - inicio > 20 * 60:
            sys.exit(f"Kling tarda demasiado (tarea {tarea}). Vuelve a ejecutar más tarde.")
        log(f"     … Kling: {estado} ({int(time.time() - inicio)} s)")


# --------------------------------------------------------------------- Pexels

_pexels_usados: set[int] = set()


def clip_pexels(busqueda: str, destino: Path) -> None:
    clave = env("PEXELS_API_KEY", obligatoria=True)
    for consulta in (busqueda, "interior design living room", "cozy home interior"):
        r = requests.get(
            "https://api.pexels.com/videos/search",
            params={"query": consulta, "orientation": "portrait",
                    "size": "medium", "per_page": 15},
            headers={"Authorization": clave}, timeout=60)
        if r.status_code != 200:
            sys.exit(f"Pexels respondió {r.status_code}: {r.text[:300]}")
        videos = [v for v in r.json().get("videos", []) if v["id"] not in _pexels_usados]
        random.shuffle(videos)
        for v in videos:
            archivos = [f for f in v.get("video_files", [])
                        if f.get("height") and f.get("width")
                        and f["height"] > f["width"] and f["height"] >= 1280]
            if not archivos:
                continue
            mejor = min(archivos, key=lambda f: abs(f["height"] - ALTO))
            _pexels_usados.add(v["id"])
            descargar(mejor["link"], destino)
            return
    sys.exit(f"Pexels no encontró vídeos verticales para: {busqueda}")


def clip_simulado(n: int, destino: Path) -> None:
    colores = ["0xE8DCCB", "0xB7C4A8", "0xD9A38A", "0xCFC6B8"]
    ejecutar(["ffmpeg", "-y", "-f", "lavfi", "-i",
              f"color=c={colores[n % len(colores)]}:s={ANCHO}x{ALTO}:r={FPS}:d=5",
              "-c:v", "libx264", "-pix_fmt", "yuv420p", str(destino)])


# --------------------------------------------------------------- subtítulos

def _t_ass(seg: float) -> str:
    h, resto = divmod(max(seg, 0), 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _escapar_ass(texto: str) -> str:
    return texto.replace("\\", "").replace("{", "(").replace("}", ")")


def palabras_desde_alineacion(ali: dict) -> list[tuple[str, float, float]]:
    palabras, actual, ini, fin = [], "", None, 0.0
    for c, a, b in zip(ali["characters"], ali["character_start_times_seconds"],
                       ali["character_end_times_seconds"]):
        if c.isspace():
            if actual:
                palabras.append((actual, ini, fin))
            actual, ini = "", None
            continue
        if ini is None:
            ini = a
        actual += c
        fin = b
    if actual:
        palabras.append((actual, ini, fin))
    return palabras


def crear_ass(gancho: str, ali: dict, total: float, destino: Path,
              con_subtitulos: bool = True) -> None:
    letra = env("FUENTE_LETRA", "Arial")
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {ANCHO}
PlayResY: {ALTO}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Gancho,{letra},78,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,8,70,70,230,1
Style: Sub,{letra},86,&H0000F0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,560,1
Style: Firma,{letra},44,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,70,70,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    eventos = [f"Dialogue: 0,{_t_ass(0)},{_t_ass(total)},Gancho,,0,0,0,,"
               f"{_escapar_ass(quitar_emojis(gancho))}"]
    firma = env("FIRMA", "@casafaciltrucos")
    if firma:
        eventos.append(f"Dialogue: 0,{_t_ass(0)},{_t_ass(total)},Firma,,0,0,0,,{_escapar_ass(firma)}")

    if con_subtitulos:
        palabras = palabras_desde_alineacion(ali)
        grupo: list[tuple[str, float, float]] = []

        def volcar():
            if not grupo:
                return
            texto = " ".join(p[0] for p in grupo).upper()
            eventos.append(f"Dialogue: 1,{_t_ass(grupo[0][1])},{_t_ass(grupo[-1][2])},"
                           f"Sub,,0,0,0,,{_escapar_ass(texto)}")
            grupo.clear()

        for p in palabras:
            grupo.append(p)
            if len(grupo) >= 3 or p[0][-1] in ".,:;?!":
                volcar()
        volcar()

    destino.write_text(cab + "\n".join(eventos) + "\n", encoding="utf-8")


# ------------------------------------------------------------------- montaje

def normalizar_clip(origen: Path, destino: Path) -> None:
    ejecutar(["ffmpeg", "-y", "-i", str(origen), "-an",
              "-vf", f"scale={ANCHO}:{ALTO}:force_original_aspect_ratio=increase,"
                     f"crop={ANCHO}:{ALTO},fps={FPS},setsar=1",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
              "-pix_fmt", "yuv420p", str(destino)])


def montar(carpeta: Path, clips: list[Path], voz: Path, gancho: str, ali: dict,
           musica: Path | None, con_subtitulos: bool) -> Path:
    normalizados = []
    for i, c in enumerate(clips, 1):
        n = carpeta / f"_norm{i}.mp4"
        normalizar_clip(c, n)
        normalizados.append(n)
    lista = carpeta / "_lista.txt"
    lista.write_text("".join(f"file '{n.name}'\n" for n in normalizados), encoding="utf-8")
    ejecutar(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista.name,
              "-c", "copy", "_union.mp4"], cwd=carpeta)

    total = duracion(voz) + 0.8
    crear_ass(gancho, ali, total, carpeta / "subs.ass", con_subtitulos)

    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", "_union.mp4", "-i", voz.name]
    if musica:
        cmd += ["-stream_loop", "-1", "-i", str(musica.resolve())]
        filtro_audio = (f"[1:a]apad[v];[2:a]volume={env('VOLUMEN_MUSICA', '0.12')}[m];"
                        "[v][m]amix=inputs=2:duration=first:dropout_transition=0[a]")
    else:
        filtro_audio = "[1:a]apad[a]"
    cmd += ["-filter_complex", f"[0:v]subtitles=subs.ass[vid];{filtro_audio}",
            "-map", "[vid]", "-map", "[a]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "FINAL.mp4"]
    ejecutar(cmd, cwd=carpeta)

    for f in [*normalizados, lista, carpeta / "_union.mp4"]:
        f.unlink(missing_ok=True)
    return carpeta / "FINAL.mp4"


# -------------------------------------------------------------------- flujo

def elegir_musica() -> Path | None:
    carpeta = BASE_DIR / "musica"
    if not carpeta.is_dir():
        return None
    pistas = [p for p in carpeta.iterdir() if p.suffix.lower() in (".mp3", ".m4a", ".wav")]
    return random.choice(pistas) if pistas else None


def procesar_video(v: dict, conf: dict, salida: Path, fuente: str,
                   simular: bool, con_subtitulos: bool) -> Path:
    carpeta = salida / v["id"]
    carpeta.mkdir(parents=True, exist_ok=True)
    log(f"\n▶ {v['id']}: {quitar_emojis(v['gancho'])}")

    if simular:
        voz, ali = simular_voz(v["voz"], carpeta)
    else:
        voz, ali = generar_voz(v["voz"], carpeta)

    estilo = conf.get("estilo_kling", "")
    negativo = conf.get("negativo_kling", "")
    clips = []
    for i, clip in enumerate(v["clips"], 1):
        destino = carpeta / f"clip{i}.mp4"
        clips.append(destino)
        if destino.exists():
            log(f"   · clip {i}: ya existe, se reutiliza")
            continue
        if simular:
            clip_simulado(i, destino)
        elif fuente == "kling":
            log(f"   · clip {i}: generando con Kling (tarda unos minutos)…")
            clip_kling(f"{clip['prompt']}, {estilo}".strip(", "), negativo, destino)
        else:
            busqueda = clip.get("pexels") or " ".join(clip["prompt"].split()[:4])
            log(f"   · clip {i}: buscando en Pexels «{busqueda}»…")
            clip_pexels(busqueda, destino)

    log("   · montando vídeo final…")
    final = montar(carpeta, clips, voz, v["gancho"], ali,
                   None if simular else elegir_musica(), con_subtitulos)
    (carpeta / "descripcion.txt").write_text(v.get("descripcion", ""), encoding="utf-8")
    log(f"   ✔ {final.relative_to(BASE_DIR)}")
    return final


def escribir_publicar(videos: list[dict], salida: Path) -> None:
    lineas = ["# Qué publicar y cuándo\n",
              "Sube cada vídeo en TikTok Studio (ordenador) → Subir → Programar.",
              "Activa siempre la etiqueta **Contenido generado por IA**.\n",
              "| Día | Hora | Archivo | Descripción |", "|---|---|---|---|"]
    for v in videos:
        desc = v.get("descripcion", "").replace("|", "/").replace("\n", " ")
        lineas.append(f"| {v.get('dia', '')} | {v.get('hora', '')} | "
                      f"`{v['id']}/FINAL.mp4` | {desc} |")
    (salida / "PUBLICAR.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera los vídeos de Casa Fácil Trucos.")
    ap.add_argument("guiones", help="archivo YAML con los guiones (p. ej. guiones/semana1.yaml)")
    ap.add_argument("--solo", help="genera solo el vídeo con este id (p. ej. d1-principal)")
    ap.add_argument("--fuente", choices=["kling", "pexels"],
                    help="de dónde salen los clips (por defecto FUENTE_VIDEO del .env o kling)")
    ap.add_argument("--simular", action="store_true",
                    help="prueba gratis: sin APIs, con fondos de color y audio en silencio")
    ap.add_argument("--sin-subtitulos", action="store_true", help="no quema subtítulos")
    args = ap.parse_args()

    cargar_env(BASE_DIR / ".env")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("No encuentro ffmpeg. Instálalo con: sudo apt install ffmpeg")

    ruta = Path(args.guiones)
    if not ruta.is_absolute() and not ruta.exists():
        ruta = BASE_DIR / ruta
    conf = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    videos = conf["videos"]
    if args.solo:
        videos = [v for v in videos if v["id"] == args.solo]
        if not videos:
            sys.exit(f"No hay ningún vídeo con id «{args.solo}» en {ruta.name}")

    fuente = args.fuente or env("FUENTE_VIDEO", "kling")
    salida = BASE_DIR / "salida" / (ruta.stem + ("-simulado" if args.simular else ""))
    salida.mkdir(parents=True, exist_ok=True)
    log(f"Guiones: {ruta.name} · vídeos: {len(videos)} · clips: "
        f"{'simulados' if args.simular else fuente} · salida: {salida.relative_to(BASE_DIR)}")

    for v in videos:
        procesar_video(v, conf, salida, fuente, args.simular, not args.sin_subtitulos)
    escribir_publicar(conf["videos"], salida)
    log(f"\nListo. Revisa los vídeos y sigue {salida.relative_to(BASE_DIR)}/PUBLICAR.md")


if __name__ == "__main__":
    main()

"""Montaje de vídeo vertical 1080x1920 con ffmpeg + Pillow (sin coste).

Fondo de cada escena, por orden de preferencia:
  1. Fotos o clips REALES y autorizados en productos/medios/<id_producto>/ (jpg, png, mp4, mov).
  2. Si no hay material: fondo liso con la indicación de qué plano real falta (solo borradores).
Nunca se generan imágenes de cartas ni de productos.
"""
import json
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from configuracion import ajustes

W, H, FPS = ajustes.ANCHO, ajustes.ALTO, ajustes.FPS
IMG, VID = {".jpg", ".jpeg", ".png", ".webp"}, {".mp4", ".mov"}


def _fuente(tam):
    return ImageFont.truetype(ajustes.FUENTE, tam)


def _partir(draw, texto, fuente, ancho_max):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=fuente) <= ancho_max or not actual:
            actual = prueba
        else:
            lineas.append(actual); actual = palabra
    return lineas + [actual] if actual else lineas


def _texto_centrado(draw, texto, y, tam, relleno="white", caja=None):
    fuente = _fuente(tam)
    lineas = _partir(draw, texto, fuente, W - 160)
    alto = int(tam * 1.25)
    if caja:
        ancho = max(draw.textlength(l, font=fuente) for l in lineas)
        draw.rounded_rectangle([(W - ancho) / 2 - 30, y - 18, (W + ancho) / 2 + 30, y + alto * len(lineas) + 14],
                               radius=24, fill=caja)
    for i, linea in enumerate(lineas):
        x = (W - draw.textlength(linea, font=fuente)) / 2
        draw.text((x, y + i * alto), linea, font=fuente, fill=relleno, stroke_width=5, stroke_fill="black")


def _fondo_imagen(ruta: Path) -> Image.Image:
    """Ajusta una foto al formato vertical: foto completa sobre su versión desenfocada."""
    foto = Image.open(ruta).convert("RGB")
    escala = max(W / foto.width, H / foto.height)
    fondo = foto.resize((int(foto.width * escala) + 1, int(foto.height * escala) + 1))
    fondo = fondo.crop(((fondo.width - W) // 2, (fondo.height - H) // 2, (fondo.width + W) // 2, (fondo.height + H) // 2))
    fondo = fondo.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * 0.55))
    # La foto va en la franja central (y 520-1420): deja libre el título arriba y los subtítulos abajo,
    # para no tapar textos de la propia foto (p. ej. «cartas no incluidas»).
    escala = min(900 / foto.width, 900 / foto.height)
    foto = foto.resize((int(foto.width * escala), int(foto.height * escala)))
    fondo.paste(foto, ((W - foto.width) // 2, 520 + (900 - foto.height) // 2))
    return fondo


def _fondo_vacio(indicacion: str) -> Image.Image:
    img = Image.new("RGB", (W, H), (24, 28, 44))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([90, 640, W - 90, 1240], radius=40, outline=(255, 200, 0), width=6)
    _texto_centrado(d, "FALTA MATERIAL REAL", 720, 54, relleno=(255, 200, 0))
    _texto_centrado(d, indicacion, 860, 48)
    return img


def _capa(pantalla: str, subtitulo: str, borrador: bool) -> Image.Image:
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    if borrador:
        _texto_centrado(d, "BORRADOR · DATOS SIN VERIFICAR · NO PUBLICAR", 110, 34, relleno=(255, 80, 80))
    _texto_centrado(d, pantalla, 190, 64, caja=(0, 0, 0, 150))
    if subtitulo:
        _texto_centrado(d, subtitulo, 1455, 56, relleno=(255, 230, 0), caja=(0, 0, 0, 170))
    return capa


def _duracion(ruta: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def _ffmpeg(args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"ffmpeg falló: {r.stderr[-800:]}")


def _escena(i, escena, medio, audio, borrador, tmp: Path) -> tuple[Path, float]:
    palabras = escena["voz"].split()
    dur = (_duracion(audio) + 0.35) if audio else max(2.0, len(palabras) / ajustes.PALABRAS_POR_SEGUNDO + 0.6)
    frames = int(dur * FPS)
    # Subtítulos: bloques de 4 palabras repartidos proporcionalmente en la duración.
    bloques = [" ".join(palabras[j:j + 4]) for j in range(0, len(palabras), 4)]
    entradas, filtro = [], []
    if medio and medio.suffix.lower() in VID:
        entradas += ["-stream_loop", "-1", "-t", f"{dur:.3f}", "-i", str(medio)]
        filtro.append(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1[b0]")
    else:
        fondo = _fondo_imagen(medio) if medio else _fondo_vacio(escena["visual"])
        ruta_fondo = tmp / f"fondo_{i}.png"
        fondo.save(ruta_fondo)
        entradas += ["-i", str(ruta_fondo)]
        filtro.append(f"[0:v]scale={W * 2}:{H * 2},zoompan=z='min(1+0.0005*on,1.08)':x='iw/2-(iw/zoom/2)':"
                      f"y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},setsar=1[b0]")
    total = sum(len(b) for b in bloques)
    t = 0.0
    for k, bloque in enumerate(bloques):
        ruta_capa = tmp / f"capa_{i}_{k}.png"
        _capa(escena["pantalla"], bloque, borrador).save(ruta_capa)
        entradas += ["-i", str(ruta_capa)]
        fin = t + dur * len(bloque) / total
        filtro.append(f"[b{k}][{k + 1}:v]overlay=enable='between(t,{t:.3f},{fin + 0.01:.3f})'[b{k + 1}]")
        t = fin
    n = len(bloques) + 1
    if audio:
        entradas += ["-i", str(audio)]
        filtro.append(f"[{n}:a]aresample=44100,apad[a]")
    else:
        entradas += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        filtro.append(f"[{n}:a]anull[a]")
    salida = tmp / f"escena_{i:02d}.mp4"
    _ffmpeg([*entradas, "-filter_complex", ";".join(filtro), "-map", f"[b{len(bloques)}]", "-map", "[a]",
             "-t", f"{dur:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", "-ac", "2", str(salida)])
    return salida, dur


def montar(con, guion_id: int) -> Path:
    """Monta el vídeo de un guion y lo registra. Devuelve la ruta del MP4."""
    g = con.execute("SELECT g.*, p.verificado_el FROM guiones g JOIN productos p ON p.id = g.producto_id "
                    "WHERE g.id = ?", (guion_id,)).fetchone()
    escenas = json.loads(g["escenas_json"])
    carpeta = ajustes.DIR_MEDIOS / str(g["producto_id"])
    medios = sorted(m for m in carpeta.glob("*") if m.suffix.lower() in IMG | VID) if carpeta.exists() else []
    borrador = not g["verificado_el"] or not medios
    ajustes.DIR_VIDEOS.mkdir(parents=True, exist_ok=True)
    salida = ajustes.DIR_VIDEOS / f"p{g['producto_id']}_{g['formato']}.mp4"
    con_voz, total = True, 0.0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        clips = []
        for i, e in enumerate(escenas):
            audio = ajustes.DIR_AUDIO / f"guion_{guion_id}" / f"escena_{i:02d}.mp3"
            if not audio.exists():
                audio, con_voz = None, False
            medio = medios[i % len(medios)] if medios else None  # material real, en rotación
            clip, dur = _escena(i, e, medio, audio, borrador, tmp)
            clips.append(clip); total += dur
        lista = tmp / "lista.txt"
        lista.write_text("".join(f"file '{c}'\n" for c in clips))
        _ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(salida)])
    con.execute("INSERT INTO videos (guion_id, ruta, duracion_s, con_voz, borrador) VALUES (?,?,?,?,?) "
                "ON CONFLICT(guion_id) DO UPDATE SET ruta=excluded.ruta, duracion_s=excluded.duracion_s, "
                "con_voz=excluded.con_voz, borrador=excluded.borrador, creado_el=datetime('now')",
                (guion_id, str(salida), round(total, 1), int(con_voz), int(borrador)))
    con.commit()
    return salida

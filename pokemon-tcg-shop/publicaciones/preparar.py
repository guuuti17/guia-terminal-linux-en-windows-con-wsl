"""Calendario y paquetes de publicación (2 vídeos/día: uno de producto y uno de coleccionismo).

TikTok no ofrece hoy una vía oficial abierta para vincular el producto afiliado por API,
así que el sistema deja cada publicación lista y tú haces la subida + enlace en la app.
"""
import shutil
from datetime import date, timedelta
from configuracion import ajustes

PASOS = """PASOS (app de TikTok, ~2 min):
1. Pulsa «+» > «Cargar» y elige video.mp4.
2. Pega el texto de descripcion.txt.
3. Pulsa «Añadir enlace» > «Productos» y elige: {producto}
   (antes debe estar en tu escaparate: TikTok Shop > Centro de creadores > Mercado de afiliados).
4. «Más opciones» > activa «Contenido generado por IA» (la voz es sintética).
5. Programa o publica a la hora indicada: {fecha} {hora}.
6. Copia el enlace del vídeo publicado y regístralo:
   python main.py publicado --pub {pub} --id-publicacion ENLACE_O_ID
"""


def preparar(con, producto_id: int, inicio: date, permitir_borrador: bool = False) -> list[dict]:
    """Asigna hueco de calendario a los vídeos aún no preparados y exporta su carpeta."""
    videos = con.execute(
        "SELECT v.id, v.ruta, v.borrador, v.con_voz, g.formato, g.tipo, g.descripcion, p.nombre "
        "FROM videos v JOIN guiones g ON g.id = v.guion_id JOIN productos p ON p.id = g.producto_id "
        "WHERE g.producto_id = ? AND v.id NOT IN (SELECT video_id FROM publicaciones) ORDER BY v.id",
        (producto_id,)).fetchall()
    if not permitir_borrador:
        malos = [v["formato"] for v in videos if v["borrador"] or not v["con_voz"]]
        if malos:
            raise RuntimeError(f"Vídeos en borrador o sin voz: {', '.join(malos)}. Complétalos antes de preparar.")
    # Hora 1 del día -> vídeo de producto; hora 2 -> coleccionismo (si hay de ambos tipos).
    colas = {"producto": [v for v in videos if v["tipo"] == "producto"],
             "coleccionismo": [v for v in videos if v["tipo"] != "producto"]}
    ocupados = {(f["fecha"], f["hora"]) for f in con.execute("SELECT fecha, hora FROM publicaciones")}
    hechas, dia = [], inicio
    while colas["producto"] or colas["coleccionismo"]:
        for n, hora in enumerate(ajustes.HORAS_PUBLICACION):
            if (dia.isoformat(), hora) in ocupados:
                continue
            orden = ("producto", "coleccionismo") if n % 2 == 0 else ("coleccionismo", "producto")
            cola = colas[orden[0]] or colas[orden[1]]
            if not cola:
                break
            v = cola.pop(0)
            pub = con.execute("INSERT INTO publicaciones (video_id, producto_id, fecha, hora, descripcion) "
                              "VALUES (?,?,?,?,?)", (v["id"], producto_id, dia.isoformat(), hora, v["descripcion"])).lastrowid
            carpeta = ajustes.DIR_LOTES / f"{dia.isoformat()}_{hora.replace(':', '')}_{v['formato']}"
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.copy(v["ruta"], carpeta / "video.mp4")
            (carpeta / "descripcion.txt").write_text(v["descripcion"] + "\n", encoding="utf-8")
            (carpeta / "pasos.txt").write_text(PASOS.format(producto=v["nombre"], fecha=dia.isoformat(), hora=hora, pub=pub),
                                               encoding="utf-8")
            hechas.append({"pub": pub, "fecha": dia.isoformat(), "hora": hora, "formato": v["formato"], "carpeta": carpeta})
        dia += timedelta(days=1)
    con.commit()
    return hechas


def marcar_publicada(con, pub: int, id_publicacion: str):
    if con.execute("SELECT 1 FROM publicaciones WHERE id_publicacion = ? AND id != ?", (id_publicacion, pub)).fetchone():
        raise RuntimeError("Ese identificador ya está registrado en otra publicación (duplicado).")
    if not con.execute("UPDATE publicaciones SET id_publicacion = ?, estado = 'publicada' WHERE id = ?",
                       (id_publicacion, pub)).rowcount:
        raise RuntimeError(f"No existe la publicación {pub}")
    con.commit()


def registrar_resultado(con, pub: int, ventas: int, comision_eur: float):
    """Anota los totales acumulados que muestra TikTok Shop para esa publicación."""
    if not con.execute("UPDATE publicaciones SET ventas = ?, comision_eur = ? WHERE id = ?",
                       (ventas, comision_eur, pub)).rowcount:
        raise RuntimeError(f"No existe la publicación {pub}")
    con.commit()

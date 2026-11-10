"""Importación de fichas de producto desde CSV y clasificación de oportunidades."""
import csv
from configuracion.reglas import AUTENTICIDADES

NUMERICOS = {"precio_eur": float, "comision_pct": float, "valoracion": float, "num_resenas": int,
             "ventas": int, "demanda": int, "competencia": int, "facilidad_video": int,
             "fiabilidad_vendedor": int}
TEXTO = ["id_tiktok", "nombre", "nombre_corto", "categoria", "idioma", "autenticidad", "vendedor",
         "caracteristicas", "verificado_el", "notas"]
COLUMNAS = TEXTO + list(NUMERICOS)


def importar(con, ruta_csv) -> tuple[int, list[str]]:
    """Inserta o actualiza productos. Devuelve (nº importados, avisos)."""
    n, avisos = 0, []
    with open(ruta_csv, newline="", encoding="utf-8-sig") as f:
        for i, fila in enumerate(csv.DictReader(f), start=2):
            d = {c: (fila.get(c) or "").strip() or None for c in COLUMNAS}
            if not d["id_tiktok"] or not d["nombre"]:
                avisos.append(f"Línea {i}: falta id_tiktok o nombre; ignorada."); continue
            if d["autenticidad"] not in AUTENTICIDADES:
                avisos.append(f"Línea {i}: autenticidad '{d['autenticidad']}' no válida; ignorada."); continue
            if d["autenticidad"] == "no_oficial":
                avisos.append(f"Línea {i}: '{d['nombre']}' es no oficial (réplica/sin licencia); RECHAZADO."); continue
            if d["categoria"] not in ("accesorio", "sellado"):
                avisos.append(f"Línea {i}: categoria debe ser accesorio o sellado; ignorada."); continue
            try:
                for c, tipo in NUMERICOS.items():
                    if d[c] is not None:
                        d[c] = tipo(str(d[c]).replace(",", "."))
            except ValueError:
                avisos.append(f"Línea {i}: número no válido en '{c}'; ignorada."); continue
            d["nombre_corto"] = d["nombre_corto"] or d["nombre"]
            sets = ", ".join(f"{c}=excluded.{c}" for c in COLUMNAS if c != "id_tiktok")
            con.execute(f"INSERT INTO productos ({', '.join(COLUMNAS)}) VALUES ({', '.join('?' * len(COLUMNAS))}) "
                        f"ON CONFLICT(id_tiktok) DO UPDATE SET {sets}", [d[c] for c in COLUMNAS])
            n += 1
    con.commit()
    return n, avisos


def puntuar(p) -> tuple[float, float | None, list[str]]:
    """Puntuación 0-100, comisión € por venta y datos que faltan.

    Pesos: comisión €/venta 25 · demanda 20 · facilidad de vídeo 15 · fiabilidad vendedor 15 ·
    precio de impulso 15 · competencia (inversa) 10. Un dato ausente puntúa 0: no se inventa.
    """
    faltan = [c for c in ("precio_eur", "comision_pct", "demanda", "competencia",
                          "facilidad_video", "fiabilidad_vendedor") if p[c] is None]
    comision = None
    pts = 0.0
    if p["precio_eur"] is not None and p["comision_pct"] is not None:
        comision = round(p["precio_eur"] * p["comision_pct"] / 100, 2)
        pts += min(comision / 3.0, 1.0) * 25          # 3 €/venta o más = máximo
    if p["precio_eur"] is not None:
        pts += 15 if 8 <= p["precio_eur"] <= 35 else 8  # compra por impulso
    pts += (p["demanda"] or 0) / 5 * 20
    pts += (p["facilidad_video"] or 0) / 5 * 15
    pts += (p["fiabilidad_vendedor"] or 0) / 5 * 15
    if p["competencia"]:
        pts += (6 - p["competencia"]) / 5 * 10
    return round(pts, 1), comision, faltan


def ranking(con) -> list[dict]:
    filas = []
    for p in con.execute("SELECT * FROM productos"):
        pts, comision, faltan = puntuar(p)
        filas.append({"p": p, "puntos": pts, "comision_eur": comision, "faltan": faltan})
    return sorted(filas, key=lambda f: f["puntos"], reverse=True)

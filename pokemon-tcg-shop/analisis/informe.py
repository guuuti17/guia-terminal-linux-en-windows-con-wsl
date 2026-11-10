"""Control económico: ingresos por comisiones, costes y beneficio."""


def resumen(con) -> dict:
    uno = lambda sql: con.execute(sql).fetchone()[0] or 0
    ingresos = uno("SELECT SUM(comision_eur) FROM publicaciones")
    costes = uno("SELECT SUM(importe_eur) FROM costes")
    ventas = uno("SELECT SUM(ventas) FROM publicaciones")
    videos = uno("SELECT COUNT(*) FROM videos")
    por_producto = [dict(f) for f in con.execute(
        "SELECT p.id, p.nombre_corto, "
        " (SELECT COUNT(*) FROM publicaciones x WHERE x.producto_id = p.id AND x.estado = 'publicada') AS publicadas,"
        " (SELECT COALESCE(SUM(ventas), 0) FROM publicaciones x WHERE x.producto_id = p.id) AS ventas,"
        " (SELECT COALESCE(SUM(comision_eur), 0) FROM publicaciones x WHERE x.producto_id = p.id) AS ingresos,"
        " (SELECT COALESCE(SUM(importe_eur), 0) FROM costes c WHERE c.producto_id = p.id) AS costes "
        "FROM productos p")]
    return {
        "ingresos": round(ingresos, 2), "costes": round(costes, 2), "beneficio": round(ingresos - costes, 2),
        "ventas": ventas, "videos": videos,
        "coste_por_video": round(costes / videos, 2) if videos else None,
        "comision_por_venta": round(ingresos / ventas, 2) if ventas else None,
        "por_tipo": [dict(f) for f in con.execute("SELECT tipo, ROUND(SUM(importe_eur), 2) AS total FROM costes GROUP BY tipo")],
        "por_producto": por_producto,
    }

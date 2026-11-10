#!/usr/bin/env python3
"""Pokémon TCG Shop — sistema de afiliación para TikTok Shop España.

Uso: python main.py <orden> [opciones]      (python main.py -h para ver todas)
"""
import argparse
import sys
from datetime import date, timedelta

import bd
from analisis import informe
from configuracion import ajustes
from generador import video
from guiones import generar as guiones
from productos import catalogo
from publicaciones import preparar as pubs
from voces import elevenlabs


def o_importar(con, a):
    n, avisos = catalogo.importar(con, a.csv)
    print(f"{n} producto(s) importados o actualizados.")
    for aviso in avisos:
        print("  AVISO:", aviso)


def o_ranking(con, a):
    filas = catalogo.ranking(con)
    if not filas:
        print("No hay productos. Importa primero: python main.py importar productos/mis_productos.csv"); return
    print(f"{'ID':>3} {'Pts':>5} {'€/venta':>8} {'Precio':>7} {'Com.%':>6}  Producto")
    for f in filas:
        p = f["p"]
        fmt = lambda v, s="": "—" if v is None else f"{v:g}{s}"
        marca = "" if p["verificado_el"] else "  [SIN VERIFICAR]"
        print(f"{p['id']:>3} {f['puntos']:>5} {fmt(f['comision_eur']):>8} {fmt(p['precio_eur']):>7} "
              f"{fmt(p['comision_pct']):>6}  {p['nombre_corto']} ({p['vendedor'] or 'vendedor ?'}){marca}")
        if f["faltan"]:
            print(f"      faltan datos: {', '.join(f['faltan'])}")


def o_guiones(con, a):
    ids = guiones.generar(con, a.producto, borrador=a.borrador)
    for g in con.execute(f"SELECT id, formato, tipo, titulo FROM guiones WHERE id IN ({','.join('?' * len(ids))})", ids):
        print(f"  guion {g['id']}: {g['formato']} [{g['tipo']}] — {g['titulo']}")


def o_voces_listar(con, a):
    c = elevenlabs.cuota()
    print(f"Plan {c['plan']}: {c['usados']}/{c['limite']} caracteres usados este ciclo.")
    for v in elevenlabs.listar_voces():
        print(f"  {v['id']}  {v['nombre']}  {v['idioma']}")


def o_voces(con, a):
    faltan = elevenlabs.pendientes(con, a.producto)
    caracteres, euros = elevenlabs.estimar(faltan)
    if not faltan:
        print("No hay audios pendientes."); return
    print(f"Pendiente: {len(faltan)} audios, {caracteres} caracteres (~{euros} € según tu tarifa configurada).")
    if not a.confirmar_gasto:
        print("No se ha gastado nada. Para generar, repite la orden añadiendo --confirmar-gasto"); return
    caracteres, euros = elevenlabs.generar(con, a.producto)
    print(f"Generado: {caracteres} caracteres, coste registrado {euros} €.")


def o_videos(con, a):
    for g in con.execute("SELECT id, formato FROM guiones WHERE producto_id = ?", (a.producto,)).fetchall():
        ruta = video.montar(con, g["id"])
        v = con.execute("SELECT * FROM videos WHERE guion_id = ?", (g["id"],)).fetchone()
        estado = "BORRADOR" if v["borrador"] else "final"
        print(f"  {ruta.name}: {v['duracion_s']} s, {'con' if v['con_voz'] else 'SIN'} voz, {estado}")


def o_preparar(con, a):
    inicio = date.fromisoformat(a.inicio) if a.inicio else date.today() + timedelta(days=1)
    for h in pubs.preparar(con, a.producto, inicio, permitir_borrador=a.borrador):
        print(f"  pub {h['pub']}: {h['fecha']} {h['hora']} — {h['formato']} -> {h['carpeta']}")


def o_publicado(con, a):
    pubs.marcar_publicada(con, a.pub, a.id_publicacion)
    print("Publicación registrada.")


def o_resultado(con, a):
    pubs.registrar_resultado(con, a.pub, a.ventas, a.comision)
    print("Resultado registrado.")


def o_coste(con, a):
    con.execute("INSERT INTO costes (concepto, tipo, importe_eur, producto_id) VALUES (?,?,?,?)",
                (a.concepto, a.tipo, a.importe, a.producto))
    con.commit()
    print("Coste registrado.")


def o_informe(con, a):
    r = informe.resumen(con)
    nd = lambda v: "—" if v is None else f"{v} €"
    print(f"Ingresos (comisiones): {r['ingresos']} €\nCostes:                {r['costes']} €\n"
          f"Beneficio estimado:    {r['beneficio']} €  (antes de impuestos y cuota de autónomo)\n"
          f"Ventas: {r['ventas']} · Vídeos: {r['videos']} · Coste/vídeo: {nd(r['coste_por_video'])} · "
          f"Comisión/venta: {nd(r['comision_por_venta'])}")
    for t in r["por_tipo"]:
        print(f"  coste {t['tipo']}: {t['total']} €")
    for p in r["por_producto"]:
        print(f"  producto {p['id']} {p['nombre_corto']}: {p['publicadas']} publicadas, {p['ventas']} ventas, "
              f"{p['ingresos']:.2f} € ingresos, {p['costes']:.2f} € costes")


def o_estado(con, a):
    for f in con.execute("SELECT pu.id, pu.fecha, pu.hora, pu.estado, pu.ventas, pu.comision_eur, pu.id_publicacion, "
                         "g.formato, p.nombre_corto FROM publicaciones pu JOIN videos v ON v.id = pu.video_id "
                         "JOIN guiones g ON g.id = v.guion_id JOIN productos p ON p.id = pu.producto_id ORDER BY fecha, hora"):
        print(f"  pub {f['id']}: {f['fecha']} {f['hora']} {f['estado']:<10} {f['formato']:<13} {f['nombre_corto']} "
              f"· {f['ventas']} ventas · {f['comision_eur']} € · {f['id_publicacion'] or 'sin id'}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)

    def orden(nombre, fn, ayuda, producto=False):
        s = sub.add_parser(nombre, help=ayuda)
        s.set_defaults(fn=fn)
        if producto:
            s.add_argument("--producto", type=int, required=True, help="ID interno (ver «ranking»)")
        return s

    orden("importar", o_importar, "Importa/actualiza productos desde un CSV").add_argument("csv")
    orden("ranking", o_ranking, "Clasifica los productos por oportunidad")
    orden("guiones", o_guiones, "Genera los guiones de un producto", True).add_argument("--borrador", action="store_true")
    orden("voces-listar", o_voces_listar, "Muestra cuota y voces de ElevenLabs (gratis)")
    orden("voces", o_voces, "Genera las voces pendientes (pide confirmación de gasto)", True) \
        .add_argument("--confirmar-gasto", action="store_true")
    orden("videos", o_videos, "Monta los vídeos verticales de un producto", True)
    s = orden("preparar", o_preparar, "Crea calendario y carpetas de publicación", True)
    s.add_argument("--inicio", help="AAAA-MM-DD (por defecto, mañana)")
    s.add_argument("--borrador", action="store_true", help="Permite preparar borradores (solo pruebas)")
    s = orden("publicado", o_publicado, "Registra el identificador de un vídeo ya publicado")
    s.add_argument("--pub", type=int, required=True); s.add_argument("--id-publicacion", required=True)
    s = orden("resultado", o_resultado, "Anota ventas y comisión acumuladas de una publicación")
    s.add_argument("--pub", type=int, required=True); s.add_argument("--ventas", type=int, required=True)
    s.add_argument("--comision", type=float, required=True, help="€ acumulados")
    s = orden("coste", o_coste, "Registra un coste (suscripción, muestra, herramienta...)")
    s.add_argument("--concepto", required=True); s.add_argument("--importe", type=float, required=True)
    s.add_argument("--tipo", required=True, choices=["ia", "suscripcion", "servidor", "analisis", "muestra", "otro"])
    s.add_argument("--producto", type=int)
    orden("informe", o_informe, "Ingresos, costes y beneficio")
    orden("estado", o_estado, "Lista las publicaciones y su estado")

    a = ap.parse_args(argv)
    con = bd.conectar()
    try:
        a.fn(con, a)
    except (guiones.GuionInvalido, RuntimeError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

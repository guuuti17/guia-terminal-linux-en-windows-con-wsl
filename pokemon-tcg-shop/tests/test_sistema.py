"""Pruebas del flujo completo sin APIs de pago: python -m unittest discover tests"""
import os, sys, tempfile, unittest
from datetime import date
from pathlib import Path

TMP = tempfile.mkdtemp()
os.environ["PTS_BD"] = str(Path(TMP) / "test.sqlite3")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bd
from configuracion import ajustes, reglas
from guiones import generar as guiones
from productos import catalogo
from publicaciones import preparar as pubs
from generador import video
from analisis import informe

ajustes.DIR_VIDEOS, ajustes.DIR_LOTES = Path(TMP) / "v", Path(TMP) / "l"
ajustes.DIR_AUDIO, ajustes.DIR_MEDIOS = Path(TMP) / "a", Path(TMP) / "m"
CAB = ("id_tiktok,nombre,nombre_corto,categoria,idioma,autenticidad,precio_eur,comision_pct,vendedor,"
       "caracteristicas,demanda,competencia,facilidad_video,fiabilidad_vendedor,verificado_el\n")


def csv(filas):
    ruta = Path(TMP) / "p.csv"
    ruta.write_text(CAB + filas, encoding="utf-8")
    return ruta


class Flujo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = bd.conectar()
        cls.n, cls.avisos = catalogo.importar(cls.con, csv(
            "A1,Álbum X,álbum X,accesorio,no_aplica,generico,\"19,99\",15,Tienda,a|b|c,4,3,5,4,2026-11-10\n"
            "A2,Carta réplica,réplica,accesorio,,no_oficial,5,30,T,a|b|c,5,1,5,1,2026-11-10\n"
            "A3,ETB sin verificar,ETB,sellado,español,oficial,,,T,a|b|c,,,,,\n"))

    def test_1_importacion_rechaza_no_oficial_y_no_duplica(self):
        self.assertEqual(self.n, 2)
        self.assertTrue(any("RECHAZADO" in a for a in self.avisos))
        catalogo.importar(self.con, csv("A1,Álbum X,álbum X,accesorio,no_aplica,generico,21,15,Tienda,a|b|c,4,3,5,4,2026-11-10\n"))
        self.assertEqual(self.con.execute("SELECT COUNT(*), MAX(precio_eur) FROM productos WHERE id_tiktok='A1'").fetchone()[:], (1, 21.0))

    def test_2_ranking_no_inventa_datos(self):
        r = catalogo.ranking(self.con)
        self.assertEqual(r[0]["p"]["id_tiktok"], "A1")
        self.assertEqual(r[0]["comision_eur"], 3.15)
        self.assertIsNone(r[1]["comision_eur"])
        self.assertIn("comision_pct", r[1]["faltan"])

    def test_3_reglas(self):
        self.assertTrue(reglas.revisar("Es una inversión segura"))
        self.assertTrue(reglas.revisar("Te va a tocar una carta rara garantizada"))
        self.assertEqual(reglas.revisar("Mira el precio en el carrito naranja"), [])

    def test_4_guiones_exigen_verificacion(self):
        sin_verificar = self.con.execute("SELECT id FROM productos WHERE id_tiktok='A3'").fetchone()[0]
        with self.assertRaises(guiones.GuionInvalido):
            guiones.generar(self.con, sin_verificar)
        self.assertEqual(len(guiones.generar(self.con, sin_verificar, borrador=True)), 2)
        pid = self.con.execute("SELECT id FROM productos WHERE id_tiktok='A1'").fetchone()[0]
        self.assertEqual(len(guiones.generar(self.con, pid)), 5)
        self.assertEqual(len(guiones.generar(self.con, pid)), 5)  # regenerar no duplica
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM guiones WHERE producto_id=?", (pid,)).fetchone()[0], 5)

    def test_5_video_calendario_e_informe(self):
        pid = self.con.execute("SELECT id FROM productos WHERE id_tiktok='A1'").fetchone()[0]
        for g in self.con.execute("SELECT id FROM guiones WHERE producto_id=?", (pid,)).fetchall():
            ruta = video.montar(self.con, g["id"])
            self.assertGreater(ruta.stat().st_size, 10_000)
        with self.assertRaises(RuntimeError):  # sin voz ni material real no se puede preparar
            pubs.preparar(self.con, pid, date(2026, 11, 12))
        hechas = pubs.preparar(self.con, pid, date(2026, 11, 12), permitir_borrador=True)
        self.assertEqual(len(hechas), 5)
        self.assertEqual(len({(h["fecha"], h["hora"]) for h in hechas}), 5)
        self.assertEqual(pubs.preparar(self.con, pid, date(2026, 11, 12), permitir_borrador=True), [])  # sin duplicados
        pubs.marcar_publicada(self.con, hechas[0]["pub"], "https://tiktok/x1")
        with self.assertRaises(RuntimeError):
            pubs.marcar_publicada(self.con, hechas[1]["pub"], "https://tiktok/x1")
        pubs.registrar_resultado(self.con, hechas[0]["pub"], 2, 6.30)
        self.con.execute("INSERT INTO costes (concepto, tipo, importe_eur, producto_id) VALUES ('voz','ia',1.3,?)", (pid,))
        r = informe.resumen(self.con)
        self.assertEqual((r["ingresos"], r["costes"], r["beneficio"], r["comision_por_venta"]), (6.3, 1.3, 5.0, 3.15))


if __name__ == "__main__":
    unittest.main()

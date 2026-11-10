"""Base de datos SQLite: productos, guiones, vídeos, publicaciones y costes."""
import sqlite3
from configuracion import ajustes

ESQUEMA = """
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY,
    id_tiktok TEXT UNIQUE NOT NULL,      -- ID o URL del producto en TikTok Shop
    nombre TEXT NOT NULL, nombre_corto TEXT NOT NULL,
    categoria TEXT NOT NULL,             -- accesorio | sellado
    idioma TEXT,                         -- español | inglés | japonés | no_aplica
    autenticidad TEXT NOT NULL,          -- oficial | licenciado | generico | no_oficial
    precio_eur REAL, comision_pct REAL,
    vendedor TEXT, valoracion REAL, num_resenas INTEGER, ventas INTEGER,
    caracteristicas TEXT,                -- verificadas en la ficha, separadas por |
    demanda INTEGER, competencia INTEGER, facilidad_video INTEGER, fiabilidad_vendedor INTEGER, -- 1-5
    verificado_el TEXT,                  -- fecha en que TÚ comprobaste la ficha en la app
    notas TEXT
);
CREATE TABLE IF NOT EXISTS guiones (
    id INTEGER PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    formato TEXT NOT NULL, tipo TEXT NOT NULL,   -- tipo: producto | coleccionismo
    titulo TEXT NOT NULL, escenas_json TEXT NOT NULL,
    descripcion TEXT NOT NULL, creado_el TEXT DEFAULT (datetime('now')),
    UNIQUE (producto_id, formato)
);
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY,
    guion_id INTEGER NOT NULL UNIQUE REFERENCES guiones(id),
    ruta TEXT NOT NULL, duracion_s REAL, con_voz INTEGER, borrador INTEGER,
    creado_el TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS publicaciones (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL UNIQUE REFERENCES videos(id),   -- UNIQUE evita duplicados
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    fecha TEXT NOT NULL, hora TEXT NOT NULL, descripcion TEXT NOT NULL,
    id_publicacion TEXT, estado TEXT NOT NULL DEFAULT 'preparada',  -- preparada | publicada
    ventas INTEGER DEFAULT 0, comision_eur REAL DEFAULT 0,
    UNIQUE (fecha, hora)
);
CREATE TABLE IF NOT EXISTS costes (
    id INTEGER PRIMARY KEY,
    fecha TEXT DEFAULT (date('now')), concepto TEXT NOT NULL,
    tipo TEXT NOT NULL,                  -- ia | suscripcion | servidor | analisis | muestra | otro
    importe_eur REAL NOT NULL, unidades TEXT,
    producto_id INTEGER, video_id INTEGER
);
"""


def conectar() -> sqlite3.Connection:
    con = sqlite3.connect(ajustes.BD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    return con

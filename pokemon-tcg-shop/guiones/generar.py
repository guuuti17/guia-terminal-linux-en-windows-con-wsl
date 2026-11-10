"""Generación de guiones a partir de plantillas y de datos VERIFICADOS de la ficha.

Las plantillas no mencionan precios (cambian) ni prometen cartas, rarezas o rentabilidad.
Marcadores: {n} nombre corto · {c1} {c2} {c3} características verificadas · {idioma}.
Cada escena: (voz, texto en pantalla, qué material REAL mostrar).
"""
import json
from configuracion import ajustes, reglas

CTA = ("Lo tienes en el carrito naranja. Mira el precio y las opiniones antes de decidir.",
       "Carrito naranja", "Plano final del producto real")

PLANTILLAS = {
    "accesorio": {
        "principiante": ("producto", "¿Empiezas a coleccionar Pokémon?", [
            ("Si estás empezando a coleccionar Pokémon, esto te interesa.", "¿Empiezas a coleccionar Pokémon?", "Producto real, plano general"),
            ("Tus cartas se dañan antes de lo que crees: esquinas dobladas, roces y humedad.", "Esquinas dobladas. Roces. Humedad.", "Fondo ambiental (mesa, sin cartas inventadas)"),
            ("Mira esto: {n}.", "{n}", "Producto real, primer plano"),
            ("Uno: {c1}.", "1 · {c1}", "Detalle real de esa característica"),
            ("Dos: {c2}.", "2 · {c2}", "Detalle real de esa característica"),
            ("Y tres: {c3}.", "3 · {c3}", "Detalle real de esa característica"),
            CTA]),
        "errores": ("coleccionismo", "3 errores que estropean tus cartas", [
            ("Tres errores que estropean tus cartas Pokémon sin que te des cuenta.", "3 errores que estropean tus cartas", "Fondo ambiental"),
            ("Uno: sujetarlas con gomas elásticas. Marcan los bordes y las curvan.", "1 · Gomas elásticas", "Fondo ambiental"),
            ("Dos: dejarlas sueltas en una caja. Se rozan entre ellas y sufren las esquinas.", "2 · Sueltas en una caja", "Fondo ambiental"),
            ("Tres: dejarlas al sol o en sitios húmedos. Los colores se apagan y el cartón se comba.", "3 · Sol y humedad", "Fondo ambiental"),
            ("La solución es sencilla: cada carta protegida y en su sitio. Por ejemplo, con esto: {n}, con {c1}.", "La solución: {n}", "Producto real"),
            CTA]),
        "comparacion": ("producto", "Opción básica vs. opción de coleccionista", [
            ("Guardar cartas Pokémon: opción básica frente a opción de coleccionista.", "Básica vs. coleccionista", "Fondo ambiental"),
            ("Opción básica: una caja o un taco de cartas. Sale barato, pero las cartas rozan y cuesta encontrar nada.", "Básica: caja o taco de cartas", "Fondo ambiental"),
            ("Opción de coleccionista: {n}.", "Coleccionista: {n}", "Producto real"),
            ("Qué cambia: {c1}, {c2} y {c3}.", "{c1} · {c2} · {c3}", "Detalles reales del producto"),
            ("Si solo tienes unas pocas cartas, la básica te vale. Si tu colección crece, toca dar el salto.", "¿Tu colección crece?", "Producto real"),
            CTA]),
        "regalo": ("producto", "Regalo para un fan de Pokémon", [
            ("¿Tienes que regalar algo a un fan de Pokémon y no entiendes de cartas?", "¿Regalo para un fan de Pokémon?", "Fondo ambiental (regalo, sin cartas inventadas)"),
            ("No hace falta acertar con la expansión ni con el idioma. Un accesorio para su colección le sirve tenga las cartas que tenga.", "Sin acertar expansión ni idioma", "Fondo ambiental"),
            ("Por ejemplo: {n}.", "{n}", "Producto real"),
            ("{c1}. {c2}. {c3}.", "{c1} · {c2} · {c3}", "Detalles reales del producto"),
            ("Ojo: las cartas no vienen incluidas, salvo que la ficha diga lo contrario. Míralo en el carrito naranja.", "Cartas no incluidas · Carrito naranja", "Plano final del producto real")]),
        "organizacion": ("coleccionismo", "Organiza tu colección en 3 pasos", [
            ("Cómo organizar tu colección de cartas Pokémon en tres pasos.", "Organiza tu colección en 3 pasos", "Fondo ambiental"),
            ("Paso uno: separa las cartas por expansión o por tipo. Elige un criterio y no lo cambies.", "1 · Un solo criterio", "Fondo ambiental"),
            ("Paso dos: las cartas que más te importan, siempre con funda antes de guardarlas.", "2 · Funda primero", "Fondo ambiental"),
            ("Paso tres: un sitio fijo para todas. Por ejemplo: {n}, con {c1}.", "3 · Un sitio fijo: {n}", "Producto real"),
            ("Guárdate este vídeo. El producto está en el carrito naranja.", "Carrito naranja", "Plano final del producto real")]),
    },
    "sellado": {
        "presentacion": ("producto", "Qué trae exactamente", [
            ("Qué trae exactamente: {n}.", "{n}", "Producto real precintado"),
            ("Es producto original y precintado, en {idioma}.", "Original · precintado · {idioma}", "Producto real, precinto visible"),
            ("Dentro vienen: {c1}, {c2} y {c3}.", "{c1} · {c2} · {c3}", "Foto real/autorizada del contenido"),
            (reglas.AVISO_AZAR + " Nadie sabe qué cartas hay dentro hasta abrirlos.", "Contenido de sobres: aleatorio", "Producto real"),
            CTA]),
        "regalo": ("producto", "Regalo Pokémon sin equivocarte", [
            ("Si vas a regalar cartas Pokémon, fíjate en dos cosas antes de comprar.", "2 cosas antes de regalar cartas", "Fondo ambiental"),
            ("Una: que sea producto original y precintado. Dos: el idioma. Este viene en {idioma}.", "Original · precintado · {idioma}", "Producto real, precinto visible"),
            ("Es esto: {n}. Incluye {c1}, {c2} y {c3}.", "{n}", "Producto real"),
            (reglas.AVISO_AZAR, "Contenido de sobres: aleatorio", "Producto real"),
            CTA]),
    },
}


class GuionInvalido(Exception):
    pass


def _comprobar_producto(p, borrador: bool) -> list[str]:
    carac = [c.strip() for c in (p["caracteristicas"] or "").split("|") if c.strip()]
    errores = []
    if len(carac) < 3:
        errores.append("faltan características verificadas (mínimo 3, separadas por |)")
    if p["categoria"] == "sellado" and p["idioma"] in (None, "no_aplica"):
        errores.append("producto sellado sin idioma")
    if not p["verificado_el"] and not borrador:
        errores.append("ficha sin verificar (verificado_el vacío). Usa --borrador solo para pruebas")
    if errores:
        raise GuionInvalido(f"Producto {p['id']} «{p['nombre_corto']}»: " + "; ".join(errores))
    return carac


def generar(con, producto_id: int, borrador: bool = False) -> list[int]:
    """Crea (o regenera) todos los guiones del producto. Devuelve sus ids."""
    p = con.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if p is None:
        raise GuionInvalido(f"No existe el producto {producto_id}")
    carac = _comprobar_producto(p, borrador)
    datos = {"n": p["nombre_corto"], "c1": carac[0], "c2": carac[1], "c3": carac[2], "idioma": p["idioma"] or ""}
    ids = []
    for formato, (tipo, titulo, escenas) in PLANTILLAS[p["categoria"]].items():
        hechas = [{"voz": v.format(**datos), "pantalla": t.format(**datos), "visual": vis} for v, t, vis in escenas]
        descripcion = f"{titulo} · {p['nombre_corto']} en el carrito naranja. "
        if p["categoria"] == "sellado":
            descripcion += reglas.AVISO_AZAR + " "
        descripcion += " ".join(ajustes.HASHTAGS_BASE)
        problemas = reglas.revisar(" ".join(e["voz"] + " " + e["pantalla"] for e in hechas) + " " + descripcion)
        if problemas:
            raise GuionInvalido(f"Guion «{formato}» incumple reglas: {', '.join(problemas)}")
        con.execute(
            "INSERT INTO guiones (producto_id, formato, tipo, titulo, escenas_json, descripcion) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(producto_id, formato) DO UPDATE SET tipo=excluded.tipo, titulo=excluded.titulo, "
            "escenas_json=excluded.escenas_json, descripcion=excluded.descripcion",
            (producto_id, formato, tipo, titulo, json.dumps(hechas, ensure_ascii=False), descripcion))
        ids.append(con.execute("SELECT id FROM guiones WHERE producto_id=? AND formato=?",
                               (producto_id, formato)).fetchone()["id"])
    con.commit()
    return ids

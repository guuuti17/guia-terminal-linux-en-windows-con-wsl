"""Reglas de cumplimiento Pokémon TCG / TikTok Shop aplicadas a todo texto generado."""
import re

# Expresiones que no pueden aparecer en guiones ni descripciones.
PROHIBIDO = [
    (r"\binversi[oó]n\b|\brevaloriz|\bsubir[aá] de precio|\bganar dinero", "promesa de inversión/rentabilidad"),
    (r"\bgarantiz|\bseguro que (te )?(toca|sale)|\bte va a (tocar|salir)|\bsiempre (toca|sale)",
     "garantía de cartas raras o resultados"),
    (r"\bvale(n)? (m[aá]s de )?\d+ ?(€|euros)", "afirmación de valor de cartas"),
    (r"\b(el|la) m[aá]s barat[oa]\b|\bprecio m[aá]s bajo\b|\b(el|la) mejor del mercado\b",
     "superlativo de precio/calidad no demostrable"),
    (r"\b[uú]ltimas unidades\b|\bse agota(n)? hoy\b", "urgencia falsa"),
    (r"\bproxy\b|\br[eé]plica", "proxies/réplicas no se promocionan"),
]

AVISO_AZAR = "El contenido de los sobres es aleatorio."

AUTENTICIDADES = {
    "oficial",      # producto original de The Pokémon Company
    "licenciado",   # accesorio con licencia oficial (p. ej. Ultra PRO)
    "generico",     # accesorio sin marca Pokémon (válido: no usa la marca)
    "no_oficial",   # usa marca/arte Pokémon sin licencia, proxies, réplicas -> SE RECHAZA
}


def revisar(texto: str) -> list[str]:
    """Devuelve la lista de problemas encontrados en un texto (vacía = correcto)."""
    return [motivo for patron, motivo in PROHIBIDO if re.search(patron, texto, re.IGNORECASE)]

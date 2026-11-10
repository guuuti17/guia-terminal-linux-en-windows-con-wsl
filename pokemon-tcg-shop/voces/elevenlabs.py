"""Voz sintética con la API oficial de ElevenLabs. Nunca gasta sin confirmación explícita."""
import json
import requests
from configuracion import ajustes

API = "https://api.elevenlabs.io/v1"


def _cabeceras() -> dict:
    if not ajustes.ELEVENLABS_API_KEY:
        raise RuntimeError("Falta ELEVENLABS_API_KEY en .env")
    return {"xi-api-key": ajustes.ELEVENLABS_API_KEY}


def cuota() -> dict:
    """Consulta gratuita: caracteres usados y límite del plan."""
    r = requests.get(f"{API}/user/subscription", headers=_cabeceras(), timeout=30)
    r.raise_for_status()
    d = r.json()
    return {"plan": d["tier"], "usados": d["character_count"], "limite": d["character_limit"]}


def listar_voces() -> list[dict]:
    """Consulta gratuita: voces disponibles en tu cuenta."""
    r = requests.get(f"{API}/voices", headers=_cabeceras(), timeout=30)
    r.raise_for_status()
    return [{"id": v["voice_id"], "nombre": v["name"], "idioma": (v.get("labels") or {}).get("language", "")}
            for v in r.json()["voices"]]


def pendientes(con, producto_id: int) -> list[tuple]:
    """Escenas sin audio todavía: (guion_id, nº escena, texto, ruta mp3)."""
    faltan = []
    for g in con.execute("SELECT id, escenas_json FROM guiones WHERE producto_id = ?", (producto_id,)):
        for i, e in enumerate(json.loads(g["escenas_json"])):
            ruta = ajustes.DIR_AUDIO / f"guion_{g['id']}" / f"escena_{i:02d}.mp3"
            if not ruta.exists():
                faltan.append((g["id"], i, e["voz"], ruta))
    return faltan


def estimar(faltan) -> tuple[int, float]:
    caracteres = sum(len(t) for _, _, t, _ in faltan)
    return caracteres, round(caracteres / 1000 * ajustes.EUR_POR_1000_CARACTERES, 2)


def generar(con, producto_id: int) -> tuple[int, float]:
    """Genera los audios pendientes y registra el coste. Llamar SOLO con gasto confirmado."""
    if not ajustes.ELEVENLABS_VOICE_ID:
        raise RuntimeError("Falta ELEVENLABS_VOICE_ID en .env (ejecuta: python main.py voces-listar)")
    faltan = pendientes(con, producto_id)
    hechos = 0
    try:
        for _, _, texto, ruta in faltan:
            r = requests.post(
                f"{API}/text-to-speech/{ajustes.ELEVENLABS_VOICE_ID}",
                params={"output_format": "mp3_44100_128"}, headers=_cabeceras(), timeout=120,
                json={"text": texto, "model_id": ajustes.ELEVENLABS_MODELO, "language_code": "es"}
                if "v2_5" in ajustes.ELEVENLABS_MODELO else {"text": texto, "model_id": ajustes.ELEVENLABS_MODELO})
            r.raise_for_status()
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(r.content)
            hechos += 1
    finally:  # registra lo realmente gastado aunque falle a mitad
        caracteres, euros = estimar(faltan[:hechos])
        if hechos:
            con.execute("INSERT INTO costes (concepto, tipo, importe_eur, unidades, producto_id) VALUES (?,?,?,?,?)",
                        ("Voz ElevenLabs", "ia", euros, f"{caracteres} caracteres", producto_id))
            con.commit()
    return caracteres, euros

"""Ajustes centrales. Las claves API solo se leen de variables de entorno (.env)."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

try:  # python-dotenv es opcional
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
except ImportError:
    pass

BD = Path(os.getenv("PTS_BD", RAIZ / "negocio.sqlite3"))
DIR_MEDIOS = RAIZ / "productos" / "medios"      # fotos/clips REALES y autorizados, por producto
DIR_AUDIO = RAIZ / "voces" / "audio"
DIR_VIDEOS = RAIZ / "videos"
DIR_LOTES = RAIZ / "publicaciones" / "lotes"

# --- Voz (ElevenLabs) ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODELO = os.getenv("ELEVENLABS_MODELO", "eleven_multilingual_v2")
# Coste orientativo para el control económico (plan Starter: 5 $/mes ≈ 4,7 € por 30.000 créditos).
# Ajústalo a tu plan real en .env; es una estimación contable, no un precio oficial.
EUR_POR_1000_CARACTERES = float(os.getenv("EUR_POR_1000_CARACTERES", "0.16"))

# --- Vídeo ---
ANCHO, ALTO, FPS = 1080, 1920, 30
FUENTE = os.getenv("PTS_FUENTE", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
PALABRAS_POR_SEGUNDO = 2.7  # para estimar duración cuando aún no hay voz

# --- Calendario (HIPÓTESIS iniciales, a validar con tus analíticas) ---
HORAS_PUBLICACION = os.getenv("PTS_HORAS", "13:30,20:30").split(",")

HASHTAGS_BASE = ["#pokemontcg", "#cartaspokemon", "#jccpokemon", "#coleccionismo", "#tiktokshopespaña"]

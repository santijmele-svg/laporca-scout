"""
Geocoding gratis con Nominatim (OpenStreetMap).
Tiene rate limit de 1 req/seg, así que cacheamos en SQLite.
"""
import logging
import time
import sqlite3
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DB = "data/geocode_cache.db"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "LaPorcaScout/1.0 (locales-scout)"


def _conn():
    Path(CACHE_DB).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(CACHE_DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            direccion TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            fecha TEXT
        )
    """)
    return c


def geocodificar(direccion: str, ciudad: str, provincia: str) -> tuple[float | None, float | None]:
    """Devuelve (lat, lon) o (None, None). Cachea resultados."""
    if not direccion:
        return None, None

    query = f"{direccion}, {ciudad}, {provincia}, Argentina"

    with _conn() as c:
        cached = c.execute(
            "SELECT lat, lon FROM cache WHERE direccion = ?",
            (query,)
        ).fetchone()
        if cached:
            return cached[0], cached[1]

    try:
        r = requests.get(
            NOMINATIM,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "ar"},
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        r.raise_for_status()
        results = r.json()
        time.sleep(1.1)  # rate limit Nominatim

        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            with _conn() as c:
                c.execute(
                    "INSERT OR REPLACE INTO cache (direccion, lat, lon, fecha) VALUES (?, ?, ?, datetime('now'))",
                    (query, lat, lon)
                )
            return lat, lon
    except Exception as e:
        logger.warning(f"Geocode fallo para '{query}': {e}")

    # Cachear fallos también para no reintentar
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO cache (direccion, lat, lon, fecha) VALUES (?, NULL, NULL, datetime('now'))",
            (query,)
        )
    return None, None

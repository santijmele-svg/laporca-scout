"""
Capa de persistencia. SQLite local — simple y suficiente.
Maneja deduplicación por hash y tracking histórico.
"""
import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from config import DB_PATH


def _conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Crea las tablas si no existen."""
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS propiedades (
            id TEXT PRIMARY KEY,              -- hash url+precio
            url TEXT NOT NULL,
            portal TEXT NOT NULL,             -- argenprop / zonaprop / ml / inmobiliaria_local
            zona TEXT NOT NULL,
            titulo TEXT,
            descripcion TEXT,
            direccion TEXT,
            precio REAL,
            moneda TEXT,
            superficie_m2 REAL,
            lat REAL,
            lon REAL,
            score INTEGER DEFAULT 0,
            criterios_match TEXT,             -- JSON con qué blandos matchearon
            primera_vez_visto TEXT NOT NULL,
            ultima_vez_visto TEXT NOT NULL,
            estado TEXT DEFAULT 'activa',     -- activa / desaparecida
            descartada INTEGER DEFAULT 0,     -- el usuario la marcó como no interesante
            notas TEXT
        );

        CREATE TABLE IF NOT EXISTS historico_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            propiedad_id TEXT NOT NULL,
            precio REAL,
            moneda TEXT,
            fecha TEXT NOT NULL,
            FOREIGN KEY (propiedad_id) REFERENCES propiedades(id)
        );

        CREATE INDEX IF NOT EXISTS idx_zona ON propiedades(zona);
        CREATE INDEX IF NOT EXISTS idx_score ON propiedades(score DESC);
        CREATE INDEX IF NOT EXISTS idx_estado ON propiedades(estado);
        """)


def hash_id(url: str, precio: float | None) -> str:
    """ID estable: url + precio. Si baja el precio, contamos como cambio histórico."""
    base = f"{url}|{precio or 0}"
    return hashlib.sha1(base.encode()).hexdigest()[:16]


def upsert_propiedad(prop: dict) -> str:
    """
    Inserta o actualiza una propiedad. Devuelve 'nueva', 'actualizada' o 'sin_cambios'.
    """
    pid = hash_id(prop["url"], prop.get("precio"))
    now = datetime.utcnow().isoformat(timespec="seconds")

    with _conn() as c:
        existente = c.execute(
            "SELECT id, precio FROM propiedades WHERE url = ?",
            (prop["url"],)
        ).fetchone()

        if existente is None:
            # Nueva
            c.execute("""
                INSERT INTO propiedades
                (id, url, portal, zona, titulo, descripcion, direccion,
                 precio, moneda, superficie_m2, lat, lon, score, criterios_match,
                 primera_vez_visto, ultima_vez_visto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pid, prop["url"], prop["portal"], prop["zona"],
                prop.get("titulo"), prop.get("descripcion"), prop.get("direccion"),
                prop.get("precio"), prop.get("moneda"), prop.get("superficie_m2"),
                prop.get("lat"), prop.get("lon"),
                prop.get("score", 0),
                json.dumps(prop.get("criterios_match", [])),
                now, now
            ))
            c.execute("""
                INSERT INTO historico_precios (propiedad_id, precio, moneda, fecha)
                VALUES (?, ?, ?, ?)
            """, (pid, prop.get("precio"), prop.get("moneda"), now))
            return "nueva"

        # Existente: actualizar last seen y precio si cambió
        old_id, old_precio = existente
        if old_precio != prop.get("precio"):
            c.execute("""
                UPDATE propiedades
                SET ultima_vez_visto = ?, precio = ?, score = ?, criterios_match = ?,
                    estado = 'activa'
                WHERE id = ?
            """, (now, prop.get("precio"), prop.get("score", 0),
                  json.dumps(prop.get("criterios_match", [])), old_id))
            c.execute("""
                INSERT INTO historico_precios (propiedad_id, precio, moneda, fecha)
                VALUES (?, ?, ?, ?)
            """, (old_id, prop.get("precio"), prop.get("moneda"), now))
            return "actualizada"

        c.execute(
            "UPDATE propiedades SET ultima_vez_visto = ?, estado = 'activa' WHERE id = ?",
            (now, old_id)
        )
        return "sin_cambios"


def marcar_desaparecidas(urls_vistas_hoy: set[str], portal: str):
    """Las que ya no aparecen en el portal probablemente se alquilaron."""
    with _conn() as c:
        if not urls_vistas_hoy:
            return
        # Marcar como desaparecidas las del portal que no se vieron hoy
        placeholders = ",".join("?" * len(urls_vistas_hoy))
        c.execute(f"""
            UPDATE propiedades
            SET estado = 'desaparecida'
            WHERE portal = ? AND estado = 'activa'
              AND url NOT IN ({placeholders})
        """, (portal, *urls_vistas_hoy))


def export_para_dashboard() -> list[dict]:
    """Exporta las propiedades activas y no descartadas para el JSON del dashboard."""
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("""
            SELECT * FROM propiedades
            WHERE estado = 'activa' AND descartada = 0
            ORDER BY score DESC, ultima_vez_visto DESC
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["criterios_match"] = json.loads(d["criterios_match"] or "[]")
            result.append(d)
        return result


if __name__ == "__main__":
    init_db()
    print(f"Base inicializada en {DB_PATH}")

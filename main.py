"""
Punto de entrada del autómata. Corre una vez por día.
Flujo:
  1. Por cada zona, por cada portal: scrapea
  2. Aplica filtros duros y scoring
  3. Geocodifica direcciones nuevas
  4. Persiste en SQLite (deduplicando)
  5. Marca como 'desaparecidas' las que ya no aparecen
  6. Exporta JSON al dashboard
"""
import json
import logging
import sys
import traceback
from pathlib import Path

from config import ZONAS, JSON_OUTPUT, LOG_PATH, MARKETPLACE_BUSQUEDAS, UMBRAL_INTERES
from db import init_db, upsert_propiedad, marcar_desaparecidas, export_para_dashboard
from scoring import pasa_filtros_duros, calcular_score
from scrapers import ALL_SCRAPERS
from geocoder import geocodificar


def setup_logging():
    Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(sys.stdout),
        ],
    )


def correr():
    log = logging.getLogger("main")
    init_db()

    stats = {"nuevas": 0, "actualizadas": 0, "sin_cambios": 0, "descartadas_filtro": 0, "nueva": 0, "actualizada": 0}
    urls_por_portal: dict[str, set] = {}

    for zona in ZONAS:
        log.info(f"=== Zona: {zona['nombre']} ===")
        for scraper in ALL_SCRAPERS:
            try:
                items = scraper.scrape_zona(zona)
            except Exception as e:
                log.error(f"  scraper {scraper.portal_name} reventó: {e}")
                log.debug(traceback.format_exc())
                continue

            urls_por_portal.setdefault(scraper.portal_name, set())

            for prop in items:
                # Filtros duros
                pasa, razon = pasa_filtros_duros(prop)
                if not pasa:
                    stats["descartadas_filtro"] += 1
                    continue

                # Scoring
                score, matches = calcular_score(prop)
                prop["score"] = score
                prop["criterios_match"] = matches

                # Geocoding (solo si no vino de ML que ya trae lat/lon)
                if not prop.get("lat") and prop.get("direccion"):
                    lat, lon = geocodificar(
                        prop["direccion"], zona["nombre"], zona["provincia"]
                    )
                    prop["lat"] = lat
                    prop["lon"] = lon

                # Si igual no tenemos lat/lon, usar el centro de la zona como fallback
                if not prop.get("lat"):
                    prop["lat"] = zona["centro"][0]
                    prop["lon"] = zona["centro"][1]

                # Persistir
                resultado = upsert_propiedad(prop)
                stats[resultado] = stats.get(resultado, 0) + 1
                urls_por_portal[scraper.portal_name].add(prop["url"])

    # Marcar desaparecidas
    for portal, urls in urls_por_portal.items():
        marcar_desaparecidas(urls, portal)

    # Exportar JSON para dashboard
    propiedades = export_para_dashboard()
    Path(JSON_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "actualizado": __import__("datetime").datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "total": len(propiedades),
            "umbral_interes": UMBRAL_INTERES,
            "stats": stats,
            "zonas": [
                {"nombre": z["nombre"], "centro": list(z["centro"])} for z in ZONAS
            ],
            "marketplace": MARKETPLACE_BUSQUEDAS,
            "propiedades": propiedades,
        }, f, ensure_ascii=False, indent=2)

    log.info(f"=== Resumen ===")
    log.info(f"  Nuevas: {stats['nuevas']}")
    log.info(f"  Actualizadas: {stats['actualizadas']}")
    log.info(f"  Sin cambios: {stats['sin_cambios']}")
    log.info(f"  Descartadas por filtro: {stats['descartadas_filtro']}")
    log.info(f"  Total activas en dashboard: {len(propiedades)}")


if __name__ == "__main__":
    setup_logging()
    correr()

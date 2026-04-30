"""
MercadoLibre Inmuebles — usa la API pública (sin auth necesaria para búsqueda).
Mucho más estable que scrapear HTML.

Docs: https://developers.mercadolibre.com.ar/es_ar/items-y-busquedas
"""
import logging
import requests
from .base import BaseScraper

logger = logging.getLogger(__name__)


class MercadoLibreScraper(BaseScraper):
    portal_name = "mercadolibre"
    API = "https://api.mercadolibre.com/sites/MLA/search"

    # Categoría MLA1473 = Inmuebles, MLA50547 = Locales Comerciales
    CATEGORIA_LOCALES = "MLA50547"

    def scrape_zona(self, zona: dict) -> list[dict]:
        logger.info(f"[ML] {zona['nombre']}")
        items = []
        offset = 0
        limit = 50

        while offset < 200:  # tope de 200 resultados por zona
            params = {
                "category": self.CATEGORIA_LOCALES,
                "q": zona["ml_query"],
                "OPERATION": "242075",  # Alquiler
                "offset": offset,
                "limit": limit,
            }
            try:
                r = requests.get(self.API, params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                logger.error(f"  ML error: {e}")
                break

            results = data.get("results", [])
            if not results:
                break

            for it in results:
                try:
                    # Atributos: superficie, ambientes, etc
                    attrs = {a["id"]: a for a in it.get("attributes", [])}
                    superficie = None
                    if "TOTAL_AREA" in attrs:
                        val = attrs["TOTAL_AREA"].get("value_struct")
                        if val:
                            superficie = float(val.get("number") or 0) or None
                    elif "COVERED_AREA" in attrs:
                        val = attrs["COVERED_AREA"].get("value_struct")
                        if val:
                            superficie = float(val.get("number") or 0) or None

                    direccion = ""
                    loc = it.get("location", {})
                    if loc:
                        partes = [
                            loc.get("address_line"),
                            loc.get("neighborhood", {}).get("name"),
                            loc.get("city", {}).get("name"),
                        ]
                        direccion = ", ".join(p for p in partes if p)

                    lat = None
                    lon = None
                    geo = it.get("location", {})
                    if geo:
                        lat = geo.get("latitude")
                        lon = geo.get("longitude")

                    items.append({
                        "url": it.get("permalink"),
                        "titulo": it.get("title"),
                        "descripcion": it.get("title", ""),  # ML no expone desc en search
                        "direccion": direccion,
                        "precio": it.get("price"),
                        "moneda": it.get("currency_id"),
                        "superficie_m2": superficie,
                        "lat": lat,
                        "lon": lon,
                    })
                except Exception as e:
                    logger.warning(f"  ML item parse fail: {e}")
                    continue

            offset += limit
            if len(results) < limit:
                break

        logger.info(f"  ML: {len(items)} items")
        return [self.normalizar(it, zona) for it in items]

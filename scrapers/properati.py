"""
Properati — locales en alquiler.
Es agregador, suele tener menos protección que Zonaprop. Usa requests + BS4.

URL pattern: https://www.properati.com.ar/s/{zona-slug}/local/alquiler
"""
import logging
import re
import time
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ProperatiScraper(BaseScraper):
    portal_name = "properati"
    BASE = "https://www.properati.com.ar"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-AR,es;q=0.9",
    }

    # Mapeo a slugs de Properati (algunos coinciden, otros no)
    ZONA_SLUG = {
        "Paraná": "parana",
        "Oro Verde": "oro-verde-entre-rios",
        "San Benito": "san-benito-entre-rios",
        "Santa Fe": "santa-fe-santa-fe",
        "Santo Tomé": "santo-tome-santa-fe",
    }

    def scrape_zona(self, zona: dict) -> list[dict]:
        slug = self.ZONA_SLUG.get(zona["nombre"])
        if not slug:
            logger.warning(f"[Properati] sin slug para {zona['nombre']}")
            return []

        url_base = f"{self.BASE}/s/{slug}/local/alquiler"
        logger.info(f"[Properati] {zona['nombre']}: {url_base}")
        items = []

        for pagina in range(1, 6):
            url = url_base if pagina == 1 else f"{url_base}?page={pagina}"
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=20)
                if r.status_code == 404:
                    break
                r.raise_for_status()
            except Exception as e:
                logger.error(f"  Properati error pag {pagina}: {e}")
                break

            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("[data-testid='listing-card'], .listing-card, article")
            if not cards:
                logger.info(f"  página {pagina}: sin cards, corto.")
                break

            page_items = 0
            for card in cards:
                try:
                    link = card.select_one("a[href]")
                    if not link:
                        continue
                    href = link.get("href", "")
                    full_url = self.BASE + href if href.startswith("/") else href
                    if "/p/" not in full_url and "/inmuebles/" not in full_url:
                        continue  # filtrar enlaces que no son a publicaciones

                    titulo_el = card.select_one("h2, h3, .listing-card__title")
                    direccion_el = card.select_one(".listing-card__location, [class*='location']")
                    precio_el = card.select_one(".listing-card__price, [class*='price']")

                    titulo = titulo_el.get_text(strip=True) if titulo_el else ""
                    direccion = direccion_el.get_text(strip=True) if direccion_el else ""
                    precio_txt = precio_el.get_text(strip=True) if precio_el else ""

                    # Properati a veces incluye m² en el card
                    features_txt = card.get_text(" ", strip=True)
                    superficie = self._parse_superficie(features_txt)

                    precio, moneda = self._parse_precio(precio_txt)

                    items.append({
                        "url": full_url,
                        "titulo": titulo,
                        "descripcion": features_txt[:500],
                        "direccion": direccion,
                        "precio": precio,
                        "moneda": moneda,
                        "superficie_m2": superficie,
                    })
                    page_items += 1
                except Exception as e:
                    logger.warning(f"  card fail: {e}")
                    continue

            logger.info(f"  página {pagina}: {page_items} items")
            if page_items == 0:
                break
            time.sleep(1.5)  # cortés

        # Dedup por URL dentro del mismo scrape
        seen = set()
        deduped = []
        for it in items:
            if it["url"] not in seen:
                seen.add(it["url"])
                deduped.append(it)

        return [self.normalizar(it, zona) for it in deduped]

    @staticmethod
    def _parse_precio(txt: str) -> tuple[float | None, str | None]:
        if not txt:
            return None, None
        moneda = "USD" if "USD" in txt or "U$S" in txt else "ARS"
        clean = txt.replace(".", "").replace(",", ".")
        nums = re.findall(r"\d+\.?\d*", clean)
        if nums:
            try:
                return float(nums[0]), moneda
            except ValueError:
                pass
        return None, moneda

    @staticmethod
    def _parse_superficie(txt: str) -> float | None:
        if not txt:
            return None
        m = re.search(r"(\d{2,4})\s*m[²2]", txt.lower())
        if m:
            val = float(m.group(1))
            if 20 <= val <= 2000:
                return val
        return None

"""
Argenprop — locales en alquiler.
Usa Playwright porque tiene anti-bot básico.

URL pattern: https://www.argenprop.com/locales-comerciales/alquiler/{slug-zona}
"""
import logging
import re
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ArgenpropScraper(BaseScraper):
    portal_name = "argenprop"
    BASE = "https://www.argenprop.com"

    def scrape_zona(self, zona: dict) -> list[dict]:
        url = f"{self.BASE}/locales-comerciales/alquiler/{zona['argenprop_slug']}"
        logger.info(f"[Argenprop] {zona['nombre']}: {url}")
        items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Paginación: capturamos hasta 5 páginas o hasta que no haya más
                for pagina in range(1, 6):
                    if pagina > 1:
                        next_url = f"{url}?pagina-{pagina}"
                        page.goto(next_url, wait_until="domcontentloaded", timeout=30000)

                    try:
                        page.wait_for_selector(".listing__items .listing__item", timeout=10000)
                    except PWTimeout:
                        logger.info(f"  página {pagina}: sin resultados, corto.")
                        break

                    cards = page.query_selector_all(".listing__items .listing__item")
                    if not cards:
                        break

                    for card in cards:
                        try:
                            link_el = card.query_selector("a")
                            if not link_el:
                                continue
                            href = link_el.get_attribute("href") or ""
                            full_url = self.BASE + href if href.startswith("/") else href

                            titulo_el = card.query_selector(".card__title")
                            direccion_el = card.query_selector(".card__address")
                            precio_el = card.query_selector(".card__price")
                            features = card.query_selector(".card__main-features")

                            titulo = titulo_el.inner_text().strip() if titulo_el else ""
                            direccion = direccion_el.inner_text().strip() if direccion_el else ""
                            precio_txt = precio_el.inner_text().strip() if precio_el else ""
                            features_txt = features.inner_text().strip() if features else ""

                            precio, moneda = self._parse_precio(precio_txt)
                            superficie = self._parse_superficie(features_txt)

                            items.append({
                                "url": full_url,
                                "titulo": titulo,
                                "descripcion": features_txt,
                                "direccion": direccion,
                                "precio": precio,
                                "moneda": moneda,
                                "superficie_m2": superficie,
                            })
                        except Exception as e:
                            logger.warning(f"  fallo en card: {e}")
                            continue

                    logger.info(f"  página {pagina}: {len(cards)} cards")
            finally:
                browser.close()

        return [self.normalizar(it, zona) for it in items]

    @staticmethod
    def _parse_precio(txt: str) -> tuple[float | None, str | None]:
        if not txt:
            return None, None
        txt = txt.replace(".", "").replace(",", ".")
        moneda = "USD" if "USD" in txt or "U$S" in txt else "ARS"
        nums = re.findall(r"\d+\.?\d*", txt)
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
        m = re.search(r"(\d{2,4})\s*m", txt.lower())
        if m:
            return float(m.group(1))
        return None

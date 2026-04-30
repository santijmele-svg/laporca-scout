"""
Zonaprop — locales en alquiler.
Igual que Argenprop, requiere Playwright. Tiene Cloudflare así que conviene
correrlo con headers realistas y delay entre requests.

URL pattern: https://www.zonaprop.com.ar/locales-comerciales-alquiler-{slug}.html
"""
import logging
import re
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ZonapropScraper(BaseScraper):
    portal_name = "zonaprop"
    BASE = "https://www.zonaprop.com.ar"

    def scrape_zona(self, zona: dict) -> list[dict]:
        url = f"{self.BASE}/locales-comerciales-alquiler-{zona['zonaprop_slug']}.html"
        logger.info(f"[Zonaprop] {zona['nombre']}: {url}")
        items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768}
            )
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(3)  # esperar Cloudflare check

                for pagina in range(1, 6):
                    if pagina > 1:
                        next_url = url.replace(".html", f"-pagina-{pagina}.html")
                        page.goto(next_url, wait_until="domcontentloaded", timeout=45000)
                        time.sleep(2)

                    try:
                        page.wait_for_selector("[data-qa='posting PROPERTY']", timeout=15000)
                    except PWTimeout:
                        logger.info(f"  página {pagina}: sin resultados, corto.")
                        break

                    cards = page.query_selector_all("[data-qa='posting PROPERTY']")
                    if not cards:
                        break

                    for card in cards:
                        try:
                            link_el = card.query_selector("h3 a") or card.query_selector("a")
                            href = link_el.get_attribute("href") if link_el else ""
                            full_url = self.BASE + href if href and href.startswith("/") else href

                            precio_el = card.query_selector("[data-qa='POSTING_CARD_PRICE']")
                            direccion_el = card.query_selector("[data-qa='POSTING_CARD_LOCATION']")
                            features_el = card.query_selector("[data-qa='POSTING_CARD_FEATURES']")
                            titulo_el = card.query_selector("h3")

                            titulo = titulo_el.inner_text().strip() if titulo_el else ""
                            direccion = direccion_el.inner_text().strip() if direccion_el else ""
                            precio_txt = precio_el.inner_text().strip() if precio_el else ""
                            features_txt = features_el.inner_text().strip() if features_el else ""

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
                    time.sleep(2)  # rate limit cortés
            finally:
                browser.close()

        return [self.normalizar(it, zona) for it in items]

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
        m = re.search(r"(\d{2,4})\s*m", txt.lower())
        if m:
            return float(m.group(1))
        return None

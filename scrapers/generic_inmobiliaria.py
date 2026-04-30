"""
Scraper genérico para inmobiliarias locales.

Heurística: visita la home, busca todos los links que parezcan ser de propiedades
en alquiler de tipo local comercial, y extrae info con patrones comunes.

NO va a funcionar perfectamente con todas. Es un primer intento que cubre
las que tengan estructura "estándar" (CMS tipo Pixel Inmobiliario, Mapaprop,
plantillas de RE/MAX, sitios WordPress con el plugin típico).

Para inmobiliarias importantes que no funcionen bien con el genérico,
se crea un scraper dedicado heredando de BaseScraper.
"""
import logging
import re
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)


# Patrones que sugieren que un link es una publicación de local en alquiler
PATTERNS_URL_LOCAL = [
    re.compile(r"local", re.I),
    re.compile(r"comercial", re.I),
]
PATTERNS_URL_ALQUILER = [
    re.compile(r"alquil", re.I),
    re.compile(r"renta", re.I),
]

# Términos que sugieren que la propiedad es lo que buscamos
KEYWORDS_RELEVANTES = [
    "local", "salón", "comercial", "alquiler", "alquila"
]


class GenericInmobiliariaScraper(BaseScraper):
    """
    Se construye con el dict de la inmobiliaria del config.
    portal_name = nombre de la inmobiliaria (slug-ificado)
    """
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-AR,es;q=0.9",
    }
    MAX_PAGES_TO_VISIT = 20  # cap para no quedar dando vueltas

    def __init__(self, inmobiliaria: dict):
        self.inmobiliaria = inmobiliaria
        self.portal_name = "inmo:" + self._slug(inmobiliaria["nombre"])
        self.base_url = inmobiliaria["url"].rstrip("/")
        self.zonas_target = set(inmobiliaria["zonas"])

    @staticmethod
    def _slug(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

    def scrape_zona(self, zona: dict) -> list[dict]:
        # Solo scrapeamos esta inmobiliaria si tiene esa zona en su lista
        if zona["nombre"] not in self.zonas_target:
            return []

        logger.info(f"[{self.portal_name}] {zona['nombre']}: {self.base_url}")

        # Paso 1: descargar home y otras páginas potenciales de listado
        candidate_urls = [
            self.base_url,
            f"{self.base_url}/alquiler",
            f"{self.base_url}/alquileres",
            f"{self.base_url}/locales",
            f"{self.base_url}/locales-en-alquiler",
            f"{self.base_url}/propiedades?operacion=alquiler&tipo=local",
        ]

        all_property_links = set()
        for cu in candidate_urls:
            html = self._fetch(cu)
            if not html:
                continue
            links = self._find_property_links(html, cu)
            all_property_links.update(links)
            time.sleep(0.5)

        if not all_property_links:
            logger.info(f"  no se encontraron links de propiedades")
            return []

        # Cap para no tardar demasiado por inmobiliaria
        property_links = list(all_property_links)[:self.MAX_PAGES_TO_VISIT]
        logger.info(f"  visitando {len(property_links)} páginas de propiedades")

        items = []
        for link in property_links:
            html = self._fetch(link)
            if not html:
                continue
            prop = self._parse_property_page(html, link, zona)
            if prop:
                items.append(prop)
            time.sleep(0.8)

        logger.info(f"  extraídos: {len(items)}")
        return [self.normalizar(it, zona) for it in items]

    def _fetch(self, url: str) -> str | None:
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=15, allow_redirects=True)
            if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
                return r.text
        except Exception as e:
            logger.debug(f"  fetch fail {url}: {e}")
        return None

    def _find_property_links(self, html: str, current_url: str) -> set[str]:
        """Extrae links que parezcan ser publicaciones de local en alquiler."""
        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(self.base_url).netloc
        found = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(current_url, href)
            # Solo links del mismo dominio
            if urlparse(full).netloc != base_domain:
                continue

            # Mirar el texto del link y la URL
            link_text = a.get_text(" ", strip=True).lower()
            url_lower = full.lower()
            combined = link_text + " " + url_lower

            # Heurística: tiene que mencionar local/comercial Y alquiler/renta
            has_local = any(p.search(combined) for p in PATTERNS_URL_LOCAL)
            has_alquiler = any(p.search(combined) for p in PATTERNS_URL_ALQUILER)

            if has_local and has_alquiler:
                # Filtrar enlaces que claramente no son a una publicación
                if any(skip in url_lower for skip in [
                    "javascript:", "mailto:", "#", "facebook.com", "instagram.com",
                    "/contacto", "/nosotros", "/servicios"
                ]):
                    continue
                found.add(full)

        return found

    def _parse_property_page(self, html: str, url: str, zona: dict) -> dict | None:
        """Extrae datos de una página de publicación con heurísticas."""
        soup = BeautifulSoup(html, "html.parser")

        # Título: h1 suele ser el título de la propiedad
        h1 = soup.find("h1")
        titulo = h1.get_text(strip=True) if h1 else ""

        # Body completo para keyword matching
        body_text = soup.get_text(" ", strip=True)
        body_lower = body_text.lower()

        # Filtro mínimo: debe parecer ser un local en alquiler
        if not any(kw in body_lower for kw in ["local", "salón", "comercial"]):
            return None
        if not any(kw in body_lower for kw in ["alquil", "renta"]):
            return None

        # Dirección: buscar patrones tipo "calle X al 1234" o usar el título
        direccion = self._extraer_direccion(body_text, titulo)

        # Precio
        precio, moneda = self._extraer_precio(body_text)

        # Superficie
        superficie = self._extraer_superficie(body_text)

        # Descripción: tomamos un fragmento útil
        # primero metadata description, sino los primeros párrafos largos
        descripcion = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            descripcion = meta_desc["content"]
        else:
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
            paragraphs = [p for p in paragraphs if len(p) > 40]
            descripcion = " ".join(paragraphs[:3])[:1000]

        return {
            "url": url,
            "titulo": titulo,
            "descripcion": descripcion or body_text[:500],
            "direccion": direccion,
            "precio": precio,
            "moneda": moneda,
            "superficie_m2": superficie,
        }

    @staticmethod
    def _extraer_direccion(body: str, titulo: str) -> str:
        # Patrón: "calle Foo 123" o "Av. Bar 456" o "Foo y Bar"
        # Primero probar en el título
        m = re.search(
            r"((?:av\.?|avenida|calle|bv\.?|boulevard|pje\.?|pasaje)?\s*"
            r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\s+\d{1,5})",
            titulo
        )
        if m:
            return m.group(1).strip()
        # Probar en cuerpo (limitamos los primeros 500 chars)
        m = re.search(
            r"((?:av\.?|avenida|calle|bv\.?|boulevard)\s+[A-ZÁÉÍÓÚÑ][\w áéíóúñ]+\s+\d{1,5})",
            body[:500]
        )
        if m:
            return m.group(1).strip()
        return ""

    @staticmethod
    def _extraer_precio(body: str) -> tuple[float | None, str | None]:
        # Buscar patrones tipo "$ 1.500.000" o "USD 3.500"
        m = re.search(
            r"(USD|U\$S|\$)\s*([\d\.]+)",
            body[:1500]
        )
        if not m:
            return None, None
        moneda = "USD" if m.group(1) in ("USD", "U$S") else "ARS"
        try:
            valor = float(m.group(2).replace(".", ""))
            # Sanity check: precios ARS suelen estar entre 100k y 10M, USD entre 500 y 20k
            if moneda == "ARS" and not (100_000 <= valor <= 50_000_000):
                return None, moneda
            if moneda == "USD" and not (200 <= valor <= 50_000):
                return None, moneda
            return valor, moneda
        except ValueError:
            return None, moneda

    @staticmethod
    def _extraer_superficie(body: str) -> float | None:
        # Patrones: "120 m²", "120m2", "120 mts", "120 metros cuadrados"
        m = re.search(
            r"(\d{2,4})\s*(?:m\s*²|m2|m\s+cubiertos|mts?(?:\s+cuadrados)?|metros\s+cuadrados)",
            body.lower()
        )
        if m:
            val = float(m.group(1))
            if 20 <= val <= 2000:
                return val
        return None

from .argenprop import ArgenpropScraper
from .zonaprop import ZonapropScraper
from .mercadolibre import MercadoLibreScraper
from .properati import ProperatiScraper
from .generic_inmobiliaria import GenericInmobiliariaScraper

# Importamos la lista de inmobiliarias del config
from config import INMOBILIARIAS_LOCALES


# Scrapers de portales nacionales (cubren todas las zonas)
PORTAL_SCRAPERS = [
    MercadoLibreScraper(),    # más estable: usa API pública
    ProperatiScraper(),       # requests + BS4
    ArgenpropScraper(),       # Playwright
    ZonapropScraper(),        # Playwright + Cloudflare
]

# Un GenericScraper por cada inmobiliaria local
INMOBILIARIA_SCRAPERS = [
    GenericInmobiliariaScraper(inmo) for inmo in INMOBILIARIAS_LOCALES
]

ALL_SCRAPERS = PORTAL_SCRAPERS + INMOBILIARIA_SCRAPERS

"""
Clase base de scrapers. Cada portal hereda y completa.
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Cada scraper devuelve una lista de dicts con keys estandarizadas."""

    portal_name: str = "base"

    @abstractmethod
    def scrape_zona(self, zona: dict) -> list[dict]:
        """
        Scrapea todos los locales en alquiler de la zona.
        Devuelve lista de dicts con keys:
        - url (str, requerido)
        - titulo (str)
        - descripcion (str)
        - direccion (str)
        - precio (float)
        - moneda (str: 'ARS' o 'USD')
        - superficie_m2 (float)
        """
        ...

    def normalizar(self, raw: dict, zona: dict) -> dict:
        """Agrega campos comunes a todos los scrapers."""
        return {
            **raw,
            "portal": self.portal_name,
            "zona": zona["nombre"],
        }

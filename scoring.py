"""
Aplica criterios duros (descarta) y calcula score blando (0-100).
"""
import re
from config import (CRITERIOS_DUROS, CRITERIOS_BLANDOS,
                    EXCLUIR_KEYWORDS, EXCEPCIONES_EXCLUSION)


def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    return texto.lower().strip()


def pasa_filtros_duros(prop: dict) -> tuple[bool, str]:
    """
    Devuelve (pasa, razon_si_no_pasa).
    """
    desc = _normalizar(prop.get("descripcion", "") + " " + prop.get("titulo", ""))

    # Exclusiones, salvo excepciones
    for kw in EXCLUIR_KEYWORDS:
        if kw in desc:
            # ¿Hay excepción que la salve?
            if any(exc in desc for exc in EXCEPCIONES_EXCLUSION):
                continue
            return False, f"contiene '{kw}'"

    # Superficie
    sup = prop.get("superficie_m2")
    if sup is not None:
        if sup < CRITERIOS_DUROS["superficie_min_m2"]:
            return False, f"superficie {sup}m² < mínimo {CRITERIOS_DUROS['superficie_min_m2']}m²"
        if sup > CRITERIOS_DUROS["superficie_max_m2"]:
            # No descartamos automáticamente si es algo más grande, solo si es muy desproporcionado
            if sup > CRITERIOS_DUROS["superficie_max_m2"] * 1.5:
                return False, f"superficie {sup}m² muy por encima del máximo"

    return True, ""


def calcular_score(prop: dict) -> tuple[int, list[str]]:
    """
    Score 0-100 basado en keywords blandas en titulo+descripcion.
    Devuelve (score, lista_criterios_match).
    """
    desc = _normalizar(prop.get("descripcion", "") + " " + prop.get("titulo", ""))
    score = 0
    matches = []

    for criterio, info in CRITERIOS_BLANDOS.items():
        for kw in info["keywords"]:
            if kw in desc:
                score += info["peso"]
                matches.append(criterio)
                break  # un criterio cuenta una sola vez

    # Bonus si la superficie está en el rango ideal estricto
    sup = prop.get("superficie_m2")
    if sup is not None and 80 <= sup <= 150:
        score += 10
        matches.append("superficie_ideal")

    return min(score, 100), matches


def extraer_superficie_de_texto(texto: str) -> float | None:
    """
    Intenta extraer m² de un texto libre cuando el portal no lo da estructurado.
    Busca patrones tipo '120 m2', '120m²', '120 mts', etc.
    """
    if not texto:
        return None
    patron = r'(\d{2,4})\s*(?:m2|m²|mts?|metros?\s*cuadrados?)'
    matches = re.findall(patron, texto.lower())
    if matches:
        # Devolvemos el primero razonable (entre 20 y 2000 m²)
        for m in matches:
            val = float(m)
            if 20 <= val <= 2000:
                return val
    return None

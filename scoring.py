"""
Filtros duros (descartan) y scoring blando (puntúa).

Filtros duros aplicados en orden:
  1. Moneda USD → descarta (probable venta, no alquiler)
  2. Precio en ARS por encima del máximo → descarta
  3. Superficie fuera de rango → descarta
  4. Coordenadas fuera del bounding box → descarta
  5. Keywords excluyentes en título/descripción → descarta
"""
import re
from config import (
    CRITERIOS_DUROS,
    CRITERIOS_BLANDOS,
    EXCLUIR_KEYWORDS,
    EXCEPCIONES_EXCLUSION,
    BBOX_GEO,
)


def pasa_filtros_duros(prop: dict) -> tuple[bool, str]:
    """
    Devuelve (True, "ok") si la propiedad pasa todos los filtros duros,
    o (False, "razón") con el motivo del descarte.
    """
    # 1. Moneda USD → descarta (es venta, no alquiler)
    moneda = (prop.get("moneda") or "").upper()
    if CRITERIOS_DUROS.get("descartar_usd", False) and moneda in ("USD", "U$S", "DOLAR", "DOLARES"):
        return False, "moneda_usd"

    # 2. Precio en ARS sobre el máximo
    precio = prop.get("precio")
    precio_max = CRITERIOS_DUROS.get("precio_max_ars")
    if precio_max and precio and moneda == "ARS":
        if precio > precio_max:
            return False, "precio_excede_max"

    # 3. Superficie
    sup = prop.get("superficie_m2")
    sup_min = CRITERIOS_DUROS.get("superficie_min_m2", 0)
    sup_max = CRITERIOS_DUROS.get("superficie_max_m2", 9999)
    if sup is not None:
        if sup < sup_min or sup > sup_max:
            return False, "superficie_fuera_de_rango"

    # 4. Bounding box geográfico
    lat = prop.get("lat")
    lon = prop.get("lon")
    if lat is not None and lon is not None and BBOX_GEO:
        if not (BBOX_GEO["lat_min"] <= lat <= BBOX_GEO["lat_max"]):
            return False, "fuera_de_zona_geografica"
        if not (BBOX_GEO["lon_min"] <= lon <= BBOX_GEO["lon_max"]):
            return False, "fuera_de_zona_geografica"

    # 5. Keywords excluyentes
    texto = (
        (prop.get("titulo") or "") + " " +
        (prop.get("descripcion") or "")
    ).lower()

    # Si matchea una keyword de exclusión PERO también una excepción, no se descarta
    for excl in EXCLUIR_KEYWORDS:
        if excl in texto:
            # Verificar excepciones
            tiene_excepcion = any(exc in texto for exc in EXCEPCIONES_EXCLUSION)
            if not tiene_excepcion:
                return False, f"contiene_keyword_excluyente:{excl}"

    return True, "ok"


def calcular_score(prop: dict) -> tuple[int, list[str]]:
    """
    Devuelve (score_total, lista_de_criterios_que_matchean).
    El score es la suma de pesos de los criterios blandos que coinciden.
    """
    texto = (
        (prop.get("titulo") or "") + " " +
        (prop.get("descripcion") or "")
    ).lower()

    score = 0
    matches = []

    for criterio_id, info in CRITERIOS_BLANDOS.items():
        # Caso especial: superficie ideal (no por keywords sino por valor numérico)
        if criterio_id == "superficie_ideal":
            sup = prop.get("superficie_m2")
            if sup and 90 <= sup <= 130:
                score += info["peso"]
                matches.append(criterio_id)
            continue

        # Caso normal: matchear keywords
        for kw in info["keywords"]:
            if kw.lower() in texto:
                score += info["peso"]
                matches.append(criterio_id)
                break  # un solo match por criterio

    return score, matches

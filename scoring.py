"""
Filtros duros (descartan) y scoring blando (puntúa).

Filtros duros aplicados en orden:
  1. Título basura/genérico → descarta
  2. Moneda USD → descarta (probable venta, no alquiler)
  3. Precio en ARS por encima del máximo → descarta
  4. Superficie fuera de rango → descarta
  5. Sin coordenadas válidas → descarta
  6. Coordenadas fuera del bounding box → descarta
  7. Keywords excluyentes → descarta
  8. Mención a otras ciudades fuera de zona → descarta

Las propiedades sin precio (que dicen "Consultar") SÍ pasan,
si cumplen el resto de los criterios.
"""
import re
from config import (
    CRITERIOS_DUROS,
    CRITERIOS_BLANDOS,
    EXCLUIR_KEYWORDS,
    EXCEPCIONES_EXCLUSION,
    BBOX_GEO,
)

# Títulos basura típicos de scrapers genéricos que extrajeron menús/headers
TITULOS_BASURA = [
    "propiedades",
    "properties",
    "locales en alquiler",
    "alquileres",
    "alquiler",
    "(sin título)",
    "sin título",
    "inmuebles",
    "ver propiedades",
    "ver más",
    "home",
    "inicio",
]

# Otras ciudades que NO queremos
CIUDADES_OTRAS = [
    "buenos aires", "caba", "capital federal", "rosario",
    "córdoba", "cordoba", "mendoza", "tucumán", "tucuman",
    "mar del plata", "punta del este", "uruguay",
    "concordia", "gualeguaychú", "gualeguaychu",
    "san nicolás", "san nicolas", "rafaela",
]

# Ciudades que SÍ son nuestras zonas
CIUDADES_OBJETIVO = [
    "paraná", "parana", "santa fe", "santo tomé", "santo tome",
    "oro verde", "san benito",
]


def pasa_filtros_duros(prop: dict) -> tuple[bool, str]:
    """
    Devuelve (True, "ok") si la propiedad pasa todos los filtros duros,
    o (False, "razón") con el motivo del descarte.
    """
    titulo = (prop.get("titulo") or "").strip()
    titulo_lower = titulo.lower()
    desc = (prop.get("descripcion") or "").strip()
    desc_lower = desc.lower()
    texto = (titulo_lower + " " + desc_lower)

    # 1. Título basura/genérico → descarta
    if not titulo or len(titulo) < 5:
        return False, "titulo_vacio_o_corto"
    for basura in TITULOS_BASURA:
        if titulo_lower == basura or titulo_lower.startswith(basura + " "):
            return False, f"titulo_basura:{basura}"

    # 2. Moneda USD → descarta SOLO si hay precio (sin precio dejamos pasar)
    moneda = (prop.get("moneda") or "").upper()
    precio = prop.get("precio")
    if precio and CRITERIOS_DUROS.get("descartar_usd", False):
        if moneda in ("USD", "U$S", "DOLAR", "DOLARES"):
            return False, "moneda_usd"

    # 3. Precio en ARS sobre el máximo (solo si hay precio)
    precio_max = CRITERIOS_DUROS.get("precio_max_ars")
    if precio_max and precio and moneda == "ARS":
        if precio > precio_max:
            return False, "precio_excede_max"

    # 4. Superficie
    sup = prop.get("superficie_m2")
    sup_min = CRITERIOS_DUROS.get("superficie_min_m2", 0)
    sup_max = CRITERIOS_DUROS.get("superficie_max_m2", 9999)
    if sup is not None:
        if sup < sup_min or sup > sup_max:
            return False, "superficie_fuera_de_rango"

    # 5. Sin coordenadas válidas → descarta
    lat = prop.get("lat")
    lon = prop.get("lon")
    if lat is None or lon is None:
        return False, "sin_coordenadas"

    # 6. Bounding box geográfico
    if BBOX_GEO:
        if not (BBOX_GEO["lat_min"] <= lat <= BBOX_GEO["lat_max"]):
            return False, "fuera_de_zona_geografica"
        if not (BBOX_GEO["lon_min"] <= lon <= BBOX_GEO["lon_max"]):
            return False, "fuera_de_zona_geografica"

    # 7. Keywords excluyentes
    for excl in EXCLUIR_KEYWORDS:
        if excl in texto:
            tiene_excepcion = any(exc in texto for exc in EXCEPCIONES_EXCLUSION)
            if not tiene_excepcion:
                return False, f"contiene_keyword_excluyente:{excl}"

    # 8. Mención a otras ciudades
    menciona_otra = any(c in texto for c in CIUDADES_OTRAS)
    menciona_objetivo = any(c in texto for c in CIUDADES_OBJETIVO)
    if menciona_otra and not menciona_objetivo:
        return False, "otra_ciudad"

    return True, "ok"


def calcular_score(prop: dict) -> tuple[int, list[str]]:
    """
    Devuelve (score_total, lista_de_criterios_que_matchean).
    """
    texto = (
        (prop.get("titulo") or "") + " " +
        (prop.get("descripcion") or "")
    ).lower()

    score = 0
    matches = []

    for criterio_id, info in CRITERIOS_BLANDOS.items():
        if criterio_id == "superficie_ideal":
            sup = prop.get("superficie_m2")
            if sup and 90 <= sup <= 130:
                score += info["peso"]
                matches.append(criterio_id)
            continue

        for kw in info["keywords"]:
            if kw.lower() in texto:
                score += info["peso"]
                matches.append(criterio_id)
                break

    return score, matches

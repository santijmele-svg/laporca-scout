"""
Filtros duros (descartan) y scoring blando (puntúa).

Filtros aflojados:
- Sin coordenadas → NO descarta (no se aplica filtro geográfico)
- Título basura → solo si es exactamente uno
- Otras ciudades → más estricto, solo si menciona Y NO menciona zona objetivo
"""
import re
from config import (
    CRITERIOS_DUROS,
    CRITERIOS_BLANDOS,
    EXCLUIR_KEYWORDS,
    EXCEPCIONES_EXCLUSION,
    BBOX_GEO,
)

# Solo descarta si el título es EXACTAMENTE uno de estos (sin texto adicional)
TITULOS_BASURA_EXACTOS = [
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

CIUDADES_OTRAS = [
    "buenos aires", "caba", "capital federal", "rosario",
    "córdoba", "mendoza", "tucumán",
    "mar del plata", "punta del este",
    "concordia", "gualeguaychú", "rafaela",
]

CIUDADES_OBJETIVO = [
    "paraná", "parana", "santa fe", "santo tomé", "santo tome",
    "oro verde", "san benito",
]


def pasa_filtros_duros(prop: dict) -> tuple[bool, str]:
    """
    Devuelve (True, "ok") o (False, "razón").
    """
    titulo = (prop.get("titulo") or "").strip()
    titulo_lower = titulo.lower()
    desc = (prop.get("descripcion") or "").strip()
    desc_lower = desc.lower()
    texto = (titulo_lower + " " + desc_lower)

    # 1. Título vacío → descarta
    if not titulo:
        return False, "titulo_vacio"

    # 2. Título basura EXACTO → descarta
    if titulo_lower in TITULOS_BASURA_EXACTOS:
        return False, f"titulo_basura_exacto:{titulo_lower}"

    # 3. Moneda USD → descarta SOLO si tiene precio
    moneda = (prop.get("moneda") or "").upper()
    precio = prop.get("precio")
    if precio and CRITERIOS_DUROS.get("descartar_usd", False):
        if moneda in ("USD", "U$S", "DOLAR", "DOLARES"):
            return False, "moneda_usd"

    # 4. Precio en ARS sobre el máximo
    precio_max = CRITERIOS_DUROS.get("precio_max_ars")
    if precio_max and precio and moneda == "ARS":
        if precio > precio_max:
            return False, "precio_excede_max"

    # 5. Superficie
    sup = prop.get("superficie_m2")
    sup_min = CRITERIOS_DUROS.get("superficie_min_m2", 0)
    sup_max = CRITERIOS_DUROS.get("superficie_max_m2", 9999)
    if sup is not None:
        if sup < sup_min or sup > sup_max:
            return False, "superficie_fuera_de_rango"

    # 6. Bounding box geográfico (SOLO si tiene coordenadas)
    lat = prop.get("lat")
    lon = prop.get("lon")
    if lat is not None and lon is not None and BBOX_GEO:
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

    # 8. Otras ciudades (filtro más estricto)
    # Solo descarta si menciona otra ciudad explícitamente
    # Y NO menciona ninguna de nuestras zonas
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

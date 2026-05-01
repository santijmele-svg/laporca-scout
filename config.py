"""
Configuración central del autómata.
Editar acá: zonas, criterios, inmobiliarias.
"""

# ---------- ZONAS ----------
# Cada zona define dónde buscar y centro geográfico para fallback de geocoding
ZONAS = [
    {
        "nombre": "Paraná",
        "provincia": "Entre Ríos",
        "centro": (-31.7319, -60.5238),
        "slug_argenprop": "parana",
        "slug_zonaprop": "parana-entre-rios",
        "slug_ml": "parana",
    },
    {
        "nombre": "Oro Verde",
        "provincia": "Entre Ríos",
        "centro": (-31.8267, -60.5306),
        "slug_argenprop": "oro-verde",
        "slug_zonaprop": "oro-verde-entre-rios",
        "slug_ml": "oro-verde",
    },
    {
        "nombre": "San Benito",
        "provincia": "Entre Ríos",
        "centro": (-31.7833, -60.4500),
        "slug_argenprop": "san-benito",
        "slug_zonaprop": "san-benito-entre-rios",
        "slug_ml": "san-benito",
    },
    {
        "nombre": "Santa Fe",
        "provincia": "Santa Fe",
        "centro": (-31.6333, -60.7000),
        "slug_argenprop": "santa-fe",
        "slug_zonaprop": "santa-fe-santa-fe",
        "slug_ml": "santa-fe",
    },
    {
        "nombre": "Santo Tomé",
        "provincia": "Santa Fe",
        "centro": (-31.6667, -60.7667),
        "slug_argenprop": "santo-tome",
        "slug_zonaprop": "santo-tome-santa-fe",
        "slug_ml": "santo-tome",
    },
]

# ---------- CRITERIOS DUROS (filtros que descartan) ----------
# Si una propiedad NO cumple esto, se descarta automáticamente
SUPERFICIE_MIN = 80     # m² mínimo (criterio La Porca)
SUPERFICIE_MAX = 225    # m² máximo (con tolerancia sobre los 150 ideales)

# Variable que usa scoring.py para los filtros duros
CRITERIOS_DUROS = {
    "superficie_min": SUPERFICIE_MIN,
    "superficie_max": SUPERFICIE_MAX,
}

# ---------- CRITERIOS BLANDOS (suman puntos al score) ----------
# Cada keyword que matchea suma sus puntos
CRITERIOS_BLANDOS = {
    "esquina": {"keywords": ["esquina", "ochava"], "puntos": 20},
    "buena_visibilidad": {"keywords": ["vidriera", "ventanal", "ventana grande"], "puntos": 15},
    "frente_amplio": {"keywords": ["6 mts de frente", "6m de frente", "frente amplio", "doble frente", "7 mts de frente", "8 mts de frente"], "puntos": 15},
    "alta_circulacion": {"keywords": ["alta circulación", "muy transitada", "avenida principal", "sobre avenida", "sobre av", "zona comercial"], "puntos": 10},
    "estacionamiento": {"keywords": ["estacionamiento", "cochera", "playa de estacionamiento"], "puntos": 5},
    "trifasica": {"keywords": ["trifásica", "trifasica", "380v", "380 v"], "puntos": 10},
    "apto_alimentos": {"keywords": ["apto alimentos", "apto gastronomía", "carnicería", "rotisería", "fiambrería", "supermercado"], "puntos": 15},
    "superficie_ideal": {"keywords": [], "puntos": 10},  # se asigna por código si está entre 90-130m²
}

UMBRAL_INTERES = 40  # Score a partir del cual una propiedad se marca como prioritaria

# ---------- KEYWORDS DE EXCLUSIÓN ----------
# Si la descripción contiene esto, se descarta (rompe el req "una sola planta")
EXCLUIR_KEYWORDS = [
    "primer piso", "1° piso", "segundo piso", "2° piso",
    "planta alta", "entrepiso",
    "oficina",      # buscamos local, no oficina pura
    "consultorio",  # idem, no es local comercial de alimentos
]

# Keywords que NO son de exclusión aunque matcheen las anteriores
# (ej: "local + oficina anexa" debería pasar, no es solo oficina)
EXCEPCIONES_EXCLUSION = [
    "local + oficina",
    "local y oficina",
    "local con oficina",
]

# ---------- ARCHIVOS DE SALIDA ----------
DB_PATH = "data/propiedades.db"
JSON_OUTPUT = "dashboard/data.json"
LOG_PATH = "data/scraper.log"

# ---------- INMOBILIARIAS LOCALES ----------
# Cada una se scrapea con el GenericScraper que intenta extraer listings
# con heurísticas. Las que no funcionen bien se refinan con un scraper dedicado.
# Para agregar una nueva: copiar formato y poner la URL del listado de alquileres.
INMOBILIARIAS_LOCALES = [
    # --- PARANÁ Y GRAN PARANÁ ---
    {"nombre": "Russo Real Estate", "url": "https://www.russorealestate.com.ar", "zonas": ["Paraná", "Oro Verde", "San Benito"]},
    {"nombre": "Walter Ferrando", "url": "https://www.walterferrando.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Campa Inmobiliaria", "url": "https://www.campainmobiliaria.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Gaspar Fita", "url": "https://www.gasparfita.com.ar", "zonas": ["Paraná"]},
    {"nombre": "JC Bustamante", "url": "https://www.jcbustamante.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Calabrese García", "url": "https://www.calabresegarcia.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Ramirez Bienes Raices", "url": "https://www.ramirezbienesraices.com.ar", "zonas": ["Paraná"]},
    {"nombre": "León Inmobiliaria", "url": "https://leoninmobiliaria.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Buscema", "url": "https://buscemainmobiliaria.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Umedez", "url": "https://inmobiliariaumedez.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Florencio Bogado", "url": "https://www.florenciobogado.com.ar", "zonas": ["Paraná"]},
    {"nombre": "Inmobiliaria Paraná", "url": "https://www.inmobiliariaparana.com.ar", "zonas": ["Paraná"]},

    # --- SANTA FE CAPITAL ---
    {"nombre": "Demichelis & Biasoni", "url": "https://www.demichelisbiasoni.com", "zonas": ["Santa Fe", "Santo Tomé"]},
    {"nombre": "Salas Inmobiliaria", "url": "https://www.salasinmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Anabel Inmobiliaria", "url": "https://www.anabelinmobiliaria.com.ar", "zonas": ["Santa Fe", "Santo Tomé"]},
    {"nombre": "Christen Inmobiliaria", "url": "https://www.christen.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Coldwell Banker Iovaldi", "url": "https://www.coldwellbanker.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Faro", "url": "https://www.remax.com.ar/oficina/remax-faro", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Futuro", "url": "https://www.remax.com.ar/oficina/remax-futuro", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Cordial", "url": "https://www.remax.com.ar/oficina/remax-cordial", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Impulso", "url": "https://www.remax.com.ar/oficina/remax-impulso", "zonas": ["Santa Fe"]},
    {"nombre": "Migone", "url": "https://migoneinmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Tomas Inmobiliaria", "url": "https://inmobiliariatomas.com.ar", "zonas": ["Santa Fe", "Santo Tomé"]},
    {"nombre": "Raíces Inmobiliaria", "url": "https://www.raicesinmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Imperio Servicios Inmobiliarios", "url": "https://www.imperiosi.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "CF Propiedades", "url": "https://www.cfpropiedades.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Orcu", "url": "https://www.orcuinmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Guastavino e Imbert", "url": "https://guastavinoeimbert.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Sauce", "url": "https://www.sauce.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Lenarduzzi", "url": "https://lenarduzzi.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Benuzzi", "url": "https://benuzzi.com", "zonas": ["Santa Fe"]},
    {"nombre": "Ureta Cortés", "url": "https://uretacortes.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Pilay", "url": "https://www.pilayinmobiliaria.com", "zonas": ["Santa Fe"]},

    # --- SANTO TOMÉ ---
    {"nombre": "Loquet", "url": "https://www.loquetinmobiliaria.com.ar", "zonas": ["Santo Tomé"]},
    {"nombre": "Santo Tomé Propiedades", "url": "https://santotomeprop.com.ar", "zonas": ["Santo Tomé"]},
    {"nombre": "APL Inmobiliaria", "url": "https://www.aplinmobiliaria.com", "zonas": ["Santo Tomé"]},
    {"nombre": "Inmobiliaria Abraham", "url": "https://inmobiliariaabraham.com.ar", "zonas": ["Santo Tomé"]},
    {"nombre": "Danisa Robledo Propiedades", "url": "https://danisarobledopropiedades.com.ar", "zonas": ["Santo Tomé"]},
    {"nombre": "Cometto Inmobiliaria", "url": "https://www.comettoinmobiliaria.com.ar", "zonas": ["Santo Tomé"]},
    {"nombre": "Questa Inmobiliaria", "url": "https://questainmobiliaria.com.ar", "zonas": ["Santo Tomé"]},
]

# ---------- FACEBOOK MARKETPLACE (búsquedas guardadas) ----------
# El dashboard muestra estos links como acceso directo. No se scrapea.
MARKETPLACE_BUSQUEDAS = [
    {"zona": "Paraná", "url": "https://www.facebook.com/marketplace/parana/propertyrentals?query=local%20comercial"},
    {"zona": "Santa Fe", "url": "https://www.facebook.com/marketplace/santafe/propertyrentals?query=local%20comercial"},
    {"zona": "Santo Tomé", "url": "https://www.facebook.com/marketplace/santotome/propertyrentals?query=local%20comercial"},
    {"zona": "Oro Verde", "url": "https://www.facebook.com/marketplace/category/propertyrentals?query=local%20oro%20verde"},
]

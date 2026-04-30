"""
Configuración central del scout de locales para La Porca.
Editá acá los criterios sin tocar el resto del código.
"""

# ---------- ZONAS DE BÚSQUEDA ----------
# Cada zona tiene su nombre normalizado y los slugs/queries que usa cada portal
ZONAS = [
    {
        "nombre": "Paraná",
        "provincia": "Entre Ríos",
        "argenprop_slug": "parana",
        "zonaprop_slug": "parana-entre-rios",
        "ml_query": "parana entre rios",
        "centro": (-31.7319, -60.5238),  # lat, lon para mapa
    },
    {
        "nombre": "Oro Verde",
        "provincia": "Entre Ríos",
        "argenprop_slug": "oro-verde",
        "zonaprop_slug": "oro-verde-entre-rios",
        "ml_query": "oro verde entre rios",
        "centro": (-31.8267, -60.5306),
    },
    {
        "nombre": "San Benito",
        "provincia": "Entre Ríos",
        "argenprop_slug": "san-benito-entre-rios",
        "zonaprop_slug": "san-benito-entre-rios",
        "ml_query": "san benito entre rios",
        "centro": (-31.7833, -60.4500),
    },
    {
        "nombre": "Santa Fe",
        "provincia": "Santa Fe",
        "argenprop_slug": "santa-fe",
        "zonaprop_slug": "santa-fe-capital",
        "ml_query": "santa fe capital",
        "centro": (-31.6333, -60.7000),
    },
    {
        "nombre": "Santo Tomé",
        "provincia": "Santa Fe",
        "argenprop_slug": "santo-tome-santa-fe",
        "zonaprop_slug": "santo-tome-santa-fe",
        "ml_query": "santo tome santa fe",
        "centro": (-31.6667, -60.7667),
    },
]

# ---------- CRITERIOS DUROS (filtros automáticos) ----------
CRITERIOS_DUROS = {
    "tipo": "local_comercial",      # solo locales en alquiler
    "operacion": "alquiler",
    "superficie_min_m2": 80,
    "superficie_max_m2": 150,
    "una_planta": True,             # se infiere por descripción
}

# ---------- CRITERIOS BLANDOS (scoring 0-100) ----------
# Cada uno suma puntos si la descripción del aviso lo menciona
CRITERIOS_BLANDOS = {
    "esquina": {
        "peso": 20,
        "keywords": ["esquina", "ochava", "doble frente"],
    },
    "frente_amplio": {
        "peso": 15,
        "keywords": ["6 mts de frente", "6m de frente", "amplio frente",
                     "7 mts de frente", "8 mts de frente", "gran frente",
                     "frente vidriado"],
    },
    "estacionamiento": {
        "peso": 10,
        "keywords": ["estacionamiento", "cochera", "playa de estacionamiento",
                     "espacio para estacionar"],
    },
    "alta_circulacion": {
        "peso": 15,
        "keywords": ["alta circulación", "muy transitada", "zona comercial",
                     "avenida", "peatonal", "céntrico", "centro comercial"],
    },
    "trifasica": {
        "peso": 10,
        "keywords": ["trifásica", "trifasica", "luz industrial", "380v",
                     "fuerza motriz"],
    },
    "apto_alimentos": {
        "peso": 15,
        "keywords": ["apto gastronomía", "apto alimentos", "habilitación gastronómica",
                     "carnicería", "rotisería", "fiambrería", "cámara",
                     "desagüe industrial", "agua caliente"],
    },
    "buena_visibilidad": {
        "peso": 15,
        "keywords": ["vidriera", "gran vidriera", "muy visible", "excelente ubicación",
                     "ubicación estratégica", "alta exposición"],
    },
}

# Las propiedades con score >= UMBRAL_INTERES van marcadas como "prioritarias"
UMBRAL_INTERES = 40

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

    # --- SANTA FE CAPITAL Y SANTO TOMÉ ---
    {"nombre": "Demichelis & Biasoni", "url": "https://www.demichelisbiasoni.com", "zonas": ["Santa Fe", "Santo Tomé"]},
    {"nombre": "Salas Inmobiliaria", "url": "https://www.salasinmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Anabel Inmobiliaria", "url": "https://www.anabelinmobiliaria.com.ar", "zonas": ["Santa Fe", "Santo Tomé"]},
    {"nombre": "Christen Inmobiliaria", "url": "https://www.christeninmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Coldwell Banker Iovaldi", "url": "https://www.coldwellbanker.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Faro", "url": "https://www.remax.com.ar/oficina/remax-faro", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Futuro", "url": "https://www.remax.com.ar/oficina/remax-futuro", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Cordial", "url": "https://www.remax.com.ar/oficina/remax-cordial", "zonas": ["Santa Fe"]},
    {"nombre": "RE/MAX Impulso", "url": "https://www.remax.com.ar/oficina/remax-impulso", "zonas": ["Santa Fe"]},
    {"nombre": "Migone", "url": "https://migoneinmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Tomas Inmobiliaria", "url": "https://inmobiliariatomas.com.ar", "zonas": ["Santa Fe", "Santo Tomé"]},
    {"nombre": "Loquet", "url": "https://www.loquetinmobiliaria.com.ar", "zonas": ["Santo Tomé"]},
    {"nombre": "Raíces Inmobiliaria", "url": "https://www.raicesinmobiliaria.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "Imperio Servicios Inmobiliarios", "url": "https://www.imperiosi.com.ar", "zonas": ["Santa Fe"]},
    {"nombre": "CF Propiedades", "url": "https://www.cfpropiedades.com.ar", "zonas": ["Santa Fe"]},
]

# ---------- FACEBOOK MARKETPLACE (búsquedas guardadas) ----------
# El dashboard muestra estos links como acceso directo. No se scrapea.
MARKETPLACE_BUSQUEDAS = [
    {"zona": "Paraná", "url": "https://www.facebook.com/marketplace/parana/propertyrentals?query=local%20comercial"},
    {"zona": "Santa Fe", "url": "https://www.facebook.com/marketplace/santafe/propertyrentals?query=local%20comercial"},
    {"zona": "Santo Tomé", "url": "https://www.facebook.com/marketplace/santotome/propertyrentals?query=local%20comercial"},
    {"zona": "Oro Verde", "url": "https://www.facebook.com/marketplace/category/propertyrentals?query=local%20oro%20verde"},
]

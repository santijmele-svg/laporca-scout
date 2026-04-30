# La Porca · Scout de Locales

Autómata que scrapea diariamente portales inmobiliarios e inmobiliarias locales
buscando locales comerciales en alquiler que cumplan con los **Requerimientos
Operativos de Puntos de Venta de La Porca**, en Paraná, Gran Paraná, Santa Fe
capital y Santo Tomé.

## Cómo funciona

1. **`main.py`** corre una vez por día (vía GitHub Actions) y por cada zona,
   por cada portal/inmobiliaria configurada, scrapea los locales en alquiler.
2. Aplica **filtros duros** (descarta lo que rompe los requisitos) y **scoring
   blando** (puntúa 0-100 según cuántos requisitos satisface).
3. **Geocodifica** cada dirección (caché local en SQLite con Nominatim).
4. **Persiste** en SQLite con histórico de precios y dedupe por URL.
5. Marca como **desaparecidas** las propiedades que ya no aparecen (probable
   señal de que se alquilaron).
6. Exporta `dashboard/data.json` y un workflow separado lo despliega en GitHub
   Pages como dashboard interactivo con mapa.

## Estructura

```
laporca-scout/
├── config.py                  ← Editá acá zonas, criterios e inmobiliarias
├── main.py                    ← Punto de entrada
├── db.py                      ← SQLite + dedupe + histórico
├── geocoder.py                ← Nominatim con caché
├── scoring.py                 ← Filtros duros y score blando
├── scrapers/
│   ├── base.py                ← Clase abstracta
│   ├── argenprop.py           ← Playwright
│   ├── zonaprop.py            ← Playwright + Cloudflare
│   ├── mercadolibre.py        ← API pública
│   ├── properati.py           ← requests + BS4
│   └── generic_inmobiliaria.py ← Heurístico para inmobiliarias locales
├── dashboard/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── data.json              ← Output del scraper, leído por el dashboard
├── data/
│   ├── propiedades.db         ← SQLite (se commitea para histórico)
│   ├── geocode_cache.db       ← Caché Nominatim
│   └── scraper.log
└── .github/workflows/
    ├── daily-scrape.yml       ← Cron diario
    └── deploy-pages.yml       ← Deploy del dashboard
```

## Setup local

```bash
git clone <tu-fork>
cd laporca-scout
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Inicializar la DB (la primera vez)
python -c "from db import init_db; init_db()"

# Correr el scraper
python main.py

# Ver el dashboard local (en otra terminal)
cd dashboard && python -m http.server 8000
# abrir http://localhost:8000
```

## Setup en GitHub

1. **Subir el repo a GitHub** (puede ser privado).
2. En *Settings → Pages*, configurar source = "GitHub Actions".
3. En *Settings → Actions → General → Workflow permissions*, marcar
   **"Read and write permissions"** (necesario para que la action commitee
   el JSON actualizado).
4. La acción corre todos los días a las 9 AM hora Argentina (12 UTC). También
   se puede correr manualmente desde *Actions → Daily scrape → Run workflow*.

## Editar criterios

Todo está en `config.py`:

- **`ZONAS`** — agregar/quitar zonas y sus slugs por portal.
- **`CRITERIOS_DUROS`** — superficie mínima/máxima.
- **`CRITERIOS_BLANDOS`** — keywords que suman puntos al score.
- **`UMBRAL_INTERES`** — score a partir del cual una propiedad se marca como
  prioritaria en el dashboard.
- **`EXCLUIR_KEYWORDS`** — descarta cualquier publicación que las contenga.
- **`INMOBILIARIAS_LOCALES`** — lista de inmobiliarias para scrapear con el
  scraper genérico. Para agregar una nueva, copiar formato y poner la URL
  raíz del sitio.
- **`MARKETPLACE_BUSQUEDAS`** — links a búsquedas guardadas de Facebook
  Marketplace por zona (no se scrapean, se muestran como acceso rápido).

## Limitaciones conocidas

- **Zonaprop y Argenprop** tienen anti-bot. El scraper funciona pero puede
  romperse si actualizan el HTML. Cuando eso pase, hay que actualizar los
  selectores CSS en los respectivos archivos.
- **Scraper genérico de inmobiliarias** funciona razonablemente bien con
  sitios "estándar" (Pixel Inmobiliario, RE/MAX, WordPress típico) pero
  va a fallar con sitios muy customizados. Las inmobiliarias importantes
  que no funcionen bien deberían tener su scraper dedicado.
- **Geocoding** usa Nominatim que tiene rate limit de 1 req/seg. La caché
  local evita re-geocodificar pero la primera corrida puede ser lenta.
- **Facebook Marketplace** no se scrapea (Meta no provee API y scrapearlo
  arriesga la cuenta). El dashboard incluye links a búsquedas guardadas
  para revisión manual.

## Workflow del usuario

En el dashboard se puede:

- **Filtrar** por zona, portal, score mínimo, superficie mínima.
- **Marcar** propiedades como **"de interés"** (★) — se guardan en
  localStorage del navegador.
- **Descartar** propiedades — se ocultan por defecto pero se pueden ver
  desactivando el filtro.
- **Tomar notas** sobre cada propiedad (también localStorage).
- Ver propiedades **NUEVAS** (≤48hs) marcadas en verde.
- Ver propiedades **prioritarias** (score ≥ 40) en amarillo.
- Click en cualquier propiedad → drawer con detalle completo y link al
  aviso original.

## Próximas mejoras

- [ ] Scraper dedicado para las inmobiliarias locales que no funcionen bien
      con el genérico (refinamiento iterativo).
- [ ] Mapeo de barrios por nivel socioeconómico (req #7 de La Porca).
- [ ] Notificación por email/WhatsApp de propiedades nuevas con score alto.
- [ ] Vista histórica de evolución de precios.

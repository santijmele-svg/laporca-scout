// =================================================================
// La Porca Scout - Dashboard logic
// =================================================================

const STORAGE_KEY_USER = 'laporca_user_state_v1';

const PORTAL_LABELS = {
  argenprop: 'ARGENPROP',
  zonaprop: 'ZONAPROP',
  mercadolibre: 'ML',
  properati: 'PROPERATI',
};

const state = {
  data: null,
  filters: {
    zonas: new Set(),
    portales: new Set(),
    scoreMin: 0,
    supMin: 0,
    soloPrioritarias: false,
    soloNuevas: false,
    ocultarDescartadas: true,
  },
  sortBy: 'score',
  user: loadUserState(),
  map: null,
  cluster: null,
  markers: new Map(),
};

// =================================================================
// Persistencia local
// =================================================================
function loadUserState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_USER);
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return { saved: {}, discarded: {}, notes: {} };
}

function persistUserState() {
  localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(state.user));
}

function isSaved(id) { return !!state.user.saved[id]; }
function isDiscarded(id) { return !!state.user.discarded[id]; }
function getNote(id) { return state.user.notes[id] || ''; }

function toggleSaved(id) {
  if (state.user.saved[id]) delete state.user.saved[id];
  else state.user.saved[id] = Date.now();
  persistUserState();
}

function toggleDiscarded(id) {
  if (state.user.discarded[id]) delete state.user.discarded[id];
  else state.user.discarded[id] = Date.now();
  persistUserState();
}

function setNote(id, text) {
  if (text.trim()) state.user.notes[id] = text;
  else delete state.user.notes[id];
  persistUserState();
}

// =================================================================
// Carga de datos
// =================================================================
async function loadData() {
  try {
    const r = await fetch('data.json?t=' + Date.now());
    if (!r.ok) throw new Error('No se pudo cargar data.json');
    state.data = await r.json();
  } catch (e) {
    document.getElementById('results-list').innerHTML =
      `<div class="empty-state">ERROR CARGANDO DATOS<br><br>${e.message}</div>`;
    throw e;
  }
}

// =================================================================
// Helpers
// =================================================================
function formatPrecio(precio, moneda) {
  if (!precio) return null;
  const sym = moneda === 'USD' ? 'U$S' : '$';
  return `${sym} ${precio.toLocaleString('es-AR')}`;
}

function isNew(prop) {
  if (!prop.primera_vez_visto) return false;
  const first = new Date(prop.primera_vez_visto + 'Z');
  const now = new Date();
  const hours = (now - first) / (1000 * 60 * 60);
  return hours <= 48;
}

function getMarkerCategory(prop) {
  if (isDiscarded(prop.id)) return 'discarded';
  if (isSaved(prop.id)) return 'saved';
  if (isNew(prop)) return 'new';
  if (prop.score >= (state.data.umbral_interes || 40)) return 'priority';
  return 'regular';
}

// =================================================================
// Filtros UI
// =================================================================
function buildFilterChips() {
  const zonaContainer = document.getElementById('filter-zona');
  const portalContainer = document.getElementById('filter-portal');

  const zonas = state.data.zonas.map(z => z.nombre);
  zonaContainer.innerHTML = '';
  zonas.forEach(z => {
    const btn = document.createElement('button');
    btn.className = 'chip';
    btn.textContent = z.toUpperCase();
    btn.dataset.value = z;
    btn.onclick = () => {
      if (state.filters.zonas.has(z)) state.filters.zonas.delete(z);
      else state.filters.zonas.add(z);
      btn.classList.toggle('active');
      render();
    };
    zonaContainer.appendChild(btn);
  });

  const portalesPresentes = new Set();
  state.data.propiedades.forEach(p => {
    if (p.portal) portalesPresentes.add(p.portal);
  });
  portalContainer.innerHTML = '';
  Array.from(portalesPresentes).sort().forEach(p => {
    const btn = document.createElement('button');
    btn.className = 'chip';
    btn.textContent = (PORTAL_LABELS[p] || p.replace('inmo:', '').replace(/_/g, ' ')).toUpperCase();
    btn.dataset.value = p;
    btn.onclick = () => {
      if (state.filters.portales.has(p)) state.filters.portales.delete(p);
      else state.filters.portales.add(p);
      btn.classList.toggle('active');
      render();
    };
    portalContainer.appendChild(btn);
  });
}

function buildMarketplaceLinks() {
  const container = document.getElementById('marketplace-links');
  container.innerHTML = '';
  (state.data.marketplace || []).forEach(mkt => {
    const a = document.createElement('a');
    a.className = 'mkt-link';
    a.href = mkt.url;
    a.target = '_blank';
    a.rel = 'noopener';
    a.innerHTML = `
      <span class="mkt-link__zone">${mkt.zona}</span>
      <span class="mkt-link__arrow">→</span>
    `;
    container.appendChild(a);
  });
}

function bindFilterEvents() {
  const score = document.getElementById('filter-score');
  const scoreVal = document.getElementById('filter-score-val');
  score.oninput = () => {
    state.filters.scoreMin = +score.value;
    scoreVal.textContent = score.value;
    render();
  };

  const sup = document.getElementById('filter-sup');
  const supVal = document.getElementById('filter-sup-val');
  sup.oninput = () => {
    state.filters.supMin = +sup.value;
    supVal.textContent = sup.value;
    render();
  };

  document.getElementById('filter-prioritarias').onchange = (e) => {
    state.filters.soloPrioritarias = e.target.checked;
    render();
  };
  document.getElementById('filter-nuevas').onchange = (e) => {
    state.filters.soloNuevas = e.target.checked;
    render();
  };
  document.getElementById('filter-ocultar-descartadas').onchange = (e) => {
    state.filters.ocultarDescartadas = e.target.checked;
    render();
  };

  document.getElementById('sort-by').onchange = (e) => {
    state.sortBy = e.target.value;
    render();
  };

  document.getElementById('btn-reset').onclick = () => {
    state.filters = {
      zonas: new Set(), portales: new Set(),
      scoreMin: 0, supMin: 0,
      soloPrioritarias: false, soloNuevas: false,
      ocultarDescartadas: true,
    };
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    score.value = 0; scoreVal.textContent = '0';
    sup.value = 0; supVal.textContent = '0';
    document.getElementById('filter-prioritarias').checked = false;
    document.getElementById('filter-nuevas').checked = false;
    document.getElementById('filter-ocultar-descartadas').checked = true;
    render();
  };
}

// =================================================================
// Filtro y orden
// =================================================================
function applyFilters() {
  const f = state.filters;
  const umbral = state.data.umbral_interes || 40;
  return state.data.propiedades.filter(p => {
    if (f.ocultarDescartadas && isDiscarded(p.id)) return false;
    if (f.zonas.size > 0 && !f.zonas.has(p.zona)) return false;
    if (f.portales.size > 0 && !f.portales.has(p.portal)) return false;
    if (f.scoreMin > 0 && (p.score || 0) < f.scoreMin) return false;
    if (f.supMin > 0 && (p.superficie_m2 || 0) < f.supMin) return false;
    if (f.soloPrioritarias && (p.score || 0) < umbral) return false;
    if (f.soloNuevas && !isNew(p)) return false;
    return true;
  });
}

function applySort(props) {
  const sorted = [...props];
  switch (state.sortBy) {
    case 'score':
      sorted.sort((a, b) => (b.score || 0) - (a.score || 0));
      break;
    case 'reciente':
      sorted.sort((a, b) =>
        new Date(b.primera_vez_visto || 0) - new Date(a.primera_vez_visto || 0));
      break;
    case 'precio_asc':
      sorted.sort((a, b) => (a.precio || Infinity) - (b.precio || Infinity));
      break;
    case 'precio_desc':
      sorted.sort((a, b) => (b.precio || 0) - (a.precio || 0));
      break;
    case 'superficie':
      sorted.sort((a, b) => (b.superficie_m2 || 0) - (a.superficie_m2 || 0));
      break;
  }
  return sorted;
}

// =================================================================
// Mapa
// =================================================================
function initMap() {
  const center = [-31.72, -60.61];
  state.map = L.map('map', {
    zoomControl: true,
    attributionControl: true,
  }).setView(center, 9);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 19,
  }).addTo(state.map);

  state.cluster = L.markerClusterGroup({
    maxClusterRadius: 40,
    showCoverageOnHover: false,
  });
  state.map.addLayer(state.cluster);
}

function buildMarker(prop) {
  const cat = getMarkerCategory(prop);
  const html = `<div class="lp-marker lp-marker--${cat}">${Math.round(prop.score || 0)}</div>`;
  const icon = L.divIcon({
    html, className: '', iconSize: [28, 28], iconAnchor: [14, 14],
  });
  const marker = L.marker([prop.lat, prop.lon], { icon });
  marker.bindPopup(`
    <div style="min-width:180px">
      <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#888;letter-spacing:0.15em;margin-bottom:4px">
        ${prop.zona.toUpperCase()} · ${(PORTAL_LABELS[prop.portal] || prop.portal).toUpperCase()}
      </div>
      <div style="font-weight:600;margin-bottom:6px;line-height:1.3">${prop.titulo || '(sin título)'}</div>
      <div style="font-family:'Bebas Neue';font-size:18px;color:#ffd400">
        ${formatPrecio(prop.precio, prop.moneda) || 'Consultar'}
      </div>
      <div style="font-size:11px;color:#888;margin-top:4px">
        ${prop.superficie_m2 ? prop.superficie_m2 + ' m²' : '—'}
      </div>
      <a href="${prop.url}" target="_blank" rel="noopener" style="display:inline-block;margin-top:8px;padding:4px 10px;background:#ffd400;color:#000;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.15em;text-decoration:none;font-weight:700">
        VER AVISO ↗
      </a>
    </div>
  `);
  marker.on('click', () => {
    // En el mapa abrimos popup primero (default), no drawer
  });
  return marker;
}

function renderMap(props) {
  state.cluster.clearLayers();
  state.markers.clear();
  props.forEach(p => {
    if (p.lat == null || p.lon == null) return;
    const m = buildMarker(p);
    state.markers.set(p.id, m);
    state.cluster.addLayer(m);
  });
}

// =================================================================
// Lista de resultados
// =================================================================
function buildResultCard(prop) {
  const card = document.createElement('div');
  const cat = getMarkerCategory(prop);
  const classes = ['result-card'];
  if (cat === 'new') classes.push('result-card--new');
  else if (cat === 'priority') classes.push('result-card--priority');
  else if (cat === 'saved') classes.push('result-card--saved');
  card.className = classes.join(' ');

  // Click en la tarjeta abre el aviso directamente
  card.onclick = (e) => {
    // Si clickearon el botón "info", no hacer nada (el botón maneja su propio evento)
    if (e.target.closest('.rc-info-btn')) return;
    if (prop.url) window.open(prop.url, '_blank', 'noopener');
  };
  card.style.cursor = 'pointer';

  const score = prop.score || 0;
  const umbral = state.data.umbral_interes || 40;
  let scoreClass = '';
  if (score >= umbral + 20) scoreClass = 'rc-score--high';
  else if (score >= umbral) scoreClass = 'rc-score--mid';

  const portal = (PORTAL_LABELS[prop.portal] || prop.portal.replace('inmo:', '')).toUpperCase();

  card.innerHTML = `
    ${isNew(prop) ? '<span class="rc-tag-new">NUEVA</span>' : ''}
    <button class="rc-info-btn" title="Ver detalle">i</button>
    <div class="rc-row">
      <span class="rc-zone">${prop.zona}</span>
      <span class="rc-portal">${portal}</span>
    </div>
    <div class="rc-title">${prop.titulo || '(sin título)'}</div>
    <div class="rc-bottom">
      <div class="${prop.precio ? 'rc-price' : 'rc-price rc-price--null'}">
        ${formatPrecio(prop.precio, prop.moneda) || 'Consultar'}
      </div>
      <div class="rc-meta">
        ${prop.superficie_m2 ? `<span class="rc-sup">${prop.superficie_m2} m²</span>` : ''}
        <span class="rc-score ${scoreClass}">${score}</span>
      </div>
    </div>
  `;

  // Botón "i" abre el drawer de detalle
  const infoBtn = card.querySelector('.rc-info-btn');
  if (infoBtn) {
    infoBtn.onclick = (e) => {
      e.stopPropagation();
      openDrawer(prop);
    };
  }

  return card;
}

function renderList(props) {
  const container = document.getElementById('results-list');
  container.innerHTML = '';
  if (props.length === 0) {
    container.innerHTML = '<div class="empty-state">SIN RESULTADOS<br><br>Probá ajustar los filtros</div>';
    return;
  }
  props.forEach(p => container.appendChild(buildResultCard(p)));
}

// =================================================================
// Drawer (detalle)
// =================================================================
function openDrawer(prop) {
  const drawer = document.getElementById('drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  const content = document.getElementById('drawer-content');

  const score = prop.score || 0;
  const umbral = state.data.umbral_interes || 40;
  const isProp = score >= umbral;
  const portal = (PORTAL_LABELS[prop.portal] || prop.portal.replace('inmo:', '')).toUpperCase();

  const criteriosHtml = (prop.criterios_match || [])
    .map(c => `<span class="criterio-tag">${c.replace(/_/g, ' ')}</span>`)
    .join('');

  content.innerHTML = `
    <button class="drawer__close" id="drawer-close">×</button>
    <div class="drawer__zone">${prop.zona.toUpperCase()} · ${portal}</div>
    <h2 class="drawer__title">${prop.titulo || '(sin título)'}</h2>

    ${prop.direccion ? `<div class="drawer__address">${prop.direccion}</div>` : ''}

    <div class="drawer__stats">
      <div class="drawer__stat">
        <div class="drawer__stat-label">PRECIO</div>
        <div class="drawer__stat-value">${formatPrecio(prop.precio, prop.moneda) || '—'}</div>
      </div>
      <div class="drawer__stat">
        <div class="drawer__stat-label">SUPERFICIE</div>
        <div class="drawer__stat-value">${prop.superficie_m2 ? prop.superficie_m2 + ' m²' : '—'}</div>
      </div>
      <div class="drawer__stat">
        <div class="drawer__stat-label">SCORE</div>
        <div class="drawer__stat-value ${isProp ? 'drawer__stat-value--score-high' : ''}">${score}</div>
      </div>
    </div>

    ${criteriosHtml ? `
      <div class="drawer__criterios">
        <div class="drawer__criterios-title">CRITERIOS QUE MATCHEAN</div>
        ${criteriosHtml}
      </div>
    ` : ''}

    ${prop.descripcion ? `<div class="drawer__desc">${prop.descripcion}</div>` : ''}

    <div class="drawer__actions">
      <a href="${prop.url}" target="_blank" rel="noopener" class="drawer__btn drawer__btn--primary">
        VER EN ${portal} ↗
      </a>
      <button class="drawer__btn ${isSaved(prop.id) ? 'drawer__btn--saved' : ''}" id="btn-save">
        ${isSaved(prop.id) ? '★ DE INTERÉS' : '☆ MARCAR INTERÉS'}
      </button>
    </div>

    <div class="drawer__actions" style="grid-template-columns: 1fr">
      <button class="drawer__btn drawer__btn--discard" id="btn-discard">
        ${isDiscarded(prop.id) ? 'RESTAURAR' : 'DESCARTAR'}
      </button>
    </div>

    <div class="drawer__criterios-title" style="margin-top: 18px">NOTAS PERSONALES</div>
    <textarea class="drawer__notes" id="drawer-notes" placeholder="Tus apuntes sobre este local...">${getNote(prop.id)}</textarea>
  `;

  document.getElementById('drawer-close').onclick = closeDrawer;
  document.getElementById('btn-save').onclick = () => {
    toggleSaved(prop.id);
    openDrawer(prop);
    render();
  };
  document.getElementById('btn-discard').onclick = () => {
    toggleDiscarded(prop.id);
    closeDrawer();
    render();
  };
  document.getElementById('drawer-notes').oninput = (e) => {
    setNote(prop.id, e.target.value);
  };

  drawer.classList.add('open');
  backdrop.classList.add('open');
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawer-backdrop').classList.remove('open');
}

// =================================================================
// Render principal
// =================================================================
function updateMeta() {
  const fecha = new Date(state.data.actualizado);
  const fechaStr = fecha.toLocaleString('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
  document.getElementById('meta-fecha').textContent = fechaStr;
  document.getElementById('meta-total').textContent = state.data.propiedades.length;
  document.getElementById('meta-nuevas').textContent =
    state.data.propiedades.filter(p => isNew(p)).length;
}

function render() {
  const filtered = applyFilters();
  const sorted = applySort(filtered);

  document.getElementById('visible-count').textContent = sorted.length;
  document.getElementById('total-count').textContent = state.data.propiedades.length;

  renderMap(sorted);
  renderList(sorted);
}

// =================================================================
// Bootstrap
// =================================================================
async function bootstrap() {
  await loadData();
  updateMeta();
  initMap();
  buildFilterChips();
  buildMarketplaceLinks();
  bindFilterEvents();
  render();

  document.getElementById('drawer-backdrop').onclick = closeDrawer;
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeDrawer();
  });
}

bootstrap();

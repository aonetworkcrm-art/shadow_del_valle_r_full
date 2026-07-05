// 🌍 Shadow Del Valle R — Oráculo Sísmico API v2.0 (MULTIFUENTE + PAGER + PROPAGACIÓN)
// GET /api/oraculo              → Estado del oráculo
// GET /api/oraculo?action=live  → Datos en vivo: USGS + EMSC + NOAA + GDACS + PAGER + Propagación
//
// Fuentes:
//   - USGS Earthquake Hazards Program (RD, Venezuela, Caribe, Global)
//   - USGS PAGER (daños, víctimas, impacto económico)
//   - EMSC European-Mediterranean Seismological Centre
//   - NOAA/NWS Tsunami Alerts
//   - GDACS Global Disaster Alert System (UN/EC)
//   - Análisis de Propagación de Ondas Sísmicas

const USER_AGENT = 'ShadowDelValleR-Oraculo/1.0 (shadowdelvalle.com)';

// ─── Configuración Regional USGS ───
const USGS_REGION_QUERIES = {
  'rd': {
    name: 'República Dominicana',
    emoji: '🇩🇴',
    url: 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=2.5&minlatitude=17.0&maxlatitude=20.5&minlongitude=-72.0&maxlongitude=-68.0&orderby=magnitude&limit=20'
  },
  'venezuela': {
    name: 'Venezuela',
    emoji: '🇻🇪',
    url: 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=2.5&minlatitude=0.0&maxlatitude=12.5&minlongitude=-73.0&maxlongitude=-59.0&orderby=magnitude&limit=20'
  },
  'caribe': {
    name: 'Caribe',
    emoji: '🌊',
    url: 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=3.0&minlatitude=10.0&maxlatitude=25.0&minlongitude=-85.0&maxlongitude=-60.0&orderby=magnitude&limit=20'
  },
  'global': {
    name: 'Global Significativos',
    emoji: '🌍',
    url: 'https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/2.5_day.geojson'
  }
};

// ─── URLs de APIs adicionales ───
const API_SOURCES = {
  emsc: {
    name: 'EMSC (EU-Med)',
    emoji: '🇪🇺',
    url: 'https://www.seismicportal.eu/fdsnws/event/1/query?format=geojson&minmagnitude=3.0&orderby=magnitude&limit=15'
  },
  noaa_tsunami: {
    name: 'NOAA/NWS Tsunami',
    emoji: '🌊',
    url: 'https://api.weather.gov/alerts/active?event=Tsunami&limit=10',
    headers: { 'Accept': 'application/geo+json' }
  },
  gdacs: {
    name: 'GDACS (UN/EC)',
    emoji: '🆘',
    url: 'https://www.gdacs.org/xml/rss.xml'
  }
};

// ─── Helpers ───
async function fetchJSON(url, timeout = 10000, extraHeaders = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const resp = await fetch(url, {
      signal: controller.signal,
      headers: { 'User-Agent': USER_AGENT, ...extraHeaders }
    });
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

async function fetchText(url, timeout = 10000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const resp = await fetch(url, {
      signal: controller.signal,
      headers: { 'User-Agent': USER_AGENT }
    });
    if (!resp.ok) return null;
    return await resp.text();
  } catch (e) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

// Simple RSS XML parser (no dependencies)
function parseRSSXML(xmlText) {
  if (!xmlText || typeof xmlText !== 'string') return [];
  const items = [];
  // Extract <item>...</item> blocks
  const itemRegex = /<item[^>]*>([\s\S]*?)<\/item\s*>/gi;
  let match;
  while ((match = itemRegex.exec(xmlText)) !== null) {
    const itemBlock = match[1];
    const title = (itemBlock.match(/<title[^>]*><!\[CDATA\[([\s\S]*?)\]\]><\/title\s*>/) ||
                   itemBlock.match(/<title[^>]*>([\s\S]*?)<\/title\s*>/) || [])[1] || '';
    const link = (itemBlock.match(/<link[^>]*>([\s\S]*?)<\/link\s*>/) || [])[1] || '';
    const description = (itemBlock.match(/<description[^>]*><!\[CDATA\[([\s\S]*?)\]\]><\/description\s*>/) ||
                         itemBlock.match(/<description[^>]*>([\s\S]*?)<\/description\s*>/) || [])[1] || '';
    const pubDate = (itemBlock.match(/<pubDate[^>]*>([\s\S]*?)<\/pubDate\s*>/) || [])[1] || '';
    items.push({ title: title.trim(), link: link.trim(), description: description.trim(), pubDate: pubDate.trim() });
  }
  return items;
}

function calcularTiempoHace(timestamp) {
  const diff = Date.now() - (typeof timestamp === 'string' ? new Date(timestamp).getTime() : timestamp);
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'ahora';
  if (mins < 60) return `hace ${mins} min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `hace ${hrs}h ${mins % 60}m`;
  const days = Math.floor(hrs / 24);
  return `hace ${days}d`;
}

// ─── PAGER Data Fetcher ───
async function fetchPager(evento) {
  if (!evento.detalle_url || evento.magnitud < 4.5) return null;
  const data = await fetchJSON(evento.detalle_url, 8000);
  if (!data) return null;

  try {
    const products = data.properties?.products || {};
    for (const key of ['losspager', 'pager']) {
      if (products[key] && products[key].length > 0) {
        const p = products[key][0].properties || {};
        const fatMin = parseInt(p['fat-min']) || 0;
        const fatMax = parseInt(p['fat-max']) || 0;
        const injMin = parseInt(p['inj-min']) || 0;
        const injMax = parseInt(p['inj-max']) || 0;
        const lossMin = parseFloat(p['loss-min']) || 0;
        const lossMax = parseFloat(p['loss-max']) || 0;

        return {
          alertlevel: p.alertlevel || '',
          fatalities_min: fatMin,
          fatalities_max: fatMax,
          fatalities_promedio: Math.round((fatMin + fatMax) / 2),
          injuries_min: injMin,
          injuries_max: injMax,
          injuries_promedio: Math.round((injMin + injMax) / 2),
          damage_min_usd: lossMin,
          damage_max_usd: lossMax,
          damage_millions: Math.round((lossMin + lossMax) / 2000000 * 100) / 100,
          maxmmi: parseFloat(p.maxmmi) || null,
          alertscore: parseInt(p.alertscore) || null
        };
      }
    }
  } catch (e) { /* ignore */ }
  return null;
}

// ─── Haversine (cliente) ───
function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dlat = (lat2 - lat1) * Math.PI / 180;
  const dlon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dlat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dlon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function bearing(lat1, lon1, lat2, lon2) {
  const dlon = (lon2 - lon1) * Math.PI / 180;
  const lat1r = lat1 * Math.PI / 180;
  const lat2r = lat2 * Math.PI / 180;
  const x = Math.sin(dlon) * Math.cos(lat2r);
  const y = Math.cos(lat1r) * Math.sin(lat2r) - Math.sin(lat1r) * Math.cos(lat2r) * Math.cos(dlon);
  return (Math.atan2(x, y) * 180 / Math.PI + 360) % 360;
}

function bearingName(deg) {
  const dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  return dirs[Math.round(deg / 22.5) % 16];
}

// ─── Propagation Analysis ───
function analyzePropagation(eventos) {
  if (!eventos || eventos.length < 2) return null;

  const significantes = eventos.filter(e => e.magnitud >= 3.0)
    .sort((a, b) => new Date(a.tiempo) - new Date(b.tiempo));

  if (significantes.length < 2) return null;

  // Detect clusters
  const clusters = [];
  const usados = new Set();

  for (let i = 0; i < significantes.length; i++) {
    if (usados.has(i)) continue;
    const cluster = {
      eventos: [significantes[i]],
      magnitud_maxima: significantes[i].magnitud,
      centro_lat: significantes[i].lat,
      centro_lon: significantes[i].lon
    };
    usados.add(i);

    for (let j = i + 1; j < significantes.length; j++) {
      if (usados.has(j)) continue;
      const dist = haversineKm(significantes[i].lat, significantes[i].lon, significantes[j].lat, significantes[j].lon);
      const diffHoras = Math.abs(new Date(significantes[j].tiempo) - new Date(significantes[i].tiempo)) / 3600000;
      if (dist <= 200 && diffHoras <= 12) {
        cluster.eventos.push(significantes[j]);
        cluster.magnitud_maxima = Math.max(cluster.magnitud_maxima, significantes[j].magnitud);
        usados.add(j);
      }
    }

    if (cluster.eventos.length > 1) {
      const lats = cluster.eventos.map(e => e.lat);
      const lons = cluster.eventos.map(e => e.lon);
      cluster.centro_lat = lats.reduce((a, b) => a + b, 0) / lats.length;
      cluster.centro_lon = lons.reduce((a, b) => a + b, 0) / lons.length;
      cluster.tipo = cluster.eventos.length >= 3 ? 'swarm' : 'doble';
      clusters.push(cluster);
    }
  }

  // Calculate vectors
  const vectores = [];
  for (const cluster of clusters) {
    for (let i = 1; i < cluster.eventos.length; i++) {
      const a = cluster.eventos[i - 1];
      const b = cluster.eventos[i];
      const dist = haversineKm(a.lat, a.lon, b.lat, b.lon);
      if (dist < 1) continue;
      const bear = bearing(a.lat, a.lon, b.lat, b.lon);
      const diffHoras = Math.abs(new Date(b.tiempo) - new Date(a.tiempo)) / 3600000;
      vectores.push({
        desde: { lat: a.lat, lon: a.lon, lugar: a.lugar },
        hasta: { lat: b.lat, lon: b.lon, lugar: b.lugar },
        distancia_km: Math.round(dist * 10) / 10,
        direccion_grados: Math.round(bear * 10) / 10,
        direccion_nombre: bearingName(bear),
        delta_magnitud: Math.round((b.magnitud - a.magnitud) * 10) / 10,
        duracion_horas: Math.round(diffHoras * 100) / 100,
        magnitud_desde: a.magnitud,
        magnitud_hasta: b.magnitud
      });
    }
  }

  // General direction
  let direccion_general = { activa: false, descripcion: 'Sin vectores de movimiento' };
  if (vectores.length > 0) {
    const x = vectores.reduce((s, v) => s + Math.sin(v.direccion_grados * Math.PI / 180), 0) / vectores.length;
    const y = vectores.reduce((s, v) => s + Math.cos(v.direccion_grados * Math.PI / 180), 0) / vectores.length;
    const angulo = (Math.atan2(x, y) * 180 / Math.PI + 360) % 360;
    const distanciaTotal = vectores.reduce((s, v) => s + v.distancia_km, 0);
    const deltaProm = vectores.reduce((s, v) => s + v.delta_magnitud, 0) / vectores.length;

    let tendencia = 'ESTABLE ➡️';
    if (deltaProm > 0.3) tendencia = 'AUMENTANDO ⬆️';
    else if (deltaProm < -0.3) tendencia = 'DISMINUYENDO ⬇️';

    direccion_general = {
      activa: true,
      direccion_promedio: Math.round(angulo * 10) / 10,
      direccion_nombre: bearingName(angulo),
      distancia_total_km: Math.round(distanciaTotal * 10) / 10,
      delta_magnitud_promedio: Math.round(deltaProm * 100) / 100,
      tendencia_magnitud: tendencia,
      total_vectores_analizados: vectores.length,
      descripcion: `Propagación hacia el ${bearingName(angulo)} (${Math.round(distanciaTotal)} km en ${vectores.length} movimiento(s))`
    };
  }

  // Prediction
  let prediccion = null;
  if (vectores.length >= 1) {
    const ultimos = vectores.slice(-2);
    const dirProm = ultimos.reduce((s, v) => s + v.direccion_grados, 0) / ultimos.length;
    const distProm = ultimos.reduce((s, v) => s + v.distancia_km, 0) / ultimos.length;
    const tiempoProm = ultimos.reduce((s, v) => s + v.duracion_horas, 0) / ultimos.length;
    const ultimo = significantes[significantes.length - 1];

    const br = dirProm * Math.PI / 180;
    const R = 6371;
    const dr = distProm / R;
    const latPred = Math.asin(
      Math.sin(ultimo.lat * Math.PI / 180) * Math.cos(dr) +
      Math.cos(ultimo.lat * Math.PI / 180) * Math.sin(dr) * Math.cos(br)
    ) * 180 / Math.PI;
    const lonPred = (ultimo.lon * Math.PI / 180 + Math.atan2(
      Math.sin(br) * Math.sin(dr) * Math.cos(ultimo.lat * Math.PI / 180),
      Math.cos(dr) - Math.sin(ultimo.lat * Math.PI / 180) * Math.sin(latPred * Math.PI / 180)
    )) * 180 / Math.PI;

    prediccion = {
      lat_predicho: Math.round(latPred * 10000) / 10000,
      lon_predicho: Math.round(lonPred * 10000) / 10000,
      distancia_estimada_km: Math.round(distProm * 10) / 10,
      direccion: bearingName(dirProm),
      direccion_grados: Math.round(dirProm * 10) / 10,
      ventana_horas: Math.round(tiempoProm * 10) / 10,
      confianza: vectores.length >= 2 ? 'ALTA' : 'MEDIA',
      descripcion: `Próximo evento probable: ~${Math.round(distProm)} km al ${bearingName(dirProm)} desde ${(ultimo.lugar || 'último evento').substring(0, 30)}`
    };
  }

  return {
    total_eventos_analizados: significantes.length,
    total_clusters: clusters.length,
    total_vectores: vectores.length,
    clusters: clusters.slice(0, 3).map(c => ({
      ...c,
      eventos: c.eventos.map(e => ({ magnitud: e.magnitud, lugar: (e.lugar || '').substring(0, 30), lat: e.lat, lon: e.lon }))
    })),
    vectores: vectores.slice(0, 5),
    direccion_general,
    prediccion
  };
}

function parseEarthquakeEvents(data) {
  if (!data || !data.features) return [];
  return data.features.map(f => {
    const p = f.properties || {};
    const g = f.geometry || {};
    const coords = g.coordinates || [0, 0, 0];
    const mag = p.mag || 0;
    const time = p.time || Date.now();

    let severidad, emoji;
    if (mag >= 7.0) { severidad = 'CRÍTICO'; emoji = '🔴🔴🔴'; }
    else if (mag >= 6.0) { severidad = 'GRAVE'; emoji = '🔴🔴'; }
    else if (mag >= 5.0) { severidad = 'ALERTA'; emoji = '🟡🟡'; }
    else if (mag >= 4.0) { severidad = 'MODERADO'; emoji = '🟡'; }
    else if (mag >= 3.0) { severidad = 'LEVE'; emoji = '🔵'; }
    else { severidad = 'MENOR'; emoji = '⚪'; }

    return {
      id: f.id,
      magnitud: Math.round(mag * 10) / 10,
      lugar: p.place || 'Desconocido',
      lat: Math.round(coords[1] * 10000) / 10000,
      lon: Math.round(coords[0] * 10000) / 10000,
      profundidad_km: Math.round(coords[2] * 10) / 10,
      tiempo: new Date(time).toISOString(),
      tiempo_hace: calcularTiempoHace(time),
      severidad, emoji,
      tsunami: !!p.tsunami,
      sig: p.sig || 0,
      detalle_url: p.detail || '',
      fuente: 'USGS'
    };
  }).sort((a, b) => b.magnitud - a.magnitud);
}

function procesarRegionUSGS(data, regionKey) {
  const eventos = parseEarthquakeEvents(data);
  const limite = 24 * 60 * 60 * 1000;
  const recientes = eventos.filter(e => Date.now() - new Date(e.tiempo).getTime() < limite);
  return {
    region: regionKey,
    nombre: USGS_REGION_QUERIES[regionKey]?.nombre || regionKey,
    emoji: USGS_REGION_QUERIES[regionKey]?.emoji || '🌍',
    total: recientes.length,
    ultimo: recientes[0] || null,
    eventos: recientes.slice(0, 15),
    magnitud_maxima: recientes.length > 0 ? Math.max(...recientes.map(e => e.magnitud)) : 0,
    fuente: 'USGS'
  };
}

function parseEMSC(data) {
  if (!data || !data.features) return [];
  
  // Severidad humana mapping
  const severidadHumanaMap = {
    'CRÍTICO': 'Crítico', 'GRAVE': 'Grave', 'ALERTA': 'Alerta',
    'MODERADO': 'Moderado', 'LEVE': 'Leve', 'MENOR': 'Menor'
  };
  
  return data.features.map(f => {
    const p = f.properties || {};
    const mag = Math.round((p.mag || 0) * 10) / 10;
    const depth = Math.round(parseFloat(p.depth) || 0);
    const lugar = p.flynn_region || p.region || 'Desconocido';
    
    // Severidad y emoji mejorados
    let severidad, emoji, color;
    if (mag >= 7.0) { severidad = 'CRÍTICO'; emoji = '🔴🔴🔴'; color = '#d32f2f'; }
    else if (mag >= 6.0) { severidad = 'GRAVE'; emoji = '🔴🔴'; color = '#ef5350'; }
    else if (mag >= 5.0) { severidad = 'ALERTA'; emoji = '🟡🟡'; color = '#ff9800'; }
    else if (mag >= 4.0) { severidad = 'MODERADO'; emoji = '🟡'; color = '#ffd54f'; }
    else if (mag >= 3.0) { severidad = 'LEVE'; emoji = '🔵'; color = '#26c6da'; }
    else { severidad = 'MENOR'; emoji = '⚪'; color = '#6b6b88'; }
    
    // Descripción humana: "Terremoto · magnitud 5.7 · 51 km de profundidad · en Región"
    let descripcionHumana = 'Terremoto';
    const partes = [];
    if (mag > 0) partes.push('magnitud ' + mag.toFixed(1));
    if (depth > 0) partes.push(depth + ' km de profundidad');
    if (lugar && lugar !== 'Desconocido') partes.push('en ' + lugar.substring(0, 40));
    if (partes.length > 0) descripcionHumana = partes.join(' · ');
    
    // Fecha humanizada (reusa humanizarFecha con ISO string)
    const fechaHumana = p.time ? humanizarFecha(new Date(p.time).toISOString()) : '';
    
    return {
      id: `${f.id || 'emsc'}-${Date.now()}`,
      magnitud: mag,
      lugar: lugar,
      lat: Math.round((parseFloat(p.lat) || 0) * 10000) / 10000,
      lon: Math.round((parseFloat(p.lon) || 0) * 10000) / 10000,
      profundidad_km: depth,
      tiempo: tiempo.toISOString(),
      tiempo_hace: calcularTiempoHace(tiempo.getTime()),
      severidad: severidad,
      severidad_humana: severidadHumanaMap[severidad] || severidad,
      emoji: emoji,
      color_severidad: color,
      descripcion_humana: descripcionHumana,
      fecha_humana: fechaHumana,
      fuente: 'EMSC'
    };
  }).sort((a, b) => b.magnitud - a.magnitud).slice(0, 10);
}


function parseNOAATsunami(data) {
  if (!data || !data.features) return [];
  return data.features.map(f => {
    const p = f.properties || {};
    return {
      id: f.id || `noaa-${Date.now()}`,
      titulo: p.headline || 'Alerta de Tsunami',
      evento: p.event || 'Tsunami Warning',
      severidad: p.severity || 'Unknown',
      certeza: p.certainty || 'Unknown',
      urgencia: p.urgency || 'Unknown',
      area: (p.areaDesc || '').substring(0, 100),
      descripcion: (p.description || '').substring(0, 200),
      instrucciones: (p.instruction || '').substring(0, 200),
      tiempo: p.sent || new Date().toISOString(),
      estatus: p.status || 'Actual',
      emoji: (p.event || '').toLowerCase().includes('warning') ? '🔴🔴🔴' : '🌊',
      fuente: 'NOAA/NWS'
    };
  });
}

// ─── Humanizar fecha (de RSS a español) ───
function humanizarFecha(fechaStr) {
  if (!fechaStr) return '';
  try {
    var d = new Date(fechaStr);
    if (isNaN(d.getTime())) return fechaStr;
    var ahora = Date.now();
    var diff = ahora - d.getTime();
    var min = Math.floor(diff / 60000);
    var hr = Math.floor(diff / 3600000);
    var dias = Math.floor(diff / 86400000);
    var meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
    var fechaLocal = d.getDate() + ' ' + meses[d.getMonth()] + ' ' + d.getFullYear();
    if (min < 60) return 'hace ' + min + ' min · ' + fechaLocal;
    if (hr < 24) return 'hace ' + hr + 'h · ' + fechaLocal;
    if (dias < 7) return 'hace ' + dias + ' días · ' + fechaLocal;
    return fechaLocal;
  } catch(e) { return fechaStr; }
}

// ─── Humanizar título GDACS (de inglés a español legible) ───
function humanizarTituloGDACS(title) {
  if (!title) return 'Evento sin descripción';
  var mag = null, depth = null, location = '';
  // Extraer magnitud: "Magnitude 5.7M"
  var magMatch = title.match(/Magnitude\s+([\d.]+)\s*M/i);
  if (magMatch) mag = parseFloat(magMatch[1]);
  // Extraer profundidad: "Depth:50.92km" o "Depth:50.92"
  var depthMatch = title.match(/Depth[:\s]*([\d.]+)\s*km/i);
  if (depthMatch) depth = parseFloat(depthMatch[1]);
  // Extraer ubicación: texto después de "in "
  var locMatch = title.match(/\bin\s+(.+)$/i);
  if (locMatch) location = locMatch[1].replace(/\.$/, '').trim();
  // Limpiar nombre del evento
  var nombre = title
    .replace(/^(Red|Orange|Yellow|Green)\s+/i, '')
    .replace(/\s*\(Magnitude[^)]*\)/i, '')
    .replace(/\bin\s+.+$/, '')
    .replace(/\s*alert$/i, '')
    .replace(/\s*notification$/i, '')
    .trim();
  // Traducir tipo de evento al español
  var traducciones = {
    'earthquake': 'Terremoto', 'flood': 'Inundación', 'tropical cyclone': 'Ciclón tropical',
    'tsunami': 'Tsunami', 'volcano': 'Volcán', 'forest fire': 'Incendio forestal',
    'fire': 'Incendio', 'drought': 'Sequía', 'epidemic': 'Epidemia'
  };
  var nLower = nombre.toLowerCase();
  for (var eng in traducciones) {
    if (nLower.indexOf(eng) >= 0) {
      nombre = traducciones[eng];
      break;
    }
  }
  // Primera letra mayúscula
  nombre = nombre.charAt(0).toUpperCase() + nombre.slice(1);
  // Construir descripción humana
  var partes = [nombre];
  if (mag) partes.push('magnitud ' + mag.toFixed(1));
  if (depth) partes.push(depth.toFixed(0) + ' km de profundidad');
  if (location) partes.push('en ' + location);
  return partes.join(' · ');
}

function parseGDACS(items) {
  if (!items || !items.length) return [];
  
  const tipoMap = { 'EQ': 'Terremoto', 'TC': 'Ciclón tropical', 'FL': 'Inundación', 'TS': 'Tsunami', 'VO': 'Volcán', 'WF': 'Incendio forestal' };
  const emojiMap = { 'Red': '🔴🔴🔴', 'Orange': '🟡🟡', 'Yellow': '🟡', 'Green': '🟢' };
  const severidadHumana = { 'Red': 'Crítico', 'Orange': 'Moderado', 'Yellow': 'Leve', 'Green': 'Informativo' };
  
  return items.slice(0, 10).map((item, i) => {
    const title = (item.title || '');
    const desc = (item.description || '');
    
    // Detect event type from title
    let eventtype = 'Desastre';
    const t = title.toLowerCase();
    if (t.includes('earthquake') || t.includes('eq ')) eventtype = 'EQ';
    else if (t.includes('tsunami') || t.includes('ts ')) eventtype = 'TS';
    else if (t.includes('cyclone') || t.includes('tc ') || t.includes('hurac') || t.includes('tormenta')) eventtype = 'TC';
    else if (t.includes('flood') || t.includes('fl ')) eventtype = 'FL';
    else if (t.includes('volcano') || t.includes('vo ')) eventtype = 'VO';
    else if (t.includes('fire')) eventtype = 'WF';
    
    // Severity from title keywords
    let severity = 'Green';
    if (t.includes('red') || t.includes('critical') || t.includes('extreme')) severity = 'Red';
    else if (t.includes('orange') || t.includes('severe') || t.includes('major')) severity = 'Orange';
    else if (t.includes('yellow') || t.includes('moderate')) severity = 'Yellow';
    
    // Descripción humanizada
    var descripcionHumana = humanizarTituloGDACS(title);
    
    // Fecha humanizada
    var fechaHumana = humanizarFecha(item.pubDate || '');
    
    // País: extraer ubicación del título si no hay description
    var pais = (desc || '').substring(0, 50);
    if (!pais) {
      var locM = title.match(/\bin\s+(.+)$/i);
      if (locM) pais = locM[1].replace(/\.$/, '').trim().substring(0, 50);
    }
    
    return {
      id: `gdacs-rss-${i}`,
      tipo: eventtype,
      tipo_nombre: tipoMap[eventtype] || 'Desastre',
      nombre: (title || '').substring(0, 100),
      severidad: severity,
      severidad_humana: severidadHumana[severity] || severity,
      descripcion_humana: descripcionHumana,
      pais: pais,
      fecha_humana: fechaHumana,
      lat: 0, lon: 0,
      fecha: (item.pubDate || '').substring(0, 19),
      emoji: emojiMap[severity] || '⚪',
      fuente: 'GDACS (UN/EC)'
    };
  });
}

// ─── Handler principal ───
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'OPTIONS') return res.status(204).end();

  const url = new URL(req.url, 'http://localhost');
  const action = url.searchParams.get('action') || 'state';

  try {
    if (action === 'live') {
      const resultados = {};

      // 1. USGS Earthquakes (4 regiones en paralelo)
      const usgsEntries = Object.entries(USGS_REGION_QUERIES);
      await Promise.all(usgsEntries.map(async ([key, cfg]) => {
        const data = await fetchJSON(cfg.url);
        resultados[key] = procesarRegionUSGS(data, key);
      }));

      // Reunir todos los eventos USGS para PAGER y propagación
      const todosUSGS = [];
      Object.entries(resultados).forEach(([key, r]) => {
        if (r.eventos) {
          r.eventos.forEach(e => {
            todosUSGS.push({ ...e, region_key: key });
          });
        }
      });

      // 2. PAGER — Fetch damage data for significant events (M≥4.5) en paralelo
      const eventosParaPager = todosUSGS.filter(e => e.magnitud >= 4.5 && e.detalle_url).slice(0, 5);
      const pagerResults = await Promise.all(
        eventosParaPager.map(e => fetchPager(e).then(pager => ({ eventId: e.id, pager })))
      );
      const pagerMap = {};
      pagerResults.forEach(pr => { if (pr.pager) pagerMap[pr.eventId] = pr.pager; });

      // Asignar PAGER a eventos
      const eventosConPager = todosUSGS.filter(e => pagerMap[e.id]);
      resultados.pager = {
        nombre: 'USGS PAGER',
        emoji: '📊',
        fuente: 'USGS PAGER',
        total: eventosConPager.length,
        eventos: eventosConPager.map(e => ({
          ...e,
          pager: pagerMap[e.id]
        }))
      };

      // 3. Propagation Analysis
      const propagacion = analyzePropagation(todosUSGS);
      resultados.propagacion = propagacion ? {
        nombre: 'Análisis de Propagación',
        emoji: '🌀',
        fuente: 'Algoritmo de Propagación',
        ...propagacion
      } : null;

      // 4. EMSC
      const emscData = await fetchJSON(API_SOURCES.emsc.url);
      resultados.emsc = {
        nombre: 'EMSC (EU-Med)', emoji: '🇪🇺', fuente: 'EMSC',
        total: (emscData?.features || []).length,
        eventos: parseEMSC(emscData)
      };

      // 5. NOAA Tsunami
      const noaaData = await fetchJSON(API_SOURCES.noaa_tsunami.url, 10000, API_SOURCES.noaa_tsunami.headers);
      const tsunamiEvents = parseNOAATsunami(noaaData);
      resultados.tsunami = {
        nombre: 'NOAA/NWS Tsunami', emoji: '🌊', fuente: 'NOAA',
        total: tsunamiEvents.length,
        alertas: tsunamiEvents
      };

      // 6. GDACS (RSS XML)
      const gdacsRaw = await fetchText(API_SOURCES.gdacs.url);
      const gdacsItems = gdacsRaw ? parseRSSXML(gdacsRaw) : [];
      const gdacsEvents = parseGDACS(gdacsItems);
      resultados.gdacs = {
        nombre: 'GDACS (UN/EC)', emoji: '🆘', fuente: 'GDACS',
        total: gdacsEvents.length,
        alertas: gdacsEvents
      };

      // Estadísticas globales
      let totalEventos = 0;
      let maxMag = 0;
      let ultimoEvento = null;

      Object.values(resultados).forEach(r => {
        if (r && r.eventos) {
          totalEventos += r.eventos.length;
          r.eventos.forEach(e => { if (e.magnitud > maxMag) maxMag = e.magnitud; });
        }
        if (r && r.ultimo && (!ultimoEvento || new Date(r.ultimo.tiempo) > new Date(ultimoEvento.tiempo))) {
          ultimoEvento = r.ultimo;
        }
      });

      return res.status(200).json({
        success: true,
        timestamp: new Date().toISOString(),
        total_eventos: totalEventos,
        magnitud_maxima: Math.round(maxMag * 10) / 10,
        ultimo_evento: ultimoEvento,
        fuentes_activas: ['USGS', 'USGS PAGER', 'Propagación', 'EMSC', 'NOAA/NWS', 'GDACS'],
        regiones: resultados
      });
    }

    // ─── STATE ───
    return res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      message: 'Oráculo v2.0 Multifuente activo. Usa ?action=live para datos en vivo.',
      fuentes: ['USGS + PAGER', 'Propagación', 'EMSC', 'NOAA/NWS Tsunami', 'GDACS UN/EC']
    });

  } catch (error) {
    return res.status(500).json({ success: false, error: error.message });
  }
}

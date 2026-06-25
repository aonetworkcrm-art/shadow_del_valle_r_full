// Shadow Del Valle R — Analytics Tracker (Vercel Serverless)
// POST /api/track
// Body: { slug: "mi-post", type: "pageview"|"click", referrer?: string }

const FALLBACK_FILE = '/tmp/analytics_fallback.json';

function getFallbackData() {
  try {
    const fs = require('fs');
    if (fs.existsSync(FALLBACK_FILE)) {
      return JSON.parse(fs.readFileSync(FALLBACK_FILE, 'utf8'));
    }
  } catch(e) {}
  return { pv: {}, click: {}, totalPv: 0, totalClick: 0 };
}

function saveFallbackData(data) {
  try {
    const fs = require('fs');
    fs.writeFileSync(FALLBACK_FILE, JSON.stringify(data), 'utf8');
  } catch(e) {}
}

export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { slug = 'home', type = 'pageview', referrer = '' } = req.body;
    const today = new Date().toISOString().split('T')[0];

    // Intentar con KV si está disponible (Vercel KV)
    try {
      const { kv } = require('@vercel/kv');
      if (kv) {
        const key = type === 'pageview' ? `pv:${today}` : `click:${today}`;
        const slugKey = `${type}:slug:${today}:${slug}`;
        const totalKey = type === 'pageview' ? 'pv:total' : 'click:total';

        const pipeline = kv.pipeline();
        pipeline.hincrby(key, slug, 1);
        pipeline.hincrby(key, '_total', 1);
        pipeline.hincrby(slugKey, '_count', 1);
        pipeline.incr(totalKey);
        pipeline.hincrby(`hourly:${today}`, `${new Date().getHours()}`, 1);
        if (referrer) pipeline.hincrby(`ref:${today}`, referrer, 1);
        await pipeline.exec();

        return res.status(200).json({ ok: true, storage: 'kv' });
      }
    } catch(e) {
      // KV no disponible, continuar con fallback
    }

    // Fallback: registrar en memoria volátil
    const fallback = getFallbackData();
    if (type === 'pageview') {
      fallback.pv[slug] = (fallback.pv[slug] || 0) + 1;
      fallback.totalPv++;
    } else {
      fallback.click[slug] = (fallback.click[slug] || 0) + 1;
      fallback.totalClick++;
    }
    saveFallbackData(fallback);

    return res.status(200).json({ ok: true, storage: 'memory' });
  } catch (error) {
    console.error('Track error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

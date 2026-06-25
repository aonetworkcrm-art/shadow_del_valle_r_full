// Shadow Del Valle R — Analytics Stats (Vercel Serverless)
// GET /api/stats

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  try {
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

    // Intentar con KV
    try {
      const { kv } = require('@vercel/kv');
      if (kv) {
        const [totalViews, totalClicks, todayViewsRaw, todayClicksRaw, yesterdayRaw, hourlyRaw, refRaw] = await Promise.all([
          kv.get('pv:total'),
          kv.get('click:total'),
          kv.hgetall(`pv:${today}`),
          kv.hgetall(`click:${today}`),
          kv.hgetall(`pv:${yesterday}`),
          kv.hgetall(`hourly:${today}`),
          kv.hgetall(`ref:${today}`)
        ]);

        const todayViews = todayViewsRaw || {};
        const todayClicks = todayClicksRaw || {};
        const yesterdayViews = yesterdayRaw || {};
        const hourly = Array.from({ length: 24 }, (_, i) => ({
          hour: i,
          count: parseInt((hourlyRaw || {})[String(i)] || '0', 10)
        }));

        const referrers = Object.entries(refRaw || {})
          .map(([source, count]) => ({ source, count: parseInt(count, 10) }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10);

        const slugs = new Set();
        Object.keys(todayViews).forEach(k => { if (k !== '_total') slugs.add(k); });

        const pageStats = [];
        for (const slug of slugs) {
          const pv = parseInt(todayViews[slug] || '0', 10);
          const clickData = await kv.hgetall(`click:slug:${today}:${slug}`) || {};
          const clicks = parseInt(clickData._count || '0', 10);
          pageStats.push({
            slug,
            pageviews: pv,
            clicks,
            ctr: pv > 0 ? ((clicks / pv) * 100).toFixed(1) + '%' : '0%'
          });
        }
        pageStats.sort((a, b) => b.pageviews - a.pageviews);

        return res.status(200).json({
          today: {
            pageviews: parseInt(todayViews._total || '0', 10),
            clicks: parseInt(todayClicks._total || '0', 10),
            ctr: parseInt(todayViews._total || '0', 10) > 0 ? ((parseInt(todayClicks._total || '0', 10) / parseInt(todayViews._total || '0', 10)) * 100).toFixed(1) + '%' : '0%'
          },
          yesterday: { pageviews: parseInt(yesterdayViews._total || '0', 10) },
          allTime: { pageviews: parseInt(totalViews || '0', 10), clicks: parseInt(totalClicks || '0', 10) },
          pages: pageStats, hourly, referrers, date: today
        });
      }
    } catch(e) {}

    // Sin KV — datos vacíos
    return res.status(200).json({
      today: { pageviews: 0, clicks: 0, ctr: '0%' },
      yesterday: { pageviews: 0 },
      allTime: { pageviews: 0, clicks: 0 },
      pages: [], hourly: Array.from({ length: 24 }, (_, i) => ({ hour: i, count: 0 })),
      referrers: [], date: today,
      note: 'KV no configurado. Ejecuta: vercel kv create'
    });

  } catch (error) {
    return res.status(200).json({
      today: { pageviews: 0, clicks: 0, ctr: '0%' },
      yesterday: { pageviews: 0 },
      allTime: { pageviews: 0, clicks: 0 },
      pages: [], hourly: Array.from({ length: 24 }, (_, i) => ({ hour: i, count: 0 })),
      referrers: [], date: new Date().toISOString().split('T')[0],
      error: error.message
    });
  }
}

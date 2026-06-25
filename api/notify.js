// Shadow Del Valle R — Search Engine Notifier (Vercel Serverless)
// Endpoints: GET /api/notify?url=URL | ?action=all | ?action=verify

const INDEXNOW_KEY = 'c291a640b45f48eab74384a1a7f653d8';
const DOMAIN = 'shadow-del-valle-r.vercel.app';
const BING_INDEXNOW = 'https://www.bing.com/indexnow';
const SITEMAP_URL = `https://${DOMAIN}/sitemap.xml`;

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  const { url, action } = req.query;

  try {
    if (action === 'verify') {
      const keyUrl = `https://${DOMAIN}/${INDEXNOW_KEY}.txt`;
      const keyResp = await fetch(keyUrl);
      const keyContent = await keyResp.text();
      return res.status(200).json({
        domain: DOMAIN, key: INDEXNOW_KEY.substring(0, 8) + '...', keyUrl,
        keyAccessible: keyResp.ok && keyContent.trim() === INDEXNOW_KEY,
        sitemapUrl: SITEMAP_URL, status: 'configured'
      });
    }

    if (action === 'all' || url === 'all') {
      const sitemapResp = await fetch(SITEMAP_URL);
      const sitemapText = await sitemapResp.text();
      const urls = [...sitemapText.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1].trim());
      if (!urls.length) return res.status(200).json({ success: false, error: 'No URLs found in sitemap' });

      const indexnowResp = await fetch(BING_INDEXNOW, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host: DOMAIN, key: INDEXNOW_KEY, keyLocation: `https://${DOMAIN}/${INDEXNOW_KEY}.txt`, urlList: urls })
      });
      fetch(`https://www.google.com/ping?sitemap=${encodeURIComponent(SITEMAP_URL)}`).catch(() => {});

      return res.status(200).json({
        success: indexnowResp.ok, statusCode: indexnowResp.status,
        urlsSubmitted: urls.length, urls, googlePinged: true
      });
    }

    if (url) {
      const indexnowResp = await fetch(`${BING_INDEXNOW}?url=${encodeURIComponent(url)}&key=${INDEXNOW_KEY}`);
      fetch(`https://www.google.com/ping?sitemap=${encodeURIComponent(SITEMAP_URL)}`).catch(() => {});
      return res.status(200).json({
        success: indexnowResp.ok || indexnowResp.status === 200, statusCode: indexnowResp.status, url, googlePinged: true
      });
    }

    return res.status(200).json({
      domain: DOMAIN, keyConfigured: true, keyUrl: `https://${DOMAIN}/${INDEXNOW_KEY}.txt`, sitemapUrl: SITEMAP_URL,
      usage: { notifySingle: `GET /api/notify?url=https://${DOMAIN}/posts/your-post/`, notifyAll: 'GET /api/notify?action=all', verify: 'GET /api/notify?action=verify' }
    });

  } catch (error) {
    return res.status(500).json({ success: false, error: error.message });
  }
}

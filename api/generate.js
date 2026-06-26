// 🌑 Shadow Del Valle R — Generate & Deploy API
// POST /api/generate — Triggers GitHub Actions workflow
// Requires: GITHUB_PAT env var (Personal Access Token with repo scope)

const GITHUB_REPO = 'aonetworkcrm-art/shadow_del_valle_r_full';
const GITHUB_API = `https://api.github.com/repos/${GITHUB_REPO}/dispatches`;

export default async function handler(req, res) {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const token = process.env.GITHUB_PAT;
  if (!token) {
    return res.status(200).json({
      success: false,
      error: 'GITHUB_PAT not configured',
      offline: true,
      instructions: 'Ejecuta localmente: python control.py --all'
    });
  }

  try {
    const action = req.body?.action || 'all';
    const resp = await fetch(GITHUB_API, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'shadow-del-valle-r'
      },
      body: JSON.stringify({
        event_type: 'generate-posts',
        client_payload: {
          action: action,
          triggered_by: 'web-button',
          timestamp: new Date().toISOString()
        }
      })
    });

    if (resp.status === 204) {
      return res.status(200).json({
        success: true,
        message: 'Generación iniciada en GitHub Actions',
        runUrl: `https://github.com/${GITHUB_REPO}/actions`,
        note: 'El proceso toma ~2-3 minutos. Revisa el estado en GitHub Actions.'
      });
    }

    const errData = await resp.text();
    return res.status(200).json({
      success: false,
      error: `GitHub API error: ${resp.status}`,
      detail: errData,
      offline: true,
      instructions: 'Ejecuta localmente: python control.py --all'
    });

  } catch (error) {
    return res.status(200).json({
      success: false,
      error: error.message,
      offline: true,
      instructions: 'Ejecuta localmente: python control.py --all'
    });
  }
}

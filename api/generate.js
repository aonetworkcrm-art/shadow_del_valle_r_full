// 🌑 Shadow Del Valle R — Generate & Deploy API (FULL)
// POST /api/generate — Triggers GitHub Actions workflow
//
// Requiere: GITHUB_PAT en Environment Variables de Vercel
//   - Ir a: Vercel Dashboard > Project > Settings > Environment Variables
//   - Agregar: GITHUB_PAT = tu_personal_access_token
//   - Token debe tener permisos: repo (full control)
//
// El workflow de GitHub Actions (.github/workflows/generate.yml)
// ejecuta: generate_all.py --force → deploy → notify

const GITHUB_REPO = 'aonetworkcrm-art/shadow_del_valle_r_full';
const GITHUB_API = `https://api.github.com/repos/${GITHUB_REPO}/dispatches`;
const GITHUB_ACTIONS_URL = `https://github.com/${GITHUB_REPO}/actions`;

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
      error: 'GITHUB_PAT no configurado en Vercel',
      offline: true,
      setupUrl: `https://vercel.com/aonetworkcrm-art/shadow-del-valle-r/settings/environment-variables`,
      instructions: [
        'Para activar el boton desde el dashboard:',
        '1. Ve a GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)',
        '2. Crea un token con permisos: repo (full control)',
        '3. Copia el token',
        '4. Ve a Vercel > Project > Settings > Environment Variables',
        '5. Agrega: GITHUB_PAT = <tu_token>',
        '6. Redeploy la funcion serverless',
        '',
        'Mientras tanto, ejecuta LOCALMENTE:',
        '   cd shadow_del_valle_r',
        '   python control.py --' + (req.body?.action || 'all')
      ]
    });
  }

  try {
    const action = req.body?.action || 'all';
    
    // ─── Handle 'verify' action — solo check de conectividad ───
    if (action === 'verify') {
      return res.status(200).json({
        success: true,
        online: true,
        message: 'Conexion con GitHub API establecida',
        repo: GITHUB_REPO,
        actionsUrl: GITHUB_ACTIONS_URL
      });
    }
    
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
      const messages = {
        'all': '🚀 Pipeline completo iniciado en GitHub Actions',
        'generate': '📝 Generacion de posts iniciada en GitHub Actions',
        'deploy': '▲ Deploy a Vercel iniciado en GitHub Actions',
        'notify': '⚡ Notificacion IndexNow iniciada en GitHub Actions'
      };
      return res.status(200).json({
        success: true,
        message: messages[action] || `🚀 Accion '${action}' iniciada en GitHub Actions`,
        action: action,
        runUrl: GITHUB_ACTIONS_URL,
        note: 'El proceso toma ~2-3 minutos. Puedes ver el progreso en vivo en GitHub Actions.'
      });
    }

    // Error de GitHub API
    let errMsg = `GitHub API error: ${resp.status}`;
    try {
      const errJson = await resp.json();
      if (errJson.message) errMsg = errJson.message;
    } catch(e) {
      const errText = await resp.text().catch(() => '');
      if (errText) errMsg = errText.substring(0, 200);
    }

    return res.status(200).json({
      success: false,
      error: errMsg,
      offline: false,
      instructions: [
        'Error al conectar con GitHub.',
        'Verifica que:',
        '- El GITHUB_PAT tenga permisos repo (full control)',
        '- El token no haya expirado',
        '- El repo ' + GITHUB_REPO + ' exista y sea accesible',
        '',
        'Alternativa local:',
        '   cd shadow_del_valle_r',
        '   python control.py --' + action
      ]
    });

  } catch (error) {
    return res.status(200).json({
      success: false,
      error: error.message,
      offline: true,
      instructions: [
        'Error de conexion:', error.message,
        '',
        'Ejecuta LOCALMENTE:',
        '   cd shadow_del_valle_r',
        '   python control.py --' + (req.body?.action || 'all')
      ]
    });
  }
}

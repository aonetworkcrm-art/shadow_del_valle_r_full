# 📋 MANUAL DE OPERACIONES — Shadow Del Valle R

> Versión 1.0 — 25 Junio 2026

---

## 📌 RESUMEN DEL SISTEMA

- **Sitio:** https://shadow-del-valle-r.vercel.app
- **Posts:** 16 (CPC $85-$250, promedio $179)
- **Monetag:** ✅ Verificado — Zone 253508, quge5.com
- **Google Search Console:** ✅ Verificado
- **Hosting:** Vercel (gratis)
- **GitHub:** https://github.com/aonetworkcrm-art/shadow_del_valle_r_full

---

## 🎯 FLUJO DE TRABAJO DIARIO

### 🌅 Cada mañana (2 minutos)

```bash
# 1. Abre el acceso directo del escritorio (Shadow_Del_Valle_R.bat)
#    O ejecuta:
cd shadow_del_valle_r

# 2. Pipeline completo (genera hasta 6 posts + deploy + IndexNow)
python control.py --all
```

### 🔄 Rotación automática
Cada día se genera un subconjunto diferente de los 16 posts (rotación circular).
En 3 días se habrán generado todos. El sistema evita saturar a Google.

---

## 🚀 COMANDOS RÁPIDOS

### Control Center (recomendado)
```bash
python control.py              # Menú interactivo
python control.py --all         # Generar + Deploy + IndexNow
python control.py --generate    # Solo generar
python control.py --deploy      # Solo desplegar
python control.py --status      # Ver estado completo
```

### Generación de posts
```bash
python generate_all.py          # Hasta 6 posts del día (respeta límite)
python generate_all.py --force  # Los 16 posts (ignora límite)
```

### Agente autónomo (con OpenRouter)
```bash
python main_agent.py --once     # Una ronda con IA
python main_agent.py            # Loop infinito 24/7
python main_agent.py --status   # Estado del agente
```

---

## 📈 DÓNDE VER EL DINERO

### Monetag — Tus ingresos
```
https://monetag.com
→ Login → Dashboard → Statistics
→ Ver: impressions, clicks, CPM, earnings
```

### Google Search Console — Tráfico orgánico
```
https://search.google.com/search-console
→ Propiedad: shadow-del-valle-r.vercel.app
→ Sitemaps → verificar envío
→ Rendimiento → ver impresiones y clics de Google
```

### Analytics propio del sitio
```
https://shadow-del-valle-r.vercel.app/api/stats
```

---

## ⚙️ CONFIGURACIÓN IMPORTANTE

### Para activar el botón "Generar y Desplegar" desde el navegador

1. **GITHUB_PAT** en Vercel:
   → https://vercel.com/tnt5/shadow-del-valle-r/settings/environment-variables
   → Name: `GITHUB_PAT`, Value: (token de GitHub con scope `repo`)

2. **VERCEL_TOKEN** en GitHub:
   → https://github.com/aonetworkcrm-art/shadow_del_valle_r_full/settings/secrets/actions/new
   → Name: `VERCEL_TOKEN`, Value: (token de Vercel)

### Para activar generación con IA (OpenRouter)

En `config/settings.json`:
```json
"openrouter": {
  "api_key": "sk-or-v1-tu-api-key",
  "modelo": "google/gemini-2.0-flash-lite-preview",
  "max_tokens": 2048
}
```

---

## 🛑 LÍMITES ANTI-SPAM

En `config/settings.json`:

| Parámetro | Valor | Qué controla |
|---|---|---|
| `max_posts_por_dia` | 6 | Máximo de posts nuevos por día |
| `intervalo_generacion_horas` | 4.0 | Cada cuántas horas puede generar el agente |
| `umbral_frr_minimo` | 150.0 | FRR mínimo para considerar un nicho rentable |
| `cpc_minimo` | 80.0 | CPC mínimo para generar contenido |

---

## 🔄 PIPELINE COMPLETO

```
INVESTIGAR → Radar escanea 15 nichos, calcula FRR
     ↓
GENERAR   → OpenRouter (IA) o templates → Refinery forja HTML
     ↓     → Hasta 6 posts/día (rotación circular)
     ↓     → FAQs, Schema, Open Graph, Monetag
INDEXAR   → IndexNow notifica a Bing/Yandex
     ↓     → Sitemap actualizado para Google
DESPLEGAR → Vercel publica en segundos
     ↓     → https://shadow-del-valle-r.vercel.app
MONITOREAR → Monetag dashboard + Google Search Console
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

| Problema | Causa probable | Solución |
|---|---|---|
| Monetag no muestra anuncios | CDN regional bloqueada | Verificar desde otro navegador/VPN |
| El botón Admin no funciona | Falta GITHUB_PAT | Ejecutar `python control.py --all` localmente |
| API devuelve 500 | Error en Vercel | Ejecutar `vercel --prod --yes` |
| Google no indexa | Sitemap no actualizado | Verificar en Search Console |
| Error "pip install" | Faltan dependencias | `pip install -r requirements.txt` |
| No se generan posts hoy | Límite diario alcanzado | Esperar al día siguiente o `--force` |
| OpenRouter no responde | API key inválida | Verificar key en settings.json |

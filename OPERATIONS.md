# 📋 OPERATIONS — Manual de Operaciones

## Shadow Del Valle R

---

## 🎯 Flujo de Trabajo Diario

### 1. Generar contenido nuevo

```bash
cd shadow_del_valle_r
python generate_all.py
```

Esto regenera los 11 posts, actualiza el sitemap y notifica a IndexNow automáticamente.

### 2. Desplegar a producción

```bash
vercel --prod --yes
```

### 3. Verificar que Google lo reciba

```
https://shadow-del-valle-r.vercel.app/sitemap.xml
```

---

## 🚀 One-Click: Generar + Desplegar

```bash
python control.py --all
```

Este comando:
1. ✅ Regenera todos los posts
2. ✅ Actualiza el sitemap
3. ✅ Notifica a IndexNow (Bing/Yandex)
4. ✅ Despliega a Vercel

---

## 📈 Monitoreo

### Google Search Console
```
https://search.google.com/search-console
→ shadow-del-valle-r.vercel.app
→ Sitemaps → sitemap.xml
→ URL Inspection → buscar una URL específica
```

### Monetag Dashboard
```
https://monetag.com
→ Sites → shadow-del-valle-r.vercel.app
→ Statistics
```

### Analytics del sitio
```
https://shadow-del-valle-r.vercel.app/api/stats
```

---

## ⚙️ Control del Agente Autónomo

```bash
# Ver estado
python main_agent.py --status

# Pausar agente
python main_agent.py --kill-switch off

# Reanudar agente
python main_agent.py --kill-switch on

# Ejecutar una ronda
python main_agent.py --once

# Iniciar loop 24/7
python main_agent.py
```

---

## 🛑 Anti-Spam: Límites Configurables

En `config/settings.json`:

```json
{
  "scheduler": {
    "max_posts_por_dia": 6,       ← Máximo de posts por día
    "intervalo_generacion_horas": 4.0  ← Cada cuántas horas generar
  },
  "radar": {
    "umbral_frr_minimo": 150.0,   ← FRR mínimo para considerar un nicho
    "cpc_minimo": 80.0            ← CPC mínimo para generar contenido
  }
}
```

---

## 🔄 Pipeline Completo

```
1. INVESTIGAR → Radar escanea nichos de alto CPC
       ↓
2. GENERAR   → Refinery forja contenido SEO + Monetag
       ↓
3. INDEXAR   → IndexNow notifica a Bing/Yandex
       ↓
4. DESPLEGAR → Vercel publica a producción
       ↓
5. MONITOREAR → Google Search Console + Monetag analytics
```

---

## 🆘 Solución de Problemas

| Problema | Solución |
|---|---|
| Monetag no carga | Verificar `sw.js` en raíz y `quge5.com` en index.html |
| APIs no responden | Ejecutar `vercel --prod --yes` para redeploy |
| Google no indexa | Verificar sitemap en Search Console |
| Error al generar | Ejecutar `pip install -r requirements.txt` |

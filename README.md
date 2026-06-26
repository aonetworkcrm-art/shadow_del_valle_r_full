# 🌑 Shadow Del Valle R

**Sistema de generación y publicación automatizada de contenido nicho con monetización mediante Monetag.**

> *"Madera refinada que solo existe aquí"*

---

## 📋 Descripción

Shadow Del Valle R es un ecosistema completo para la creación, gestión y publicación de contenido nicho con alto CPC. Genera páginas HTML estáticas optimizadas para SEO, con Monetag integrado, y las despliega automáticamente a Vercel.

### Stack Tecnológico

- **Frontend:** HTML + CSS nativo (sin frameworks, sin imágenes, <15KB por página)
- **Backend:** Python 3.9+ (generación) + Node.js (API serverless en Vercel)
- **IA:** OpenRouter (Google Gemini, GPT-4o-mini, etc.) para contenido variado
- **Hosting:** Vercel (static + serverless functions, capa gratuita)
- **Monetización:** Monetag MultiTag (popunder + push + banners)
- **CDN:** Vercel Edge Network (global, <50ms de latencia)

### Capacidades

| Componente | Descripción |
|---|---|
| **Generación de contenido** | 16 posts de alto CPC ($85-$250) sobre el terremoto Venezuela 2026 |
| **Generación con IA** | OpenRouter + FreeBuff prompts para contenido único y variado |
| **Monetización** | Monetag MultiTag (popunder + smartlink + banners) integrado |
| **SEO** | Schema.org (Article + BreadcrumbList + FAQ), Open Graph, Twitter Cards, sitemap |
| **Indexación** | IndexNow (Bing/Yandex) automático + Google Search Console configurado |
| **Analytics** | Tracking de visitas/clics propio (track.js + stats.js) |
| **Anti-Spam** | Límite configurable de posts/día + rotación de contenido |
| **Automatización** | Botón web para generar/desplegar + GitHub Actions + agente autónomo |
| **Hosting** | Vercel (gratis), static HTML ultra-ligero (carga <0.5s) |

---

## 🚀 Inicio Rápido

```bash
# 1. Generar todos los posts
python generate_all.py

# 2. Desplegar a Vercel
vercel --prod --yes

# 3. El sitio está en vivo en:
#    https://shadow-del-valle-r.vercel.app
```

---

## 📁 Estructura del Proyecto

```
shadow_del_valle_r/
├── index.html                ← Landing page (lista dinámica de posts)
├── sw.js                     ← Service Worker de Monetag
├── api/                      ← Vercel Serverless Functions
│   ├── track.js              ←   POST /api/track (registrar visitas/clics)
│   ├── stats.js              ←   GET  /api/stats (dashboard analytics)
│   └── notify.js             ←   GET  /api/notify (IndexNow)
├── core/                     ← Motores del sistema
│   ├── silo_builder.py       ←   Generador de HTML con SEO + Monetag
│   ├── radar.py              ←   Escáner de nichos y FRR
│   ├── ledger.py             ←   Contabilidad y dashboard financiero
│   ├── deployer.py           ←   Deploy a Vercel/GitHub
│   └── silo_connector.py     ←   Conector de silos
├── config/
│   └── settings.json         ← Configuración central del sistema
├── output/                   ← Archivos generados
│   ├── posts/                ←   Posts en HTML (output/posts/slug/index.html)
│   ├── posts.json            ←   Lista de posts para la API
│   ├── sitemap.xml           ←   Mapa del sitio para Google
│   └── robots.txt            ←   Instrucciones para crawlers
├── generate_all.py           ← Genera todos los posts + sitemap + IndexNow
├── control.py                ← Centro de control unificado
├── shadow_del_valle_r.py     ← CLI Centro de Mando (menú interactivo)
├── main_agent.py             ← Agente autónomo AaaS (loop infinito)
├── deploy.py                 ← Scripts de deploy
├── vercel.json               ← Routing y configuración de Vercel
├── requirements.txt          ← Dependencias Python
├── package.json              ← Dependencias Node
├── ESTRATEGIA_DIFUSION.md    ← Guía de difusión en redes sociales
└── GOOGLE_SEARCH_CONSOLE.md  ← Guía de Google Search Console
```

---

## 🎮 Comandos Principales

### Generar contenido

```bash
# Generar hasta 6 posts del día (respeta límite diario)
python generate_all.py

# Forzar generación de TODOS los posts (16)
python generate_all.py --force

# Centro de mando interactivo
python shadow_del_valle_r.py

# Generar con IA (si configuraste OpenRouter)
python main_agent.py --once
```

### Desplegar

```bash
# Deploy directo a Vercel
vercel --prod --yes

# Pipeline completo con script
python deploy.py --all
```

### Control Unificado

```bash
# Menú interactivo (recomendado)
python control.py

# Pipeline completo: generar + deploy + notify
python control.py --all

# Ver estado del sistema
python control.py --status
```

**O desde el acceso directo del escritorio:**
Haz doble clic en `Shadow_Del_Valle_R.bat`

---

## 🔧 Configuración

Editar `config/settings.json`:

```json
{
  "monetag": {
    "habilitado": true,
    "site_id": "253508"
  },
  "scheduler": {
    "agente_activo": true,
    "intervalo_generacion_horas": 4.0,
    "max_posts_por_dia": 6
  },
  "radar": {
    "umbral_frr_minimo": 150.0,
    "cpc_minimo": 80.0
  }
}
```

---

## 🌐 APIs

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/posts` | GET | Lista de todos los posts (desde posts.json) |
| `/api/track` | POST | Registrar visita o clic |
| `/api/stats` | GET | Estadísticas de analytics |
| `/api/notify` | GET | Notificar URLs a IndexNow |

---

## 📊 Estado del Sitio

- **URL:** https://shadow-del-valle-r.vercel.app
- **Posts:** 16 (CPC promedio $179, top CPC $250)
- **Monetag:** MultiTag verificado (zone 253508, quge5.com)
- **Google Search Console:** ✅ Verificado + sitemap enviado
- **IndexNow:** ✅ Activo (Bing/Yandex)
- **Hosting:** Vercel (gratis)
- **Carga de página:** <0.5s
- **Peso por página:** ~12KB

---

## 📄 Licencia

Uso privado — Shadow Del Valle R © 2026

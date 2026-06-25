# 🌑 Shadow Del Valle R

**Sistema de generación y publicación automatizada de contenido nicho con monetización mediante Monetag.**

> *"Madera refinada que solo existe aquí"*

---

## 📋 Descripción

Shadow Del Valle R es un ecosistema completo para la creación, gestión y publicación de contenido nicho con alto CPC. Genera páginas HTML estáticas optimizadas para SEO, con Monetag integrado, y las despliega automáticamente a Vercel.

### Capacidades

| Componente | Descripción |
|---|---|
| **Generación de contenido** | 11 posts de alto CPC ($85-$220) sobre el terremoto Venezuela 2026 |
| **Monetización** | Monetag MultiTag (popunder + smartlink) integrado en todas las páginas |
| **SEO** | Schema.org (Article + BreadcrumbList + FAQ), Open Graph, Twitter Cards, sitemap |
| **Indexación** | IndexNow (Bing/Yandex) automático + Google Search Console configurado |
| **Analytics** | Tracking de visitas/clics con Vercel KV (o fallback en memoria) |
| **Hosting** | Vercel (gratis), static HTML ultra-ligero |

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
# Generar TODOS los posts (11 posts)
python generate_all.py

# Centro de mando interactivo
python shadow_del_valle_r.py

# Agente autónomo (una ronda)
python main_agent.py --once

# Agente autónomo (loop infinito 24/7)
python main_agent.py
```

### Desplegar

```bash
# Deploy directo a Vercel
vercel --prod --yes

# Deploy con script
python deploy.py --vercel

# Pipeline completo (GitHub + Vercel)
python deploy.py --all
```

### Control

```bash
# Centro de control unificado
python control.py

# Modo interactivo
python control.py --menu

# Generar + deploy + notify en un solo comando
python control.py --all

# Ver estado
python control.py --status
```

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
- **Posts:** 11 (CPC promedio $158, top CPC $220)
- **Monetag:** MultiTag verificado (zone 253508)
- **Google Search Console:** ✅ Verificado + sitemap enviado
- **IndexNow:** ✅ Activo (Bing/Yandex)
- **Hosting:** Vercel (gratis)

---

## 📄 Licencia

Uso privado — Shadow Del Valle R © 2026

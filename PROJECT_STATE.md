# 🌑 Shadow Del Valle R — Estado del Proyecto

> **Última sesión:** 5 Julio 2026, ~4:00 AM  
> **Próxima sesión:** Al amanecer ☀️

---

## 📡 Links

| Recurso | URL |
|---------|-----|
| **GitHub Repo** | https://github.com/aonetworkcrm-art/shadow_del_valle_r_full |
| **Sitio Vercel** | https://shadow-del-valle-r.vercel.app |
| **Dashboard Flask (local)** | `http://localhost:5000` |
| **SEO Oracle (local)** | `http://localhost:5000/seo-oracle` |
| **Railway** (pendiente) | Conectar repo en https://railway.app |

---

## ✅ Completado (4 Fases)

### ✅ FASE A — Radar v2.0 (SEO Oracle absorbido en radar.py)
- `core/radar.py` ahora tiene `HighCPCNiche`, `ContentNode`, `YieldProjection` dataclasses
- Enums: `TrafficDifficulty`, `SearchVolume`, `SearchIntent`, `ConfidenceLevel`
- Métodos nuevos: `rank_by_profitability()`, `get_confidence()`, `calculate_yield_projection()`, `create_content_plan()`, `export_report()`, `get_seo_stats()`
- `NICHES_DB_ENRICHED` derivado automáticamente de `NICHOS_DB`
- 100% backward compatible con `Radar` legacy
- `core/seo_oracle.py` eliminado (absorbido en radar.py)

### ✅ FASE B — Menús CLI Separados
- **`control.py`**: Opción `[8] 📊 SEO Oracle` → submenú con 7 opciones (ranking FRR, Profitability, proyección, plan, stats, export, evergreen)
- **`shadow_del_valle_r.py`**: Opción `[10] 📊 SEO Oracle` → mismo submenú
- Ambos menús Radar existentes intactos

### ✅ FASE C — Integración Hybrid en main_agent.py
- Nueva estrategia `"hybrid"`: FRR(40%) + Profitability(40%) + Confidence(20%)
- Normalización min-max en una sola pasada (sin escaneos repetidos)
- Rotación preservada (no repite nichos)
- `register_node()` en cada post generado → tracking de revenue
- Bugfixes: `fuente` scope, `slug` out of scope
- 3 estrategias legacy intactas: `rotating`, `highest-cpc`, `random`

### ✅ FASE D — Dashboard Flask SEO Oracle
- Ruta: `GET /seo-oracle` → página SPA completa
- 7 endpoints API:
  - `/api/seo-oracle/niches` — lista de nichos
  - `/api/seo-oracle/ranking-frr` — ranking FRR (15)
  - `/api/seo-oracle/ranking-profit` — ranking Profitability (15)
  - `/api/seo-oracle/projection` — proyección LOW/AVG/HIGH
  - `/api/seo-oracle/plan` — plan multi-nicho
  - `/api/seo-oracle/stats` — estadísticas unificadas
  - `/api/seo-oracle/export` — exportar reporte JSON
- Frontend: sidebar con 6 secciones, tablas interactivas, selectores, KPIs

### ✅ Estrategia Hybrid como Default
- `config/settings.json`: `"estrategia": "hybrid"`
- Pipeline probado con `python main_agent.py --once` ✅

---

## 🗺️ Pendiente para el Amanecer

### 🔲 Deploy a Railway (prioridad #1)
```
1. Ir a https://railway.app
2. "Sign in with GitHub"
3. "New Project" → "Deploy from GitHub repo"
4. Seleccionar: aonetworkcrm-art/shadow_del_valle_r_full
5. Railway detecta railway.json → despliega solo
6. URLs:
   - Dashboard: https://[nombre].up.railway.app
   - SEO Oracle: https://[nombre].up.railway.app/seo-oracle
   - Health: https://[nombre].up.railway.app/health
```

### 🔲 Configurar API Keys
```bash
# .env.local (para Railway o local)
OPENROUTER_API_KEY=sk-or-v1-...
MONETAG_API_TOKEN=tu_token_de_monetag
```

### 🔲 Posibles Mejoras
- [ ] Agregar botón "Open Dashboard" en los menús CLI (abre navegador)
- [ ] Página de inicio en Flask con enlaces a Monetag y SEO Oracle
- [ ] Tests unitarios para la estrategia hybrid
- [ ] Analytics: tracking de revenue real vs proyectado en SEO Oracle

---

## 📊 Último Estado del Sistema

```
Estrategia: hybrid (default)
Nichos: 15 (10 validados PI + 5 terremoto)
FRR mínimo: 150
Pipeline: ✅ Funcionando (con template fallback)
Dashboard: ✅ Cargando correctamente (localhost:5000/seo-oracle)
Git: ✅ Último commit: 359ac96 (push a origin/main)
```

---

*"Cuando todos dormían, nosotros construíamos el futuro."* 🌑

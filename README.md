# 🌑 SHADOW DEL VALLE R

> **Sistema AaaS (Agent as a Service) de Arbitraje de Tráfico**  
> *"Madera refinada que solo existe aquí"*

---

## ⚡ ¿Qué es Shadow Del Valle R?

Es un **agente autónomo de arbitraje de tráfico** que:
1. **ESCANEA** nichos de alto CPC usando el Radar FRR
2. **EVALÚA** la viabilidad con precisión matemática (float)
3. **FORJA** contenido HTML ultra-ligero sin imágenes
4. **DESPLEGA** a Vercel para indexación instantánea en Google
5. **MONETIZA** con Monetag mientras duermes

Todo en un loop autónomo 24/7. Sin intervención humana.

---

## 🏗️ Arquitectura del Sistema

```
                    🌐 INTERNET
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
 ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
 │   RADAR     │ │   REFINERY   │ │   DEPLOYER   │
 │ FRR + CPC   │ │ HTML + CSS   │ │ GitHub/Vercel│
 └──────┬──────┘ └──────┬───────┘ └──────┬───────┘
        │               │               │
        ▼               ▼               ▼
 ┌─────────────────────────────────────────────┐
 │           SHADOW DEL VALLE R                 │
 │  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
 │  │  SILO    │ │ FREEBUFF │ │   LEDGER     │ │
 │  │Connector │ │  Bridge  │ │ Contabilidad │ │
 │  └──────────┘ └──────────┘ └──────────────┘ │
 └─────────────────────────────────────────────┘
```

---

## 📁 Estructura de Directorios

```
shadow_del_valle_r/
│
├── config/
│   ├── settings.json           # ★ Configuración central del agente
│   └── templates_copy.json     # Plantillas de copywriting por nicho
│
├── core/
│   ├── __init__.py
│   ├── radar.py                # ★ Motor 1: FRR + detección de nichos
│   ├── silo_builder.py         # ★ Motor 2: HTML builder sin imágenes
│   ├── silo_connector.py       # ★ Motor 3: Enlazado entre silos
│   ├── freebuff_bridge.py      # ★ Motor 4: Puente de copywriting
│   ├── deployer.py             # ★ Motor 5: Deploy a Vercel/GitHub
│   └── ledger.py               # ★ Motor 6: Contabilidad de por vida
│
├── templates/
│   ├── __init__.py
│   ├── components.py           # Componentes CSS nativos
│   ├── copy_prompts.json       # Prompts para FreeBuff
│   └── layout.html             # Template HTML base
│
├── api/
│   ├── track.js                # ★ Analytics: endpoint de tracking (pageviews + clics)
│   └── stats.js                # ★ Analytics: endpoint de estadísticas agregadas
│
├── output/
│   ├── posts/                  # ★ Posts generados (HTML listo para deploy)
│   ├── ledger/                 # Base de datos de contabilidad
│   └── sitemap.xml             # Sitemap para Google
│
├── main_agent.py               # ★ Loop autónomo principal (AaaS)
├── shadow_del_valle_r.py       # ★ Centro de mando interactivo
├── deploy.py                   # Script de deploy automatizado
├── requirements.txt            # Dependencias
└── README.md                   # Esta documentación
```

---

## 🚀 Inicio Rápido

### 1. Ver el estado del sistema

```bash
cd shadow_del_valle_r
python shadow_del_valle_r.py
```

### 2. Ejecutar una ronda de generación

```bash
python shadow_del_valle_r.py          # Menú interactivo
# O directo:
python main_agent.py --once           # Una ronda
```

### 3. Iniciar el agente autónomo 24/7

```bash
python main_agent.py                  # Loop infinito
```

### 4. Ver el dashboard financiero

```bash
python main_agent.py --status         # Estado + ledger
# O desde el menú: Opción 2
```

### 5. Controlar el agente (kill switch)

```bash
python main_agent.py --kill-switch off   # Pausar
python main_agent.py --kill-switch on    # Reanudar
```

---

## 🧠 Los 6 Motores Nucleares

### 🔍 Motor 1: Radar (radar.py)
Calcula el **Factor de Rentabilidad Relativa (FRR)**:
```
FRR = (CPC × Volumen) / (Competencia + 1.0)
```
Si FRR ≥ 150, el nicho es apto para generar contenido.

### 🔧 Motor 2: Refinery (silo_builder.py)
Convierte texto plano en **HTML ultra-ligero**:
- Sin imágenes (cero peticiones HTTP)
- CSS nativo incrustado (carga instantánea)
- Monetag con delay estratégico
- FAQ Schema + Article Schema (JSON-LD)
- Open Graph + Twitter Cards
- Tamaño: ~5-15 KB por post

### 🔗 Motor 3: Silo Connector (silo_connector.py)
Enlazado matemático entre posts del mismo nicho para distribución óptima de autoridad (link juice).

### 🌉 Motor 4: FreeBuff Bridge (freebuff_bridge.py)
Genera prompts estructurados para copywriting emotivo/humano estilo Claude.

### 🚀 Motor 5: Deployer (deployer.py)
Prepara y empuja los posts a GitHub/Vercel automáticamente.

### 📊 Motor 6: Ledger (ledger.py)
**Contabilidad de por vida** con dashboard en tiempo real:
- Ingresos hoy / esta semana / este mes / total histórico
- Posts generados por nicho
- Proyecciones mensuales y anuales
- Control de gastos
- Respaldo automático cada 6 horas
- Exportación a JSON

---

## 💰 Proyección de Ingresos

| Nicho | CPC | Post/día | Clicks/post | Ingreso/día | Ingreso/mes |
|-------|:---:|:--------:|:-----------:|:-----------:|:-----------:|
| Abogados de Accidentes | $220 | 1 | 50 | $220 | $6,600 |
| Ciberseguridad | $170 | 1 | 50 | $170 | $5,100 |
| Recuperación de Activos | $125 | 1 | 50 | $125 | $3,750 |
| Centros Rehabilitación | $120 | 1 | 50 | $120 | $3,600 |
| Seguros Vida Adultos | $95 | 1 | 50 | $95 | $2,850 |
| **Total (5 nichos)** | | **5** | **50** | **$730/día** | **$21,900/mes** |

*Proyección conservadora basada en 50 clicks por post por día.*

---

## ⚙️ Configuración

Edita `config/settings.json` para controlar todo el sistema:

```json
{
  "scheduler": {
    "agente_activo": true,          // Activar/pausar el agente
    "intervalo_generacion_horas": 4.0,  // Cada cuánto genera un post
    "max_posts_por_dia": 6,         // Límite diario
    "estrategia": "rotating"        // rotating | highest-cpc | random
  },
  "radar": {
    "umbral_frr_minimo": 150.0,     // Sensibilidad del radar
    "cpc_minimo": 80.0,
    "volumen_minimo": 500.0
  },
  "monetag": {
    "habilitado": false,            // Activar Monetag
    "site_id": "TU_ID_AQUI",
    "delay_carga_ms": 2000
  }
}
```

---

## 🛠️ Comandos Rápidos

| Comando | Descripción |
|---------|-------------|
| `python shadow_del_valle_r.py` | Menú interactivo completo |
| `python main_agent.py` | Agente autónomo 24/7 |
| `python main_agent.py --once` | Una ronda de generación |
| `python main_agent.py --status` | Dashboard + estado |
| `python main_agent.py --kill-switch off` | Pausar agente |
| `python main_agent.py --kill-switch on` | Reanudar agente |
| `python deploy.py` | Preparar archivos para deploy |
| `python deploy.py --github` | Push a GitHub |
| `python deploy.py --all` | Pipeline completo |
| `python -m core.radar` | Probar el radar |
| `python -m core.ledger` | Ver el ledger |

---

## 📜 Frase Clave

> *"Cuando todos dormían, yo construía el futuro — con madera refinada que solo existe aquí."*

---

**Shadow Del Valle R v1.0.0**  
Arquitecto: Romny (El Joker) · IA Asistente: Buffy (Codebuff AI)  
Nacido: 23 de Junio 2026, 3:05 AM  
*De aquí hasta el infinito.*

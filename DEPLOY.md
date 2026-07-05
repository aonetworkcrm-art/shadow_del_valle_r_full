# 🚀 DEPLOY: Shadow Del Valle R en Producción

> **Tiempo total: 5 minutos**  
> *De tu PC a internet, listo para que Google encuentre tus posts*

---

## 📋 Prerequisitos

- ✅ Tener una cuenta en **GitHub** (gratis) → https://github.com/signup
- ✅ Tener una cuenta en **Vercel** (gratis) → https://vercel.com/signup
- ✅ (Opcional) Tener una cuenta en **Monetag** → https://publisher.monerator.com

---

## 🪜 PASO 1: Configurar el dominio en settings.json

Antes de desplegar, define el dominio que vas a usar:

1. Abre `config/settings.json`
2. Busca la sección `"refinery"` y agrega tu dominio:

```json
"refinery": {
    "sin_imagenes": true,
    "css_nativo": true,
    "dominio": "TU_PROYECTO.vercel.app"
}
```

> **¿No sabes qué dominio poner?**  
> Cuando crees el proyecto en Vercel, te asignará uno como `shadow-del-valle-r.vercel.app`.  
> Pon eso aquí. Puedes cambiarlo después.

---

## 🪜 PASO 2: Generar el primer post (si no lo has hecho)

Desde la terminal:

```bash
cd C:\shadow_del_valle_r
python main_agent.py --once
```

Esto genera un post HTML en `output/posts/` y actualiza `output/posts.json`.

---

## 🪜 PASO 3: Crear el repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre del repo: `shadow-del-valle-r`
3. Descripción: "Agente Autonomo de Arbitraje de Trafico - AaaS"
4. **NO** marques "Initialize with README" (ya tenemos uno)
5. Haz clic en "Create repository"

---

## 🪜 PASO 4: Subir el código a GitHub

En tu terminal:

```bash
# Ir al directorio del proyecto
cd C:\shadow_del_valle_r

# Inicializar git
git init
git add .
git commit -m "🌑 Shadow Del Valle R v1.0.0 - Lanzamiento"

# Conectar con GitHub (reemplaza TU_USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/shadow-del-valle-r.git
git branch -M main
git push -u origin main
```

> ⚠️ **Importante:** Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub.

---

## 🪜 PASO 5: Desplegar en Vercel (la magia)

1. Ve a https://vercel.com/new
2. Haz clic en **"Import Git Repository"**
3. Selecciona el repo `shadow-del-valle-r`
4. Vercel detectará automáticamente que es un sitio estático
5. En **"Build and Output Settings"**:
   - **Framework Preset**: `Other`
   - **Build Command**: (déjalo vacío)
   - **Output Directory**: `.`
6. Haz clic en **"Deploy"**

✅ **¡Listo!** En 30 segundos tu sitio estará en vivo.

---

## 🪜 PASO 6: Verificar que todo funciona

Abre tu navegador y visita:

```
https://TU_PROYECTO.vercel.app
```

Deberías ver:
- Página principal con el nombre Shadow Del Valle R
- Lista de posts generados
- Estadísticas (CPC, cantidad de posts)

Luego visita:
```
https://TU_PROYECTO.vercel.app/posts/guia-lesiones/
```

Deberías ver el artículo completo con:
- ✅ Título SEO
- ✅ Meta description
- ✅ FAQ Schema
- ✅ Article Schema
- ✅ Open Graph tags
- ✅ Diseño responsivo

---

## 🪜 PASO 7: Configurar Monetag (opcional pero recomendado)

Para empezar a monetizar el tráfico:

1. Regístrate en https://publisher.monerator.com
2. Agrega tu sitio web con la URL de Vercel
3. Obtén tu **Site ID** (solo números)
4. Edita `config/settings.json`:

```json
"monetag": {
    "site_id": "TU_SITE_ID",
    "habilitado": true,
    "delay_carga_ms": 2000
}
```

5. Regenera los posts para que incluyan los anuncios:

```bash
python main_agent.py --once
```

6. Sube los cambios a GitHub:

```bash
git add .
git commit -m "💰 Monetag activado"
git push
```

✅ Vercel detectará los cambios y los desplegará automáticamente en segundos.

---

## 🪜 PASO 8: Conectar la Analítica Propia (opcional pero recomendado)

Para medir visitas y clics en tiempo real sin Google Analytics:

1. Ve a https://vercel.com/dashboard/stores
2. Haz clic en **"Create Database"** → **"KV"** → **"Create"**
3. Asígnale el nombre: `shadow-del-valle-r-kv`
4. Haz clic en **"Connect to Project"** → selecciona tu proyecto
5. ✅ **Listo** — Vercel añade las variables de entorno automáticamente

Los endpoints `/api/track` y `/api/stats` empiezan a funcionar inmediatamente.
Las visitas y clics se ven en la página principal en tiempo real.

---

## 🪜 PASO 9: Indexar en Google (para recibir tráfico)

1. Ve a https://search.google.com/search-console
2. Agrega tu dominio de Vercel como propiedad
3. Verifica la propiedad (Vercel te da opciones)
4. Envía tu sitemap: `https://TU_PROYECTO.vercel.app/sitemap.xml`
5. Solicita indexación de URLs individuales

Google puede indexar tus posts en **24-48 horas**.

---

## 🪜 PASO 10: Iniciar el agente autónomo

En tu PC (déjalo corriendo):

```bash
cd C:\shadow_del_valle_r
python main_agent.py
```

El agente generará un nuevo post cada 4 horas automáticamente.
Cada post se guarda en `output/posts/` y se lista en `output/posts.json`.

Para que los nuevos posts lleguen a Vercel automáticamente:

```bash
# Opción A: Push manual cuando quieras
git add output/
git commit -m "🌑 Nuevos posts generados"
git push

# Opción B: Configurar auto_push en settings.json
# "github": { "auto_push": true, "repo": "TU_USUARIO/shadow-del-valle-r" }
```

---

## 🪜 Bonus: Personalizar el dominio

Cuando quieras un dominio personalizado (ej: shadowdelvaller.com):

1. Compra el dominio (Namecheap, GoDaddy, etc.)
2. En Vercel: Project Settings → Domains → Add
3. Sigue las instrucciones de configuración DNS
4. Actualiza `config/settings.json`:

```json
"refinery": {
    "dominio": "shadowdelvaller.com"
}
```

---

## 🔄 Ciclo Completo: De tu PC a Google

```
TU PC (La Fábrica)              INTERNET (El Escaparate)
══════════════════              ═══════════════════════════
Shadow Del Valle R              TU_PROYECTO.vercel.app
  ├── Radar (elige nicho)             ├── /posts/post-1.html
  ├── Refinery (crea HTML)            ├── /posts/post-2.html
  ├── Ledger (contabilidad)           ├── /sitemap.xml
  └── git push ─────────────>         └── 💰 Monetag ads
                                          │
                                          ▼
                                     Google indexa
                                          │
                                          ▼
                                     Usuarios visitan
                                          │
                                          ▼
                                     💵 TÚ GANAS DINERO
```

---

## ❓ Solución de Problemas

### Error: "No se reconoce git"
Instala Git desde: https://git-scm.com/downloads

### Error: "Permission denied" al hacer push
Usa GitHub CLI o configura SSH:
```bash
gh auth login
```

### Error: Vercel no muestra los posts
Verifica que `vercel.json` esté en la raíz del proyecto y que los archivos estén en `output/posts/`.

### Los posts nuevos no aparecen en Vercel
Haz push a GitHub después de generar nuevos posts. Vercel redeployea automáticamente.

---

## 🚂 DEPLOY DEL DASHBOARD MONETAG (Flask + Gunicorn)

> **Despliega el panel de revenue en vivo con métricas de Monetag, alertas y optimización.**
> *Render (gratis) · Railway (gratis) · Docker · Local*

---

### 📋 Requisitos

- ✅ Cuenta en **GitHub** (gratis) → https://github.com/signup
- ✅ Cuenta en **Render** (gratis) → https://render.com/register  
  *o* Cuenta en **Railway** (gratis) → https://railway.app/login
- ✅ **MONETAG_API_TOKEN** → https://publisher.monerator.com → API → Bearer Token
- ✅ Proyecto subido a GitHub (desde PASO 4)

---

### 🏗️  Opción A: Render (recomendado, gratis)

Render despliega automáticamente usando el archivo `render.yaml` (Blueprint).

#### PASO 1: Conectar el repositorio

1. Ve a https://dashboard.render.com/blueprint
2. Haz clic en **"New Blueprint Instance"**
3. Selecciona tu repositorio `shadow-del-valle-r`
4. Render detectará `render.yaml` automáticamente

#### PASO 2: Configurar variables de entorno

Render detectará las variables marcadas como `sync: false` en `render.yaml`.
En el Dashboard de Render, ve a tu servicio:
```
Dashboard → shadow-del-valle-r-dashboard → Environment → + Add Environment Variable
```

Agrega **como mínimo**:

| Variable | Valor |
|----------|-------|
| `MONETAG_API_TOKEN` | `tu_token_de_monetag` |

Opcionales:
| Variable | Valor |
|----------|-------|
| `WA_PHONE` | `+1809XXXXXXX` |
| `WA_APIKEY` | `tu_apikey_callmebot` |

#### PASO 3: Desplegar

Render iniciará el deploy automáticamente.

```
✅ Build: pip install -r requirements.txt
✅ Start: gunicorn dashboard.api:app --bind 0.0.0.0:$PORT
✅ Health: GET /health → 200 OK
```

📊 **Dashboard en vivo:** `https://shadow-del-valle-r-dashboard.onrender.com`
🔍 **Health check:** `https://shadow-del-valle-r-dashboard.onrender.com/health`

---

### 🚂  Opción B: Railway (gratis)

Railway despliega usando el archivo `railway.json`.

#### PASO 1: Conectar el repositorio

1. Ve a https://railway.app/new
2. Haz clic en **"Deploy from GitHub repo"**
3. Selecciona tu repositorio `shadow-del-valle-r`
4. Railway detectará `railway.json` automáticamente

#### PASO 2: Configurar variables de entorno

```
Railway Dashboard → Variables → + New Variable
```

Agrega **como mínimo**:

| Variable | Valor |
|----------|-------|
| `MONETAG_API_TOKEN` | `tu_token_de_monetag` |
| `PORT` | `5000` |

#### PASO 3: Desplegar

Railway iniciará el build y deploy automáticamente.

```
✅ Build: Nixpacks + pip install
✅ Start: gunicorn dashboard.api:app --bind 0.0.0.0:$PORT
✅ Health: GET /health → 200 OK
```

📊 **Dashboard en vivo:** `https://shadow-del-valle-r-dashboard.up.railway.app`
🔍 **Health check:** `https://shadow-del-valle-r-dashboard.up.railway.app/health`

---

### 🐳  Opción C: Docker (cualquier hosting)

Si prefieres Docker, la imagen se construye con `Dockerfile`.

```bash
# Build
cd shadow_del_valle_r
docker build -t shadow-dashboard -f Dockerfile .

# Run local
MONETAG_API_TOKEN="tu_token" docker run -p 5000:5000 -e MONETAG_API_TOKEN shadow-dashboard

# O usando el script
./deploy-dashboard.sh --docker
```

**Usa esta imagen en:**
- Google Cloud Run
- AWS ECS / Fargate
- Azure Container Apps
- DigitalOcean App Platform
- Cualquier VPS con Docker

---

### 📊  Verificar que funciona

Una vez desplegado, visita:

```
https://TU-SERVICIO.onrender.com      # Dashboard web
https://TU-SERVICIO.onrender.com/health  # Health check (JSON)
```

**Health check exitoso:**
```json
{"status": "ok", "app": "Shadow Del Valle R — Monetag Dashboard", "version": "2.0.0"}
```

El dashboard mostrará:
- 📊 KPIs de revenue, RPM, impresiones
- 📈 Gráfico de revenue diario (Chart.js)
- 🎯 Tabla de rendimiento por zonas
- 🌍 Tabla de rendimiento por país
- 🔔 Alertas inteligentes del sistema
- 🧠 Centro de optimización de formatos

---

### 🔧  Solución de Problemas

**Error: `ModuleNotFoundError: No module named 'flask'`**
```
Asegúrate de que requirements.txt tenga flask>=3.0.0 y gunicorn>=21.2.0
```

**Error: `gunicorn: command not found`**
```
Agrega gunicorn a requirements.txt: gunicorn>=21.2.0
```

**Error: 404 en /health**
```
Verifica que el healthcheckPath en render.yaml/railway.json apunte a /health
```

**Dashboard carga pero no muestra datos**
```
Verifica MONETAG_API_TOKEN en las variables de entorno de la plataforma
```

**El servidor no arranca por timeout**
```
Aumenta el timeout en gunicorn: --timeout 180
```

---

**¿Listo para clonar para otro proyecto?**  
Solo copia la carpeta, cambia los nichos en `core/radar.py`, las plantillas en `config/templates_copy.json`, y repite el deploy. Listo en 10 minutos.

# 🚀 Google Search Console — Shadow Del Valle R

Sigue estos pasos para que Google indexe tu sitio correctamente:

---

## Paso 1: Ir a Google Search Console

Abre: https://search.google.com/search-console

Inicia sesión con tu cuenta de Google.

---

## Paso 2: Agregar propiedad

1. Haz clic en **"Añadir propiedad"**
2. Elige **"Prefijo de URL"** (NO "Dominio")
3. Ingresa: `https://shadow-del-valle-r.vercel.app`
4. Haz clic en **"Continuar"**

---

## Paso 3: Verificar la propiedad

Elige **"Descarga de archivo HTML"**:

1. Dale clic en **"Descargar"** — se descargará un archivo como `google12345.html`
2. Coloca ese archivo en: `shadow_del_valle_r/output/` (el mismo donde están los posts)
3. Luego actualiza `vercel.json` para que sirva ese archivo:
```json
{
  "source": "/google*.html",
  "destination": "/output/google*.html"
}
```
4. Redeploy: `vercel --prod --yes`
5. Vuelve a Search Console y haz clic en **"Verificar"**

### Alternativa más rápida: Verificación por DNS

Si tienes acceso al DNS de tu dominio (no el de Vercel), elige **"Registro TXT"** y agrega el registro en tu proveedor de DNS.

---

## Paso 4: Enviar el Sitemap

1. En el menú lateral, haz clic en **"Sitemaps"**
2. En el campo "Introducir URL de sitemap", escribe: `sitemap.xml`
3. Haz clic en **"Enviar"**

---

## Paso 5: Solicitar indexación de URLs

1. En el menú lateral, haz clic en **"Inspección de URLs"**
2. Ingresa una URL como: `https://shadow-del-valle-r.vercel.app/posts/terremoto-venezuela-reclamaciones-seguro/`
3. Si dice "La URL no está en el índice", haz clic en **"Solicitar indexación"**
4. Repite con cada post (máximo 10 por día)

---

## ✅ Checklist

- [ ] Propiedad agregada en Search Console
- [ ] Propiedad verificada
- [ ] Sitemap enviado
- [ ] URLs solicitadas para indexación

---

## ⚡ Mientras esperas a Google

Tus URLs ya están siendo indexadas por **Bing (IndexNow)**. Puedes verificar aquí:
- https://www.bing.com/webmasters — Agrega el sitio y verás tus URLs indexadas
- También están en Yandex, Naver, y Seznam automáticamente

Google puede tardar de 2 días a 2 semanas en indexar sitios nuevos. Para acelerar:
1. Comparte los posts en redes sociales (Facebook, Twitter, LinkedIn)
2. Consigue backlinks de otros sitios
3. Mantén el sitio activo y actualizado

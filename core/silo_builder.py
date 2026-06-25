# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Motor 2: El Refinery & Deployer
=====================================================
Compila el texto contextual en HTML puro optimizado para Vercel.
Sin imágenes, solo CSS nativo, cajas de alerta visuales y Monetag.

Características:
    - HTML estático ultra-ligero (pesa KB, no MB)
    - CSS nativo incrustado (cero peticiones HTTP extras)
    - Monetag inyectado con delay estratégico
    - FAQ Schema + Article Schema (JSON-LD)
    - Open Graph + Twitter Cards
    - Diseño responsivo sin frameworks
    - Tiempo de carga: < 0.5 segundos
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class Refinery:
    """
    Motor de refinamiento que convierte texto plano en HTML
    indexable, ultra-rápido y optimizado para Monetag.
    """
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config = self._load_config(config_path)
        self.posts_generados: List[Dict] = []
    
    def _load_config(self, path: str) -> Dict:
        default = {
            "monetag": {"habilitado": False, "site_id": "", "delay_carga_ms": 2000},
            "refinery": {
                "sin_imagenes": True, "css_nativo": True, "emojis_estrategicos": True,
                "incluir_faq_schema": True, "incluir_article_schema": True,
                "incluir_open_graph": True, "incluir_twitter_card": True,
                "dominio": "TU_DOMINIO.vercel.app"
            }
        }
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg
            return default
        except:
            return default
    
    def _build_monetag_script(self) -> Tuple[str, str]:
        """Construye scripts de Monetag optimizados.
        Estrategia: carga diferida + trigger en interacción del usuario.
        """
        cfg = self.config.get("monetag", {})
        habilitado = cfg.get("habilitado", False)
        site_id = cfg.get("site_id", "")
        
        if not habilitado or not site_id:
            return "", ""
        
        head_script = f"""
    <script>
        // 🌑 Shadow Monetag — Carga inteligente
        (function() {{
            var zone = '{site_id}';
            var loaded = false;
            var pendingPop = null;
            
            function loadMonetag() {{
                if (loaded) return;
                loaded = true;
                var s = document.createElement('script');
                s.src = 'https://quge5.com/88/tag.min.js';
                s.setAttribute('data-zone', zone);
                s.setAttribute('data-cfasync', 'false');
                s.async = true;
                document.head.appendChild(s);
            }}
            
            // Cargar después de 3s o al primer clic
            setTimeout(loadMonetag, 3000);
            document.addEventListener('click', loadMonetag, {{once: true}});
            document.addEventListener('scroll', function() {{
                if (window.scrollY > 200) loadMonetag();
            }}, {{once: true}});
            
            // Solicitar notificación push al hacer clic
            document.addEventListener('click', function() {{
                if ('Notification' in window && Notification.permission === 'default') {{
                    setTimeout(function() {{ Notification.requestPermission(); }}, 500);
                }}
            }}, {{once: true}});
        }})();
    </script>"""
        
        body_script = ""  # Todo viaja en head ahora
        return head_script, body_script
    
    def _build_css(self) -> str:
        """Genera CSS nativo ultra-ligero."""
        return """
        *{margin:0;padding:0;box-sizing:border-box}
        :root{--bg:#fafafa;--text:#1a1a1a;--accent:#d32f2f;--accent2:#1565c0;
               --box-bg:#fff5f5;--box-border:#ffcdd2;--success-bg:#f0fdf4;
               --success-border:#bbf7d0;--tip-bg:#fff7ed;--tip-border:#fed7aa;
               --card:#ffffff;--border:#e5e7eb;--dim:#6b7280}
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
             line-height:1.7;color:var(--text);background:var(--bg);max-width:720px;
             margin:0 auto;padding:24px 20px}
        h1{font-size:1.8rem;color:#111;line-height:1.25;margin:0 0 8px;font-weight:700}
        h2{font-size:1.3rem;margin:32px 0 12px;color:#222;font-weight:600;padding-bottom:6px;border-bottom:2px solid var(--accent)}
        h3{font-size:1.1rem;margin:20px 0 8px;color:#333;font-weight:600}
        p{margin:0 0 16px;font-size:1.05rem;color:#333}
        .meta{font-size:0.8rem;color:var(--dim);margin:0 0 24px;padding-bottom:16px;border-bottom:1px solid var(--border)}
        .meta span{margin-right:16px}
        .alerta-box{background:var(--box-bg);border-left:4px solid var(--accent);border-radius:6px;padding:16px 20px;margin:24px 0}
        .alerta-title{font-weight:700;color:var(--accent);margin-bottom:6px;font-size:0.9rem}
        .success-box{background:var(--success-bg);border-left:4px solid #16a34a;border-radius:6px;padding:16px 20px;margin:24px 0}
        .tip-box{background:var(--tip-bg);border-left:4px solid #f59e0b;border-radius:6px;padding:16px 20px;margin:24px 0}
        ul,ol{margin:0 0 16px 24px}
        li{margin:6px 0;font-size:1.05rem;color:#333}
        li::marker{color:var(--accent)}
        .btn-accion{display:inline-block;background:var(--accent);color:#fff!important;padding:14px 28px;
                    text-decoration:none;font-weight:700;border-radius:8px;margin:8px 0;
                    text-align:center;transition:all 0.2s;font-size:1rem}
        .btn-accion:hover{background:#b71c1c;transform:translateY(-1px);box-shadow:0 4px 12px rgba(211,47,47,0.3)}
        .btn-secundario{display:inline-block;background:var(--accent2);color:#fff!important;padding:12px 24px;
                        text-decoration:none;font-weight:600;border-radius:8px;margin:8px 0;
                        text-align:center;transition:all 0.2s;font-size:0.95rem}
        .btn-secundario:hover{background:#0d47a1;transform:translateY(-1px)}
        .cta-box{margin:32px 0;padding:24px;border:1px solid var(--border);border-radius:8px;
                 text-align:center;background:var(--card)}
        .cta-box p{font-size:0.9rem;color:var(--dim);margin-bottom:12px}
        .faq-item{padding:16px 0;border-bottom:1px solid var(--border)}
        .faq-item:last-child{border-bottom:none}
        .faq-q{font-weight:600;color:var(--accent2);margin-bottom:6px;font-size:1rem}
        .faq-a{font-size:0.95rem;color:#555;line-height:1.6}
        footer{margin-top:48px;padding:20px 0;border-top:1px solid var(--border);text-align:center;font-size:0.75rem;color:var(--dim)}
        .badge{display:inline-block;font-size:0.65rem;color:var(--accent);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px}
        @media(max-width:600px){body{padding:16px 12px}h1{font-size:1.4rem}h2{font-size:1.1rem}}
"""
    
    def _build_faq_schema(self, faqs: List[Dict]) -> str:
        """Genera JSON-LD de FAQ Schema."""
        if not faqs:
            return ""
        items = []
        for faq in faqs:
            items.append(f'{{"@type":"Question","name":{json.dumps(faq["question"],ensure_ascii=False)},"acceptedAnswer":{{"@type":"Answer","text":{json.dumps(faq["answer"],ensure_ascii=False)}}}}}')
        schema = '{\n  "@context":"https://schema.org",\n  "@type":"FAQPage",\n  "mainEntity":[\n    ' + ',\n    '.join(items) + '\n  ]\n}'
        return schema
    
    def _build_article_schema(self, titulo: str, desc: str, niche: str, fecha: str, dominio: str = "TU_DOMINIO.vercel.app", slug: str = "") -> str:
        """Genera JSON-LD con Article Schema + BreadcrumbList en @graph."""
        slug_path = f"/posts/{slug}/" if slug else "/"
        schema = f"""{{
  "@context":"https://schema.org",
  "@graph":[
    {{
      "@type":"Article",
      "headline":{json.dumps(titulo, ensure_ascii=False)},
      "description":{json.dumps(desc, ensure_ascii=False)},
      "datePublished":"{fecha}",
      "dateModified":"{datetime.now().strftime('%Y-%m-%d')}",
      "author":{{"@type":"Person","name":"Shadow Del Valle R"}},
      "publisher":{{"@type":"Organization","name":"Shadow Del Valle R"}},
      "mainEntityOfPage":{{"@type":"WebPage","@id":"https://{dominio}{slug_path}"}}
    }},
    {{
      "@type":"BreadcrumbList",
      "itemListElement":[
        {{"@type":"ListItem","position":1,"name":"Inicio","item":"https://{dominio}/"}},
        {{"@type":"ListItem","position":2,"name":"Posts","item":"https://{dominio}{slug_path}"}}
      ]
    }}
  ]
}}"""
        return schema
    
    def convertir_a_html(self,
                         titulo: str,
                         nicho: str,
                         categoria: str,
                         cpc: float,
                         contenido_html: str,
                         meta_desc: str = "",
                         keywords: str = "",
                         faqs: Optional[List[Dict]] = None,
                         slug: str = "") -> str:
        """
        Convierte contenido a HTML estático completo.
        
        Args:
            titulo: Título del post
            nicho: Nombre del nicho
            categoria: Categoría del nicho
            cpc: CPC promedio
            contenido_html: Contenido en HTML (párrafos, listas, etc.)
            meta_desc: Meta description (opcional)
            keywords: Keywords separadas por coma (opcional)
            faqs: Lista de preguntas frecuentes (opcional)
            slug: Slug del post (opcional)
        
        Returns:
            str: HTML completo listo para deploy
        """
        fecha = datetime.now().strftime("%Y-%m-%d")
        meta = meta_desc or f"Guía completa sobre {nicho}. Información actualizada y verificada."
        kw = keywords or nicho
        dominio = self.config.get("refinery", {}).get("dominio", "TU_DOMINIO.vercel.app")
        
        if not slug:
            slug = titulo.lower().replace(" ", "-").replace(":", "").replace("?", "")[:60]
        
        monetag_head, monetag_body = self._build_monetag_script()
        css = self._build_css()
        
        faq_schema = ""
        faq_html = ""
        if faqs:
            faq_schema = self._build_faq_schema(faqs)
            faq_html = '\n'.join([
                f'        <div class="faq-item"><div class="faq-q">{f["question"]}</div><div class="faq-a">{f["answer"]}</div></div>'
                for f in faqs
            ])
        
        article_schema = self._build_article_schema(titulo, meta, nicho, fecha, dominio, slug)
        
        # Construir el HTML completo
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <meta name="description" content="{meta}">
    <meta name="keywords" content="{kw}">
    <meta name="robots" content="index, follow">
    <meta name="author" content="Shadow Del Valle R">
    
    <!-- Open Graph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{titulo}">
    <meta property="og:description" content="{meta}">
    <meta property="og:locale" content="es_ES">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{titulo}">
    <meta name="twitter:description" content="{meta}">
    
    <link rel="canonical" href="https://{dominio}/posts/{slug}/">
    
    <script type="application/ld+json">{article_schema}</script>
    {faq_schema and '<script type="application/ld+json">' + faq_schema + '</script>' or ''}
    
    <!-- Analytics: Shadow Del Valle R tracking -->
    <script defer>
        (function() {{
            var slug = '{slug}';
            var payload = JSON.stringify({{slug: slug, type: 'pageview'}});
            var payloadClick = JSON.stringify({{slug: slug, type: 'click'}});
            // Enviar pageview al cargar
            if (navigator.sendBeacon) {{
                navigator.sendBeacon('/api/track', payload);
            }} else {{
                var x = new XMLHttpRequest();
                x.open('POST', '/api/track', true);
                x.setRequestHeader('Content-Type', 'application/json');
                x.send(payload);
            }}
            // Tracking de clics en CTAs
            document.addEventListener('click', function(e) {{
                var btn = e.target.closest('.btn-accion, .btn-secundario');
                if (btn) {{
                    if (navigator.sendBeacon) {{
                        navigator.sendBeacon('/api/track', payloadClick);
                    }} else {{
                        var x2 = new XMLHttpRequest();
                        x2.open('POST', '/api/track', true);
                        x2.setRequestHeader('Content-Type', 'application/json');
                        x2.send(payloadClick);
                    }}
                }}
            }});
        }})();
    </script>
    
    <style>{css}</style>
    {monetag_head}
</head>
<body>

    <header>
        <div class="badge">🌑 SHADOW DEL VALLE R · {categoria.upper()}</div>
        <h1>{titulo}</h1>
        <div class="meta">
            <span>📂 {nicho}</span>
            <span>💰 CPC: ${cpc:.0f}</span>
            <span>📅 {fecha}</span>
        </div>
    </header>

    <main>
        {contenido_html}
    </main>

    {"<div class='faq-section'><h2>❓ Preguntas Frecuentes</h2>" + faq_html + "</div>" if faq_html else ""}

    <footer>
        <strong>🌑 Shadow Del Valle R</strong> &mdash; Ecosistema Privado de Contenido Premium<br>
        Generado por IA · {fecha} · {nicho}
    </footer>

    {monetag_body}
</body>
</html>"""
        return html
    
    def guardar_post(self, html: str, slug: str, output_dir: str = "output/posts") -> str:
        """
        Guarda el HTML como output/posts/slug/index.html
        (formato nativo de Cloudflare Pages para clean URLs).
        
        Args:
            html: Contenido HTML completo
            slug: Nombre del archivo (sin extensión)
            output_dir: Directorio de salida
        
        Returns:
            str: Ruta completa del archivo guardado
        """
        post_dir = os.path.join(output_dir, slug)
        os.makedirs(post_dir, exist_ok=True)
        filepath = os.path.join(post_dir, "index.html")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        
        self.posts_generados.append({
            "slug": slug,
            "filepath": filepath,
            "timestamp": time.time(),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tamano_bytes": len(html.encode('utf-8'))
        })
        
        return filepath
    
    def generar_sitemap(self, posts: List[Dict], output_path: str = "output/sitemap.xml") -> str:
        """
        Genera sitemap.xml para Google Search Console.
        
        Args:
            posts: Lista de posts con slug y timestamp
            output_path: Ruta de salida
        
        Returns:
            str: Ruta del sitemap generado
        """
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for post in posts:
            fecha = datetime.fromtimestamp(post.get("timestamp", time.time())).strftime("%Y-%m-%d")
            slug = post.get("slug", "post")
            dominio_base = self.config.get("refinery", {}).get("dominio", "TU_DOMINIO.vercel.app")
            xml += f"""  <url>
    <loc>https://{dominio_base}/posts/{slug}/</loc>
    <lastmod>{fecha}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>\n"""
        
        xml += '</urlset>'
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml)
        
        return output_path
    
    def get_estadisticas(self) -> Dict:
        """Retorna estadísticas del refinery."""
        total = len(self.posts_generados)
        tamano_total = sum(p.get("tamano_bytes", 0) for p in self.posts_generados)
        
        return {
            "total_posts_generados": total,
            "tamano_total_bytes": tamano_total,
            "tamano_promedio_bytes": round(tamano_total / total, 0) if total > 0 else 0,
            "ultimo_post": self.posts_generados[-1] if self.posts_generados else None
        }


# ─── Demo / Uso directo ───
if __name__ == "__main__":
    refinery = Refinery()
    
    print("=" * 60)
    print("  🔧 SHADOW DEL VALLE R — REFINERY MOTOR")
    print("=" * 60)
    
    # Contenido de ejemplo
    contenido = """
    <p>Si estás buscando información clara y directa sobre <strong>cómo proteger tus derechos después de un accidente</strong>, has llegado al lugar correcto. Vamos a desglosar todo lo que necesitas saber sin rodeos.</p>
    
    <div class="alerta-box">
        <div class="alerta-title">⚠️ ATENCIÓN IMPORTANTE:</div>
        <p>Las aseguradoras tienen equipos de ajustadores entrenados para minimizar los pagos. Todo lo que digas puede ser usado en tu contra. No des declaraciones grabadas sin asesoría legal.</p>
    </div>
    
    <h2>Pasos Inmediatos Después del Accidente</h2>
    <ol>
        <li><strong>Busca atención médica</strong> — aunque no sientas dolor, las lesiones pueden manifestarse horas después</li>
        <li><strong>Documenta la escena</strong> — fotos, videos, testigos, número de placas</li>
        <li><strong>No admitas culpa</strong> — ni siquiera disculpas educadas</li>
        <li><strong>Contacta a un abogado</strong> — antes de aceptar cualquier oferta</li>
    </ol>
    
    <div class="tip-box">
        <div class="alerta-title">💡 CONSEJO PRO:</div>
        <p>Las primeras 24 horas son críticas. Cuanto antes involucres a un profesional, más evidencia podrá preservarse para tu caso.</p>
    </div>
    
    <h2>¿Cuánto Vale tu Caso?</h2>
    <p>El valor depende de múltiples factores: gravedad de las lesiones, costos médicos, pérdida de ingresos, y el nivel de sufrimiento experimentado. Los casos con lesiones comprobables y documentación exhaustiva tienden a recibir compensaciones 3x más altas.</p>
    
    <ul>
        <li>Lesiones leves: <strong>$5,000 - $25,000</strong></li>
        <li>Lesiones moderadas: <strong>$25,000 - $100,000</strong></li>
        <li>Lesiones graves: <strong>$100,000 - $500,000+</strong></li>
    </ul>
    
    <div class="cta-box">
        <p>Tu consulta inicial es completamente gratuita y sin compromiso. Descubre si calificas para compensación.</p>
        <a href="#" class="btn-accion">Verificar mi Caso Ahora</a>
    </div>
    """
    
    html = refinery.convertir_a_html(
        titulo="Guía Completa: Qué Hacer Después de un Accidente de Tránsito [2026]",
        nicho="Abogados de Accidentes",
        categoria="Servicios Legales",
        cpc=220.0,
        contenido_html=contenido,
        meta_desc="Guía completa sobre qué hacer después de un accidente. Pasos legales, cómo calcular tu indemnización y cuándo contactar a un abogado.",
        keywords="accidente de tránsito, abogado de accidentes, indemnización, compensación, pasos legales",
        faqs=[
            {"question": "¿Cuánto tiempo tengo para demandar después de un accidente?", "answer": "El plazo de prescripción varía según el estado, pero generalmente es de 1 a 3 años desde la fecha del accidente."},
            {"question": "¿Cuánto cuesta una consulta con un abogado de accidentes?", "answer": "La mayoría de los abogados de lesiones personales ofrecen consultas iniciales completamente gratuitas. Trabajan bajo honorarios de contingencia."},
            {"question": "¿Qué pasa si el accidente fue parcialmente mi culpa?", "answer": "Depende del estado. En muchos estados con culpa comparativa, puedes recuperar compensación incluso si eres parcialmente responsable."}
        ],
        slug="guia-que-hacer-despues-accidente"
    )
    
    ruta = refinery.guardar_post(html, "guia-que-hacer-despues-accidente")
    print(f"\n✅ Post generado: {ruta}")
    print(f"📏 Tamaño: {len(html.encode('utf-8')):,} bytes")
    print(f"🚀 Listo para deploy en Vercel")

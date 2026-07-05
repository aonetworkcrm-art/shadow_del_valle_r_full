#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌑 Shadow Del Valle R — Generador de Contenido con IA
======================================================
Usa OpenRouter + prompts de FreeBuff Bridge para generar
contenido único, variado y optimizado para cada nicho.

Flujo:
    1. FreeBuff Bridge genera un prompt estructurado para el nicho
    2. OpenRouter genera contenido único basado en el prompt (con fallback chain)
    3. Se parsea la respuesta JSON (title, content, faqs)
    4. Si OpenRouter no está disponible, usa template de respaldo

Uso:
    generator = ContentGenerator()
    resultado = generator.generate_for_niche(nicho_dict)
    # resultado tiene: titulo, contenido_html, meta_desc, faqs, etc.
"""

import json
import os
import re
import sys
import time
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.freebuff_bridge import FreeBuffBridge
from api_openrouter import OpenRouterClient


# ─── System prompt experto SEO — Proyecto Infinito + Shadow Del Valle R ───
SYSTEM_PROMPT_COPY = """Eres un redactor SEO experto con 10 años de experiencia. Tu especialidad es el copywriting persuasivo que convierte visitantes en leads.

## REGLAS DE ORO:
1. NUNCA empieces con "Si estás buscando..." o "En el mundo actual..." — eso mata el CTR.
2. Primer párrafo: hook que pare el dedo. Una pregunta incómoda, una estadística que duela, una historia corta que el lector sienta propia.
3. Párrafos cortos (< 3 líneas). La gente escanea, no lee.
4. Tono: directo, honesto, sin rodeos. Como un amigo que te da la real. No corporativo, no robótico.
5. Incluye vocabulario relevante del nicho para demostrar autoridad.
6. Datos concretos > opiniones. Números, estadísticas, hechos.

## ESTRUCTURA DEL CONTENIDO (síguela al pie de la letra):
1. **HOOK** — Primer párrafo que engancha. Problema real que el lector reconoce al instante.
2. **PROBLEMA** — Describe el dolor exacto. Haz que diga "ESO MISMO ME PASÓ A MÍ".
3. **ALERTA** — <div class="alerta-box"> con datos impactantes o información crítica.
4. **SOLUCIÓN** — 2-3 párrafos de información útil. Pasos concretos, opciones reales.
5. **TIP** — <div class="tip-box"> con un consejo exclusivo que nadie más da.
6. **CIERRE** — Resumen y CTA claro.

## ELEMENTOS HTML REQUERIDOS:
- <strong> para palabras clave
- <ul> o <ol> para listas de pasos/items
- <div class="alerta-box"> para información crítica (obligatorio)
- <div class="tip-box"> para consejos exclusivos (obligatorio)
- <div class="cta-box"> con <a class="btn-accion"> al final (obligatorio)

## REQUISITOS TÉCNICOS:
- Título: máx 70 caracteres, incluye keyword principal + año
- Meta description: máx 160 caracteres, optimizada para CTR
- 3 FAQs que respondan objeciones reales, no preguntas genéricas
- Schema-ready: contenido estructurado y semántico

RESPONDE EXACTAMENTE EN ESTE FORMATO JSON (sin markdown, sin texto adicional):
{
  "title": "Título SEO aquí (max 70 chars)",
  "meta_description": "Meta description aquí (max 160 chars)",
  "content": "HTML completo del contenido aquí",
  "faqs": [
    {"question": "Pregunta real?",
     "answer": "Respuesta detallada que derriba una objeción"}
  ]
}"""


class ContentGenerator:
    """
    Generador de contenido que usa IA real (OpenRouter) con
    fallback chain de modelos y respaldo a templates.
    """
    
    def __init__(self):
        self.bridge = FreeBuffBridge()
        self.openrouter = OpenRouterClient()
        self.history: List[Dict] = []
    
    @property
    def is_ai_available(self) -> bool:
        """Verifica si la IA está disponible."""
        return self.openrouter.is_configured
    
    @property
    def transport(self) -> str:
        """Transporte activo de OpenRouter."""
        return self.openrouter.transport
    
    def generate_for_niche(self,
                          nicho: Dict,
                          preferred_model: Optional[str] = None) -> Dict:
        """
        Genera contenido para un nicho usando OpenRouter + FreeBuff.
        
        Args:
            nicho: Dict con datos del nicho (de NICHOS_DB o Radar)
                Requiere: id, name, category, cpc_avg, tags, language
            preferred_model: Modelo preferido para esta generación
        
        Returns:
            Dict con: titulo, contenido_html, meta_desc, faqs, slug, etc.
        """
        nicho_id = nicho.get("id", "unknown")
        nicho_name = nicho.get("name", "Nicho")
        category = nicho.get("category", "General")
        cpc = nicho.get("cpc_avg", 0)
        keywords = nicho.get("tags", [nicho_name])
        language = nicho.get("language", "es")
        
        print(f"  🎯 Generando contenido para: {nicho_name}")
        if preferred_model:
            print(f"     🤖 Modelo preferido: {preferred_model}")
        print(f"     🚚 Transporte: {self.transport}")
        
        # 1. Construir prompt vía FreeBuff Bridge
        prompt_data = self.bridge.generar_prompt_post(
            nicho_id=nicho_id,
            nicho_nombre=nicho_name,
            categoria=category,
            cpc=cpc,
            keywords=keywords,
            idioma=language
        )
        prompt = prompt_data["prompt"]
        
        # 2. Intentar con OpenRouter (IA real) con fallback chain
        resultado = self._try_openrouter(prompt, nicho, prompt_data, preferred_model)
        if resultado:
            return resultado
        
        # 3. Fallback a template
        print(f"     ⚠️ Usando template de respaldo")
        resultado = self._fallback_template(nicho)
        self.history.append({
            "nicho": nicho_name,
            "source": "template",
            "timestamp": time.time(),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return resultado
    
    def _try_openrouter(self,
                       prompt: str,
                       nicho: Dict,
                       prompt_data: Dict,
                       preferred_model: Optional[str] = None) -> Optional[Dict]:
        """
        Intenta generar contenido con OpenRouter (fallback chain automático).
        Retorna None si falla (para usar fallback).
        """
        if not self.openrouter.is_configured:
            print(f"     ⚠️ OpenRouter no configurado (sin API key)")
            return None
        
        try:
            response = self.openrouter.generate_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_COPY,
                temperature=0.7,
                preferred_model=preferred_model
            )
            
            if response and self._validate_response(response):
                resultado = self._build_result(response, nicho, prompt_data)
                model_used = self.openrouter.last_model_used or "unknown"
                
                self.history.append({
                    "nicho": nicho.get("name", ""),
                    "source": "openrouter",
                    "model": model_used,
                    "transport": self.transport,
                    "tokens": self.openrouter.total_tokens_used,
                    "cost": self.openrouter.total_cost,
                    "timestamp": time.time(),
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                print(f"     ✅ Contenido generado con {model_used}")
                print(f"     🚚 Transporte: {self.transport}")
                print(f"     💰 Costo: ${self.openrouter.total_cost:.6f}")
                return resultado
            
            error = self.openrouter.last_error or "Respuesta inválida"
            print(f"     ⚠️ OpenRouter falló: {error[:120]}")
                
        except Exception as e:
            print(f"     ⚠️ Error OpenRouter: {str(e)[:120]}")
        
        return None
    
    def _validate_response(self, data: Dict) -> bool:
        """Valida que la respuesta tenga todos los campos requeridos."""
        required = ["title", "content", "faqs"]
        if not all(k in data for k in required):
            return False
        if not data["title"] or not data["content"]:
            return False
        if not isinstance(data.get("faqs"), list) or len(data["faqs"]) < 1:
            return False
        if len(data["title"]) > 120:  # Título muy largo, truncar
            data["title"] = data["title"][:117] + "..."
        return True
    
    def _build_result(self, response: Dict, nicho: Dict, prompt_data: Dict) -> Dict:
        """Construye el resultado estructurado desde la respuesta de OpenRouter."""
        titulo = response.get("title", prompt_data.get("nicho_nombre", ""))
        contenido = response.get("content", "")
        meta_desc = response.get("meta_description", "")
        faqs = response.get("faqs", [])
        
        # Asegurar que el contenido HTML tenga los elementos requeridos
        contenido = self._ensure_html_elements(contenido, nicho)
        
        return {
            "titulo": titulo,
            "contenido_html": contenido,
            "meta_desc": meta_desc[:160] if meta_desc else f"Guía completa sobre {nicho.get('name', '')}. Información actualizada y verif.",
            "faqs": faqs[:5],  # Máximo 5 FAQs
            "nicho": prompt_data["nicho_nombre"],
            "categoria": prompt_data["categoria"],
            "cpc": prompt_data["cpc"],
            "keywords": ", ".join(prompt_data.get("keywords", [])),
            "slug": self._slugify(titulo),
            "source": "openrouter",
            "model": self.openrouter.last_model_used or "unknown",
            "transport": self.transport,
        }
    
    def _ensure_html_elements(self, html: str, nicho: Dict) -> str:
        """
        Asegura que el HTML tenga los elementos mínimos requeridos:
        - Al menos un <div class="alerta-box">
        - Un CTA al final
        """
        if '<div class="alerta-box"' not in html:
            alerta = f"""
    <div class="alerta-box">
        <div class="alerta-title">⚠️ LO QUE DEBES SABER:</div>
        <p>La informacion que sigue puede marcar la diferencia en tu caso. No es exageracion — son datos verificados que la mayoria de la gente ignora hasta que es demasiado tarde.</p>
    </div>"""
            html = html.replace("</h2>", "</h2>" + alerta, 1) if "</h2>" in html else html + alerta
        
        if '<div class="tip-box"' not in html:
            tip = f"""
    <div class="tip-box">
        <div class="alerta-title">💡 CONSEJO PRO:</div>
        <p>La diferencia entre los que logran resultados y los que no, no es la suerte — es la informacion correcta aplicada en el momento correcto.</p>
    </div>"""
            html = html.replace("</h2>", "</h2>" + tip, 1) if "</h2>" in html else html + tip
        
        if '<div class="cta-box"' not in html:
            cta = f"""
    <div class="cta-box">
        <p>💡 <strong>IMPORTANTE:</strong> Para que los enlaces funcionen correctamente, permite ventanas emergentes (popups) para este sitio en tu navegador. Es rapido y seguro.</p>
        <a href="#" class="btn-accion">👉 Verifica si Calificas Ahora — Es Gratis</a>
    </div>"""
            html += cta
        
        return html
    
    def _fallback_template(self, nicho: Dict) -> Dict:
        """
        Genera contenido template cuando OpenRouter no está disponible.
        El template varía ligeramente según el nicho para no ser idéntico.
        """
        import random
        
        nicho_name = nicho.get("name", "Nicho")
        category = nicho.get("category", "General")
        cpc = nicho.get("cpc_avg", 0)
        tags = nicho.get("tags", [nicho_name])
        topic = random.choice(tags)
        
        # Variar el template según el nicho para no ser completamente repetitivo
        templates = [
            {
                "hook": f"<p>Vamos directo al grano con <strong>{topic}</strong>: esto es lo que realmente necesitas saber, sin filtros y sin informacion que no te sirva.</p>",
                "alerta": f"<p>La mayoria de la gente pierde oportunidades en esto simplemente porque no conoce los pasos correctos desde el principio. Tu ya estas un paso adelante solo por estar aqui.</p>",
            },
            {
                "hook": f"<p>Si hay algo que he aprendido sobre <strong>{topic}</strong> es que la informacion correcta en el momento correcto puede ahorrarte cientos de dolares y horas de frustracion. Y eso es justo lo que vas a encontrar aqui.</p>",
                "alerta": f"<p>El problema no es que la informacion no exista — es que hay demasiada y la mayoria es basura. Aca te doy solo lo que sirve, lo que realmente funciona.</p>",
            },
            {
                "hook": f"<p>Te voy a ser honesto: cuando se trata de <strong>{topic}</strong>, el 90% de lo que lees en internet es relleno. Esto no. Esto es lo que realmente importa.</p>",
                "alerta": f"<p>He visto a demasiadas personas tomar decisiones basadas en informacion incompleta y terminar pagando el doble de lo que debian. No seas una de ellas.</p>",
            },
        ]
        
        t = random.choice(templates)
        titulo = f"Todo lo que Necesitas Saber sobre {topic} [2026]"
        
        # Elegir aleatoriamente entre variantes de estructura
        estructura_variante = random.choice(["pasos", "puntos", "preguntas"])
        
        if estructura_variante == "pasos":
            cuerpo = f"""
    <h2>Pasos Concretos para Hoy</h2>
    <ol>
        <li><strong>Identifica tu situacion</strong> — cada caso es unico. Entiende el tuyo antes de comparar opciones</li>
        <li><strong>Investiga con criterio</strong> — no te guies solo por el precio. Mira resultados, reputacion, tiempo en el mercado</li>
        <li><strong>Toma accion</strong> — la informacion sin accion no sirve de nada. El mejor momento para empezar es ahora</li>
    </ol>"""
        elif estructura_variante == "puntos":
            cuerpo = f"""
    <h2>Lo Que Realmente Importa</h2>
    <ul>
        <li><strong>El conocimiento es poder</strong> — pero solo si lo usas. La gente que mejor le va no es la mas inteligente, es la que actua</li>
        <li><strong>No todo lo que brilla es oro</strong> — especialmente en {nicho_name.lower()}. Saber diferenciar lo real de lo falso es clave</li>
        <li><strong>El tiempo es tu recurso mas valioso</strong> — no lo gastes en informacion que no te sirve. Ve directo a lo que necesitas</li>
    </ul>"""
        else:
            cuerpo = f"""
    <h2>Las Preguntas que Todos se Hacen</h2>
    <p>Antes de empezar, seguro te estas preguntando: ¿por donde empiezo? ¿cuanto cuesta? ¿vale la pena? Son preguntas validas y las vamos a responder una por una.</p>
    
    <p>La respuesta corta es: si, vale la pena. Pero no te quedes con la respuesta corta — la diferencia entre los que tienen exito y los que no, esta en los detalles.</p>"""
        
        contenido = f"""
    {t["hook"]}
    
    <div class="alerta-box">
        <div class="alerta-title">⚠️ ATENCION:</div>
        {t["alerta"]}
    </div>
    
    {cuerpo}
    
    <div class="tip-box">
        <div class="alerta-title">💡 CONSEJO:</div>
        <p>La diferencia entre los que logran resultados y los que no, no es la suerte — es la informacion correcta aplicada en el momento correcto. Ya tienes la informacion. El resto depende de ti.</p>
    </div>
    
    <div class="cta-box">
        <p>💡 <strong>IMPORTANTE:</strong> Para acceder a todos los recursos y herramientas, asegurate de permitir ventanas emergentes para este sitio en tu navegador.</p>
        <a href="#" class="btn-accion">👉 Verifica si Calificas — Es Gratis</a>
    </div>
    """
        
        faqs = [
            {"question": f"¿Que es exactamente {topic}?", 
             "answer": f"Es un tema que genera muchas dudas y desinformacion. Esta guia te da la informacion clara y directa que necesitas para tomar decisiones informadas."},
            {"question": f"¿Cuanto cuesta?",
             "answer": "Los costos varian segun el proveedor, la ubicacion y la complejidad de tu caso. Te recomendamos solicitar cotizaciones personalizadas para obtener precios exactos."},
            {"question": "¿Vale la pena?",
             "answer": "Absolutamente. La mayoria de las personas que invierten tiempo en informarse correctamente terminan ahorrando dinero y evitando problemas a largo plazo."}
        ]
        
        return {
            "titulo": titulo,
            "contenido_html": contenido,
            "meta_desc": f"Guia completa sobre {topic}. Informacion actualizada, pasos practicos y recursos utiles para tomar la mejor decision.",
            "faqs": faqs,
            "nicho": nicho_name,
            "categoria": category,
            "cpc": cpc,
            "keywords": ", ".join(tags),
            "slug": self._slugify(titulo),
            "source": "template",
            "model": "template",
            "transport": "template",
        }
    
    def _slugify(self, text: str) -> str:
        """Convierte texto a slug URL-friendly."""
        slug = text.lower().strip()
        # Reemplazar caracteres especiales
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
            "ñ": "n", "ü": "u", "Á": "a", "É": "e", "Í": "i",
            "Ó": "o", "Ú": "u", "Ñ": "n"
        }
        for old, new in replacements.items():
            slug = slug.replace(old, new)
        slug = re.sub(r'[^a-z0-9\-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')[:60]
        return slug or f"post-{int(time.time())}"
    
    def get_stats(self) -> Dict:
        """Estadísticas del generador."""
        total = len(self.history)
        ai_count = sum(1 for h in self.history if h["source"] == "openrouter")
        template_count = total - ai_count
        
        ai_stats = {}
        if self.openrouter.is_configured:
            ai_stats = self.openrouter.get_usage_stats()
        
        return {
            "total_generados": total,
            "con_ia": ai_count,
            "con_template": template_count,
            "openrouter_configurado": self.is_ai_available,
            "transporte": self.transport,
            "ultimo_modelo": self.openrouter.last_model_used,
            "stats_openrouter": ai_stats,
            "ultimos": self.history[-5:] if self.history else []
        }


# ─── Demo / Uso directo ───
if __name__ == "__main__":
    generator = ContentGenerator()
    
    print("=" * 60)
    print("  🎯 SHADOW DEL VALLE R — GENERADOR DE CONTENIDO v2")
    print("  🤖 OpenRouter IA + Fallback Chain + Templates")
    print("=" * 60)
    
    if generator.is_ai_available:
        print(f"  ✅ OpenRouter configurado — contenido REAL con IA")
        print(f"  🚚 Transporte: {generator.transport}")
        print(f"  🤖 Modelo: {generator.openrouter.model}")
        print(f"  🔄 Fallback: {generator.openrouter.fallback_model}")
    else:
        print(f"  ⚠️  OpenRouter NO configurado — usando templates")
        print(f"  Para activar IA, configura api_key en config/settings.json")
    
    print()
    
    # Demo con un nicho
    try:
        from core.radar import NICHOS_DB
        nicho = NICHOS_DB[0]  # Abogados de Accidentes
        
        print(f"  Demo con: {nicho['name']} (CPC: ${nicho['cpc_avg']:.0f})")
        print()
        
        resultado = generator.generate_for_niche(nicho)
        
        print(f"\n  📝 Titulo: {resultado['titulo'][:70]}")
        print(f"  🔍 Fuente: {resultado['source']}")
        print(f"  🤖 Modelo: {resultado.get('model', 'N/A')}")
        print(f"  🚚 Transporte: {resultado.get('transport', 'N/A')}")
        print(f"  📏 Contenido: {len(resultado['contenido_html'])} chars")
        print(f"  ❓ FAQs: {len(resultado['faqs'])}")
        print(f"  🔗 Slug: {resultado['slug']}")
        
        stats = generator.get_stats()
        print(f"\n  📊 Stats: {stats['total_generados']} generados ({stats['con_ia']} IA, {stats['con_template']} template)")
        if stats.get('stats_openrouter'):
            ors = stats['stats_openrouter']
            print(f"     ⚡ Llamadas: {ors.get('llamadas_totales', 0)} | Tokens: {ors.get('tokens_consumidos', 0)}")
            print(f"     💰 Costo: ${ors.get('costo_total_usd', 0):.6f}")
    except ImportError:
        print("  ℹ️ Ejecuta el demo desde la carpeta shadow_del_valle_r/")
    
    print(f"\n{'=' * 60}")

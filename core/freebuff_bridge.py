# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Motor 4: FreeBuff Bridge
===============================================
Puente de comunicación con FreeBuff (Codebuff en VS Code).
Genera prompts estructurados para copywriting emotivo/humano
y recibe el contenido generado para procesarlo.

Estilo: Claude empático, directo, sin rodeos, "con to' lo' muñequito'".
"""

import json
import os
import random
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class FreeBuffBridge:
    """
    Puente que conecta el Radar + Refinery con FreeBuff.
    Genera prompts estructurados para que FreeBuff redacte
    el copy emotivo que convierte.
    """
    
    def __init__(self, config_path: str = "config/templates_copy.json"):
        self.plantillas = self._load_templates(config_path)
        self.historial_prompts: List[Dict] = []
    
    def _load_templates(self, path: str) -> Dict:
        """Carga plantillas de copywriting."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _get_gancho(self, nicho_id: str) -> str:
        """Obtiene el gancho psicológico para un nicho."""
        nichos = self.plantillas.get("nichos", {})
        nicho = nichos.get(nicho_id, {})
        return nicho.get("gancho", "¿Necesitas información confiable y directa? Has llegado al lugar correcto.")
    
    def _get_cta(self, nicho_id: str) -> str:
        """Obtiene el call-to-action para un nicho."""
        nichos = self.plantillas.get("nichos", {})
        nicho = nichos.get(nicho_id, {})
        return nicho.get("cta", "Consulta gratuita — Sin compromiso")
    
    def _get_palabras_poder(self, nicho_id: str) -> List[str]:
        """Obtiene palabras de poder para un nicho."""
        nichos = self.plantillas.get("nichos", {})
        nicho = nichos.get(nicho_id, {})
        return nicho.get("palabras_poder", ["solución", "inmediato", "gratis", "garantizado"])
    
    def generar_prompt_post(self,
                           nicho_id: str,
                           nicho_nombre: str,
                           categoria: str,
                           cpc: float,
                           keywords: List[str],
                           idioma: str = "es") -> Dict:
        """
        Genera un prompt estructurado para FreeBuff.
        
        Args:
            nicho_id: ID del nicho
            nicho_nombre: Nombre del nicho
            categoria: Categoría del nicho
            cpc: Costo por clic
            keywords: Palabras clave principales
            idioma: Idioma del contenido
        
        Returns:
            Dict con el prompt y metadatos
        """
        gancho = self._get_gancho(nicho_id)
        cta = self._get_cta(nicho_id)
        palabras_poder = self._get_palabras_poder(nicho_id)
        
        kw_str = ", ".join(keywords[:5])
        lang_instr = "Responde en espanol." if idioma == "es" else "Answer in English."
        palabras_str = ", ".join(palabras_poder)
        
        # Construir el prompt con tono Claude-humano y embudo de copy
        prompt = (
            f"[INSTRUCCION] {lang_instr}\n\n"
            f"Eres un redactor con alma de cuentacuentos. Escribes como un amigo que se sienta "
            f"en la mesa del frente y te dice: 'Mira, te voy a ser sincero...'. Nada de: "
            f"'Si estás buscando información clara y directa...' — esa mierda ya la vio mil veces.\n\n"
            f"Tu tono: natural, conversacional, de la calle. Como si hablaras con un conocido. "
            f"Usas contracciones ('pa', 'tamos', 'tá bien'), preguntas retóricas, y de vez en "
            f"cuando una jerga que pegue con el contexto. No eres un académico, eres el amigo "
            f"que sabe del tema y te da la real.\n\n"
            f"NICHO: {nicho_nombre}\n"
            f"CATEGORIA: {categoria}\n"
            f"CPC PROMEDIO: ${cpc:.0f} USD\n"
            f"KEYWORDS PRINCIPALES: {kw_str}\n\n"
            f"GANCHO EMOCIONAL (primeros 2 parrafos, lo mas importante):\n{gancho}\n\n"
            f"ESTRUCTURA DEL EMBUDO DE COPY (síguelo al pie de la letra):\n"
            f"1. HOOK — Arranca con una frase que pare el dedo. Una pregunta incomoda, una "
            f"   estadística que duela, una historia corta que el lector sienta propia. NO empieces "
            f"   con 'Si estás buscando...' o 'En este articulo...'.\n"
            f"2. PROBLEMA — Describe el dolor exacto que siente tu lector. Haz que diga 'ESO MISMO "
            f"   ME PASO A MI'. Usa sus mismas palabras, sus miedos, sus dudas.\n"
            f"3. AGITACIÓN — Explica por qué ignorar esto le va a costar caro. No asustes, solo "
            f"   hazle ver la realidad de lo que pasa si no actúa.\n"
            f"4. SOLUCIÓN — Aquí entras tú con la info útil. Pasos concretos, opciones reales, "
            f"   datos que le sirvan. Usa <ul>, <ol>, <div class='alerta-box'>, <div class='tip-box'>.\n"
            f"5. PRUEBA SOCIAL — 'Miles de personas ya...', 'Los casos mejor documentados reciben...'.\n"
            f"6. OBJECIONES — Anticipa las excusas mentales y respondelas: 'No tengo tiempo', "
            f"   'No me van a hacer caso', 'Seguro es caro...'. Derríbalas una por una.\n"
            f"7. CALL TO ACTION — {cta}\n"
            f"\n"
            f"REGLAS DE ORO:\n"
            f"- Siempre <p> para parrafos, <strong> para palabras clave\n"
            f"- Una alerta visual (<div class='alerta-box'>) para info critica\n"
            f"- Un tip (<div class='tip-box'>) con un consejo que nadie mas te da\n"
            f"- Listas (<ul> o <ol>) para pasos o items clave\n"
            f"- CTA al final con <div class='cta-box'> y <a href='#' class='btn-accion'>\n"
            f"- 3 FAQs que respondan objeciones reales\n"
            f"- Palabras de poder: {palabras_str}\n"
            f"- Titulo SEO max 70 caracteres\n"
            f"- Meta description max 160 caracteres\n"
            f"- NO empieces con 'Si estás buscando...' ni 'En este articulo...'\n"
            f"- Suena a humano, no a chatbot. Usa preguntas retoricas, emocion, calle.\n"
            f"- Si el nicho es en espanol, incluye expresiones latinas/caribenas que suenen naturales\n"
            f"\n"
            "RESPONDE EXACTAMENTE EN ESTE FORMATO JSON (sin markdown):\n"
            '{\n'
            '  "title": "Titulo SEO del articulo (max 70 chars)",\n'
            '  "meta_description": "Meta description (max 160 chars)",\n'
            '  "content": "HTML completo del contenido aqui",\n'
            '  "faqs": [\n'
            '    {"question": "Pregunta 1?", "answer": "Respuesta 1"},\n'
            '    {"question": "Pregunta 2?", "answer": "Respuesta 2"},\n'
            '    {"question": "Pregunta 3?", "answer": "Respuesta 3"}\n'
            '  ]\n'
            '}\n'
            'IMPORTANTE: Solo responde con el JSON. Sin texto adicional. Sin marcas de agua.'
        )
        
        prompt_data = {
            "nicho_id": nicho_id,
            "nicho_nombre": nicho_nombre,
            "categoria": categoria,
            "cpc": cpc,
            "keywords": keywords,
            "idioma": idioma,
            "prompt": prompt,
            "timestamp": time.time(),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.historial_prompts.append(prompt_data)
        
        return prompt_data
    
    def generar_prompt_bulk(self, nichos: List[Dict]) -> List[Dict]:
        """Genera prompts para múltiples nichos."""
        return [
            self.generar_prompt_post(
                nicho_id=n["id"],
                nicho_nombre=n["name"],
                categoria=n.get("category", "General"),
                cpc=n.get("cpc_avg", 100),
                keywords=n.get("tags", [n["name"]]),
                idioma=n.get("language", "es")
            )
            for n in nichos
        ]
    
    def procesar_respuesta(self, respuesta_json: Dict, prompt_original: Dict) -> Dict:
        """
        Procesa la respuesta de FreeBuff y la prepara para el Refinery.
        
        Args:
            respuesta_json: JSON con title, content, faqs
            prompt_original: El prompt que se envió
        
        Returns:
            Dict listo para pasar a Refinery.convertir_a_html()
        """
        return {
            "titulo": respuesta_json.get("title", prompt_original.get("nicho_nombre", "")),
            "contenido_html": respuesta_json.get("content", ""),
            "meta_desc": respuesta_json.get("meta_description", ""),
            "faqs": respuesta_json.get("faqs", []),
            "nicho": prompt_original.get("nicho_nombre", ""),
            "nicho_id": prompt_original.get("nicho_id", ""),
            "categoria": prompt_original.get("categoria", "General"),
            "cpc": prompt_original.get("cpc", 0),
            "keywords": ", ".join(prompt_original.get("keywords", [])),
            "timestamp": time.time()
        }
    
    def get_estadisticas(self) -> Dict:
        """Retorna estadísticas del bridge."""
        return {
            "total_prompts_generados": len(self.historial_prompts),
            "ultimo_prompt": self.historial_prompts[-1]["nicho_nombre"] if self.historial_prompts else None,
            "ultima_fecha": self.historial_prompts[-1]["fecha"] if self.historial_prompts else None
        }


# ─── Demo ───
if __name__ == "__main__":
    bridge = FreeBuffBridge()
    
    print("=" * 60)
    print("  🌉 SHADOW DEL VALLE R — FREEBUFF BRIDGE")
    print("=" * 60)
    
    prompt = bridge.generar_prompt_post(
        nicho_id="personal-injury-law",
        nicho_nombre="Abogados de Accidentes",
        categoria="Servicios Legales",
        cpc=220.0,
        keywords=["abogado de accidentes", "indemnización", "compensación", "lesiones personales"],
        idioma="es"
    )
    
    print(f"\n✅ Prompt generado para: {prompt['nicho_nombre']}")
    print(f"   CPC: ${prompt['cpc']:.0f}")
    print(f"   Longitud del prompt: {len(prompt['prompt']):,} caracteres")
    print(f"   Listo para enviar a FreeBuff")

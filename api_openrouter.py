#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌑 Shadow Del Valle R — OpenRouter API Client
==============================================
Cliente robusto para la API de OpenRouter (compatible con OpenAI).
Genera contenido variado y único para cada nicho.

Uso:
    client = OpenRouterClient()
    if client.is_configured:
        respuesta = client.generate(prompt, system_prompt)
    
Configuración en config/settings.json:
    "openrouter": {
        "api_key": "sk-or-v1-...",
        "modelo": "google/gemini-2.0-flash-lite-preview",
        "max_tokens": 2048,
        "temperatura": 0.7
    }
"""

import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Dict, List
from datetime import datetime


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS = "https://openrouter.ai/api/v1/models"


class OpenRouterClient:
    """
    Cliente para la API de OpenRouter.
    
    Características:
        - Llamadas a cualquier modelo de OpenRouter
        - Tracking de tokens y costo
        - Timeout configurable
        - Manejo de errores HTTP
        - Historial de llamadas
    """
    
    # Costos por modelo (USD por 1M tokens) — actualizado Junio 2026
    MODEL_COSTS = {
        "google/gemini-2.0-flash-lite-preview": {"input": 0.075, "output": 0.30},
        "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        "meta-llama/llama-3.3-70b-instruct": {"input": 0.25, "output": 0.25},
        "mistralai/mistral-small-24b-instruct-2501": {"input": 0.10, "output": 0.30},
        "default": {"input": 0.20, "output": 0.40},
    }
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        Inicializa el cliente con configuración de settings.json.
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        config = self._load_config(config_path)
        or_config = config.get("openrouter", {})
        
        self.api_key = or_config.get("api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = or_config.get("modelo", "google/gemini-2.0-flash-lite-preview")
        self.max_tokens = int(or_config.get("max_tokens", 2048))
        self.temperature = float(or_config.get("temperatura", 0.7))
        
        # Estadísticas de uso
        self.total_tokens_used = 0
        self.total_calls = 0
        self.total_cost = 0.0
        self.call_history: List[Dict] = []
        self.last_error: Optional[str] = None
        
        # Cache de modelos disponibles
        self._available_models: Optional[List[str]] = None
    
    def _load_config(self, path: str) -> Dict:
        """Carga configuración desde JSON."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    @property
    def is_configured(self) -> bool:
        """Verifica si hay API key configurada."""
        return bool(self.api_key) and len(self.api_key) > 10
    
    def _get_model_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calcula el costo estimado de una llamada."""
        costs = self.MODEL_COSTS.get(self.model, self.MODEL_COSTS["default"])
        cost = (tokens_input * costs["input"] / 1_000_000) + \
               (tokens_output * costs["output"] / 1_000_000)
        return round(cost, 6)
    
    def generate(self, 
                 prompt: str, 
                 system_prompt: Optional[str] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 timeout: int = 90) -> Optional[str]:
        """
        Envía un prompt a OpenRouter y obtiene la respuesta.
        
        Args:
            prompt: El prompt principal del usuario
            system_prompt: Prompt de sistema (opcional)
            temperature: Temperatura (override de config)
            max_tokens: Máximo de tokens (override de config)
            timeout: Timeout en segundos
        
        Returns:
            str con la respuesta, o None si hay error
        """
        if not self.is_configured:
            self.last_error = "API key no configurada"
            return None
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }).encode("utf-8")
        
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://shadow-del-valle-r.vercel.app",
                "X-Title": "Shadow Del Valle R",
            },
            method="POST"
        )
        
        start = time.time()
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                elapsed = round(time.time() - start, 2)
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
                
                self.total_calls += 1
                
                # Extraer uso de tokens
                usage = data.get("usage", {})
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)
                tokens_total = usage.get("total_tokens", tokens_input + tokens_output)
                self.total_tokens_used += tokens_total
                
                # Calcular costo
                cost = self._get_model_cost(tokens_input, tokens_output)
                self.total_cost += cost
                
                # Extraer contenido
                choices = data.get("choices", [])
                if not choices:
                    self.last_error = "Respuesta vacía de OpenRouter"
                    return None
                
                content = choices[0].get("message", {}).get("content", "")
                
                # Registrar en historial
                self.call_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "model": self.model,
                    "tokens": tokens_total,
                    "cost": cost,
                    "elapsed": elapsed,
                    "response_length": len(content),
                })
                
                return content
                
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")[:300]
            self.last_error = f"HTTP {e.code}: {body}"
            return None
            
        except urllib.error.URLError as e:
            self.last_error = f"Timeout/Connection: {str(e.reason)[:100]}"
            return None
            
        except Exception as e:
            self.last_error = f"Error: {str(e)[:200]}"
            return None
    
    def generate_json(self, 
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None) -> Optional[Dict]:
        """
        Envía un prompt y espera una respuesta JSON válida.
        
        Args:
            prompt: Prompt que debe generar JSON
            system_prompt: Prompt de sistema
        
        Returns:
            Dict con el JSON parseado, o None si falla
        """
        full_prompt = (
            prompt + "\n\n"
            "IMPORTANTE: Responde ÚNICAMENTE con el objeto JSON. "
            "Sin markdown, sin texto adicional, sin comillas al inicio/final."
        )
        
        sys = system_prompt or "Eres un asistente que responde solo con JSON válido."
        
        response = self.generate(
            prompt=full_prompt,
            system_prompt=sys,
            temperature=temperature or 0.3  # Más bajo para JSON preciso
        )
        
        if not response:
            return None
        
        # Limpiar la respuesta
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3].strip()
        
        # Intentar parsear JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Buscar JSON en el texto
            import re
            # Encontrar el primer { ... } o [ ... ] que sea JSON válido
            for pattern in [r'(\{.*\})', r'(\[.*\])']:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        continue
            return None
    
    def get_usage_stats(self) -> Dict:
        """Retorna estadísticas de uso de la API."""
        return {
            "configurado": self.is_configured,
            "modelo": self.model,
            "llamadas_totales": self.total_calls,
            "tokens_consumidos": self.total_tokens_used,
            "costo_total_usd": round(self.total_cost, 6),
            "ultimo_error": self.last_error,
            "historial_reciente": self.call_history[-5:] if self.call_history else []
        }


# ─── Demo / Uso directo ───
if __name__ == "__main__":
    client = OpenRouterClient()
    
    print("=" * 60)
    print("  🌐 SHADOW DEL VALLE R — OPENROUTER CLIENT")
    print("=" * 60)
    
    if client.is_configured:
        print(f"\n  ✅ API Key configurada")
        print(f"  🤖 Modelo: {client.model}")
        print(f"  📊 Tokens máx: {client.max_tokens}")
        print(f"  🌡️  Temperatura: {client.temperature}")
        
        # Test rápido
        print("\n  🧪 Probando conexión...")
        response = client.generate(
            prompt="Responde solo 'OK' si funcionas correctamente.",
            max_tokens=10
        )
        if response:
            print(f"  ✅ Respuesta: {response.strip()}")
            print(f"  💰 Costo: ${client.total_cost:.6f}")
        else:
            print(f"  ❌ Error: {client.last_error}")
    else:
        print(f"\n  ⚠️  API Key NO configurada")
        print(f"  Agrega tu API key en config/settings.json:")
        print(f'    "openrouter": {{"api_key": "sk-or-v1-..."}}')
        print(f"  O en variable de entorno: OPENROUTER_API_KEY")
        print()
        print(f"  📝 Modo DEMO activado — se usarán templates de respaldo")
    
    print(f"\n{'=' * 60}")

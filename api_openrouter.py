#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌑 Shadow Del Valle R — OpenRouter API Client (Enhanced)
=========================================================
Cliente robusto para OpenRouter con:
  - OpenAI SDK como transporte primario (más confiable, streaming)
  - Fallback a urllib si openai no está instalado
  - Cadena de fallback de modelos: primary → fallback → cheap
  - Exponential backoff en reintentos
  - Tracking de tokens y costos por modelo

Uso:
    client = OpenRouterClient()
    if client.is_configured:
        respuesta = client.generate(prompt, system_prompt)

Configuración en config/settings.json:
    "openrouter": {
        "api_key": "sk-or-v1-...",
        "modelo": "google/gemini-2.0-flash-lite-preview",
        "fallback_modelo": "google/gemini-2.0-flash-001",
        "cheap_modelo": "mistralai/mistral-small-24b-instruct-2501",
        "max_tokens": 2048,
        "temperatura": 0.7
    }
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Optional, Dict, List, Any
from datetime import datetime


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS = "https://openrouter.ai/api/v1/models"


class OpenRouterError(Exception):
    """Error base de OpenRouter."""
    pass

class ConfigError(OpenRouterError):
    """Error de configuración (API key faltante, etc.)."""
    pass

class ModelError(OpenRouterError):
    """Error del modelo (rate limit, timeout, etc.)."""
    pass

class ParseError(OpenRouterError):
    """Error parseando la respuesta."""
    pass


class OpenRouterClient:
    """
    Cliente para la API de OpenRouter con soporte multi-transporte.
    
    Características:
        - OpenAI SDK como transporte preferido (más confiable)
        - Fallback automático a urllib si openai no está instalado
        - Cadena de fallback de modelos (primary → fallback → cheap)
        - Exponential backoff (1s, 2s, 4s) en errores recuperables
        - Tracking de tokens y costo por modelo
        - Historial de llamadas
    """
    
    # Costos por modelo (USD por 1M tokens) — actualizado Junio 2026
    MODEL_COSTS = {
        "google/gemini-2.0-flash-lite-preview": {"input": 0.075, "output": 0.30},
        "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
        "google/gemini-2.5-flash-preview-04-17": {"input": 0.15, "output": 0.60},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "openai/gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        "meta-llama/llama-3.3-70b-instruct": {"input": 0.25, "output": 0.25},
        "mistralai/mistral-small-24b-instruct-2501": {"input": 0.10, "output": 0.30},
        "default": {"input": 0.20, "output": 0.40},
    }
    
    # Cadena de modelos de respaldo (de más capaz a más barato)
    FALLBACK_CHAIN = [
        "google/gemini-2.0-flash-lite-preview",
        "google/gemini-2.0-flash-001",
        "google/gemini-2.5-flash-preview-04-17",
        "mistralai/mistral-small-24b-instruct-2501",
        "meta-llama/llama-3.3-70b-instruct",
    ]
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        Inicializa el cliente con configuración.
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        config = self._load_config(config_path)
        or_config = config.get("openrouter", {})
        
        # API Key: settings.json > env var
        self.api_key = or_config.get("api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
        
        # Modelos: primary, fallback, cheap
        self.model = or_config.get("modelo", "google/gemini-2.0-flash-lite-preview")
        self.fallback_model = or_config.get("fallback_modelo", "google/gemini-2.0-flash-001")
        self.cheap_model = or_config.get("cheap_modelo", "mistralai/mistral-small-24b-instruct-2501")
        
        self.max_tokens = int(or_config.get("max_tokens", 2048))
        self.temperature = float(or_config.get("temperatura", 0.7))
        
        # Detectar SDKs disponibles
        self._openai_available = self._check_openai_sdk()
        
        # Estadísticas de uso
        self.total_tokens_used = 0
        self.total_calls = 0
        self.total_cost = 0.0
        self.call_history: List[Dict[str, Any]] = []
        self.last_error: Optional[str] = None
        self.last_model_used: Optional[str] = None
        
        # Contador de fallbacks por sesión
        self._fallback_count = 0
    
    def _check_openai_sdk(self) -> bool:
        """Verifica si el SDK de OpenAI está instalado."""
        try:
            import openai
            return True
        except ImportError:
            return False
    
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
    
    @property
    def transport(self) -> str:
        """Transporte activo: 'openai' o 'urllib'."""
        return "openai" if self._openai_available else "urllib"
    
    def _get_model_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        """Calcula el costo estimado de una llamada."""
        costs = self.MODEL_COSTS.get(model, self.MODEL_COSTS["default"])
        cost = (tokens_input * costs["input"] / 1_000_000) + \
               (tokens_output * costs["output"] / 1_000_000)
        return round(cost, 6)
    
    def _resolve_model_chain(self, preferred_model: Optional[str] = None) -> List[str]:
        """
        Resuelve la cadena de modelos a probar.
        
        Args:
            preferred_model: Modelo preferido (si es diferente del configurado)
        
        Returns:
            Lista de modelos en orden de preferencia
        """
        models = []
        
        # Modelo preferido (del caller)
        if preferred_model and preferred_model not in models:
            models.append(preferred_model)
        
        # Modelo primario
        if self.model and self.model not in models:
            models.append(self.model)
        
        # Modelo fallback
        if self.fallback_model and self.fallback_model not in models:
            models.append(self.fallback_model)
        
        # Modelo cheap
        if self.cheap_model and self.cheap_model not in models:
            models.append(self.cheap_model)
        
        # Cadena global de respaldo
        for m in self.FALLBACK_CHAIN:
            if m not in models:
                models.append(m)
        
        return models[:5]  # Máximo 5 intentos
    
    # ─── Transporte 1: OpenAI SDK ───
    
    def _call_openai_sdk(self, messages: List[Dict], model: str,
                         temperature: float, max_tokens: int,
                         timeout: int) -> Optional[Dict]:
        """
        Llama a OpenRouter usando el SDK de OpenAI.
        
        Args:
            messages: Lista de mensajes (system + user)
            model: Modelo a usar
            temperature: Temperatura
            max_tokens: Máximo de tokens
            timeout: Timeout en segundos
        
        Returns:
            Dict con la respuesta parseada, o None si hay error
        """
        try:
            import openai
        except ImportError:
            self.last_error = "openai SDK no disponible"
            return None
        
        try:
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                timeout=timeout,
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers={
                    "HTTP-Referer": "https://shadow-del-valle-r.vercel.app",
                    "X-Title": "Shadow Del Valle R",
                },
            )
            
            content = response.choices[0].message.content
            if not content:
                self.last_error = "Respuesta vacía del modelo"
                return None
            
            # Extraer usage del response
            usage = response.usage
            usage_dict = {}
            if usage:
                usage_dict = {
                    "prompt_tokens": usage.prompt_tokens or 0,
                    "completion_tokens": usage.completion_tokens or 0,
                    "total_tokens": usage.total_tokens or 0,
                }
            
            return {
                "content": content,
                "model": model,
                "usage": usage_dict,
            }
            
        except openai.RateLimitError as e:
            self.last_error = f"Rate limit (SDK): {str(e)[:100]}"
            raise ModelError(f"Rate limit en {model}: {str(e)[:100]}") from e
            
        except openai.APITimeoutError as e:
            self.last_error = f"Timeout (SDK): {str(e)[:100]}"
            raise ModelError(f"Timeout en {model}: {str(e)[:100]}") from e
            
        except openai.APIConnectionError as e:
            self.last_error = f"Connection error (SDK): {str(e)[:100]}"
            raise ModelError(f"Connection error en {model}: {str(e)[:100]}") from e
            
        except openai.AuthenticationError as e:
            self.last_error = f"Auth error: {str(e)[:100]}"
            return None  # No recuperable, no fallback
            
        except openai.BadRequestError as e:
            self.last_error = f"Bad request: {str(e)[:100]}"
            return None  # No recuperable
    
    # ─── Transporte 2: urllib (fallback) ───
    
    def _call_urllib(self, messages: List[Dict], model: str,
                     temperature: float, max_tokens: int,
                     timeout: int) -> Optional[Dict]:
        """
        Llama a OpenRouter usando urllib (fallback cuando no hay openai SDK).
        
        Args:
            messages: Lista de mensajes (system + user)
            model: Modelo a usar
            temperature: Temperatura
            max_tokens: Máximo de tokens
            timeout: Timeout en segundos
        
        Returns:
            Dict con la respuesta parseada, o None si hay error
        """
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
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
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
                
                choices = data.get("choices", [])
                if not choices:
                    self.last_error = "Respuesta vacía de OpenRouter"
                    return None
                
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    self.last_error = "Contenido vacío en respuesta"
                    return None
                
                return {
                    "content": content,
                    "model": model,
                    "usage": data.get("usage", {}),
                }
                
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")[:300]
            self.last_error = f"HTTP {e.code}: {body}"
            
            # Rate limit detected — return special signal
            if e.code == 429:
                raise ModelError(f"Rate limit en {model}: {body[:100]}")
            
            return None
            
        except urllib.error.URLError as e:
            self.last_error = f"Timeout/Connection: {str(e.reason)[:100]}"
            raise ModelError(f"Timeout/Connection en {model}: {str(e.reason)[:100]}")
        
        except json.JSONDecodeError as e:
            self.last_error = f"JSON inválido: {str(e)[:100]}"
            return None
    
    # ─── Método principal de generación ───
    
    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 preferred_model: Optional[str] = None,
                 timeout: int = 90) -> Optional[str]:
        """
        Envía un prompt a OpenRouter con fallback automático de modelos.
        
        Args:
            prompt: El prompt principal del usuario
            system_prompt: Prompt de sistema (opcional)
            temperature: Temperatura (override de config)
            max_tokens: Máximo de tokens (override de config)
            preferred_model: Modelo preferido para esta llamada
            timeout: Timeout en segundos
        
        Returns:
            str con la respuesta, o None si todos los modelos fallan
        """
        if not self.is_configured:
            self.last_error = "API key no configurada. Configúrala en settings.json o env OPENROUTER_API_KEY"
            return None
        
        # Configurar parámetros
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens or self.max_tokens
        
        # Construir mensajes
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Resolver cadena de modelos
        models_to_try = self._resolve_model_chain(preferred_model)
        
        # Intentar cada modelo con exponential backoff
        last_error = None
        start = time.time()
        
        for attempt, model in enumerate(models_to_try):
            # Backoff: 1s, 2s, 4s entre intentos de diferentes modelos
            if attempt > 0:
                backoff = 2 ** (attempt - 1)
            if backoff >= 1:
                time.sleep(backoff)
            
            try:
                # Elegir transporte
                if self._openai_available:
                    result = self._call_openai_sdk(
                        messages=messages,
                        model=model,
                        temperature=temp,
                        max_tokens=max_tok,
                        timeout=timeout,
                    )
                else:
                    result = self._call_urllib(
                        messages=messages,
                        model=model,
                        temperature=temp,
                        max_tokens=max_tok,
                        timeout=timeout,
                    )
                
                if result is None:
                    # Error no recuperable con este modelo
                    if attempt < len(models_to_try) - 1:
                        self._fallback_count += 1
                    continue
                
                # ✅ Éxito — procesar resultado
                content = result["content"]
                model_used = result.get("model", model)
                usage = result.get("usage", {})
                
                # Actualizar estadísticas
                self.total_calls += 1
                self.last_model_used = model_used
                
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)
                tokens_total = usage.get("total_tokens", tokens_input + tokens_output)
                self.total_tokens_used += tokens_total
                
                cost = self._get_model_cost(model_used, tokens_input, tokens_output)
                self.total_cost += cost
                
                elapsed = round(time.time() - start, 2)
                
                # Registrar en historial
                self.call_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "model": model_used,
                    "transport": self.transport,
                    "tokens": tokens_total,
                    "cost": cost,
                    "elapsed": elapsed,
                    "response_length": len(content),
                    "fallback_chain_position": attempt,
                })
                
                return content
                
            except ModelError as e:
                # Error recuperable (rate limit, timeout) — probar otro modelo
                last_error = str(e)
                self._fallback_count += 1
                continue
                
            except Exception as e:
                last_error = str(e)[:200]
                continue
        
        # Todos los modelos fallaron
        self.last_error = f"Todos los modelos fallaron. Último error: {last_error}"
        return None
    
    def generate_json(self,
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None,
                      preferred_model: Optional[str] = None) -> Optional[Dict]:
        """
        Envía un prompt y espera una respuesta JSON válida.
        
        Args:
            prompt: Prompt que debe generar JSON
            system_prompt: Prompt de sistema
            preferred_model: Modelo preferido
        
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
            temperature=temperature if temperature is not None else 0.3,
            preferred_model=preferred_model,
        )
        
        if not response:
            return None
        
        return self._parse_json_response(response)
    
    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """
        Parsea una respuesta JSON, limpiando markdown si es necesario.
        
        Args:
            text: Texto a parsear
        
        Returns:
            Dict parseado, o None si falla
        """
        text = text.strip()
        
        # Limpiar bloques markdown ```json ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            # Quitar primera línea (``` o ```json)
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3].strip()
        
        # Intentar parsear JSON completo
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Buscar primer { ... } o [ ... ] que sea JSON válido
        for pattern in [r'(\{.*\})', r'(\[.*\])']:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        self.last_error = "No se pudo parsear JSON de la respuesta"
        return None
    
    def get_usage_stats(self) -> Dict:
        """Retorna estadísticas de uso de la API."""
        return {
            "configurado": self.is_configured,
            "transporte": self.transport,
            "modelo_primario": self.model,
            "modelo_fallback": self.fallback_model,
            "ultimo_modelo_usado": self.last_model_used,
            "llamadas_totales": self.total_calls,
            "tokens_consumidos": self.total_tokens_used,
            "costo_total_usd": round(self.total_cost, 6),
            "fallbacks_por_sesion": self._fallback_count,
            "ultimo_error": self.last_error,
            "historial_reciente": self.call_history[-5:] if self.call_history else []
        }


# ─── Demo / Uso directo ───
if __name__ == "__main__":
    client = OpenRouterClient()
    
    print("=" * 60)
    print("  🌐 SHADOW DEL VALLE R — OPENROUTER CLIENT v2")
    print("=" * 60)
    
    if client.is_configured:
        print(f"\n  ✅ API Key configurada")
        print(f"  🚚 Transporte: {client.transport}")
        print(f"  🤖 Modelo: {client.model}")
        print(f"  🔄 Fallback: {client.fallback_model}")
        print(f"  💰 Cheap: {client.cheap_model}")
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
            print(f"  🤖 Modelo usado: {client.last_model_used}")
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

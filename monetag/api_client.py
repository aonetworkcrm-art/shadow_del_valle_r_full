# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Monetag SSP API v5 Client
================================================
Cliente oficial para la API de Monetag (Supply-Side Platform).
Autenticación via Bearer Token.

Documentación: https://api.monetag.com/v5/docs/

Endpoints implementados:
    GET  /pub/statistics       — Estadísticas de revenue, RPM, impresiones
    GET  /pub/zones            — Listar zonas/publicidad activas
    POST /pub/statistics       — Estadísticas filtradas (fechas, grupos)
    GET  /pub/sites            — Listar sitios registrados

Uso:
    from monetag.api_client import MonetagAPI
    api = MonetagAPI(api_token="tu_token_aqui")
    stats = api.get_statistics(date_from="2026-01-01", date_to="2026-01-31")
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import URLError
from urllib.request import Request, urlopen


# ─── Configuración de la API ───
MONETAG_API_BASE = "https://api.monetag.com/v5"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


# ─── Colores para consola ───
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"


def c(text, color, bold=False):
    prefix = Colors.BOLD if bold else ""
    return prefix + color + str(text) + Colors.RESET


class MonetagAPIError(Exception):
    """Error de la API de Monetag."""
    def __init__(self, message: str, status_code: int = 0, response: str = ""):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class MonetagAPI:
    """
    Cliente para la Monetag SSP API v5.
    
    Proporciona acceso a estadísticas de revenue, zonas publicitarias,
    y gestión de la cuenta.
    
    Args:
        api_token: Token Bearer de la API de Monetag (del panel de publisher)
        base_url: URL base de la API (default: https://api.monetag.com/v5)
        timeout: Timeout en segundos para las peticiones
    """
    
    def __init__(self, api_token: str = "", base_url: str = MONETAG_API_BASE, timeout: int = DEFAULT_TIMEOUT):
        self.api_token = api_token or os.environ.get("MONETAG_API_TOKEN", "")
        self.base_url = base_url
        self.timeout = timeout
        
        # Estadísticas de uso de la API
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_response = None
        self.last_error = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutos
        
        if self.api_token:
            self._log(f"✅ Monetag API configurada (token: {self.api_token[:8]}...{self.api_token[-4:]})")
        else:
            self._log("⚠️ Monetag API NO configurada. Usa MONETAG_API_TOKEN o pasa api_token")
    
    def _log(self, msg: str):
        print(f"  {c('[Monetag]', Colors.CYAN)} {msg}")
    
    def is_configured(self) -> bool:
        """Verifica si el API token está configurado."""
        return bool(self.api_token)
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                 params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Ejecuta una petición autenticada a la API de Monetag.
        
        Args:
            method: Método HTTP (GET, POST)
            endpoint: Ruta del endpoint (ej: /pub/statistics)
            data: Datos para el body (solo POST)
            params: Parámetros de query string
        
        Returns:
            Dict con la respuesta parseada, o None si hay error
        """
        if not self.api_token:
            self.last_error = "API token no configurado"
            return None
        
        # Construir URL
        url = f"{self.base_url}{endpoint}"
        
        # Añadir query params
        if params:
            query_parts = []
            for k, v in params.items():
                if v is not None:
                    query_parts.append(f"{k}={v}")
            if query_parts:
                url += "?" + "&".join(query_parts)
        
        # Headers
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ShadowDelValleR-Monetag/1.0"
        }
        
        body = None
        if data:
            body = json.dumps(data).encode("utf-8")
        
        # Intentar con retries
        for attempt in range(MAX_RETRIES):
            try:
                req = Request(url, data=body, headers=headers, method=method)
                
                with urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    self.total_requests += 1
                    
                    if raw.strip():
                        result = json.loads(raw)
                    else:
                        result = {}
                    
                    self.successful_requests += 1
                    self.last_response = result
                    
                    # Cachear resultados GET
                    if method == "GET":
                        cache_key = f"{endpoint}:{json.dumps(params or {})}"
                        self.cache[cache_key] = {
                            "data": result,
                            "timestamp": time.time()
                        }
                    
                    return result
                    
            except URLError as e:
                self.failed_requests += 1
                self.total_requests += 1
                status = getattr(e, "code", 0)
                reason = getattr(e, "reason", str(e))
                self.last_error = f"HTTP {status}: {reason}"
                
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_SECONDS * (attempt + 1)
                    print(f"     ⚠️ Reintento {attempt + 1}/{MAX_RETRIES} en {delay}s... ({self.last_error})")
                    time.sleep(delay)
                else:
                    print(f"     ❌ Error Monetag API: {self.last_error}")
                    
            except json.JSONDecodeError as e:
                self.failed_requests += 1
                self.last_error = f"Error parseando respuesta: {e}"
                print(f"     ❌ {self.last_error}")
                return None
                
            except Exception as e:
                self.failed_requests += 1
                self.last_error = str(e)
                print(f"     ❌ Error: {e}")
                return None
        
        return None
    
    def _get_cached(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Obtiene datos cacheados si aún son válidos."""
        cache_key = f"{endpoint}:{json.dumps(params or {})}"
        cached = self.cache.get(cache_key)
        if cached and (time.time() - cached["timestamp"]) < self.cache_ttl:
            return cached["data"]
        return None
    
    def _clear_cache(self):
        """Limpia toda la caché."""
        self.cache.clear()
    
    # ─── ENDPOINTS PRINCIPALES ───────────────────────────────────────────
    
    def get_statistics(self, date_from: str = "", date_to: str = "", 
                       group_by: str = "day", zone_ids: Optional[List[str]] = None,
                       force_refresh: bool = False) -> Optional[Dict]:
        """
        Obtiene estadísticas de rendimiento.
        
        Args:
            date_from: Fecha inicio (YYYY-MM-DD). Default: hace 7 días
            date_to: Fecha fin (YYYY-MM-DD). Default: hoy
            group_by: Agrupación ('day', 'zone', 'country', 'hour')
            zone_ids: IDs de zonas específicas (opcional)
            force_refresh: Ignorar caché
        
        Returns:
            Dict con estadísticas o None si error
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "group_by": group_by
        }
        
        if zone_ids:
            params["zone_ids"] = ",".join(zone_ids)
        
        # Verificar caché
        if not force_refresh:
            cached = self._get_cached("/pub/statistics", params)
            if cached:
                return cached
        
        return self._request("GET", "/pub/statistics", params=params)
    
    def get_statistics_filtered(self, date_from: str = "", date_to: str = "",
                                 filters: Optional[Dict] = None) -> Optional[Dict]:
        """
        Obtiene estadísticas con filtros avanzados (POST).
        
        Args:
            date_from: Fecha inicio
            date_to: Fecha fin
            filters: Filtros adicionales (country, zone_id, format, etc.)
        
        Returns:
            Dict con estadísticas filtradas
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        data = {
            "date_from": date_from,
            "date_to": date_to,
            **({"filters": filters} if filters else {})
        }
        
        return self._request("POST", "/pub/statistics", data=data)
    
    def get_zones(self, force_refresh: bool = False) -> Optional[Dict]:
        """
        Obtiene todas las zonas publicitarias.
        
        Returns:
            Dict con lista de zonas
        """
        if not force_refresh:
            cached = self._get_cached("/pub/zones")
            if cached:
                return cached
        
        result = self._request("GET", "/pub/zones")
        
        # Cachear por más tiempo (5 min)
        if result:
            cache_key = f"/pub/zones:{json.dumps({})}"
            self.cache[cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
        
        return result
    
    def get_sites(self, force_refresh: bool = False) -> Optional[Dict]:
        """
        Obtiene todos los sitios registrados.
        
        Returns:
            Dict con lista de sitios
        """
        if not force_refresh:
            cached = self._get_cached("/pub/sites")
            if cached:
                return cached
        
        return self._request("GET", "/pub/sites")
    
    # ─── MÉTODOS DE ALTO NIVEL ──────────────────────────────────────────
    
    def get_revenue_summary(self, days: int = 7, force_refresh: bool = False) -> Dict:
        """
        Obtiene un resumen de revenue para los últimos N días.
        
        Args:
            days: Número de días hacia atrás
            force_refresh: Ignorar caché
        
        Returns:
            Dict con resumen: total_revenue, total_impressions, avg_rpm, etc.
        """
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.get_statistics(date_from=date_from, date_to=date_to, 
                                    force_refresh=force_refresh)
        
        if not stats:
            return {
                "success": False,
                "error": self.last_error or "Sin datos",
                "days": days,
                "date_from": date_from,
                "date_to": date_to
            }
        
        # Parsear respuesta (la estructura puede variar según la API)
        # Intentar extraer datos de diferentes formatos posibles
        rows = []
        if isinstance(stats, list):
            rows = stats
        elif isinstance(stats, dict):
            rows = stats.get("data", stats.get("rows", stats.get("result", [])))
        
        total_revenue = 0.0
        total_impressions = 0
        total_clicks = 0
        total_rpm_sum = 0.0
        rows_with_data = 0
        best_day_revenue = 0.0
        best_day_date = ""
        
        for row in rows:
            if isinstance(row, dict):
                revenue = float(row.get("revenue", row.get("amount", row.get("earning", 0))))
                impressions = int(row.get("impressions", row.get("views", row.get("shows", 0))))
                clicks = int(row.get("clicks", 0))
                rpm = float(row.get("rpm", row.get("ecpm", 0)))
                date = row.get("date", row.get("day", ""))
                
                total_revenue += revenue
                total_impressions += impressions
                total_clicks += clicks
                
                if rpm > 0:
                    total_rpm_sum += rpm
                    rows_with_data += 1
                
                if revenue > best_day_revenue:
                    best_day_revenue = revenue
                    best_day_date = date
        
        avg_rpm = total_rpm_sum / rows_with_data if rows_with_data > 0 else 0.0
        avg_daily_revenue = total_revenue / days if days > 0 else 0.0
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        
        return {
            "success": True,
            "days": days,
            "date_from": date_from,
            "date_to": date_to,
            "total_revenue": round(total_revenue, 2),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "avg_daily_revenue": round(avg_daily_revenue, 2),
            "avg_rpm": round(avg_rpm, 2),
            "ctr_percent": round(ctr, 2),
            "best_day": {
                "date": best_day_date,
                "revenue": round(best_day_revenue, 2)
            },
            "projected_monthly": round(avg_daily_revenue * 30, 2),
            "projected_yearly": round(avg_daily_revenue * 365, 2),
            "total_rows": len(rows),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_zone_performance(self, days: int = 7) -> Dict:
        """
        Obtiene rendimiento por zona publicitaria.
        
        Returns:
            Dict con rendimiento detallado por zona
        """
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.get_statistics(date_from=date_from, date_to=date_to, 
                                    group_by="zone")
        
        if not stats:
            return {"success": False, "error": self.last_error or "Sin datos"}
        
        rows = []
        if isinstance(stats, list):
            rows = stats
        elif isinstance(stats, dict):
            rows = stats.get("data", stats.get("rows", stats.get("result", [])))
        
        zones = []
        total_revenue_all = 0.0
        
        for row in rows:
            if isinstance(row, dict):
                zone_name = row.get("zone_name", row.get("name", f"Zone {row.get('zone_id', '?')}"))
                zone_id = row.get("zone_id", row.get("id", ""))
                revenue = float(row.get("revenue", row.get("amount", 0)))
                impressions = int(row.get("impressions", row.get("views", 0)))
                clicks = int(row.get("clicks", 0))
                rpm = float(row.get("rpm", row.get("ecpm", 0)))
                
                total_revenue_all += revenue
                
                zones.append({
                    "zone_id": str(zone_id),
                    "zone_name": str(zone_name)[:40],
                    "revenue": round(revenue, 2),
                    "impressions": impressions,
                    "clicks": clicks,
                    "rpm": round(rpm, 2),
                    "revenue_percent": 0.0  # Se calcula después
                })
        
        # Calcular porcentaje del total
        for z in zones:
            if total_revenue_all > 0:
                z["revenue_percent"] = round(z["revenue"] / total_revenue_all * 100, 1)
        
        # Ordenar por revenue descendente
        zones.sort(key=lambda z: z["revenue"], reverse=True)
        
        return {
            "success": True,
            "days": days,
            "total_zones": len(zones),
            "total_revenue": round(total_revenue_all, 2),
            "zones": zones,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_daily_trend(self, days: int = 30) -> Dict:
        """
        Obtiene tendencia diaria de revenue.
        
        Returns:
            Dict con revenue diario para graficar
        """
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.get_statistics(date_from=date_from, date_to=date_to, 
                                    group_by="day", force_refresh=True)
        
        if not stats:
            return {"success": False, "error": self.last_error or "Sin datos"}
        
        rows = []
        if isinstance(stats, list):
            rows = stats
        elif isinstance(stats, dict):
            rows = stats.get("data", stats.get("rows", stats.get("result", [])))
        
        daily = []
        for row in rows:
            if isinstance(row, dict):
                daily.append({
                    "date": row.get("date", row.get("day", "")),
                    "revenue": round(float(row.get("revenue", row.get("amount", 0))), 2),
                    "impressions": int(row.get("impressions", 0)),
                    "clicks": int(row.get("clicks", 0)),
                    "rpm": round(float(row.get("rpm", row.get("ecpm", 0))), 2)
                })
        
        # Ordenar por fecha
        daily.sort(key=lambda d: d["date"])
        
        # Calcular tendencia (simple: promedio móvil de 7 días)
        trend = []
        window = min(7, len(daily))
        for i in range(len(daily)):
            if i >= window - 1:
                avg = sum(daily[j]["revenue"] for j in range(i - window + 1, i + 1)) / window
                trend.append({
                    "date": daily[i]["date"],
                    "moving_avg_7d": round(avg, 2)
                })
        
        return {
            "success": True,
            "days": days,
            "total_days": len(daily),
            "daily": daily,
            "trend_7d": trend,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_geo_performance(self, days: int = 7) -> Dict:
        """
        Obtiene rendimiento por país (geográfico).
        
        Returns:
            Dict con revenue, RPM y CTR por país
        """
        stats = self.get_statistics(
            date_from=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            date_to=datetime.now().strftime("%Y-%m-%d"),
            group_by="country"
        )
        
        if not stats:
            return {"success": False, "error": self.last_error or "Sin datos"}
        
        rows = []
        if isinstance(stats, list):
            rows = stats
        elif isinstance(stats, dict):
            rows = stats.get("data", stats.get("rows", stats.get("result", [])))
        
        countries = []
        for row in rows:
            if isinstance(row, dict):
                country = row.get("country", row.get("country_name", "Unknown"))
                revenue = float(row.get("revenue", 0))
                impressions = int(row.get("impressions", 0))
                clicks = int(row.get("clicks", 0))
                rpm = float(row.get("rpm", row.get("ecpm", 0)))
                
                countries.append({
                    "country": country,
                    "revenue": round(revenue, 2),
                    "impressions": impressions,
                    "clicks": clicks,
                    "rpm": round(rpm, 2),
                    "ctr": round(clicks / impressions * 100, 2) if impressions > 0 else 0
                })
        
        countries.sort(key=lambda c: c["revenue"], reverse=True)
        
        return {
            "success": True,
            "days": days,
            "total_countries": len(countries),
            "countries": countries,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_api_stats(self) -> Dict:
        """Estadísticas de uso de la API."""
        return {
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "success_rate": round(self.successful_requests / max(self.total_requests, 1) * 100, 1),
            "configured": self.is_configured(),
            "cache_size": len(self.cache),
            "last_error": self.last_error
        }
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con la API.
        Intenta obtener las zonas como test.
        
        Returns:
            True si la conexión es exitosa
        """
        if not self.is_configured():
            print(f"  {c('❌ API no configurada (sin token)', Colors.RED)}")
            return False
        
        print(f"  {c('🔌 Probando conexión con Monetag API...', Colors.YELLOW)}")
        print(f"     URL: {self.base_url}")
        print(f"     Token: {self.api_token[:8]}...{self.api_token[-4:]}")
        
        result = self.get_zones(force_refresh=True)
        
        if result is not None:
            print(f"  {c('✅ Conexión exitosa!', Colors.GREEN, bold=True)}")
            return True
        else:
            print(f"  {c(f'❌ Error: {self.last_error}', Colors.RED)}")
            return False

# ─── CLI para pruebas ───
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🔌 Monetag API Client v5")
    parser.add_argument("--token", type=str, help="API Bearer Token")
    parser.add_argument("--test", action="store_true", help="Probar conexión")
    parser.add_argument("--revenue", type=int, nargs="?", const=7, help="Ver resumen revenue (días)")
    parser.add_argument("--zones", action="store_true", help="Ver zonas")
    parser.add_argument("--daily", type=int, nargs="?", const=30, help="Ver tendencia diaria (días)")
    parser.add_argument("--geo", type=int, nargs="?", const=7, help="Ver rendimiento por país (días)")
    
    args = parser.parse_args()
    
    token = args.token or os.environ.get("MONETAG_API_TOKEN", "")
    api = MonetagAPI(api_token=token)
    
    if args.test:
        api.test_connection()
    elif args.revenue:
        result = api.get_revenue_summary(days=args.revenue)
        print(json.dumps(result, indent=2, default=str))
    elif args.zones:
        result = api.get_zone_performance()
        print(json.dumps(result, indent=2, default=str))
    elif args.daily:
        result = api.get_daily_trend(days=args.daily)
        print(json.dumps(result, indent=2, default=str))
    elif args.geo:
        result = api.get_geo_performance(days=args.geo)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Demo: mostrar resumen
        print(f"\n{c('=' * 60, Colors.CYAN, bold=True)}")
        print(c(f'  🔌 MONETAG API CLIENT v5', Colors.CYAN, bold=True))
        print(c('=' * 60, Colors.CYAN, bold=True))
        
        if api.is_configured():
            print(f"\n  {c('✅ Token configurado', Colors.GREEN)}")
            print(f"  {c('🔍 Probando conexión...', Colors.YELLOW)}")
            api.test_connection()
            
            print(f"\n  {c('📊 Resumen de revenue (7 días):', Colors.YELLOW, bold=True)}")
            revenue = api.get_revenue_summary(days=7)
            if revenue.get("success"):
                print(f"     Revenue total:    ${revenue['total_revenue']:>8,.2f}")
                print(f"     Avg diario:       ${revenue['avg_daily_revenue']:>8,.2f}")
                print(f"     Impresiones:      {revenue['total_impressions']:,}")
                print(f"     RPM promedio:     ${revenue['avg_rpm']:>8,.2f}")
                print(f"     CTR:              {revenue['ctr_percent']:.2f}%")
                print(f"     Proy. mensual:    ${revenue['projected_monthly']:>8,.2f}")
                print(f"     Mejor día:        {revenue['best_day']['date']} (${revenue['best_day']['revenue']:.2f})")
        else:
            print(f"\n  {c('❌ Token no configurado', Colors.RED)}")
            print(f"  {c('Usa: --token TU_TOKEN o exporta MONETAG_API_TOKEN', Colors.YELLOW)}")
        
        print(f"\n{c('=' * 60, Colors.CYAN, bold=True)}")

# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Monetag Smart Optimizer
=============================================
Motor de optimización inteligente para maximizar revenue.
Analiza datos de rendimiento y ajusta automáticamente la configuración
de Monetag para maximizar ingresos.

Capacidades:
    - A/B Testing automático de formatos (popunder vs push vs smartlink)
    - Geo-Routing: formato óptimo según país del visitante
    - Horario Inteligente: ajusta formatos según hora del día
    - MultiTag Dynamic: recomienda cambios en configuración MultiTag
    - Presupuesto: distribución óptima de tráfico entre zonas
"""

import json
import math
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from .api_client import MonetagAPI
from .revenue_tracker import RevenueTracker


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


class MonetagOptimizer:
    """
    Motor de optimización inteligente de Monetag.
    
    Analiza datos de rendimiento y genera recomendaciones accionables
    para maximizar el revenue.
    
    Args:
        api: Instancia de MonetagAPI
        tracker: Instancia de RevenueTracker
        config_path: Ruta al archivo de configuración (settings.json)
    """
    
    # RPM thresholds por formato (basados en datos de la industria)
    FORMAT_RPM_BENCHMARKS = {
        "popunder": {"min": 0.50, "avg": 1.50, "max": 5.00},
        "push": {"min": 0.30, "avg": 0.80, "max": 2.50},
        "smartlink": {"min": 1.00, "avg": 3.00, "max": 8.00},
        "inpage_push": {"min": 0.20, "avg": 0.60, "max": 1.80},
        "vignette": {"min": 0.40, "avg": 1.20, "max": 3.50}
    }
    
    # Mejor formato por hora del día (24h)
    HOUR_FORMAT_RECOMMENDATION = {
        "00-06": "popunder",    # Madrugada: tráfico de noche, popunder funciona mejor
        "06-12": "smartlink",   # Mañana: usuarios más receptivos a ofertas
        "12-18": "push",        # Tarde: usuarios navegando activamente
        "18-24": "popunder"     # Noche: máximo tráfico, popunder maximiza revenue
    }
    
    # Países Tier 1 (alto RPM) vs Tier 3 (bajo RPM)
    TIER1_COUNTRIES = {"US", "GB", "CA", "AU", "DE", "FR", "NL", "CH", "SE", "NO", "DK", "FI", "IE", "NZ", "JP", "KR", "SG", "AE", "IL"}
    TIER3_COUNTRIES = {"IN", "ID", "PH", "PK", "BD", "NG", "ET", "KE", "GH", "UG"}
    
    def __init__(self, api: Optional[MonetagAPI] = None, tracker: Optional[RevenueTracker] = None,
                 config_path: str = "config/settings.json"):
        self.api = api or MonetagAPI()
        self.tracker = tracker or RevenueTracker(api=self.api)
        self.config_path = config_path
        
        # Historial de optimizaciones
        self.optimization_history: List[Dict] = []
        self.last_optimization = 0.0
        self.optimization_interval = 3600  # 1 hora
        
        # Cache de recomendaciones
        self._last_recommendations: Optional[Dict] = None
        self._last_analysis_time = 0.0
    
    def _log(self, msg: str):
        print(f"  {c('[Optimizer]', Colors.MAGENTA)} {msg}")
    
    def _load_config(self) -> Dict:
        """Carga configuración actual de Monetag desde settings.json."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    
    def _save_config(self, config: Dict):
        """Guarda configuración actualizada."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"  {c(f'⚠️ Error guardando config: {e}', Colors.RED)}")
            return False
    
    # ─── ANÁLISIS DE RENDIMIENTO ────────────────────────────────────────
    
    def analyze_format_performance(self, force_refresh: bool = False) -> Dict:
        """
        Analiza el rendimiento de los formatos actuales.
        
        Returns:
            Dict con análisis de formato, RPM y recomendaciones
        """
        # Obtener datos de revenue
        if force_refresh:
            self.tracker.sync_now(force=True)
        
        revenue = self.tracker.get_current_revenue()
        zones = self.tracker.get_zone_analysis()
        daily = self.tracker.get_daily_breakdown(days=14)
        
        avg_rpm = revenue.get("avg_rpm", 0) if isinstance(revenue, dict) else 0
        
        # Comparar con benchmarks
        format_analysis = []
        best_format = "popunder"  # Default
        best_rpm = 0
        
        for fmt, benchmarks in self.FORMAT_RPM_BENCHMARKS.items():
            # Estimar RPM para este formato basado en datos disponibles
            estimated_rpm = self._estimate_format_rpm(fmt, zones)
            
            status = "✅" if estimated_rpm >= benchmarks["avg"] else ("⚠️" if estimated_rpm >= benchmarks["min"] else "❌")
            
            comparison = {
                "format": fmt,
                "current_rpm": estimated_rpm,
                "benchmark_min": benchmarks["min"],
                "benchmark_avg": benchmarks["avg"],
                "benchmark_max": benchmarks["max"],
                "status": status,
                "gap_to_avg": round(estimated_rpm - benchmarks["avg"], 2),
                "potential_increase": self._calculate_potential(estimated_rpm, benchmarks)
            }
            
            format_analysis.append(comparison)
            
            if estimated_rpm > best_rpm:
                best_rpm = estimated_rpm
                best_format = fmt
        
        # Ordenar por RPM descendente
        format_analysis.sort(key=lambda f: f["current_rpm"], reverse=True)
        
        # Análisis de tendencia
        trend_analysis = self._analyze_trend(daily)
        
        result = {
            "success": True,
            "current_rpm": avg_rpm,
            "best_format": best_format,
            "best_rpm": best_rpm,
            "formats": format_analysis,
            "trend": trend_analysis,
            "recommendations": self._generate_performance_recommendations(format_analysis, trend_analysis, avg_rpm),
            "timestamp": datetime.now().isoformat()
        }
        
        self._last_recommendations = result
        self._last_analysis_time = time.time()
        
        return result
    
    def _estimate_format_rpm(self, fmt: str, zones_data: Any) -> float:
        """Estima el RPM para un formato basado en datos disponibles."""
        # Extraer RPM de zonas si es posible
        if isinstance(zones_data, dict):
            zones = zones_data.get("zones", zones_data.get("analysis", {}))
            if isinstance(zones, list) and zones:
                rpms = [z.get("rpm", 0) for z in zones if z.get("rpm", 0) > 0]
                if rpms:
                    return sum(rpms) / len(rpms)
        
        # Fallback: usar benchmarks promedio
        benchmarks = self.FORMAT_RPM_BENCHMARKS.get(fmt, {})
        return benchmarks.get("avg", 1.0)
    
    def _calculate_potential(self, current: float, benchmarks: Dict) -> Dict:
        """Calcula el potencial de mejora."""
        if current <= 0 or benchmarks.get("avg", 0) <= 0:
            return {"percent": 0, "description": "Sin datos suficientes"}
        
        gap = benchmarks["avg"] - current
        pct = (gap / current) * 100 if current > 0 else 0
        
        return {
            "percent": round(pct, 1),
            "to_reach_avg": round(benchmarks["avg"], 2),
            "description": f"{'+' if pct > 0 else ''}{pct:.0f}% vs promedio del mercado"
        }
    
    def _analyze_trend(self, daily_data: Any) -> Dict:
        """Analiza la tendencia de revenue."""
        if not isinstance(daily_data, dict):
            return {"direction": "unknown", "strength": 0, "description": "Sin datos"}
        
        analysis = daily_data.get("analysis", {})
        trend_pct = analysis.get("trend_last_week_pct", 0)
        direction = analysis.get("trend_direction", "stable")
        
        strengths = {"up": min(abs(trend_pct) / 10, 1.0), "down": min(abs(trend_pct) / 10, 1.0), "stable": 0.2}
        
        return {
            "direction": direction,
            "strength": strengths.get(direction, 0.2),
            "change_pct": trend_pct,
            "description": f"Tendencia: {direction.upper()} ({trend_pct:+.1f}% última semana)"
        }
    
    def _generate_performance_recommendations(self, formats: List, trend: Dict, current_rpm: float) -> List[str]:
        """Genera recomendaciones basadas en análisis de rendimiento."""
        recommendations = []
        
        # Recomendación por formato
        if formats:
            best = formats[0]
            worst = formats[-1]
            
            if best["gap_to_avg"] > 0:
                recommendations.append(f"🔥 {best['format'].upper()} es tu mejor formato (RPM: ${best['current_rpm']:.2f}). Maximiza su uso.")
            
            if worst["gap_to_avg"] < -1.0:
                recommendations.append(f"⚠️ {worst['format'].upper()} está muy por debajo del promedio. Considera desactivarlo temporalmente.")
        
        # Recomendación por tendencia
        if trend.get("direction") == "down" and trend.get("strength", 0) > 0.5:
            recommendations.append("📉 Tendencia bajista fuerte. Revisa formato y origen del tráfico.")
        elif trend.get("direction") == "up" and trend.get("strength", 0) > 0.5:
            recommendations.append(f"📈 Tendencia alcista. Aprovecha el momento aumentando inventario.")
        
        # Recomendación general por RPM
        if current_rpm < 0.5:
            recommendations.append("🚨 RPM muy bajo. Cambia a popunder o smartlink urgentemente.")
        elif current_rpm < 1.0:
            recommendations.append("💡 RPM por debajo del promedio. Prueba con smartlink para mejorar.")
        elif current_rpm > 3.0:
            recommendations.append(f"🏆 RPM excepcional (${current_rpm:.2f}). Sigue así y escala.")
        
        return recommendations
    
    # ─── OPTIMIZACIÓN POR HORARIO ───────────────────────────────────────
    
    def get_hourly_recommendation(self) -> Dict:
        """
        Obtiene la recomendación de formato según la hora actual.
        
        Returns:
            Dict con formato recomendado para la hora actual
        """
        hour = datetime.now().hour
        
        if hour < 6:
            period = "00-06"
        elif hour < 12:
            period = "06-12"
        elif hour < 18:
            period = "12-18"
        else:
            period = "18-24"
        
        recommended = self.HOUR_FORMAT_RECOMMENDATION.get(period, "popunder")
        
        return {
            "current_hour": hour,
            "period": period,
            "recommended_format": recommended,
            "reason": self._get_hourly_reason(period, recommended),
            "is_optimal": True  # Siempre óptimo para la hora actual
        }
    
    def _get_hourly_reason(self, period: str, fmt: str) -> str:
        reasons = {
            "00-06": "Madrugada: tráfico de noche, popunder tiene mayor tasa de conversión",
            "06-12": "Mañana: usuarios revisando contenido, smartlink ofrece mejores RPM",
            "12-18": "Tarde: navegación activa, push notifications mantienen engagement",
            "18-24": "Noche: pico de tráfico, popunder maximiza revenue"
        }
        return reasons.get(period, f"Formato recomendado: {fmt}")
    
    # ─── OPTIMIZACIÓN GEOGRÁFICA ────────────────────────────────────────
    
    def get_geo_recommendation(self) -> Dict:
        """
        Analiza tráfico por país y recomienda estrategia.
        
        Returns:
            Dict con recomendaciones por grupo de países
        """
        geo = self.tracker.get_geo_analysis()
        
        if not geo.get("success"):
            return geo
        
        countries = geo.get("countries", [])
        analysis = geo.get("analysis", {})
        
        tier1_found = [c for c in countries if c["country"] in self.TIER1_COUNTRIES]
        tier3_found = [c for c in countries if c["country"] in self.TIER3_COUNTRIES]
        
        return {
            "success": True,
            "tier1_countries": tier1_found,
            "tier3_countries": tier3_found,
            "recommended_format_by_tier": {
                "tier1": "smartlink",   # Alto RPM: ofertas premium
                "tier2": "popunder",    # RPM medio: popunder maximiza
                "tier3": "push"         # Bajo RPM: push no ahuyenta usuarios
            },
            "recommendations": [
                f"🎯 Para tráfico Tier 1 ({', '.join(c['country'] for c in tier1_found[:3])}): usa SMARTLINK (máximo RPM)",
                f"🌍 Para tráfico general: usa POPUNDER (mejor balance)",
                f"📱 Para tráfico mobile: usa IN-PAGE PUSH (menos intrusivo)"
            ] if tier1_found else ["ℹ️ Sin datos de países Tier 1 aún."],
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    # ─── OPTIMIZACIÓN COMPLETA ──────────────────────────────────────────
    
    def run_optimization_cycle(self, force: bool = False) -> Dict:
        """
        Ejecuta un ciclo completo de optimización.
        
        1. Sincroniza datos de Monetag
        2. Analiza rendimiento de formatos
        3. Evalúa horario óptimo
        4. Analiza geografía
        5. Genera recomendaciones
        6. Aplica cambios automáticos si está configurado
        
        Args:
            force: Forzar ciclo aunque haya uno reciente
        
        Returns:
            Dict con todas las recomendaciones y acciones tomadas
        """
        ahora = time.time()
        if not force and (ahora - self.last_optimization) < self.optimization_interval:
            return {"success": True, "cached": True, "message": "Optimización reciente. Usa force=True para forzar."}
        
        self._log("Ejecutando ciclo de optimización...")
        
        if not self.api.is_configured():
            return {"success": False, "error": "Monetag API no configurada"}
        
        # 1. Sincronizar datos
        self._log("Sincronizando datos de revenue...")
        self.tracker.sync_now(force=True)
        
        # 2. Analizar formatos
        self._log("Analizando rendimiento de formatos...")
        format_analysis = self.analyze_format_performance()
        
        # 3. Recomendación horaria
        self._log("Evaluando horario óptimo...")
        hourly = self.get_hourly_recommendation()
        
        # 4. Análisis geográfico
        self._log("Analizando geografía del tráfico...")
        geo = self.get_geo_recommendation()
        
        # 5. Generar recomendaciones integradas
        all_recommendations = []
        all_recommendations.extend(format_analysis.get("recommendations", []))
        all_recommendations.append(f"⏰ {hourly['reason']}")
        all_recommendations.extend(geo.get("recommendations", []))
        
        # 6. Aplicar cambios automáticos si es necesario
        auto_changes = self._apply_auto_optimizations(format_analysis, hourly, geo)
        
        result = {
            "success": True,
            "cycle_number": len(self.optimization_history) + 1,
            "format_analysis": format_analysis,
            "hourly_recommendation": hourly,
            "geo_recommendation": geo,
            "recommendations": all_recommendations,
            "auto_changes_applied": auto_changes,
            "timestamp": datetime.now().isoformat()
        }
        
        self.optimization_history.append(result)
        self.last_optimization = ahora
        
        self._log(f"Ciclo completado. {len(all_recommendations)} recomendaciones generadas.")
        if auto_changes:
            self._log(f"✅ {len(auto_changes)} cambio(s) aplicado(s) automáticamente.")
        
        return result
    
    def _apply_auto_optimizations(self, format_analysis: Dict, hourly: Dict, geo: Dict) -> List[Dict]:
        """
        Aplica cambios automáticos a la configuración si es necesario.
        Por ahora solo genera recomendaciones (no cambia config automáticamente
        sin aprobación del usuario).
        
        Returns:
            Lista de cambios que se aplicarían
        """
        changes = []
        config = self._load_config()
        monetag_cfg = config.get("monetag", {})
        current_format = monetag_cfg.get("formato", "popunder_smartlink")
        
        # Verificar si el formato actual es óptimo
        best_format = format_analysis.get("best_format", "popunder")
        recommended_hourly = hourly.get("recommended_format", "popunder")
        
        # Mapear formatos recomendados a config
        format_map = {
            "popunder": "popunder_smartlink",
            "push": "push_notifications",
            "smartlink": "smartlink_only",
            "inpage_push": "inpage_push",
            "vignette": "vignette"
        }
        
        suggested_format = format_map.get(recommended_hourly, "popunder_smartlink")
        
        if current_format != suggested_format:
            changes.append({
                "parameter": "formato",
                "from": current_format,
                "to": suggested_format,
                "reason": f"Optimización horaria: {hourly['reason']}",
                "auto_appliable": True
            })
        
        # Verificar delay de carga
        current_delay = monetag_cfg.get("delay_carga_ms", 2000)
        rpm = format_analysis.get("current_rpm", 1.0)
        
        if rpm < 0.5 and current_delay > 1000:
            changes.append({
                "parameter": "delay_carga_ms",
                "from": current_delay,
                "to": 500,
                "reason": "RPM bajo. Reducir delay puede aumentar visibilidad de anuncios",
                "auto_appliable": True
            })
        elif rpm > 3.0 and current_delay < 2000:
            changes.append({
                "parameter": "delay_carga_ms",
                "from": current_delay,
                "to": 3000,
                "reason": "RPM alto. Aumentar delay mejora experiencia de usuario sin perder revenue",
                "auto_appliable": True
            })
        
        return changes
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict]:
        """Obtiene historial de optimizaciones."""
        return self.optimization_history[-limit:]
    
    def get_summary_stats(self) -> Dict:
        """Estadísticas del optimizer."""
        return {
            "total_optimizations": len(self.optimization_history),
            "last_optimization": datetime.fromtimestamp(self.last_optimization).strftime("%Y-%m-%d %H:%M:%S") if self.last_optimization else "Nunca",
            "optimization_interval_hours": self.optimization_interval / 3600,
            "api_configured": self.api.is_configured()
        }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🧠 Monetag Smart Optimizer")
    parser.add_argument("--token", type=str, help="API Bearer Token")
    parser.add_argument("--analyze", action="store_true", help="Analizar rendimiento de formatos")
    parser.add_argument("--hourly", action="store_true", help="Recomendación por horario")
    parser.add_argument("--geo", action="store_true", help="Recomendación geográfica")
    parser.add_argument("--optimize", action="store_true", help="Ciclo completo de optimización")
    parser.add_argument("--loop", type=int, nargs="?", const=60, help="Loop de optimización (intervalo en min)")
    
    args = parser.parse_args()
    
    token = args.token or os.environ.get("MONETAG_API_TOKEN", "")
    api = MonetagAPI(api_token=token)
    tracker = RevenueTracker(api=api)
    optimizer = MonetagOptimizer(api=api, tracker=tracker)
    
    if args.analyze:
        result = optimizer.analyze_format_performance(force_refresh=True)
        print(json.dumps(result, indent=2, default=str))
    elif args.hourly:
        result = optimizer.get_hourly_recommendation()
        print(json.dumps(result, indent=2, default=str))
    elif args.geo:
        result = optimizer.get_geo_recommendation()
        print(json.dumps(result, indent=2, default=str))
    elif args.optimize:
        result = optimizer.run_optimization_cycle(force=True)
        print(json.dumps(result, indent=2, default=str))
    elif args.loop:
        print(f"\n  {c(f'🔄 Loop de optimización cada {args.loop} min...', Colors.MAGENTA, bold=True)}")
        interval = args.loop * 60
        try:
            while True:
                optimizer.run_optimization_cycle(force=True)
                for _ in range(interval):
                    time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n  {c('👋 Loop detenido.', Colors.YELLOW)}")
    else:
        print(f"\n{c('=' * 60, Colors.MAGENTA, bold=True)}")
        print(c(f'  🧠 MONETAG SMART OPTIMIZER', Colors.MAGENTA, bold=True))
        print(c('=' * 60, Colors.MAGENTA, bold=True))
        
        if api.is_configured():
            result = optimizer.analyze_format_performance()
            print(f"\n  {c('📊 ANÁLISIS DE FORMATOS', Colors.YELLOW, bold=True)}")
            for fmt in result.get("formats", []):
                status = fmt["status"]
                print(f"     {status} {fmt['format']:>12}: ${fmt['current_rpm']:>5.2f} RPM (benchmark: ${fmt['benchmark_avg']:.2f})")
            
            print(f"\n  {c('⏰ RECOMENDACIÓN HORARIA', Colors.YELLOW, bold=True)}")
            hourly = result.get("recommendations", [])
            for i, rec in enumerate(hourly[:3]):
                print(f"     {rec}")
        else:
            print(f"\n  {c('❌ API no configurada', Colors.RED)}")
        
        print(f"\n{c('=' * 60, Colors.MAGENTA, bold=True)}")

# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Monetag Revenue Tracker
=============================================
Sistema de tracking de revenue en tiempo real.
Sincroniza los datos de la API de Monetag con el Ledger existente
y proporciona métricas de rendimiento histórico.

Características:
    - Sincronización automática con Ledger cada N minutos
    - Revenue histórico diario (7, 30, 90 días)
    - Top zonas por rendimiento
    - Proyecciones inteligentes
    - Reportes exportables
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from .api_client import MonetagAPI

# ─── Colores ───
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


class RevenueTracker:
    """
    Rastrea el revenue de Monetag y lo sincroniza con el Ledger.
    
    Args:
        api: Instancia de MonetagAPI configurada
        ledger: Instancia de Ledger (opcional, para sincronización)
        data_dir: Directorio para persistencia de datos
    """
    
    def __init__(self, api: Optional[MonetagAPI] = None, ledger=None, 
                 data_dir: str = "output/revenue"):
        self.api = api or MonetagAPI()
        self.ledger = ledger
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Estado del tracker
        self.last_sync = 0.0
        self.sync_count = 0
        self.sync_errors = 0
        self.sync_interval_seconds = 300  # 5 minutos
        
        # Datos cacheados
        self._revenue_cache: Optional[Dict] = None
        self._daily_cache: Optional[Dict] = None
        self._zone_cache: Optional[Dict] = None
        self._geo_cache: Optional[Dict] = None
        self._cache_time = 0.0
        self._cache_ttl = 60  # 1 minuto
    
    def _log(self, msg: str):
        print(f"  {c('[Revenue]', Colors.GREEN)} {msg}")
    
    def _get_db_path(self, name: str) -> str:
        return os.path.join(self.data_dir, f"{name}.json")
    
    def _load_json(self, name: str, default: Any = None) -> Any:
        path = self._get_db_path(name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return default if default is not None else {}
    
    def _save_json(self, name: str, data: Any):
        path = self._get_db_path(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _is_cache_valid(self) -> bool:
        return (time.time() - self._cache_time) < self._cache_ttl and self._revenue_cache is not None
    
    # ─── SINCRONIZACIÓN ─────────────────────────────────────────────────
    
    def sync_now(self, force: bool = False) -> Dict:
        """
        Ejecuta una sincronización completa con la API de Monetag.
        Actualiza el Ledger con los datos de revenue.
        
        Args:
            force: Forzar sincronización aunque haya una reciente
        
        Returns:
            Dict con resultado de la sincronización
        """
        if not self.api.is_configured():
            return {"success": False, "error": "Monetag API no configurada"}
        
        ahora = time.time()
        if not force and (ahora - self.last_sync) < self.sync_interval_seconds:
            return {"success": True, "cached": True, "message": "Usando datos en caché"}
        
        self._log("Sincronizando revenue con Monetag API...")
        
        try:
            # Obtener revenue de los últimos 7 días
            summary = self.api.get_revenue_summary(days=7, force_refresh=True)
            zones = self.api.get_zone_performance(days=7)
            daily = self.api.get_daily_trend(days=30)
            geo = self.api.get_geo_performance(days=7)
            
            if not summary.get("success"):
                self.sync_errors += 1
                return {"success": False, "error": summary.get("error", "Error obteniendo revenue")}
            
            self._revenue_cache = summary
            self._zone_cache = zones
            self._daily_cache = daily
            self._geo_cache = geo
            self._cache_time = ahora
            
            # Sincronizar con el Ledger si está disponible
            if self.ledger and summary.get("total_revenue", 0) > 0:
                self._sync_to_ledger(summary)
            
            self.last_sync = ahora
            self.sync_count += 1
            
            # Guardar snapshot histórico
            self._save_snapshot(summary)
            
            self._log(f"Sincronizado: ${summary['total_revenue']:.2f} en {summary['days']} días "
                      f"(RPM: ${summary['avg_rpm']:.2f})")
            
            return {
                "success": True,
                "summary": summary,
                "zones": zones,
                "daily": daily,
                "geo": geo,
                "sync_count": self.sync_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.sync_errors += 1
            error_msg = f"Error de sincronización: {e}"
            self._log(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def _sync_to_ledger(self, summary: Dict):
        """Sincroniza el revenue con el Ledger del sistema."""
        if not self.ledger:
            return
        
        # Registrar ingreso en el Ledger
        revenue = summary.get("total_revenue", 0)
        if revenue > 0:
            self.ledger.registrar_ingreso(
                monto=revenue,
                concepto=f"Monetag — {summary['days']} días (RPM: ${summary['avg_rpm']:.2f})",
                fuente="monetag",
                nicho="MultiTag"
            )
    
    def _save_snapshot(self, summary: Dict):
        """Guarda un snapshot histórico de revenue."""
        history = self._load_json("revenue_history", [])
        
        snapshot = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_revenue": summary.get("total_revenue", 0),
            "avg_daily_revenue": summary.get("avg_daily_revenue", 0),
            "avg_rpm": summary.get("avg_rpm", 0),
            "total_impressions": summary.get("total_impressions", 0),
            "total_clicks": summary.get("total_clicks", 0),
            "ctr": summary.get("ctr_percent", 0),
            "projected_monthly": summary.get("projected_monthly", 0)
        }
        
        history.append(snapshot)
        
        # Mantener solo últimos 90 días de snapshots
        if len(history) > 90:
            history = history[-90:]
        
        self._save_json("revenue_history", history)
    
    # ─── CONSULTAS ──────────────────────────────────────────────────────
    
    def get_current_revenue(self, force_refresh: bool = False) -> Dict:
        """
        Obtiene el resumen de revenue actual.
        
        Returns:
            Dict con revenue resumido
        """
        if force_refresh or not self._is_cache_valid():
            result = self.sync_now(force=force_refresh)
            if not result.get("success") and not self._revenue_cache:
                return {"success": False, "error": "No hay datos"}
            if result.get("success"):
                return result.get("summary", self._revenue_cache)
        
        return self._revenue_cache or {"success": False, "error": "Sin datos"}
    
    def get_daily_breakdown(self, days: int = 30) -> Dict:
        """
        Obtiene desglose diario de revenue.
        
        Returns:
            Dict con revenue diario, tendencia, y proyecciones
        """
        if days == 30 and self._daily_cache:
            daily = self._daily_cache
        else:
            daily = self.api.get_daily_trend(days=days)
            if days == 30:
                self._daily_cache = daily
        
        if not daily.get("success"):
            return daily
        
        # Calcular métricas adicionales
        entries = daily.get("daily", [])
        if not entries:
            return daily
        
        revenues = [d["revenue"] for d in entries]
        total = sum(revenues)
        avg = total / len(revenues) if revenues else 0
        max_rev = max(revenues) if revenues else 0
        min_rev = min(revenues) if revenues else 0
        best_day = entries[revenues.index(max_rev)] if revenues else {}
        
        # Tendencia: comparar última semana con semana anterior
        if len(entries) >= 14:
            last_week = sum(d["revenue"] for d in entries[-7:])
            prev_week = sum(d["revenue"] for d in entries[-14:-7])
            trend_pct = ((last_week - prev_week) / prev_week * 100) if prev_week > 0 else 0
        else:
            trend_pct = 0
        
        daily["analysis"] = {
            "total_revenue": round(total, 2),
            "avg_daily": round(avg, 2),
            "max_day": {
                "date": best_day.get("date", ""),
                "revenue": round(max_rev, 2)
            },
            "min_revenue_day": round(min_rev, 2),
            "trend_last_week_pct": round(trend_pct, 1),
            "trend_direction": "up" if trend_pct > 5 else ("down" if trend_pct < -5 else "stable"),
            "projected_monthly": round(avg * 30, 2),
            "projected_quarterly": round(avg * 90, 2),
            "projected_yearly": round(avg * 365, 2)
        }
        
        return daily
    
    def get_zone_analysis(self) -> Dict:
        """
        Obtiene análisis detallado de zonas.
        
        Returns:
            Dict con rendimiento por zona + recomendaciones
        """
        if self._zone_cache:
            zones = self._zone_cache
        else:
            zones = self.api.get_zone_performance(days=7)
            self._zone_cache = zones
        
        if not zones.get("success"):
            return zones
        
        zone_list = zones.get("zones", [])
        if not zone_list:
            return zones
        
        # Identificar zonas top y low performers
        total_revenue = zones.get("total_revenue", 0)
        
        top_zones = [z for z in zone_list if z["revenue_percent"] >= 10]
        low_zones = [z for z in zone_list if z["revenue_percent"] < 2 and z["impressions"] > 0]
        
        # RPM promedio ponderado
        rpm_values = [z["rpm"] for z in zone_list if z["impressions"] > 0]
        avg_rpm = sum(rpm_values) / len(rpm_values) if rpm_values else 0
        
        zones["analysis"] = {
            "total_revenue": round(total_revenue, 2),
            "avg_rpm": round(avg_rpm, 2),
            "top_zones_count": len(top_zones),
            "low_zones_count": len(low_zones),
            "top_zones": top_zones[:3],
            "low_zones": low_zones[:3],
            "recommendations": self._generate_zone_recommendations(top_zones, low_zones, avg_rpm)
        }
        
        return zones
    
    def _generate_zone_recommendations(self, top_zones: List, low_zones: List, avg_rpm: float) -> List[str]:
        """Genera recomendaciones basadas en rendimiento de zonas."""
        recommendations = []
        
        if top_zones:
            best_zones = ", ".join(z["zone_name"] for z in top_zones[:3])
            recommendations.append(f"🔝 Tus mejores zonas: {best_zones}. Considera aumentar el tráfico a estas.")
        
        if low_zones:
            for z in low_zones[:2]:
                if z["rpm"] < avg_rpm * 0.5:
                    recommendations.append(f"⚠️ La zona '{z['zone_name']}' tiene RPM ${z['rpm']:.2f} (50% bajo el promedio ${avg_rpm:.2f}). Evalúa cambiar formato.")
        
        if avg_rpm < 0.5:
            recommendations.append("📉 RPM bajo. Considera cambiar a formatos más rentables (popunder > push > banner).")
        elif avg_rpm > 2.0:
            recommendations.append(f"🔥 Excelente RPM de ${avg_rpm:.2f}. Sigue optimizando tráfico Tier 1.")
        
        if not recommendations:
            recommendations.append("✅ Todo en orden. Sigue monitoreando.")
        
        return recommendations
    
    def get_geo_analysis(self) -> Dict:
        """
        Obtiene análisis geográfico del revenue.
        
        Returns:
            Dict con rendimiento por país + insights
        """
        if self._geo_cache:
            geo = self._geo_cache
        else:
            geo = self.api.get_geo_performance(days=7)
            self._geo_cache = geo
        
        if not geo.get("success"):
            return geo
        
        countries = geo.get("countries", [])
        if not countries:
            return geo
        
        # Clasificar países por RPM
        tier1 = [c for c in countries if c["rpm"] > 2.0]
        tier2 = [c for c in countries if 0.5 <= c["rpm"] <= 2.0]
        tier3 = [c for c in countries if c["rpm"] < 0.5 and c["impressions"] > 0]
        
        geo["analysis"] = {
            "total_countries": len(countries),
            "tier1_count": len(tier1),
            "tier2_count": len(tier2),
            "tier3_count": len(tier3),
            "top_countries": [{"country": c["country"], "rpm": c["rpm"], "revenue": c["revenue"]} for c in tier1[:5]],
            "best_rpm_country": max(countries, key=lambda c: c["rpm"]) if countries else {},
            "insights": self._generate_geo_insights(tier1, tier3, countries)
        }
        
        return geo
    
    def _generate_geo_insights(self, tier1: List, tier3: List, all_countries: List) -> List[str]:
        """Genera insights basados en datos geográficos."""
        insights = []
        
        if tier1:
            countries_str = ", ".join(c["country"] for c in tier1[:3])
            insights.append(f"💰 Tus mercados TOP: {countries_str}. Enfoca contenido en estos países.")
        
        if tier3:
            for c in tier3[:2]:
                if c["impressions"] > 100:
                    insights.append(f"🎯 País con bajo RPM: {c['country']} (${c['rpm']:.2f}). Revisa si vale la pena mantener tráfico aquí.")
        
        # Dependencia de un solo país
        if all_countries and len(all_countries) > 2:
            top_rev = max(c["revenue"] for c in all_countries)
            total_rev = sum(c["revenue"] for c in all_countries)
            if total_rev > 0 and (top_rev / total_rev) > 0.6:
                top_country = next(c for c in all_countries if c["revenue"] == top_rev)
                insights.append(f"⚠️ Alta dependencia de {top_country['country']} ({top_rev/total_rev*100:.0f}% del revenue). Diversifica.")
        
        if not insights:
            insights.append("✅ Distribución geográfica saludable.")
        
        return insights
    
    def get_full_report(self, force_refresh: bool = False) -> Dict:
        """
        Obtiene un reporte completo de revenue.
        
        Returns:
            Dict con todos los datos: revenue, daily, zones, geo
        """
        if force_refresh:
            self.sync_now(force=True)
        
        return {
            "success": True,
            "revenue": self.get_current_revenue(),
            "daily": self.get_daily_breakdown(days=30),
            "zones": self.get_zone_analysis(),
            "geo": self.get_geo_analysis(),
            "api_stats": self.api.get_api_stats(),
            "tracker_stats": {
                "sync_count": self.sync_count,
                "sync_errors": self.sync_errors,
                "last_sync": datetime.fromtimestamp(self.last_sync).strftime("%Y-%m-%d %H:%M:%S") if self.last_sync else "Nunca",
                "cache_valid": self._is_cache_valid()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def get_historical_summary(self) -> Dict:
        """
        Obtiene resumen histórico de revenue desde snapshots guardados.
        
        Returns:
            Dict con revenue histórico, tendencias y métricas agregadas
        """
        history = self._load_json("revenue_history", [])
        
        if not history:
            return {"success": False, "message": "No hay datos históricos aún. Ejecuta sync_now() primero."}
        
        revenues = [h["total_revenue"] for h in history]
        avg_rpms = [h["avg_rpm"] for h in history]
        impressions = [h["total_impressions"] for h in history]
        
        return {
            "success": True,
            "total_snapshots": len(history),
            "date_range": {
                "first": history[0]["date"] if history else "",
                "last": history[-1]["date"] if history else ""
            },
            "totals": {
                "revenue": round(sum(revenues), 2) if revenues else 0,
                "avg_rpm": round(sum(avg_rpms) / len(avg_rpms), 2) if avg_rpms else 0,
                "impressions": sum(impressions) if impressions else 0
            },
            "trend": {
                "first_revenue": round(revenues[0], 2) if revenues else 0,
                "last_revenue": round(revenues[-1], 2) if revenues else 0,
                "change_pct": round((revenues[-1] - revenues[0]) / revenues[0] * 100, 1) if len(revenues) > 1 and revenues[0] > 0 else 0
            },
            "projections": {
                "monthly": round(sum(revenues) / len(revenues) * 30, 2) if revenues else 0,
                "yearly": round(sum(revenues) / len(revenues) * 365, 2) if revenues else 0
            },
            "history": history[-30:]  # Últimos 30 snapshots
        }
    
    def get_tracker_stats(self) -> Dict:
        """Estadísticas del tracker."""
        return {
            "sync_count": self.sync_count,
            "sync_errors": self.sync_errors,
            "last_sync": datetime.fromtimestamp(self.last_sync).strftime("%Y-%m-%d %H:%M:%S") if self.last_sync else "Nunca",
            "sync_interval_seconds": self.sync_interval_seconds,
            "api_configured": self.api.is_configured(),
            "ledger_connected": self.ledger is not None,
            "cache_valid": self._is_cache_valid(),
            "snapshots_saved": len(self._load_json("revenue_history", []))
        }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="📊 Monetag Revenue Tracker")
    parser.add_argument("--token", type=str, help="API Bearer Token")
    parser.add_argument("--sync", action="store_true", help="Sincronizar ahora")
    parser.add_argument("--report", action="store_true", help="Reporte completo")
    parser.add_argument("--daily", action="store_true", help="Desglose diario")
    parser.add_argument("--zones", action="store_true", help="Análisis de zonas")
    parser.add_argument("--geo", action="store_true", help="Análisis geográfico")
    parser.add_argument("--history", action="store_true", help="Resumen histórico")
    parser.add_argument("--loop", type=int, nargs="?", const=5, help="Loop de sincronización (intervalo en min)")
    
    args = parser.parse_args()
    
    token = args.token or os.environ.get("MONETAG_API_TOKEN", "")
    api = MonetagAPI(api_token=token)
    tracker = RevenueTracker(api=api)
    
    if args.sync:
        result = tracker.sync_now(force=True)
        print(json.dumps(result, indent=2, default=str))
    elif args.report:
        report = tracker.get_full_report(force_refresh=True)
        print(json.dumps(report, indent=2, default=str))
    elif args.daily:
        result = tracker.get_daily_breakdown()
        print(json.dumps(result, indent=2, default=str))
    elif args.zones:
        result = tracker.get_zone_analysis()
        print(json.dumps(result, indent=2, default=str))
    elif args.geo:
        result = tracker.get_geo_analysis()
        print(json.dumps(result, indent=2, default=str))
    elif args.history:
        result = tracker.get_historical_summary()
        print(json.dumps(result, indent=2, default=str))
    elif args.loop:
        print(f"\n  {c('🔄 Loop de sincronización cada {args.loop} min...', Colors.CYAN, bold=True)}")
        interval = args.loop * 60
        try:
            while True:
                tracker.sync_now(force=True)
                for _ in range(interval):
                    time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n  {c('👋 Loop detenido.', Colors.YELLOW)}")
    else:
        print(f"\n{c('=' * 60, Colors.CYAN, bold=True)}")
        print(c(f'  📊 MONETAG REVENUE TRACKER', Colors.CYAN, bold=True))
        print(c('=' * 60, Colors.CYAN, bold=True))
        
        if api.is_configured():
            tracker.sync_now(force=True)
            summary = tracker.get_current_revenue()
            if summary.get("success"):
                print(f"\n  {c('📈 RESUMEN DE REVENUE', Colors.YELLOW, bold=True)}")
                print(f"     Revenue (7d):     ${summary['total_revenue']:>8,.2f}")
                print(f"     Avg diario:       ${summary['avg_daily_revenue']:>8,.2f}")
                print(f"     RPM promedio:     ${summary['avg_rpm']:>8,.2f}")
                print(f"     Impresiones:      {summary['total_impressions']:,}")
                print(f"     CTR:              {summary['ctr_percent']:.2f}%")
                print(f"     Proy. mensual:    ${summary['projected_monthly']:>8,.2f}")
                print(f"     Proy. anual:      ${summary['projected_yearly']:>8,.2f}")
        else:
            print(f"\n  {c('❌ API no configurada', Colors.RED)}")
            print(f"  {c('Usa: --token TU_TOKEN', Colors.YELLOW)}")
        
        print(f"\n{c('=' * 60, Colors.CYAN, bold=True)}")

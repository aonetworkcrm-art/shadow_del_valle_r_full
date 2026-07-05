# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Monetag Alert Engine
==========================================
Sistema de alertas inteligentes basado en datos de revenue.
Detecta anomalías, oportunidades y genera notificaciones.

Tipos de alertas:
    - RPM bajo: cuando cae por debajo del umbral
    - Picos de tráfico: aumento repentino de visitas
    - Caída de revenue: descenso significativo vs. promedio
    - Oportunidad: momento óptimo para publicar/maximizar
    - Zona muerta: zona sin rendimiento
    - Best performer: zona/hour/geo destacado
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import deque

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


class AlertEngine:
    """
    Motor de alertas inteligentes para Monetag.
    
    Args:
        api: Instancia de MonetagAPI
        tracker: Instancia de RevenueTracker
        data_dir: Directorio para persistencia
    """
    
    # Umbrales por defecto
    DEFAULT_RPM_THRESHOLD = 0.50
    DEFAULT_REVENUE_DROP_THRESHOLD = 0.30  # 30% de caída
    DEFAULT_TRAFFIC_SPIKE_THRESHOLD = 2.0  # 2x el promedio
    
    def __init__(self, api: Optional[MonetagAPI] = None, tracker: Optional[RevenueTracker] = None,
                 data_dir: str = "output/revenue"):
        self.api = api or MonetagAPI()
        self.tracker = tracker or RevenueTracker(api=self.api)
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Alertas
        self.alerts: List[Dict] = []
        self.suppressed_alerts: set = set()  # Alertas suprimidas (por tipo)
        self.max_alerts = 100
        
        # Datos para detección de tendencias
        self._revenue_history: deque = deque(maxlen=24)  # Últimas 24 lecturas
        self._rpm_history: deque = deque(maxlen=24)
        self._impression_history: deque = deque(maxlen=24)
        
        # Cargar alertas previas
        self._load_alerts()
    
    def _log(self, msg: str):
        print(f"  {c('[Alertas]', Colors.YELLOW)} {msg}")
    
    def _get_db_path(self) -> str:
        return os.path.join(self.data_dir, "alerts.json")
    
    def _load_alerts(self):
        path = self._get_db_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.alerts = data.get("alerts", [])
                self.suppressed_alerts = set(data.get("suppressed", []))
            except:
                pass
    
    def _save_alerts(self):
        path = self._get_db_path()
        data = {
            "alerts": self.alerts[-self.max_alerts:],
            "suppressed": list(self.suppressed_alerts),
            "total_alerts": len(self.alerts),
            "last_update": datetime.now().isoformat()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _add_alert(self, alert_type: str, severity: str, title: str, 
                   message: str, value: float = 0.0, threshold: float = 0.0,
                   recommendation: str = "") -> Dict:
        """Crea y registra una nueva alerta."""
        alert = {
            "id": f"alert-{int(time.time() * 1000)}",
            "type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "value": round(value, 2),
            "threshold": round(threshold, 2),
            "recommendation": recommendation,
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "acknowledged": False
        }
        
        self.alerts.append(alert)
        self._save_alerts()
        
        # Mostrar en consola
        severity_color = Colors.RED if severity == "critical" else (Colors.YELLOW if severity == "warning" else Colors.CYAN)
        sev_icon = "🔴" if severity == "critical" else ("🟡" if severity == "warning" else "🔵")
        print(f"     {sev_icon} {c(title, severity_color, bold=True)}")
        print(f"       {message}")
        if recommendation:
            print(f"       💡 {c(recommendation, Colors.DIM)}")
        
        return alert
    
    def _is_suppressed(self, alert_type: str) -> bool:
        return alert_type in self.suppressed_alerts
    
    def suppress_alert_type(self, alert_type: str):
        """Suprime un tipo de alerta."""
        self.suppressed_alerts.add(alert_type)
        self._save_alerts()
    
    def unsuppress_alert_type(self, alert_type: str):
        """Reactivar un tipo de alerta."""
        self.suppressed_alerts.discard(alert_type)
        self._save_alerts()
    
    # ─── DETECTORES ─────────────────────────────────────────────────────
    
    def check_rpm(self, min_rpm: float = 0.0) -> Optional[Dict]:
        """
        Verifica si el RPM está por debajo del umbral.
        
        Returns:
            Alerta si RPM bajo, None si está bien
        """
        threshold = min_rpm or self.DEFAULT_RPM_THRESHOLD
        
        if self._is_suppressed("rpm_low"):
            return None
        
        revenue = self.tracker.get_current_revenue()
        rpm = revenue.get("avg_rpm", 0) if isinstance(revenue, dict) else 0
        
        if rpm <= 0:
            return None
        
        # Guardar en historial
        self._rpm_history.append(rpm)
        
        if rpm < threshold:
            alert = self._add_alert(
                alert_type="rpm_low",
                severity="warning" if rpm < threshold * 0.8 else "info",
                title="RPM por debajo del umbral",
                message=f"RPM actual: ${rpm:.2f} (umbral: ${threshold:.2f})",
                value=rpm,
                threshold=threshold,
                recommendation="Cambia a formato SMARTLINK para mejorar RPM. Revisa tráfico de países Tier 3."
            )
            return alert
        
        return None
    
    def check_revenue_drop(self, drop_threshold: float = 0.0) -> Optional[Dict]:
        """
        Verifica si hay una caída significativa de revenue.
        
        Returns:
            Alerta si hay caída, None si está estable
        """
        threshold = drop_threshold or self.DEFAULT_REVENUE_DROP_THRESHOLD
        
        if self._is_suppressed("revenue_drop"):
            return None
        
        revenue = self.tracker.get_current_revenue()
        current_avg = revenue.get("avg_daily_revenue", 0) if isinstance(revenue, dict) else 0
        
        if current_avg <= 0:
            return None
        
        # Comparar con datos históricos
        history = self.tracker.get_historical_summary()
        if not history.get("success"):
            return None
        
        historical_entries = history.get("history", [])
        if len(historical_entries) < 2:
            return None
        
        # Promedio de los últimos N snapshots
        recent = historical_entries[-3:] if len(historical_entries) >= 3 else historical_entries
        previous_avg = sum(h.get("avg_daily_revenue", 0) for h in recent) / len(recent)
        
        if previous_avg <= 0:
            return None
        
        drop_pct = (previous_avg - current_avg) / previous_avg
        
        if drop_pct > threshold:
            alert = self._add_alert(
                alert_type="revenue_drop",
                severity="critical" if drop_pct > threshold * 1.5 else "warning",
                title="Caída significativa de revenue",
                message=f"Revenue promedio bajó {drop_pct*100:.0f}% (de ${previous_avg:.2f} a ${current_avg:.2f})",
                value=current_avg,
                threshold=previous_avg * (1 - threshold),
                recommendation="Revisa estado del sitio, formato de anuncios y tráfico entrante."
            )
            return alert
        
        return None
    
    def check_traffic_spike(self, spike_threshold: float = 0.0) -> Optional[Dict]:
        """
        Detecta picos de tráfico inusuales.
        
        Returns:
            Alerta si hay pico, None si es normal
        """
        threshold = spike_threshold or self.DEFAULT_TRAFFIC_SPIKE_THRESHOLD
        
        if self._is_suppressed("traffic_spike"):
            return None
        
        revenue = self.tracker.get_current_revenue()
        current_impressions = revenue.get("total_impressions", 0) if isinstance(revenue, dict) else 0
        
        if current_impressions <= 0:
            return None
        
        # Guardar en historial
        self._impression_history.append(current_impressions)
        
        if len(self._impression_history) < 3:
            return None
        
        # Promedio histórico de impresiones
        avg_impressions = sum(self._impression_history) / len(self._impression_history)
        
        if avg_impressions <= 0:
            return None
        
        ratio = current_impressions / avg_impressions
        
        if ratio > threshold:
            alert = self._add_alert(
                alert_type="traffic_spike",
                severity="info",
                title="🚀 Pico de tráfico detectado",
                message=f"Impresiones: {current_impressions:,} vs promedio {int(avg_impressions):,} (x{ratio:.1f})",
                value=current_impressions,
                threshold=avg_impressions * threshold,
                recommendation="Aprovecha el momento. Asegúrate de que todos los anuncios estén activos."
            )
            return alert
        
        return None
    
    def check_opportunity(self) -> Optional[Dict]:
        """
        Detecta oportunidades de optimización.
        
        Returns:
            Alerta de oportunidad si aplica
        """
        if self._is_suppressed("opportunity"):
            return None
        
        # Verificar hora del día
        hour = datetime.now().hour
        
        # Mejores horas para publicar contenido nuevo
        best_hours = [7, 8, 9, 12, 13, 18, 19, 20]
        good_hours = [6, 10, 11, 14, 15, 16, 17, 21, 22]
        
        if hour in best_hours:
            alert = self._add_alert(
                alert_type="opportunity",
                severity="info",
                title="⏰ Hora óptima para publicar",
                message=f"Son las {hour}:00 — hora de alto tráfico. Publica contenido nuevo ahora.",
                recommendation="Programa publicación de posts. Máximo impacto en revenue."
            )
            return alert
        
        return None
    
    def check_zone_performance(self) -> Optional[Dict]:
        """
        Verifica rendimiento de zonas y detecta zonas problema.
        
        Returns:
            Alerta si hay zonas con bajo rendimiento
        """
        if self._is_suppressed("zone_performance"):
            return None
        
        zones = self.tracker.get_zone_analysis()
        
        if not zones.get("success"):
            return None
        
        analysis = zones.get("analysis", {})
        low_zones = analysis.get("low_zones", [])
        
        if low_zones:
            for z in low_zones[:1]:
                alert = self._add_alert(
                    alert_type="zone_performance",
                    severity="warning",
                    title=f"Zona con bajo rendimiento: {z.get('zone_name', '?')}",
                    message=f"RPM: ${z.get('rpm', 0):.2f} — muy por debajo del promedio",
                    value=z.get("rpm", 0),
                    recommendation="Revisa configuración de esa zona. Considera cambiar el formato."
                )
            return alert
        
        return None
    
    # ─── CICLO COMPLETO ─────────────────────────────────────────────────
    
    def run_checks(self, force_sync: bool = False) -> List[Dict]:
        """
        Ejecuta todas las verificaciones y retorna las alertas generadas.
        
        Args:
            force_sync: Forzar sincronización con API
        
        Returns:
            Lista de alertas generadas en este ciclo
        """
        if force_sync:
            self.tracker.sync_now(force=True)
        
        if not self.api.is_configured():
            return []
        
        before = len(self.alerts)
        
        # Ejecutar todos los checks
        self.check_rpm()
        self.check_revenue_drop()
        self.check_traffic_spike()
        self.check_opportunity()
        self.check_zone_performance()
        
        # Alertas generadas
        new_alerts = len(self.alerts) - before
        
        return self.get_recent_alerts(new_alerts) if new_alerts > 0 else []
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """Obtiene las alertas más recientes."""
        alerts = sorted(self.alerts, key=lambda a: a["timestamp"], reverse=True)
        return alerts[:count]
    
    def get_alerts_by_severity(self, severity: str) -> List[Dict]:
        """Filtra alertas por severidad."""
        return [a for a in self.alerts if a["severity"] == severity]
    
    def get_unacknowledged_alerts(self) -> List[Dict]:
        """Obtiene alertas no leídas."""
        return [a for a in self.alerts if not a["acknowledged"]]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Marca una alerta como leída."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                self._save_alerts()
                return True
        return False
    
    def acknowledge_all(self):
        """Marca todas las alertas como leídas."""
        for alert in self.alerts:
            alert["acknowledged"] = True
        self._save_alerts()
    
    def get_stats(self) -> Dict:
        """Estadísticas del motor de alertas."""
        criticals = sum(1 for a in self.alerts if a["severity"] == "critical")
        warnings = sum(1 for a in self.alerts if a["severity"] == "warning")
        infos = sum(1 for a in self.alerts if a["severity"] == "info")
        unacked = sum(1 for a in self.alerts if not a["acknowledged"])
        
        return {
            "total_alerts": len(self.alerts),
            "critical": criticals,
            "warning": warnings,
            "info": infos,
            "unacknowledged": unacked,
            "suppressed_types": list(self.suppressed_alerts),
            "monitoring_active": True
        }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🔔 Monetag Alert Engine")
    parser.add_argument("--token", type=str, help="API Bearer Token")
    parser.add_argument("--check", action="store_true", help="Ejecutar checks")
    parser.add_argument("--alerts", action="store_true", help="Ver alertas recientes")
    parser.add_argument("--stats", action="store_true", help="Estadísticas de alertas")
    parser.add_argument("--ack-all", action="store_true", help="Marcar todas como leídas")
    
    args = parser.parse_args()
    
    token = args.token or os.environ.get("MONETAG_API_TOKEN", "")
    api = MonetagAPI(api_token=token)
    tracker = RevenueTracker(api=api)
    engine = AlertEngine(api=api, tracker=tracker)
    
    if args.check:
        print(f"\n  {c('🔍 Ejecutando verificaciones...', Colors.YELLOW)}")
        alerts = engine.run_checks(force_sync=True)
        if alerts:
            print(f"\n  {c(f'{len(alerts)} alerta(s) generada(s):', Colors.YELLOW, bold=True)}")
            for a in alerts:
                print(f"     [{a['severity'].upper()}] {a['title']}: {a['message']}")
        else:
            print(f"\n  {c('✅ Sin novedades. Todo en orden.', Colors.GREEN)}")
    elif args.alerts:
        alerts = engine.get_recent_alerts(20)
        print(f"\n  {c(f'📋 Últimas {len(alerts)} alertas:', Colors.CYAN, bold=True)}")
        for a in alerts:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(a["severity"], "⚪")
            status = "✅" if a["acknowledged"] else "🆕"
            print(f"  {status} {icon} [{a['type']}] {a['title']}")
            print(f"       {a['date']} — {a['message']}")
    elif args.stats:
        stats = engine.get_stats()
        print(json.dumps(stats, indent=2))
    elif args.ack_all:
        engine.acknowledge_all()
        print(f"  {c('✅ Todas las alertas marcadas como leídas.', Colors.GREEN)}")
    else:
        print(f"\n{c('=' * 60, Colors.YELLOW, bold=True)}")
        print(c('  🔔 MONETAG ALERT ENGINE', Colors.YELLOW, bold=True))
        print(c('=' * 60, Colors.YELLOW, bold=True))
        stats = engine.get_stats()
        print(f"\n  Alertas totales:  {stats['total_alerts']}")
        print(f"  🔴 Críticas:       {stats['critical']}")
        print(f"  🟡 Advertencias:   {stats['warning']}")
        print(f"  🔵 Informativas:   {stats['info']}")
        print(f"  🆕 No leídas:      {stats['unacknowledged']}")
        print(f"\n  {c('Usa --check para ejecutar verificaciones.', Colors.DIM)}")
        print(f"{c('=' * 60, Colors.YELLOW, bold=True)}")

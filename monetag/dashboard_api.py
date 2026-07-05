# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Monetag Dashboard API
===========================================
Endpoints Flask para el dashboard de revenue de Monetag.
Se integra con el sistema de rutas existente en dashboard/api.py.

Endpoints:
    GET  /api/monetag/status      — Estado de la conexión Monetag
    GET  /api/monetag/revenue     — Resumen de revenue en tiempo real
    GET  /api/monetag/daily       — Desglose diario (30 días)
    GET  /api/monetag/zones       — Análisis de zonas
    GET  /api/monetag/geo         — Análisis geográfico
    GET  /api/monetag/full-report — Reporte completo
    GET  /api/monetag/alerts      — Alertas recientes
    GET  /api/monetag/optimize    — Ciclo de optimización
    GET  /api/monetag/history     — Historial de revenue
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from flask import request

# Asegurar que podemos importar los módulos del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from .api_client import MonetagAPI
from .revenue_tracker import RevenueTracker
from .optimizer import MonetagOptimizer
from .alert_engine import AlertEngine


def create_monetag_routes(app, data_dir: str = None, config_path: str = "config/settings.json"):
    """
    Registra las rutas de Monetag en una app Flask existente.
    
    Args:
        app: Instancia de Flask
        data_dir: Directorio de datos
        config_path: Ruta al archivo de configuración
    """
    
    if data_dir is None:
        data_dir = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
    
    # Inicializar módulos (singleton perezoso)
    _api: Optional[MonetagAPI] = None
    _tracker: Optional[RevenueTracker] = None
    _optimizer: Optional[MonetagOptimizer] = None
    _alerts: Optional[AlertEngine] = None
    
    # Cargar configuración
    _config = {}
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                _config = json.load(f)
    except:
        pass
    
    def _get_api() -> MonetagAPI:
        nonlocal _api
        if _api is None:
            monetag_cfg = _config.get("monetag_api", {})
            token = monetag_cfg.get("api_token", os.environ.get("MONETAG_API_TOKEN", ""))
            _api = MonetagAPI(api_token=token)
        return _api
    
    def _get_tracker() -> RevenueTracker:
        nonlocal _tracker
        if _tracker is None:
            from core.ledger import Ledger
            ledger = Ledger(data_dir=os.path.join("output", "ledger"))
            _tracker = RevenueTracker(api=_get_api(), ledger=ledger)
        return _tracker
    
    def _get_optimizer() -> MonetagOptimizer:
        nonlocal _optimizer
        if _optimizer is None:
            _optimizer = MonetagOptimizer(api=_get_api(), tracker=_get_tracker(), 
                                         config_path=config_path)
        return _optimizer
    
    def _get_alerts() -> AlertEngine:
        nonlocal _alerts
        if _alerts is None:
            _alerts = AlertEngine(api=_get_api(), tracker=_get_tracker())
        return _alerts
    
    # ─── ENDPOINTS ──────────────────────────────────────────────────────
    
    @app.route("/api/monetag/status")
    def api_monetag_status():
        """Estado de la conexión con Monetag."""
        api = _get_api()
        tracker = _get_tracker()
        optimizer = _get_optimizer()
        alerts = _get_alerts()
        
        return {
            "success": True,
            "configured": api.is_configured(),
            "last_sync": datetime.fromtimestamp(tracker.last_sync).strftime("%Y-%m-%d %H:%M:%S") if tracker.last_sync else "Nunca",
            "api_stats": api.get_api_stats(),
            "tracker_stats": tracker.get_tracker_stats(),
            "optimizer_stats": optimizer.get_summary_stats(),
            "alert_stats": alerts.get_stats(),
            "timestamp": datetime.now().isoformat()
        }
    
    @app.route("/api/monetag/revenue")
    def api_monetag_revenue():
        """Resumen de revenue en tiempo real."""
        force = request.args.get("force", "0") == "1"
        tracker = _get_tracker()
        
        if force:
            tracker.sync_now(force=True)
        
        return tracker.get_current_revenue()
    
    @app.route("/api/monetag/daily")
    def api_monetag_daily():
        """Desglose diario de revenue."""
        days = int(request.args.get("days", 30))
        tracker = _get_tracker()
        return tracker.get_daily_breakdown(days=days)
    
    @app.route("/api/monetag/zones")
    def api_monetag_zones():
        """Análisis de zonas publicitarias."""
        tracker = _get_tracker()
        return tracker.get_zone_analysis()
    
    @app.route("/api/monetag/geo")
    def api_monetag_geo():
        """Análisis geográfico del tráfico."""
        tracker = _get_tracker()
        return tracker.get_geo_analysis()
    
    @app.route("/api/monetag/full-report")
    def api_monetag_full_report():
        """Reporte completo de revenue."""
        tracker = _get_tracker()
        return tracker.get_full_report(force_refresh=True)
    
    @app.route("/api/monetag/alerts")
    def api_monetag_alerts():
        """Alertas recientes."""
        alerts = _get_alerts()
        count = int(request.args.get("count", 20))
        return {
            "success": True,
            "alerts": alerts.get_recent_alerts(count),
            "stats": alerts.get_stats()
        }
    
    @app.route("/api/monetag/optimize", methods=["POST"])
    def api_monetag_optimize():
        """Ejecutar ciclo de optimización."""
        optimizer = _get_optimizer()
        result = optimizer.run_optimization_cycle(force=True)
        return result
    
    @app.route("/api/monetag/optimize/format")
    def api_monetag_optimize_format():
        """Análisis de formatos (sin ejecutar optimización completa)."""
        optimizer = _get_optimizer()
        return optimizer.analyze_format_performance(force_refresh=True)
    
    @app.route("/api/monetag/history")
    def api_monetag_history():
        """Historial de revenue."""
        tracker = _get_tracker()
        return tracker.get_historical_summary()
    
    @app.route("/api/monetag/alerts/acknowledge", methods=["POST"])
    def api_monetag_alerts_acknowledge():
        """Marcar alertas como leídas."""
        alerts = _get_alerts()
        data = request.json or {}
        alert_id = data.get("alert_id")
        
        if alert_id:
            alerts.acknowledge_alert(alert_id)
        else:
            alerts.acknowledge_all()
        
        return {"success": True}
    
    @app.route("/api/monetag/config", methods=["GET", "POST"])
    def api_monetag_config():
        """Obtener o actualizar configuración de Monetag."""
        if request.method == "POST":
            data = request.json or {}
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                
                if "monetag_api" not in cfg:
                    cfg["monetag_api"] = {}
                
                for k, v in data.items():
                    cfg["monetag_api"][k] = v
                
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                
                # Reinicializar API con nuevo token
                nonlocal _api
                _api = MonetagAPI(api_token=cfg["monetag_api"].get("api_token", ""))
                
                return {"success": True, "config": cfg["monetag_api"]}
            except Exception as e:
                return {"success": False, "error": str(e)}, 500
        else:
            monetag_cfg = _config.get("monetag_api", {})
            return {
                **monetag_cfg,
                "token_preview": monetag_cfg.get("api_token", "")[:8] + "..." if monetag_cfg.get("api_token") else ""
            }
    
    from monetag.api_client import Colors, c
    print(f"  {c('[Monetag]', Colors.CYAN)} Rutas API registradas:")
    print(f"     GET  /api/monetag/status")
    print(f"     GET  /api/monetag/revenue")
    print(f"     GET  /api/monetag/daily")
    print(f"     GET  /api/monetag/zones")
    print(f"     GET  /api/monetag/geo")
    print(f"     GET  /api/monetag/full-report")
    print(f"     GET  /api/monetag/alerts")
    print(f"     POST /api/monetag/optimize")
    print(f"     GET  /api/monetag/history")
    print(f"     GET/POST /api/monetag/config")
    
    return app

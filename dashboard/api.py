# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Dashboard API
===================================
Servidor Flask unificado que integra:
  - Dashboard web de revenue Monetag (frontend)
  - API REST de Monetag (backend)
  - Servicio de archivos estáticos

Arranque:
    python dashboard/api.py
    python dashboard/api.py --port 8080 --debug
"""

import json
import os
import sys
import argparse
from pathlib import Path

# Asegurar que podemos importar módulos del proyecto
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flask import Flask, render_template

# ── App global para gunicorn y WSGI servers ──────────────────
# Render, Railway y Docker usan: gunicorn dashboard.api:app
app = None


def create_app(config_path: str = None, data_dir: str = None):
    """
    Crea y configura la aplicación Flask completa.
    
    Args:
        config_path: Ruta al archivo de configuración settings.json
        data_dir: Directorio de datos para el Ledger
    
    Returns:
        Flask app configurada
    """
    # ── Resolver rutas por defecto ──────────────────────────────────
    if config_path is None:
        config_path = os.path.join(_project_root, "config", "settings.json")
    
    if data_dir is None:
        data_dir = os.path.join(_project_root, "output", "ledger")
    
    # ── Crear app Flask ─────────────────────────────────────────────
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    
    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path="/static"
    )
    
    # ── Ruta principal: Dashboard ───────────────────────────────────
    @app.route("/")
    def index():
        """Sirve el dashboard principal de Monetag Revenue."""
        return render_template("index.html")
    
    # ── Ruta SEO Oracle ─────────────────────────────────────────────
    @app.route("/seo-oracle")
    def seo_oracle():
        """Sirve el dashboard de SEO Oracle."""
        return render_template("seo_oracle.html")
    
    # ── Ruta de salud / healthcheck ─────────────────────────────────
    @app.route("/health")
    def health():
        """Endpoint de healthcheck para Railway/render."""
        return {
            "status": "ok",
            "app": "Shadow Del Valle R — Monetag Dashboard",
            "version": "2.0.0"
        }
    
    # ── CORS para desarrollo local ──────────────────────────────────
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
    
    # ── Registrar rutas SEO Oracle ──────────────────────────────────
    _register_seo_oracle_routes(app)
    
    # ── Registrar rutas de Monetag ──────────────────────────────────
    try:
        from monetag.dashboard_api import create_monetag_routes
        app = create_monetag_routes(app, data_dir=data_dir, config_path=config_path)
    except ImportError as e:
        print(f"  ⚠️  No se pudieron cargar las rutas Monetag: {e}")
        print(f"     Ejecuta 'pip install -r requirements.txt' si faltan dependencias.")
    except Exception as e:
        print(f"  ⚠️  Error al registrar rutas Monetag: {e}")
    
    return app


# ═══════════════════════════════════════════════════════════════
# 📊 SEO ORACLE — API Routes
# ═══════════════════════════════════════════════════════════════

def _register_seo_oracle_routes(app):
    """Registra los endpoints de la API SEO Oracle."""
    from core.radar import Radar, NICHES_DB_ENRICHED
    from decimal import Decimal
    from datetime import datetime
    
    radar = Radar()
    
    @app.route("/api/seo-oracle/niches")
    def seo_oracle_niches():
        """Lista todos los nichos disponibles."""
        return {
            "success": True,
            "niches": [n.to_dict() for n in NICHES_DB_ENRICHED]
        }
    
    @app.route("/api/seo-oracle/ranking-frr")
    def seo_oracle_ranking_frr():
        """Ranking completo por FRR."""
        ranking = radar.rank_by_frr(top_n=len(NICHES_DB_ENRICHED))
        return {"success": True, "ranking": ranking}
    
    @app.route("/api/seo-oracle/ranking-profit")
    def seo_oracle_ranking_profit():
        """Ranking completo por Profitability."""
        ranking = radar.rank_by_profitability()
        return {"success": True, "ranking": ranking}
    
    @app.route("/api/seo-oracle/projection")
    def seo_oracle_projection():
        """Proyección LOW/AVG/HIGH para un nicho."""
        from flask import request
        niche_id = request.args.get("niche_id", "")
        if not niche_id:
            return {"success": False, "error": "niche_id requerido"}
        
        visitors = int(request.args.get("visitors", 2000))
        ctr = float(request.args.get("ctr", 2.0))
        nodes = int(request.args.get("nodes", 3))
        
        proj = radar.calculate_yield_projection(
            niche_id=niche_id,
            monthly_visitors=visitors,
            ctr_pct=ctr,
            nodes_count=nodes
        )
        if not proj:
            return {"success": False, "error": "Nicho no encontrado"}
        
        return {"success": True, "projection": proj.to_dict()}
    
    @app.route("/api/seo-oracle/plan")
    def seo_oracle_plan():
        """Plan de contenido multi-nicho."""
        from flask import request
        niches_str = request.args.get("niches", "")
        if not niches_str:
            return {"success": False, "error": "niches requerido (separados por coma)"}
        
        selected = [n.strip() for n in niches_str.split(",") if n.strip()]
        if not selected:
            return {"success": False, "error": "Selecciona al menos un nicho"}
        
        plan = radar.create_content_plan(selected)
        return {"success": True, "plan": plan}
    
    @app.route("/api/seo-oracle/stats")
    def seo_oracle_stats():
        """Estadísticas SEO Oracle."""
        stats = radar.get_seo_stats()
        
        # Añadir evergreen 5yr
        stats["evergreen_5yr"] = radar.get_evergreen_multiplier(5)
        stats["success"] = True
        
        
        return stats
    
    @app.route("/api/seo-oracle/export")
    def seo_oracle_export():
        """Exporta reporte completo a JSON."""
        filepath = os.path.join(
            _project_root, "output", "reports",
            f"seo_oracle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        result = radar.export_report(filepath)
        return result


def parse_args():
    """Argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Shadow Del Valle R — Monetag Revenue Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Puerto del servidor (default: 5000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host del servidor (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Modo debug con autoreload"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Ruta al archivo settings.json"
    )
    return parser.parse_args()


def main():
    """Punto de entrada principal."""
    args = parse_args()
    
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🌑  Shadow Del Valle R — Monetag Dashboard 2.0   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    
    # Verificar token de Monetag
    token = os.environ.get("MONETAG_API_TOKEN", "")
    has_token = bool(token)
    
    # Verificar configuración local
    if not has_token:
        cfg_path = args.config or os.path.join(_project_root, "config", "settings.json")
        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
            token = cfg.get("monetag_api", {}).get("api_token", "")
            has_token = bool(token)
        except:
            pass
    
    print(f"  📍  Puerto:        {args.port}")
    print(f"  🔑  Monetag API:   {'✅ Configurado' if has_token else '❌ No configurado'}")
    print(f"  📁  Proyecto:      {_project_root}")
    print()
    
    if not has_token:
        print("  ⚠️  No se detectó token de Monetag.")
        print("     Configúralo en settings.json o variable de entorno MONETAG_API_TOKEN")
        print()
    
    app = create_app(config_path=args.config)
    
    print("  🚀  Servidor listo → http://localhost:{}".format(args.port))
    print()
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


# ── Inicializar app global para gunicorn ─────────────────────
# Cuando gunicorn importa 'dashboard.api:app', necesita una
# instancia lista. Si falla (dependencias sin instalar), se
# muestra advertencia pero no interrumpe el import.
if app is None:
    try:
        app = create_app()
    except Exception as e:
        import warnings
        warnings.warn(f"⚠️  No se pudo inicializar la app Flask: {e}")
        from flask import Flask
        app = Flask(__name__)
        app.route("/")(lambda: "{\"status\":\"error\",\"message\":\"Dashboard no disponible\"}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Shadow Del Valle R — Centro de Mando
Sistema AaaS de Arbitraje de Trafico
Version 1.0.0 — Junio 2026
"""

import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.radar import Radar
from core.silo_builder import Refinery
from core.silo_connector import SiloConnector
from core.freebuff_bridge import FreeBuffBridge
from core.deployer import Deployer
from core.ledger import Ledger
from core.oraculo import Oraculo


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

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def press_enter():
    msg = c("[Presiona Enter para continuar]", Colors.DIM)
    input("\n  " + msg + "  ")

radar = Radar()
refinery = Refinery()
connector = SiloConnector()
bridge = FreeBuffBridge()
deployer = Deployer()
ledger = Ledger()
oraculo = Oraculo()


def show_header():
    clear_screen()
    print()
    print(c("=" * 58, Colors.CYAN, bold=True))
    print(c("  SHADOW DEL VALLE R — CENTRO DE MANDO", Colors.CYAN, bold=True))
    print(c('  "Madera refinada que solo existe aqui"', Colors.DIM))
    print(c("-" * 58, Colors.CYAN))
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(c("  v1.0.0 · " + fecha, Colors.DIM))
    print()


def menu_option(num, text, desc=""):
    n_str = str(num)
    print("  " + c("[" + n_str + "]", Colors.GREEN, bold=True) + " " + c(text, Colors.CYAN))
    if desc:
        print("       " + c(desc, Colors.DIM))


def show_radar():
    show_header()
    print(c("  RADAR PREDICTIVO — Factor de Rentabilidad Relativa", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))

    resultados = radar.escanear_todos()

    print("\n  {:<38} {:>7} {:>10} {:>14}".format('Nicho','CPC','FRR','Estado'))
    print(c("  " + "-" * 69, Colors.DIM))

    for r in sorted(resultados, key=lambda x: x.frr, reverse=True):
        estado = c("APTO", Colors.GREEN) if r.apto else c("DESCARTADO", Colors.RED)
        cpc_str = "${:.0f}".format(r.nicho['cpc_avg'])
        frr_color = Colors.GREEN if r.frr >= radar.umbral_minimo else Colors.RED
        print("  {:<36} {:>7} {:>8}  {}".format(
            r.nicho['name'][:36], cpc_str,
            c("{:.2f}".format(r.frr), frr_color, bold=True), estado))

    aptos = sum(1 for r in resultados if r.apto)
    print("\n  " + c("Umbral FRR:", Colors.YELLOW) + " " + str(radar.umbral_minimo))
    print("  " + c("Nichos aptos:", Colors.GREEN) + " {}/{}".format(aptos, len(resultados)))

    proy = radar.proyectar_ingreso_diario(posts_por_dia=4, clicks_por_post=50)
    print("\n  " + c("PROYECCION (50 clicks/post/dia):", Colors.YELLOW, bold=True))
    print("  " + c("Ingreso diario:", Colors.GREEN) + "    ${:>8,.2f}".format(proy['ingreso_diario_promedio']))
    print("  " + c("Ingreso mensual:", Colors.GREEN) + "   ${:>8,.2f}".format(proy['ingreso_mensual']))
    print("  " + c("Ingreso anual:", Colors.GREEN) + "     ${:>8,.2f}".format(proy['ingreso_anual']))
    press_enter()


def show_ledger():
    show_header()
    ledger.mostrar_dashboard()
    print("\n  " + c("Ultimas transacciones:", Colors.YELLOW, bold=True))
    for t in ledger.get_historial_reciente(8):
        emoji_map = {"ingreso": "💰", "gasto": "💳", "post": "📝", "proyeccion": "📈"}
        emoji = emoji_map.get(t["tipo"], "📌")
        tc = Colors.GREEN if t["tipo"] == "ingreso" else (Colors.RED if t["tipo"] == "gasto" else Colors.CYAN)
        monto_val = t['monto']
        monto_str = "${:>8,.2f}".format(monto_val)
        print("  {} {:<42} {}  {}".format(emoji, t['concepto'][:40], c(monto_str, tc), c(t['fecha_simple'], Colors.DIM)))
    press_enter()


def show_generator():
    show_header()
    print(c("  GENERADOR DE POSTS — Forja de Contenido", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))

    print("\n  " + c("Selecciona un nicho:", Colors.YELLOW))
    from core.radar import NICHOS_DB
    for i, n in enumerate(NICHOS_DB, 1):
        frr = radar.frr_por_nicho(n["id"])
        cpc_avg = n["cpc_avg"]
        cpc_str = "${:.0f}".format(cpc_avg)
        frr_str = "FRR: {:.2f}".format(frr) if frr else ""
        print("  {} {:<35} {} CPC  {}".format(
            c("[" + str(i) + "]", Colors.GREEN),
            n['name'][:35],
            c(cpc_str, Colors.CYAN),
            c(frr_str, Colors.DIM)))

    print("\n  " + c("[A]", Colors.GREEN) + " Generar para TODOS los nichos aptos")
    print("  " + c("[0]", Colors.RED) + " Volver")

    try:
        choice = input("\n  " + c(">", Colors.GREEN) + " Opcion: ").strip().upper()
    except (KeyboardInterrupt, EOFError):
        return

    if choice == "0":
        return
    elif choice == "A":
        resultados = radar.escanear_todos()
        aptos = [r.nicho for r in resultados if r.apto]
        for nicho in aptos[:3]:
            from main_agent import ShadowDelValleAgent
            agent = ShadowDelValleAgent()
            agent._generar_post(nicho)
            print()
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(NICHOS_DB):
                from main_agent import ShadowDelValleAgent
                agent = ShadowDelValleAgent()
                agent._generar_post(NICHOS_DB[idx])
        except (ValueError, IndexError):
            print("\n  " + c("Opcion invalida", Colors.RED))
    press_enter()


def show_deploy():
    show_header()
    print(c("  DEPLOY — Publicar a Produccion", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))

    preparado = deployer.preparar_para_deploy()
    if preparado.get("success"):
        total_archivos = preparado['total_archivos']
        tam_total = preparado['tamano_total_kb']
        print("\n  " + c("Archivos listos para deploy:", Colors.GREEN, bold=True))
        print("  Total: " + c(str(total_archivos), Colors.GREEN) + " posts")
        print("  Tamano total: " + c(str(tam_total) + " KB", Colors.CYAN))
        for f in preparado["archivos"]:
            print("  * " + c(f['archivo'], Colors.CYAN) + " (" + str(f['tamano_kb']) + " KB)")
        print("\n  " + c("Para deployar a produccion:", Colors.YELLOW))
        print("  1. Activa 'github.auto_push = true' en config/settings.json")
        print("  2. O copia los archivos de output/posts/ manualmente")
        print("  3. O usa Vercel CLI: vercel --prod")
    else:
        print("\n  " + c(preparado.get('error', 'No hay archivos'), Colors.YELLOW))
    press_enter()


def show_config():
    show_header()
    print(c("  CONFIGURACION — Control del Sistema", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))

    config_path = "config/settings.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except:
        config = {}

    scheduler = config.get("scheduler", {})
    radar_cfg = config.get("radar", {})
    monetag = config.get("monetag", {})

    print("\n  " + c("AGENTE:", Colors.YELLOW, bold=True))
    activo = scheduler.get('agente_activo', True)
    status_color = Colors.GREEN if activo else Colors.RED
    status_str = "ACTIVO" if activo else "PAUSADO"
    print("  Estado:        " + c(status_str, status_color))
    print("  Intervalo:     " + str(scheduler.get('intervalo_generacion_horas', 4.0)) + "h")
    print("  Max posts/dia: " + str(scheduler.get('max_posts_por_dia', 6)))
    print("  Estrategia:    " + scheduler.get('estrategia', 'rotating'))

    print("\n  " + c("RADAR:", Colors.YELLOW, bold=True))
    print("  Umbral FRR:    " + str(radar_cfg.get('umbral_frr_minimo', 150.0)))
    cpc_min = radar_cfg.get('cpc_minimo', 80.0)
    print("  CPC minimo:    $" + str(cpc_min))

    print("\n  " + c("MONETAG:", Colors.YELLOW, bold=True))
    m_activo = monetag.get('habilitado', False)
    m_color = Colors.GREEN if m_activo else Colors.RED
    m_str = "ACTIVO" if m_activo else "DESACTIVADO"
    print("  Estado:        " + c(m_str, m_color))
    print("  Site ID:       " + monetag.get('site_id', 'No configurado'))

    print("\n  " + c("Opciones:", Colors.YELLOW))
    print("  Para cambiar la configuracion, edita: config/settings.json")
    print("  O usa el kill switch: python main_agent.py --kill-switch off")
    press_enter()


def show_agent():
    show_header()
    print(c("  AGENTE AUTONOMO — Modo AaaS", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))

    print("\n  " + c("ADVERTENCIA:", Colors.RED, bold=True) + " El agente correra en segundo plano.")
    print("  Presiona " + c("Ctrl+C", Colors.YELLOW) + " para detenerlo.")

    print("\n  " + c("[1]", Colors.GREEN) + " Iniciar agente (loop infinito)")
    print("  " + c("[2]", Colors.GREEN) + " Ejecutar una ronda")
    print("  " + c("[3]", Colors.GREEN) + " Ver estado del agente")
    print("  " + c("[0]", Colors.RED) + " Volver")

    try:
        choice = input("\n  " + c(">", Colors.GREEN) + " Opcion: ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if choice == "1":
        from main_agent import ShadowDelValleAgent
        agent = ShadowDelValleAgent()
        try:
            agent.run()
        except KeyboardInterrupt:
            print("\n\n  " + c("Agente detenido.", Colors.YELLOW))
    elif choice == "2":
        from main_agent import ShadowDelValleAgent
        agent = ShadowDelValleAgent()
        agent.run_once()
        press_enter()
    elif choice == "3":
        from main_agent import ShadowDelValleAgent
        agent = ShadowDelValleAgent()
        agent.show_status()
        press_enter()


def show_oraculo():
    show_header()
    print(c("  ORACULO SISMICO — Monitoreo en Tiempo Real", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))
    
    oraculo.mostrar_dashboard()
    
    print("\n  " + c("[1]", Colors.GREEN) + " Escanear ahora")
    print("  " + c("[2]", Colors.GREEN) + " Iniciar monitoreo continuo")
    print("  " + c("[3]", Colors.GREEN) + " Configurar WhatsApp")
    print("  " + c("[0]", Colors.RED) + " Volver")
    
    try:
        choice = input("\n  " + c(">", Colors.GREEN) + " Opcion: ").strip()
    except (KeyboardInterrupt, EOFError):
        return
    
    if choice == "1":
        oraculo.escanear_ahora()
        press_enter()
    elif choice == "2":
        print(f"\n  {c('Iniciando monitoreo...', Colors.YELLOW)}")
        print(f"  {c('Presiona Ctrl+C para detener', Colors.DIM)}")
        oraculo.run()
    elif choice == "3":
        show_header()
        print(c("  CONFIGURAR WHATSAPP", Colors.YELLOW, bold=True))
        print(c("  " + "=" * 50, Colors.DIM))
        print('''
  Para activar alertas sismicas a WhatsApp:
  
  1. Agrega este numero a tus contactos:
     +34 613 01 49 37 (CallMeBot)
  
  2. Enviale este mensaje EXACTO:
     "I allow callmebot to send me messages"
  
  3. Te respondera con tu API key
  
  4. Ingresa los datos aqui abajo:
        ''')
        
        phone = input("  " + c("Telefono (ej: +1809XXXXXX): ", Colors.GREEN)).strip()
        apikey = input("  " + c("API Key de CallMeBot: ", Colors.GREEN)).strip()
        
        if phone and apikey:
            try:
                config_path = "config/settings.json"
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                cfg["whatsapp"] = cfg.get("whatsapp", {})
                cfg["whatsapp"]["habilitado"] = True
                cfg["whatsapp"]["phone"] = phone
                cfg["whatsapp"]["apikey"] = apikey
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                # Recargar oraculo
                oraculo.config = oraculo._load_config(config_path)
                print("\n  " + c("WhatsApp configurado exitosamente!", Colors.GREEN, bold=True))
            except Exception as e:
                print("\n  " + c(f"Error guardando config: {e}", Colors.RED))
        else:
            print("\n  " + c("Configuracion cancelada.", Colors.YELLOW))
        press_enter()


def show_monetag():
    """Menú de Monetag Revenue — Dashboard + Optimización."""
    show_header()
    print(c("  💰 MONETAG REVENUE — Centro de Optimización", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))
    
    # Verificar estado de conexión
    token = os.environ.get("MONETAG_API_TOKEN", "")
    try:
        cfg_path = "config/settings.json"
        if not token and os.path.exists(cfg_path):
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
            token = cfg.get("monetag_api", {}).get("api_token", "")
    except:
        pass
    
    has_token = bool(token)
    token_status = c("✅ CONFIGURADO" if has_token else "❌ NO CONFIGURADO",
                     Colors.GREEN if has_token else Colors.RED, bold=True)
    print(f"\n  Estado API: {token_status}")
    
    # Intentar obtener revenue si hay conexión
    if has_token:
        try:
            from monetag.api_client import MonetagAPI
            from monetag.revenue_tracker import RevenueTracker
            from core.ledger import Ledger
            api = MonetagAPI(api_token=token)
            status = api.test_connection()
            if status.get("success"):
                print(f"  Conexión:    {c('✅ OK', Colors.GREEN)}")
                stats = api.get_api_stats()
                if stats.get("ultima_request"):
                    print(f"  Última sync: {stats['ultima_request']}")
                # Revenue rápido
                try:
                    rev = api.get_revenue_summary(period="last_7_days")
                    if rev.get("success"):
                        print(f"  Revenue 7d:  {c('$' + str(rev.get('total_revenue', 0)), Colors.CYAN, bold=True)}")
                        print(f"  RPM prom:    ${rev.get('avg_rpm', 0):.2f}")
                except:
                    pass
            else:
                print(f"  Conexión:    {c('❌ Error: ' + status.get('error', 'desconocido'), Colors.RED)}")
        except ImportError as e:
            print(f"  Módulos:     {c('⚠️ No instalados: ' + str(e), Colors.YELLOW)}")
        except Exception as e:
            print(f"  Error:       {c(str(e)[:60], Colors.RED)}")
    
    print(f"\n  {c('OPCIONES:', Colors.YELLOW, bold=True)}")
    print()
    print(f"  {c('[1]', Colors.GREEN)} {c('🚀 Arrancar Dashboard Web', Colors.CYAN)}    — Abre el panel de revenue en vivo")
    print(f"  {c('[2]', Colors.GREEN)} {c('📊 Sincronizar Revenue', Colors.CYAN)}        — Forzar sync con API de Monetag")
    print(f"  {c('[3]', Colors.GREEN)} {c('⚡ Ejecutar Optimización', Colors.CYAN)}       — Analizar formatos + recomendar")
    print(f"  {c('[4]', Colors.GREEN)} {c('🔔 Ver Alertas', Colors.CYAN)}                 — Alertas inteligentes del sistema")
    print(f"  {c('[5]', Colors.GREEN)} {c('🛠️  Configurar API Token', Colors.CYAN)}       — Cambiar token de Monetag")
    print()
    print(f"  {c('[0]', Colors.RED)} {c('Volver', Colors.CYAN)}")
    
    try:
        choice = input(f"\n  {c('>', Colors.GREEN)} Opción: ").strip()
    except (KeyboardInterrupt, EOFError):
        return
    
    if choice == "1":
        # Arrancar Dashboard Web
        show_header()
        print(f"  {c('🚀 Iniciando Dashboard Web...', Colors.YELLOW)}")
        print(f"  {c('Presiona Ctrl+C para detener el servidor', Colors.DIM)}")
        print()
        try:
            from dashboard.api import create_app
            app = create_app()
            import threading
            import webbrowser
            
            def open_browser():
                import time
                time.sleep(2)
                webbrowser.open("http://localhost:5000")
            
            threading.Thread(target=open_browser, daemon=True).start()
            print(f"  {c('Dashboard → http://localhost:5000', Colors.CYAN, bold=True)}")
            print()
            app.run(host="0.0.0.0", port=5000, debug=False)
        except ImportError as e:
            print(f"\n  {c('❌ Error: ' + str(e), Colors.RED)}")
            print(f"  Para arrancar manualmente: python dashboard/api.py")
            press_enter()
        except KeyboardInterrupt:
            print(f"\n  {c('Servidor detenido.', Colors.YELLOW)}")
    
    elif choice == "2":
        # Sincronizar Revenue
        if not has_token:
            print(f"\n  {c('❌ No hay token de Monetag configurado.', Colors.RED)}")
            print(f"  Configúralo en opción [5] o en settings.json")
            press_enter()
            return
        show_header()
        print(f"  {c('🔄 Sincronizando revenue con Monetag...', Colors.YELLOW)}")
        try:
            from monetag.revenue_tracker import RevenueTracker
            from core.ledger import Ledger
            from monetag.api_client import MonetagAPI
            api = MonetagAPI(api_token=token)
            ledger = Ledger(data_dir=os.path.join("output", "ledger"))
            tracker = RevenueTracker(api=api, ledger=ledger)
            result = tracker.sync_now(force=True)
            if result.get("success"):
                print(f"\n  {c('✅ Revenue sincronizado', Colors.GREEN, bold=True)}")
                print(f"  Revenue:     {c('$' + str(result.get('current_revenue', {}).get('total_revenue', 0)), Colors.CYAN)}")
                print(f"  Impresiones: {result.get('current_revenue', {}).get('total_impressions', 0)}")
                print(f"  RPM:         ${result.get('current_revenue', {}).get('avg_rpm', 0):.2f}")
            else:
                print(f"\n  {c('⚠️ Sincronización parcial', Colors.YELLOW)}")
                if result.get("error"):
                    print(f"  Error: {c(str(result['error'])[:80], Colors.RED)}")
        except Exception as e:
            print(f"\n  {c('❌ Error: ' + str(e)[:100], Colors.RED)}")
        press_enter()
    
    elif choice == "3":
        # Ejecutar Optimización
        if not has_token:
            print(f"\n  {c('❌ No hay token de Monetag configurado.', Colors.RED)}")
            press_enter()
            return
        show_header()
        print(f"  {c('⚡ Ejecutando ciclo de optimización...', Colors.YELLOW, bold=True)}")
        print(f"  {c('Analizando formatos, RPM, y generando recomendaciones...', Colors.DIM)}")
        try:
            from monetag.optimizer import MonetagOptimizer
            from monetag.revenue_tracker import RevenueTracker
            from monetag.api_client import MonetagAPI
            from core.ledger import Ledger
            api = MonetagAPI(api_token=token)
            ledger = Ledger(data_dir=os.path.join("output", "ledger"))
            tracker = RevenueTracker(api=api, ledger=ledger)
            optimizer = MonetagOptimizer(api=api, tracker=tracker,
                                         config_path="config/settings.json")
            result = optimizer.run_optimization_cycle(force=True)
            
            if result.get("format_analysis"):
                formats = result["format_analysis"].get("formats", [])
                if formats:
                    print(f"\n  {c('📊 ANÁLISIS DE FORMATOS', Colors.YELLOW, bold=True)}")
                    for f in formats:
                        color = Colors.GREEN if f.get('gap_to_avg', -10) > 0 else (Colors.YELLOW if f.get('gap_to_avg', -10) > -1 else Colors.RED)
                        print(f"  {f['format']:<20} {c('$' + str(f.get('current_rpm', 0)), color)}  {f.get('status', '')}")
            
            if result.get("recommendations"):
                print(f"\n  {c('💡 RECOMENDACIONES', Colors.YELLOW, bold=True)}")
                for r in result["recommendations"]:
                    print(f"  • {r}")
            
            print(f"\n  {c('✅ Optimización completada', Colors.GREEN, bold=True)}")
        except Exception as e:
            print(f"\n  {c('❌ Error: ' + str(e)[:100], Colors.RED)}")
        press_enter()
    
    elif choice == "4":
        # Ver Alertas
        if not has_token:
            print(f"\n  {c('❌ No hay token de Monetag configurado.', Colors.RED)}")
            press_enter()
            return
        show_header()
        print(f"  {c('🔔 ALERTAS DEL SISTEMA', Colors.YELLOW, bold=True)}")
        print(c("  " + "=" * 50, Colors.DIM))
        try:
            from monetag.alert_engine import AlertEngine
            from monetag.revenue_tracker import RevenueTracker
            from monetag.api_client import MonetagAPI
            from core.ledger import Ledger
            api = MonetagAPI(api_token=token)
            ledger = Ledger(data_dir=os.path.join("output", "ledger"))
            tracker = RevenueTracker(api=api, ledger=ledger)
            alerts = AlertEngine(api=api, tracker=tracker)
            alerts.run_checks(force_sync=True)
            alert_list = alerts.get_recent_alerts(15)
            stats = alerts.get_stats()
            
            print(f"\n  {c('Estadísticas:', Colors.YELLOW)}")
            print(f"  Total alertas: {stats.get('total_triggered', 0)}")
            print(f"  Sin leer:      {stats.get('unacknowledged', 0)}")
            print()
            
            if alert_list:
                for a in alert_list:
                    icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(a.get("severity"), "⚪")
                    color = {"critical": Colors.RED, "warning": Colors.YELLOW, "info": Colors.CYAN}.get(a.get("severity"), Colors.DIM)
                    title = a.get("title", "Alerta")
                    msg = a.get("message", "")
                    date = a.get("date", "")
                    print(f"  {icon} {c(title, color, bold=True)}")
                    if msg:
                        print(f"     {c(msg, Colors.DIM)}")
                    if date:
                        print(f"     {c(date, Colors.DIM)}")
                    print()
            else:
                print(f"  {c('🎉 Sin alertas. Todo en orden.', Colors.GREEN)}")
        except Exception as e:
            print(f"\n  {c('❌ Error: ' + str(e)[:100], Colors.RED)}")
        press_enter()
    
    elif choice == "5":
        # Configurar API Token
        show_header()
        print(f"  {c('🛠️  CONFIGURAR API TOKEN DE MONETAG', Colors.YELLOW, bold=True)}")
        print(c("  " + "=" * 50, Colors.DIM))
        print(f"\n  Token actual: {c(token[:12] + '...' + token[-4:] if token else 'No configurado', Colors.CYAN)}")
        print()
        new_token = input(f"  {c('Nuevo token (deja vacío para cancelar):', Colors.GREEN)} ").strip()
        
        if new_token:
            try:
                with open("config/settings.json", "r") as f:
                    cfg = json.load(f)
                if "monetag_api" not in cfg:
                    cfg["monetag_api"] = {}
                cfg["monetag_api"]["api_token"] = new_token
                with open("config/settings.json", "w") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                os.environ["MONETAG_API_TOKEN"] = new_token
                print(f"\n  {c('✅ Token actualizado correctamente', Colors.GREEN, bold=True)}")
            except Exception as e:
                print(f"\n  {c('❌ Error guardando: ' + str(e), Colors.RED)}")
        press_enter()


def show_seo_oracle():
    """Menú de SEO Oracle — Inteligencia de Nichos, separado del Radar."""
    while True:
        show_header()
        print(c("  📊 SEO ORACLE — Inteligencia de Nichos", Colors.YELLOW, bold=True))
        print(c("  " + "=" * 50, Colors.DIM))
        print()
        
        print(c("  OPCIONES:", Colors.YELLOW, bold=True))
        print()
        print(f"  {c('[1]', Colors.GREEN)} {c('🏆 Ranking por FRR', Colors.CYAN)}           — Top 15 nichos con FRR + Profitability")
        print(f"  {c('[2]', Colors.GREEN)} {c('🏆 Ranking por Profitability', Colors.CYAN)}   — Score compuesto CPC × Demanda × Evergreen")
        print(f"  {c('[3]', Colors.GREEN)} {c('📈 Proyección por Nicho', Colors.CYAN)}        — LOW/AVG/HIGH + confidence")
        print(f"  {c('[4]', Colors.GREEN)} {c('📋 Plan de Contenido', Colors.CYAN)}           — Multi-nicho con ingresos totales")
        print(f"  {c('[5]', Colors.GREEN)} {c('📊 Stats SEO Oracle', Colors.CYAN)}            — Estadísticas unificadas")
        print(f"  {c('[6]', Colors.GREEN)} {c('💾 Exportar Reporte', Colors.CYAN)}            — Guardar reporte a JSON")
        print(f"  {c('[7]', Colors.GREEN)} {c('🌿 Evergreen Multiplier', Colors.CYAN)}        — Factor de decrecimiento anual")
        print()
        print(f"  {c('[0]', Colors.RED)} {c('Volver', Colors.CYAN)}")
        print()
        
        try:
            choice = input("  " + c(">", Colors.GREEN) + " Opcion: ").strip()
        except (KeyboardInterrupt, EOFError):
            return
        
        if choice == "1":
            # Ranking por FRR
            show_header()
            print(f"  {c('🏆 RANKING POR FRR (Top 15)', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            print(f"  {'Nicho':<40} {'CPC':>6} {'FRR':>10} {'Profit':>10} {'Diff':>8} {'Apto':>6}")
            print(c("  " + "-" * 80, Colors.DIM))
            ranking = radar.rank_by_frr(top_n=15)
            for i, r in enumerate(ranking, 1):
                apto_str = c("✅", Colors.GREEN) if r['apto'] else c("❌", Colors.RED)
                print(f"  {i:<2} {r['name'][:38]:<40} ${r['cpc_avg']:>4.0f} {r['frr']:>10.0f} {r['profitability_score']:>10.0f} {r['difficulty'][:7]:>8} {apto_str}")
            press_enter()
        
        elif choice == "2":
            show_header()
            print(f"  {c('🏆 RANKING POR PROFITABILITY', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            print(f"  {'Nicho':<40} {'CPC':>6} {'Score':>10} {'FRR':>10} {'Evg':>5} {'Diff':>8}")
            print(c("  " + "-" * 80, Colors.DIM))
            ranking = radar.rank_by_profitability()
            for i, r in enumerate(ranking, 1):
                print(f"  {i:<2} {r['name'][:38]:<40} ${r['cpc_avg']:>4.0f} {r['profitability_score']:>10.0f} {r['frr']:>10.0f} {r['evergreen']:>5} {r['difficulty'][:7]:>8}")
            press_enter()
        
        elif choice == "3":
            show_header()
            print(f"  {c('📈 PROYECCIÓN DE INGRESOS', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            print(f"\n  Selecciona un nicho:")
            from core.radar import NICHES_DB_ENRICHED
            for i, n in enumerate(NICHES_DB_ENRICHED, 1):
                print(f"  {c(f'[{i}]', Colors.GREEN)} {n.name[:45]:<45} ${float(n.cpc_avg):>4.0f}")
            print(f"\n  {c('[A]', Colors.GREEN)} Proyectar TODOS")
            print(f"  {c('[0]', Colors.RED)} Volver")
            print()
            try:
                sub = input("  " + c(">", Colors.GREEN) + " Nicho: ").strip().upper()
            except (KeyboardInterrupt, EOFError):
                continue
            
            if sub == "0":
                continue
            elif sub == "A":
                niche_ids = [n.id for n in NICHES_DB_ENRICHED]
            else:
                try:
                    idx = int(sub) - 1
                    if 0 <= idx < len(NICHES_DB_ENRICHED):
                        niche_ids = [NICHES_DB_ENRICHED[idx].id]
                    else:
                        continue
                except ValueError:
                    continue
            
            show_header()
            print(f"  {c('📈 PROYECCIÓN de Ingresos', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            for nid in niche_ids:
                proj = radar.calculate_yield_projection(
                    niche_id=nid, monthly_visitors=2000, ctr_pct=2.0, nodes_count=3
                )
                if proj:
                    p = proj.to_dict()
                    conf_color = {'muy_alta': Colors.GREEN, 'alta': Colors.GREEN, 'media': Colors.YELLOW, 'baja': Colors.RED}.get(p['confidence'], Colors.DIM)
                    print(f"\n  {c(p['niche'][:45], Colors.CYAN, bold=True)}")
                    print(f"  Visitantes/mes: {p['monthly_visitors_total']:>6,} | Clicks: {p['clicks_monthly']:,}")
                    print(f"  CPC rango: ${p['cpc_range']['min']:.0f} - ${p['cpc_range']['max']:.0f}")
                    print(f"  Mensual:  {c(f'${p['monthly_revenue']['low']:>8,.2f}', Colors.YELLOW)}  {c(f'${p['monthly_revenue']['avg']:>8,.2f}', Colors.CYAN, bold=True)}  {c(f'${p['monthly_revenue']['high']:>8,.2f}', Colors.GREEN)}")
                    print(f"  Anual:    {c(f'${p['yearly_revenue']['low']:>8,.2f}', Colors.YELLOW)}  {c(f'${p['yearly_revenue']['avg']:>8,.2f}', Colors.CYAN, bold=True)}  {c(f'${p['yearly_revenue']['high']:>8,.2f}', Colors.GREEN)}")
                    print(f"  Confianza: {c(p['confidence'], conf_color, bold=True)}")
            press_enter()
        
        elif choice == "4":
            show_header()
            print(f"  {c('📋 PLAN DE CONTENIDO MULTI-NICHO', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            print(f"\n  Selecciona nichos (separados por coma):")
            from core.radar import NICHES_DB_ENRICHED
            for i, n in enumerate(NICHES_DB_ENRICHED, 1):
                print(f"  {c(f'[{i}]', Colors.GREEN)} {n.name[:45]:<45} ${float(n.cpc_avg):>4.0f}")
            print(f"\n  {c('[A]', Colors.GREEN)} Todos")
            print(f"  {c('[T]', Colors.GREEN)} Top 5 FRR")
            print(f"  {c('[0]', Colors.RED)} Volver")
            print()
            try:
                sub = input("  " + c(">", Colors.GREEN) + " Nichos: ").strip().upper()
            except (KeyboardInterrupt, EOFError):
                continue
            
            if sub == "0":
                continue
            elif sub == "A":
                selected = [n.id for n in NICHES_DB_ENRICHED]
            elif sub == "T":
                selected = [r['id'] for r in radar.rank_by_frr(top_n=5)]
            else:
                selected = []
                for part in sub.split(','):
                    try:
                        idx = int(part.strip()) - 1
                        if 0 <= idx < len(NICHES_DB_ENRICHED):
                            selected.append(NICHES_DB_ENRICHED[idx].id)
                    except ValueError:
                        pass
            
            show_header()
            print(f"  {c('📋 PLAN DE CONTENIDO', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            plan = radar.create_content_plan(selected)
            print(f"\n  Nichos en plan: {len(plan['nodes'])}")
            print(f"  Visitantes/mes: {plan['total_monthly_visitors']:,}")
            print(f"  Clicks/mes:     {plan['total_clicks']:,}")
            print(f"  Confianza prom: {plan['confidence_promedio']}")
            print()
            print(f"  {'':>12} {'LOW':>12} {'AVG':>12} {'HIGH':>12}")
            print(f"  {'Mensual':>12} {c(f'${plan["total_monthly_revenue"]["low"]:>8,.2f}', Colors.YELLOW)} {c(f'${plan["total_monthly_revenue"]["avg"]:>8,.2f}', Colors.CYAN, bold=True)} {c(f'${plan["total_monthly_revenue"]["high"]:>8,.2f}', Colors.GREEN)}")
            print(f"  {'Anual':>12} {c(f'${plan["total_yearly_revenue"]["low"]:>8,.2f}', Colors.YELLOW)} {c(f'${plan["total_yearly_revenue"]["avg"]:>8,.2f}', Colors.CYAN, bold=True)} {c(f'${plan["total_yearly_revenue"]["high"]:>8,.2f}', Colors.GREEN)}")
            press_enter()
        
        elif choice == "5":
            show_header()
            print(f"  {c('📊 STATS SEO ORACLE', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            stats = radar.get_seo_stats()
            print(f"\n  {c('Resumen:', Colors.YELLOW, bold=True)}")
            print(f"  Total nichos:     {stats['total_nichos']}")
            print(f"  Nichos aptos:     {stats['nichos_aptos']}")
            print(f"  No aptos:         {stats['nichos_no_aptos']}")
            print(f"  FRR prom. aptos:  {stats['frr_promedio_aptos']:.2f}")
            print(f"  Umbral FRR:       {stats['umbral_frr']:.0f}")
            print(f"  Nodos trackeados: {stats['total_nodos_trackeados']}")
            print(f"  Revenue real:     ${stats['revenue_real_acumulado']:,.2f}")
            print()
            print(f"  {c('Por categoría:', Colors.YELLOW, bold=True)}")
            for cat, data in stats['categorias'].items():
                print(f"  {cat:<20} {data['count']} nichos | CPC prom: ${data['cpc_promedio']:.0f} | FRR prom: {data['frr_promedio']:.0f}")
            print()
            print(f"  {c('Top 5 FRR:', Colors.YELLOW, bold=True)}")
            for i, r in enumerate(stats['top_por_frr'], 1):
                print(f"  {i}. {r['name'][:40]:<42} FRR: {r['frr']:>8.0f} | CPC: ${r['cpc_avg']:.0f}")
            press_enter()
        
        elif choice == "6":
            show_header()
            print(f"  {c('💾 EXPORTAR REPORTE SEO ORACLE', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            filepath = "output/reports/seo_oracle_report.json"
            result = radar.export_report(filepath)
            if result.get("success"):
                print(f"\n  {c('✅ Reporte exportado:', Colors.GREEN, bold=True)} {c(result['filepath'], Colors.CYAN)}")
            else:
                print(f"\n  {c('❌ Error exportando reporte', Colors.RED)}")
            press_enter()
        
        elif choice == "7":
            show_header()
            print(f"  {c('🌿 MULTIPLICADOR EVERGREEN', Colors.YELLOW, bold=True)}")
            print(c("  " + "=" * 50, Colors.DIM))
            print(f"\n  Factor de decrecimiento anual (10% obsolescencia):")
            print(f"  {'Año':>6} {'Multiplicador':>15}")
            print(c("  " + "-" * 25, Colors.DIM))
            for y in [1, 2, 3, 4, 5, 10]:
                mult = radar.get_evergreen_multiplier(y)
                print(f"  {y:>5}  {mult:>14.2f}x")
            press_enter()
        
        elif choice == "0":
            break


def show_about():
    show_header()
    print(c("  ACERCA DE SHADOW DEL VALLE R", Colors.YELLOW, bold=True))
    print(c("  " + "=" * 50, Colors.DIM))

    print("""
  """ + c("Shadow Del Valle R", Colors.CYAN, bold=True) + """ v1.0.0

  """ + c("Arquitecto:", Colors.YELLOW) + """ Romny (El Joker)
  """ + c("IA Asistente:", Colors.YELLOW) + """ Buffy (Codebuff AI)
  """ + c("Nacimiento:", Colors.YELLOW) + """ 23 de Junio 2026, 3:05 AM

  """ + c("Mision:", Colors.YELLOW, bold=True) + """
  Ser el agente autonomo de arbitraje de trafico mas letal
  del mercado. Cazar intencion anticipada, forjar contenido
  que convierta, y generar ingresos 24/7 sin intervencion humana.

  """ + c("Frase Clave:", Colors.DIM) + """
  "Cuando todos dormian, yo construia el futuro."

  """ + c("Motores:", Colors.YELLOW) + """
  Radar      -> FRR, intencion anticipada, deteccion de nichos
  Refinery   -> HTML ultra-ligero, CSS nativo, Monetag
  Silo       -> Enlazado matematico, distribucion de autoridad
  Bridge     -> Copywriting emotivo, prompts estructurados
  Deployer   -> Vercel/GitHub, publicacion automatica
  Ledger     -> Contabilidad de por vida, dashboard en tiempo real
""")
    press_enter()


def main_menu():
    while True:
        show_header()

        resumen = ledger.get_resumen()
        total_hist = resumen['ingresos']['total_historico']
        total_posts = resumen['proyecciones']['total_posts']
        proy_mes = resumen['proyecciones']['ingreso_proyectado_mensual']

        balance = c("Balance:", Colors.YELLOW)
        historico = c("${:,.2f}".format(total_hist), Colors.GREEN, bold=True)
        posts_str = c(str(total_posts), Colors.CYAN)
        proy_str = c("${:,.2f}".format(proy_mes), Colors.GREEN)
        print("  " + balance + " Historico: " + historico + " | Posts: " + posts_str + " | Proy. mes: " + proy_str)
        print()

        print(c("  SELECCIONA UN MODULO:", Colors.YELLOW, bold=True))
        print()
        menu_option(1, "Radar Predictivo", "Escanea nichos, calcula FRR, proyecta ingresos")
        menu_option(2, "Contabilidad por Vida", "Dashboard financiero en tiempo real, ledger")
        menu_option(3, "Generar Post", "Forja contenido SEO para un nicho especifico")
        menu_option(4, "Deploy", "Prepara y publica posts a produccion")
        menu_option(5, "Configuracion", "Ajustes del sistema, kill switch, Monetag")
        menu_option(6, "Agente Autonomo", "Modo AaaS 24/7 - loop infinito de generacion")
        menu_option(7, "Oraculo Sismico", "Monitoreo en tiempo real: USGS + WhatsApp")
        menu_option(8, "💰 Monetag Revenue", "Dashboard + optimización de ingresos")
        menu_option(9, "Acerca de", "Informacion del sistema")
        menu_option(10, "📊 SEO Oracle", "Ranking, proyección, plan de contenido")
        print()
        menu_option(0, "Salir", "Cerrar el Centro de Mando")
        print()

        try:
            choice = input("  " + c(">", Colors.GREEN) + " Opcion: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n" + c("Hasta luego, Joker. El sistema sigue corriendo.", Colors.CYAN))
            sys.exit(0)

        if choice == "1":
            show_radar()
        elif choice == "2":
            show_ledger()
        elif choice == "3":
            show_generator()
        elif choice == "4":
            show_deploy()
        elif choice == "5":
            show_config()
        elif choice == "6":
            show_agent()
        elif choice == "7":
            show_oraculo()
        elif choice == "8":
            show_monetag()
        elif choice == "9":
            show_about()
        elif choice == "10":
            show_seo_oracle()
        elif choice == "0":
            print("\n" + c("Hasta luego, Joker. El sistema sigue corriendo.", Colors.CYAN, bold=True))
            print(c('  "La madera refinada nunca deja de crecer."', Colors.DIM))
            print()
            break
        else:
            print("\n  " + c("Opcion invalida. Intenta de nuevo.", Colors.RED))
            press_enter()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n" + c("Hasta luego, Joker. El sistema sigue corriendo.", Colors.CYAN))
        sys.exit(0)

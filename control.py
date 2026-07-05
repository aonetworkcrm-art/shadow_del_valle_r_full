#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   SHADOW DEL VALLE R — CENTRO DE CONTROL UNIFICADO         ║
║   Generar · Desplegar · Indexar · Monitorear               ║
╚══════════════════════════════════════════════════════════════╝

Uso:
    python control.py                    # Menú interactivo
    python control.py --all              # Pipeline completo
    python control.py --generate         # Solo generar posts
    python control.py --deploy           # Solo desplegar a Vercel
    python control.py --notify           # Solo notificar IndexNow
    python control.py --status           # Ver estado completo
    python control.py --post             # Generar + deploy + notify
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime


# ─── Colores ───
class C:
    N = '\033[0m'   # reset/none
    B = '\033[1m'   # bold
    D = '\033[2m'   # dim
    G = '\033[92m'  # green
    C = '\033[96m'  # cyan
    Y = '\033[93m'  # yellow
    R = '\033[91m'  # red
    M = '\033[95m'  # magenta


def c(text, color, bold=False):
    prefix = C.B if bold else ''
    return prefix + color + str(text) + C.N


def header():
    print(f'\n{c("=" * 56, C.C, bold=True)}')
    print(c('  🌑 SHADOW DEL VALLE R — CONTROL CENTER', C.C, bold=True))
    print(c(f'  {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', C.D))
    print(c('=' * 56, C.C, bold=True))
    print()


def step(msg):
    print(f'  {c("→", C.Y)} {msg}')


def ok(msg):
    print(f'  {c("✅", C.G)} {msg}')


def warn(msg):
    print(f'  {c("⚠️", C.Y)} {msg}')


def fail(msg):
    print(f'  {c("❌", C.R)} {msg}')


def run_cmd(cmd, timeout=120):
    """Ejecuta un comando y retorna (success, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=os.path.dirname(os.path.abspath(__file__))
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, 'Timeout'
    except Exception as e:
        return False, str(e)


# ═══════════════════════════════════════════════
# 🎯 ACCIONES
# ═══════════════════════════════════════════════

def action_generate():
    """Genera todos los posts + sitemap + notifica IndexNow."""
    header()
    step('Generando posts...')
    success, output = run_cmd('python generate_all.py', timeout=120)
    
    if success:
        ok('Posts generados exitosamente')
        # Extraer info clave del output
        for line in output.split('\n'):
            if 'CPC Promedio' in line or 'Top CPC' in line or 'posts generados' in line:
                print(f'     {line.strip()}')
        return True
    else:
        fail(f'Error generando posts:\n{output[:500]}')
        return False


def action_deploy():
    """Despliega a Vercel."""
    header()
    step('Desplegando a Vercel...')
    success, output = run_cmd('vercel --prod --yes', timeout=120)
    
    if success:
        # Extraer URL de producción
        for line in output.split('\n'):
            if 'aliased' in line.lower() or 'https://' in line:
                url = line.split('https://')[-1].strip()
                if url:
                    ok(f'Desplegado en https://{url}')
                    break
        else:
            ok('Deploy completado')
        return True
    else:
        # Verificar si fue error de Vercel o ya estaba actualizado
        if 'already exists' in output.lower() or 'no changes' in output.lower():
            warn('Ya estaba actualizado. No se requirió deploy.')
            return True
        fail(f'Error en deploy:\n{output[:500]}')
        return False


def action_notify():
    """Notifica IndexNow desde el endpoint del sitio."""
    header()
    step('Notificando IndexNow (Bing/Yandex)...')
    success, output = run_cmd(
        'curl -s "https://shadow-del-valle-r.vercel.app/api/notify?action=all"',
        timeout=30
    )
    
    if success:
        try:
            data = json.loads(output)
            if data.get('success') or data.get('urlsSubmitted', 0) > 0:
                ok(f'{data.get("urlsSubmitted", 0)} URLs enviadas a IndexNow')
                return True
        except json.JSONDecodeError:
            pass
        ok('Notificación enviada')
        return True
    else:
        fail(f'Error notificando:\n{output[:300]}')
        return False


def action_status():
    """Muestra el estado completo del sistema."""
    header()
    
    # 1. Posts
    posts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'posts.json')
    if os.path.exists(posts_file):
        with open(posts_file, 'r') as f:
            posts = json.load(f)
        total = len(posts)
        cpc_total = sum(p.get('cpc', 0) for p in posts)
        cpc_avg = cpc_total / total if total > 0 else 0
        top_cpc = max((p.get('cpc', 0) for p in posts), default=0)
        print(f'  📄 {c("Posts:", C.Y, bold=True)} {total} generados | CPC prom: ${cpc_avg:.0f} | Top CPC: ${top_cpc:.0f}')
    else:
        print(f'  📄 {c("Posts:", C.Y, bold=True)} No hay posts generados')
    
    # 2. Sitio en vivo
    success, output = run_cmd('curl -s -o /dev/null -w "%{http_code}" https://shadow-del-valle-r.vercel.app/', timeout=15)
    site_status = f'HTTP {output}' if success else 'No accesible'
    site_color = C.G if output == '200' else C.R
    print(f'  🌐 {c("Sitio:", C.Y, bold=True)} {c(site_status, site_color)} — shadow-del-valle-r.vercel.app')
    
    # 3. APIs
    for api in ['/api/posts', '/api/track', '/api/stats', '/api/notify']:
        method = '-X POST -H "Content-Type: application/json" -d \'{}\'' if api == '/api/track' else ''
        s, o = run_cmd(f'curl -s -o /dev/null -w "%{{http_code}}" {method} https://shadow-del-valle-r.vercel.app{api}', timeout=15)
        color = C.G if o == '200' else C.R
        print(f'  🔌 {c(api, C.Y)} {c(f"HTTP {o}", color)}')
    
    # 4. Sitemap
    s, o = run_cmd('curl -s -o /dev/null -w "%{http_code}" https://shadow-del-valle-r.vercel.app/sitemap.xml', timeout=15)
    print(f'  🗺️  {c("Sitemap:", C.Y, bold=True)} {"✅ Accesible" if o == "200" else "❌ No accesible"}')
    
    # 5. Monetag sw.js
    s, o = run_cmd('curl -s -o /dev/null -w "%{http_code}" https://shadow-del-valle-r.vercel.app/sw.js', timeout=15)
    print(f'  📦 {c("Monetag sw.js:", C.Y, bold=True)} {"✅ OK" if o == "200" else "❌ No encontrado"}')
    
    # 6. Google Search Console
    s, o = run_cmd('curl -s -o /dev/null -w "%{http_code}" https://shadow-del-valle-r.vercel.app/google5fb81666f26fc5f8.html', timeout=15)
    gsc_status = '✅ Verificado' if o in ['200', '308'] else '❌ No verificado'
    print(f'  🔍 {c("Google Search Console:", C.Y, bold=True)} {gsc_status}')
    
    # 7. Config
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'settings.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            cfg = json.load(f)
        monetag = cfg.get('monetag', {})
        scheduler = cfg.get('scheduler', {})
        print(f'  ⚙️  {c("Config:", C.Y, bold=True)} Monetag: {"✅" if monetag.get("habilitado") else "❌"} | '
              f'Max posts/día: {scheduler.get("max_posts_por_dia", 6)} | '
              f'Intervalo: {scheduler.get("intervalo_generacion_horas", 4)}h')
    
    print()


def action_pipeline():
    """Pipeline completo: generate + deploy + notify."""
    header()
    print(c('  🚀 PIPELINE COMPLETO', C.G, bold=True))
    print(c('  ' + '=' * 50, C.D))
    
    steps = [
        ('📝 Generando posts...', action_generate),
        ('▲ Desplegando a Vercel...', action_deploy),
        ('⚡ Notificando IndexNow...', action_notify),
    ]
    
    results = []
    for msg, func in steps:
        print(f'\n  {c(msg, C.C)}')
        result = func()
        results.append(result)
        if not result:
            warn('Pipeline detenido por error')
            break
    
    print(f'\n{c("=" * 56, C.G, bold=True)}')
    success_count = sum(1 for r in results if r)
    print(c(f'  ✅ Pipeline: {success_count}/{len(steps)} pasos completados', C.G, bold=True))
    print(c('=' * 56, C.G, bold=True))
    return all(results)



# ═══════════════════════════════════════════════
# 📊 SEO ORACLE — Menú separado del Radar
# ═══════════════════════════════════════════════

def action_seo_oracle():
    """Menú de SEO Oracle — Ranking, proyecciones, export."""
    import sys as _sys
    _project_root = os.path.dirname(os.path.abspath(__file__))
    _sys.path.insert(0, _project_root)
    
    while True:
        clear()
        header()
        
        print(c('  📊 SEO ORACLE — Inteligencia de Nichos', C.Y, bold=True))
        print(c('  ' + '=' * 50, C.D))
        print()
        
        from core.radar import Radar, NICHES_DB_ENRICHED
        radar = Radar()
        
        print(c('  OPCIONES:', C.Y, bold=True))
        print()
        print(f'  {c("[1]", C.G)} {c("🏆 Ranking por FRR", C.C)}           — Top 15 nichos por FRR')
        print(f'  {c("[2]", C.G)} {c("🏆 Ranking por Profitability", C.C)}   — Ranking completo SEO Oracle')
        print(f'  {c("[3]", C.G)} {c("📈 Proyección por nicho", C.C)}        — LOW/AVG/HIGH + confidence')
        print(f'  {c("[4]", C.G)} {c("📋 Plan de contenido", C.C)}           — Multi-nicho con totales')
        print(f'  {c("[5]", C.G)} {c("📊 Stats SEO Oracle", C.C)}            — Estadísticas unificadas')
        print(f'  {c("[6]", C.G)} {c("💾 Exportar reporte JSON", C.C)}        — Guarda reporte completo')
        print(f'  {c("[7]", C.G)} {c("🌿 Multiplicador Evergreen", C.C)}      — Factor de decrecimiento anual')
        print()
        print(f'  {c("[0]", C.R)} {c("Volver", C.C)}')
        print()
        
        try:
            choice = input(f'  {c(">", C.G)} Opción: ').strip()
        except (KeyboardInterrupt, EOFError):
            break
        
        if choice == '1':
            # Ranking por FRR
            clear()
            header()
            print(f'  {c("🏆 RANKING POR FRR (Top 15)", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            print(f'  {"Nicho":<40} {"CPC":>6} {"FRR":>10} {"Profit":>10} {"Diff":>8} {"Apto":>6}')
            print(c('  ' + '-' * 80, C.D))
            ranking = radar.rank_by_frr(top_n=15)
            for i, r in enumerate(ranking, 1):
                apto_str = c('✅', C.G) if r['apto'] else c('❌', C.R)
                print(f'  {i:<2} {r["name"][:38]:<40} ${r["cpc_avg"]:>4.0f} {r["frr"]:>10.0f} {r["profitability_score"]:>10.0f} {r["difficulty"][:7]:>8} {apto_str}')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '2':
            # Ranking por Profitability
            clear()
            header()
            print(f'  {c("🏆 RANKING POR PROFITABILITY", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            print(f'  {"Nicho":<40} {"CPC":>6} {"Score":>10} {"FRR":>10} {"Evergreen":>5} {"Diff":>8}')
            print(c('  ' + '-' * 80, C.D))
            ranking = radar.rank_by_profitability()
            for i, r in enumerate(ranking, 1):
                print(f'  {i:<2} {r["name"][:38]:<40} ${r["cpc_avg"]:>4.0f} {r["profitability_score"]:>10.0f} {r["frr"]:>10.0f} {r["evergreen"]:>5} {r["difficulty"][:7]:>8}')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '3':
            # Yield projection
            clear()
            header()
            print(f'  {c("📈 PROYECCIÓN DE INGRESOS", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            print(f'\n  Selecciona un nicho para proyectar:')
            for i, n in enumerate(NICHES_DB_ENRICHED, 1):
                print(f'  {c(f"[{i}]", C.G)} {n.name[:45]:<45} ${float(n.cpc_avg):>4.0f}')
            print(f'\n  {c("[A]", C.G)} Proyectar TODOS los nichos')
            print(f'  {c("[0]", C.R)} Volver')
            print()
            try:
                sub = input(f'  {c(">", C.G)} Nicho: ').strip().upper()
            except (KeyboardInterrupt, EOFError):
                continue
            
            if sub == '0':
                continue
            elif sub == 'A':
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
            
            clear()
            header()
            print(f'  {c("📈 PROYECCIÓN de Ingresos", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            for nid in niche_ids:
                proj = radar.calculate_yield_projection(
                    niche_id=nid, monthly_visitors=2000, ctr_pct=2.0, nodes_count=3
                )
                if proj:
                    p = proj.to_dict()
                    conf_color = {'muy_alta': C.G, 'alta': C.G, 'media': C.Y, 'baja': C.R}.get(p['confidence'], C.D)
                    print(f'\n  {c(p["niche"][:45], C.C, bold=True)}')
                    print(f'  Visitantes/mes: {p["monthly_visitors_total"]:>6,} | Clicks: {p["clicks_monthly"]:,}')
                    print(f'  CPC rango: ${p["cpc_range"]["min"]:.0f} - ${p["cpc_range"]["max"]:.0f}')
                    print(f'  Mensual:  {c(f"${p["monthly_revenue"]["low"]:>8,.2f}", C.Y)}  {c(f"${p["monthly_revenue"]["avg"]:>8,.2f}", C.C, bold=True)}  {c(f"${p["monthly_revenue"]["high"]:>8,.2f}", C.G)}')
                    print(f'  Anual:    {c(f"${p["yearly_revenue"]["low"]:>8,.2f}", C.Y)}  {c(f"${p["yearly_revenue"]["avg"]:>8,.2f}", C.C, bold=True)}  {c(f"${p["yearly_revenue"]["high"]:>8,.2f}", C.G)}')
                    print(f'  Confianza: {c(p["confidence"], conf_color, bold=True)}')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '4':
            # Content plan
            clear()
            header()
            print(f'  {c("📋 PLAN DE CONTENIDO MULTI-NICHO", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            print(f'\n  Selecciona nichos para el plan (separados por coma):')
            for i, n in enumerate(NICHES_DB_ENRICHED, 1):
                print(f'  {c(f"[{i}]", C.G)} {n.name[:45]:<45} ${float(n.cpc_avg):>4.0f}')
            print(f'\n  {c("[A]", C.G)} Todos los nichos')
            print(f'  {c("[T]", C.G)} Top 5 por FRR')
            print(f'  {c("[0]", C.R)} Volver')
            print()
            try:
                sub = input(f'  {c(">", C.G)} Nichos: ').strip().upper()
            except (KeyboardInterrupt, EOFError):
                continue
            
            if sub == '0':
                continue
            elif sub == 'A':
                selected = [n.id for n in NICHES_DB_ENRICHED]
            elif sub == 'T':
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
            
            clear()
            header()
            print(f'  {c("📋 PLAN DE CONTENIDO", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            plan = radar.create_content_plan(selected)
            print(f'\n  Nichos en plan: {len(plan["nodes"])}')
            print(f'  Visitantes/mes: {plan["total_monthly_visitors"]:,}')
            print(f'  Clicks/mes:     {plan["total_clicks"]:,}')
            print(f'  Confianza prom: {plan["confidence_promedio"]}')
            print()
            print(f'  {'':>12} {"LOW":>12} {"AVG":>12} {"HIGH":>12}')
            print(f'  {'Mensual':>12} {c(f"${plan['total_monthly_revenue']['low']:>8,.2f}", C.Y)} {c(f"${plan['total_monthly_revenue']['avg']:>8,.2f}", C.C, bold=True)} {c(f"${plan['total_monthly_revenue']['high']:>8,.2f}", C.G)}')
            print(f'  {'Anual':>12} {c(f"${plan['total_yearly_revenue']['low']:>8,.2f}", C.Y)} {c(f"${plan['total_yearly_revenue']['avg']:>8,.2f}", C.C, bold=True)} {c(f"${plan['total_yearly_revenue']['high']:>8,.2f}", C.G)}')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '5':
            # SEO stats
            clear()
            header()
            print(f'  {c("📊 STATS SEO ORACLE", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            stats = radar.get_seo_stats()
            print(f'\n  {c("Resumen:", C.Y, bold=True)}')
            print(f'  Total nichos:     {stats["total_nichos"]}')
            print(f'  Nichos aptos:     {stats["nichos_aptos"]}')
            print(f'  No aptos:         {stats["nichos_no_aptos"]}')
            print(f'  FRR prom. aptos:  {stats["frr_promedio_aptos"]:.2f}')
            print(f'  Umbral FRR:       {stats["umbral_frr"]:.0f}')
            print(f'  Nodos trackeados: {stats["total_nodos_trackeados"]}')
            print(f'  Revenue real:     ${stats["revenue_real_acumulado"]:,.2f}')
            print()
            print(f'  {c("Por categoría:", C.Y, bold=True)}')
            for cat, data in stats['categorias'].items():
                print(f'  {cat:<20} {data["count"]} nichos | CPC prom: ${data["cpc_promedio"]:.0f} | FRR prom: {data["frr_promedio"]:.0f}')
            print()
            print(f'  {c("Top 5 FRR:", C.Y, bold=True)}')
            for i, r in enumerate(stats['top_por_frr'], 1):
                print(f'  {i}. {r["name"][:40]:<42} FRR: {r["frr"]:>8.0f} | CPC: ${r["cpc_avg"]:.0f}')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '6':
            # Export report
            clear()
            header()
            print(f'  {c("💾 EXPORTAR REPORTE SEO ORACLE", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            filepath = os.path.join(_project_root, "output", "reports", "seo_oracle_report.json")
            result = radar.export_report(filepath)
            if result.get("success"):
                ok(f'Reporte exportado: {c(result["filepath"], C.C)}')
            else:
                fail('Error exportando reporte')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '7':
            # Evergreen multiplier
            clear()
            header()
            print(f'  {c("🌿 MULTIPLICADOR EVERGREEN", C.Y, bold=True)}')
            print(c('  ' + '=' * 50, C.D))
            print(f'\n  Factor de decrecimiento anual (10% obsolescencia):')
            print(f'  {"Año":>6} {"Multiplicador":>15}')
            print(c('  ' + '-' * 25, C.D))
            for y in [1, 2, 3, 4, 5, 10]:
                mult = radar.get_evergreen_multiplier(y)
                print(f'  {y:>5}  {mult:>14.2f}x')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '0':
            break


# ═══════════════════════════════════════════════
# 💰 MONETAG REVENUE
# ═══════════════════════════════════════════════

def action_monetag():
    """Menú de Monetag Revenue — Dashboard + Optimización."""
    import sys
    import os
    from datetime import datetime
    
    _project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _project_root)
    
    # Detectar token
    token = os.environ.get("MONETAG_API_TOKEN", "")
    cfg_path = os.path.join(_project_root, "config", "settings.json")
    try:
        if not token and os.path.exists(cfg_path):
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
            token = cfg.get("monetag_api", {}).get("api_token", "")
    except:
        pass
    
    def _token_status():
        nonlocal token
        if token:
            return c('✅ Configurado', C.G)
        return c('❌ No configurado', C.R)
    
    while True:
        clear()
        header()
        
        print(c('  💰 MONETAG REVENUE — Centro de Optimización', C.M, bold=True))
        print()
        print(f'  Token API: {_token_status()}')
        if token:
            print(f'  Token:     {c(token[:16] + "..." + token[-4:], C.D)}')
        print()
        
        print(c('  OPCIONES:', C.Y, bold=True))
        print()
        print(f'  {c("[1]", C.G)} {c("🚀 Dashboard Web", C.C)}          — Arrancar el panel de revenue en vivo')
        print(f'  {c("[2]", C.G)} {c("🔄 Sincronizar Revenue", C.C)}     — Forzar sync con API de Monetag')
        print(f'  {c("[3]", C.G)} {c("⚡ Optimizar Formatos", C.C)}      — Analizar y recomendar mejoras')
        print(f'  {c("[4]", C.G)} {c("🔔 Ver Alertas", C.C)}            — Alertas inteligentes')
        print(f'  {c("[5]", C.G)} {c("📊 Estado Monetag", C.C)}         — Verificar conexión y stats')
        print(f'  {c("[6]", C.G)} {c("🛠️  Configurar Token", C.C)}      — Cambiar API key')
        print(f'  {c("[7]", C.G)} {c("📊 Reporte Diario + WhatsApp", C.C)} — Revenue, RPM, alertas vía WhatsApp')
        print()
        print(f'  {c("[0]", C.R)} {c("Volver", C.C)}')
        print()
        
        try:
            choice = input(f'  {c(">", C.G)} Opción: ').strip()
        except (KeyboardInterrupt, EOFError):
            break
        
        if choice == '1':
            # Dashboard Web
            clear()
            header()
            print(f'  {c("🚀 Iniciando Dashboard Web...", C.Y)}')
            print(f'  {c("Presiona Ctrl+C para detener", C.D)}')
            print()
            try:
                from dashboard.api import create_app
                app = create_app()
                import threading
                import webbrowser
                threading.Thread(target=lambda: (__import__("time").sleep(2), webbrowser.open("http://localhost:5000")), daemon=True).start()
                print(f'  {c("Dashboard → http://localhost:5000", C.C, bold=True)}')
                print()
                app.run(host="0.0.0.0", port=5000, debug=False)
            except ImportError as e:
                print(f'\n  {c("❌ Error: " + str(e), C.R)}')
                print(f'  Para arrancar manualmente: python dashboard/api.py')
                input(f'\n  {c("[Enter]", C.D)} para continuar...')
            except KeyboardInterrupt:
                print(f'\n  {c("Servidor detenido.", C.Y)}')
        
        elif choice == '2':
            # Sincronizar Revenue
            if not token:
                warn('No hay token configurado')
                input(f'\n  {c("[Enter]", C.D)} para continuar...')
                continue
            clear()
            header()
            step('Sincronizando revenue con Monetag...')
            try:
                from monetag.revenue_tracker import RevenueTracker
                from monetag.api_client import MonetagAPI
                from core.ledger import Ledger
                api = MonetagAPI(api_token=token)
                ledger = Ledger(data_dir=os.path.join(_project_root, "output", "ledger"))
                tracker = RevenueTracker(api=api, ledger=ledger)
                result = tracker.sync_now(force=True)
                if result.get("success"):
                    rev = result.get("current_revenue", {})
                    ok(f"Revenue: ${rev.get('total_revenue', 0):.2f}")
                    ok(f"Impresiones: {rev.get('total_impressions', 0):,}")
                    ok(f"RPM: ${rev.get('avg_rpm', 0):.2f}")
                else:
                    if result.get("error"):
                        fail(str(result['error'])[:80])
                    else:
                        warn('Sincronización parcial')
            except Exception as e:
                fail(str(e)[:100])
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '3':
            # Optimizar Formatos
            if not token:
                warn('No hay token configurado')
                input(f'\n  {c("[Enter]", C.D)} para continuar...')
                continue
            clear()
            header()
            print(f'  {c("⚡ EJECUTANDO OPTIMIZACIÓN...", C.Y, bold=True)}')
            print(f'  {c("Analizando formatos y generando recomendaciones...", C.D)}')
            try:
                from monetag.optimizer import MonetagOptimizer
                from monetag.revenue_tracker import RevenueTracker
                from monetag.api_client import MonetagAPI
                from core.ledger import Ledger
                api = MonetagAPI(api_token=token)
                ledger = Ledger(data_dir=os.path.join(_project_root, "output", "ledger"))
                tracker = RevenueTracker(api=api, ledger=ledger)
                optimizer = MonetagOptimizer(api=api, tracker=tracker,
                                             config_path=cfg_path)
                result = optimizer.run_optimization_cycle(force=True)
                
                if result.get("format_analysis"):
                    formats = result["format_analysis"].get("formats", [])
                    if formats:
                        print(f'\n  {c("📊 ANÁLISIS DE FORMATOS", C.Y, bold=True)}')
                        for f in formats:
                            val = f.get('current_rpm', 0)
                            gap = f.get('gap_to_avg', -10)
                            color = C.G if gap > 0 else (C.Y if gap > -1 else C.R)
                            print(f'  {f.get("format", "?") + " ":.<20} {c(f"${val:.2f}", color)}  {f.get("status", "")}')
                
                if result.get("recommendations"):
                    print(f'\n  {c("💡 RECOMENDACIONES", C.Y, bold=True)}')
                    for r in result["recommendations"]:
                        print(f'  • {r}')
                
                print(f'\n  {c("✅ Optimización completada", C.G, bold=True)}')
            except Exception as e:
                fail(str(e)[:100])
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '4':
            # Ver Alertas
            if not token:
                warn('No hay token configurado')
                input(f'\n  {c("[Enter]", C.D)} para continuar...')
                continue
            clear()
            header()
            print(f'  {c("🔔 ALERTAS DEL SISTEMA", C.Y, bold=True)}')
            try:
                from monetag.alert_engine import AlertEngine
                from monetag.revenue_tracker import RevenueTracker
                from monetag.api_client import MonetagAPI
                from core.ledger import Ledger
                api = MonetagAPI(api_token=token)
                ledger = Ledger(data_dir=os.path.join(_project_root, "output", "ledger"))
                tracker = RevenueTracker(api=api, ledger=ledger)
                alerts = AlertEngine(api=api, tracker=tracker)
                alerts.run_checks(force_sync=True)
                alert_list = alerts.get_recent_alerts(15)
                stats = alerts.get_stats()
                
                print(f'\n  Total alertas: {stats.get("total_triggered", 0)}  |  Sin leer: {stats.get("unacknowledged", 0)}')
                print()
                
                if alert_list:
                    for a in alert_list:
                        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(a.get("severity"), "⚪")
                        severity_color = C.R if a.get("severity") == "critical" else (C.Y if a.get("severity") == "warning" else C.C)
                        print(f'  {icon} {c(a.get("title", "Alerta"), severity_color, bold=True)}')
                        if a.get("message"):
                            print(f'     {c(a["message"], C.D)}')
                        if a.get("recommendation"):
                            print(f'     💡 {c(a["recommendation"], C.G)}')
                        print()
                else:
                    print(f'  {c("🎉 Sin alertas. Todo en orden.", C.G)}')
            except Exception as e:
                fail(str(e)[:100])
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '5':
            # Estado Monetag
            clear()
            header()
            print(f'  {c("📊 ESTADO DE MONETAG", C.Y, bold=True)}')
            print()
            
            if not token:
                print(f'  {c("❌ No hay token de Monetag configurado.", C.R)}')
                print(f'  Configúralo en opción [6] o en settings.json')
            else:
                try:
                    from monetag.api_client import MonetagAPI
                    api = MonetagAPI(api_token=token)
                    status = api.test_connection()
                    if status.get("success"):
                        print(f'  {c("✅ Conexión OK", C.G)}')
                        stats = api.get_api_stats()
                        print(f'  API Requests:  {stats.get("total_requests", 0)}')
                        print(f'  Última sync:   {stats.get("ultima_request", "Nunca")}')
                        # Revenue rápido
                        try:
                            rev = api.get_revenue_summary(period="last_7_days")
                            if rev.get("success"):
                                print(f'  Revenue 7d:    {c("$" + str(rev.get("total_revenue", 0)), C.C, bold=True)}')
                                print(f'  Impresiones:   {rev.get("total_impressions", 0):,}')
                                print(f'  RPM Promedio:  ${rev.get("avg_rpm", 0):.2f}')
                        except Exception:
                            pass
                    else:
                        print(f'  {c("❌ Error de conexión: " + status.get("error", "desconocido"), C.R)}')
                except Exception as e:
                    print(f'  {c("❌ " + str(e)[:80], C.R)}')
            
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '6':
            # Configurar Token
            clear()
            header()
            print(f'  {c("🛠️  CONFIGURAR API TOKEN", C.Y, bold=True)}')
            print()
            print(f'  Token actual: {c(token[:16] + "..." + token[-4:] if token else "No configurado", C.C)}')
            print()
            new_token = input(f'  {c("Nuevo token (Enter para cancelar):", C.G)} ').strip()
            
            if new_token:
                try:
                    with open(cfg_path, "r") as f:
                        cfg = json.load(f)
                    if "monetag_api" not in cfg:
                        cfg["monetag_api"] = {}
                    cfg["monetag_api"]["api_token"] = new_token
                    with open(cfg_path, "w") as f:
                        json.dump(cfg, f, ensure_ascii=False, indent=2)
                    os.environ["MONETAG_API_TOKEN"] = new_token
                    token = new_token
                    print(f'\n  {c("✅ Token actualizado", C.G, bold=True)}')
                except Exception as e:
                    print(f'\n  {c("❌ Error: " + str(e), C.R)}')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        
        elif choice == '7':
            action_monetag_report(token, cfg_path, _project_root)
        
        elif choice == '0':
            break


# ═══════════════════════════════════════════════
# 📊 REPORTE DIARIO MONETAG + WHATSAPP
# ═══════════════════════════════════════════════

def action_monetag_report(token: str, cfg_path: str, project_root: str):
    """
    Genera un reporte diario completo de Monetag (revenue, RPM, alertas)
    y lo envía por WhatsApp.
    """
    import sys as _sys
    _sys.path.insert(0, project_root)
    
    from datetime import datetime
    
    clear()
    header()
    print(f'  {c("📊 REPORTE DIARIO MONETAG", C.Y, bold=True)}')
    print(c("  " + "=" * 50, C.D))
    
    if not token:
        fail('No hay token de Monetag configurado')
        input(f'\n  {c("[Enter]", C.D)} para continuar...')
        return
    
    # ── 1. Sincronizar datos ─────────────────────────────────────
    step('Sincronizando con API de Monetag...')
    try:
        from monetag.api_client import MonetagAPI
        from monetag.revenue_tracker import RevenueTracker
        from monetag.alert_engine import AlertEngine
        from core.ledger import Ledger
        
        api = MonetagAPI(api_token=token)
        ledger = Ledger(data_dir=os.path.join(project_root, "output", "ledger"))
        tracker = RevenueTracker(api=api, ledger=ledger)
        tracker.sync_now(force=True)
        ok('Datos sincronizados')
    except Exception as e:
        fail(f'Error sincronizando: {str(e)[:80]}')
        input(f'\n  {c("[Enter]", C.D)} para continuar...')
        return
    
    # ── 2. Obtener métricas ──────────────────────────────────────
    step('Obteniendo métricas...')
    
    revenue = tracker.get_current_revenue()
    daily = tracker.get_daily_breakdown(days=7)
    zones = tracker.get_zone_analysis()
    geo = tracker.get_geo_analysis()
    historical = tracker.get_historical_summary()
    
    # Alertas
    alerts_engine = AlertEngine(api=api, tracker=tracker)
    alerts_engine.run_checks(force_sync=False)
    alert_list = alerts_engine.get_recent_alerts(10)
    alert_stats = alerts_engine.get_stats()
    
    ok('Métricas obtenidas')
    
    # ── 3. Construir reporte ─────────────────────────────────────
    step('Generando reporte...')
    
    # Fecha del reporte
    today = datetime.now().strftime("%d/%m/%Y")
    
    # Métricas principales
    rev_data = revenue if isinstance(revenue, dict) else {}
    total_rev = rev_data.get('total_revenue', 0) or 0
    avg_daily = rev_data.get('avg_daily_revenue', 0) or 0
    avg_rpm = rev_data.get('avg_rpm', 0) or 0
    impressions = rev_data.get('total_impressions', 0) or 0
    clicks = rev_data.get('total_clicks', 0) or 0
    ctr = rev_data.get('ctr_percent', 0) or 0
    projected_monthly = rev_data.get('projected_monthly', 0) or 0
    projected_yearly = rev_data.get('projected_yearly', 0) or 0
    
    # Análisis diario
    daily_analysis = daily.get('analysis', {}) if isinstance(daily, dict) else {}
    trend_pct = daily_analysis.get('trend_last_week_pct', 0) or 0
    trend_dir = daily_analysis.get('trend_direction', 'stable')
    
    # Mejor día
    best_day = rev_data.get('best_day', {}) if isinstance(rev_data, dict) else {}
    best_day_str = f"{best_day.get('date', 'N/A')}: ${best_day.get('revenue', 0):.2f}" if best_day.get('date') else "N/A"
    
    # Zonas
    zone_list = zones.get('zones', []) if isinstance(zones, dict) else []
    top_zones = sorted(zone_list, key=lambda z: z.get('revenue', 0), reverse=True)[:3]
    top_zones_str = ', '.join(f"{z.get('zone_name', 'Zona')[:20]}(${z.get('revenue', 0):.2f})" for z in top_zones) if top_zones else "Sin datos"
    
    # Países
    countries = geo.get('countries', []) if isinstance(geo, dict) else []
    top_countries = sorted(countries, key=lambda c: c.get('revenue', 0), reverse=True)[:3]
    top_countries_str = ', '.join(f"{c.get('country', '?')}(${c.get('rpm', 0):.2f})" for c in top_countries) if top_countries else "Sin datos"
    
    # Tendencia
    trend_emoji = "📈" if trend_dir == "up" else ("📉" if trend_dir == "down" else "➡️")
    
    # Alertas activas
    unacked = alert_stats.get('unacknowledged', 0)
    
    # Alertas urgentes
    urgent_alerts = []
    for a in alert_list[:5]:
        if not a.get('acknowledged'):
            urgent_alerts.append(f"{a.get('severity', '').upper()}: {a.get('title', '')[:50]}")
    
    # ── 4. Formatear reporte ─────────────────────────────────────
    
    # Línea de separación
    sep = "─" * 30
    
    report_lines = [
        f"📊 *REPORTE DIARIO MONETAG*",
        f"📅 {today} | {trend_emoji} Tendencia: {trend_dir.upper()}",
        f"",
        f"💵 *RESUMEN ECONÓMICO*",
        f"Revenue (7d):    ${total_rev:>8,.2f}",
        f"Avg diario:      ${avg_daily:>8,.2f}",
        f"Proy. mensual:   ${projected_monthly:>8,.2f}",
        f"Proy. anual:     ${projected_yearly:>8,.2f}",
        f"",
        f"📈 *MÉTRICAS CLAVE*",
        f"RPM Promedio:    ${avg_rpm:>8,.2f}",
        f"Impresiones:     {impressions:>8,}",
        f"Clicks:          {clicks:>8,}",
        f"CTR:             {ctr:>6.2f}%",
        f"",
        f"🏆 Mejor día:     {best_day_str}",
        f"📉 Tendencia:     {trend_pct:>+.1f}%",
        f"",
        f"🎯 *TOP ZONAS*",
        f"{top_zones_str[:80]}",
        f"",
        f"🌍 *TOP PAÍSES (RPM)*",
        f"{top_countries_str[:80]}",
    ]
    
    # Alertas
    if urgent_alerts:
        report_lines.extend([
            f"",
            f"🔔 *ALERTAS ACTIVAS*",
        ])
        for a in urgent_alerts:
            report_lines.append(f"  • {a[:70]}")
    
    if unacked > 0:
        report_lines.append(f"  ({unacked} alerta(s) sin leer)")
    
    # Histórico
    hist_totals = historical.get('totals', {}) if isinstance(historical, dict) else {}
    hist_trend = historical.get('trend', {}) if isinstance(historical, dict) else {}
    if hist_totals:
        hist_rev = hist_totals.get('revenue', 0) or 0
        hist_change = hist_trend.get('change_pct', 0) or 0
        report_lines.extend([
            f"",
            f"📚 *HISTÓRICO TOTAL*",
            f"Revenue total:   ${hist_rev:>8,.2f}",
            f"Cambio:          {hist_change:>+.1f}%",
        ])
    
    # Recomendaciones
    report_lines.extend([
        f"",
        f"💡 *RECOMENDACIONES*",
    ])
    if avg_rpm < 0.50:
        report_lines.append("• RPM bajo: cambia a formato SMARTLINK")
    if avg_rpm > 2.0:
        report_lines.append(f"• RPM excelente (${avg_rpm:.2f}). Sigue así!")
    if len(top_zones) < 2:
        report_lines.append("• Diversifica tus zonas publicitarias")
    if impressions < 1000:
        report_lines.append("• Bajo volumen de tráfico: genera más contenido")
    if trend_dir == "down":
        report_lines.append("• Tendencia negativa: revisa fuentes de tráfico")
    if not urgent_alerts:
        report_lines.append("• Todo en orden. Sin alertas pendientes.")
    report_lines.append(f"")
    report_lines.append(f"{sep}")
    report_lines.append(f"🤖 Shadow Del Valle R — Monetag Agent")
    
    report = "\n".join(report_lines)
    
    # ── 5. Mostrar en pantalla ───────────────────────────────────
    print()
    print(c("─" * 56, C.D))
    print(report)
    print(c("─" * 56, C.D))
    print()
    
    # Guardar reporte en archivo
    report_dir = os.path.join(project_root, "output", "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f"monetag_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        ok(f"Reporte guardado: {os.path.basename(report_file)}")
    except Exception as e:
        warn(f"No se pudo guardar: {e}")
    
    # ── 6. Enviar por WhatsApp ───────────────────────────────────
    print()
    step('Consultando configuración de WhatsApp...')
    
    whatsapp_cfg = {}
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            whatsapp_cfg = cfg.get("whatsapp", {})
    except:
        pass
    
    wa_phone = whatsapp_cfg.get("phone", "") or os.environ.get("WA_PHONE", "")
    wa_apikey = whatsapp_cfg.get("apikey", "") or os.environ.get("WA_APIKEY", "")
    wa_apikey = wa_apikey or os.environ.get("WA_APIKEY", "")
    
    if wa_phone and wa_apikey:
        print(f'  Teléfono: {c(wa_phone[:5] + "..." + wa_phone[-3:] if len(wa_phone) > 8 else wa_phone, C.C)}')
        print()
        
        ask = input(f'  {c("📱 Enviar reporte por WhatsApp? (s/N):", C.G)} ').strip().lower()
        
        if ask == 's' or ask == 'si' or ask == 'y' or ask == 'yes':
            step('Enviando reporte por WhatsApp...')
            try:
                from urllib.request import Request, urlopen
                from urllib.parse import urlencode
                
                api_url = whatsapp_cfg.get("api_url", "https://api.callmebot.com/whatsapp.php")
                params = urlencode({"phone": wa_phone, "text": report, "apikey": wa_apikey})
                req = Request(f"{api_url}?{params}",
                              headers={"User-Agent": "ShadowDelValleR-Monetag/1.0"})
                
                with urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        ok('✅ Reporte enviado por WhatsApp exitosamente!')
                    else:
                        warn(f'⚠️ WhatsApp respondió con código {resp.status}')
            except Exception as e:
                fail(f'❌ Error enviando WhatsApp: {str(e)[:80]}')
        else:
            warn('Reporte no enviado')
    else:
        warn('WhatsApp no configurado')
        print(f'  Para configurar, edita {c("config/settings.json", C.C)} sección "whatsapp"')
        print(f'  O usa variables de entorno: WA_PHONE, WA_APIKEY')
    
    print()
    ok('Reporte completado')
    input(f'\n  {c("[Enter]", C.D)} para continuar...')


# ═══════════════════════════════════════════════
# 📋 MENÚ INTERACTIVO
# ═══════════════════════════════════════════════

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def menu():
    while True:
        clear()
        header()
        
        print(c('  SELECCIONA UNA ACCIÓN:', C.Y, bold=True))
        print()
        print(f'  {c("[1]", C.G)} {c("Pipeline completo", C.C)}     — Generar + Deploy + IndexNow')
        print(f'  {c("[2]", C.G)} {c("Solo generar", C.C)}          — Regenera los 11 posts + sitemap')
        print(f'  {c("[3]", C.G)} {c("Solo desplegar", C.C)}        — Deploy a Vercel')
        print(f'  {c("[4]", C.G)} {c("Solo IndexNow", C.C)}         — Notificar URLs a Bing/Yandex')
        print(f'  {c("[5]", C.G)} {c("Estado del sistema", C.C)}    — Verificar todo')
        print(f'  {c("[6]", C.G)} {c("Agente autónomo", C.C)}       — Iniciar main_agent.py')
        print(f'  {c("[7]", C.G)} {c("💰 Monetag Revenue", C.C)}      — Dashboard + optimización de ingresos')
        print(f'  {c("[8]", C.G)} {c("📊 SEO Oracle", C.C)}             — Ranking, proyección, plan de contenido')
        print(f'  {c("[0]", C.R)} {c("Salir", C.C)}')
        print()
        
        try:
            choice = input(f'  {c(">", C.G)} Opción: ').strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        
        if choice == '1':
            action_pipeline()
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        elif choice == '2':
            action_generate()
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        elif choice == '3':
            action_deploy()
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        elif choice == '4':
            action_notify()
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        elif choice == '5':
            action_status()
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        elif choice == '6':
            print(f'\n  {c("Iniciando agente autónomo...", C.Y)}')
            print(f'  {c("Presiona Ctrl+C para detener", C.D)}')
            os.system('python main_agent.py')
            input(f'\n  {c("[Enter]", C.D)} para continuar...')
        elif choice == '7':
            action_monetag()
        elif choice == '8':
            action_seo_oracle()
        elif choice == '0':
            print(f'\n  {c("Hasta luego, Joker.", C.C, bold=True)}')
            break


# ═══════════════════════════════════════════════
# 🚀 PUNTO DE ENTRADA
# ═══════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='🌑 Shadow Del Valle R — Control Center')
    parser.add_argument('--all', action='store_true', help='Pipeline completo')
    parser.add_argument('--generate', action='store_true', help='Solo generar posts')
    parser.add_argument('--deploy', action='store_true', help='Solo desplegar a Vercel')
    parser.add_argument('--notify', action='store_true', help='Solo notificar IndexNow')
    parser.add_argument('--status', action='store_true', help='Estado completo del sistema')
    parser.add_argument('--menu', action='store_true', help='Menú interactivo')
    parser.add_argument('--post', action='store_true', help='Generar + deploy + notify')
    
    args = parser.parse_args()
    
    if args.all or args.post:
        action_pipeline()
    elif args.generate:
        action_generate()
    elif args.deploy:
        action_deploy()
    elif args.notify:
        action_notify()
    elif args.status:
        action_status()
    else:
        menu()

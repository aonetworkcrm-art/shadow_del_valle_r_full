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
    R = '\033[0m'
    B = '\033[1m'
    D = '\033[2m'
    G = '\033[92m'
    C = '\033[96m'
    Y = '\033[93m'
    R = '\033[91m'
    M = '\033[95m'


def c(text, color, bold=False):
    prefix = C.B if bold else ''
    return prefix + color + str(text) + C.R


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

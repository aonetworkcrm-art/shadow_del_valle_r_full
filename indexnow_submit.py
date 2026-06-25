#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌑 SHADOW DEL VALLE R — IndexNow Submitter
============================================
Envía URLs a Bing IndexNow para indexación instantánea.
IndexNow es soportado por Bing, Yandex, Naver, Seznam.

Uso:
    python indexnow_submit.py                    # Envía todas las URLs del sitemap
    python indexnow_submit.py --url https://...  # Envía una URL específica
    python indexnow_submit.py --check            # Verifica si IndexNow está configurado
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import argparse
from datetime import datetime

# ─── Configuración ───
DOMAIN = "shadow-del-valle-r.vercel.app"
INDEXNOW_KEY = "c291a640b45f48eab74384a1a7f653d8"
BING_INDEXNOW_URL = "https://www.bing.com/indexnow"
YANDEX_INDEXNOW_URL = "https://yandex.com/indexnow"
# También se puede usar el API directo: https://api.indexnow.org/indexnow

OUTPUT_DIR = "output"
SITEMAP_PATH = os.path.join(OUTPUT_DIR, "sitemap.xml")
POSTS_JSON_PATH = os.path.join(OUTPUT_DIR, "posts.json")

# ─── Colores (Windows compatible) ───
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


def c(text, color, bold=False):
    prefix = C.BOLD if bold else ""
    return prefix + color + str(text) + C.RESET


def get_urls_from_sitemap() -> list:
    """Extrae todas las URLs del sitemap.xml."""
    if not os.path.exists(SITEMAP_PATH):
        print(f"  {c('❌ No se encontró sitemap en:', C.RED)} {SITEMAP_PATH}")
        return []
    
    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    urls = []
    for line in content.split("\n"):
        line = line.strip()
        if "<loc>" in line and "</loc>" in line:
            url = line.split("<loc>")[1].split("</loc>")[0].strip()
            if url:
                urls.append(url)
    
    return urls


def get_urls_from_posts_json() -> list:
    """Obtiene URLs desde posts.json."""
    if not os.path.exists(POSTS_JSON_PATH):
        return []
    
    with open(POSTS_JSON_PATH, "r", encoding="utf-8") as f:
        posts = json.load(f)
    
    return [f"https://{DOMAIN}/posts/{p['slug']}/" for p in posts]


def submit_to_indexnow(urls: list, search_engine_url: str = BING_INDEXNOW_URL) -> dict:
    """
    Envía URLs a IndexNow usando el endpoint de bulk POST.
    
    Args:
        urls: Lista de URLs a indexar
        search_engine_url: URL del endpoint IndexNow
    
    Returns:
        dict: Resultado de la operación
    """
    if not urls:
        return {"success": False, "error": "No URLs to submit", "status_code": 0}
    
    # IndexNow bulk endpoint recibe hasta 10,000 URLs por request
    payload = {
        "host": DOMAIN,
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://{DOMAIN}/{INDEXNOW_KEY}.txt",
        "urlList": urls
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        search_engine_url,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": f"ShadowDelValleR-IndexNow/1.0 ({DOMAIN})"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.status
            body = response.read().decode("utf-8")
            return {
                "success": status in [200, 202],
                "status_code": status,
                "response": body[:200] if body else "OK",
                "urls_submitted": len(urls),
                "engine": search_engine_url
            }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "status_code": e.code,
            "error": str(e),
            "response": e.read().decode("utf-8")[:200] if e.fp else "",
            "urls_submitted": len(urls),
            "engine": search_engine_url
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "status_code": 0,
            "error": f"Connection error: {e.reason}",
            "urls_submitted": len(urls),
            "engine": search_engine_url
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "error": str(e),
            "urls_submitted": len(urls),
            "engine": search_engine_url
        }


def submit_single_url(url: str, search_engine_url: str = BING_INDEXNOW_URL) -> dict:
    """
    Envía una sola URL a IndexNow usando GET.
    
    IndexNow GET format:
    https://www.bing.com/indexnow?url=URL_ENCODED&key=KEY
    """
    import urllib.parse
    encoded_url = urllib.parse.quote(url, safe="")
    full_url = f"{search_engine_url}?url={encoded_url}&key={INDEXNOW_KEY}"
    
    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": f"ShadowDelValleR-IndexNow/1.0 ({DOMAIN})"},
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.status
            return {
                "success": status in [200, 202],
                "status_code": status,
                "url": url,
                "engine": search_engine_url
            }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "status_code": e.code,
            "error": str(e),
            "url": url,
            "engine": search_engine_url
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "status_code": 0,
            "error": f"Connection error: {e.reason}",
            "url": url,
            "engine": search_engine_url
        }


def verify_key_accessibility() -> bool:
    """Verifica que el archivo de key de IndexNow sea accesible públicamente."""
    key_url = f"https://{DOMAIN}/{INDEXNOW_KEY}.txt"
    try:
        req = urllib.request.Request(key_url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8").strip()
            if content == INDEXNOW_KEY:
                print(f"  {c('✅ Key verification file is PUBLICLY ACCESSIBLE', C.GREEN)}")
                print(f"     {key_url}")
                return True
            else:
                print(f"  {c('❌ Key file content mismatch!', C.RED)}")
                print(f"     Expected: {INDEXNOW_KEY}")
                print(f"     Got:      {content}")
                return False
    except Exception as e:
        print(f"  {c(f'❌ Key file NOT accessible: {e}', C.RED)}")
        return False


def check_status():
    """Verifica el estado de configuración de IndexNow."""
    print(f"\n  {c('🔍 VERIFICACIÓN DE INDEXNOW:', C.CYAN, bold=True)}")
    print(f"  {'=' * 50}")
    print(f"  {c('Dominio:', C.YELLOW)} {DOMAIN}")
    print(f"  {c('Key:', C.YELLOW)} {INDEXNOW_KEY}")
    print(f"  {c('Key URL:', C.YELLOW)} https://{DOMAIN}/{INDEXNOW_KEY}.txt")
    
    # Verificar key file
    if os.path.exists(f"output/{INDEXNOW_KEY}.txt"):
        with open(f"output/{INDEXNOW_KEY}.txt") as f:
            content = f.read().strip()
            if content == INDEXNOW_KEY:
                print(f"  {c('✅ Key file local:', C.GREEN)} output/{INDEXNOW_KEY}.txt")
            else:
                print(f"  {c('❌ Key file local content mismatch!', C.RED)}")
    else:
        print(f"  {c('❌ Key file local NOT FOUND!', C.RED)}")
    
    # Verificar accesibilidad pública
    verify_key_accessibility()
    
    # Mostrar URLs a indexar
    urls = get_urls_from_sitemap()
    print(f"\n  {c('📄 URLs en sitemap:', C.YELLOW)} {len(urls)}")
    for u in urls[:5]:
        print(f"     • {u}")
    if len(urls) > 5:
        print(f"     ... y {len(urls) - 5} más")
    
    print(f"\n  {c('Para enviar a IndexNow:', C.CYAN)}")
    print(f"     python indexnow_submit.py")
    print(f"     python indexnow_submit.py --check")
    print(f"     python indexnow_submit.py --url https://{DOMAIN}/posts/tu-post/")


def submit_all(search_engine_url: str = BING_INDEXNOW_URL):
    """Envía TODAS las URLs del sitemap a IndexNow."""
    urls = get_urls_from_sitemap()
    if not urls:
        urls = get_urls_from_posts_json()
    
    if not urls:
        print(f"  {c('❌ No se encontraron URLs para enviar.', C.RED)}")
        print(f"  {c('💡 Genera posts primero:', C.YELLOW)} python generate_all.py")
        return
    
    engine_name = search_engine_url.split("//")[1].split(".")[0].upper()
    
    print(f"\n  {c(f'📤 ENVIANDO A {engine_name} INDEXNOW:', C.CYAN, bold=True)}")
    print(f"  {'=' * 50}")
    print(f"  {c('URLs:', C.YELLOW)} {len(urls)}")
    print(f"  {c('Host:', C.YELLOW)} {DOMAIN}")
    print(f"  {c('Engine:', C.YELLOW)} {search_engine_url}")
    
    # Enviar en lotes de 100 (límite práctico)
    batch_size = 100
    total_success = 0
    total_fail = 0
    
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        print(f"\n  {c(f'Lote {i//batch_size + 1}/{(len(urls)-1)//batch_size + 1}:', C.CYAN)} {len(batch)} URLs")
        
        result = submit_to_indexnow(batch, search_engine_url)
        
        if result["success"]:
            print(f"    {c('✅ Enviado exitosamente', C.GREEN)}")
            total_success += len(batch)
        else:
            status_code = str(result.get("status_code", "?"))
            error_msg = result.get("error", "Desconocido")
            print(f"    {c('❌ Error ' + status_code + ': ' + error_msg, C.RED)}")
            total_fail += len(batch)
            
            # Si falló el bulk, intentar una por una
            if result.get("status_code") in [400, 422, 429]:
                print(f"    {c('↳ Intentando una por una...', C.YELLOW)}")
                for url in batch:
                    r = submit_single_url(url, search_engine_url)
                    if r["success"]:
                        total_success += 1
                    else:
                        total_fail += 1
        
        # Pequeña pausa entre lotes
        if i + batch_size < len(urls):
            time.sleep(0.5)
    
    # Resumen
    print(f"\n  {c('📊 RESUMEN:', C.CYAN, bold=True)}")
    print(f"  {c('✓ Exitosas:', C.GREEN)} {total_success}")
    print(f"  {c('✗ Fallidas:', C.RED)} {total_fail}")
    print(f"  {c('Total:', C.YELLOW)} {total_success + total_fail}")
    
    if total_success > 0:
        print(f"\n  {c('🎯 URLs indexadas en segundos en Bing/Yandex!', C.GREEN, bold=True)}")


def main():
    parser = argparse.ArgumentParser(
        description="🌑 Shadow Del Valle R — IndexNow Submitter"
    )
    parser.add_argument("--url", type=str, help="Enviar una URL específica")
    parser.add_argument("--check", action="store_true", help="Verificar configuración")
    parser.add_argument("--bing", action="store_true", help="Enviar a Bing (default)")
    parser.add_argument("--yandex", action="store_true", help="Enviar a Yandex también")
    
    args = parser.parse_args()
    
    print(f"\n  {c('🌑 SHADOW DEL VALLE R — INDEXNOW SUBMITTER', C.CYAN, bold=True)}")
    print(f"  {c('=' * 46, C.DIM)}")
    
    if args.check:
        check_status()
        return
    
    if args.url:
        print(f"\n  {c('📤 Enviando URL individual...', C.YELLOW)}")
        result = submit_single_url(args.url)
        if result["success"]:
            msg = '✅ URL enviada a IndexNow: ' + args.url
            print(f"  {c(msg, C.GREEN)}")
        else:
            err_msg = result.get("error", "Desconocido")
            print(f"  {c('❌ Error: ' + err_msg, C.RED)}")
        return
    
    # Verificar configuración primero
    check_status()
    
    # Enviar a Bing
    print(f"\n  {'=' * 50}")
    submit_all(BING_INDEXNOW_URL)
    
    # Opcional: enviar también a Yandex
    if args.yandex:
        print(f"\n  {'=' * 50}")
        submit_all(YANDEX_INDEXNOW_URL)
    
    print(f"\n  {c('✅ Proceso completado.', C.GREEN, bold=True)}")
    print(f"  {c('💡 Las URLs ahora están siendo indexadas por Bing/Yandex.', C.DIM)}")
    print(f"  {c('💡 Para Google: agrega el sitio en Google Search Console manualmente.', C.DIM)}")


if __name__ == "__main__":
    main()

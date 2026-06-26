#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   SHADOW DEL VALLE R — AGENTE AUTÓNOMO (AaaS)              ║
║   Agent as a Service — Arbitraje de Tráfico 24/7           ║
╚══════════════════════════════════════════════════════════════╝

Modo de uso:
    python main_agent.py                    # Inicia el agente en modo autónomo
    python main_agent.py --once             # Una sola ronda
    python main_agent.py --status           # Ver estado actual
    python main_agent.py --kill-switch off  # Pausa el agente
    python main_agent.py --kill-switch on   # Reanuda el agente

El agente corre en un bucle infinito controlado por configuración.
Ejecuta: ESCANEAR → EVALUAR → FORJAR → DESPLEGAR → REPETIR.
"""

import json
import os
import signal
import sys
import time
from typing import Dict, List, Optional
from datetime import datetime

# ─── Asegurar que podemos importar los módulos ───
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.radar import Radar, NICHOS_DB
from core.silo_builder import Refinery
from core.silo_connector import SiloConnector
from core.freebuff_bridge import FreeBuffBridge
from core.deployer import Deployer
from core.ledger import Ledger
from generar_contenido import ContentGenerator


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
    BLUE = "\033[94m"

def c(text, color, bold=False):
    prefix = Colors.BOLD if bold else ""
    return prefix + color + str(text) + Colors.RESET


# ─── Estado global ───
class AgentState:
    """Estado del agente, accesible desde cualquier parte."""
    
    def __init__(self):
        self.running = True
        self.paused = False
        self.start_time = time.time()
        self.rounds_completed = 0
        self.total_posts_generated = 0
        self.total_errors = 0
        self.last_round_time = 0
        self.current_cycle = 0
    
    @property
    def uptime(self) -> str:
        delta = time.time() - self.start_time
        days = int(delta // 86400)
        hours = int((delta % 86400) // 3600)
        minutes = int((delta % 3600) // 60)
        return f"{days}d {hours}h {minutes}m"
    
    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time


# ─── Instancia global de estado ───
state = AgentState()


class ShadowDelValleAgent:
    """
    Agente autónomo principal.
    Orquesta el ciclo: ESCANEAR → EVALUAR → FORJAR → DESPLEGAR.
    """
    
    def __init__(self):
        self.name = "Shadow Del Valle R"
        self.version = "1.0.0"
        
        # Cargar configuración
        self.config = self._load_config()
        
        # Inicializar motores
        self.radar = Radar()
        self.refinery = Refinery()
        self.connector = SiloConnector()
        self.bridge = FreeBuffBridge()
        self.deployer = Deployer()
        self.ledger = Ledger()
        self.content_generator = ContentGenerator()
        
        # Config del scheduler
        scheduler = self.config.get("scheduler", {})
        self.agente_activo = scheduler.get("agente_activo", True)
        self.intervalo_horas = float(scheduler.get("intervalo_generacion_horas", 4.0))
        self.max_posts_por_dia = int(scheduler.get("max_posts_por_dia", 6))
        self.estrategia = scheduler.get("estrategia", "rotating")
        
        # Nichos ya procesados (para estrategia rotativa)
        self.nichos_procesados: List[str] = []
        
        # Signal handlers para detención limpia
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        self._log(f"🚀 {self.name} v{self.version} iniciado")
    
    def _load_config(self) -> Dict:
        """Carga configuración desde settings.json."""
        default = {
            "scheduler": {
                "agente_activo": True,
                "intervalo_generacion_horas": 4.0,
                "max_posts_por_dia": 6,
                "estrategia": "rotating"
            },
            "radar": {"umbral_frr_minimo": 150.0},
            "monetag": {"habilitado": False, "site_id": ""}
        }
        try:
            if os.path.exists("config/settings.json"):
                with open("config/settings.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return default
        except:
            return default
    
    def _signal_handler(self, signum, frame):
        self._log("⏹️ Deteniendo agente...")
        state.running = False
    
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {c(msg, Colors.CYAN)}")
    
    def _log_success(self, msg: str):
        print(f"     {c('✅', Colors.GREEN)} {msg}")
    
    def _log_warning(self, msg: str):
        print(f"     {c('⚠️', Colors.YELLOW)} {msg}")
    
    def _log_error(self, msg: str):
        print(f"     {c('❌', Colors.RED)} {msg}")
    
    def _deberia_ejecutar(self) -> bool:
        """Verifica si el agente debería ejecutar una ronda."""
        if not self.agente_activo:
            return False
        
        ahora = time.time()
        if ahora - state.last_round_time < self.intervalo_horas * 3600:
            return False
        
        # Límite diario de posts
        posts_hoy = sum(
            1 for e in self.ledger.entries
            if e.tipo == "post" and e.fecha_simple == datetime.now().strftime("%Y-%m-%d")
        )
        if posts_hoy >= self.max_posts_por_dia:
            self._log_warning(f"Límite diario alcanzado: {posts_hoy}/{self.max_posts_por_dia} posts")
            return False
        
        return True
    
    def _seleccionar_nicho(self) -> Optional[Dict]:
        """Selecciona el siguiente nicho según la estrategia."""
        # Obtener nichos aptos ordenados por FRR
        mejores = self.radar.get_mejores_nichos(top_n=10)
        nichos_aptos = [r.nicho for r in mejores if r.apto]
        
        if not nichos_aptos:
            self._log_warning("No hay nichos aptos para generar contenido")
            return None
        
        if self.estrategia == "highest-cpc":
            nichos_aptos.sort(key=lambda n: n["cpc_avg"], reverse=True)
            return nichos_aptos[0]
        
        elif self.estrategia == "random":
            import random
            return random.choice(nichos_aptos)
        
        else:  # "rotating" (default)
            # Evitar repetir nichos
            no_procesados = [n for n in nichos_aptos if n["id"] not in self.nichos_procesados]
            if not no_procesados:
                # Todos han sido procesados, resetear
                self.nichos_procesados = []
                no_procesados = nichos_aptos
            seleccionado = no_procesados[0]
            self.nichos_procesados.append(seleccionado["id"])
            return seleccionado
    
    def _generar_post(self, nicho: Dict) -> bool:
        """
        Genera un post para el nicho seleccionado.
        Usa OpenRouter (IA real) con fallback a template.
        
        Args:
            nicho: Dict con datos del nicho (de NICHOS_DB o Radar)
        
        Returns:
            bool: True si se generó exitosamente
        """
        try:
            self._log(f"Generando post para: {c(nicho['name'], Colors.YELLOW)}")
            
            # 1. Generar contenido con IA (o template fallback)
            resultado = self.content_generator.generate_for_niche(nicho)
            
            # 2. Extraer datos del resultado
            titulo = resultado["titulo"]
            contenido = resultado["contenido_html"]
            meta_desc = resultado.get("meta_desc", "")
            faqs = resultado.get("faqs", [])
            slug = resultado["slug"]
            keywords = resultado.get("keywords", ", ".join(nicho.get("tags", [])))
            cpc = resultado.get("cpc", nicho.get("cpc_avg", 0))
            
            # 3. Construir el HTML con el Refinery
            html = self.refinery.convertir_a_html(
                titulo=titulo,
                nicho=nicho["name"],
                categoria=nicho.get("category", "General"),
                cpc=cpc,
                contenido_html=contenido,
                meta_desc=meta_desc or f"Guia completa sobre {nicho.get('name', '')}. Informacion actualizada y verificada.",
                keywords=keywords,
                faqs=faqs,
                slug=slug
            )
            
            # 4. Guardar el post
            ruta = self.refinery.guardar_post(html, slug)
            
            # 5. Registrar en el ledger
            clicks_estimados = int(cpc * 0.5)  # Estimación conservadora
            entry = self.ledger.registrar_post(
                titulo=titulo,
                nicho=nicho["name"],
                cpc=cpc,
                clicks_estimados=clicks_estimados
            )
            
            # 6. Registrar en el conector de silos
            self.connector.registrar_post({
                "slug": slug,
                "titulo": titulo,
                "nicho_id": nicho["id"],
                "nicho": nicho["name"],
                "categoria": nicho.get("category", "General"),
                "timestamp": time.time(),
                "frr": self.radar.frr_por_nicho(nicho["id"]) or 0
            })
            
            # 7. Actualizar contadores
            state.total_posts_generated += 1
            state.rounds_completed += 1
            state.last_round_time = time.time()
            
            # Estadísticas del post
            tamano_kb = round(len(html.encode('utf-8')) / 1024, 2)
            frr = self.radar.frr_por_nicho(nicho["id"])
            fuente = resultado.get("source", "template")
            
            self._log_success(f"Post generado: {c(titulo[:50], Colors.GREEN)}")
            self._log_success(f"  📁 {ruta} ({tamano_kb} KB)  🧠 Fuente: {fuente}")
            self._log_success(f"  💰 CPC: ${cpc:.0f} | FRR: {frr:.2f}")
            self._log_success(f"  📈 Proyección diaria: ${cpc * clicks_estimados:.2f}")
            
            # 8. Auto-deploy si está configurado
            if self.config.get("github", {}).get("auto_push", False):
                deploy_result = self.deployer.deploy_completo(
                    f"🌑 Auto: {titulo[:40]} (${cpc:.0f} CPC)"
                )
                if deploy_result.get("success"):
                    self._log_success("Deploy a producción exitoso")
                else:
                    self._log_warning(f"Deploy: {deploy_result.get('etapas', {}).get('github', {}).get('error', 'Configurar auto_push')}")
            
            return True
            
        except Exception as e:
            self._log_error(f"Error generando post: {str(e)}")
            state.total_errors += 1
            return False
    
    def _ejecutar_ronda(self):
        """Ejecuta una ronda completa del ciclo."""
        state.current_cycle += 1
        ciclo = state.current_cycle
        
        print(f"\n{c('─' * 60, Colors.DIM)}")
        self._log(f"Ciclo #{ciclo} — {c(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), Colors.YELLOW)}")
        
        # 1. ESCANEAR — El Radar analiza los nichos
        self._log("🔍 ESCANEANDO nichos de alto CPC...")
        resultados = self.radar.escanear_todos()
        aptos = [r for r in resultados if r.apto]
        self._log_success(f"{len(aptos)}/{len(resultados)} nichos aptos (FRR ≥ {self.radar.umbral_minimo})")
        
        if not aptos:
            self._log_warning("No hay nichos aptos en esta ronda")
            return
        
        # 2. EVALUAR — Seleccionar el mejor nicho
        self._log("📊 EVALUANDO mejor oportunidad...")
        nicho = self._seleccionar_nicho()
        if not nicho:
            self._log_warning("No se pudo seleccionar nicho")
            return
        
        frr = self.radar.frr_por_nicho(nicho["id"])
        self._log_success(f"Seleccionado: {c(nicho['name'], Colors.GREEN)} (FRR: {frr:.2f}, CPC: ${nicho['cpc_avg']:.0f})")
        
        # 3. FORJAR — Generar el post
        self._log("🔧 FORJANDO contenido...")
        exito = self._generar_post(nicho)
        
        if exito:
            # 4. Mostrar dashboard financiero
            print()
            self.ledger.mostrar_dashboard()
    
    def run(self):
        """Bucle principal del agente."""
        self._log(f"Intervalo: {c(f'{self.intervalo_horas}h', Colors.YELLOW)} | "
                  f"Max posts/día: {c(str(self.max_posts_por_dia), Colors.YELLOW)} | "
                  f"Estrategia: {c(self.estrategia, Colors.YELLOW)}")
        self._log("Esperando primera ejecución programada...")
        
        # Primera ejecución inmediata
        self._ejecutar_ronda()
        
        # Bucle principal
        while state.running:
            try:
                # Verificar kill switch en config
                self._reload_config()
                
                if not self.agente_activo:
                    time.sleep(60)  # Revisar cada minuto si se reactivó
                    continue
                
                if self._deberia_ejecutar():
                    self._ejecutar_ronda()
                else:
                    # Mostrar estado cada 30 segundos
                    time.sleep(30)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self._log_error(f"Error en bucle principal: {str(e)}")
                state.total_errors += 1
                time.sleep(60)
        
        self._shutdown()
    
    def run_once(self):
        """Ejecuta una sola ronda y termina."""
        self._log("Modo: Una ronda")
        self._ejecutar_ronda()
        self._log("✅ Ronda completada")
    
    def _reload_config(self):
        """Recarga configuración para detectar cambios en caliente."""
        try:
            config = self._load_config()
            scheduler = config.get("scheduler", {})
            self.agente_activo = scheduler.get("agente_activo", True)
            self.intervalo_horas = float(scheduler.get("intervalo_generacion_horas", 4.0))
            
            # Actualizar umbral del radar
            radar_cfg = config.get("radar", {})
            self.radar.umbral_minimo = float(radar_cfg.get("umbral_frr_minimo", 150.0))
            
            # Actualizar configuración del refinery
            self.refinery.config = config
        except:
            pass
    
    def show_status(self):
        """Muestra el estado actual del agente."""
        print(f"\n{c('═' * 60, Colors.CYAN, bold=True)}")
        print(c(f'  🌑 {self.name} v{self.version} — ESTADO', Colors.CYAN, bold=True))
        print(c('═' * 60, Colors.CYAN, bold=True))
        
        print(f"\n  {c('Estado:', Colors.YELLOW, bold=True)} {c('🟢 ACTIVO' if self.agente_activo else '🔴 PAUSADO', Colors.GREEN if self.agente_activo else Colors.RED)}")
        print(f"  {c('Uptime:', Colors.YELLOW)} {state.uptime}")
        print(f"  {c('Ciclos completados:', Colors.YELLOW)} {state.rounds_completed}")
        print(f"  {c('Posts generados:', Colors.YELLOW)} {state.total_posts_generated}")
        print(f"  {c('Errores:', Colors.YELLOW)} {state.total_errors}")
        print(f"  {c('Intervalo:', Colors.YELLOW)} {self.intervalo_horas}h")
        print(f"  {c('Estrategia:', Colors.YELLOW)} {self.estrategia}")
        print(f"  {c('Max posts/día:', Colors.YELLOW)} {self.max_posts_por_dia}")
        
        # Mostrar dashboard financiero
        self.ledger.mostrar_dashboard()
    
    def _shutdown(self):
        """Apagado limpio del agente."""
        self._log("👋 Apagando agente...")
        
        # Guardar ledger
        reporte = self.ledger.exportar_reporte()
        self._log(f"Ledger guardado: {reporte}")
        
        # Generar sitemap
        if self.refinery.posts_generados:
            sitemap = self.refinery.generar_sitemap(self.refinery.posts_generados)
            self._log(f"Sitemap generado: {sitemap}")
        
        self._log(f"Tiempo total de operación: {state.uptime}")
        self._log("✅ Agente detenido exitosamente")


def kill_switch(action: str):
    """Controla el kill switch del agente."""
    config_path = "config/settings.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        if action == "off":
            config["scheduler"]["agente_activo"] = False
            print("🔴 Agente PAUSADO. Para reanudar: python main_agent.py --kill-switch on")
        elif action == "on":
            config["scheduler"]["agente_activo"] = True
            print("🟢 Agente REANUDADO.")
        else:
            current = config.get("scheduler", {}).get("agente_activo", True)
            print(f"Estado actual del agente: {'🟢 ACTIVO' if current else '🔴 PAUSADO'}")
            return
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Error: {e}")


# ─── Punto de entrada ───
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🌑 Shadow Del Valle R — Agente Autónomo AaaS"
    )
    parser.add_argument("--once", action="store_true", help="Ejecutar una sola ronda")
    parser.add_argument("--status", action="store_true", help="Mostrar estado actual")
    parser.add_argument("--kill-switch", type=str, choices=["on", "off", "status"],
                      help="Controlar el agente (on/off/status)")
    
    args = parser.parse_args()
    
    if args.kill_switch:
        kill_switch(args.kill_switch)
    elif args.status:
        agent = ShadowDelValleAgent()
        agent.show_status()
    elif args.once:
        agent = ShadowDelValleAgent()
        agent.run_once()
    else:
        agent = ShadowDelValleAgent()
        try:
            agent.run()
        except KeyboardInterrupt:
            print("\n\n👋 Hasta luego, Joker. El sistema queda listo para continuar.")

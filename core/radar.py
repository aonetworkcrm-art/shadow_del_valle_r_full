# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Motor 1: El Radar
=======================================
Cálculo de viabilidad predictiva para nichos de alto CPC.
Factor de Rentabilidad Relativa (FRR) con precisión de float.

Detecta intención anticipada, mide tendencias en tiempo real
y decide qué nichos atacar con precisión quirúrgica.
"""

import json
import math
import os
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal, getcontext, ROUND_HALF_DOWN

getcontext().prec = 28
getcontext().rounding = ROUND_HALF_DOWN


# ─── Base de conocimiento de nichos de alto CPC ───
NICHOS_DB = [
    {
        "id": "personal-injury-law",
        "name": "Abogados de Accidentes (Personal Injury)",
        "category": "Servicios Legales",
        "cpc_avg": 220.0,
        "cpc_min": 150.0,
        "cpc_max": 300.0,
        "search_volume": 8500.0,
        "competencia": 85.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["accidentes", "abogados", "lesiones", "compensación", "indemnización"],
        "description": "El nicho más caro en publicidad digital. Personas que sufrieron accidentes buscan representación legal inmediata."
    },
    {
        "id": "asset-recovery",
        "name": "Recuperación de Activos Financieros",
        "category": "Servicios Legales",
        "cpc_avg": 125.0,
        "cpc_min": 100.0,
        "cpc_max": 150.0,
        "search_volume": 3400.0,
        "competencia": 45.0,
        "evergreen_score": 9,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["recuperación", "activos", "estafas", "fondos", "crypto"],
        "description": "Personas que perdieron dinero en estafas financieras o cripto y buscan servicios profesionales para recuperarlo."
    },
    {
        "id": "cybersecurity-compliance",
        "name": "Ciberseguridad y Compliance",
        "category": "Tecnología B2B",
        "cpc_avg": 170.0,
        "cpc_min": 140.0,
        "cpc_max": 200.0,
        "search_volume": 2800.0,
        "competencia": 55.0,
        "evergreen_score": 9,
        "intent": "comercial",
        "language": "en",
        "tags": ["ciberseguridad", "compliance", "SOC2", "auditoría", "seguridad"],
        "description": "Empresas que necesitan certificaciones de seguridad y compliance. Alto valor por cliente (B2B)."
    },
    {
        "id": "drug-rehab",
        "name": "Centros de Rehabilitación",
        "category": "Salud",
        "cpc_avg": 120.0,
        "cpc_min": 80.0,
        "cpc_max": 150.0,
        "search_volume": 7200.0,
        "competencia": 75.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["rehabilitación", "adicción", "tratamiento", "desintoxicación", "ayuda"],
        "description": "Personas y familias buscando ayuda para adicciones. Cada paciente vale miles de dólares."
    },
    {
        "id": "life-insurance-seniors",
        "name": "Seguros de Vida para Adultos Mayores",
        "category": "Seguros",
        "cpc_avg": 95.0,
        "cpc_min": 70.0,
        "cpc_max": 120.0,
        "search_volume": 9500.0,
        "competencia": 70.0,
        "evergreen_score": 9,
        "intent": "comercial",
        "language": "ambos",
        "tags": ["seguros", "vida", "adultos mayores", "funerarios", "protección"],
        "description": "Adultos mayores buscando opciones de seguro. Nicho YMYL que requiere contenido altamente confiable."
    },
    {
        "id": "online-mba",
        "name": "MBA y Posgrados Online",
        "category": "Educación",
        "cpc_avg": 100.0,
        "cpc_min": 70.0,
        "cpc_max": 130.0,
        "search_volume": 5200.0,
        "competencia": 40.0,
        "evergreen_score": 8,
        "intent": "comercial",
        "language": "ambos",
        "tags": ["MBA", "posgrado", "educación", "online", "maestría"],
        "description": "Profesionales buscando avanzar su educación. Buen CPC con dificultad media de posicionamiento."
    },
    {
        "id": "high-risk-auto",
        "name": "Seguros de Auto Alto Riesgo",
        "category": "Seguros",
        "cpc_avg": 105.0,
        "cpc_min": 80.0,
        "cpc_max": 130.0,
        "search_volume": 6800.0,
        "competencia": 60.0,
        "evergreen_score": 9,
        "intent": "transaccional",
        "language": "en",
        "tags": ["seguro", "auto", "alto riesgo", "SR22", "cotización"],
        "description": "Conductores con historial problemático buscando seguro. Muy alta demanda, CPC elevado."
    },
    {
        "id": "defi-investment",
        "name": "Inversiones DeFi",
        "category": "Finanzas",
        "cpc_avg": 85.0,
        "cpc_min": 60.0,
        "cpc_max": 110.0,
        "search_volume": 4200.0,
        "competencia": 35.0,
        "evergreen_score": 7,
        "intent": "comercial",
        "language": "ambos",
        "tags": ["DeFi", "inversiones", "cripto", "yield", "portfolio"],
        "description": "Inversores buscando plataformas y estrategias DeFi. Contenido educativo con alta conversión."
    },
    {
        "id": "mesothelioma",
        "name": "Mesotelioma y Enfermedades Laborales",
        "category": "Servicios Legales",
        "cpc_avg": 150.0,
        "cpc_min": 100.0,
        "cpc_max": 200.0,
        "search_volume": 1800.0,
        "competencia": 90.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["mesotelioma", "asbesto", "cáncer", "compensación", "laboral"],
        "description": "Nicho ultra específico pero de altísimo CPC. Volumen bajo, pero cada conversión vale fortunas."
    },
    {
        "id": "enterprise-cyber",
        "name": "Ciberseguridad Empresarial",
        "category": "Tecnología B2B",
        "cpc_avg": 120.0,
        "cpc_min": 90.0,
        "cpc_max": 160.0,
        "search_volume": 4800.0,
        "competencia": 50.0,
        "evergreen_score": 9,
        "intent": "comercial",
        "language": "en",
        "tags": ["ciberseguridad", "empresarial", "ransomware", "cloud", "protección"],
        "description": "Empresas buscando soluciones de ciberseguridad. Alto CPC y contratos anuales de gran valor."
    },
    # ═══════════════════════════════════════════════
    # 🆕 NICHOS DE ALTO CPC (>$200) — AGREGADOS JUNIO 2026
    # ═══════════════════════════════════════════════
    {
        "id": "earthquake-personal-injury",
        "name": "Lesiones por Terremoto — Abogados",
        "category": "Servicios Legales",
        "cpc_avg": 250.0,
        "cpc_min": 180.0,
        "cpc_max": 350.0,
        "search_volume": 6400.0,
        "competencia": 70.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["lesiones", "terremoto", "abogados", "indemnización", "compensación", "daños"],
        "description": "Victimas de terremotos buscando representacion legal por lesiones personales. CPC altisimo por urgencia y alto valor de cada caso."
    },
    {
        "id": "wrongful-death-earthquake",
        "name": "Muerte Accidental por Terremoto — Indemnización",
        "category": "Servicios Legales",
        "cpc_avg": 245.0,
        "cpc_min": 180.0,
        "cpc_max": 320.0,
        "search_volume": 3800.0,
        "competencia": 65.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["muerte accidental", "indemnización", "terremoto", "abogados", "compensación familiar", "wrongful death"],
        "description": "Familias que perdieron seres queridos en el terremoto buscan compensación legal. Nicho sensible pero de altísimo CPC."
    },
    {
        "id": "post-disaster-fraud-law",
        "name": "Estafas Post-Desastre — Protección Legal",
        "category": "Servicios Legales",
        "cpc_avg": 210.0,
        "cpc_min": 150.0,
        "cpc_max": 280.0,
        "search_volume": 4200.0,
        "competencia": 50.0,
        "evergreen_score": 9,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["estafas", "fraude", "post-desastre", "abogados", "recuperación", "protección legal"],
        "description": "Personas estafadas después del terremoto buscan recuperar su dinero y protección legal. Nicho con alta intención de contratación."
    },
    {
        "id": "life-insurance-disaster",
        "name": "Seguro de Vida por Desastres Naturales",
        "category": "Seguros",
        "cpc_avg": 200.0,
        "cpc_min": 140.0,
        "cpc_max": 260.0,
        "search_volume": 7500.0,
        "competencia": 60.0,
        "evergreen_score": 9,
        "intent": "comercial",
        "language": "ambos",
        "tags": ["seguro de vida", "desastres naturales", "protección familiar", "cobertura terremoto", "reclamación"],
        "description": "Personas que quieren proteger a su familia ante desastres naturales. Alto volumen de búsqueda con CPC premium."
    },
    {
        "id": "structural-damage-claims",
        "name": "Reclamaciones por Daños Estructurales",
        "category": "Seguros",
        "cpc_avg": 225.0,
        "cpc_min": 160.0,
        "cpc_max": 300.0,
        "search_volume": 5100.0,
        "competencia": 55.0,
        "evergreen_score": 9,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["daños estructurales", "reclamaciones", "seguro vivienda", "perito", "evaluación daños", "terremoto"],
        "description": "Propietarios de viviendas dañadas por el terremoto buscando maximizar su reclamo de seguro. Alto CPC por alta competencia entre ajustadores."
    }
]


class RadarReport:
    """Reporte de una ronda de escaneo del radar."""
    
    def __init__(self, nicho: Dict, frr: float, apto: bool, timestamp: float):
        self.nicho = nicho
        self.frr = frr
        self.apto = apto
        self.timestamp = timestamp
        self.fecha = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict:
        return {
            "nicho": self.nicho["name"],
            "nicho_id": self.nicho["id"],
            "cpc_avg": self.nicho["cpc_avg"],
            "frr": round(self.frr, 4),
            "apto": self.apto,
            "timestamp": self.timestamp,
            "fecha": self.fecha,
            "categoria": self.nicho["category"],
            "intencion": self.nicho["intent"],
        }


class Radar:
    """
    Motor de radar predictivo.
    Escanea nichos, calcula FRR y determina viabilidad.
    """
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config = self._load_config(config_path)
        self.umbral_minimo = float(self.config.get("radar", {}).get("umbral_frr_minimo", 150.0))
        self.historial_escaneos: List[RadarReport] = []
        self.nichos_activos: List[str] = []
        self._ultimo_escaneo = 0.0
    
    def _load_config(self, path: str) -> Dict:
        """Carga configuración desde JSON."""
        default = {
            "radar": {
                "umbral_frr_minimo": 150.0,
                "intervalo_escaneo_horas": 2.0,
                "cpc_minimo": 80.0,
                "volumen_minimo": 500.0
            }
        }
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return default
        except:
            return default
    
    def calcular_frr(self, cpc: float, volumen: float, competencia: float) -> float:
        """
        Calcula el Factor de Rentabilidad Relativa (FRR).
        
        FRR = (CPC * Volumen) / (Competencia + 1.0)
        
        Args:
            cpc: Costo por clic en USD
            volumen: Volumen de búsqueda estimado
            competencia: Nivel de competencia (0-100)
        
        Returns:
            float: FRR a 4 decimales. >150 = apto para silo
        """
        cpc_f = float(cpc)
        volumen_f = float(volumen)
        competencia_f = float(competencia)
        
        if cpc_f < 0.0 or volumen_f < 0.0 or competencia_f < 0.0:
            return 0.0
        
        if cpc_f < float(self.config.get("radar", {}).get("cpc_minimo", 80.0)):
            return 0.0
        
        if volumen_f < float(self.config.get("radar", {}).get("volumen_minimo", 500.0)):
            return 0.0
        
        numerador = cpc_f * volumen_f
        denominador = competencia_f + 1.0
        
        return round(numerador / denominador, 4)
    
    def escanear_nicho(self, nicho: Dict) -> RadarReport:
        """Escanea un nicho individual y genera reporte."""
        frr = self.calcular_frr(
            cpc=nicho["cpc_avg"],
            volumen=nicho["search_volume"],
            competencia=nicho["competencia"]
        )
        apto = frr >= self.umbral_minimo
        reporte = RadarReport(nicho, frr, apto, time.time())
        self.historial_escaneos.append(reporte)
        return reporte
    
    def escanear_todos(self) -> List[RadarReport]:
        """Escanea todos los nichos disponibles y devuelve resultados."""
        resultados = []
        for nicho in NICHOS_DB:
            reporte = self.escanear_nicho(nicho)
            resultados.append(reporte)
        self._ultimo_escaneo = time.time()
        return resultados
    
    def get_mejores_nichos(self, top_n: int = 3) -> List[RadarReport]:
        """Retorna los top_n nichos con mejor FRR."""
        reportes = self.escanear_todos()
        aptos = [r for r in reportes if r.apto]
        aptos.sort(key=lambda r: r.frr, reverse=True)
        return aptos[:top_n]
    
    def get_estadisticas_radar(self) -> Dict:
        """Retorna estadísticas del radar en tiempo real."""
        total = len(self.historial_escaneos)
        aptos = sum(1 for r in self.historial_escaneos if r.apto)
        no_aptos = total - aptos
        
        frr_promedio = 0.0
        if aptos > 0:
            frr_promedio = sum(r.frr for r in self.historial_escaneos if r.apto) / aptos
        
        mejores = [r for r in self.historial_escaneos if r.apto]
        mejores.sort(key=lambda r: r.frr, reverse=True)
        
        return {
            "total_escaneos": total,
            "nichos_aptos": aptos,
            "nichos_no_aptos": no_aptos,
            "frr_promedio_aptos": round(frr_promedio, 2),
            "umbral_actual": self.umbral_minimo,
            "ultimo_escaneo": datetime.fromtimestamp(self._ultimo_escaneo).strftime("%Y-%m-%d %H:%M:%S") if self._ultimo_escaneo else "Nunca",
            "mejores_nichos": [
                {
                    "nombre": r.nicho["name"],
                    "frr": r.frr,
                    "cpc": r.nicho["cpc_avg"],
                    "categoria": r.nicho["category"]
                }
                for r in mejores[:5]
            ],
            "timestamp": time.time()
        }
    
    def proyectar_ingreso_diario(self, posts_por_dia: int = 4, clicks_por_post: int = 50) -> Dict:
        """
        Proyección de ingreso diario basado en los nichos activos.
        
        Args:
            posts_por_dia: Cantidad de posts generados por día
            clicks_por_post: Clicks estimados por post por día
        
        Returns:
            Dict con proyecciones detalladas
        """
        nichos_aptos = [r for r in self.historial_escaneos if r.apto]
        
        if not nichos_aptos:
            return {
                "ingreso_diario_min": 0.0,
                "ingreso_diario_max": 0.0,
                "ingreso_diario_avg": 0.0,
                "ingreso_mensual": 0.0,
                "ingreso_anual": 0.0,
                "posts_por_dia": 0,
                "mensaje": "No hay nichos aptos. Ajusta el umbral FRR."
            }
        
        # Tomar los mejores nichos
        nichos_aptos.sort(key=lambda r: r.frr, reverse=True)
        top = nichos_aptos[:min(posts_por_dia, len(nichos_aptos))]
        
        ingresos_diarios = []
        for r in top:
            cpc = r.nicho["cpc_avg"]
            ingreso_diario = cpc * clicks_por_post
            ingresos_diarios.append(ingreso_diario)
        
        total_diario = sum(ingresos_diarios)
        
        return {
            "ingreso_diario_promedio": round(total_diario, 2),
            "ingreso_diario_por_nicho": [
                {
                    "nicho": r.nicho["name"],
                    "cpc": r.nicho["cpc_avg"],
                    "clicks_estimados": clicks_por_post,
                    "ingreso_diario": round(r.nicho["cpc_avg"] * clicks_por_post, 2)
                }
                for r in top
            ],
            "ingreso_semanal": round(total_diario * 7, 2),
            "ingreso_mensual": round(total_diario * 30, 2),
            "ingreso_anual": round(total_diario * 365, 2),
            "posts_por_dia": len(top),
            "clicks_por_post": clicks_por_post,
            "timestamp": time.time()
        }
    
    def frr_por_nicho(self, nicho_id: str) -> Optional[float]:
        """Calcula FRR para un nicho específico por ID."""
        nicho = next((n for n in NICHOS_DB if n["id"] == nicho_id), None)
        if not nicho:
            return None
        return self.calcular_frr(nicho["cpc_avg"], nicho["search_volume"], nicho["competencia"])


# ─── Demo / Uso directo ───
if __name__ == "__main__":
    import time
    
    radar = Radar()
    
    print("=" * 65)
    print("  🔍 SHADOW DEL VALLE R — RADAR PREDICTIVO")
    print("=" * 65)
    
    resultados = radar.escanear_todos()
    
    print(f"\n{'Nicho':<40} {'CPC':>8} {'FRR':>10} {'Estado':>12}")
    print("-" * 70)
    
    for r in sorted(resultados, key=lambda x: x.frr, reverse=True):
        estado = "✅ APTO" if r.apto else "❌ DESCARTADO"
        cpc_str = f"${r.nicho['cpc_avg']:.0f}"
        print(f"  {r.nicho['name']:<38} {cpc_str:>8} {r.frr:>10.2f} {estado:>12}")
    
    print("\n📊 PROYECCIÓN DE INGRESOS (50 clicks/post/día):")
    proy = radar.proyectar_ingreso_diario(posts_por_dia=4, clicks_por_post=50)
    print(f"  💵 Ingreso diario:        ${proy['ingreso_diario_promedio']:>8,.2f}")
    print(f"  💵 Ingreso semanal:       ${proy['ingreso_semanal']:>8,.2f}")
    print(f"  💵 Ingreso mensual:       ${proy['ingreso_mensual']:>8,.2f}")
    print(f"  💵 Ingreso anual:         ${proy['ingreso_anual']:>8,.2f}")
    print(f"  📝 Posts activos:         {proy['posts_por_dia']}")
    
    print("\n" + "=" * 65)
    print("  ✅ RADAR OPERACIONAL")
    print("=" * 65)

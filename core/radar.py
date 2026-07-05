# -*- coding: utf-8 -*-
"""
Shadow Del Valle R — Motor 1: El Radar
=======================================
Cálculo de viabilidad predictiva para nichos de alto CPC.
Factor de Rentabilidad Relativa (FRR) con precisión de float.

Fusión de:
  - Radar original: FRR, escaneo, historial, proyección simple
  - SEO Oracle (Proyecto Infinito): dataclasses, profitability_score,
    yield projection LOW/AVG/HIGH, confidence, content plan

Uso:
    # Legacy (compatible)
    radar = Radar()
    resultados = radar.escanear_todos()
    mejores = radar.get_mejores_nichos(5)

    # Nuevo SEO Oracle (en el mismo Radar)
    ranking = radar.rank_by_profitability()
    proy = radar.calculate_yield_projection("personal-injury-law")
    plan = radar.create_content_plan(["personal-injury-law", "asset-recovery"])
    radar.export_report("reporte.json")

Autor: Romny (El Joker) + Buffy (Codebuff AI)
Versión: 2.0.0
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
from enum import Enum
from typing import Dict, List, Optional, Any

getcontext().prec = 28
getcontext().rounding = ROUND_HALF_DOWN


# ═══════════════════════════════════════════════════════════════
# ENUMS Y DATACLASSES — SEO Oracle (Proyecto Infinito)
# ═══════════════════════════════════════════════════════════════

class TrafficDifficulty(Enum):
    """Nivel de dificultad para posicionar tráfico."""
    MUY_BAJA = "muy_baja"
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    MUY_ALTA = "muy_alta"


class SearchVolume(Enum):
    """Volumen de búsqueda cualitativo."""
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    MUY_ALTO = "muy_alto"


class SearchIntent(Enum):
    """Intención de búsqueda."""
    INFORMATIVA = "informativa"
    TRANSACCIONAL = "transaccional"
    COMERCIAL = "comercial"
    NAVEGACIONAL = "navegacional"


class ConfidenceLevel(Enum):
    """Nivel de confianza en la proyección."""
    MUY_ALTA = "muy_alta"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


@dataclass
class HighCPCNiche:
    """
    Representa un nicho de alto CPC con todas sus métricas.
    Combina campos del Radar (search_volume_numeric, competencia) con
    los del SEO Oracle (search_volume cualitativo, difficulty enum).
    """
    id: str
    name: str
    category: str
    keywords: List[str]
    cpc_min: Decimal
    cpc_max: Decimal
    cpc_avg: Decimal
    search_volume: SearchVolume
    search_volume_numeric: float
    difficulty: TrafficDifficulty
    competencia: float
    intent: SearchIntent
    evergreen_score: int
    language: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    example_urls: List[str] = field(default_factory=list)

    @property
    def cpc_range_str(self) -> str:
        return f"${self.cpc_min} - ${self.cpc_max}"

    @property
    def profitability_score(self) -> Decimal:
        """
        Score combinado de rentabilidad (CPC × demanda × evergreen).
        Fórmula original del SEO Oracle de Proyecto Infinito.
        """
        volume_map = {
            SearchVolume.BAJO: 2,
            SearchVolume.MEDIO: 5,
            SearchVolume.ALTO: 8,
            SearchVolume.MUY_ALTO: 10,
        }
        vol_score = Decimal(str(volume_map.get(self.search_volume, 5)))
        return self.cpc_avg * vol_score * Decimal(str(self.evergreen_score))

    def calcular_frr(self) -> float:
        """FRR = (CPC * Volumen) / (Competencia + 1) — fórmula del Radar."""
        return round(
            (float(self.cpc_avg) * self.search_volume_numeric) / (self.competencia + 1.0),
            4
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "keywords": self.keywords,
            "cpc_min": float(self.cpc_min), "cpc_max": float(self.cpc_max),
            "cpc_avg": float(self.cpc_avg),
            "search_volume": self.search_volume.value,
            "search_volume_numeric": self.search_volume_numeric,
            "difficulty": self.difficulty.value,
            "competencia": self.competencia,
            "intent": self.intent.value,
            "evergreen_score": self.evergreen_score,
            "language": self.language, "description": self.description,
            "tags": self.tags,
            "frr": self.calcular_frr(),
            "profitability_score": float(self.profitability_score),
        }


@dataclass
class ContentNode:
    """Nodo de contenido (post) para tracking de revenue real vs proyectado."""
    niche_id: str
    niche_name: str
    title: str
    slug: str
    target_keywords: List[str]
    monthly_visitors: int = 0
    ctr_pct: float = 2.0
    cpc_actual: float = 0.0
    cpc_expected: float = 0.0
    monthly_revenue_est: float = 0.0
    monthly_revenue_real: float = 0.0
    created_at: str = ""
    published: bool = False
    source: str = ""

    def estimate_revenue(self) -> float:
        clicks = int(self.monthly_visitors * (self.ctr_pct / 100))
        return round(clicks * (self.cpc_actual or self.cpc_expected), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "niche_id": self.niche_id, "niche_name": self.niche_name,
            "title": self.title, "slug": self.slug,
            "target_keywords": self.target_keywords,
            "monthly_visitors": self.monthly_visitors,
            "ctr_pct": self.ctr_pct,
            "cpc_actual": self.cpc_actual, "cpc_expected": self.cpc_expected,
            "monthly_revenue_est": self.monthly_revenue_est or self.estimate_revenue(),
            "monthly_revenue_real": self.monthly_revenue_real,
            "created_at": self.created_at,
            "published": self.published, "source": self.source,
        }


@dataclass
class YieldProjection:
    """Proyección de ingresos con rangos LOW/AVG/HIGH y confidence."""
    niche_id: str
    niche_name: str
    nodes_count: int
    monthly_visitors_total: int
    ctr_pct: float
    clicks_monthly: int
    cpc_range: Dict[str, float]
    monthly_revenue: Dict[str, float]
    yearly_revenue: Dict[str, float]
    confidence: ConfidenceLevel

    def to_dict(self) -> Dict[str, Any]:
        return {
            "niche": self.niche_name, "niche_id": self.niche_id,
            "nodes_count": self.nodes_count,
            "monthly_visitors_total": self.monthly_visitors_total,
            "ctr_pct": self.ctr_pct, "clicks_monthly": self.clicks_monthly,
            "cpc_range": self.cpc_range,
            "monthly_revenue": self.monthly_revenue,
            "yearly_revenue": self.yearly_revenue,
            "confidence": self.confidence.value,
        }


# ═══════════════════════════════════════════════════════════════
# MAPEO de volúmenes cualitativos → SearchVolume enum
# ═══════════════════════════════════════════════════════════════

_VOLUME_TO_ENUM = {
    2200: SearchVolume.BAJO,
    3200: SearchVolume.MEDIO,
    3800: SearchVolume.MEDIO,
    4200: SearchVolume.MEDIO,
    4500: SearchVolume.MEDIO,
    5100: SearchVolume.ALTO,
    5500: SearchVolume.ALTO,
    5800: SearchVolume.ALTO,
    6400: SearchVolume.ALTO,
    7500: SearchVolume.MUY_ALTO,
    8000: SearchVolume.MUY_ALTO,
    9500: SearchVolume.MUY_ALTO,
    10000: SearchVolume.MUY_ALTO,
}

_DIFFICULTY_MAP = {
    40: TrafficDifficulty.MEDIA,
    45: TrafficDifficulty.MEDIA,
    50: TrafficDifficulty.ALTA,
    55: TrafficDifficulty.ALTA,
    60: TrafficDifficulty.ALTA,
    65: TrafficDifficulty.ALTA,
    70: TrafficDifficulty.ALTA,
    75: TrafficDifficulty.ALTA,
    80: TrafficDifficulty.MUY_ALTA,
    90: TrafficDifficulty.MUY_ALTA,
}

_INTENT_MAP = {
    "transaccional": SearchIntent.TRANSACCIONAL,
    "comercial": SearchIntent.COMERCIAL,
    "informativa": SearchIntent.INFORMATIVA,
    "navegacional": SearchIntent.NAVEGACIONAL,
}


def _get_search_volume_enum(volume: float) -> SearchVolume:
    """Mapea un volumen numérico a su enum cualitativo."""
    return _VOLUME_TO_ENUM.get(volume, SearchVolume.MEDIO)


def _get_difficulty_enum(comp: float) -> TrafficDifficulty:
    """Mapea competencia numérica a enum de dificultad."""
    return _DIFFICULTY_MAP.get(int(comp), TrafficDifficulty.ALTA)


def _get_intent_enum(intent: str) -> SearchIntent:
    """Mapea string de intención a enum."""
    return _INTENT_MAP.get(intent, SearchIntent.COMERCIAL)


def _dict_to_highcpc(d: Dict) -> HighCPCNiche:
    """Convierte un dict de NICHOS_DB a HighCPCNiche dataclass."""
    return HighCPCNiche(
        id=d["id"],
        name=d["name"],
        category=d["category"],
        keywords=d.get("tags", []),
        cpc_min=Decimal(str(d.get("cpc_min", d["cpc_avg"]))),
        cpc_max=Decimal(str(d.get("cpc_max", d["cpc_avg"]))),
        cpc_avg=Decimal(str(d["cpc_avg"])),
        search_volume=_get_search_volume_enum(d["search_volume"]),
        search_volume_numeric=d["search_volume"],
        difficulty=_get_difficulty_enum(d["competencia"]),
        competencia=d["competencia"],
        intent=_get_intent_enum(d.get("intent", "comercial")),
        evergreen_score=d.get("evergreen_score", 7),
        language=d.get("language", "ambos"),
        description=d.get("description", ""),
        tags=d.get("tags", []),
    )


# ═══════════════════════════════════════════════════════════════
# BASE DE CONOCIMIENTO DE NICHOS (backward compatible)
# ═══════════════════════════════════════════════════════════════

NICHOS_DB = [
    {
        "id": "personal-injury-law",
        "name": "Abogados de Accidentes (Personal Injury)",
        "category": "Servicios Legales",
        "cpc_avg": 220.0,
        "cpc_min": 150.0,
        "cpc_max": 300.0,
        "search_volume": 9500.0,
        "competencia": 90.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["accidentes", "abogados", "lesiones personales", "indemnización", "personal injury attorney", "car accident lawyer"],
        "description": "El nicho más caro en publicidad digital. Personas que sufrieron accidentes buscan representación legal inmediata."
    },
    {
        "id": "cybersecurity-compliance",
        "name": "Ciberseguridad y Compliance Empresarial",
        "category": "Tecnología B2B",
        "cpc_avg": 170.0,
        "cpc_min": 140.0,
        "cpc_max": 200.0,
        "search_volume": 3200.0,
        "competencia": 70.0,
        "evergreen_score": 9,
        "intent": "comercial",
        "language": "en",
        "tags": ["ciberseguridad", "compliance", "SOC2", "auditoría seguridad", "enterprise cybersecurity", "penetration testing"],
        "description": "Empresas que necesitan certificaciones de seguridad y compliance. Alto valor por cliente (B2B)."
    },
    {
        "id": "mesothelioma",
        "name": "Mesotelioma y Enfermedades Laborales",
        "category": "Servicios Legales",
        "cpc_avg": 150.0,
        "cpc_min": 100.0,
        "cpc_max": 200.0,
        "search_volume": 2200.0,
        "competencia": 90.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["mesotelioma", "asbesto", "cáncer laboral", "compensación", "mesothelioma law firm", "asbestos cancer lawyer"],
        "description": "Nicho ultra específico pero de altísimo CPC. Volumen bajo, pero cada conversión vale fortunas."
    },
    {
        "id": "asset-recovery",
        "name": "Recuperación de Activos Financieros",
        "category": "Servicios Legales",
        "cpc_avg": 125.0,
        "cpc_min": 100.0,
        "cpc_max": 150.0,
        "search_volume": 3800.0,
        "competencia": 50.0,
        "evergreen_score": 9,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["recuperación activos", "estafas financieras", "fondos recuperados", "crypto tracing", "fund recovery specialist", "stolen asset recovery"],
        "description": "Personas que perdieron dinero en estafas financieras o cripto y buscan servicios profesionales para recuperarlo."
    },
    {
        "id": "enterprise-cyber",
        "name": "Ciberseguridad Empresarial",
        "category": "Tecnología B2B",
        "cpc_avg": 120.0,
        "cpc_min": 90.0,
        "cpc_max": 160.0,
        "search_volume": 5500.0,
        "competencia": 55.0,
        "evergreen_score": 9,
        "intent": "comercial",
        "language": "en",
        "tags": ["ciberseguridad empresarial", "ransomware", "cloud security", "managed detection response", "zero trust security", "endpoint protection"],
        "description": "Empresas buscando soluciones de ciberseguridad. Alto CPC y contratos anuales de gran valor."
    },
    {
        "id": "drug-rehab",
        "name": "Centros de Rehabilitación",
        "category": "Salud",
        "cpc_avg": 120.0,
        "cpc_min": 80.0,
        "cpc_max": 150.0,
        "search_volume": 8000.0,
        "competencia": 80.0,
        "evergreen_score": 10,
        "intent": "transaccional",
        "language": "ambos",
        "tags": ["rehabilitación", "adicción", "tratamiento drogas", "desintoxicación", "inpatient rehab", "detox center", "alcohol rehab"],
        "description": "Personas y familias buscando ayuda para adicciones. Cada paciente vale miles de dólares."
    },
    {
        "id": "high-risk-auto",
        "name": "Seguros de Auto para Alto Riesgo",
        "category": "Seguros",
        "cpc_avg": 105.0,
        "cpc_min": 80.0,
        "cpc_max": 130.0,
        "search_volume": 7500.0,
        "competencia": 65.0,
        "evergreen_score": 9,
        "intent": "transaccional",
        "language": "en",
        "tags": ["seguro auto alto riesgo", "SR22 insurance", "non owner car insurance", "high risk auto insurance", "cheap insurance after accident"],
        "description": "Conductores con historial problemático buscando seguro. Muy alta demanda, CPC elevado."
    },
    {
        "id": "online-mba",
        "name": "MBA y Programas de Posgrado Online",
        "category": "Educación",
        "cpc_avg": 100.0,
        "cpc_min": 70.0,
        "cpc_max": 130.0,
        "search_volume": 5800.0,
        "competencia": 45.0,
        "evergreen_score": 8,
        "intent": "comercial",
        "language": "ambos",
        "tags": ["MBA online", "posgrado", "maestría en línea", "executive MBA", "online master degree", "accredited online education"],
        "description": "Profesionales buscando avanzar su educación. Buen CPC con dificultad media de posicionamiento."
    },
    {
        "id": "life-insurance-seniors",
        "name": "Seguros de Vida para Adultos Mayores",
        "category": "Seguros",
        "cpc_avg": 95.0,
        "cpc_min": 70.0,
        "cpc_max": 120.0,
        "search_volume": 10000.0,
        "competencia": 75.0,
        "evergreen_score": 9,
        "intent": "comercial",
        "language": "ambos",
        "tags": ["seguro vida adultos mayores", "final expense insurance", "burial insurance", "life insurance seniors", "seguro funerario"],
        "description": "Adultos mayores buscando opciones de seguro. Nicho YMYL que requiere contenido altamente confiable."
    },
    {
        "id": "defi-investment",
        "name": "Inversiones y Gestión DeFi",
        "category": "Finanzas",
        "cpc_avg": 85.0,
        "cpc_min": 60.0,
        "cpc_max": 110.0,
        "search_volume": 4500.0,
        "competencia": 40.0,
        "evergreen_score": 7,
        "intent": "comercial",
        "language": "ambos",
        "tags": ["DeFi", "inversiones cripto", "yield farming", "crypto portfolio", "DeFi asset management", "gestión DeFi"],
        "description": "Inversores buscando plataformas y estrategias DeFi. Contenido educativo con alta conversión."
    },
    # ═══════════════════════════════════════════════
    # 🆕 NICHOS DE ALTO CPC (>$200) — TERREMOTO VENEZUELA
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
        "description": "Victimas de terremotos buscando representacion legal por lesiones personales. CPC altisimo por urgencia."
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
        "description": "Personas estafadas después del terremoto buscan recuperar su dinero y protección legal."
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
        "description": "Propietarios de viviendas dañadas por el terremoto buscando maximizar su reclamo de seguro."
    }
]


# ═══════════════════════════════════════════════════════════════
# NICHES_DB — Lista de dataclasses (NUEVO, para SEO Oracle)
# ═══════════════════════════════════════════════════════════════

NICHES_DB_ENRICHED: List[HighCPCNiche] = [_dict_to_highcpc(d) for d in NICHOS_DB]


# ═══════════════════════════════════════════════════════════════
# RadarReport — Legacy (backward compatible)
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# RADAR — Motor predictivo + SEO Oracle (unificado)
# ═══════════════════════════════════════════════════════════════

class Radar:
    """
    Motor de radar predictivo + SEO Oracle unificado.
    
    Métodos legacy (100% compatibles):
        __init__, _load_config, calcular_frr, escanear_nicho,
        escanear_todos, get_mejores_nichos, get_estadisticas_radar,
        proyectar_ingreso_diario, frr_por_nicho
    
    Nuevos métodos SEO Oracle:
        get_niche, rank_by_frr (desde dataclass), rank_by_profitability,
        get_confidence, calculate_yield_projection, create_content_plan,
        get_evergreen_multiplier, get_seo_stats, export_report,
        register_node, update_node_revenue,
        get_niches_by_category, get_top_niches
    """

    def __init__(self, config_path: str = "config/settings.json"):
        self.config = self._load_config(config_path)
        radar_cfg = self.config.get("radar", {})
        self.umbral_minimo = float(radar_cfg.get("umbral_frr_minimo", 150.0))
        self.cpc_minimo = float(radar_cfg.get("cpc_minimo", 80.0))
        self.historial_escaneos: List[RadarReport] = []
        self.nichos_activos: List[str] = []
        self._ultimo_escaneo = 0.0
        # SEO Oracle: nodos de contenido trackeados
        self.nodes: Dict[str, ContentNode] = {}

    def _load_config(self, path: str) -> Dict:
        default = {
            "radar": {
                "umbral_frr_minimo": 150.0, "intervalo_escaneo_horas": 2.0,
                "cpc_minimo": 80.0, "volumen_minimo": 500.0
            }
        }
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return default
        except:
            return default

    # ════════════════════════════════════════════════════════
    # MÉTODOS LEGACY (backward compatible)
    # ════════════════════════════════════════════════════════

    def calcular_frr(self, cpc: float, volumen: float, competencia: float) -> float:
        """
        FRR = (CPC * Volumen) / (Competencia + 1.0)
        Legacy — 100% compatible.
        """
        cpc_f = float(cpc)
        volumen_f = float(volumen)
        competencia_f = float(competencia)
        if cpc_f < 0.0 or volumen_f < 0.0 or competencia_f < 0.0:
            return 0.0
        if cpc_f < self.cpc_minimo:
            return 0.0
        if volumen_f < 500.0:
            return 0.0
        return round((cpc_f * volumen_f) / (competencia_f + 1.0), 4)

    def escanear_nicho(self, nicho: Dict) -> RadarReport:
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
        resultados = []
        for nicho in NICHOS_DB:
            reporte = self.escanear_nicho(nicho)
            resultados.append(reporte)
        self._ultimo_escaneo = time.time()
        return resultados

    def get_mejores_nichos(self, top_n: int = 3) -> List[RadarReport]:
        reportes = self.escanear_todos()
        aptos = [r for r in reportes if r.apto]
        aptos.sort(key=lambda r: r.frr, reverse=True)
        return aptos[:top_n]

    def get_estadisticas_radar(self) -> Dict:
        total = len(self.historial_escaneos)
        aptos = sum(1 for r in self.historial_escaneos if r.apto)
        frr_promedio = 0.0
        if aptos > 0:
            frr_promedio = sum(r.frr for r in self.historial_escaneos if r.apto) / aptos
        mejores = sorted(
            [r for r in self.historial_escaneos if r.apto],
            key=lambda r: r.frr, reverse=True
        )
        return {
            "total_escaneos": total, "nichos_aptos": aptos,
            "nichos_no_aptos": total - aptos,
            "frr_promedio_aptos": round(frr_promedio, 2),
            "umbral_actual": self.umbral_minimo,
            "ultimo_escaneo": datetime.fromtimestamp(self._ultimo_escaneo).strftime(
                "%Y-%m-%d %H:%M:%S"
            ) if self._ultimo_escaneo else "Nunca",
            "mejores_nichos": [
                {"nombre": r.nicho["name"], "frr": r.frr,
                 "cpc": r.nicho["cpc_avg"], "categoria": r.nicho["category"]}
                for r in mejores[:5]
            ],
            "timestamp": time.time()
        }

    def proyectar_ingreso_diario(
        self, posts_por_dia: int = 4, clicks_por_post: int = 50
    ) -> Dict:
        nichos_aptos = [r for r in self.historial_escaneos if r.apto]
        if not nichos_aptos:
            return {
                "ingreso_diario_promedio": 0.0, "ingreso_semanal": 0.0,
                "ingreso_mensual": 0.0, "ingreso_anual": 0.0,
                "posts_por_dia": 0,
                "mensaje": "No hay nichos aptos. Ajusta el umbral FRR."
            }
        nichos_aptos.sort(key=lambda r: r.frr, reverse=True)
        top = nichos_aptos[:min(posts_por_dia, len(nichos_aptos))]
        ingresos = [r.nicho["cpc_avg"] * clicks_por_post for r in top]
        total = sum(ingresos)
        return {
            "ingreso_diario_promedio": round(total, 2),
            "ingreso_diario_por_nicho": [
                {"nicho": r.nicho["name"], "cpc": r.nicho["cpc_avg"],
                 "clicks_estimados": clicks_por_post,
                 "ingreso_diario": round(r.nicho["cpc_avg"] * clicks_por_post, 2)}
                for r in top
            ],
            "ingreso_semanal": round(total * 7, 2),
            "ingreso_mensual": round(total * 30, 2),
            "ingreso_anual": round(total * 365, 2),
            "posts_por_dia": len(top), "clicks_por_post": clicks_por_post,
            "timestamp": time.time()
        }

    def frr_por_nicho(self, nicho_id: str) -> Optional[float]:
        nicho = next((n for n in NICHOS_DB if n["id"] == nicho_id), None)
        if not nicho:
            return None
        return self.calcular_frr(
            nicho["cpc_avg"], nicho["search_volume"], nicho["competencia"]
        )

    # ════════════════════════════════════════════════════════
    # NUEVOS MÉTODOS — SEO Oracle (Proyecto Infinito)
    # ════════════════════════════════════════════════════════

    # ─── Acceso a nichos enriquecidos ───

    @property
    def nichos_enriched(self) -> List[HighCPCNiche]:
        """Acceso a nichos como dataclasses."""
        return NICHES_DB_ENRICHED

    def get_niche(self, niche_id: str) -> Optional[HighCPCNiche]:
        """Obtiene un nicho como dataclass por su ID."""
        return next((n for n in NICHES_DB_ENRICHED if n.id == niche_id), None)

    def get_top_niches(self, min_cpc: Decimal = Decimal("80")) -> List[HighCPCNiche]:
        """Filtra nichos por CPC mínimo. ← Del SEO Oracle."""
        return [n for n in NICHES_DB_ENRICHED if n.cpc_avg >= min_cpc]

    def get_niches_by_category(self, category: str) -> List[HighCPCNiche]:
        """Filtra nichos por categoría. ← Del SEO Oracle."""
        return [n for n in NICHES_DB_ENRICHED if n.category == category]

    # ─── FRR Ranking (desde dataclass) ───

    def rank_by_frr(self, top_n: int = 5) -> List[Dict]:
        """
        Ranking por FRR desde dataclasses enriquecidas.
        Incluye profitability_score y datos cualitativos.
        """
        ranked = []
        for niche in NICHES_DB_ENRICHED:
            frr = niche.calcular_frr()
            ranked.append({
                "id": niche.id, "name": niche.name,
                "category": niche.category,
                "cpc_avg": float(niche.cpc_avg),
                "search_volume": niche.search_volume_numeric,
                "competencia": niche.competencia,
                "frr": frr, "apto": frr >= self.umbral_minimo,
                "profitability_score": float(niche.profitability_score),
                "difficulty": niche.difficulty.value,
                "evergreen": niche.evergreen_score,
            })
        ranked.sort(key=lambda x: x["frr"], reverse=True)
        return ranked[:top_n]

    # ─── Profitability Score ← del SEO Oracle ───

    def rank_by_profitability(self) -> List[Dict]:
        """
        Ranking por profitability score.
        Fórmula: CPC × demanda_score × evergreen
        ← Del SEO Oracle de Proyecto Infinito
        """
        ranked = []
        for niche in NICHES_DB_ENRICHED:
            ranked.append({
                "id": niche.id, "name": niche.name,
                "category": niche.category,
                "cpc_range": niche.cpc_range_str,
                "cpc_avg": float(niche.cpc_avg),
                "profitability_score": float(niche.profitability_score),
                "evergreen": niche.evergreen_score,
                "difficulty": niche.difficulty.value,
                "language": niche.language,
                "frr": niche.calcular_frr(),
            })
        ranked.sort(key=lambda x: x["profitability_score"], reverse=True)
        return ranked

    # ─── Confidence Score ← del SEO Oracle ───

    def get_confidence(self, niche: HighCPCNiche) -> ConfidenceLevel:
        """
        Calcula nivel de confianza basado en:
        evergreen_score (≥8 → +3), volumen (alto/muy_alto → +3),
        dificultad (media/baja → +2), intención (transaccional → +2)
        ← Del SEO Oracle de Proyecto Infinito
        """
        score = 0
        if niche.evergreen_score >= 8:
            score += 3
        if niche.search_volume in (SearchVolume.ALTO, SearchVolume.MUY_ALTO):
            score += 3
        if niche.difficulty in (TrafficDifficulty.MEDIA, TrafficDifficulty.BAJA):
            score += 2
        if niche.intent == SearchIntent.TRANSACCIONAL:
            score += 2
        if score >= 8:
            return ConfidenceLevel.MUY_ALTA
        elif score >= 6:
            return ConfidenceLevel.ALTA
        elif score >= 4:
            return ConfidenceLevel.MEDIA
        else:
            return ConfidenceLevel.BAJA

    # ─── Yield Projection ← del SEO Oracle (mejorado) ───

    def calculate_yield_projection(
        self,
        niche_id: str,
        monthly_visitors: int = 2000,
        ctr_pct: float = 2.0,
        nodes_count: int = 3,
    ) -> Optional[YieldProjection]:
        """
        Proyección de ingresos con rangos LOW/AVG/HIGH y confidence.
        ← Del SEO Oracle de Proyecto Infinito
        """
        niche = self.get_niche(niche_id)
        if not niche:
            return None
        visitors_total = monthly_visitors * nodes_count
        clicks = int(visitors_total * (ctr_pct / 100))
        rev_low = clicks * float(niche.cpc_min)
        rev_high = clicks * float(niche.cpc_max)
        rev_avg = clicks * float(niche.cpc_avg)
        conf = self.get_confidence(niche)
        return YieldProjection(
            niche_id=niche.id, niche_name=niche.name,
            nodes_count=nodes_count,
            monthly_visitors_total=visitors_total,
            ctr_pct=ctr_pct, clicks_monthly=clicks,
            cpc_range={"min": float(niche.cpc_min), "max": float(niche.cpc_max),
                        "avg": float(niche.cpc_avg)},
            monthly_revenue={"low": round(rev_low, 2), "avg": round(rev_avg, 2),
                             "high": round(rev_high, 2)},
            yearly_revenue={"low": round(rev_low * 12, 2), "avg": round(rev_avg * 12, 2),
                            "high": round(rev_high * 12, 2)},
            confidence=conf,
        )

    # ─── Content Plan ← del SEO Oracle ───

    def create_content_plan(self, selected_niches: List[str]) -> Dict:
        """
        Plan de contenido multi-nicho con proyecciones LOW/AVG/HIGH.
        ← Del SEO Oracle de Proyecto Infinito
        """
        plan = {
            "nodes": [],
            "total_monthly_revenue": {"low": 0.0, "avg": 0.0, "high": 0.0},
            "total_yearly_revenue": {"low": 0.0, "avg": 0.0, "high": 0.0},
            "total_monthly_visitors": 0, "total_clicks": 0,
            "confidence_promedio": "",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        confidences = []
        for niche_id in selected_niches:
            proj = self.calculate_yield_projection(
                niche_id=niche_id, monthly_visitors=2000, ctr_pct=2.0, nodes_count=3
            )
            if proj:
                p = proj.to_dict()
                plan["nodes"].append(p)
                for k in ["low", "avg", "high"]:
                    plan["total_monthly_revenue"][k] += p["monthly_revenue"][k]
                    plan["total_yearly_revenue"][k] += p["yearly_revenue"][k]
                plan["total_monthly_visitors"] += p["monthly_visitors_total"]
                plan["total_clicks"] += p["clicks_monthly"]
                confidences.append(p["confidence"])
        if confidences:
            order = ["baja", "media", "alta", "muy_alta"]
            scores = [order.index(c) + 1 for c in confidences]
            plan["confidence_promedio"] = order[
                min(int(sum(scores) / len(scores)), len(order) - 1)
            ]
        for key in ["total_monthly_revenue", "total_yearly_revenue"]:
            for sub in ["low", "avg", "high"]:
                plan[key][sub] = round(plan[key][sub], 2)
        return plan

    # ─── Evergreen Multiplier ← del SEO Oracle ───

    def get_evergreen_multiplier(self, years_active: int) -> float:
        """
        Multiplicador de ingresos para contenido evergreen.
        Asume 10% de caída anual por obsolescencia.
        ← Del SEO Oracle de Proyecto Infinito
        """
        decay = 0.9 ** years_active
        return round(1.0 + decay * (years_active - 1), 2)

    # ─── Proyección simple mejorada ───

    def proyectar_ingreso_diario_enriched(
        self, posts_por_dia: int = 4, clicks_por_post: int = 50
    ) -> Dict:
        """
        Proyección simple desde dataclasses (versión enriquecida).
        Incluye profitability_score y confidence.
        """
        aptos = [n for n in NICHES_DB_ENRICHED
                 if n.calcular_frr() >= self.umbral_minimo]
        if not aptos:
            return {"ingreso_diario_promedio": 0.0, "mensaje": "No hay nichos aptos."}
        aptos.sort(key=lambda n: n.calcular_frr(), reverse=True)
        top = aptos[:min(posts_por_dia, len(aptos))]
        ingresos = [float(n.cpc_avg) * clicks_por_post for n in top]
        total = sum(ingresos)
        return {
            "ingreso_diario_promedio": round(total, 2),
            "ingreso_diario_por_nicho": [
                {"nicho": n.name, "cpc": float(n.cpc_avg),
                 "frr": n.calcular_frr(),
                 "profitability": float(n.profitability_score),
                 "clicks_estimados": clicks_por_post,
                 "ingreso_diario": round(float(n.cpc_avg) * clicks_por_post, 2)}
                for n in top
            ],
            "ingreso_semanal": round(total * 7, 2),
            "ingreso_mensual": round(total * 30, 2),
            "ingreso_anual": round(total * 365, 2),
            "posts_por_dia": len(top), "clicks_por_post": clicks_por_post,
            "timestamp": time.time(),
        }

    # ─── Stats unificadas ───

    def get_seo_stats(self) -> Dict:
        """Estadísticas completas del Radar + SEO Oracle."""
        aptos = [n for n in NICHES_DB_ENRICHED
                 if n.calcular_frr() >= self.umbral_minimo]
        frr_prom = sum(n.calcular_frr() for n in aptos) / len(aptos) if aptos else 0.0
        categorias = {}
        for n in NICHES_DB_ENRICHED:
            cat = n.category
            if cat not in categorias:
                categorias[cat] = {"count": 0, "cpc_promedio": 0.0, "frr_promedio": 0.0}
            categorias[cat]["count"] += 1
            categorias[cat]["cpc_promedio"] += float(n.cpc_avg)
            categorias[cat]["frr_promedio"] += n.calcular_frr()
        for cat in categorias:
            c = categorias[cat]["count"]
            if c > 0:
                categorias[cat]["cpc_promedio"] = round(categorias[cat]["cpc_promedio"] / c, 2)
                categorias[cat]["frr_promedio"] = round(categorias[cat]["frr_promedio"] / c, 2)
        return {
            "total_nichos": len(NICHES_DB_ENRICHED),
            "nichos_aptos": len(aptos),
            "nichos_no_aptos": len(NICHES_DB_ENRICHED) - len(aptos),
            "frr_promedio_aptos": round(frr_prom, 2),
            "umbral_frr": self.umbral_minimo,
            "total_nodos_trackeados": len(self.nodes),
            "revenue_real_acumulado": round(
                sum(n.monthly_revenue_real for n in self.nodes.values()), 2
            ),
            "top_por_frr": self.rank_by_frr(top_n=5),
            "top_por_profitability": self.rank_by_profitability()[:5],
            "categorias": categorias,
            "timestamp": time.time(),
        }

    # ─── Export Report ← del SEO Oracle ───

    def export_report(self, filepath: str = "output/seo_oracle_report.json") -> Dict:
        """Exporta reporte completo a JSON. ← Del SEO Oracle."""
        data = {
            "reporte": "SEO Oracle — Shadow Del Valle R",
            "version": "2.0.0",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_nichos": len(NICHES_DB_ENRICHED),
            "niches": [n.to_dict() for n in NICHES_DB_ENRICHED],
            "ranking_frr": self.rank_by_frr(top_n=len(NICHES_DB_ENRICHED)),
            "ranking_profitability": self.rank_by_profitability(),
            "stats": self.get_seo_stats(),
            "nodos_trackeados": [n.to_dict() for n in self.nodes.values()],
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return {"success": True, "filepath": filepath}

    # ─── ContentNode tracking ← del SEO Oracle ───

    def register_node(
        self, niche_id: str, title: str, slug: str,
        target_keywords: List[str], source: str = "",
    ) -> Optional[str]:
        """Registra un nodo de contenido para tracking de revenue."""
        niche = self.get_niche(niche_id)
        if not niche:
            return None
        self.nodes[slug] = ContentNode(
            niche_id=niche_id, niche_name=niche.name, title=title, slug=slug,
            target_keywords=target_keywords,
            cpc_expected=float(niche.cpc_avg),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source=source,
        )
        return slug

    def update_node_revenue(
        self, slug: str, visitors: int = 0, revenue: float = 0.0
    ) -> bool:
        """Actualiza revenue real de un nodo (desde Monetag)."""
        if slug not in self.nodes:
            return False
        node = self.nodes[slug]
        if visitors:
            node.monthly_visitors = visitors
        if revenue:
            node.monthly_revenue_real = revenue
        node.monthly_revenue_est = node.estimate_revenue()
        return True


# ═══════════════════════════════════════════════════════════════
# DEMO / USO DIRECTO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    radar = Radar()

    print("=" * 65)
    print("  🌑 RADAR + SEO ORACLE v2.0 — Shadow Del Valle R")
    print("  Motor Unificado de Inteligencia de Nichos")
    print("=" * 65)

    # 1. Legacy scan (backward compatible)
    print("\n📡 ESCANEO LEGACY:")
    resultados = radar.escanear_todos()
    for r in sorted(resultados, key=lambda x: x.frr, reverse=True):
        est = "✅ APTO" if r.apto else "❌"
        print(f"  ${r.nicho['cpc_avg']:.0f} | FRR {r.frr:>8.0f} | {est:8} | {r.nicho['name'][:40]}")

    # 2. Full enriched scan
    print("\n🎯 ESCANEO ENRIQUECIDO (SEO Oracle):")
    print(f"{'Nicho':<42} {'CPC':>6} {'FRR':>10} {'Profit':>10} {'Conf':>8}")
    print("-" * 76)
    for niche in NICHES_DB_ENRICHED:
        frr = niche.calcular_frr()
        profit = float(niche.profitability_score)
        conf = radar.get_confidence(niche).value
        apto = "✅" if frr >= radar.umbral_minimo else "❌"
        print(f"  {niche.name:<40} ${float(niche.cpc_avg):>4.0f} {frr:>10.0f} {profit:>10.0f} {conf:>8} {apto:>4}")

    # 3. Rankings
    print("\n🏆 RANKING POR PROFITABILITY (Top 5):")
    for i, r in enumerate(radar.rank_by_profitability()[:5], 1):
        print(f"  {i}. {r['name'][:40]:<42} Score: {r['profitability_score']:>8.0f} | CPC: ${r['cpc_avg']:.0f}")

    # 4. Yield projection
    print("\n📈 PROYECCIÓN: Abogados de Accidentes")
    proy = radar.calculate_yield_projection(
        niche_id="personal-injury-law", monthly_visitors=5000, ctr_pct=2.0, nodes_count=5
    )
    if proy:
        p = proy.to_dict()
        print(f"   Visitantes/mes: {p['monthly_visitors_total']:,}")
        print(f"   Clicks/mes: {p['clicks_monthly']:,}")
        print(f"   Ingreso mensual: ${p['monthly_revenue']['avg']:,.2f} ", end="")
        print(f"(${p['monthly_revenue']['low']:,.2f} - ${p['monthly_revenue']['high']:,.2f})")
        print(f"   Confianza: {p['confidence']}")

    # 5. Content plan
    print("\n📋 PLAN DE CONTENIDO (Top 3):")
    plan = radar.create_content_plan(["personal-injury-law", "asset-recovery", "cybersecurity-compliance"])
    print(f"   Visitantes/mes: {plan['total_monthly_visitors']:,}")
    print(f"   Clicks/mes: {plan['total_clicks']:,}")
    print(f"   Ingreso mensual: ${plan['total_monthly_revenue']['avg']:,.2f} ", end="")
    print(f"(${plan['total_monthly_revenue']['low']:,.2f} - ${plan['total_monthly_revenue']['high']:,.2f})")
    print(f"   Confianza promedio: {plan['confidence_promedio']}")

    # 6. SEO stats
    print("\n📊 STATS SEO ORACLE:")
    stats = radar.get_seo_stats()
    print(f"   Total: {stats['total_nichos']} | Aptos: {stats['nichos_aptos']} | No aptos: {stats['nichos_no_aptos']}")
    print(f"   FRR promedio aptos: {stats['frr_promedio_aptos']:.2f}")
    print(f"   Categorías: {', '.join(stats['categorias'].keys())}")

    # 7. Evergreen
    print("\n🌿 MULTIPLICADOR EVERGREEN:")
    for y in [1, 2, 3, 5]:
        print(f"   Año {y}: {radar.get_evergreen_multiplier(y):.2f}x")

    # 8. Node tracking
    print("\n📌 CONTENT NODE TRACKING:")
    radar.register_node("personal-injury-law", "Test Post", "test-post", ["keyword1"], source="openrouter")
    radar.update_node_revenue("test-post", visitors=1000, revenue=50.0)
    print(f"   Nodo registrado: test-post | Visitantes: {radar.nodes['test-post'].monthly_visitors} | Revenue: ${radar.nodes['test-post'].monthly_revenue_real:.2f}")

    print(f"\n{'=' * 65}")
    print(f"  ✅ RADAR + SEO ORACLE v2.0 — Operacional")
    print(f"  {len(NICHOS_DB)} nichos · FRR + Profitability + Confidence + Yield")
    print(f"{'=' * 65}")

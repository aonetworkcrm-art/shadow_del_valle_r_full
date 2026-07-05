#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   SHADOW DEL VALLE R — ORÁCULO SÍSMICO MULTIFUENTE v2.0   ║
║   Vigilancia 24/7 · USGS · EMSC · NOAA Tsunami · GDACS     ║
║   PAGER Daños · Propagación · Predicción · WhatsApp Alert   ║
╚══════════════════════════════════════════════════════════════╝

Características:
  - Detección multi-fuente (USGS, EMSC, NOAA, GDACS)
  - Análisis de propagación de ondas sísmicas (vectores, clusters)
  - Predicción de dirección de movimiento sísmico
  - Datos PAGER (daños, víctimas, impacto económico)
  - Alertas WhatsApp con info de emergencia
  - Dashboard web y CLI

Uso:
    from core.oraculo import Oraculo
    oraculo = Oraculo()
    oraculo.escanear_ahora()           # Escaneo único
    oraculo.run()                       # Bucle infinito
    oraculo.get_estado()                # Estado actual
    oraculo.analizar_propagacion()      # Análisis de movimiento

Modo CLI:
    python core/oraculo.py --once       # Escaneo único
    python core/oraculo.py --daemon     # Bucle infinito
    python core/oraculo.py --status     # Estado del oráculo
"""

import json
import math
import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════
#  COLORES PARA CONSOLA
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN REGIONAL — Bounding Boxes para filtrado USGS
# ═══════════════════════════════════════════════════════════════

REGIONES = {
    "republica_dominicana": {
        "nombre": "República Dominicana",
        "emoji": "🇩🇴",
        "bbox": {"minlat": 17.0, "maxlat": 20.5, "minlon": -72.0, "maxlon": -68.0},
        "magnitud_minima": 2.5,
        "alerta_roja": 5.0
    },
    "venezuela": {
        "nombre": "Venezuela",
        "emoji": "🇻🇪",
        "bbox": {"minlat": 0.0, "maxlat": 12.5, "minlon": -73.0, "maxlon": -59.0},
        "magnitud_minima": 2.5,
        "alerta_roja": 5.0
    },
    "caribe": {
        "nombre": "Caribe",
        "emoji": "🌊",
        "bbox": {"minlat": 10.0, "maxlat": 25.0, "minlon": -85.0, "maxlon": -60.0},
        "magnitud_minima": 3.0,
        "alerta_roja": 5.5
    },
    "global": {
        "nombre": "Global (Significativos)",
        "emoji": "🌍",
        "bbox": None,
        "magnitud_minima": 4.5,
        "alerta_roja": 6.0
    }
}

# ─── URLs de APIs ───
USGS_FEEDS = {
    "hora": "https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/all_hour.geojson",
    "dia": "https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/all_day.geojson",
    "significativos": "https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/significant_day.geojson",
    "m2.5_hora": "https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/2.5_hour.geojson",
    "m2.5_dia": "https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/2.5_day.geojson",
    "m4.5_dia": "https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/4.5_day.geojson"
}

# ─── URLs de Fuentes Adicionales ───
NOAA_WEATHER_API = "https://api.weather.gov"
EMSC_API = "https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
GDACS_RSS = "https://www.gdacs.org/xml/rss.xml"
NOAA_USER_AGENT = "ShadowDelValleR-Oraculo/1.0 (shadowdelvalle.com, contact@shadowdelvalle.com)"

# ─── Constantes de Emergencia ───
EMERGENCIA_INFO = (
    "⚠️ *PROTOCOLO DE EMERGENCIA:*\n"
    "• Mantén la calma y busca una zona segura\n"
    "• Aléjate de ventanas, vidrios y objetos que puedan caer\n"
    "• Si estás en el interior: agáchate, cúbrete, sujétate\n"
    "• Si estás en el exterior: aléjate de edificios y postes\n"
    "• Ten tu teléfono con carga y datos móviles\n"
    "• Prepara linterna, agua, comida y botiquín\n"
    "• Revisa llave de gas y conexiones eléctricas\n"
    "• Ayuda a niños, adultos mayores y mascotas\n"
    "• Sigue las indicaciones de Defensa Civil/Protección Civil"
)


# ═══════════════════════════════════════════════════════════════
#  PROPAGATION ANALYZER — Análisis de movimiento sísmico
# ═══════════════════════════════════════════════════════════════

class PropagationAnalyzer:
    """
    Analiza patrones de propagación de ondas sísmicas.
    
    Detecta:
    - Clusters de eventos (swarms) en espacio-tiempo
    - Vectores de movimiento entre eventos consecutivos
    - Dirección general de propagación del swarm
    - Predicción de próxima ubicación probable
    
    Fórmulas:
    - Distancia Haversine entre dos puntos geográficos
    - Vector de movimiento: (Δlat, Δlon, Δtiempo, distancia_km, dirección)
    - Dirección: ángulo del rumbo (bearing) entre 0-360°
    """

    # Distancia máxima en km para considerar eventos como parte del mismo cluster
    CLUSTER_DISTANCIA_KM = 200
    # Tiempo máximo en horas entre eventos del mismo cluster
    CLUSTER_VENTANA_HORAS = 12
    # Magnitud mínima para análisis de propagación
    MAGNITUD_MINIMA = 3.0

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Distancia Haversine entre dos puntos en kilómetros."""
        R = 6371.0  # Radio de la Tierra en km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Ángulo del rumbo (bearing) entre dos puntos en grados (0-360)."""
        dlon = math.radians(lon2 - lon1)
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        x = math.sin(dlon) * math.cos(lat2_r)
        y = (math.cos(lat1_r) * math.sin(lat2_r) -
             math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon))
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    @staticmethod
    def bearing_name(bearing_deg: float) -> str:
        """Convierte grados a nombre de dirección cardinal."""
        direcciones = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        idx = round(bearing_deg / 22.5) % 16
        return direcciones[idx]

    def __init__(self):
        self.clusters: List[Dict] = []
        self.vectores: List[Dict] = []
        self.ultimo_analisis = None

    def analizar(self, eventos: List[Dict]) -> Dict:
        """
        Analiza una lista de eventos (dicts con lat, lon, tiempo_timestamp, magnitud).
        Retorna análisis completo de propagación.
        """
        if not eventos or len(eventos) < 2:
            return self._vacio()

        # Ordenar por tiempo
        sorted_events = sorted(eventos, key=lambda e: e.get("tiempo_timestamp", 0))

        # Filtrar por magnitud mínima
        significantes = [e for e in sorted_events if e.get("magnitud", 0) >= self.MAGNITUD_MINIMA]
        if len(significantes) < 2:
            return self._vacio()

        # 1. Detectar clusters
        clusters = self._detectar_clusters(significantes)
        self.clusters = clusters

        # 2. Calcular vectores de movimiento dentro de cada cluster
        vectores = []
        for cluster in clusters:
            eventos_cluster = cluster["eventos"]
            for i in range(1, len(eventos_cluster)):
                a = eventos_cluster[i - 1]
                b = eventos_cluster[i]
                vector = self._calcular_vector(a, b)
                if vector:
                    vectores.append(vector)
        self.vectores = vectores

        # 3. Determinar dirección general
        direccion_general = self._direccion_general(vectores)

        # 4. Predecir próxima ubicación
        prediccion = self._predecir_siguiente(significantes, vectores)

        resultado = {
            "total_eventos_analizados": len(significantes),
            "total_clusters": len(clusters),
            "total_vectores": len(vectores),
            "clusters": clusters[:3],
            "vectores": vectores[:5],
            "direccion_general": direccion_general,
            "prediccion": prediccion,
            "timestamp_analisis": datetime.now().isoformat()
        }
        self.ultimo_analisis = resultado
        return resultado

    def _vacio(self) -> Dict:
        return {
            "total_eventos_analizados": 0,
            "total_clusters": 0,
            "total_vectores": 0,
            "clusters": [],
            "vectores": [],
            "direccion_general": {"activa": False, "descripcion": "Datos insuficientes para análisis de propagación"},
            "prediccion": None
        }

    def _detectar_clusters(self, eventos: List[Dict]) -> List[Dict]:
        """Agrupa eventos en clusters por cercanía espacial y temporal."""
        clusters = []
        usados = set()

        for i, a in enumerate(eventos):
            if i in usados:
                continue
            cluster = {
                "centro_lat": a.get("lat", 0),
                "centro_lon": a.get("lon", 0),
                "eventos": [a],
                "magnitud_maxima": a.get("magnitud", 0),
                "tiempo_inicio": a.get("tiempo_timestamp", 0),
                "tiempo_fin": a.get("tiempo_timestamp", 0),
                "duracion_horas": 0,
                "area_km2": 0,
                "tipo": "swarm"
            }
            usados.add(i)
            t_inicio = a.get("tiempo_timestamp", 0)

            for j, b in enumerate(eventos):
                if j in usados or i == j:
                    continue
                dist = self.haversine_km(
                    a.get("lat", 0), a.get("lon", 0),
                    b.get("lat", 0), b.get("lon", 0)
                )
                diff_horas = abs(b.get("tiempo_timestamp", 0) - t_inicio) / 3600000

                if dist <= self.CLUSTER_DISTANCIA_KM and diff_horas <= self.CLUSTER_VENTANA_HORAS:
                    cluster["eventos"].append(b)
                    cluster["magnitud_maxima"] = max(cluster["magnitud_maxima"], b.get("magnitud", 0))
                    cluster["tiempo_inicio"] = min(cluster["tiempo_inicio"], b.get("tiempo_timestamp", 0))
                    cluster["tiempo_fin"] = max(cluster["tiempo_fin"], b.get("tiempo_timestamp", 0))
                    usados.add(j)

            # Calcular centroide y área
            if len(cluster["eventos"]) > 1:
                lats = [e.get("lat", 0) for e in cluster["eventos"]]
                lons = [e.get("lon", 0) for e in cluster["eventos"]]
                cluster["centro_lat"] = sum(lats) / len(lats)
                cluster["centro_lon"] = sum(lons) / len(lons)
                cluster["duracion_horas"] = (cluster["tiempo_fin"] - cluster["tiempo_inicio"]) / 3600000
                # Área aproximada: diámetro máximo del cluster
                max_dist = 0
                for e1 in cluster["eventos"]:
                    for e2 in cluster["eventos"]:
                        d = self.haversine_km(e1.get("lat", 0), e1.get("lon", 0),
                                              e2.get("lat", 0), e2.get("lon", 0))
                        max_dist = max(max_dist, d)
                cluster["area_km2"] = round(math.pi * (max_dist / 2) ** 2)
                cluster["tipo"] = "swarm" if len(cluster["eventos"]) >= 3 else "doble"

            clusters.append(cluster)

        # Ordenar por magnitud máxima descendente
        clusters.sort(key=lambda c: c["magnitud_maxima"], reverse=True)
        return clusters

    def _calcular_vector(self, a: Dict, b: Dict) -> Optional[Dict]:
        """Calcula vector de movimiento entre dos eventos."""
        try:
            lat1, lon1 = a.get("lat", 0), a.get("lon", 0)
            lat2, lon2 = b.get("lat", 0), b.get("lon", 0)
            t1 = a.get("tiempo_timestamp", 0)
            t2 = b.get("tiempo_timestamp", 0)

            dist_km = self.haversine_km(lat1, lon1, lat2, lon2)
            if dist_km < 1:
                return None  # Misma ubicación, ignorar

            bearing = self.bearing(lat1, lon1, lat2, lon2)
            dir_name = self.bearing_name(bearing)
            diff_horas = (t2 - t1) / 3600000 if t2 > t1 else 0.01
            velocidad_kmh = dist_km / diff_horas if diff_horas > 0 else 0

            return {
                "desde": {"lat": round(lat1, 4), "lon": round(lon1, 4), "lugar": a.get("lugar", "")},
                "hasta": {"lat": round(lat2, 4), "lon": round(lon2, 4), "lugar": b.get("lugar", "")},
                "distancia_km": round(dist_km, 1),
                "direccion_grados": round(bearing, 1),
                "direccion_nombre": dir_name,
                "delta_magnitud": round(b.get("magnitud", 0) - a.get("magnitud", 0), 1),
                "duracion_horas": round(diff_horas, 2),
                "velocidad_kmh": round(velocidad_kmh, 1),
                "magnitud_desde": a.get("magnitud", 0),
                "magnitud_hasta": b.get("magnitud", 0)
            }
        except Exception:
            return None

    def _direccion_general(self, vectores: List[Dict]) -> Dict:
        """Determina la dirección general de propagación del swarm."""
        if not vectores:
            return {"activa": False, "descripcion": "Sin vectores de movimiento detectados"}

        # Promedio de direcciones (usando trigonometría para promediar ángulos)
        x = sum(math.sin(math.radians(v["direccion_grados"])) for v in vectores)
        y = sum(math.cos(math.radians(v["direccion_grados"])) for v in vectores)
        bearing_promedio = (math.degrees(math.atan2(x / len(vectores), y / len(vectores))) + 360) % 360
        dir_nombre = self.bearing_name(bearing_promedio)

        distancia_total = sum(v["distancia_km"] for v in vectores)
        delta_mag_promedio = sum(v["delta_magnitud"] for v in vectores) / len(vectores)

        # Clasificar tendencia de magnitud
        if delta_mag_promedio > 0.3:
            tendencia = "AUMENTANDO ⬆️"
        elif delta_mag_promedio < -0.3:
            tendencia = "DISMINUYENDO ⬇️"
        else:
            tendencia = "ESTABLE ➡️"

        return {
            "activa": True,
            "direccion_promedio": round(bearing_promedio, 1),
            "direccion_nombre": dir_nombre,
            "distancia_total_km": round(distancia_total, 1),
            "delta_magnitud_promedio": round(delta_mag_promedio, 2),
            "tendencia_magnitud": tendencia,
            "total_vectores_analizados": len(vectores),
            "descripcion": (
                f"Propagación hacia el {dir_nombre} "
                f"({distancia_total:.0f} km recorridos en {len(vectores)} movimiento(s))"
            )
        }

    def _predecir_siguiente(self, eventos: List[Dict], vectores: List[Dict]) -> Optional[Dict]:
        """
        Predice la próxima ubicación probable basándose en:
        - Últimos 2-3 vectores de movimiento
        - Promedio de dirección y distancia
        """
        if len(vectores) < 1:
            return None

        # Usar los últimos 2 vectores (o menos si no hay suficientes)
        ultimos = vectores[-min(2, len(vectores)):]

        # Promedio de dirección y distancia
        dir_promedio = sum(v["direccion_grados"] for v in ultimos) / len(ultimos)
        dist_promedio = sum(v["distancia_km"] for v in ultimos) / len(ultimos)
        tiempo_promedio = sum(v["duracion_horas"] for v in ultimos) / len(ultimos)

        # Último evento conocido
        ultimo = eventos[-1]
        lat0, lon0 = ultimo.get("lat", 0), ultimo.get("lon", 0)

        # Proyectar siguiente punto: desde el último evento, avanzar en la dirección promedio
        # Fórmula: destino = punto + distancia * vector_unitario
        bearing_r = math.radians(dir_promedio)
        R = 6371.0
        dist_rad = dist_promedio / R

        lat_pred = math.degrees(math.asin(
            math.sin(math.radians(lat0)) * math.cos(dist_rad) +
            math.cos(math.radians(lat0)) * math.sin(dist_rad) * math.cos(bearing_r)
        ))
        lon_pred = math.degrees(math.radians(lon0) + math.atan2(
            math.sin(bearing_r) * math.sin(dist_rad) * math.cos(math.radians(lat0)),
            math.cos(dist_rad) - math.sin(math.radians(lat0)) * math.sin(math.radians(lat_pred))
        ))

        dir_nombre = self.bearing_name(dir_promedio)

        return {
            "lat_predicho": round(lat_pred, 4),
            "lon_predicho": round(lon_pred, 4),
            "distancia_estimada_km": round(dist_promedio, 1),
            "direccion": dir_nombre,
            "direccion_grados": round(dir_promedio, 1),
            "ventana_horas": round(tiempo_promedio, 1),
            "confianza": "ALTA" if len(vectores) >= 2 else "MEDIA",
            "basado_en_vectores": len(ultimos),
            "desde_ultimo_evento": ultimo.get("lugar", ""),
            "descripcion": (
                f"Próximo evento probable: ~{dist_promedio:.0f} km al {dir_nombre} "
                f"desde {ultimo.get('lugar', 'último evento')[:30]} "
                f"(en ~{tiempo_promedio:.1f}h)"
            )
        }


# ═══════════════════════════════════════════════════════════════
#  EVENTO SÍSMICO — Clase principal de un sismo detectado
# ═══════════════════════════════════════════════════════════════

class Evento:
    """Un evento sísmico detectado por el oráculo."""
    
    def __init__(self, data: Dict):
        props = data.get("properties", {})
        geo = data.get("geometry", {})
        coords = geo.get("coordinates", [0, 0, 0])
        
        self.id = data.get("id", str(uuid.uuid4()))
        self.magnitud = props.get("mag", 0)
        self.lugar = props.get("place", "Desconocido")
        # Manejar time: puede ser epoch ms (USGS) o string ISO (EMSC)
        raw_time = props.get("time", int(time.time() * 1000))
        if isinstance(raw_time, (int, float)):
            self.tiempo_ms = int(raw_time)
            self.tiempo = datetime.fromtimestamp(self.tiempo_ms / 1000, tz=timezone.utc)
        elif isinstance(raw_time, str):
            # ISO format from EMSC: "2026-06-26T11:34:00.0"
            try:
                self.tiempo = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                if self.tiempo.tzinfo is None:
                    self.tiempo = self.tiempo.replace(tzinfo=timezone.utc)
                self.tiempo_ms = int(self.tiempo.timestamp() * 1000)
            except:
                self.tiempo = datetime.now(timezone.utc)
                self.tiempo_ms = int(time.time() * 1000)
        else:
            self.tiempo_ms = int(time.time() * 1000)
            self.tiempo = datetime.now(timezone.utc)
        self.tiempo_str = self.tiempo.strftime("%Y-%m-%d %H:%M:%S UTC")
        self.url = props.get("url", "")
        self.detalle_url = props.get("detail", "")
        self.tipo = props.get("type", "earthquake")
        self.status = props.get("status", "")
        self.tsunami = props.get("tsunami", 0)
        self.sig = props.get("sig", 0)
        self.nst = props.get("nst", 0)
        self.dmin = props.get("dmin", 0)
        self.rms = props.get("rms", 0)
        self.gap = props.get("gap", 0)
        self.mag_type = props.get("magType", "")
        self.lon = coords[0]
        self.lat = coords[1]
        self.profundidad_km = coords[2]
        
        # ─── Datos PAGER (rellenados después) ───
        self.pager_data = None  # Dict con alertlevel, fatalities, etc.
        self.pager_cargado = False
        
        # ─── Severidad ───
        if self.magnitud >= 7.0:
            self.severidad = "CRÍTICO"
            self.color = Colors.RED
            self.emoji = "🔴🔴🔴"
        elif self.magnitud >= 6.0:
            self.severidad = "GRAVE"
            self.color = Colors.RED
            self.emoji = "🔴🔴"
        elif self.magnitud >= 5.0:
            self.severidad = "ALERTA"
            self.color = Colors.YELLOW
            self.emoji = "🟡🟡"
        elif self.magnitud >= 4.0:
            self.severidad = "MODERADO"
            self.color = Colors.YELLOW
            self.emoji = "🟡"
        elif self.magnitud >= 3.0:
            self.severidad = "LEVE"
            self.color = Colors.CYAN
            self.emoji = "🔵"
        else:
            self.severidad = "MENOR"
            self.color = Colors.DIM
            self.emoji = "⚪"

    def cargar_pager(self, timeout: int = 10) -> bool:
        """
        Carga datos PAGER desde la URL de detalle de USGS.
        Retorna True si se cargó exitosamente.
        """
        if self.pager_cargado:
            return self.pager_data is not None
        self.pager_cargado = True

        if not self.detalle_url:
            return False

        try:
            req = Request(self.detalle_url, headers={"User-Agent": "ShadowDelValleR-Oraculo/1.0"})
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            products = data.get("properties", {}).get("products", {})

            # Intentar losspager primero, luego pager
            for key in ["losspager", "pager"]:
                if key in products and products[key]:
                    pager = products[key][0]
                    p_props = pager.get("properties", {})

                    # Alert level
                    alertlevel = p_props.get("alertlevel", "")

                    # Fatalities
                    fatalities_min = p_props.get("fat-min", 0)
                    fatalities_max = p_props.get("fat-max", 0)
                    fatalities_avg = int((int(fatalities_min) + int(fatalities_max)) / 2) if fatalities_min and fatalities_max else None

                    # Injuries
                    injuries_min = p_props.get("inj-min", 0)
                    injuries_max = p_props.get("inj-max", 0)
                    injuries_avg = int((int(injuries_min) + int(injuries_max)) / 2) if injuries_min and injuries_max else None

                    # Damage (economic)
                    damage_min = float(p_props.get("loss-min", 0))
                    damage_max = float(p_props.get("loss-max", 0))
                    damage_millions = (damage_min + damage_max) / 2_000_000 if damage_min and damage_max else None

                    # Max MMI
                    maxmmi = p_props.get("maxmmi", None)
                    if maxmmi:
                        maxmmi = float(maxmmi)

                    # Alert score
                    alertscore = p_props.get("alertscore", None)
                    if alertscore:
                        alertscore = int(alertscore)

                    self.pager_data = {
                        "alertlevel": alertlevel or "",
                        "fatalities_min": int(fatalities_min) if fatalities_min else 0,
                        "fatalities_max": int(fatalities_max) if fatalities_max else 0,
                        "fatalities_promedio": fatalities_avg,
                        "injuries_min": int(injuries_min) if injuries_min else 0,
                        "injuries_max": int(injuries_max) if injuries_max else 0,
                        "injuries_promedio": injuries_avg,
                        "damage_min_usd": int(damage_min) if damage_min else 0,
                        "damage_max_usd": int(damage_max) if damage_max else 0,
                        "damage_millions": round(damage_millions, 2) if damage_millions else None,
                        "maxmmi": maxmmi,
                        "alertscore": alertscore,
                        "fuente": key
                    }
                    return True

            return False
        except Exception:
            return False

    def esta_en_region(self, bbox: Optional[Dict]) -> bool:
        """Verifica si el evento está dentro de un bounding box."""
        if bbox is None:
            return True
        return (bbox["minlat"] <= self.lat <= bbox["maxlat"] and
                bbox["minlon"] <= self.lon <= bbox["maxlon"])

    def a_dict(self) -> Dict:
        d = {
            "id": self.id,
            "magnitud": round(self.magnitud, 1),
            "lugar": self.lugar,
            "lat": round(self.lat, 4),
            "lon": round(self.lon, 4),
            "profundidad_km": round(self.profundidad_km, 1),
            "tiempo": self.tiempo_str,
            "tiempo_timestamp": self.tiempo_ms,
            "url": self.url,
            "detalle_url": self.detalle_url,
            "severidad": self.severidad,
            "tsunami": bool(self.tsunami),
            "sig": self.sig,
            "tipo": self.tipo,
            "mag_type": self.mag_type,
            "nst": self.nst,
            "gap": self.gap,
            "rms": self.rms
        }
        # Incluir PAGER si está cargado
        if self.pager_data:
            d["pager"] = self.pager_data
        return d

    def mensaje_whatsapp(self, propagacion: Optional[Dict] = None) -> str:
        """
        Genera mensaje para WhatsApp con:
        - Datos del sismo
        - Daños PAGER (si disponibles)
        - Análisis de propagación (si disponible)
        - Información de emergencia
        """
        ts = self.tiempo.strftime("%H:%M UTC")
        prof = f"{self.profundidad_km:.0f} km" if self.profundidad_km < 100 else f"{self.profundidad_km:.0f} km"
        
        # ─── Línea 1: Alerta ───
        alerta_tipo = "🌊 TSUNAMI" if self.tsunami else "🌍 TERREMOTO"
        lines = [
            f"⚠️ *{alerta_tipo} DETECTADO* {self.emoji}",
            f"M{self.magnitud:.1f} - {self.lugar[:50]}",
            f"📍 {self.lat:.2f}°, {self.lon:.2f}° | 📏 {prof}",
            f"🕐 {ts}",
        ]

        # ─── Línea: Tsunami ───
        if self.tsunami:
            lines.append("⚠️ *POSIBLE TSUNAMI!* Aléjate de la costa inmediatamente")

        # ─── Datos PAGER (daños) ───
        if self.pager_data:
            p = self.pager_data
            alertlevel = p.get("alertlevel", "")
            if alertlevel:
                al_emoji = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}.get(alertlevel.lower(), "⚪")
                lines.append(f"📊 PAGER: {al_emoji} Alerta {alertlevel.upper()}")

            if p.get("fatalities_promedio") and p["fatalities_promedio"] > 0:
                lines.append(f"💀 Víctimas fatales: ~{p['fatalities_promedio']:,}")
            if p.get("injuries_promedio") and p["injuries_promedio"] > 0:
                lines.append(f"🤕 Heridos: ~{p['injuries_promedio']:,}")
            if p.get("damage_millions") and p["damage_millions"] > 0:
                lines.append(f"💰 Daños económicos: ~${p['damage_millions']:.1f}M")
            if p.get("maxmmi"):
                lines.append(f"📐 Intensidad máxima MMI: {p['maxmmi']}")

        # ─── Análisis de Propagación ───
        if propagacion and propagacion.get("direccion_general", {}).get("activa"):
            dirg = propagacion["direccion_general"]
            lines.append(f"🌀 Propagación: {dirg['direccion_nombre']} ({dirg['distancia_total_km']:.0f}km)")

            if propagacion.get("prediccion"):
                pred = propagacion["prediccion"]
                lines.append(f"🔮 Predicción: {pred['descripcion'][:60]}")

        # ─── Información de Emergencia ───
        if self.magnitud >= 5.0:
            lines.append("")
            lines.append(EMERGENCIA_INFO)

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  ALERTA TSUNAMI — NOAA/NWS
# ═══════════════════════════════════════════════════════════════

class AlertaTsunami:
    """Alerta de tsunami desde NOAA/NWS."""
    
    def __init__(self, data: Dict):
        props = data.get("properties", {})
        self.id = data.get("id", str(uuid.uuid4()))
        self.titulo = props.get("headline", "Alerta de Tsunami")
        self.severidad = props.get("severity", "Unknown")
        self.certeza = props.get("certainty", "Unknown")
        self.urgencia = props.get("urgency", "Unknown")
        self.descripcion = props.get("description", "")[:200]
        self.area = props.get("areaDesc", "")
        self.instrucciones = props.get("instruction", "")[:200]
        self.tiempo = props.get("sent", datetime.now(timezone.utc).isoformat())
        self.evento = props.get("event", "")
        self.estatus = props.get("status", "Actual")
        
        if "warning" in self.evento.lower():
            self.emoji = "🔴🔴🔴"
        elif "watch" in self.evento.lower():
            self.emoji = "🟡🟡"
        elif "advisory" in self.evento.lower():
            self.emoji = "🟡"
        else:
            self.emoji = "🌊"
    
    def a_dict(self) -> Dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "evento": self.evento,
            "severidad": self.severidad,
            "certeza": self.certeza,
            "area": self.area[:100],
            "descripcion": self.descripcion,
            "instrucciones": self.instrucciones,
            "tiempo": self.tiempo,
            "emoji": self.emoji,
            "fuente": "NOAA/NWS"
        }
    
    def mensaje_whatsapp(self) -> str:
        return (
            f"🌊 *ALERTA DE TSUNAMI* {self.emoji}\n"
            f"{self.titulo[:80]}\n"
            f"📍 {self.area[:80]}\n"
            f"⚠️ {self.severidad} · {self.certeza}\n"
            f"🕐 {self.tiempo[:19]}\n\n"
            f"{EMERGENCIA_INFO}"
        )


# ═══════════════════════════════════════════════════════════════
#  ALERTA GDACS — UN/European Commission
# ═══════════════════════════════════════════════════════════════

class AlertaGDACS:
    """Alerta de desastre desde GDACS (UN + European Commission)."""
    
    def __init__(self, data: Dict):
        self.id = data.get("eventid", str(uuid.uuid4()))
        self.tipo = data.get("eventtype", "Desconocido")
        self.nombre = data.get("eventname", "Evento")[:80]
        self.severidad = data.get("severity", "Green")
        self.impacto = data.get("alertlevel", "")
        self.pais = data.get("country", "")
        self.lat = float(data.get("latitude", 0))
        self.lon = float(data.get("longitude", 0))
        self.fecha = data.get("fromdate", "")
        self.url = data.get("url", "")
        
        self.emoji_map = {"Red": "🔴🔴🔴", "Orange": "🟡🟡", "Green": "🟢", "": "⚪"}
        self.emoji = self.emoji_map.get(self.severidad, "⚪")
        self.tipo_nombre = {"EQ": "Terremoto", "TC": "Ciclón", "FL": "Inundación", "TS": "Tsunami", "VO": "Volcán"}.get(self.tipo, self.tipo)
    
    def a_dict(self) -> Dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "tipo_nombre": self.tipo_nombre,
            "nombre": self.nombre,
            "severidad": self.severidad,
            "impacto": self.impacto,
            "pais": self.pais[:60],
            "lat": round(self.lat, 4),
            "lon": round(self.lon, 4),
            "fecha": self.fecha[:19],
            "url": self.url,
            "emoji": self.emoji,
            "fuente": "GDACS (UN/EC)"
        }
    
    def mensaje_whatsapp(self) -> str:
        nivel = "CRITICO" if self.severidad == "Red" else ("ALERTA" if self.severidad == "Orange" else "INFO")
        return (
            f"🆘 *GDACS: {nivel} - {self.tipo_nombre}* {self.emoji}\n"
            f"{self.nombre[:70]}\n"
            f"📍 {self.pais[:50]}\n"
            f"⚠️ Severidad: {self.severidad}\n"
            f"🕐 {self.fecha[:16]}\n\n"
            f"{EMERGENCIA_INFO}"
        )


# ═══════════════════════════════════════════════════════════════
#  ORÁCULO SÍSMICO — Motor principal
# ═══════════════════════════════════════════════════════════════

class Oraculo:
    """
    El Oráculo v2.0 — Vigilante sísmico 24/7.
    
    Monitorea:
      - USGS Earthquake (4 regiones)
      - EMSC European-Mediterranean
      - NOAA/NWS Tsunami alerts
      - GDACS Global Disaster alerts
      - News RSS
    
    Analiza:
      - Propagación de ondas sísmicas (vectores, clusters, predicción)
      - Daños y víctimas (USGS PAGER)
    
    Notifica:
      - WhatsApp (CallMeBot)
      - Dashboard web (API)
    """
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.nombre = "Oráculo Sísmico Shadow Del Valle R"
        self.version = "2.0.0"
        self.config = self._load_config(config_path)
        self.eventos_conocidos: List[str] = []
        self.historial: List[Dict] = []
        self.ultimo_escaneo = 0
        self.escaneos_totales = 0
        self.eventos_detectados = 0
        self.notificaciones_enviadas = 0
        self.activo = True
        
        # Analizadores
        self.propagation = PropagationAnalyzer()
        self.ultima_propagacion: Optional[Dict] = None
        
        # Cargar estado previo
        self._cargar_estado()
    
    def _load_config(self, path: str) -> Dict:
        default = {
            "oraculo": {
                "intervalo_minutos": 5,
                "magnitud_minima": 2.5,
                "habilitado": True,
                "regiones_activas": ["republica_dominicana", "venezuela", "caribe", "global"]
            },
            "whatsapp": {
                "habilitado": False,
                "phone": "",
                "apikey": "",
                "api_url": "https://api.callmebot.com/whatsapp.php"
            },
            "telegram": {
                "habilitado": False,
                "bot_token": "",
                "chat_id": ""
            }
        }
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    for key in default:
                        if key not in cfg:
                            cfg[key] = default[key]
                        elif isinstance(default[key], dict):
                            for subkey in default[key]:
                                if subkey not in cfg.get(key, {}):
                                    cfg.setdefault(key, {})[subkey] = default[key][subkey]
                    return cfg
            return default
        except:
            return default
    
    def _get_state_path(self) -> str:
        return os.path.join("output", "oraculo_state.json")
    
    def _cargar_estado(self):
        path = self._get_state_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self.eventos_conocidos = state.get("eventos_conocidos", [])
                self.escaneos_totales = state.get("escaneos_totales", 0)
                self.eventos_detectados = state.get("eventos_detectados", 0)
                self.notificaciones_enviadas = state.get("notificaciones_enviadas", 0)
                self.ultima_propagacion = state.get("ultima_propagacion")
        except:
            pass
    
    def _guardar_estado(self):
        path = self._get_state_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "eventos_conocidos": self.eventos_conocidos[-500:],
                    "escaneos_totales": self.escaneos_totales,
                    "eventos_detectados": self.eventos_detectados,
                    "notificaciones_enviadas": self.notificaciones_enviadas,
                    "ultimo_escaneo": self.ultimo_escaneo,
                    "ultima_fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ultima_propagacion": self.ultima_propagacion
                }, f, indent=2)
        except:
            pass
    
    def _fetch_json(self, url: str, timeout: int = 15, headers: Optional[Dict] = None) -> Optional[Dict]:
        """Fetch JSON desde una URL con timeout."""
        all_headers = {"User-Agent": "ShadowDelValleR-Oraculo/1.0"}
        if headers:
            all_headers.update(headers)
        try:
            req = Request(url, headers=all_headers)
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except URLError as e:
            print(f"     ⚠️ Error fetching {url[:60]}: {e.reason}")
            return None
        except Exception as e:
            print(f"     ⚠️ Error fetching {url[:60]}: {str(e)[:60]}")
            return None
    
    def _fetch_usgs_region(self, region_key: str, horas: int = 6) -> List[Evento]:
        """Obtiene sismos de USGS para una región específica."""
        region = REGIONES.get(region_key)
        if not region:
            return []
        
        bbox = region["bbox"]
        mag_min = region["magnitud_minima"]
        
        if bbox is None:
            url = USGS_FEEDS["significativos"]
        else:
            start = (datetime.now(timezone.utc) - timedelta(hours=horas)).strftime("%Y-%m-%dT%H:%M:%S")
            url = (f"https://earthquake.usgs.gov/fdsnws/event/1/query"
                   f"?format=geojson"
                   f"&minlatitude={bbox['minlat']}"
                   f"&maxlatitude={bbox['maxlat']}"
                   f"&minlongitude={bbox['minlon']}"
                   f"&maxlongitude={bbox['maxlon']}"
                   f"&minmagnitude={mag_min}"
                   f"&starttime={start}"
                   f"&orderby=magnitude")
        
        data = self._fetch_json(url)
        if not data:
            return []
        
        eventos = []
        for f in data.get("features", []):
            evento = Evento(f)
            if evento.id not in self.eventos_conocidos:
                eventos.append(evento)
        
        return eventos
    
    def _fetch_pager(self, evento: Evento) -> bool:
        """Carga datos PAGER para un evento."""
        if not evento.detalle_url or evento.magnitud < 4.5:
            return False
        return evento.cargar_pager()
    
    def _fetch_news(self, region_key: str) -> List[Dict]:
        """Busca breaking news de sismos/desastres para la región."""
        region = REGIONES.get(region_key)
        if not region:
            return []
        
        nombre = region["nombre"]
        noticias = []
        
        rss_urls = [
            f"https://news.google.com/rss/search?q=earthquake+{nombre.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en",
            f"https://news.google.com/rss/search?q=terremoto+{nombre.replace(' ', '+')}&hl=es-ES&gl=ES&ceid=ES:es",
            f"https://news.google.com/rss/search?q=sismo+{nombre.replace(' ', '+')}&hl=es-ES&gl=ES&ceid=ES:es"
        ]
        
        for url in rss_urls:
            try:
                req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                with urlopen(req, timeout=8) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    titles = re.findall(r"<title[^>]*>([^<]+)</title>", html)
                    links = re.findall(r"<link[^>]*>([^<]+)</link>", html)
                    
                    for i, titulo in enumerate(titles[:5]):
                        if i == 0:
                            continue
                        link = links[i] if i < len(links) else ""
                        if "&url=" in link:
                            link = link.split("&url=")[-1].split("&")[0]
                            link = unquote(link)
                        
                        noticias.append({
                            "titulo": titulo,
                            "url": link,
                            "fuente": "Google News",
                            "region": region_key,
                            "timestamp": time.time()
                        })
                    break
            except:
                continue
        
        # También consultar USGS
        try:
            if region["bbox"]:
                b = region["bbox"]
                url = (f"https://earthquake.usgs.gov/fdsnws/event/1/query"
                       f"?format=geojson"
                       f"&minlatitude={b['minlat']}&maxlatitude={b['maxlat']}"
                       f"&minlongitude={b['minlon']}&maxlongitude={b['maxlon']}"
                       f"&minmagnitude=4.0&limit=3&orderby=magnitude")
                data = self._fetch_json(url)
                if data and data.get("features"):
                    for f in data["features"]:
                        p = f.get("properties", {})
                        noticias.append({
                            "titulo": f"M{p.get('mag', '?')} - {p.get('place', 'Desconocido')}",
                            "url": p.get("url", ""),
                            "fuente": "USGS",
                            "region": region_key,
                            "timestamp": p.get("time", 0) / 1000
                        })
        except:
            pass
        
        return noticias
    
    def _fetch_noaa_tsunami(self) -> List[AlertaTsunami]:
        """Obtiene alertas de tsunami desde NOAA/NWS API."""
        alertas = []
        try:
            url = f"{NOAA_WEATHER_API}/alerts/active?event=Tsunami&limit=10"
            req = Request(url, headers={
                "User-Agent": NOAA_USER_AGENT,
                "Accept": "application/geo+json"
            })
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for f in data.get("features", []):
                    alertas.append(AlertaTsunami(f))
        except:
            pass
        return alertas
    
    def _fetch_gdacs(self, max_eventos: int = 10) -> List[AlertaGDACS]:
        """Obtiene alertas de desastres desde GDACS vía RSS feed."""
        alertas = []
        try:
            req = Request(GDACS_RSS, headers={"User-Agent": "ShadowDelValleR-Oraculo/1.0"})
            with urlopen(req, timeout=10) as resp:
                xml_data = resp.read().decode("utf-8", errors="ignore")
            
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            
            for item in items[:max_eventos]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")
                pubdate = item.findtext("pubDate", "")
                
                # Extraer tipo de evento del título o categoría
                eventtype = "Desastre"
                if "earthquake" in title.lower() or "EQ" in title:
                    eventtype = "EQ"
                elif "tsunami" in title.lower() or "TS" in title:
                    eventtype = "TS"
                elif "tropical cyclone" in title.lower() or "TC" in title or "huracán" in title.lower() or "tormenta" in title.lower():
                    eventtype = "TC"
                elif "flood" in title.lower() or "FL" in title:
                    eventtype = "FL"
                elif "volcano" in title.lower() or "VO" in title:
                    eventtype = "VO"
                
                # Severidad por palabras clave en el título
                severity = "Green"
                if any(w in title.lower() for w in ["red", "critical", "extreme"]):
                    severity = "Red"
                elif any(w in title.lower() for w in ["orange", "severe", "major"]):
                    severity = "Orange"
                elif any(w in title.lower() for w in ["yellow", "moderate"]):
                    severity = "Yellow"
                
                alertas.append(AlertaGDACS({
                    "eventid": f"rss-{len(alertas)}",
                    "eventtype": eventtype,
                    "eventname": title[:80],
                    "severity": severity,
                    "country": desc[:60] if desc else "",
                    "fromdate": pubdate[:19],
                    "url": link
                }))
        except Exception as ex:
            print(f"     ⚠️ GDACS: {str(ex)[:60]}")
        return alertas
    
    def _fetch_emsc(self, horas: int = 24) -> List[Evento]:
        """Obtiene eventos sísmicos desde EMSC (European-Mediterranean Seismological Centre)."""
        start = (datetime.now(timezone.utc) - timedelta(hours=horas)).strftime("%Y-%m-%dT%H:%M:%S")
        # URL-encode el starttime para evitar caracteres problemáticos
        start_encoded = quote(start, safe="")
        url = f"{EMSC_API}&minmagnitude=3.0&starttime={start_encoded}&orderby=magnitude&limit=20"
        
        data = self._fetch_json(url)
        if not data:
            return []
        
        eventos = []
        for f in data.get("features", []):
            evento = Evento(f)
            if evento.id not in self.eventos_conocidos:
                evento.fuente = "EMSC"
                eventos.append(evento)
        return eventos
    
    def enviar_whatsapp(self, mensaje: str) -> bool:
        """Envía mensaje vía WhatsApp usando CallMeBot API."""
        cfg = self.config.get("whatsapp", {})
        if not cfg.get("habilitado"):
            return False
        
        phone = cfg.get("phone", "")
        apikey = cfg.get("apikey", "")
        api_url = cfg.get("api_url", "https://api.callmebot.com/whatsapp.php")
        
        if not phone or not apikey:
            return False
        
        try:
            params = urlencode({"phone": phone, "text": mensaje, "apikey": apikey})
            url = f"{api_url}?{params}"
            
            req = Request(url, headers={"User-Agent": "ShadowDelValleR-Oraculo/1.0"})
            with urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    self.notificaciones_enviadas += 1
                    return True
                return False
        except Exception as e:
            print(f"     ❌ Error WhatsApp: {str(e)[:80]}")
            return False
    
    def _enviar_whatsapp_alerta(self, alerta) -> bool:
        """Envía alerta vía WhatsApp (wrapper genérico)."""
        if hasattr(alerta, "mensaje_whatsapp"):
            return self.enviar_whatsapp(alerta.mensaje_whatsapp())
        return False
    
    def analizar_propagacion(self) -> Dict:
        """
        Ejecuta análisis de propagación sobre el historial de eventos.
        """
        if not self.historial or len(self.historial) < 2:
            result = self.propagation._vacio()
            self.ultima_propagacion = result
            return result
        
        # Eventos de las últimas 48 horas para análisis
        ahora = time.time() * 1000
        recientes = [e for e in self.historial if e.get("tiempo_timestamp", 0) > ahora - (48 * 3600 * 1000)]
        
        if len(recientes) < 2:
            result = self.propagation._vacio()
            self.ultima_propagacion = result
            return result
        
        result = self.propagation.analizar(recientes)
        self.ultima_propagacion = result
        return result
    
    def escanear_region(self, region_key: str) -> List[Evento]:
        """Escanea una región específica y retorna eventos NUEVOS."""
        region = REGIONES.get(region_key)
        if not region:
            return []
        
        print(f"  {region['emoji']} {c(region['nombre'], Colors.CYAN)} (M≥{region['magnitud_minima']})...", end=" ")
        
        eventos = self._fetch_usgs_region(region_key)
        
        if not eventos:
            print(c("✅ Sin novedades", Colors.DIM))
            return []
        
        nuevos = [e for e in eventos if e.id not in self.eventos_conocidos]
        
        if not nuevos:
            print(c(f"✅ {len(eventos)} conocidos, sin nuevos", Colors.DIM))
            return []
        
        print(c(f"⚠️ {len(nuevos)} NUEVO(S)!", Colors.YELLOW, bold=True))
        
        for e in nuevos:
            self.eventos_conocidos.append(e.id)
            self.eventos_detectados += 1
            
            # Cargar datos PAGER para eventos significativos
            if e.magnitud >= 4.5:
                self._fetch_pager(e)
            
            self.historial.append(e.a_dict())
            
            # Mostrar en consola
            print(f"     {e.emoji} {c(f'M{e.magnitud:.1f}', e.color, bold=True)} | {e.lugar[:60]}")
            print(f"       📍 {e.lat:.2f}°, {e.lon:.2f}° | 📏 {e.profundidad_km:.0f} km | 🕐 {e.tiempo.strftime('%H:%M:%S')}")
            
            # Mostrar PAGER si está disponible
            if e.pager_data:
                p = e.pager_data
                if p.get("alertlevel"):
                    print(f"       📊 PAGER: {p['alertlevel'].upper()} | Víctimas: ~{p.get('fatalities_promedio', 'N/A')} | Daños: ${p.get('damage_millions', 'N/A')}M")
            
            # Enviar notificación WhatsApp
            if e.magnitud >= 4.0:
                # Obtener propagación para incluir en el mensaje
                propagacion = None
                if len(self.historial) >= 2:
                    propagacion = self.ultima_propagacion
                
                mensaje = e.mensaje_whatsapp(propagacion=propagacion)
                ok = self.enviar_whatsapp(mensaje)
                if ok:
                    print(f"       {c('📱 WhatsApp alerta enviada (con PAGER + propagación)', Colors.GREEN)}")
                elif self.config.get("whatsapp", {}).get("habilitado"):
                    print(f"       {c('📱 WhatsApp no configurado', Colors.DIM)}")
        
        return nuevos
    
    def escanear_ahora(self) -> Dict:
        """Ejecuta un escaneo completo de TODAS las fuentes."""
        self.escaneos_totales += 1
        self.ultimo_escaneo = time.time()
        
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{c('═' * 62, Colors.CYAN, bold=True)}")
        print(f"  🌍 {c('ORÁCULO MULTIFUENTE v2.0 — Escaneo #' + str(self.escaneos_totales), Colors.CYAN, bold=True)}")
        print(f"  {c(ahora + ' UTC', Colors.DIM)}")
        print(c('═' * 62, Colors.CYAN, bold=True))
        
        regiones_activas = self.config.get("oraculo", {}).get("regiones_activas", 
            ["republica_dominicana", "venezuela", "caribe", "global"])
        
        total_nuevos = 0
        resultados = {}
        todos_eventos = []
        
        # ─── 1. USGS Earthquake ───
        print(f"\n  {c('📡 FUENTE: USGS Earthquake + PAGER', Colors.YELLOW, bold=True)}")
        for rk in regiones_activas:
            nuevos = self.escanear_region(rk)
            resultados[rk] = [e.a_dict() for e in nuevos]
            total_nuevos += len(nuevos)
            todos_eventos.extend([e.a_dict() for e in nuevos])
        
        # ─── 2. EMSC ───
        print(f"\n  {c('🌍 FUENTE: EMSC (EU-Med)', Colors.YELLOW, bold=True)}")
        try:
            emsc_eventos = self._fetch_emsc(horas=24)
            if emsc_eventos:
                for e in emsc_eventos[:5]:
                    self.eventos_conocidos.append(e.id)
                    self.eventos_detectados += 1
                    if e.magnitud >= 4.5:
                        self._fetch_pager(e)
                    dic = e.a_dict()
                    self.historial.append(dic)
                    todos_eventos.append(dic)
                    print(f"     {e.emoji} M{e.magnitud:.1f} | {e.lugar[:60]} | {e.tiempo.strftime('%H:%M UTC')}")
                    total_nuevos += 1
                print(f"     {c(f'✅ {len(emsc_eventos)} eventos EMSC', Colors.GREEN)}")
            else:
                print(f"     {c('✅ Sin novedades EMSC', Colors.DIM)}")
        except Exception as ex:
            print(f"     ⚠️ EMSC error: {str(ex)[:60]}")
        
        # ─── 3. NOAA Tsunami ───
        print(f"\n  {c('🌊 FUENTE: NOAA Tsunami', Colors.YELLOW, bold=True)}", end=" ")
        try:
            tsunami_alerts = self._fetch_noaa_tsunami()
            if tsunami_alerts:
                for ta in tsunami_alerts:
                    print(f"\n     {ta.emoji} {c(ta.evento, Colors.RED, bold=True)} | {ta.area[:60]}")
                    print(f"       {c('⚠️ ' + ta.severidad + ' · ' + ta.certeza, Colors.YELLOW)}")
                    self._enviar_whatsapp_alerta(ta)
                resultados["tsunami"] = [ta.a_dict() for ta in tsunami_alerts]
                print(f"\n     {c(f'⚠️ {len(tsunami_alerts)} alerta(s) de tsunami!', Colors.RED, bold=True)}")
            else:
                print(c(f"✅ Sin alertas de tsunami", Colors.DIM))
        except Exception as ex:
            print(c(f"⚠️ Error: {str(ex)[:60]}", Colors.YELLOW))
        
        # ─── 4. GDACS ───
        print(f"\n  {c('🆘 FUENTE: GDACS (UN/EU)', Colors.YELLOW, bold=True)}")
        try:
            gdacs_alerts = self._fetch_gdacs(max_eventos=5)
            if gdacs_alerts:
                for ga in gdacs_alerts:
                    print(f"     {ga.emoji} {ga.tipo_nombre} | {ga.nombre[:50]} | {ga.pais[:30]}")
                    if "Red" in ga.severidad or "Orange" in ga.severidad:
                        print(f"       {c(f'⚠️ Severidad: {ga.severidad}', Colors.RED)}")
                resultados["gdacs"] = [ga.a_dict() for ga in gdacs_alerts]
            else:
                print(f"     {c('✅ Sin alertas GDACS', Colors.DIM)}")
        except Exception as ex:
            print(f"     ⚠️ GDACS error: {str(ex)[:60]}")
        
        # ─── 5. Análisis de Propagación ───
        print(f"\n  {c('🌀 ANÁLISIS DE PROPAGACIÓN', Colors.YELLOW, bold=True)}")
        try:
            propagacion = self.analizar_propagacion()
            if propagacion["total_eventos_analizados"] >= 2:
                if propagacion["direccion_general"].get("activa"):
                    dirg = propagacion["direccion_general"]
                    print(f"     📐 Dirección general: {c(dirg['direccion_nombre'], Colors.CYAN, bold=True)} ({dirg['distancia_total_km']:.0f} km)")
                    print(f"     📊 Tendencia magnitud: {dirg['tendencia_magnitud']}")
                    if propagacion.get("prediccion"):
                        pred = propagacion["prediccion"]
                        print(f"     🔮 Predicción: {pred['descripcion'][:70]}")
                    if propagacion["total_clusters"] > 0:
                        print(f"     🌀 {propagacion['total_clusters']} cluster(s) sísmicos detectados")
                else:
                    print(f"     {c('✅ Sin patrones de propagación activos', Colors.DIM)}")
            else:
                print(f"     {c('✅ Datos insuficientes para análisis', Colors.DIM)}")
        except Exception as ex:
            print(f"     ⚠️ Propagación: {str(ex)[:60]}")
        
        # Guardar estado
        self._guardar_estado()
        
        # ─── Resumen Final ───
        print(f"\n{c('═' * 62, Colors.CYAN, bold=True)}")
        print(f"  {c('📊 RESUMEN', Colors.YELLOW, bold=True)}")
        print(f"  Escaneo #{self.escaneos_totales} · {ahora}")
        
        if total_nuevos > 0:
            print(f"  {c(f'⚠️ {total_nuevos} nuevo(s) evento(s) detectado(s)!', Colors.YELLOW, bold=True)}")
            if self.config.get("whatsapp", {}).get("habilitado"):
                print(f"  {c('📱 WhatsApp: ALERTAS ENVIADAS con PAGER + propagación', Colors.GREEN, bold=True)}")
        else:
            print(f"  {c('✅ Todo tranquilo. Ningún evento nuevo.', Colors.GREEN)}")
        
        if self.ultima_propagacion and self.ultima_propagacion["direccion_general"].get("activa"):
            dirg = self.ultima_propagacion["direccion_general"]
            print(f"  🌀 Propagación activa: {dirg['descripcion'][:50]}")
        
        print(f"  Eventos en seguimiento: {c(str(len(self.eventos_conocidos)), Colors.CYAN)}")
        print(f"  Fuentes: USGS + EMSC + NOAA + GDACS + PAGER + Propagación")
        print(c('═' * 62, Colors.CYAN, bold=True))
        print()
        
        return {
            "timestamp": ahora,
            "escaneo": self.escaneos_totales,
            "total_nuevos": total_nuevos,
            "resultados": resultados,
            "eventos_conocidos": len(self.eventos_conocidos),
            "notificaciones_enviadas": self.notificaciones_enviadas,
            "propagacion": self.ultima_propagacion
        }
    
    def get_estado(self) -> Dict:
        """Retorna el estado actual del oráculo."""
        cfg_oraculo = self.config.get("oraculo", {})
        cfg_whatsapp = self.config.get("whatsapp", {})
        
        ultimos_por_region = {}
        if self.historial:
            for e in reversed(self.historial[-30:]):
                for rk, reg in REGIONES.items():
                    if e["magnitud"] >= reg["magnitud_minima"]:
                        if reg["bbox"] is None or (reg["bbox"]["minlat"] <= e["lat"] <= reg["bbox"]["maxlat"] and
                                                   reg["bbox"]["minlon"] <= e["lon"] <= reg["bbox"]["maxlon"]):
                            if rk not in ultimos_por_region:
                                ultimos_por_region[rk] = e
        
        return {
            "nombre": self.nombre,
            "version": self.version,
            "activo": cfg_oraculo.get("habilitado", True),
            "intervalo_minutos": cfg_oraculo.get("intervalo_minutos", 5),
            "whatsapp_activo": cfg_whatsapp.get("habilitado", False),
            "whatsapp_phone": cfg_whatsapp.get("phone", "")[-4:] if cfg_whatsapp.get("phone") else "",
            "estadisticas": {
                "escaneos_totales": self.escaneos_totales,
                "eventos_detectados": self.eventos_detectados,
                "notificaciones_enviadas": self.notificaciones_enviadas,
                "eventos_en_seguimiento": len(self.eventos_conocidos),
                "ultimo_escaneo": datetime.fromtimestamp(self.ultimo_escaneo).strftime("%Y-%m-%d %H:%M:%S") if self.ultimo_escaneo else "Nunca"
            },
            "regiones_activas": [
                {
                    "key": rk,
                    "nombre": REGIONES[rk]["nombre"],
                    "emoji": REGIONES[rk]["emoji"],
                    "magnitud_minima": REGIONES[rk]["magnitud_minima"],
                    "ultimo_evento": ultimos_por_region.get(rk)
                }
                for rk in cfg_oraculo.get("regiones_activas", [])
            ],
            "ultimos_eventos": self.historial[-10:] if self.historial else [],
            "propagacion": self.ultima_propagacion if self.ultima_propagacion else None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def run(self):
        """Bucle principal del oráculo."""
        intervalo = self.config.get("oraculo", {}).get("intervalo_minutos", 5)
        print(f"\n  {c('🌍 ORÁCULO SÍSMICO v2.0 ACTIVADO', Colors.CYAN, bold=True)}")
        print(f"  {c(f'Escaneando cada {intervalo} minuto(s)', Colors.DIM)}")
        print(f"  {c('Presiona Ctrl+C para detener', Colors.DIM)}")
        
        while self.activo:
            try:
                self.escanear_ahora()
                
                if not self.activo:
                    break
                
                for _ in range(intervalo * 60):
                    if not self.activo:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n  {c(f'❌ Error: {str(e)[:100]}', Colors.RED)}")
                time.sleep(60)
        
        print(f"\n  {c('👋 Oráculo detenido.', Colors.CYAN)}")
    
    def mostrar_dashboard(self):
        """Muestra dashboard del oráculo en consola."""
        estado = self.get_estado()
        
        print(f"\n{c('═' * 60, Colors.CYAN, bold=True)}")
        print(c('  🌍 ORÁCULO SÍSMICO v2.0 — DASHBOARD EN VIVO', Colors.CYAN, bold=True))
        print(c('═' * 60, Colors.CYAN, bold=True))
        
        est = estado["estadisticas"]
        print(f"\n  {c('📊 ESTADÍSTICAS', Colors.YELLOW, bold=True)}")
        print(f"  Escaneos:       {c(str(est['escaneos_totales']), Colors.GREEN)}")
        print(f"  Eventos detect: {c(str(est['eventos_detectados']), Colors.YELLOW)}")
        print(f"  Notificaciones: {c(str(est['notificaciones_enviadas']), Colors.GREEN)}")
        print(f"  En seguimiento: {c(str(est['eventos_en_seguimiento']), Colors.CYAN)}")
        print(f"  Último escaneo: {est['ultimo_escaneo']}")
        print(f"  WhatsApp:       {c('✅ Activo' if estado['whatsapp_activo'] else '❌ Inactivo', Colors.GREEN if estado['whatsapp_activo'] else Colors.RED)}")
        
        print(f"\n  {c('📍 REGIONES VIGILADAS', Colors.YELLOW, bold=True)}")
        for r in estado["regiones_activas"]:
            ultimo = r.get("ultimo_evento")
            ultimo_str = f"M{ultimo['magnitud']:.1f} - {ultimo['lugar'][:40]}" if ultimo else "Sin datos"
            print(f"  {r['emoji']} {r['nombre']:<25} M≥{r['magnitud_minima']}  {c(ultimo_str, Colors.DIM)}")
        
        # Sección de Propagación
        if estado.get("propagacion") and estado["propagacion"]["direccion_general"].get("activa"):
            prop = estado["propagacion"]
            print(f"\n  {c('🌀 PROPAGACIÓN ACTIVA', Colors.YELLOW, bold=True)}")
            dirg = prop["direccion_general"]
            print(f"  Dirección: {c(dirg['direccion_nombre'], Colors.CYAN, bold=True)} ({dirg['descripcion'][:40]})")
            print(f"  Distancia total: {dirg['distancia_total_km']:.0f} km | Vectores: {dirg['total_vectores_analizados']}")
            print(f"  Tendencia: {dirg['tendencia_magnitud']}")
            if prop.get("prediccion"):
                pred = prop["prediccion"]
                print(f"  🔮 {pred['descripcion'][:60]} (confianza: {pred['confianza']})")
        
        if estado["ultimos_eventos"]:
            print(f"\n  {c('⚠️ ÚLTIMOS EVENTOS', Colors.YELLOW, bold=True)}")
            for e in estado["ultimos_eventos"][:5]:
                pager_str = ""
                if "pager" in e:
                    p = e["pager"]
                    if p.get("alertlevel"):
                        pager_str = f" [PAGER: {p['alertlevel'].upper()}]"
                print(f"  M{e['magnitud']:.1f} | {e['lugar'][:50]} | {e['tiempo']}{pager_str}")
        
        print(c('═' * 60, Colors.CYAN, bold=True))
        print()


# ═══════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🌍 Shadow Del Valle R — Oráculo Sísmico v2.0")
    parser.add_argument("--once", action="store_true", help="Ejecutar un escaneo único")
    parser.add_argument("--daemon", action="store_true", help="Modo bucle infinito")
    parser.add_argument("--status", action="store_true", help="Mostrar estado actual")
    
    args = parser.parse_args()
    
    oraculo = Oraculo()
    
    if args.status:
        oraculo.mostrar_dashboard()
    elif args.once:
        oraculo.escanear_ahora()
    elif args.daemon:
        oraculo.run()
    else:
        oraculo.mostrar_dashboard()
        print(f"  {c('[1]', Colors.GREEN)} Escanear ahora")
        print(f"  {c('[2]', Colors.GREEN)} Iniciar monitoreo continuo")
        print(f"  {c('[0]', Colors.RED)} Salir")
        choice = input(f"\n  {c('>', Colors.GREEN)} Opción: ").strip()
        if choice == "1":
            oraculo.escanear_ahora()
        elif choice == "2":
            oraculo.run()

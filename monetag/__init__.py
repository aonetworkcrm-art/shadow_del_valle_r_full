"""
Shadow Del Valle R — Monetag Revenue Optimization Module
=========================================================
Sistema completo de optimización de ingresos via Monetag SSP API v5.

Módulos:
    api_client.py       — Cliente SSP API v5 con Bearer Token auth
    revenue_tracker.py  — Tracking de revenue en tiempo real + Ledger
    optimizer.py        — Motor de optimización inteligente (A/B, geo, schedule)
    alert_engine.py     — Alertas por RPM bajo, picos de tráfico
    dashboard_api.py    — Endpoints Flask para dashboard web
"""

__version__ = "1.0.0"
__author__ = "Shadow Del Valle R"

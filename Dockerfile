# ═══════════════════════════════════════════════════════════════
# Dockerfile — Shadow Del Valle R Monetag Dashboard
# ═══════════════════════════════════════════════════════════════
# Usado por: Render (render.yaml), Railway (railway.json),
#            Google Cloud Run, AWS ECS, cualquier Docker host
#
# Build:
#   docker build -t shadow-dashboard -f Dockerfile .
#
# Run:
#   docker run -p 5000:5000 -e MONETAG_API_TOKEN=tu_token shadow-dashboard
# ═══════════════════════════════════════════════════════════════

FROM python:3.11-slim

# ── Evitar writes innecesarios ──
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ── Directorio de trabajo ──
WORKDIR /app

# ── Copiar dependencias primero (cache layer) ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copiar el proyecto ──
COPY . .

# ── Puerto ──
EXPOSE 5000

# ── Healthcheck ──
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# ── Arranque ──
# Usa gunicorn en producción, flask run en desarrollo
CMD gunicorn dashboard.api:app \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info}

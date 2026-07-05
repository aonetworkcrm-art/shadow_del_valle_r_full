#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# deploy-dashboard.sh — Shadow Del Valle R Monetag Dashboard
# ═══════════════════════════════════════════════════════════════
# Script unificado para desplegar el dashboard Flask a:
#   • Render    (--render)
#   • Railway   (--railway)
#   • Docker    (--docker)
#   • Local     (--local)
#
# Uso:
#   ./deploy-dashboard.sh --render          # Deploy a Render
#   ./deploy-dashboard.sh --railway         # Deploy a Railway  
#   ./deploy-dashboard.sh --docker          # Build + run Docker
#   ./deploy-dashboard.sh --local           # Arrancar localmente
#   ./deploy-dashboard.sh --help            # Ver ayuda
# ═══════════════════════════════════════════════════════════════

set -euo pipefail
cd "$(dirname "$0")"

# ─── Colores ───
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; DIM='\033[2m'; NC='\033[0m'
c() { echo -e "${2}${1}${NC}"; }
step() { echo -e "  ${CYAN}→${NC} ${1}"; }
ok()   { echo -e "  ${GREEN}✅${NC} ${1}"; }
warn() { echo -e "  ${YELLOW}⚠️${NC} ${1}"; }
fail() { echo -e "  ${RED}❌${NC} ${1}"; }

# ─── Banner ───
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   🌑  Shadow Del Valle R — Deploy Dashboard       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Help ───
if [[ "${1:-}" == "--help" ]]; then
    echo "  Uso: ./deploy-dashboard.sh [OPCIÓN]"
    echo ""
    echo "  Opciones:"
    echo "    --render        Deploy a Render usando render.yaml"
    echo "    --railway       Deploy a Railway usando railway.json"
    echo "    --docker        Build imagen Docker y arrancar contenedor"
    echo "    --local         Arrancar dashboard localmente"
    echo "    --help          Mostrar esta ayuda"
    echo ""
    echo "  Variables de entorno requeridas:"
    echo "    MONETAG_API_TOKEN   Token de API de Monetag"
    echo ""
    echo "  Opcionales:"
    echo "    WA_PHONE            Teléfono WhatsApp"
    echo "    WA_APIKEY           API Key de CallMeBot"
    echo "    PORT                Puerto (default: 5000)"
    echo ""
    exit 0
fi

# ─── Validar token ───
if [[ -z "${MONETAG_API_TOKEN:-}" ]]; then
    warn "MONETAG_API_TOKEN no configurado"
    echo "     El dashboard arrancará pero la API de Monetag no estará disponible."
    echo "     Para configurarlo: export MONETAG_API_TOKEN='tu_token_aqui'"
    echo ""
fi

MODE="${1:---local}"

# ═══════════════════════════════════════════════════════════
# 🏠  LOCAL
# ═══════════════════════════════════════════════════════════
if [[ "$MODE" == "--local" ]]; then
    step "Arrancando dashboard localmente..."
    
    # Verificar Flask
    if ! python -c "import flask" 2>/dev/null; then
        step "Instalando dependencias..."
        pip install -r requirements.txt
    fi
    
    PORT="${PORT:-5000}"
    echo ""
    echo -e "  ${CYAN}📊 Dashboard:${NC}  http://localhost:${PORT}"
    echo -e "  ${DIM}   Health:${NC}     http://localhost:${PORT}/health"
    echo -e "  ${DIM}   Ctrl+C para detener${NC}"
    echo ""
    
    python dashboard/api.py --port "${PORT}"

# ═══════════════════════════════════════════════════════════
# 🐳  DOCKER
# ═══════════════════════════════════════════════════════════
elif [[ "$MODE" == "--docker" ]]; then
    IMAGE="shadow-dashboard:latest"
    PORT="${PORT:-5000}"
    
    step "Construyendo imagen Docker..."
    docker build -t "${IMAGE}" -f Dockerfile .
    ok "Imagen ${IMAGE} creada"
    
    echo ""
    step "Arrancando contenedor..."
    echo -e "  ${CYAN}📊 Dashboard:${NC}  http://localhost:${PORT}"
    echo ""
    
    docker run --rm \
        -p "${PORT}:5000" \
        -e MONETAG_API_TOKEN="${MONETAG_API_TOKEN:-}" \
        -e WA_PHONE="${WA_PHONE:-}" \
        -e WA_APIKEY="${WA_APIKEY:-}" \
        -e PORT=5000 \
        "${IMAGE}"

# ═══════════════════════════════════════════════════════════
# 🎯  RENDER
# ═══════════════════════════════════════════════════════════
elif [[ "$MODE" == "--render" ]]; then
    # Verificar Render CLI
    if ! command -v render &>/dev/null; then
        fail "Render CLI no instalado"
        echo "     Instálalo: npm install -g @renderinc/cli"
        echo "     O deploy manualmente desde: https://dashboard.render.com"
        echo ""
        echo "     Pasos manuales:"
        echo "     1. Sube el proyecto a GitHub"
        echo "     2. Ve a https://dashboard.render.com/blueprint"
        echo "     3. Conecta tu repositorio"
        echo "     4. Render detectará render.yaml automáticamente"
        exit 1
    fi
    
    step "Desplegando a Render via Blueprint..."
    render blueprint launch --file render.yaml
    ok "Deploy iniciado en Render"

# ═══════════════════════════════════════════════════════════
# 🚂  RAILWAY
# ═══════════════════════════════════════════════════════════
elif [[ "$MODE" == "--railway" ]]; then
    # Verificar Railway CLI
    if ! command -v railway &>/dev/null; then
        fail "Railway CLI no instalado"
        echo "     Instálalo: npm install -g @railway/cli"
        echo "     O deploy manualmente desde: https://railway.app/dashboard"
        echo ""
        echo "     Pasos manuales:"
        echo "     1. Sube el proyecto a GitHub"
        echo "     2. Ve a https://railway.app/new"
        echo "     3. Conecta tu repositorio"
        echo "     4. Railway detectará railway.json automáticamente"
        exit 1
    fi
    
    step "Desplegando a Railway..."
    railway up --service shadow-del-valle-r-dashboard
    ok "Deploy iniciado en Railway"

else
    fail "Opción desconocida: ${MODE}"
    echo "  Usa --help para ver las opciones disponibles."
    exit 1
fi

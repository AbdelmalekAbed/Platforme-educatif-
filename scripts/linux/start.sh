#!/usr/bin/env bash
# ========================================
# EdTech Platform - Démarrage Complet
# Fusionne: start_app, fix_and_restart
# ========================================
# Usage:
#   bash scripts/linux/start.sh           # Démarrage normal
#   bash scripts/linux/start.sh --clean   # Tue les processus existants puis démarre
# ========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

CLEAN_START=false
[[ "${1:-}" == "--clean" ]] && CLEAN_START=true

cd "$PROJECT_ROOT"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║    EdTech Platform - Démarrage         ║"
echo "╚════════════════════════════════════════╝"
echo ""

# ── Mode --clean: kill existing processes + free ports ───────────────────
if [[ "$CLEAN_START" == true ]]; then
    echo -e "${CYAN}Nettoyage des processus existants...${NC}"
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "node" 2>/dev/null || true
    sudo fuser -k 8000/tcp 2>/dev/null || true
    sudo fuser -k 3000/tcp 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ Processus et ports libérés${NC}"
    echo ""
fi

# ── PostgreSQL ────────────────────────────────────────────────────────────
echo -e "${CYAN}Vérification de PostgreSQL...${NC}"
if command -v systemctl &>/dev/null && systemctl list-unit-files 2>/dev/null | grep -q postgresql; then
    sudo systemctl start postgresql 2>/dev/null || true
elif command -v service &>/dev/null; then
    sudo service postgresql start 2>/dev/null || true
fi
echo -e "${GREEN}✅ PostgreSQL prêt${NC}"
echo ""

# ── Backend ───────────────────────────────────────────────────────────────
echo -e "${CYAN}Démarrage du Backend (port 8000)...${NC}"
(
    cd backend
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!
sleep 2
echo -e "${GREEN}✅ Backend lancé (PID: $BACKEND_PID)${NC}"
echo ""

# ── Frontend ─────────────────────────────────────────────────────────────
echo -e "${CYAN}Démarrage du Frontend (port 3000)...${NC}"
(
    cd frontend
    npm run dev
) &
FRONTEND_PID=$!
sleep 2
echo -e "${GREEN}✅ Frontend lancé (PID: $FRONTEND_PID)${NC}"
echo ""

echo "╔════════════════════════════════════════╗"
echo "║   ✅ APPLICATION DÉMARRÉE!             ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo -e "🌐 Accès:"
echo -e "   Frontend : ${CYAN}http://localhost:3000${NC}"
echo -e "   API      : ${CYAN}http://localhost:8000${NC}"
echo -e "   Docs     : ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo -e "🔑 Login admin:"
echo -e "   Email    : admin@edtech.com"
echo -e "   Password : Admin123456"
echo ""
echo -e "📊 Processus:"
echo -e "   Backend  : PID $BACKEND_PID"
echo -e "   Frontend : PID $FRONTEND_PID"
echo ""
echo -e "❌ Pour arrêter : ${RED}Ctrl+C${NC}"
echo ""

# Keep running until user interrupts
trap "echo ''; echo 'Arrêt...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" INT TERM
wait

#!/usr/bin/env bash
# ========================================
# EdTech Platform - Setup Linux / WSL
# Fusionne: setup_wsl, setup-new-pc, fix_wsl_complete, run_all
# ========================================
# Usage:
#   bash scripts/linux/setup.sh           # Setup seul
#   bash scripts/linux/setup.sh --start   # Setup + lancement automatique
# ========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

DB_NAME="${DB_NAME:-edtech}"
DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

RUN_AFTER_SETUP=false
[[ "${1:-}" == "--start" ]] && RUN_AFTER_SETUP=true

# Colors
c_blue="\033[1;34m"; c_green="\033[1;32m"; c_yellow="\033[1;33m"
c_red="\033[1;31m"; c_reset="\033[0m"

step() { echo -e "\n${c_blue}==>${c_reset} $1"; }
ok()   { echo -e "    ${c_green}✓${c_reset} $1"; }
warn() { echo -e "    ${c_yellow}!${c_reset} $1"; }
fail() { echo -e "    ${c_red}✗${c_reset} $1"; exit 1; }

cd "$PROJECT_ROOT"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   EdTech Platform - Setup Linux/WSL   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# ── Warn if running from a Windows mount (slow I/O in WSL) ──────────────
case "$PROJECT_ROOT" in
  /mnt/c/*|/mnt/d/*|/mnt/e/*)
    warn "Le projet est sur $PROJECT_ROOT."
    warn "Sur WSL c'est ~10× plus lent que dans ~/projects/. Sur Ubuntu natif, c'est OK."
    read -r -p "    Continuer quand même ? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || fail "Déplacez le projet dans ~/projects/ et relancez."
    ;;
esac

# ── [1/5] System prerequisites ─────────────────────────────────────────────
step "[1/5] Vérification et installation des prérequis système"

# Python3
if ! command -v python3 &>/dev/null; then
    warn "python3 manquant — installation en cours..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv
fi
ok "python3 : $(python3 --version)"

# PostgreSQL
if ! command -v psql &>/dev/null; then
    warn "psql manquant — installation en cours..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq postgresql postgresql-contrib libpq-dev
fi
ok "PostgreSQL : $(psql --version)"

# Node.js >= 18 (résout aussi les conflits de packages)
NODE_REQUIRED=18
NEED_NODE=false

if ! command -v node &>/dev/null; then
    warn "node manquant"
    NEED_NODE=true
else
    NODE_MAJOR=$(node -v | sed 's/v\([0-9]*\).*/\1/')
    if [[ "$NODE_MAJOR" -lt "$NODE_REQUIRED" ]]; then
        warn "Node.js $NODE_MAJOR détecté, version $NODE_REQUIRED+ requise — mise à jour..."
        NEED_NODE=true
    fi
fi

if [[ "$NEED_NODE" == true ]]; then
    warn "Suppression des packages Node conflictuels..."
    sudo apt-get remove -y nodejs libnode-dev npm 2>/dev/null || true
    sudo apt-get autoremove -y 2>/dev/null || true
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_REQUIRED}.x" | sudo -E bash - 2>&1 | grep -v "^$" || true
    sudo apt-get install -y nodejs
fi

ok "Node.js : $(node --version)"
ok "npm     : $(npm --version)"

# ── [2/5] PostgreSQL service + database ────────────────────────────────────
step "[2/5] PostgreSQL — service et base de données"

if command -v systemctl &>/dev/null && systemctl list-unit-files 2>/dev/null | grep -q postgresql; then
    sudo systemctl start postgresql 2>/dev/null || true
    sudo systemctl enable postgresql &>/dev/null || true
    ok "Service postgresql démarré (systemd)"
elif command -v service &>/dev/null; then
    sudo service postgresql start 2>/dev/null || true
    ok "Service postgresql démarré (service)"
else
    warn "Aucun gestionnaire de services détecté — vérifiez que PostgreSQL tourne sur $DB_HOST:$DB_PORT"
fi

# Configure user password
if ! PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c '\q' &>/dev/null; then
    warn "Configuration du mot de passe pour '$DB_USER'..."
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null \
        || sudo -u postgres psql -c "CREATE USER $DB_USER WITH SUPERUSER PASSWORD '$DB_PASS';"
fi
ok "Utilisateur '$DB_USER' configuré"

# Create database if missing
if ! PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt 2>/dev/null \
        | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    PGPASSWORD="$DB_PASS" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    ok "Base '$DB_NAME' créée"
else
    ok "Base '$DB_NAME' déjà présente"
fi

# ── [3/5] Backend ───────────────────────────────────────────────────────────
step "[3/5] Backend — venv, dépendances, .env, migrations, admin"

cd "$BACKEND_DIR"

# Remove Windows-incompatible venv if present
if [[ -d venv ]] && [[ ! -f venv/bin/activate ]]; then
    warn "venv incompatible (créé sous Windows?) — suppression..."
    rm -rf venv
fi

if [[ ! -d venv ]]; then
    python3 -m venv venv
    ok "venv créé"
else
    ok "venv déjà présent"
fi

# shellcheck source=/dev/null
source venv/bin/activate

# Find requirements file
REQ=""
for f in requirements/dev.txt requirements/base.txt requirements.txt; do
    [[ -f "$f" ]] && { REQ="$f"; break; }
done
[[ -n "$REQ" ]] || fail "Aucun fichier requirements trouvé dans backend/"

pip install --upgrade pip -q
pip install -r "$REQ"
ok "Dépendances Python installées depuis $REQ"

# Generate .env if missing
if [[ ! -f .env ]]; then
    cat > .env <<EOF
# EdTech Platform — généré par setup.sh
APP_NAME=EdTech Platform
DEBUG=True
SECRET_KEY=change-me-in-production-use-long-random-secret-key
ALLOWED_ORIGINS=["http://localhost:3000"]

DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DATABASE_URL_SYNC=postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}

REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=change-me-jwt-secret-key-make-it-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF
    ok ".env créé  ⚠️  Changez les SECRET_KEY avant la production"
else
    ok ".env déjà présent"
fi

# Migrations
if [[ -f alembic.ini ]]; then
    alembic upgrade head
    ok "Migrations Alembic appliquées"
fi

# Seed admin
python "$PROJECT_ROOT/scripts/db/seed_admin.py" \
    && ok "Compte admin vérifié" \
    || warn "Admin déjà présent ou erreur lors du seed (ignorée)"

deactivate

# ── [4/5] Frontend ──────────────────────────────────────────────────────────
step "[4/5] Frontend — npm install"

cd "$FRONTEND_DIR"

if [[ -d node_modules ]]; then
    ok "node_modules déjà présent (npm ci pour réinstaller proprement)"
else
    npm install 2>&1 | tail -5
    ok "Dépendances Node installées"
fi

# ── [5/5] Summary ───────────────────────────────────────────────────────────
step "[5/5] Setup terminé ✅"

echo ""
echo -e "${c_green}Tout est prêt !${c_reset}"
echo ""

if [[ "$RUN_AFTER_SETUP" == true ]]; then
    echo "Lancement de l'application automatiquement..."
    bash "$SCRIPT_DIR/start.sh"
else
    cat <<EOF
Pour lancer la stack, ouvrez deux terminaux :

  # Terminal 1 — backend
  cd $BACKEND_DIR
  source venv/bin/activate
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Terminal 2 — frontend
  cd $FRONTEND_DIR
  npm run dev

Puis ouvrez http://localhost:3000

Login admin : admin@edtech.com / Admin123456

Ou tout d'un coup :
  bash scripts/linux/setup.sh --start
  bash scripts/linux/start.sh
EOF
fi

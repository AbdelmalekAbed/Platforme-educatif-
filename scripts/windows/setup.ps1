# ========================================
# EdTech Platform - Setup Windows (PowerShell)
# Fusionne: check_requirements, setup_local.ps1, run_create_admin
# ========================================
# Usage: .\scripts\windows\setup.ps1

$ErrorActionPreference = "Stop"

# Resolve project root (scripts/windows -> scripts -> project root)
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " EdTech Platform - Setup Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── [1/4] Prerequisites ────────────────────────────────────────────────────
Write-Host "[1/4] Verification des prerequis..." -ForegroundColor Yellow
Write-Host ""

$ok = $true

try {
    $v = python --version 2>&1
    Write-Host "OK  $v" -ForegroundColor Green
} catch {
    Write-Host "x   Python: NON TROUVE" -ForegroundColor Red
    Write-Host "    Solution: https://www.python.org  (cocher 'Add Python to PATH')" -ForegroundColor Gray
    $ok = $false
}

try {
    $v = psql --version 2>&1
    Write-Host "OK  $v" -ForegroundColor Green
} catch {
    Write-Host "x   PostgreSQL: NON TROUVE" -ForegroundColor Red
    Write-Host "    Solution: https://www.postgresql.org/download/" -ForegroundColor Gray
    Write-Host "    Ajouter au PATH: C:\Program Files\PostgreSQL\[VERSION]\bin" -ForegroundColor Gray
    $ok = $false
}

try {
    $v = node --version 2>&1
    Write-Host "OK  Node.js $v" -ForegroundColor Green
} catch {
    Write-Host "!   Node.js: non trouve (optionnel pour le frontend)" -ForegroundColor Yellow
}

if (-not $ok) {
    Write-Host "`n❌ Prerequis manquants. Installez-les puis relancez." -ForegroundColor Red
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}

if (-not (Test-Path "backend")) {
    Write-Host "❌ Dossier backend introuvable. Lancez depuis la racine du projet." -ForegroundColor Red
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}

# ── [2/4] Backend ──────────────────────────────────────────────────────────
Write-Host "`n[2/4] Backend - venv + dependances + migrations..." -ForegroundColor Yellow
Write-Host ""

Set-Location "backend"

if (-not (Test-Path "venv")) {
    Write-Host "Creation de l'environnement virtuel..." -ForegroundColor Gray
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Creation venv echouee" -ForegroundColor Red
        Read-Host "Appuyez sur Entree pour quitter"; exit 1
    }
    Write-Host "OK  venv cree" -ForegroundColor Green
} else {
    Write-Host "OK  venv existant" -ForegroundColor Green
}

& ".\venv\Scripts\Activate.ps1"

Write-Host "Installation des dependances..." -ForegroundColor Gray
pip install -q -r requirements/base.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Installation des dependances echouee" -ForegroundColor Red
    Read-Host "Appuyez sur Entree pour quitter"; exit 1
}
Write-Host "OK  Dependances installees" -ForegroundColor Green

Write-Host "Application des migrations..." -ForegroundColor Gray
alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Migrations echouees. Verifiez PostgreSQL + base 'edtech'." -ForegroundColor Red
    Read-Host "Appuyez sur Entree pour quitter"; exit 1
}
Write-Host "OK  Migrations appliquees" -ForegroundColor Green

Set-Location $ProjectRoot

# ── [3/4] Frontend ─────────────────────────────────────────────────────────
Write-Host "`n[3/4] Frontend - npm install..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "frontend") {
    Set-Location "frontend"
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installation des dependances Node..." -ForegroundColor Gray
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "!   npm install echoue (ignore)" -ForegroundColor Yellow
        } else {
            Write-Host "OK  Dependances Node installees" -ForegroundColor Green
        }
    } else {
        Write-Host "OK  node_modules existant" -ForegroundColor Green
    }
    Set-Location $ProjectRoot
} else {
    Write-Host "!   Dossier frontend introuvable - ignore" -ForegroundColor Yellow
}

# ── [4/4] Admin seed ───────────────────────────────────────────────────────
Write-Host "`n[4/4] Creation du compte admin..." -ForegroundColor Yellow
Write-Host ""

python scripts\db\seed_admin.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "!   Admin deja present ou erreur (ignoree)" -ForegroundColor Yellow
}

# ── Summary ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines etapes:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Terminal 1 - Backend:" -ForegroundColor White
Write-Host "    cd backend" -ForegroundColor Gray
Write-Host "    .\venv\Scripts\Activate" -ForegroundColor Gray
Write-Host "    uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "  Terminal 2 - Frontend:" -ForegroundColor White
Write-Host "    cd frontend" -ForegroundColor Gray
Write-Host "    npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "  Acces:" -ForegroundColor White
Write-Host "    Frontend : http://localhost:3000" -ForegroundColor Gray
Write-Host "    API Docs : http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "  Login admin:" -ForegroundColor White
Write-Host "    Email    : admin@edtech.com" -ForegroundColor Gray
Write-Host "    Password : Admin123456" -ForegroundColor Gray
Write-Host ""

Read-Host "Appuyez sur Entree pour quitter"

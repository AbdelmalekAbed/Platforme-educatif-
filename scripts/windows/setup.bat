@echo off
REM ========================================
REM EdTech Platform - Setup Windows Complet
REM Fusionne: check_requirements, setup_local, run_create_admin
REM ========================================
setlocal enabledelayedexpansion
cls

echo.
echo ========================================
echo  EdTech Platform - Setup Windows
echo ========================================
echo.

REM ---------- PHASE 1: Verification des prerequis ----------
echo [1/4] Verification des prerequis...
echo.

set ALL_OK=1

python --version >nul 2>&1
if errorlevel 1 (
    echo x  Python: NON TROUVE
    echo    Solution: https://www.python.org  ^(cocher "Add Python to PATH"^)
    set ALL_OK=0
) else (
    for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
    echo OK !PY_VER!
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo x  pip: NON TROUVE
    set ALL_OK=0
) else (
    echo OK pip trouve
)

psql --version >nul 2>&1
if errorlevel 1 (
    echo x  PostgreSQL: NON TROUVE
    echo    Solution: https://www.postgresql.org/download/
    echo    Ajouter au PATH: C:\Program Files\PostgreSQL\[VERSION]\bin
    set ALL_OK=0
) else (
    for /f "tokens=*" %%i in ('psql --version') do set PG_VER=%%i
    echo OK !PG_VER!
)

node --version >nul 2>&1
if errorlevel 1 (
    echo !  Node.js: NON TROUVE ^(optionnel pour le frontend^)
) else (
    for /f "tokens=*" %%i in ('node --version') do echo OK Node.js %%i
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo !  npm: NON TROUVE ^(optionnel pour le frontend^)
) else (
    echo OK npm trouve
)

if "!ALL_OK!"=="0" (
    echo.
    echo x  Prerequis manquants. Installez-les puis relancez ce script.
    pause
    exit /b 1
)

if not exist "backend" (
    echo x  Dossier backend introuvable. Lancez depuis la racine du projet.
    pause
    exit /b 1
)

if not exist "backend\requirements\base.txt" (
    echo x  backend\requirements\base.txt introuvable.
    pause
    exit /b 1
)

echo.
echo [2/4] Backend - venv + dependances + migrations...
echo.

cd backend

if not exist "venv" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 ( echo x  Creation venv echouee & pause & exit /b 1 )
    echo OK  venv cree
) else (
    echo OK  venv existant
)

call venv\Scripts\activate.bat
if errorlevel 1 ( echo x  Activation venv echouee & pause & exit /b 1 )

echo Installation des dependances...
pip install -q -r requirements/base.txt
if errorlevel 1 ( echo x  Installation des dependances echouee & pause & exit /b 1 )
echo OK  Dependances installees

echo Application des migrations...
alembic upgrade head
if errorlevel 1 (
    echo x  Migrations echouees. Verifiez que:
    echo    - PostgreSQL tourne
    echo    - La base 'edtech' existe
    echo    - Identifiants postgres/postgres corrects
    pause
    exit /b 1
)
echo OK  Migrations appliquees

cd ..

echo.
echo [3/4] Frontend - npm install...
echo.

if exist "frontend" (
    cd frontend
    if not exist "node_modules" (
        echo Installation des dependances Node...
        npm install
        if errorlevel 1 ( echo !  npm install echoue - ignoree & cd .. & goto admin )
        echo OK  Dependances Node installees
    ) else (
        echo OK  node_modules existant
    )
    cd ..
) else (
    echo !  Dossier frontend introuvable - ignore
)

:admin
echo.
echo [4/4] Creation du compte admin...
echo.

python scripts\db\seed_admin.py
if errorlevel 1 ( echo !  Admin deja present ou erreur ^(ignoree^) )

echo.
echo ========================================
echo   SETUP COMPLETE!
echo ========================================
echo.
echo Prochaines etapes:
echo.
echo   Terminal 1 - Backend:
echo     cd backend
echo     venv\Scripts\activate
echo     uvicorn app.main:app --reload
echo.
echo   Terminal 2 - Frontend:
echo     cd frontend
echo     npm run dev
echo.
echo   Acces:
echo     Frontend : http://localhost:3000
echo     API Docs : http://localhost:8000/docs
echo.
echo   Login admin:
echo     Email    : admin@edtech.com
echo     Password : Admin123456
echo.
pause

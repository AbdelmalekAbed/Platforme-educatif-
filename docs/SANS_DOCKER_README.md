# 🎯 Setup Sans Docker - Pour Utilisateurs Windows

Vous n'avez pas Docker? Pas de problème! Ce guide vous aide à configurer la plateforme localement.

## 📖 Documentation

| Guide | Description |
|-------|-------------|
| **[QUICKSTART_LOCAL.md](QUICKSTART_LOCAL.md)** 🚀 | Démarrage rapide (2 étapes) |
| **[SETUP_LOCAL_GUIDE.md](SETUP_LOCAL_GUIDE.md)** 📖 | Guide détaillé complet |
| **[GUIDE_ADMIN_SETUP.md](GUIDE_ADMIN_SETUP.md)** 🐳 | Alternative: Avec Docker |

---

## ⚡ Démarrage Ultra-Rapide

### 1️⃣ Vérification des Prérequis
```bash
check_requirements.bat
```

### 2️⃣ Installation Automatique
```bash
setup_local.bat
```

### 3️⃣ Démarrer l'Application

**Terminal 1 (Backend):**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### 4️⃣ Accès
- Frontend: http://localhost:3000
- Admin Email: admin@edtech.com
- Admin Password: Admin123456

---

## 📋 Fichiers de Configuration

| Fichier | Description |
|---------|-------------|
| `check_requirements.bat` | Vérifier les prérequis |
| `setup_local.bat` | Installation automatique (Batch) |
| `setup_local.ps1` | Installation automatique (PowerShell) |
| `seed_admin.py` | Script de création du compte admin |
| `QUICKSTART_LOCAL.md` | Guide de démarrage rapide |
| `SETUP_LOCAL_GUIDE.md` | Guide détaillé complet |

---

## 🔧 Prérequis à Installer

### Python 3.9+
```bash
# Vérifier
python --version

# Télécharger: https://www.python.org
# ⚠️ Cochez "Add Python to PATH"
```

### PostgreSQL
```bash
# Vérifier
psql --version

# Télécharger: https://www.postgresql.org
# Créer la base de données 'edtech'
psql -U postgres -c "CREATE DATABASE edtech;"
```

### Node.js (pour le frontend)
```bash
# Vérifier
node --version

# Télécharger: https://nodejs.org
```

---

## 🚀 Étapes Détaillées

### Étape 1: Préparer PostgreSQL
```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données
CREATE DATABASE edtech;

# Quitter
\q
```

### Étape 2: Exécuter le Script de Setup
```bash
# Option A: Batch (Command Prompt)
setup_local.bat

# Option B: PowerShell
.\setup_local.ps1
```

### Étape 3: Démarrer le Backend
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Étape 4: Démarrer le Frontend
```bash
# Dans un nouveau terminal
cd frontend
npm run dev
```

### Étape 5: Accéder à l'Application
- Ouvrez http://localhost:3000
- Connectez-vous avec admin@edtech.com / Admin123456

---

## 📊 Architecture Locale

```
┌─────────────────────────────────────┐
│     http://localhost:3000           │
│   Frontend (Next.js)                │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│     http://localhost:8000           │
│   Backend (FastAPI)                 │
└────────────────┬────────────────────┘
                 │
                 ↓
         ┌───────────────┐
         │  PostgreSQL   │
         │ localhost:5432│
         └───────────────┘
```

---

## 🔄 Redémarrage Ultérieur

### Backend
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm run dev
```

**Note**: Vous n'avez pas besoin de relancer `setup_local.bat` après la première exécution.

---

## 🆘 Troubleshooting Rapide

| Problème | Solution |
|----------|----------|
| "Python not found" | Réinstallez Python avec "Add Python to PATH" |
| "psql not found" | Ajoutez PostgreSQL bin folder au PATH |
| "Database connection refused" | Vérifiez que PostgreSQL est en cours d'exécution |
| "Cannot connect to database" | Créez la base de données: `psql -U postgres -c "CREATE DATABASE edtech;"` |
| "Port 3000 already in use" | Changez le port avec: `npm run dev -- -p 3001` |
| "Port 8000 already in use" | Changez le port: `uvicorn app.main:app --port 8001 --reload` |

**Pour plus de détails**, consultez [SETUP_LOCAL_GUIDE.md](SETUP_LOCAL_GUIDE.md#-troubleshooting)

---

## 📞 Support

1. Lisez les guides complets
2. Vérifiez les logs de terminal
3. Vérifiez que PostgreSQL est en cours d'exécution
4. Consultez la section Troubleshooting

---

## 🎓 Commandes Utiles

```bash
# Vérifier l'état de PostgreSQL
psql -U postgres -c "SELECT version();"

# Vérifier la base de données
psql -U postgres -l

# Réinitialiser la base de données
psql -U postgres -c "DROP DATABASE edtech; CREATE DATABASE edtech;"

# Appliquer les migrations
cd backend
alembic upgrade head

# Voir les migrations
alembic current

# Créer un compte admin
python ../seed_admin.py
```

---

## 📋 Compte Admin

Créé automatiquement par `setup_local.bat`

```
Email: admin@edtech.com
Mot de passe: Admin123456
Rôle: admin
Accès: Tous les espaces
```

---

## ✅ Résumé

1. Installez Python, PostgreSQL, Node.js
2. Créez la base de données `edtech`
3. Exécutez `setup_local.bat`
4. Démarrez le backend et le frontend
5. Connectez-vous à http://localhost:3000
6. Utilisez admin@edtech.com / Admin123456

**Vous êtes prêt!** 🎉


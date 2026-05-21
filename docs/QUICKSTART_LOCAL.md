# 🎯 QUICK START - Sans Docker

## ✅ CHECKLIST PRÉ-INSTALLATION

Avant de commencer, vérifiez que vous avez:

- [ ] Python 3.9+ installé et dans le PATH
- [ ] PostgreSQL installé et en cours d'exécution
- [ ] La base de données `edtech` créée dans PostgreSQL
- [ ] Node.js installé (pour le frontend)

**Pas sûr? Consultez [SETUP_LOCAL_GUIDE.md](SETUP_LOCAL_GUIDE.md) pour les détails**

---

## 🚀 DÉMARRAGE EN 2 ÉTAPES

### Étape 1: Configuration Initiale (PREMIÈRE FOIS SEULEMENT)

**Ouvrez Command Prompt ou PowerShell** depuis le dossier racine du projet:

#### Option A: Batch (Command Prompt)
```bash
setup_local.bat
```

#### Option B: PowerShell
```bash
.\setup_local.ps1
```

**Cela va:**
- ✅ Créer l'environnement virtuel
- ✅ Installer les dépendances
- ✅ Appliquer les migrations BD
- ✅ Créer le compte admin

**Durée: 2-3 minutes**

---

### Étape 2: Démarrage de l'Application (À CHAQUE FOIS)

#### Terminal 1: Backend
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

#### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

---

## 🌐 ACCÈS

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |

---

## 🔑 LOGIN ADMIN

```
Email: admin@edtech.com
Mot de passe: Admin123456
```

---

## 📖 GUIDES COMPLETS

- **Installation détaillée**: [SETUP_LOCAL_GUIDE.md](SETUP_LOCAL_GUIDE.md)
- **Avec Docker**: [GUIDE_ADMIN_SETUP.md](GUIDE_ADMIN_SETUP.md)
- **Instructions générales**: [INSTRUCTIONS.md](INSTRUCTIONS.md)

---

## ❌ PROBLÈMES?

### "Python not found"
→ Réinstallez Python et cochez "Add Python to PATH"

### "PostgreSQL not found"
→ Ajoutez `C:\Program Files\PostgreSQL\[VERSION]\bin` au PATH Windows

### "Could not connect to database"
→ Créez la base de données:
```bash
psql -U postgres -c "CREATE DATABASE edtech;"
```

### Autres problèmes?
→ Consultez la section **Troubleshooting** dans [SETUP_LOCAL_GUIDE.md](SETUP_LOCAL_GUIDE.md)


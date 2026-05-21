# 🎯 EdTech Platform - Guides de Setup

Vous avez choisi **WSL** pour votre environnement de développement. Excellent! 🐧

---

## 📖 Guides Disponibles

### 🐧 WSL (Votre Choix - RECOMMANDÉ)

| Guide | Description | Durée |
|-------|-------------|-------|
| [QUICKSTART_WSL.md](QUICKSTART_WSL.md) | 3 étapes pour démarrer rapidement | 5 min |
| [SETUP_WSL_GUIDE.md](SETUP_WSL_GUIDE.md) | Guide complet avec troubleshooting | 30 min |
| [WSL_README.md](WSL_README.md) | Vue d'ensemble et conseils pro | 15 min |
| [VSCODE_WSL_INTEGRATION.md](VSCODE_WSL_INTEGRATION.md) | Intégration VS Code + WSL | 10 min |

### 🐳 Docker Alternative

- [GUIDE_ADMIN_SETUP.md](GUIDE_ADMIN_SETUP.md) - Setup avec Docker

### 💻 Windows Local (Sans Docker, Sans WSL)

- [QUICKSTART_LOCAL.md](QUICKSTART_LOCAL.md) - Setup Windows natif
- [SETUP_LOCAL_GUIDE.md](SETUP_LOCAL_GUIDE.md) - Guide complet Windows

---

## 🚀 Démarrage WSL - 3 Étapes

### 1. Ouvrir WSL
```bash
# Menu Démarrer → WSL ou PowerShell → wsl
wsl
```

### 2. Aller au Projet et Setup
```bash
cd /mnt/c/Users/aabed/Desktop/Platform
bash setup_wsl.sh
```

### 3. Démarrer l'Application

**Terminal 1:**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

**Terminal 2:**
```bash
cd frontend && npm run dev
```

---

## 🌐 Accès

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Admin Email | admin@edtech.com |
| Admin Password | Admin123456 |

---

## 📁 Fichiers de Setup

| Fichier | Description |
|---------|-------------|
| `setup_wsl.sh` | Script d'installation automatique (bash) |
| `seed_admin.py` | Crée le compte admin |
| `QUICKSTART_WSL.md` | Démarrage rapide (3 étapes) |
| `SETUP_WSL_GUIDE.md` | Guide détaillé complet |
| `VSCODE_WSL_INTEGRATION.md` | VS Code + WSL |

---

## 💡 Conseils Pro WSL

### 1. Utiliser VS Code + WSL
```bash
# Dans le dossier du projet
code .
```

### 2. Créer des Alias
```bash
echo 'alias start-backend="cd backend && source venv/bin/activate && uvicorn app.main:app --reload"' >> ~/.bashrc
echo 'alias start-frontend="cd frontend && npm run dev"' >> ~/.bashrc
source ~/.bashrc

# Puis utiliser:
start-backend
start-frontend
```

### 3. Autostart PostgreSQL
```bash
sudo service postgresql start
```

---

## ✅ Checklist de Configuration

- [ ] WSL installé
- [ ] Terminal WSL ouvert
- [ ] Accès au dossier `/mnt/c/Users/aabed/Desktop/Platform`
- [ ] Script `setup_wsl.sh` exécuté
- [ ] Backend en cours d'exécution
- [ ] Frontend en cours d'exécution
- [ ] Frontend accessible sur http://localhost:3000
- [ ] Connexion admin réussie

---

## 🔄 Commandes Quotidiennes

```bash
# Démarrer le backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Démarrer le frontend (nouveau terminal)
cd frontend && npm run dev

# Voir les logs
# Consultez les terminaux

# Accéder
# http://localhost:3000
```

---

## ❌ Besoin d'Aide?

### Pour WSL
→ Consultez [SETUP_WSL_GUIDE.md#-troubleshooting](SETUP_WSL_GUIDE.md#-troubleshooting)

### Pour VS Code + WSL
→ Consultez [VSCODE_WSL_INTEGRATION.md](VSCODE_WSL_INTEGRATION.md)

### Pour Autres Problèmes
- Vérifiez que PostgreSQL est lancé: `sudo service postgresql status`
- Vérifiez les logs dans les terminaux
- Consultez le guide complet

---

## 📚 Documentation Complète

- **Frontend**: [INSTRUCTIONS.md](INSTRUCTIONS.md)
- **Backend**: [INSTRUCTIONS.md](INSTRUCTIONS.md)
- **Base de Données**: Consultez `backend/alembic/`
- **API**: http://localhost:8000/docs (après démarrage)

---

## 🎉 Prêt à Développer?

Commencez par [QUICKSTART_WSL.md](QUICKSTART_WSL.md) pour une mise en route rapide!

Bon développement! 🚀


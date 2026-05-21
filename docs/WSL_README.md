# 🐧 WSL - Guide Complet pour EdTech Platform

Vous avez choisi de développer avec **WSL (Windows Subsystem for Linux)**. Excellente décision! WSL offre une vraie expérience Linux sur Windows. 🚀

---

## 📖 Documentation WSL

| Document | Description |
|----------|-------------|
| **[QUICKSTART_WSL.md](QUICKSTART_WSL.md)** ⚡ | Démarrage en 3 étapes |
| **[SETUP_WSL_GUIDE.md](SETUP_WSL_GUIDE.md)** 📖 | Guide détaillé complet |

---

## ✅ Configuration Requise

### WSL 2 (Recommandé)

```bash
# Vérifier votre version WSL
wsl --list --verbose

# Si WSL 1, mettre à jour vers WSL 2:
# https://docs.microsoft.com/en-us/windows/wsl/install
```

### Distro Ubuntu (Recommandée)

```bash
# Si pas encore installée:
wsl --install -d Ubuntu
```

---

## 🚀 Démarrage Ultra-Rapide

### Étape 1: Ouvrir WSL
```bash
# Depuis le menu Démarrer ou PowerShell
wsl
```

### Étape 2: Accéder au Projet
```bash
cd /mnt/c/Users/aabed/Desktop/Platform
```

### Étape 3: Setup Initial (PREMIÈRE FOIS SEULEMENT)
```bash
bash setup_wsl.sh
```

Cela va:
- ✅ Installer Python3, PostgreSQL, Node.js (si nécessaire)
- ✅ Créer l'environnement virtuel
- ✅ Installer toutes les dépendances
- ✅ Appliquer les migrations
- ✅ Créer le compte admin

**Durée: 2-5 minutes**

### Étape 4: Démarrer l'Application

**Terminal WSL 1:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal WSL 2 (nouveau):**
```bash
cd frontend
npm run dev
```

### Étape 5: Accéder
- **Frontend**: http://localhost:3000
- **Admin**: admin@edtech.com / Admin123456

---

## 🔄 Commandes Quotidiennes

### Backend
```bash
cd /mnt/c/Users/aabed/Desktop/Platform/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend
```bash
cd /mnt/c/Users/aabed/Desktop/Platform/frontend
npm run dev
```

### PostgreSQL
```bash
# Démarrer
sudo service postgresql start

# Arrêter
sudo service postgresql stop

# Vérifier
sudo service postgresql status
```

---

## 💡 Conseils Pro

### 1. Utiliser VS Code avec WSL

Installez l'extension "Remote - WSL" dans VS Code, puis:

```bash
code .
```

VS Code s'ouvrira dans WSL automatiquement.

### 2. Créer des Alias

Éditer `~/.bashrc`:

```bash
alias platform="cd /mnt/c/Users/aabed/Desktop/Platform"
alias start-backend="cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
alias start-frontend="cd frontend && npm run dev"
```

Puis:
```bash
source ~/.bashrc
```

### 3. Autostart PostgreSQL

Pour que PostgreSQL démarre automatiquement:

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
# Chercher "listen_addresses" et vérifier qu'il est configuré
```

---

## 📁 Structure du Projet WSL

```
/mnt/c/Users/aabed/Desktop/Platform/
├── backend/
│   ├── venv/                    # ← Environnement virtuel
│   ├── app/
│   ├── requirements/
│   └── ...
├── frontend/
│   ├── node_modules/
│   ├── app/
│   └── ...
├── setup_wsl.sh                 # ← Script de setup
├── seed_admin.py
└── ...
```

---

## 🔧 Optimisation WSL

### Augmenter les Ressources

Créez un fichier `%USERPROFILE%\.wslconfig` depuis Windows:

```ini
[interop]
enabled=true
appendWindowsPath=true

[wsl2]
memory=4GB
processors=4
swap=2GB
localhostForwarding=true
```

Puis redémarrez WSL:
```bash
wsl --shutdown
wsl
```

---

## 📊 Ports et Services

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | localhost:5432 |

---

## 🆘 Troubleshooting Courant

### PostgreSQL ne démarre pas
```bash
sudo service postgresql start
sudo service postgresql status
```

### "alembic: command not found"
```bash
source venv/bin/activate
pip install -r requirements/base.txt
```

### "Can't connect to database"
```bash
# Créer la base de données si elle n'existe pas
psql -U postgres -c "CREATE DATABASE edtech;"
```

### WSL très lent
- Utiliser **WSL 2** (vs WSL 1)
- Stocker le projet dans le **système de fichiers Linux** (~/ au lieu de /mnt/c/)
- Augmenter les ressources (voir section Optimisation)

Pour plus de solutions, consultez [SETUP_WSL_GUIDE.md#-troubleshooting](SETUP_WSL_GUIDE.md#-troubleshooting)

---

## 🎓 Commandes Utiles WSL

```bash
# Gestion WSL
wsl --list                          # Voir toutes les distros
wsl --shutdown                      # Arrêter WSL
wsl -u root                         # Lancer en tant que root

# Dans WSL - Gestion des packages
sudo apt update                     # Mettre à jour les packages
sudo apt install python3 python3-pip   # Installer Python
sudo apt install postgresql         # Installer PostgreSQL

# Dans WSL - Navigation
cd /mnt/c/Users/aabed/Desktop/Platform   # Accéder au projet Windows
cd ~                                # Home Linux
ls -la                              # Lister les fichiers
tree                                # Voir l'arborescence

# Dans WSL - Python
python3 --version                   # Version Python
pip list                            # Packages installés
pip install -r requirements/base.txt # Installer les dépendances
source venv/bin/activate            # Activer venv
deactivate                          # Désactiver venv

# Dans WSL - Node.js
node --version                      # Version Node
npm --version                       # Version npm
npm install                         # Installer les packages
npm run dev                         # Lancer dev server
```

---

## 📚 Ressources Complémentaires

- [WSL Official Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [WSL 2 Setup](https://docs.microsoft.com/en-us/windows/wsl/install)
- [VS Code Remote WSL](https://code.visualstudio.com/docs/remote/wsl)
- [Ubuntu in WSL](https://ubuntu.com/wsl)
- [PostgreSQL on WSL](https://www.postgresql.org/download/linux/ubuntu/)

---

## 🎯 Résumé des Étapes

```bash
# 1. Ouvrir WSL
wsl

# 2. Accéder au projet
cd /mnt/c/Users/aabed/Desktop/Platform

# 3. Setup initial (première fois)
bash setup_wsl.sh

# 4. Démarrer backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# 5. Démarrer frontend (nouveau terminal)
cd frontend && npm run dev

# 6. Accéder à http://localhost:3000
# Login: admin@edtech.com / Admin123456
```

---

## ✨ Avantages de WSL

✅ Expérience Linux native sur Windows  
✅ Meilleure performance avec WSL 2  
✅ Intégration seamless avec VS Code  
✅ Accès aux outils Linux standards  
✅ Pas de virtualisation lourde (vs VirtualBox)  
✅ Système de fichiers unifié  

---

## 🎉 Prêt à Développer?

Vous avez maintenant un environnement WSL complet et configuré pour l'EdTech Platform.

**Consultez [QUICKSTART_WSL.md](QUICKSTART_WSL.md) pour démarrer rapidement!**

Bon développement! 🚀


# 🐧 Setup WSL - Guide Complet

## ✅ Prérequis

WSL doit être installé sur votre système Windows:

```bash
# Vérifier la version WSL
wsl --list --verbose

# Devrait afficher quelque chose comme:
# NAME      STATE         VERSION
# Ubuntu    Running       2
```

Si WSL n'est pas installé, exécutez dans PowerShell (Admin):
```powershell
wsl --install
wsl --install -d Ubuntu
```

---

## 🚀 Configuration Initiale (PREMIÈRE FOIS SEULEMENT)

### Étape 1: Ouvrir WSL

Ouvrez WSL en tant que terminal:
```bash
# Depuis Windows, tapez dans le menu Démarrer: "WSL"
# Ou ouvrez PowerShell et tapez: wsl
```

### Étape 2: Accéder au projet

```bash
# Si votre projet est sur le disque C:
cd /mnt/c/Users/aabed/Desktop/Platform

# Ou créez un raccourci (optionnel)
cd ~
ln -s /mnt/c/Users/aabed/Desktop/Platform platform
cd platform
```

### Étape 3: Rendre le script exécutable

```bash
chmod +x setup_wsl.sh
```

### Étape 4: Lancer le script de setup

```bash
bash setup_wsl.sh
```

Le script va automatiquement:
- ✅ Installer Python3, PostgreSQL, Node.js (si nécessaire)
- ✅ Créer l'environnement virtuel
- ✅ Installer les dépendances
- ✅ Appliquer les migrations
- ✅ Créer le compte admin

**Durée estimée: 3-5 minutes**

---

## 🌐 Démarrage de l'Application

### Terminal 1: Backend

```bash
cd /mnt/c/Users/aabed/Desktop/Platform
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Vous verrez:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Frontend

Ouvrez un **nouveau terminal WSL**:

```bash
cd /mnt/c/Users/aabed/Desktop/Platform
cd frontend
npm run dev
```

Vous verrez:
```
> ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Terminal 3: PostgreSQL (si nécessaire)

```bash
# Vérifier si PostgreSQL est en cours d'exécution
sudo service postgresql status

# Si arrêté, démarrer
sudo service postgresql start
```

---

## 🌐 Accès à l'Application

Une fois les serveurs démarrés:

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

---

## 🔑 Identifiants Admin

Créés automatiquement lors du setup:

```
Email: admin@edtech.com
Mot de passe: Admin123456
```

---

## 🔄 Démarrage Ultérieur (APRÈS PREMIER SETUP)

Vous n'avez **pas besoin** de relancer `setup_wsl.sh`. Utilisez ces commandes:

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

---

## 🔧 Commandes Utiles WSL

### Gestion de PostgreSQL
```bash
# Démarrer PostgreSQL
sudo service postgresql start

# Arrêter PostgreSQL
sudo service postgresql stop

# Vérifier le statut
sudo service postgresql status

# Se connecter à la BD
psql -U postgres -d edtech

# Dans psql, voir les tables
\dt

# Quitter psql
\q
```

### Gestion des migrations
```bash
cd backend

# Voir le statut des migrations
alembic current

# Voir toutes les migrations
alembic history

# Revenir à une migration précédente
alembic downgrade -1

# Réappliquer les migrations
alembic upgrade head
```

### Gestion de l'environnement virtuel
```bash
cd backend

# Activer
source venv/bin/activate

# Désactiver
deactivate

# Installer une nouvelle dépendance
pip install nom_package

# Voir les dépendances installées
pip list

# Réinstaller les dépendances
pip install -r requirements/base.txt
```

### Gestion du projet
```bash
# Voir les fichiers
ls -la

# Voir la structure du projet
tree -L 2

# Aller au dossier frontend
cd frontend

# Mettre à jour npm
npm update

# Vérifier les dépendances
npm list
```

---

## ❌ Troubleshooting

### Erreur: "PostgreSQL is not running"

```bash
# Vérifier si PostgreSQL est démarré
sudo service postgresql status

# Le démarrer
sudo service postgresql start

# Si ça ne fonctionne pas, redémarrer WSL
wsl --shutdown
wsl

# Puis redémarrer PostgreSQL
sudo service postgresql start
```

### Erreur: "alembic: command not found"

```bash
# Vérifier que l'environnement virtuel est activé
source venv/bin/activate

# Réinstaller les dépendances
pip install -r requirements/base.txt
```

### Erreur: "Cannot connect to database"

```bash
# Vérifier que PostgreSQL est en cours d'exécution
sudo service postgresql status

# Vérifier que la base de données existe
psql -U postgres -l

# Si elle n'existe pas, la créer
psql -U postgres -c "CREATE DATABASE edtech;"
```

### Erreur: "npm: command not found"

```bash
# Installer Node.js
sudo apt-get update
sudo apt-get install -y nodejs npm

# Vérifier
node --version
npm --version
```

### Erreur: "python3: command not found"

```bash
# Installer Python3
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# Vérifier
python3 --version
```

### WSL est très lent

- **Utiliser WSL 2** (plus rapide que WSL 1)
- **Stocker le projet dans le système de fichiers Linux** (pas sous `/mnt/c/`)
- **Utiliser VS Code avec l'extension WSL**

Voir: [WSL Performance](https://docs.microsoft.com/en-us/windows/wsl/compare-versions)

---

## 💡 Conseils WSL

### 1. Utiliser VS Code avec WSL

Installez l'extension "WSL" dans VS Code, puis:

```bash
# Ouvrir VS Code depuis WSL
code .
```

### 2. Créer des alias utiles

```bash
# Éditer ~/.bashrc
nano ~/.bashrc

# Ajouter:
alias platform="cd /mnt/c/Users/aabed/Desktop/Platform"
alias dev-backend="cd /mnt/c/Users/aabed/Desktop/Platform/backend && source venv/bin/activate && uvicorn app.main:app --reload"
alias dev-frontend="cd /mnt/c/Users/aabed/Desktop/Platform/frontend && npm run dev"

# Sauvegarder (Ctrl+O, Entrée, Ctrl+X)

# Recharger
source ~/.bashrc

# Utiliser
platform
```

### 3. Autostart PostgreSQL

```bash
# Éditer le fichier sudoers
sudo visudo

# Ajouter à la fin:
%sudo ALL=(ALL) NOPASSWD: /usr/sbin/service postgresql start

# Puis au démarrage de WSL:
sudo service postgresql start
```

### 4. Optimiser les performances

Éditer `%USERPROFILE%\.wslconfig` (depuis Windows):

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

---

## 📋 Structure du Projet dans WSL

```
/mnt/c/Users/aabed/Desktop/Platform/
├── backend/
│   ├── venv/                    # Environnement virtuel
│   ├── app/
│   ├── alembic/
│   ├── requirements/
│   └── ...
├── frontend/
│   ├── node_modules/
│   ├── app/
│   └── ...
├── setup_wsl.sh                 # Script de setup
├── seed_admin.py                # Script admin
└── ...
```

---

## 🎓 Raccourcis Utiles

| Commande | Effet |
|----------|-------|
| `wsl` | Lancer WSL |
| `wsl -d Ubuntu` | Lancer la distro Ubuntu |
| `wsl --shutdown` | Arrêter WSL |
| `wsl --list` | Voir les distros |
| `wsl -u root` | Lancer WSL en tant que root |

---

## 🔗 Ressources Utiles

- [Documentation WSL](https://docs.microsoft.com/en-us/windows/wsl/)
- [WSL 2 vs WSL 1](https://docs.microsoft.com/en-us/windows/wsl/compare-versions)
- [VS Code + WSL](https://code.visualstudio.com/docs/remote/wsl)
- [Ubuntu dans WSL](https://ubuntu.com/wsl)

---

## ✅ Résumé des Commandes Essentielles

```bash
# Setup initial
bash setup_wsl.sh

# Démarrer (après setup)
cd /mnt/c/Users/aabed/Desktop/Platform/backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend (nouveau terminal WSL)
cd /mnt/c/Users/aabed/Desktop/Platform/frontend
npm run dev

# PostgreSQL (si nécessaire)
sudo service postgresql start

# Accès
http://localhost:3000

# Admin
admin@edtech.com / Admin123456
```

---

## 🎉 Vous Êtes Prêt!

Votre environnement WSL est maintenant configuré. Profitez du développement! 🚀


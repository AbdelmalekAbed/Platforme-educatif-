# 🚀 Setup Local Sans Docker - Guide Complet

## ✅ Prérequis

Avant de commencer, installez les éléments suivants:

### 1. Python 3.9+
- Télécharger: https://www.python.org/downloads/
- **IMPORTANT**: Cochez "Add Python to PATH" pendant l'installation
- Vérification:
  ```bash
  python --version
  ```

### 2. PostgreSQL
- Télécharger: https://www.postgresql.org/download/windows/
- **IMPORTANT**: Notez le mot de passe admin (par défaut: `postgres`)
- Assurez-vous que `psql` est dans le PATH
- Vérification:
  ```bash
  psql --version
  ```

### 3. Node.js (pour le frontend)
- Télécharger: https://nodejs.org/
- Vérification:
  ```bash
  node --version
  npm --version
  ```

---

## 🔧 Configuration PostgreSQL

### Créer la base de données `edtech`

#### Option 1: Via pgAdmin (GUI)
1. Ouvrez pgAdmin (livré avec PostgreSQL)
2. Connectez-vous avec les identifiants PostgreSQL
3. Right-click sur "Databases" → Create → Database
4. Nom: `edtech`
5. Cliquez "Save"

#### Option 2: Via Command Line
```bash
psql -U postgres -c "CREATE DATABASE edtech;"
```

**Vérification**:
```bash
psql -U postgres -l
# Vous devriez voir 'edtech' dans la liste
```

---

## 🚀 Exécution du Script de Setup

### Étape 1: Ouvrir Command Prompt
- Appuyez sur `Win + R`
- Tapez `cmd` et appuyez sur Entrée
- Naviguez vers le projet:
  ```bash
  cd C:\Users\aabed\Desktop\Platform
  ```

### Étape 2: Lancer le script d'installation
```bash
setup_local.bat
```

Le script va automatiquement:
- ✅ Créer l'environnement virtuel Python
- ✅ Installer les dépendances
- ✅ Appliquer les migrations de base de données
- ✅ Créer le compte admin

**Temps estimé: 2-3 minutes**

---

## 📋 Résultat Attendu

À la fin du script, vous verrez:
```
========================================
✅ SETUP COMPLÉTÉ AVEC SUCCÈS!
========================================

🎯 Prochaines étapes:

   1. Démarrer le backend:
      cd backend
      venv\Scripts\activate
      uvicorn app.main:app --reload

   2. Dans un autre terminal, démarrer le frontend:
      cd frontend
      npm install (première fois seulement)
      npm run dev
```

---

## 🎯 Démarrage de l'Application

### Terminal 1: Backend
```bash
cd C:\Users\aabed\Desktop\Platform\backend

# Activer l'environnement virtuel
venv\Scripts\activate

# Démarrer le serveur
uvicorn app.main:app --reload
```

Vous verrez:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Frontend
```bash
cd C:\Users\aabed\Desktop\Platform\frontend

# Première fois seulement
npm install

# Démarrer le serveur
npm run dev
```

Vous verrez:
```
> ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

---

## 🌐 Accès à l'Application

Une fois les serveurs démarrés:

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend** | http://localhost:3000 | Interface utilisateur |
| **API** | http://localhost:8000 | API backend |
| **API Docs** | http://localhost:8000/docs | Documentation Swagger |
| **Database** | localhost:5432 | PostgreSQL |

---

## 🔑 Identifiants de Connexion

### Compte Admin
- Email: `admin@edtech.com`
- Mot de passe: `Admin123456`
- Accès: Tous les espaces (Admin/Prof/Étudiants/Vendeurs)

### Autres Comptes de Test
Vous pouvez créer d'autres comptes via:
1. L'interface `/register` sur http://localhost:3000
2. L'endpoint API `/api/v1/auth/register`

---

## ❌ Troubleshooting

### ❌ "Python not found" ou "Python is not recognized"
**Solution:**
1. Réinstallez Python en cochant "Add Python to PATH"
2. Redémarrez Windows
3. Ouvrez une nouvelle Command Prompt

### ❌ "psql: command not found" ou "PostgreSQL is not recognized"
**Solution:**
1. Trouvez le dossier bin de PostgreSQL:
   - Généralement: `C:\Program Files\PostgreSQL\[VERSION]\bin`
2. Ajoutez-le au PATH Windows:
   - Paramètres → Variables d'environnement → Éditer les variables d'environnement système
   - Variables d'environnement → Path → Ajouter le chemin PostgreSQL

### ❌ "Could not connect to database"
**Solution:**
1. Vérifiez que PostgreSQL est en cours d'exécution:
   ```bash
   psql -U postgres -c "SELECT version();"
   ```
2. Vérifiez que la base de données existe:
   ```bash
   psql -U postgres -l
   ```
3. Créez-la si elle n'existe pas:
   ```bash
   psql -U postgres -c "CREATE DATABASE edtech;"
   ```

### ❌ "Command not found: alembic"
**Solution:**
1. Assurez-vous que l'environnement virtuel est activé:
   ```bash
   venv\Scripts\activate
   ```
2. Réinstallez les dépendances:
   ```bash
   pip install -r requirements/base.txt
   ```

### ❌ "The account admin@edtech.com already exists"
**Solution:**
C'est normal! Le compte a déjà été créé. Vous pouvez vous connecter immédiatement.

---

## 🔄 Redémarrage Ultérieur

Si vous fermez l'application et voulez relancer:

### Démarrer le Backend
```bash
cd C:\Users\aabed\Desktop\Platform\backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Démarrer le Frontend
```bash
cd C:\Users\aabed\Desktop\Platform\frontend
npm run dev
```

**Pas besoin de relancer `setup_local.bat`** à moins que vous supprimiez les fichiers.

---

## 📝 Fichiers Importants

| Fichier | Purpose |
|---------|---------|
| `setup_local.bat` | Script d'installation automatique |
| `seed_admin.py` | Script de création du compte admin |
| `backend/.env` | Configuration backend (optionnel) |
| `backend/requirements/base.txt` | Dépendances Python |
| `frontend/package.json` | Dépendances Node.js |

---

## 🎓 Commandes Utiles

```bash
# Réinitialiser la base de données
psql -U postgres -c "DROP DATABASE edtech; CREATE DATABASE edtech;"

# Appliquer les migrations à nouveau
cd backend
alembic upgrade head

# Voir les migrations appliquées
alembic current

# Revenir à une migration précédente
alembic downgrade -1
```

---

## 📞 Besoin d'Aide?

1. Consultez le README.md principal
2. Consultez INSTRUCTIONS.md
3. Vérifiez les logs du backend dans le terminal
4. Vérifiez les logs du frontend dans le terminal


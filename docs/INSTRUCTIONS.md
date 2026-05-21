# INSTRUCTIONS — EdTech Platform

Guide complet des commandes pour développer, déployer et maintenir la plateforme.

---

## 🚀 Démarrage rapide

### Option 1 : Tout lancer avec Docker (RECOMMANDÉ)

```bash
docker-compose up
```

**Accès :**
- **Frontend** → http://localhost:3000
- **Backend API** → http://localhost:8000
- **API Swagger Docs** → http://localhost:8000/docs
- **MinIO Console** → http://localhost:9001 (login: minioadmin / minioadmin)

---

### Option 2 : Développement local (sans Docker)

#### Démarrer le Backend

```bash
cd backend

# 1. Créer un environnement virtuel
python -m venv venv

# 2. Activer l'environnement
# Windows :
venv\Scripts\activate
# macOS/Linux :
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements/base.txt

# 4. (Première fois) Créer la base de données et appliquer les migrations
alembic upgrade head

# 5. Démarrer le serveur
uvicorn app.main:app --reload
```

Le backend sera accessible sur **http://localhost:8000**

#### Démarrer le Frontend

Dans un **autre terminal** :

```bash
cd frontend

# 1. Installer les dépendances (première fois seulement)
npm install

# 2. Démarrer le serveur de développement
npm run dev
```

Le frontend sera accessible sur **http://localhost:3000**

---

## 📝 Identifiants de test

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Admin | admin@edtech.com | Admin123456 |
| Professeur | teacher@edtech.com | Teacher123456 |
| Élève | student@edtech.com | Student123456 |
| Vendeur | vendor@edtech.com | Vendor123456 |

> **Note :** Ces comptes doivent être créés via l'endpoint `/api/v1/auth/register` ou en base de données.

---

## 🔧 Commandes Backend

### Gestion de la Base de Données

#### Créer une nouvelle migration

```bash
cd backend
alembic revision --autogenerate -m "Description de la modification"
```

Exemple :
```bash
alembic revision --autogenerate -m "Add user_role column to users table"
```

#### Appliquer les migrations

```bash
# Appliquer tous les changements
alembic upgrade head

# Appliquer une version spécifique
alembic upgrade 1a2b3c4d5e6f
```

#### Annuler les migrations

```bash
# Annuler la dernière migration
alembic downgrade -1

# Revenir à une version spécifique
alembic downgrade 1a2b3c4d5e6f
```

#### Voir l'historique des migrations

```bash
alembic history
```

---

### API et Serveur

#### Démarrer le serveur FastAPI

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Accéder à la documentation API

Une fois le serveur lancé, ouvrez :
- **Swagger UI** → http://localhost:8000/docs
- **ReDoc** → http://localhost:8000/redoc

#### Tester les endpoints avec curl

```bash
# Inscription
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }'

# Connexion
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123"
  }'

# Récupérer le profil (remplacer TOKEN par le token reçu)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"
```

---

### Celery et Jobs asynchrones

#### Démarrer le worker Celery

```bash
cd backend
celery -A app.tasks.worker worker --loglevel=info
```

#### Démarrer Celery Beat (scheduling)

```bash
cd backend
celery -A app.tasks.worker beat --loglevel=info
```

---

## 📱 Commandes Frontend

### Développement

```bash
cd frontend

# Démarrer le serveur de développement
npm run dev

# Vérifier la syntaxe TypeScript
npx tsc --noEmit

# Linter le code
npm run lint
```

### Production

```bash
cd frontend

# Construire pour la production
npm run build

# Démarrer le serveur optimisé
npm start
```

### Dépendances

```bash
cd frontend

# Installer les dépendances
npm install

# Ajouter une nouvelle dépendance
npm install <package-name>

# Mettre à jour les dépendances
npm update

# Vérifier les vulnérabilités
npm audit
```

---

## 🐳 Commandes Docker

### Gestion complète

```bash
# Démarrer tous les services
docker-compose up

# Démarrer en arrière-plan
docker-compose up -d

# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes (attention : supprime les données !)
docker-compose down -v

# Voir les logs
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Services individuels

```bash
# Redémarrer un service spécifique
docker-compose restart backend
docker-compose restart frontend
docker-compose restart db

# Arrêter un service
docker-compose stop backend

# Démarrer un service
docker-compose start backend

# Construire l'image d'un service
docker-compose build backend
```

### Base de données dans Docker

```bash
# Accéder à PostgreSQL dans le conteneur
docker-compose exec db psql -U postgres -d edtech

# Exécuter une commande SQL
docker-compose exec db psql -U postgres -d edtech -c "SELECT * FROM users;"
```

---

## 🔍 Debugging et Testing

### Backend — Debug avec print

```python
# Dans app/modules/courses/service.py
async def get_courses(db, teacher_id=None):
    print(f"DEBUG: teacher_id = {teacher_id}")
    # ...code
```

Voir les logs dans le terminal du serveur.

### Frontend — Debug Console

```javascript
// Dans components/dashboard/sidebar.tsx
export function Sidebar() {
  console.log("DEBUG: Rendering Sidebar");
  // ...code
}
```

Voir les logs dans la console du navigateur (F12).

### Tester les WebSocket

```bash
# Installer wscat (outil pour tester WebSocket)
npm install -g wscat

# Tester la connexion WebSocket (remplacer TOKEN)
wscat -c "ws://localhost:8000/ws/notifications?token=TOKEN"
```

---

## 📊 Requêtes API importantes

### Auth

```bash
# Inscription
POST /api/v1/auth/register

# Connexion
POST /api/v1/auth/login

# Renouveler le token
POST /api/v1/auth/refresh

# Profil courant
GET /api/v1/auth/me
```

### Cours

```bash
# Lister tous les cours
GET /api/v1/courses/

# Créer un cours
POST /api/v1/courses/

# Récupérer un cours
GET /api/v1/courses/{course_id}

# Modifier un cours
PUT /api/v1/courses/{course_id}

# Créer une session live
POST /api/v1/courses/{course_id}/sessions

# Lister les sessions d'un cours
GET /api/v1/courses/{course_id}/sessions
```

### Devoirs

```bash
# Lister les devoirs d'un cours
GET /api/v1/homework/course/{course_id}

# Créer un devoir
POST /api/v1/homework/

# Soumettre un devoir
POST /api/v1/homework/submit

# Récupérer les soumissions
GET /api/v1/homework/{homework_id}/submissions

# Noter une soumission
PUT /api/v1/homework/submissions/{submission_id}/grade
```

### Présences

```bash
# Présences d'une session
GET /api/v1/attendance/session/{session_id}

# Présences d'un élève
GET /api/v1/attendance/student/{student_id}

# Mettre à jour une présence
PUT /api/v1/attendance/{attendance_id}
```

### Notifications

```bash
# Récupérer les notifications
GET /api/v1/notifications/

# Marquer comme lue
PUT /api/v1/notifications/{notification_id}/read

# Marquer tout comme lu
PUT /api/v1/notifications/read-all
```

### Admin

```bash
# Statistiques plateforme
GET /api/v1/admin/stats

# Lister les utilisateurs
GET /api/v1/admin/users?role=student

# Activer/désactiver un utilisateur
PUT /api/v1/admin/users/{user_id}/toggle-active
```

---

## ⚙️ Variables d'environnement

Créer un fichier `backend/.env` :

```bash
# App
APP_NAME=EdTech Platform
DEBUG=True
SECRET_KEY=your-super-secret-key-change-in-production
ALLOWED_ORIGINS=["http://localhost:3000"]

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/edtech
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/edtech

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage (MinIO / S3)
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET_NAME=edtech
STORAGE_USE_SSL=false

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (optionnel)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

---

## 📚 Ressources utiles

- **FastAPI Docs** → https://fastapi.tiangolo.com
- **Next.js Docs** → https://nextjs.org/docs
- **PostgreSQL Docs** → https://www.postgresql.org/docs
- **Celery Docs** → https://docs.celeryproject.io
- **WebSocket Protocol** → https://tools.ietf.org/html/rfc6455

---

## 🆘 Dépannage

### Backend ne démarre pas

```bash
# Vérifier les dépendances
pip list

# Réinstaller les dépendances
pip install --upgrade -r requirements/base.txt

# Vérifier la connexion PostgreSQL
psql -U postgres -h localhost -d edtech
```

### Frontend ne charge pas

```bash
# Vider le cache Next.js
rm -rf .next

# Réinstaller les dépendances npm
rm -rf node_modules
npm install

# Reconstruire
npm run build
```

### Docker refuses de démarrer

```bash
# Vérifier les ports en utilisation
netstat -an | findstr ":8000\|:3000\|:5432"

# Arrêter les conteneurs
docker-compose down -v

# Relancer
docker-compose up
```

### Base de données pleine / Erreur de migration

```bash
# Se connecter à la base
docker-compose exec db psql -U postgres -d edtech

# Voir les migrations appliquées
\d alembic_version;

# Réinitialiser (ATTENTION - supprime tout)
docker-compose exec db psql -U postgres -d edtech -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose exec backend alembic upgrade head
```

---

## 📋 Workflow type de développement

### Pour ajouter une nouvelle fonctionnalité

1. **Backend**
   ```bash
   cd backend
   # Créer la migration
   alembic revision --autogenerate -m "Add new feature"
   # Appliquer la migration
   alembic upgrade head
   # Créer les modèles, services, routes
   # Tester avec Swagger docs : http://localhost:8000/docs
   ```

2. **Frontend**
   ```bash
   cd frontend
   # Créer les composants et pages
   # Ajouter les appels API dans services/api.ts
   # Tester en dev : npm run dev
   ```

3. **Mettre à jour le README**
   - Ajouter l'endpoint API
   - Documenter les nouvelles pages
   - Mettre à jour le changelog

---

**Dernière mise à jour :** 10/05/2026

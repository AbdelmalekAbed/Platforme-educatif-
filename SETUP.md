# SETUP — Installation et utilisation du projet

Ce document est **auto-suffisant** : il décrit comment installer, lancer et faire évoluer le projet sur n'importe quel PC. Il est destiné à la fois aux humains et aux assistants IA (Claude, Copilot, etc.) qui n'ont aucun contexte préalable.

---

## Vue d'ensemble du projet

**Type** : Plateforme EdTech (cours en ligne, élèves/enseignants/admin).

**Stack** :

- **Backend** : Python 3.10/3.11, FastAPI, SQLAlchemy 2 (async), Alembic, Celery
- **Frontend** : Next.js 16, React 18, TypeScript, TailwindCSS, Radix UI, Zustand
- **Base de données** : PostgreSQL 16 **hébergée sur Neon (cloud)**
- **Cache / Broker** : Redis 7 (local)
- **Stockage fichiers** : MinIO (local, S3-compatible)

**Ports utilisés** :

- `3000` → Frontend Next.js
- `8000` → Backend FastAPI (Swagger sur `/docs`)
- `6379` → Redis (local)
- `9000` → MinIO API (local)
- `9001` → Console MinIO (local)

**Architecture des données** :

- La **base PostgreSQL** est dans le cloud (Neon) → **partagée entre tous les PC du dev**
- **Redis** et **MinIO** restent **locaux à chaque PC** (pas de données métier critiques)
- Le **code** est versionné via Git

---

## 0. Prérequis logiciels

À installer **une fois** sur chaque PC :

| Outil | Version | Utilité |
|-------|---------|---------|
| Git | 2.40+ | Cloner le repo |
| Python | 3.10 ou 3.11 | Backend FastAPI |
| Node.js | 18+ (LTS) | Frontend Next.js |
| Docker Desktop | dernière | Redis + MinIO locaux (recommandé) |
| psql client | 16 (optionnel) | Pour exécuter du SQL sur Neon depuis la ligne de commande |

> Pas besoin d'installer PostgreSQL localement : la base est dans le cloud Neon.
> Sur Windows, Docker Desktop nécessite WSL2.

---

## 1. Cloner le repo

```bash
git clone https://github.com/<user>/<repo>.git
cd <repo>
```

---

## 2. Configurer les variables d'environnement

### Backend — `backend/.env`

⚠️ Ce fichier est **gitignored** (volontairement). Il doit être recréé manuellement sur chaque PC.

```bash
cp backend/.env.example backend/.env
```

Édite `backend/.env` :

```env
# App
APP_NAME=EdTech Platform
DEBUG=True
SECRET_KEY=change-me-in-production-use-long-random-secret-key
ALLOWED_ORIGINS=["http://localhost:3000"]

# Database — Neon cloud (mêmes URLs sur TOUS les PC du dev)
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@ep-xxx.eu-central-1.aws.neon.tech/edtech?ssl=require
DATABASE_URL_SYNC=postgresql://USER:PASSWORD@ep-xxx.eu-central-1.aws.neon.tech/edtech?sslmode=require

# Redis — local
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=change-me-jwt-secret-key-make-it-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# MinIO Storage — local
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET_NAME=edtech
STORAGE_USE_SSL=false

# Celery — local (via Redis)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (optionnel)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@edtech.com
```

> ⚠️ **Piège classique** — différence subtile entre les deux URLs DB :
>
> - **asyncpg** (`DATABASE_URL`) → `?ssl=require`
> - **psycopg2** (`DATABASE_URL_SYNC`) → `?sslmode=require`
>
> Les deux URLs pointent vers la **même base Neon** mais asyncpg et psycopg2 ne reconnaissent pas le même paramètre SSL.

### Frontend — aucun `.env` requis

Le frontend tape sur `/api/v1` en relatif. Aucune variable à définir pour le dev local.

---

## 3. Démarrer Redis et MinIO (locaux)

### Option A — avec Docker (recommandé)

```bash
docker compose up -d redis minio
```

Vérifier que les conteneurs tournent :

```bash
docker compose ps
```

### Option B — sans Docker

- **Redis 7** installé localement sur `localhost:6379`
- **MinIO** (optionnel, seulement si tu fais des uploads de fichiers)

---

## 4. Backend — installer et lancer

```bash
cd backend
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1
# Linux/Mac
# source venv/bin/activate

pip install -r requirements/dev.txt
```

### 4a. Migrations DB

**Décision à prendre** : la base Neon est-elle déjà initialisée ?

- **Cas 1 — Base Neon vierge** (premier setup) : applique les migrations.
- **Cas 2 — Base Neon déjà initialisée** (un autre PC l'a déjà fait) : NE PAS relancer, sinon erreurs.

Pour vérifier : ouvre le dashboard Neon → onglet **Tables**. Si tu vois `users`, `courses`, `chapters`, etc., la base est déjà initialisée → saute cette étape.

Si la base est vide :

```bash
alembic upgrade head
```

### 4b. Créer l'admin initial

Même logique :

- Si l'admin existe déjà (cas où un autre PC l'a créé) → saute cette étape
- Sinon, exécute une des options ci-dessous

**Option 1** — script Python :

```bash
python -m app.scripts.seed_admin
```

**Option 2** — SQL via psql :

```bash
psql "postgresql://USER:PASSWORD@ep-xxx.eu-central-1.aws.neon.tech/edtech?sslmode=require" -f ../scripts/db/create_admin.sql
```

**Option 3** — coller le contenu de `scripts/db/create_admin.sql` dans l'éditeur SQL du dashboard Neon.

Identifiants par défaut : `admin@edtech.com` / `Admin123456`.

### 4c. Lancer le serveur

```bash
uvicorn app.main:app --reload --port 8000
```

API : http://localhost:8000 — Swagger : http://localhost:8000/docs

### 4d. (Optionnel) Lancer Celery

Si tu utilises les tâches asynchrones :

```bash
celery -A app.tasks.worker worker --loglevel=info
```

---

## 5. Frontend — installer et lancer

Dans un autre terminal :

```bash
cd frontend
npm install
npm run dev
```

App : http://localhost:3000

---

## 6. Vérification que tout fonctionne

1. http://localhost:3000 → page d'accueil charge
2. http://localhost:8000/docs → Swagger répond
3. Login avec `admin@edtech.com` / `Admin123456` → succès
4. **Test de sync inter-PC** : créer un cours de test, vérifier qu'il apparaît dans le dashboard Neon (onglet Tables → `courses`)

---

## Configuration Neon (à faire une seule fois, premier PC uniquement)

Si la base Neon n'existe pas encore, voici la procédure pour la créer.

### 1. Créer le compte et le projet

1. Aller sur [neon.tech](https://neon.tech) → Sign up (GitHub ou email, sans carte bancaire)
2. Créer un projet :
   - Project name : `edtech-platform`
   - Postgres version : 16
   - Region : la plus proche (ex. Europe Frankfurt)
   - Database name : `edtech`

### 2. Récupérer la connection string

Sur le dashboard Neon, copier la **Connection string** :

```text
postgresql://user:password@ep-xxx.eu-central-1.aws.neon.tech/edtech?sslmode=require
```

### 3. Adapter pour le projet

Dans `backend/.env` (voir section 2), mettre **deux variantes** de cette URL :

- `DATABASE_URL` : préfixe `postgresql+asyncpg://` et suffixe `?ssl=require`
- `DATABASE_URL_SYNC` : préfixe `postgresql://` et suffixe `?sslmode=require`

### 4. Initialiser le schéma

```bash
cd backend
alembic upgrade head
```

Vérifier sur le dashboard Neon (onglet Tables) que `users`, `courses`, etc. sont créées.

### 5. Créer l'admin

Voir section 4b.

### 6. Sauvegarder la connection string

Garder la string Neon dans un gestionnaire de mots de passe — tu en auras besoin pour configurer chaque nouveau PC.

---

## Workflow multi-PC

Une fois le setup terminé sur tous les PC :

### Routine quotidienne

```bash
# En arrivant sur un PC
git pull

# En quittant un PC
git add .
git commit -m "..."
git push
```

- Le **code** se synchronise via Git
- Les **données** se synchronisent automatiquement via Neon

### Migrations DB futures

Quand tu modifies un modèle SQLAlchemy :

1. Sur **un seul** PC : `alembic revision --autogenerate -m "ajout colonne X"`
2. Sur ce **même** PC : `alembic upgrade head` (applique sur Neon)
3. `git add` + `commit` + `push` du fichier de migration
4. Sur les autres PC : juste `git pull` — la migration est déjà appliquée dans Neon, pas besoin de relancer

> ⚠️ Ne jamais lancer deux `alembic upgrade` en parallèle depuis deux PC sur la même base. Choisir un PC "maître" pour les migrations.

### Conflits Git

Toujours `git push` avant de quitter un PC, toujours `git pull` avant de commencer sur l'autre. Sinon, conflits de merge.

---

## Sauvegardes

Le free tier Neon inclut un **point-in-time restore sur 24h**. Pour des données métier critiques, faire un `pg_dump` régulier dans `backups/` (dossier gitignored) :

```bash
pg_dump "postgresql://USER:PWD@ep-xxx.neon.tech/edtech?sslmode=require" > backups/backup-AAAA-MM-JJ.sql
```

---

## Évolutions cloud futures (optionnel)

Si plus tard tu veux aussi partager Redis et les fichiers uploadés entre PC :

| Service                | Solution cloud gratuite                               |
|------------------------|-------------------------------------------------------|
| Redis (cache + Celery) | **Upstash Redis** (free tier généreux)                |
| MinIO / S3 (fichiers)  | **Cloudflare R2** (10 GB gratuit) ou **Backblaze B2** |

Pour l'instant, les garder locaux est largement suffisant.

---

## Dépannage

| Problème | Solution |
|----------|----------|
| `alembic upgrade head` échoue avec SSL error | Vérifier que `DATABASE_URL_SYNC` utilise bien `?sslmode=require` |
| Backend démarre mais erreurs DB asynchrones | Vérifier que `DATABASE_URL` utilise `?ssl=require` (pas `sslmode`) |
| Connexion Neon refusée / timeout | Vérifier la région choisie (latence > 200ms = mauvaise région) |
| Première requête lente après inactivité | Normal — Neon free tier suspend après 5 min d'inactivité, 1-2s de wake-up |
| Frontend ne contacte pas le backend | Vérifier que le backend tourne sur le port 8000 |
| `pip install` échoue sur `psycopg2-binary` | Installer les outils de build PostgreSQL ou `pip install psycopg[binary]` |
| Port 6379 déjà utilisé | Stopper l'instance Redis locale ou changer le port dans `docker-compose.yml` |
| Dépassement quota Neon (0.5 GB) | Faire le ménage dans la base, ou upgrade vers le plan payant |
| `alembic upgrade head` dit "Target database is not up to date" | Vérifier que tu pointes bien sur la même base Neon que les autres PC |

---

## Pour un assistant IA qui lit ce fichier

Si tu es un Claude (ou autre IA) sur un nouveau PC et que l'utilisateur te demande de l'aider à installer ou lancer le projet :

1. Lis ce fichier en entier d'abord.
2. Vérifie si `backend/.env` existe — sinon, demande à l'utilisateur la connection string Neon.
3. Suppose que **la base Neon est déjà initialisée et contient l'admin** (cas standard si ce n'est pas la toute première installation). NE LANCE PAS `alembic upgrade head` ni le seed admin sans confirmation.
4. L'ordre de démarrage est : (a) Docker Redis/MinIO → (b) Backend → (c) Frontend.
5. Demande à l'utilisateur de confirmer chaque étape avant de passer à la suivante — l'utilisateur peut préférer faire certaines étapes lui-même.

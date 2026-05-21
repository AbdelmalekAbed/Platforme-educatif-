# EdTech Platform

Plateforme éducative complète avec quatre espaces distincts : **Élève**, **Professeur**, **Administrateur** et **Vendeur**.

---

## Statut du projet

| Phase | Statut |
|-------|--------|
| Phase 1 — MVP (Auth, Cours, Live, Présence, Replay, Devoirs) | ✅ En cours |
| Phase 2 — Paiements, Notifications, Analytics, Calendriers | 🔲 Planifié |
| Phase 3 — Mobile, IA, Recommandations, Chatbot | 🔲 Futur |

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Frontend | Next.js 16 + TypeScript + TailwindCSS |
| Backend | FastAPI (Python) |
| Base de données | PostgreSQL |
| Cache / Temps réel | Redis + Pub/Sub |
| Live vidéo | WebRTC + WebSocket (signaling natif FastAPI) |
| Jobs asynchrones | Celery + Redis |
| Stockage vidéo | MinIO (MVP) → S3 (scale) |
| Auth | JWT + Refresh Tokens + RBAC |
| Déploiement | Docker Compose |

---

## Architecture

```
frontend/          → Next.js (App Router)
backend/           → FastAPI (monolithe modulaire)
docker-compose.yml → Orchestration complète
```

### Backend — Modules

```
app/
├── core/
│   ├── config/       → Settings (pydantic-settings)
│   ├── database/     → SQLAlchemy async + session
│   ├── security/     → JWT, hachage de mot de passe
│   └── permissions/  → RBAC — rôles & permissions
│
├── modules/
│   ├── auth/         → Register, Login, Refresh, Me
│   ├── users/        → User, StudentProfile, TeacherProfile, VendorProfile
│   ├── courses/      → Cours, Sessions, Inscriptions, Ressources
│   ├── attendance/   → Présences (auto-marquage via WebSocket)
│   ├── recordings/   → Enregistrements de sessions
│   ├── homework/     → Devoirs + Soumissions + Notes
│   ├── payments/     → Paiements + Factures
│   ├── notifications/→ Notifications in-app
│   ├── admin/        → Stats plateforme, gestion utilisateurs
│   ├── analytics/    → (planifié Phase 2)
│   ├── live_classes/ → (planifié Phase 2)
│   └── vendors/      → (planifié Phase 2)
│
├── api/routes/       → Endpoints REST
├── websocket/        → Manager WebSocket (notifications + signaling WebRTC)
└── tasks/            → Celery — workflow post-cours automatisé
```

### Frontend — Pages

```
app/
├── (auth)/auth/login/     → Connexion
├── (auth)/auth/register/  → Inscription
├── admin/                 → Dashboard admin + gestion utilisateurs
├── teacher/               → Dashboard + cours + sessions
├── student/               → Dashboard + cours + devoirs + notifications
└── vendor/                → Dashboard vendeur (Phase 2)
```

### Système de rôles (RBAC)

| Rôle | Accès |
|------|-------|
| `admin` | Toutes les permissions |
| `teacher` | Créer/gérer cours, sessions live, devoirs, présences |
| `student` | Consulter cours, soumettre devoirs, voir présences/paiements |
| `vendor` | Gérer produits/ventes (Phase 2) |

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Node.js 20+
- Python 3.12+

---

## Démarrage rapide

### Tout lancer avec Docker (recommandé)

```bash
docker-compose up
```

Services démarrés :
- Frontend → http://localhost:3000
- Backend API → http://localhost:8000
- Swagger docs → http://localhost:8000/docs
- MinIO console → http://localhost:9001 (minioadmin / minioadmin)

### Développement local (sans Docker)

#### Backend

```bash
cd backend
cp .env.example .env          # Configurer les variables
pip install -r requirements/base.txt
alembic upgrade head          # Créer les tables DB
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Migrations de base de données

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## Variables d'environnement

Copier `backend/.env.example` en `backend/.env` et ajuster :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL PostgreSQL (asyncpg) | postgresql+asyncpg://... |
| `JWT_SECRET_KEY` | Clé secrète JWT | **Changer en production** |
| `SECRET_KEY` | Clé secrète app | **Changer en production** |
| `REDIS_URL` | URL Redis | redis://localhost:6379/0 |
| `STORAGE_ENDPOINT` | MinIO endpoint | localhost:9000 |

---

## API — Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/auth/register` | Inscription |
| POST | `/api/v1/auth/login` | Connexion |
| POST | `/api/v1/auth/refresh` | Renouveler le token |
| GET | `/api/v1/auth/me` | Profil utilisateur courant |
| GET/POST | `/api/v1/courses/` | Lister / Créer des cours |
| POST | `/api/v1/courses/{id}/sessions` | Créer une session live |
| GET/POST | `/api/v1/homework/` | Devoirs |
| POST | `/api/v1/homework/submit` | Soumettre un devoir |
| GET | `/api/v1/attendance/session/{id}` | Présences d'une session |
| GET | `/api/v1/notifications/` | Notifications utilisateur |
| GET | `/api/v1/admin/stats` | Statistiques plateforme (admin) |
| GET | `/api/v1/admin/users` | Liste des utilisateurs (admin) |

## WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/notifications?token=<jwt>` | Notifications temps réel |
| `ws://localhost:8000/ws/live-class/{room_id}?token=<jwt>` | Signaling WebRTC cours live |

---

## Automatisations

Après la fin d'un cours live, le pipeline Celery exécute automatiquement :

```
Cours terminé
    ↓
Génération des présences (auto-marquage depuis les événements WebSocket)
    ↓
Sauvegarde de l'enregistrement (MinIO/S3)
    ↓
Publication dans l'espace élève
    ↓
Envoi des notifications aux élèves
```

---

## Sécurité

- Mots de passe hachés avec bcrypt
- Tokens JWT à courte durée (30 min) + Refresh tokens (7 jours)
- RBAC — chaque endpoint vérifie le rôle ET les permissions
- CORS configuré sur les origines autorisées uniquement
- Validation des données avec Pydantic (v2)
- Variables sensibles dans `.env` (jamais commitées)

---

## Changelog

### v0.1.0 — 10/05/2026 — MVP Initial
- **Backend** : Auth JWT + RBAC, modules Cours/Sessions/Inscriptions, Devoirs/Soumissions/Notes, Présences auto, Enregistrements, Paiements/Factures, Notifications
- **Frontend** : Next.js 16, 4 espaces (Admin, Professeur, Élève, Vendeur), Login/Register, Dashboards par rôle, Sidebar/TopBar/StatsCard
- **Infra** : Docker Compose (PostgreSQL, Redis, MinIO, Celery), Alembic migrations, WebSocket manager (notifications + WebRTC signaling)
- **Sécurité** : bcrypt, JWT, CORS, validation Pydantic, aucune clé en dur

# CLAUDE.md — Contexte projet pour assistants IA

Ce fichier est lu automatiquement par Claude Code au démarrage. Il décrit le projet, les conventions, et les pièges à éviter. Pour le setup d'installation, voir [SETUP.md](SETUP.md).

---

## Le projet en une phrase

Plateforme EdTech (cours en ligne) avec trois types d'utilisateurs — **élèves, enseignants, administrateurs** — gérant des cours organisés par niveau, des chapitres, des leçons, des quiz, des présences et des paiements.

---

## Stack technique

### Backend (`backend/`)

- **Framework** : FastAPI
- **Python** : 3.10 ou 3.11
- **ORM** : SQLAlchemy 2 **async** (avec `asyncpg`)
- **Migrations** : Alembic (mode sync via `psycopg2`)
- **Auth** : JWT (access + refresh tokens), bcrypt pour les mots de passe
- **Tâches asynchrones** : Celery + Redis
- **Stockage fichiers** : MinIO (S3-compatible)
- **Validation** : Pydantic v2

### Frontend (`frontend/`)

- **Framework** : Next.js 16 (App Router)
- **React** : 18
- **Langage** : TypeScript
- **Styling** : TailwindCSS + Radix UI primitives
- **State global** : Zustand (`frontend/store/`)
- **Client API** : fetch wrapper custom dans `frontend/services/api.ts`

### Infrastructure

- **Base de données** : PostgreSQL 16 sur **Neon (cloud)** — voir SETUP.md
- **Cache + broker** : Redis 7 (local)
- **Fichiers** : MinIO (local)

---

## Structure du repo

```text
backend/
  app/
    api/
      router.py              # routeur principal /api/v1
      routes/                # endpoints par domaine
      dependencies/          # auth dependencies
    core/
      config/settings.py     # Pydantic settings (lit backend/.env)
      database/session.py    # SQLAlchemy engine async + sync
      security/jwt.py        # création/validation JWT
      permissions/rbac.py    # vérifs de rôles
    modules/
      auth/, users/, courses/, homework/, attendance/,
      notifications/, payments/, admin/, analytics/,
      live_classes/, recordings/, vendors/, settings/
      # chaque module = models.py + schemas.py + service.py
    websocket/               # endpoints WebSocket
    tasks/                   # Celery worker + tasks
  alembic/
    versions/                # migrations
  requirements/
    base.txt, dev.txt
  .env.example
  .env                       # gitignored — à créer manuellement

frontend/
  app/                       # Next.js App Router
    (auth)/auth/login, register
    admin/                   # pages admin
    teacher/                 # pages enseignant
    student/                 # pages élève
    vendor/                  # pages fournisseur
  components/
    dashboard/, learning/, ui/
  services/api.ts            # client HTTP centralisé
  store/                     # stores Zustand
  types/                     # types TypeScript partagés

scripts/
  db/create_admin.sql        # seed admin SQL fallback
  linux/start.sh             # script de démarrage tout-en-un

docs/                        # documentation détaillée (historique)
docker-compose.yml           # services locaux (Redis, MinIO, etc.)
SETUP.md                     # guide d'installation complet
```

---

## État actuel du projet (à mettre à jour si ça évolue)

- **Base de données** : Neon (cloud), partagée entre tous les PC du dev. **Ne pas relancer `alembic upgrade head` ni le seed admin sur un PC qui n'est pas le premier**.
- **Branche de travail** : `master`
- **Branche principale** : `main`
- **Repo GitHub** : publié sur `origin` → <https://github.com/AbdelmalekAbed/Platforme-educatif-> (branche de dev `master`).
- **Données** : test data, mais l'utilisateur migrera bientôt vers de vraies données (raison du choix Neon).
- **Contenu 6ème** : préparé en base le 2026-06-06 via `scripts/db/seed_6eme_courses.py` depuis `cours/6ème/`. **Toute** l'arborescence du curriculum est créée : **16 cours** (= toutes les matières, sous-dossiers directs de `6ème/`, même vides), **26 chapitres** (= toutes les notions, y compris vides), **62 PDF** copiés dans `backend/uploads/`. Seuls les PDF commençant par `6eme` deviennent des ressources (kinds `pdf`/`fiche`/`correction`). Les cours sans notion (0 chapitre) et les notions sans PDF (0 ressource) sont des **placeholders** : il suffira d'ajouter les dossiers/PDF puis de relancer le script. **Idempotent (upsert)** : identifie cours par (grade_level, titre), chapitre par (course_id, titre), ressource par (chapter_id, kind) ; ne recrée/recopie jamais l'existant (progression préservée). `--replace` reconstruit tout (destructif). `--dry-run` pour un aperçu.

### Refonte profil élève (en cours — démarrée 2026-06-04)

Découpage en 4 lots :

1. **Lot 1 — schéma + migration** ✅ **appliqué sur Neon (2026-06-06, depuis le PC perso)**
   - Module `backend/app/modules/users/parent_models.py` : `ParentContact`, `ParentNotifPrefs`, enums `ParentRelation` (`pere`/`mere`/`tuteur_legal`/`autre`) et `NotifChannel` (`email`/`sms`/`both`).
   - `StudentProfile` enrichi : `school_level`, `school_name`, `city`, `preferred_language`, `gender` + `@hybrid_property is_minor` calculé depuis `date_of_birth` (default `True` si date inconnue, prudent côté flux parent).
   - Token de vérif parent stocké en **hash sha256** (colonne `verification_token_hash`, UNIQUE).
   - Contrainte partielle unique : au plus 1 `is_primary=true` par élève (index `uq_parent_contacts_primary_per_student`).
   - Migration en **2 étapes** : `d1e2f3a4b5c6` (ajout + backfill non destructif) puis `d2e3f4a5b6c7` (drop des colonnes plates legacy `grade_level`, `parent_name`, `parent_phone`, `parent_email`).
   - Chaîne alembic actuelle : `c8d4f1e9a302 → d1e2 → d2e3 → e3f4 → f4a5 (head)`.
   - **Modèles SQLAlchemy nettoyés** : les 4 colonnes legacy sont retirées de `models.py` et de `auth/schemas.py` (`StudentProfileResponse`, `StudentProfileUpdate`).
2. **Lot 2 — API + permissions** ✅ **livré (2026-06-06)** — testé live contre Neon
   - `core/permissions/field_acl.py` : matrice champ-par-champ avec 4 `Actor` (`student_self`/`parent_of`/`teacher`/`admin`) et 4 `FieldAction` (`none`/`read`/`write`/`reset_only`). 16 champs gérés. `filter_readable` est une **scope-list** (les champs hors matrice — `id`, `user_id`, `is_minor`, `enrollments` — restent visibles par défaut).
   - `modules/users/student_schemas.py` : `StudentProfileReadFull`, `StudentProfileAdminUpdate`, `StudentProfileSelfUpdate`, `ParentContactCreate/Update/Read`, `NotifPrefsRead/Update`, `EnrollmentSummary`, `FieldACLSummary`.
   - `modules/users/student_service.py` : invariants métier centralisés (max 2 contacts, reset `is_primary` des autres dans la même tx, refus suppression dernier contact si mineur, `get_invoice_recipients`, `can_deactivate_student`).
   - `api/dependencies/student.py` : `resolve_student_actor` (ADMIN > STUDENT_SELF > TEACHER si lié à un cours) et `get_my_student_profile`.
   - `api/routes/students.py` : 12 routes sous `/students/*` et `/parent-contacts/*` (CRUD profil + contacts + ACL summary + stub 501 `resend-verification` pour le lot 3). `main.py` patché pour le trailing slash hack.
   - `api/routes/admin.toggle_user_active` patché : refuse la désactivation d'un élève mineur sans contact parental vérifié (HTTP 400 `minor_requires_verified_parent`) et renvoie `parent_notified_email` quand applicable.
   - **Sous-lot 2bis** différé : sécurité compte (changement mot de passe avec ancien, sessions actives, 2FA). Nécessite migrations `user_sessions` + `user_2fa` + lib `pyotp`. Sera traité après le lot 4 ou en parallèle si demandé.
3. **Lot 3 — flux vérification parent** (email tokenisé 48h) ⏳ à venir
   - À implémenter : `core/email/sender.py` (wrapper `emails==0.6` + Jinja2), `users/email_tokens.py` (modèle `EmailToken` + migration), `verification_service.py`, `routes/parent_portal.py` (endpoints publics signés JWT court).
4. **Lot 4 — UI Next.js** (`/student/profile`, `/parent/portal`) ⏳ à venir

### Décisions d'architecture actées pour cette refonte

- `is_minor` = `@hybrid_property` (pas de colonne stockée → pas de CRON anniversaire).
- `date_of_birth` conservé tel quel (pas renommé en `birth_date`).
- Backfill `parent_contacts` : skip les élèves sans `parent_email` (pas de placeholder).
- Le parent **n'a pas de compte User** — accès via lien tokenisé reçu par email.
- Tokens email stockés en **hash sha256**, jamais en clair.
- Matrice de permissions à exposer côté API (`GET /students/me/field-permissions`) pour éviter drift front/back.
- Refresh tokens stateful en DB (table `user_sessions` à venir au lot 2) pour permettre "révoquer une session".
- Max 2 contacts parentaux : refus dur HTTP 400 si dépassé.
- Suppression du dernier contact d'un mineur : interdite.

---

## Commandes courantes

### Démarrer le projet (ordre)

```bash
# 1. Services locaux (Redis + MinIO)
docker compose up -d redis minio

# 2. Backend (terminal 1)
cd backend
.\venv\Scripts\Activate.ps1     # Windows PowerShell
uvicorn app.main:app --reload --port 8000

# 3. Frontend (terminal 2)
cd frontend
npm run dev
```

### Migrations

```bash
# Créer une migration depuis les modèles
cd backend
alembic revision --autogenerate -m "description"

# Appliquer les migrations en attente
alembic upgrade head

# Revenir en arrière d'une migration
alembic downgrade -1
```

### Tests

```bash
cd backend
pytest
```

Sécurité `/uploads` (sans pytest installé dans le venv, lancement standalone) :

```bash
# venv Linux/WSL — cf. piège #9
wsl -e bash -lc "cd /mnt/c/Users/aabed/Desktop/Platform/backend && ./venv/bin/python tests/test_uploads_security.py"
```

### Lint frontend

```bash
cd frontend
npm run lint
```

---

## Conventions de code

### Backend

- **Async partout** : les routes, services et requêtes DB sont `async def`. Pas de mélange sync/async.
- **Pattern par module** : `models.py` (SQLAlchemy) + `schemas.py` (Pydantic) + `service.py` (logique métier) + endpoints dans `app/api/routes/`.
- **Imports absolus** depuis `app.` (jamais `..` relatifs).
- **IDs** : UUID via `gen_random_uuid()` côté Postgres.
- **Auth** : dépendance FastAPI `Depends(get_current_user)` sur les routes protégées.
- **Permissions** : décorateurs / dépendances RBAC dans `core/permissions/rbac.py`.

### Frontend

- **App Router** Next.js (pas Pages Router).
- **Composants UI** : Radix primitives + Tailwind, dans `components/ui/`.
- **Client API** : passer **toujours** par `services/api.ts` (gère JWT refresh automatiquement).
- **State serveur** : appels API directs avec gestion locale du loading/error (pas de TanStack Query pour l'instant).
- **State client** : Zustand pour le global (auth, platform settings), `useState` pour le local.
- **Routes par rôle** : `/admin`, `/teacher`, `/student`, `/vendor` — chaque layout vérifie le rôle.

### Git

- Commits en français, format libre mais descriptif.
- Branche `master` pour le dev, `main` pour les releases (à confirmer avec l'utilisateur).
- Pas de force-push, pas de `--no-verify`.

---

## Pièges connus

1. **SSL Neon** : `DATABASE_URL` (asyncpg) utilise `?ssl=require`, **mais** `DATABASE_URL_SYNC` (psycopg2) utilise `?sslmode=require`. Une seule lettre de différence — facile à louper.

2. **Migrations parallèles** : ne jamais lancer `alembic upgrade head` simultanément depuis deux PC sur la même base Neon. Choisir un PC "maître".

3. **`backend/.env` est gitignored** : doit être recréé manuellement sur chaque PC depuis `backend/.env.example`.

4. **Neon free tier** : suspend après 5 min d'inactivité → première requête lente (1-2s). Normal.

5. **Wake-up Neon en CI/headless** : Neon peut être indisponible quelques secondes le matin → prévoir un retry sur la première requête en prod. `session.py` configure désormais `pool_pre_ping=True` + `pool_recycle=300` pour jeter/tester les connexions mortes après une suspension (évite le freeze de la 1ère requête au réveil).

6. **Frontend ↔ backend** : le frontend tape sur `/api/v1` en relatif (pas d'env var). Si tu changes le port backend, il faut configurer un proxy Next.js dans `next.config.js`.

7. **WSL + VPN d'entreprise** : sur le PC pro, `WSL_PAC_URL` est injecté par le VPN Sofrecom et peut casser Node/Claude Code quand le VPN est off. Pas un souci sur PC perso.

8. **`env_file=".env"` est relatif au CWD** : `Settings` (`core/config/settings.py`) lit `.env` **relativement au répertoire d'exécution**. Le backend est lancé depuis `backend/` → il charge `backend/.env` (Neon). Un script lancé depuis la **racine** ne trouve pas de `.env` et retombe sur les **defaults `localhost:5432`** → il écrit dans une base locale fantôme, pas Neon. Tout script DB doit donc `os.chdir(backend/)` avant d'importer `app.core.config` (cf. `scripts/db/seed_6eme_courses.py`), ou être lancé depuis `backend/`.

9. **Le venv est un venv WSL/Linux** (`backend/venv/bin/`, pas `Scripts/`) : l'exécuter depuis Windows/MinGW échoue. Lancer les scripts via `wsl -e bash -lc "./backend/venv/bin/python …"`.

10. **Setup de dev (PC perso) : frontend sous Windows, backend sous WSL.** Le projet vit sur `/mnt/c` ; lancer Next **depuis WSL** sur `/mnt/c` est très lent (compile ~67 s, file-watching cross-OS). Le frontend tourne donc **nativement sous Windows** (PowerShell : `cd frontend; npm run dev` → démarre en ~2 s). `frontend/node_modules` contient les binaires **win32** (`@next/swc-win32`) : il ne tourne **plus** sous WSL sauf à refaire un `npm install` côté WSL (qui re-supprimerait les binaires Windows — choisir une seule plateforme). Le **backend reste sous WSL** (venv Linux, pas de Python installé sous Windows ; ce n'est pas le goulot). Le frontend Windows atteint le backend WSL via `localhost:8000` (WSL2 forwarde localhost). Si Next refuse de démarrer (« Another next dev server is already running »), un serveur WSL tourne encore ou un verrou `.next` est obsolète → couper l'ancien, au besoin `Remove-Item -Recurse -Force frontend/.next`.

11. **`/uploads` n'est PLUS un mount statique public** (corrigé 2026-06-30). Les fichiers (PDF, vidéos, miniatures) sont servis par une route auth-gated `GET /uploads/{path}` (`app/api/routes/uploads.py`) qui **exige un token signé** dans l'URL (`?exp=&token=`). Le token est un HMAC-SHA256 (`app/core/security/media_tokens.py`, clé `SECRET_KEY`, validité 4–8 h — `DEFAULT_TTL` 4 h + bucketing par fenêtre de 4 h pour rester cacheable). Une URL `/uploads/...` **brute** (sans token) renvoie **403** — même chose pour un token trafiqué/expiré, et une tentative de path-traversal renvoie **404**. Conséquences pratiques :
    - Toute URL `/uploads/...` renvoyée au front doit passer par `sign_media_url()`. C'est déjà fait : `field_serializer` sur `ChapterResourceResponse.url`, `CourseResponse.thumbnail_url`, `HomeworkResponse/SubmissionResponse.attachment_url`, + appels manuels dans les endpoints qui renvoient des **dicts** (`content.py` items + miniatures, `admin.py` miniatures). **Si tu ajoutes un nouvel endpoint qui expose une URL `/uploads/...`, pense à la signer**, sinon l'élément casse côté UI (403).
    - L'upload (`POST /content/uploads`) renvoie l'URL **brute** (stockée telle quelle en DB) ; la signature est appliquée **à la lecture** seulement (sinon on stockerait un `exp` périmé).
    - `SECRET_KEY` protège tous les fichiers : avec une clé connue, les tokens sont forgeables. Le fix **refuse donc de démarrer** (`settings.py`, validator) si `SECRET_KEY` est un placeholder connu ou fait < 32 caractères **quand `DEBUG=False`**. En prod : `openssl rand -hex 32`. En local (`DEBUG=True`) le placeholder reste toléré.
    - Pas de gating par *enrollment* : le modèle d'autorisation du contenu est « tout utilisateur authentifié » (les endpoints `content.py` ne vérifient pas l'enrollment). Le fix aligne les fichiers sur ce même niveau.

---

## Identifiants par défaut

- **Admin** : `admin@edtech.com` / `Admin123456`
- **Neon connection string** : stockée localement dans `backend/.env` uniquement (gitignored)

---

## Quand l'utilisateur te demande de l'aider

- **"Installe / lance le projet"** → suis [SETUP.md](SETUP.md) section par section. Demande confirmation à chaque étape si tu n'es pas sûr.
- **"Ajoute une fonctionnalité X"** → identifie le module concerné dans `backend/app/modules/`, suis le pattern existant (models + schemas + service + routes).
- **"Modifie un modèle DB"** → modifie le `models.py`, génère la migration avec `alembic revision --autogenerate`, applique avec `alembic upgrade head` (mais préviens : ça touche la base Neon partagée).
- **"Crée une page frontend"** → suis le pattern Next.js App Router, place la page dans le bon dossier de rôle (`admin/`, `teacher/`, `student/`).
- **"J'ai un bug"** → demande le message d'erreur exact, lis le code concerné avant de proposer un fix.

Toujours rester court dans tes réponses : explique seulement ce qui est non-évident.

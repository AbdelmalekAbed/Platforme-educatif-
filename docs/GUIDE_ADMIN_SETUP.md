# 🔐 Guide de Création du Compte Admin

## Informations du Compte Admin

| Propriété | Valeur |
|-----------|--------|
| **Email** | admin@edtech.com |
| **Mot de passe** | Admin123456 |
| **Rôle** | Admin |
| **Accès** | Tous les espaces (Admin, Professeurs, Étudiants, Vendeurs) |

---

## 📋 Méthode 1: Via Docker (RECOMMANDÉE)

### Étape 1: Démarrer les services
```bash
docker-compose up -d
```

Attendez que tous les services soient prêts (DB, Redis, Backend, etc.)

### Étape 2: Créer le compte admin
```bash
docker-compose exec backend python seed_admin.py
```

### Attendu:
```
🔐 Création du compte admin...
------------------------------------------------------------
✅ Compte admin créé avec succès!
------------------------------------------------------------
📋 Informations de connexion admin:
   Email: admin@edtech.com
   Mot de passe: Admin123456
   Rôle: admin
   ID: [UUID généré]
------------------------------------------------------------
```

---

## 📋 Méthode 2: Installation Locale (Sans Docker)

### Étape 1: Configurer l'environnement
```bash
# Aller au dossier backend
cd backend

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements/base.txt
```

### Étape 2: Configurer la base de données
```bash
# Appliquer les migrations
alembic upgrade head
```

### Étape 3: Créer le compte admin
```bash
# Retourner au répertoire racine
cd ..

# Exécuter le script
python seed_admin.py
```

---

## 🔧 Méthode 3: Via SQL Direct (Développement)

Si vous avez accès à PostgreSQL directement:

```bash
# Connexion à la base de données
psql -U postgres -d edtech

# Générer le hash du mot de passe (dans Python):
python -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('Admin123456'))"

# Puis exécuter (remplacez le hash):
INSERT INTO users (
    id, email, hashed_password, first_name, last_name, 
    phone, role, is_active, is_verified, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'admin@edtech.com',
    '[HASH_BCRYPT_ICI]',
    'Admin',
    'Platform',
    '+1234567890',
    'admin',
    true,
    true,
    now(),
    now()
) ON CONFLICT (email) DO NOTHING;
```

---

## 🌐 Accès à l'Interface Admin

Après création du compte, accédez à:

- **Frontend**: http://localhost:3000
- **API Swagger**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)

**Identifiants de connexion:**
- Email: `admin@edtech.com`
- Mot de passe: `Admin123456`

---

## ✅ Vérification

Pour vérifier que le compte admin a été créé:

```bash
# Via Docker:
docker-compose exec db psql -U postgres -d edtech -c "SELECT email, role, is_active FROM users WHERE email = 'admin@edtech.com';"

# Ou directement avec psql (si PostgreSQL est localement accessible):
psql -U postgres -d edtech -c "SELECT email, role, is_active FROM users WHERE email = 'admin@edtech.com';"
```

Résultat attendu:
```
       email       | role  | is_active
-------------------+-------+-----------
admin@edtech.com   | admin | t
(1 row)
```

---

## 🔑 Permissions Admin

Le rôle Admin a accès à **toutes les permissions**:

- ✅ Gestion des utilisateurs (CRUD)
- ✅ Gestion des cours
- ✅ Gestion des devoirs
- ✅ Gestion de la présence
- ✅ Gestion des enregistrements
- ✅ Gestion des paiements
- ✅ Gestion des notifications
- ✅ Accès aux analytics complètes
- ✅ Tous les espaces (Admin, Professeurs, Étudiants, Vendeurs)

---

## ❌ Troubleshooting

### Erreur: "Python not found"
- Installez Python 3.9+ depuis [python.org](https://python.org)
- Assurez-vous qu'il est dans votre PATH

### Erreur: "Cannot connect to database"
1. Vérifiez que PostgreSQL est en cours d'exécution
2. Vérifiez les identifiants (par défaut: postgres/postgres)
3. Vérifiez que la base de données `edtech` existe

### Erreur: "Table users does not exist"
- Exécutez les migrations: `alembic upgrade head`

### Le compte existe déjà
- Le script affichera: "ℹ️ Compte admin existe déjà"
- C'est normal! Vous pouvez maintenant vous connecter

---

## 📝 Notes

- Les identifiants sont définis dans `INSTRUCTIONS.md`
- Le mot de passe est hashé en bcrypt avant stockage
- Le compte est créé comme `is_active=true` et `is_verified=true`
- Les autres comptes de test (prof, étudiant, vendeur) peuvent être créés de la même manière

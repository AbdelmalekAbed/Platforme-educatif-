-- ========================================
-- EdTech Platform - Création admin (SQL fallback)
-- ========================================
-- Utilisation:
--   psql -U postgres -d edtech -f scripts/db/create_admin.sql
--
-- Note: Préférez seed_admin.py qui génère le hash bcrypt correct.
--       Ce fichier est un fallback si Python n'est pas disponible.
--
-- Pour générer le hash bcrypt du mot de passe :
--   python -c "from passlib.context import CryptContext; \
--              ctx = CryptContext(schemes=['bcrypt'], deprecated='auto'); \
--              print(ctx.hash('Admin123456'))"
-- Puis remplacez la valeur hashed_password ci-dessous.
-- ========================================

INSERT INTO users (
    id,
    email,
    hashed_password,
    first_name,
    last_name,
    phone,
    role,
    is_active,
    is_verified,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'admin@edtech.com',
    '$2b$12$REMPLACEZ_PAR_LE_HASH_GENERE_CI_DESSUS',
    'Admin',
    'Platform',
    '+1234567890',
    'ADMIN',
    true,
    true,
    now(),
    now()
) ON CONFLICT (email) DO NOTHING;

SELECT id, email, role, is_active FROM users WHERE email = 'admin@edtech.com';

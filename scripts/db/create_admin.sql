-- ========================================
-- EdTech Platform - Création admin (SQL fallback)
-- ========================================
-- Utilisation:
--   psql -U postgres -d edtech -f scripts/db/create_admin.sql
--
-- Identifiants par défaut:
--   Email    : admin@edtech.com
--   Password : Admin123456
--
-- Note: Préférez seed_admin.py si Python est disponible.
--       Pour régénérer le hash bcrypt d'un autre mot de passe :
--   python -c "from passlib.context import CryptContext; \
--              ctx = CryptContext(schemes=['bcrypt'], deprecated='auto'); \
--              print(ctx.hash('VotreMotDePasse'))"
-- Puis remplacez la valeur hashed_password ci-dessous.
-- ========================================

-- gen_random_uuid() est natif depuis PostgreSQL 13 ; pgcrypto le fournit sur les versions antérieures.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

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
    -- Hash bcrypt de "Admin123456" (cost=12)
    '$2b$12$/Q7aNKyGmjFK6eUP5oHYHuO56kUdaSuik9U9cICWo17TSHQodmcze',
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

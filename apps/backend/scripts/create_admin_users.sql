-- Script to create admin users
-- Run this script to create admin and super admin users

-- 1. Admin user for "familia" company
-- Email: admin@familia.com
-- Password: AdminFamilia123
-- Role: admin
-- Company: familia

INSERT INTO "user" (
    id,
    email,
    password,
    first_name,
    last_name,
    rut,
    role,
    company,
    created_at
) VALUES (
    gen_random_uuid(),
    'admin@familia.com',
    '$2b$12$K08TdWtb4UekfnWXFEvn5eeJsrW/tA6DnASzR199jZtY0TpXOWC/i',
    'Admin',
    'Familia',
    '11111111-1',
    'admin',
    'familia',
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- 2. Super Admin user (global access)
-- Email: superadmin@sistema.com
-- Password: SuperAdmin123
-- Role: superadmin
-- Company: sistema

INSERT INTO "user" (
    id,
    email,
    password,
    first_name,
    last_name,
    rut,
    role,
    company,
    created_at
) VALUES (
    gen_random_uuid(),
    'superadmin@sistema.com',
    '$2b$12$zZYECtVqBf/sXzubP5rWT.B.jxTS.ZBu2mlrKHMWgDoWFsSilVFde',
    'Super',
    'Admin',
    '22222222-2',
    'superadmin',
    'sistema',
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Verify users were created
SELECT 
    email,
    first_name,
    last_name,
    role,
    company,
    created_at
FROM "user"
WHERE email IN ('admin@familia.com', 'superadmin@sistema.com')
ORDER BY role;

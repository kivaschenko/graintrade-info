-- ===========================
-- 1. ROLES
-- ===========================

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_owner') THEN
      CREATE ROLE app_owner LOGIN PASSWORD 'strong_owner_password';
   END IF;
END
$$;

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
      CREATE ROLE app_user LOGIN PASSWORD 'strong_app_password';
   END IF;
END
$$;


-- ===========================
-- 2. DATABASE
-- ===========================

DROP DATABASE IF EXISTS myapp;

CREATE DATABASE myapp OWNER app_owner;


-- ===========================
-- 3. CONNECT TO DATABASE
-- ===========================

\connect myapp


-- ===========================
-- 4. SCHEMA CONFIG
-- ===========================

ALTER SCHEMA public OWNER TO app_owner;

GRANT USAGE ON SCHEMA public TO app_user;

-- Если FastAPI не должен создавать объекты — CREATE не даём
-- GRANT CREATE ON SCHEMA public TO app_user;


-- ===========================
-- 5. DEFAULT PRIVILEGES
-- КЛЮЧЕВОЙ БЛОК
-- ===========================

ALTER DEFAULT PRIVILEGES FOR ROLE app_owner
IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

ALTER DEFAULT PRIVILEGES FOR ROLE app_owner
IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app_user;

ALTER DEFAULT PRIVILEGES FOR ROLE app_owner
IN SCHEMA public
GRANT EXECUTE ON FUNCTIONS TO app_user;


-- ===========================
-- 6. SAFETY: SEARCH PATH
-- ===========================

ALTER ROLE app_user SET search_path = public;
ALTER ROLE app_owner SET search_path = public;
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis_topology CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop table if it exists and create it
DROP TABLE IF EXISTS categories CASCADE;

-- Categoy table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    ua_name VARCHAR(50),
    ua_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Drop indexes if they exist
DROP INDEX IF EXISTS categories_name_idx;
DROP INDEX IF EXISTS categories_ua_name_idx;

-- Create indexes
CREATE INDEX categories_name_idx ON categories (name);
CREATE INDEX categories_ua_name_idx ON categories (ua_name);

-- Drop table if it exists and create it
DROP TABLE IF EXISTS items CASCADE;

-- Items table
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR NOT NULL DEFAULT uuid_generate_v4(),
    category_id INTEGER NOT NULL,
    offer_type VARCHAR(50) NOT NULL,  -- sell, buy, exchange
    title VARCHAR(150) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    amount INTEGER NOT NULL,
    measure VARCHAR(10) NOT NULL,
    terms_delivery VARCHAR(50) NOT NULL,
    country VARCHAR(150) NOT NULL,
    region VARCHAR(150),
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (category_id) REFERENCES categories (id)
    );

-- Drop indexes if they exist
DROP INDEX IF EXISTS items_geom_idx;
DROP INDEX IF EXISTS items_country_idx;
DROP INDEX IF EXISTS items_region_idx;
DROP INDEX IF EXISTS items_created_at_idx;
DROP INDEX IF EXISTS items_offer_type_idx;

-- Create indexes
CREATE INDEX items_offer_type_idx ON items (offer_type);
CREATE INDEX items_geom_idx ON items USING GIST (geom);
CREATE INDEX items_country_idx ON items (country);
CREATE INDEX items_region_idx ON items (region);
CREATE INDEX items_created_at_idx ON items (created_at);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    hashed_password VARCHAR(100) NOT NULL,
    disabled BOOLEAN DEFAULT FALSE,
    map_views INTEGER DEFAULT 0
);

ALTER TABLE IF EXISTS public.users
    ADD CONSTRAINT email_unique_constraint UNIQUE (email);
ALTER TABLE IF EXISTS public.users
    ADD CONSTRAINT users_username_unique_constraint UNIQUE (username);

-- Create items_users table
CREATE TABLE IF NOT EXISTS items_users (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (item_id) REFERENCES items (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create tarifs table
CREATE TABLE IF NOT EXISTS tarifs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 10.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    scope VARCHAR(100) NOT NULL DEFAULT 'basic',
    terms VARCHAR(50) NOT NULL DEFAULT 'monthly',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Drop indexes if they exist
DROP INDEX IF EXISTS tarifs_scope_idx;
DROP INDEX IF EXISTS tarifs_terms_idx;

-- Create indexes
CREATE INDEX tarifs_scope_idx ON tarifs (scope);
CREATE INDEX tarifs_terms_idx ON tarifs (terms);

-- Create table for user's subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tarif_id INTEGER NOT NULL,
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (tarif_id) REFERENCES tarifs (id)
);

-- Create table for user's payments
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tarif_id INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (tarif_id) REFERENCES tarifs (id)
);

-- Drop the function if it exists
DROP FUNCTION IF EXISTS update_geometry_from_lat_lon() CASCADE;

CREATE OR REPLACE FUNCTION update_geometry_from_lat_lon()
RETURNS trigger AS
$$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;

-- Create or update the trigger to call the function
CREATE OR REPLACE TRIGGER update_geom_trigger
BEFORE INSERT OR UPDATE ON items
FOR EACH ROW
EXECUTE FUNCTION update_geometry_from_lat_lon();
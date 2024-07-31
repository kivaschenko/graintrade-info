CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis_topology CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder CASCADE;

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
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
    created_at TIMESTAMP DEFAULT NOW()
);

-- Drop indexes if they exist
DROP INDEX IF EXISTS items_geom_idx;
DROP INDEX IF EXISTS items_country_idx;
DROP INDEX IF EXISTS items_region_idx;
DROP INDEX IF EXISTS items_created_at_idx;

-- Create indexes
CREATE INDEX items_geom_idx ON items USING GIST (geom);
CREATE INDEX items_country_idx ON items (country);
CREATE INDEX items_region_idx ON items (region);
CREATE INDEX items_created_at_idx ON items (created_at);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    full_name VARCHAR(100),
    hashed_password VARCHAR(100) NOT NULL,
    disabled BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS items_users (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (item_id) REFERENCES items (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
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
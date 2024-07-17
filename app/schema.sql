CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS postgis_sfcgal;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

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
    created_at TIMESTAMP DEFAULT NOW()
);

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

-- CREATE OR REPLACE FUNCTION update_geometry_from_lat_lon()
-- RETURNS void AS
-- $$
-- BEGIN
--     UPDATE items
--     SET geometry = ST_MakePoint(longitude, latitude)::point;
-- END;
-- $$
-- LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_geometry_from_lat_lon()
RETURNS void AS
$$
BEGIN
    UPDATE items
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);
END;
$$
LANGUAGE plpgsql;

SELECT update_geometry_from_lat_lon();
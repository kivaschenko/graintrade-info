-- Migration script to add address field to existing items table
-- This script is safe to run on existing database

-- Add address column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'items' 
        AND column_name = 'address'
    ) THEN
        ALTER TABLE items ADD COLUMN address VARCHAR(300);
        RAISE NOTICE 'Column address added to items table';
    ELSE
        RAISE NOTICE 'Column address already exists in items table';
    END IF;
END $$;

-- Make latitude and longitude nullable if they aren't already
DO $$
BEGIN
    -- Check and alter latitude
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'items' 
        AND column_name = 'latitude'
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE items ALTER COLUMN latitude DROP NOT NULL;
        RAISE NOTICE 'Column latitude is now nullable';
    END IF;

    -- Check and alter longitude
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'items' 
        AND column_name = 'longitude'
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE items ALTER COLUMN longitude DROP NOT NULL;
        RAISE NOTICE 'Column longitude is now nullable';
    END IF;
END $$;

-- Update the geometry trigger function to handle NULL coordinates
CREATE OR REPLACE FUNCTION update_geometry_from_lat_lon()
RETURNS trigger AS
$$
BEGIN
    -- Only update geometry if latitude and longitude are provided
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;

-- Add index on address for faster search (optional but recommended)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE tablename = 'items' 
        AND indexname = 'items_address_idx'
    ) THEN
        CREATE INDEX items_address_idx ON items USING gin(to_tsvector('simple', address));
        RAISE NOTICE 'Index items_address_idx created';
    ELSE
        RAISE NOTICE 'Index items_address_idx already exists';
    END IF;
END $$;

-- RAISE NOTICE 'Migration completed successfully!';

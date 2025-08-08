-- This script is used to initialize the database for the application.
-- It creates the necessary tables, indexes, and functions.
-- It also ensures that the PostGIS extension is enabled for spatial data handling.
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis_topology CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------
-- Categories related tables |
-- ---------------------------
DROP TABLE IF EXISTS categories CASCADE;

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    ua_name VARCHAR(50),
    ua_description TEXT,
    parent_category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parent_categories (
    name VARCHAR(50) PRIMARY KEY,
    ua_name VARCHAR(50) NOT NULL
);

-- Indexes
CREATE INDEX categories_name_idx ON categories (name);
CREATE INDEX categories_ua_name_idx ON categories (ua_name);
CREATE INDEX idx_categories_parent ON categories(parent_category);

-- Constraints
ALTER TABLE categories
ADD CONSTRAINT fk_parent_category 
FOREIGN KEY (parent_category) 
REFERENCES parent_categories(name)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- Drop table if it exists and create it
DROP TABLE IF EXISTS items CASCADE;

-- Items table
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT uuid_generate_v4(),
    category_id INTEGER NOT NULL,
    offer_type VARCHAR(50) NOT NULL,  -- sell, buy, exchange
    title VARCHAR(150) NOT NULL,
    description VARCHAR(600),  -- Description of the item
    price DECIMAL(10, 2) NOT NULL CONSTRAINT positive_price CHECK (price>0),
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
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
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

-- Users and authentication related tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    hashed_password VARCHAR(100) NOT NULL,
    disabled BOOLEAN DEFAULT FALSE,
    CONSTRAINT email_unique_constraint UNIQUE (email),
    CONSTRAINT users_username_unique_constraint UNIQUE (username)
);

CREATE TABLE IF NOT EXISTS items_users (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (item_id) REFERENCES items (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Subscription related tables
CREATE TABLE IF NOT EXISTS tarifs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 5.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    scope VARCHAR(100) NOT NULL DEFAULT 'basic',
    terms VARCHAR(50) NOT NULL DEFAULT 'monthly',
    items_limit INTEGER CONSTRAINT positive_items_limit CHECK (items_limit>=0),
    map_views_limit INTEGER CONSTRAINT positive_map_views_limit CHECK (map_views_limit>=0),
    geo_search_limit INTEGER CONSTRAINT positive_geo_search_limit CHECK (geo_search_limit>=0),
    navigation_limit INTEGER CONSTRAINT positive_navigation_limit CHECK (navigation_limit>=0),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT tarifs_name_unique_constraint UNIQUE (name),
    CONSTRAINT tarifs_scope_unique_constraint UNIQUE (scope)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    tarif_id INTEGER REFERENCES tarifs(id) ON DELETE SET NULL,
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    order_id VARCHAR(50) NOT NULL,
    payment_id INTEGER,
    items_count INTEGER DEFAULT 0,
    map_views INTEGER DEFAULT 0,
    geo_search_count INTEGER DEFAULT 0,
    navigation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX tarifs_scope_idx ON tarifs (scope);
CREATE INDEX tarifs_terms_idx ON tarifs (terms);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER UNIQUE NOT NULL,
    order_id UUID NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    amount INTEGER NOT NULL,  -- Amount in cents
    card_type VARCHAR(20) NOT NULL,
    card_bin INTEGER NOT NULL,
    masked_card VARCHAR(20) NOT NULL,
    payment_system VARCHAR(20) NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    sender_cell_phone VARCHAR(20),
    approval_code VARCHAR(10) NOT NULL,
    response_status VARCHAR(20) NOT NULL,
    tran_type VARCHAR(20) NOT NULL,
    eci VARCHAR(10),
    settlement_amount VARCHAR(20),
    actual_amount VARCHAR(20) NOT NULL,
    order_time TIMESTAMP NOT NULL,
    additional_info JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_payments_payment_id ON payments(payment_id);
CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_order_status ON payments(order_status);
CREATE INDEX idx_payments_created_at ON payments(created_at);
CREATE INDEX idx_payments_sender_email ON payments(sender_email);
CREATE INDEX idx_payments_additional_info ON payments USING gin(additional_info);

-- Add comments
COMMENT ON TABLE payments IS 'Stores payment transaction records from Fondy payment system';
COMMENT ON COLUMN payments.amount IS 'Payment amount in cents';
COMMENT ON COLUMN payments.additional_info IS 'Additional payment details stored as JSON';

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


-- Function to increment item count
CREATE OR REPLACE FUNCTION increment_items_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_current_count INTEGER;
BEGIN
    -- Update the counter and return new value
    UPDATE subscriptions
    SET items_count = items_count + 1
    WHERE user_id = p_user_id
    AND status = 'active'
    AND end_date > NOW()
    RETURNING items_count INTO v_current_count;
    
    RETURN COALESCE(v_current_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to increment map views
CREATE OR REPLACE FUNCTION increment_map_views(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_current_views INTEGER;
BEGIN
    -- Update the counter and return new value
    UPDATE subscriptions
    SET map_views = map_views + 1
    WHERE user_id = p_user_id
    AND status = 'active'
    AND end_date > NOW()
    RETURNING map_views INTO v_current_views;
    
    RETURN COALESCE(v_current_views, 0);
END;
$$ LANGUAGE plpgsql;

-- Functon to increment navigation count
CREATE OR REPLACE FUNCTION increment_navigation_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_current_count INTEGER;
BEGIN
    -- Update the counter and return new value
    UPDATE subscriptions
    SET navigation_count = navigation_count + 1
    WHERE user_id = p_user_id
    AND status = 'active'
    AND end_date > NOW()
    RETURNING navigation_count INTO v_current_count;

    RETURN COALESCE(v_current_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Functon to increment geo_search count
CREATE OR REPLACE FUNCTION increment_geo_search_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_current_count INTEGER;
BEGIN
    -- Update the counter and return new value
    UPDATE subscriptions
    SET geo_search_count = geo_search_count + 1
    WHERE user_id = p_user_id
    AND status = 'active'
    AND end_date > NOW()
    RETURNING geo_search_count INTO v_current_count;

    RETURN COALESCE(v_current_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to decrement item count
CREATE OR REPLACE FUNCTION decrement_items_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_current_count INTEGER;
BEGIN
    -- Update the counter and return new value
    UPDATE subscriptions
    SET items_count = items_count - 1
    WHERE user_id = p_user_id
    AND end_date > NOW()
    RETURNING items_count INTO v_current_count;

    RETURN COALESCE(v_current_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to get current usage
CREATE OR REPLACE FUNCTION get_subscription_usage(p_user_id INTEGER)
RETURNS TABLE (
    items_count INTEGER,
    map_views INTEGER,
    geo_search_count INTEGER,
    navigation_count INTEGER,
    tarif_scope VARCHAR,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.items_count,
        s.map_views,
        s.geo_search_count,
        s.navigation_count,
        t.scope as tarif_scope,
        (s.status = 'active' AND s.end_date > NOW()) as is_active
    FROM subscriptions s
    JOIN tarifs t ON s.tarif_id = t.id
    WHERE s.user_id = p_user_id
    AND s.status = 'active'
    AND s.end_date > NOW();
END;
$$ LANGUAGE plpgsql;

-- Check if the tarifs table is empty
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM tarifs) THEN
	-- Insert default tarifs
	INSERT INTO tarifs (name, description, price, currency, scope, terms, items_limit, map_views_limit, geo_search_limit, navigation_limit)
	VALUES
        ('Free', 'Free probation plan', 0.00, 'EUR', 'free', 'monthly', 5, 10, 10, 10),
	    ('Basic', 'Basic subscription plan', 5.00, 'EUR', 'basic', 'monthly', 25, 100, 100, 100),
        ('Premium', 'Premium subscription plan', 10.00, 'EUR', 'premium', 'monthly', 50, 300, 300, 300),
        ('Pro', 'Pro subscription plan', 25.00, 'EUR', 'pro', 'monthly', 125, 1000, 1000, 1000);
    END IF;
END $$;

DO $$
BEGIN
    -- Check if the parent_categories table is empty
    IF NOT EXISTS (SELECT 1 FROM parent_categories) THEN
        -- Insert default parent categories
        INSERT INTO parent_categories (name, ua_name)
        VALUES 
            ('Grains', 'Зернові'),
            ('Oilseeds', 'Олійні'),
            ('Pulses', 'Бобові'),
            ('Oils', 'Олії'),
            ('Processed products', 'Перероблені продукти'),
            ('Industrial products', 'Промислові продукти'),
            ('Feed products', 'Кормові продукти'),
            ('Other', 'Інше'),
            ('Uncategorized', 'Без категорії');
    END IF;
END $$;

DO $$
BEGIN
    -- First, let's insert new categories that don't exist yet
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Wheat 1st grade') THEN
    -- Insert new categories
    INSERT INTO categories (name, ua_name, parent_category, description, ua_description)
    VALUES
        -- Grains
        ('Wheat 1st grade', 'Пшениця 1 клас', 'Grains', 'First grade wheat, suitable for high-quality flour production.', 'Пшениця 1 клас, придатна для виробництва високоякісного борошна.'),
        ('Wheat 2nd grade', 'Пшениця 2 клас', 'Grains', 'Second grade wheat, used for standard flour.', 'Пшениця 2 клас, використовується для стандартного борошна.'),
        ('Wheat 3rd grade', 'Пшениця 3 клас', 'Grains', 'Third grade wheat, lower quality than first and second grades.', 'Пшениця 3 клас, нижча якість ніж перший і другий класи.'),
        ('Wheat 4th grade', 'Пшениця 4 клас', 'Grains', 'Fourth grade wheat, used for animal feed and lower quality products.', 'Пшениця 4 клас, використовується для кормів тваринам та нижчої якості продуктів.'),
        ('Wheat 5th grade', 'Пшениця 5 клас', 'Grains', 'Fifth grade wheat, lowest quality.', 'Пшениця 5 клас, найнижча якість.'),
        ('Wheat 6th grade', 'Пшениця 6 клас', 'Grains', 'Sixth grade wheat, typically used for animal feed.', 'Пшениця 6 клас, зазвичай використовується для кормів тваринам.'),
        ('Barley', 'Ячмінь', 'Grains', 'Barley grain, used for animal feed and brewing.', 'Ячмінь, використовується для кормів тваринам та пивоваріння.'),
        ('Corn', 'Кукурудза', 'Grains', 'Corn grain, widely used in food and feed industries.', 'Кукурудза, широко використовується в харчовій та кормовій промисловості.'),
        ('Rye', 'Жито', 'Grains', 'Rye grain, used for bread and animal feed.', 'Жито, використовується для хліба та кормів тваринам.'),
        ('Rye 2nd grade', 'Жито 2 клас', 'Grains', NULL, NULL),
        ('Rye 3rd grade', 'Жито 3 клас', 'Grains', NULL, NULL),
        ('Rye 4th grade', 'Жито 4 клас', 'Grains', NULL, NULL),
        ('Oats', 'Вівсяниця', 'Grains', 'Oats, used for food and animal feed.', 'Вівсяниця, використовується для харчування та кормів тваринам.'),
        ('Millet', 'Просо', 'Grains', 'Millet grain, used for food and bird feed.', 'Просо, використовується для харчування та кормів для птахів.'),
        ('Buckwheat', 'Гречка', 'Grains', 'Buckwheat grain, used for food.', 'Гречка, використовується для харчування.'),
        ('Einkorn wheat', 'Пшениця однозернянка', 'Grains', NULL, NULL),
        ('Spelt wheat', 'Пшениця спельта', 'Grains', NULL, NULL),
        ('Durum wheat', 'Пшениця тверда', 'Grains', NULL, NULL),
        ('Malting barley', 'Пивоварний ячмінь', 'Grains', NULL, NULL),
        ('Sorghum white', 'Сорго біле', 'Grains', NULL, NULL),
        ('Sorghum red', 'Сорго червоне', 'Grains', NULL, NULL),
        ('Rice', 'Рис', 'Grains', NULL, NULL),
        ('Triticale', 'Тритикале', 'Grains', NULL, NULL),
        -- Pulses
        ('Peas', 'Горох', 'Pulses', 'Peas, used for food and animal feed.', 'Горох, використовується для харчування та кормів тваринам.'),
        ('Vetch', 'Вика', 'Pulses', NULL, NULL),
        ('Green peas', 'Зелений горошок', 'Pulses', NULL, NULL),
        ('Chick-peas', 'Нут', 'Pulses', NULL, NULL),
        ('Lupine', 'Люпин', 'Pulses', NULL, NULL),
        ('Lentil', 'Сочевиця', 'Pulses', NULL, NULL),
        ('White kidney beans', 'Біла квасоля', 'Pulses', NULL, NULL),
        -- Oilseeds and Related
        ('Sunflower', 'Соняшник', 'Oilseeds', 'Sunflower seeds, used for oil production and food.', 'Соняшникові насіння, використовується для виробництва олії та харчування.'),
        ('Soybeans', 'Соя', 'Oilseeds', 'Soybeans, used for oil and food products.', 'Соєві боби, використовується для олії та харчових продуктів.'),
        ('Soy', 'Соєві боби', 'Oilseeds', NULL, NULL),
        ('Rapeseed', 'Ріпак', 'Oilseeds', NULL, NULL),
        ('Sunflower high-oleic', 'Соняшник високоолеїновий', 'Oilseeds', NULL, NULL),
        ('Confectionery sunflower seeds', 'Соняшник кондитерський', 'Oilseeds', NULL, NULL),
        ('Sunflower kernel', 'Ядро соняшнику', 'Oilseeds', NULL, NULL),
        ('Rapeseed high grade less 25mcm', 'Ріпак вищий сорт менше 25мкм', 'Oilseeds', NULL, NULL),
        ('Rapeseed 1 grade less 35mcm', 'Ріпак 1 клас менше 35мкм', 'Oilseeds', NULL, NULL),
        ('Rapeseed 2 grade more 35mcm', 'Ріпак 2 клас більше 35мкм', 'Oilseeds', NULL, NULL),
        ('Flax', 'Льон', 'Oilseeds', NULL, NULL),
        ('Mustard seeds', 'Гірчичне насіння', 'Oilseeds', NULL, NULL),
        ('Poppy seeds', 'Макове насіння', 'Oilseeds', NULL, NULL),
        ('Soybeans GMO-free', 'Соєві боби без ГМО', 'Oilseeds', NULL, NULL),
        ('Rapeseed coarse meal', 'Ріпаковий шрот', 'Oilseeds', NULL, NULL),
        -- Oils
        ('Sunflower oil', 'Соняшникова олія', 'Oils', 'Sunflower oil, used for cooking and food production.', 'Соняшникова олія, використовується для приготування їжі та виробництва продуктів харчування.'),
        ('Soybean oil', 'Соєва олія', 'Oils', 'Soybean oil, used for cooking and food production.', 'Соєва олія, використовується для приготування їжі та виробництва продуктів харчування.'),
        ('Rapeseed oil', 'Ріпакова олія', 'Oils', NULL, NULL),
        ('Flaxseed oil', 'Льняна олія', 'Oils', NULL, NULL),
        ('Mustard oil', 'Гірчична олія', 'Oils', NULL, NULL),
        ('Poppy seed oil', 'Макова олія', 'Oils', NULL, NULL),
        ('Corn oil', 'Кукурудзяна олія', 'Oils', NULL, NULL),
        ('Olive oil', 'Оливкова олія', 'Oils', NULL, NULL),
        ('Palm oil', 'Пальмова олія', 'Oils', NULL, NULL),
        ('Coconut oil', 'Кокосова олія', 'Oils', NULL, NULL),
        ('Sesame oil', 'Кунжутна олія', 'Oils', NULL, NULL),
        ('Hemp seed oil', 'Конопляна олія', 'Oils', NULL, NULL),
        ('Grape seed oil', 'Олія виноградних кісточок', 'Oils', NULL, NULL),
        ('Avocado oil', 'Авокадова олія', 'Oils', NULL, NULL),
        ('Walnut oil', 'Горіхова олія', 'Oils', NULL, NULL),
        ('Almond oil', 'Мигдальна олія', 'Oils', NULL, NULL),
        ('Pumpkin seed oil', 'Олія гарбузового насіння', 'Oils', NULL, NULL),
        -- Processed products
        ('Sunflower seed meal', 'Соняшниковий шрот', 'Processed products', 'Meal from sunflower seeds, used for animal feed.', 'Шрот з соняшникових насіння, використовується для кормів тваринам.'),
        ('Soybeen meal', 'Соєвий шрот', 'Processed products', 'Meal from soybeans, used for animal feed.', 'Шрот з соєвих бобів, використовується для кормів тваринам.'),
        ('Rape-seed coarse meal', 'Ріпаковий шрот', 'Processed products', 'Coarse meal from rapeseed, used for animal feed.', 'Грубий шрот з ріпаку, використовується для кормів тваринам.'),
        ('Sunflower oil cake', 'Соняшникова макуха', 'Processed products', 'Cake from sunflower oil extraction, used for animal feed.', 'Макуха з видобутку соняшникової олії, використовується для кормів тваринам.'),
        ('rapeseed cake', 'Ріпакова макуха', 'Processed products', NULL, NULL),
        ('Wheat flour extra class', 'Пшеничне борошно екстра', 'Processed products', NULL, NULL),
        ('Wheat flour class 1', 'Пшеничне борошно 1 клас', 'Processed products', NULL, NULL),
        ('Rye flour', 'Житнє борошно', 'Processed products', NULL, NULL),
        ('Oat flour', 'Вівсяне борошно', 'Processed products', NULL, NULL),
        ('Buckwheat groats', 'Гречана крупа', 'Processed products', NULL, NULL),
        ('Wheat mill offals', 'Пшеничні висівки', 'Processed products', NULL, NULL),
        -- Industrial products
        ('Sugar beet pulp gran', 'Гранульований буряковий жом', 'Industrial products', 'Granulated sugar beet pulp, used in animal feed.', 'Гранульований буряковий жом, використовується в кормі для тварин.'),
        ('Beet molasses', 'Бурякова меляса', 'Industrial products', 'Molasses from sugar beets, used in animal feed and food industry.', 'Меляса з цукрових буряків, використовується в кормі для тварин та харчовій промисловості.'),
        ('Coriander', 'Коріандр', 'Industrial products', NULL, NULL),
        ('Thistle', 'Розторопша', 'Industrial products', NULL, NULL),
        ('Soybean hulls granulated', 'Гранульована соєва оболонка', 'Industrial products', NULL, NULL),
        ('Soybean lecithin', 'Соєвий лецитин', 'Industrial products', NULL, NULL),
        ('Soybean phosphatide concentrate', 'Соєвий фосфатидний концентрат', 'Industrial products', NULL, NULL),
        ('Sunflower concentrate', 'Соняшниковий концентрат', 'Industrial products', NULL, NULL),
        ('Sugar', 'Цукор', 'Industrial products', NULL, NULL),
        -- Feed products
        ('Compound feed', 'Комбікорм', 'Feed products', 'Compound feed for livestock and poultry.', 'Комбікорм для худоби та птиці.'),
        ('Premix', 'Премікс', 'Feed products', 'Premix for animal feed, containing vitamins and minerals.', 'Премікс для кормів тваринам, що містить вітаміни та мінерали.'),
        ('Mineral feed', 'Мінеральний корм', 'Feed products', NULL, NULL),
        ('Vitamin feed', 'Вітамінний корм', 'Feed products', NULL, NULL),
        ('Protein feed', 'Білковий корм', 'Feed products', NULL, NULL),
        ('Fat feed', 'Жировий корм', 'Feed products', NULL, NULL),
        ('Enzyme feed', 'Ферментний корм', 'Feed products', NULL, NULL),
        ('Probiotic feed', 'Пробіотичний корм', 'Feed products', NULL, NULL),
        ('Antibiotic feed', 'Антибіотичний корм', 'Feed products', NULL, NULL),
        ('Mineral-vitamin feed', 'Мінерально-вітамінний корм', 'Feed products', NULL, NULL),
        -- Other
        ('Diesel', 'Дизельне паливо', 'Other', 'Diesel fuel for agricultural machinery.', 'Дизельне паливо для сільськогосподарської техніки.'),
        ('Gasoline', 'Бензин', 'Other', 'Gasoline for agricultural machinery.', 'Бензин для сільськогосподарської техніки.'),
        ('Lubricants', 'Мастила', 'Other', 'Lubricants for agricultural machinery.', 'Мастила для сільськогосподарської техніки.'),
        ('Fertilizers', 'Добрива', 'Other', NULL, NULL),
        ('Pesticides', 'Пестициди', 'Other', NULL, NULL),
        ('Herbicides', 'Гербіциди', 'Other', NULL, NULL),
        ('Insecticides', 'Інсектициди', 'Other', NULL, NULL),
        ('Fungicides', 'Фунгіциди', 'Other', NULL, NULL),
        ('Growth regulators', 'Регулятори росту', 'Other', NULL, NULL),
        ('Seeds', 'Насіння', 'Other', NULL, NULL);
    END IF;
END $$;

-- Create hierarchical view for categories

CREATE OR REPLACE VIEW categories_hierarchy AS
SELECT 
    c.id,
    c.name,
    c.description,
    c.ua_name,
    c.ua_description,
    c.parent_category,
    pc.ua_name AS parent_category_ua
FROM
    categories c
LEFT JOIN parent_categories pc ON c.parent_category = pc.name
ORDER BY
    c.parent_category, c.name;


-- First, drop existing functions and triggers
DROP TRIGGER IF EXISTS subscription_status_check ON subscriptions;
DROP FUNCTION IF EXISTS check_subscription_status();
DROP FUNCTION IF EXISTS update_expired_subscriptions();

-- Create improved version of update_expired_subscriptions function
CREATE OR REPLACE FUNCTION update_expired_subscriptions()
RETURNS void AS $$
DECLARE
    free_tarif_id INTEGER;
BEGIN
    -- Get the free tarif ID once
    SELECT id INTO free_tarif_id 
    FROM tarifs 
    WHERE scope = 'free' 
    LIMIT 1;

    -- Handle expired paid subscriptions in one statement
    INSERT INTO subscriptions (
        user_id, tarif_id, start_date, end_date, status, order_id
    )
    SELECT 
        s.user_id,
        free_tarif_id,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP + INTERVAL '1 month',
        'active',
        'auto-renewal-' || uuid_generate_v4()
    FROM subscriptions s
    JOIN tarifs t ON s.tarif_id = t.id
    WHERE t.scope != 'free'
        AND s.end_date < CURRENT_TIMESTAMP
        AND s.status = 'active'
    AND NOT EXISTS (
        SELECT 1 
        FROM subscriptions active_sub
        WHERE active_sub.user_id = s.user_id
        AND active_sub.status = 'active'
        AND active_sub.end_date > CURRENT_TIMESTAMP
    );

    -- Update status of expired subscriptions
    UPDATE subscriptions s
    SET status = 'expired'
    WHERE s.end_date < CURRENT_TIMESTAMP
    AND s.status = 'active';
END;
$$ LANGUAGE plpgsql;

-- Create a safer trigger function that prevents recursive calls
CREATE OR REPLACE FUNCTION check_subscription_status()
RETURNS trigger AS $$
BEGIN
    IF (TG_OP = 'INSERT' AND NEW.status = 'active') OR
       (TG_OP = 'UPDATE' AND NEW.status = 'active' AND OLD.status != 'active') THEN
        -- Only update expired subscriptions when activating a new subscription
        PERFORM update_expired_subscriptions();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a row-level trigger instead of statement-level
CREATE TRIGGER subscription_status_check
    AFTER INSERT OR UPDATE ON subscriptions
    FOR EACH ROW
    WHEN (NEW.status = 'active')
    EXECUTE FUNCTION check_subscription_status();

-- Add necessary indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_status_end_date 
ON subscriptions(status, end_date);
CREATE INDEX IF NOT EXISTS idx_tarifs_scope 
ON tarifs(scope);

-- Create Notifications table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    notify_new_messages BOOLEAN DEFAULT TRUE,
    notify_new_items BOOLEAN DEFAULT TRUE,
    interested_categories TEXT[],
    country VARCHAR(150) DEFAULT 'Ukraine',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
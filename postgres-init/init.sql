-- This script is used to initialize the database for the application.
-- It creates the necessary tables, indexes, and functions.
-- It also ensures that the PostGIS extension is enabled for spatial data handling.
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
    uuid UUID NOT NULL DEFAULT uuid_generate_v4(),
    category_id INTEGER NOT NULL,
    offer_type VARCHAR(50) NOT NULL,  -- sell, buy, exchange
    title VARCHAR(150) NOT NULL,
    description TEXT,
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

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    hashed_password VARCHAR(100) NOT NULL,
    disabled BOOLEAN DEFAULT FALSE
);
-- Add unique constraint to email and username columns
-- This constraint ensures that the email address and username are unique across all users
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
    price DECIMAL(10, 2) NOT NULL DEFAULT 5.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    scope VARCHAR(100) NOT NULL DEFAULT 'basic',
    terms VARCHAR(50) NOT NULL DEFAULT 'monthly',
    items_limit INTEGER CONSTRAINT positive_items_limit CHECK (items_limit>=0),
    map_views_limit INTEGER CONSTRAINT positive_map_views_limit CHECK (map_views_limit>=0),
    geo_search_limit INTEGER CONSTRAINT positive_geo_search_limit CHECK (geo_search_limit>=0),
    navigation_limit INTEGER CONSTRAINT positive_navigation_limit CHECK (navigation_limit>=0),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add unique constraint to tarifs table
ALTER TABLE IF EXISTS public.tarifs
    ADD CONSTRAINT tarifs_name_unique_constraint UNIQUE (name);
ALTER TABLE IF EXISTS public.tarifs
    ADD CONSTRAINT tarifs_scope_unique_constraint UNIQUE (scope);


-- Drop indexes if they exist
DROP INDEX IF EXISTS tarifs_scope_idx;
DROP INDEX IF EXISTS tarifs_terms_idx;

-- Create indexes
CREATE INDEX tarifs_scope_idx ON tarifs (scope);
CREATE INDEX tarifs_terms_idx ON tarifs (terms);

-- Create table for user's subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    tarif_id INTEGER,
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    payment_id VARCHAR(20),
    items_count INTEGER DEFAULT 0,
    map_views INTEGER DEFAULT 0,
    geo_search_count INTEGER DEFAULT 0,
    navigation_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
    FOREIGN KEY (tarif_id) REFERENCES tarifs (id) ON DELETE SET NULL
);

-- Create table for user's payments
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(100),
    order_id TEXT NOT NULL,
    order_status VARCHAR(30),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    amount INTEGER NOT NULL,
    card_type VARCHAR(20),
    masked_card TEXT,
    sender_email TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    data JSONB
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

-- Check if the categories table is empty
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM categories) THEN
	-- Insert default categories
	INSERT INTO categories (name, description, ua_name, ua_description)
	VALUES
    (
	'Wheat 2nd grade',
        'Wheat 2nd grade must meet the requirements of DSTU 3768:2019 and have the following basic indicators:
- moisture - basis 14%;
- trash impurity - basis 2%;
- grain impurity - max 8%;
including impurity of other crops: basis 1% max - 4%,
including sprouted grains: max - 3%,
including broken grains: max - 5%;
- protein - min. 12.50%;
- nature - min. 750g/l;
- gluten - min. 23%;
- IDK - max 100 pcs.;
- damaged by bug-turtle - basis 2%, max 3%;
- sooty grain - basis 8%;
- falling number, s, - basis 250s, min. 220s.
Sampling and sample formation for the determination of all indicators is carried out in accordance with DSTU ISO 13690:2003.',
        'Пшениця 2-го класу',
        'Пшениця 2 клас повинна відповідати вимогам ДСТУ 3768:2019 та мати наступні базисні показники:
- вологість - базис 14%;
- сміттєва домішка - базис 2%;
- зернова домішка - макс 8%;
зокрема домішка ін. культур: базис 1% макс - 4%,
зокрема пророслі зерна: макс - 3%,
зокрема биті зерна: макс - 5%;
- білок - мін. 12,50%;
- натура - мін. 750г/л.;
- клейковина - мін. 23%;
- ІДК - макс 100 од.;
- пошкоджені клопом-черепашкою -базис 2%, макс 3%;
- сажкове зерно - базис 8%;
- число падання, с, - базис 250с, мін. 220с.
Відбір та формування проб для визначення всіх показників здійснюється згідно ДСТУ ISO 13690:2003.'
    ),
    (
        'Wheat 3rd grade',
        'Wheat 3rd grade must meet the requirements of DSTU 3768:2019 and have the following basic indicators:
- moisture - basis 14%;
- trash impurity - basis 2%;
- grain impurity - max 8 %,
including impurity of other crops: max - 4%,
including sprouted grains: max - 3%;
including broken grains: max - 5%;
- protein - min. 11.0%;
- nature - min. 730g/l;
- gluten - min. 18%;
- IDK - max 100 pcs.;
- damaged by bug-turtle - basis 3%, max 5%;
- sooty grain basis 8%, max 10%;
- falling number, s, - basis 220s, min. 180s.
Sampling and sample formation for the determination of all indicators is carried out in accordance with DSTU ISO 13690:2003.',
        'Пшениця 3-го класу',
        'Пшениця 3 клас повинна відповідати вимогам ДСТУ 3768:2019 та мати наступні базисні показники:
- вологість - базис 14%;
- сміттєва домішка - базис 2%;
- зернова домішка - макс 8 %,
зокрема домішка ін. культур: макс - 4%,
зокрема пророслі зерна : макс - 3%;
зокрема биті зерна: макс - 5%;
- білок - мін. 11,0%;
- натура - мін. 730г/л;
- клейковина - мін. 18%;
- ІДК - макс 100 од.;
- пошкоджені клопом-черепашкою -базис 3%, макс 5%;
- сажкове зерно базис 8%, макс 10%;
- число падання, с, - базис 220с, мін. 180с.
Відбір та формування проб для визначення всіх показників здійснюється згідно ДСТУ ISO 13690:2003.'
    ),
    (
        'Wheat 4th grade',
        'Wheat 4th grade must meet the requirements of DSTU 3768:2019 and have the following basic indicators:
- moisture - basis 14%;
- trash impurity - basis 2%, max 3%;
- grain impurity - max 15%,
including impurity of other crops max - 5%,
including sprouted grains: within the grain impurity;
- protein - not limited;
- nature - basis 720 g/l, min. 650g/l
- gluten - not limited;
- damaged by bug-turtle - basis 10%, max - 20%,
- sooty grain - basis 10%, max - 20%.
Sampling and sample formation for the determination of all indicators is carried out in accordance with DSTU ISO 13690:2003.',
        'Пшениця 4-го класу',
        'Пшениця 4 клас повинна відповідати вимогам ДСТУ 3768:2019 та мати наступні базисні показники:
- вологість - базис 14%;
- сміттєва домішка - базис 2%, макс 3%;
- зернова домішка - макс 15%,
зокрема домішка ін. культур макс - 5%,
зокрема пророслі зерна: в межах зернової домішки;
- білок - не обмежений;
- натура - базис 720 г/л, мін. 650г/л
- клейковина - не обмежена;
- пошкоджені клопом-черепашкою - базис 10%, макс - 20%,
- сажкове зерно - базис 10%, макс - 20%.
Відбір та формування проб для визначення всіх показників здійснюється згідно ДСТУ ISO 13690:2003.'
    ),
    (
        'Barley',
        'Barley must meet the requirements of DSTU 3769-98 and have the following basic indicators:
- moisture - 14.0 %,
- trash impurity - 2.0 %,
- grain impurity - not more than 15.0%, including immature grains - not more than 5.0%,
- grains of other crops - not more than 5.0%,
- nature basis 580g/l, min.550g/l.
Sampling and sample formation for the determination of all indicators is carried out in accordance with DSTU ISO 13690:2003.',
        'Ячмінь',
        'Ячмінь повинен відповідати вимогам ДСТУ 3769-98 та мати наступні базисні показники:
- вологість - 14,0 %,
- сміттєва домішка - 2,0 %,
- зернова домішка - не більше 15,0%, в т.ч. недозрілих зерен - не більше 5,0%,
- зерна інших зернових культур - не більше 5,0%,
- натура базис 580г/л, мін.550г/л.
Відбір та формування проб для визначення всіх показників здійснюється згідно ДСТУ ISO 13690:2003.'
    ),
    (
        'Corn',
        'Corn must meet the requirements of DSTU 4525:2006 and have the following basic indicators:
- moisture - 14.0%;
- trash impurity - 2.0 %;
- grain impurity - max. 15 %;
- damaged grains - basis. 5.0%; max 8.0%
- broken grains - basis 5.0%, within the grain
Sampling and sample formation for the determination of all indicators is carried out in accordance with DSTU ISO 13690:2003.',
        'Кукурудза',
        'Кукурудза повинна відповідати вимогам ДСТУ 4525:2006 та мати наступні базисні показники:
- вологість - 14,0%;
- сміттєва домішка - 2,0 %;
- зернова домішка - макс. 15 %;
- пошкодженні зерна - базис. 5,0%; макс 8,0%
- биті зерна - базис 5,0%, в межах зернової
Відбір та формування проб для визначення всіх показників здійснюється згідно ДСТУ ISO 13690:2003.'
    ),
    (
        'Sunflower',
        'Recommended quality requirements according to DSTU 7011:2009. The following indicators should be taken into account here:
- moisture - not more than 8%,
- trash impurities - up to 3%,
- oil impurities - maximum 10%,
- oil yield - from 48% and above,
- oleic acid content - from 82%.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Соняшник',
        'Рекомендовані вимоги до якості згідно з ДСТУ 7011:2009. Тут мають враховуватися наступні показники: 
- вологість – не більше 8%, 
- сміттєві домішки – до 3%, 
- олійні домішки – максимально 10%, 
- вихід олії – від 48% і більше, 
- вміст олеїнової кислоти – від 82%. 
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
    (
        'Soy',
        'Recommended quality requirements according to DSTU 4962:2008. The following indicators should be taken into account here:
- moisture - not more than 14%,
- trash impurities - up to 2%,
- grain impurities - up to 5%,
- oil impurities - maximum 10%,
- oil yield - from 18% and above,
- protein content - from 34% and above.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Соя',
        'Рекомендовані вимоги до якості згідно з ДСТУ 4962:2008. Тут мають враховуватися наступні показники:
- вологість – не більше 14%,
- сміттєві домішки – до 2%,
- зернові домішки – до 5%,
- олійні домішки – максимально 10%,
- вихід олії – від 18% і більше,
- вміст білка – від 34% і більше.
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
    (
        'Rapeseed',
        'Recommended quality requirements according to DSTU 4963:2008. The following indicators should be taken into account here:
- moisture - not more than 9%,
- trash impurities - up to 2%,
- grain impurities - up to 5%,
- oil impurities - maximum 10%,
- oil yield - from 40% and above,
- erucic acid content - not more than 2%.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Рапс',
        'Рекомендовані вимоги до якості згідно з ДСТУ 4963:2008. Тут мають враховуватися наступні показники:
- вологість – не більше 9%,
- сміттєві домішки – до 2%,
- зернові домішки – до 5%,
- олійні домішки – максимально 10%,
- вихід олії – від 40% і більше,
- вміст ерукової кислоти – не більше 2%.
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
    (
        'Oats',
        'Recommended quality requirements according to DSTU 3767:2019. The following indicators should be taken into account here:
- moisture - not more than 14%,
- trash impurities - up to 2%,
- grain impurities - up to 5%,
- nature - basis 580g/l, min. 550g/l.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Вівсянка',
        'Рекомендовані вимоги до якості згідно з ДСТУ 3767:2019. Тут мають враховуватися наступні показники:
- вологість – не більше 14%,
- сміттєві домішки – до 2%,
- зернові домішки – до 5%,
- натура – базис 580г/л, мін. 550г/л.
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
    (
        'Rye',
        'Recommended quality requirements according to DSTU 3766:2019. The following indicators should be taken into account here:
- moisture - not more than 14%,
- trash impurities - up to 2%,
- grain impurities - up to 5%,
- nature - basis 580g/l, min. 550g/l.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Жито',
        'Рекомендовані вимоги до якості згідно з ДСТУ 3766:2019. Тут мають враховуватися наступні показники:
- вологість – не більше 14%,
- сміттєві домішки – до 2%,
- зернові домішки – до 5%,
- натура – базис 580г/л, мін. 550г/л.
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
    (
        'Millet',
        'Recommended quality requirements according to DSTU 3765:2019. The following indicators should be taken into account here:
- moisture - not more than 14%,
- trash impurities - up to 2%,
- grain impurities - up to 5%,
- nature - basis 580g/l, min. 550g/l.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Просо',
        'Рекомендовані вимоги до якості згідно з ДСТУ 3765:2019. Тут мають враховуватися наступні показники:
- вологість – не більше 14%,
- сміттєві домішки – до 2%,
- зернові домішки – до 5%,
- натура – базис 580г/л, мін. 550г/л.
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
    (
        'Peas',
        'Recommended quality requirements according to DSTU 3764:2019. The following indicators should be taken into account here:
- moisture - not more than 14%,
- trash impurities - up to 2%,
- grain impurities - up to 5%,
- nature - basis 580g/l, min. 550g/l.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Горох',
        'Рекомендовані вимоги до якості згідно з ДСТУ 3764:2019. Тут мають враховуватися наступні показники:
- вологість – не більше 14%,
- сміттєві домішки – до 2%,
- зернові домішки – до 5%,
- натура – базис 580г/л, мін. 550г/л.
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
    (
        'Buckwheat',
        'Recommended quality requirements according to DSTU 3763:2019. The following indicators should be taken into account here:
- moisture - not more than 14%,
- trash impurities - up to 2%,
- grain impurities - up to 5%,
- nature - basis 580g/l, min. 550g/l.
The presence of ticks or some other types of pests, toxic drugs is unacceptable.',
        'Гречка',
        'Рекомендовані вимоги до якості згідно з ДСТУ 3763:2019. Тут мають враховуватися наступні показники:
- вологість – не більше 14%,
- сміттєві домішки – до 2%,
- зернові домішки – до 5%,
- натура – базис 580г/л, мін. 550г/л.
Не можна допускати наявність кліщів або деяких інших видів шкідників, токсичних препаратів.'
    ),
(
        'Diesel fuel',
        'Diesel fuel must meet the requirements of DSTU 3587:2015 and have the following basic
        indicators:
        - sulfur content - not more than 0.2%;
        - water content - not more than 0.05%;
        - mechanical impurities content - not more than 0.01%;
        - flash point - not lower than 55 °C;
        - freezing point - not higher than -5 °C;
        - kinematic viscosity at 20 °C - from 2.0 to 4.5 mm2/s;
        - density at 15 °C - from 820 to 860 kg/m3;
        - cetane number - not less than 45.
        Sampling and sample formation for the determination of all indicators is carried out in accordance with DSTU ISO 3170:2007.',
        'Дизельне паливо',
        'Дизельне паливо повинно відповідати вимогам ДСТУ 3587:2015 та мати наступні базисні
    показники:
    - вміст сірки - не більше 0,2 %;
    - вміст води - не більше 0,05 %;
    - вміст механічних домішок - не більше 0,01 %;
    - температура спалаху - не нижче 55 °С;
    - температура застигання - не вище -5 °С;
    - кінематична в`язкість при 20 °С - від 2,0 до 4,5 мм2/с;
    - щільність при 15 °С - від 820 до 860 кг/м3;
    - кількість цетану - не менше 45.
    Відбір та формування проб для визначення всіх показників здійснюється згідно ДСТУ ISO 3170:2007.'
)
;
    END IF;
END $$;

-- Update default tarifs with limits
-- UPDATE tarifs 
-- SET items_limit = CASE 
--         WHEN scope = 'basic' THEN 50
--         WHEN scope = 'premium' THEN 150
--         WHEN scope = 'pro' THEN 500
--     END,
--     map_views_limit = CASE 
--         WHEN scope = 'basic' THEN 100
--         WHEN scope = 'premium' THEN 300
--         WHEN scope = 'pro' THEN 1000
--     END,
--     geo_search_limit = CASE
--         WHEN scope = 'basic' THEN 100
--         WHEN scope = 'premium' THEN 300
--         WHEN scope = 'pro' THEN 1000
--     END,
--     navigation_limit = CASE
--         WHEN scope = 'basic' THEN 100
--         WHEN scope = 'premium' THEN 300
--         WHEN scope = 'pro' THEN 1000
--     END;

-- Check if the tarifs table is empty
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM tarifs) THEN
	-- Insert default tarifs
	INSERT INTO tarifs (name, description, price, currency, scope, terms, items_limit, map_views_limit, geo_search_limit, navigation_limit)
	VALUES
        ('Free', 'Free probation plan', 0.00, 'EUR', 'free', 'monthly', 5, 10, 10, 10),
	    ('Basic', 'Basic subscription plan', 4.99, 'EUR', 'basic', 'monthly', 50, 100, 100, 100),
        ('Premium', 'Premium subscription plan', 9.99, 'EUR', 'premium', 'monthly', 150, 300, 300, 300),
        ('Pro', 'Pro subscription plan', 24.99, 'EUR', 'pro', 'monthly', 500, 1000, 1000, 1000);
    END IF;
END $$;

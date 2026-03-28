-- ============================================================================
-- Proteus Database Schema
-- Phase: Unit 1 - Database Infrastructure
-- Description: Full database schema with dimension tables, panelists, and
--              base transactions table (hypertable created separately)
-- FR Coverage: FR-6.1 through FR-6.10
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Brands dimension table
-- FR-6.5: Brand tier classification (luxury, premium, mid-market, value)
-- FR-6.5: Brand archetype (fast_casual, discount_retailer, department_store, subscription)
-- FR-6.5: Brand-to-parent mapping for corporate hierarchies
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('luxury', 'premium', 'mid-market', 'value')),
    archetype VARCHAR(50) NOT NULL CHECK (archetype IN (
        'fast_casual', 'discount_retailer', 'department_store', 'subscription',
        'grocery', 'restaurant', 'apparel', 'travel', 'entertainment',
        'electronics', 'home_improvement', 'healthcare', 'automotive'
    )),
    parent_company_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_brands_tier ON brands(tier);
CREATE INDEX idx_brands_archetype ON brands(archetype);
CREATE INDEX idx_brands_parent ON brands(parent_company_id);

-- Categories dimension table (3-level hierarchy)
-- FR-6.4: Level 1 - Style Classification (Discretionary, Consumer Staples, Services, Transportation)
-- FR-6.4: Level 2 - Spending Category (35-45 categories)
-- FR-6.4: Level 3 - Merchant Group (200-400 subcategories)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    level1 VARCHAR(50) NOT NULL CHECK (level1 IN (
        'Discretionary', 'Consumer Staples', 'Services', 'Transportation'
    )),
    level2 VARCHAR(100) NOT NULL,
    level3 VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_categories_level1 ON categories(level1);
CREATE INDEX idx_categories_level2 ON categories(level2);
CREATE INDEX idx_categories_level3 ON categories(level3);

-- Geography dimension table (hierarchical)
-- FR-6.3: State (51 values)
-- FR-6.3: CBSA/Metro Area (350-400 values)
-- FR-6.3: Urban/Suburban/Rural classification
CREATE TABLE geography (
    id SERIAL PRIMARY KEY,
    state_code CHAR(2) NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    cbsa_code VARCHAR(10),
    cbsa_name VARCHAR(200),
    urban_class VARCHAR(20) NOT NULL CHECK (urban_class IN ('urban', 'suburban', 'rural')),
    zip3 CHAR(3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_geography_state ON geography(state_code);
CREATE INDEX idx_geography_cbsa ON geography(cbsa_code);
CREATE INDEX idx_geography_urban_class ON geography(urban_class);
CREATE INDEX idx_geography_zip3 ON geography(zip3);

-- Generations dimension table
-- FR-6.7: Generational preferences for demographic correlations
CREATE TABLE generations (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    birth_year_start INTEGER NOT NULL,
    birth_year_end INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_generations_birth_years ON generations(birth_year_start, birth_year_end);

-- Income bands dimension table
-- FR-6.6: Income multipliers affecting transaction amounts
CREATE TABLE income_bands (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    min_income INTEGER NOT NULL,
    max_income INTEGER,
    income_multiplier DECIMAL(4, 2) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_income_bands_range ON income_bands(min_income, max_income);

-- ============================================================================
-- PANELIST TABLE
-- FR-6.9: Consumer panel structure (100,000-500,000 panelists)
-- ============================================================================

CREATE TABLE panelists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    income_band_id VARCHAR(20) NOT NULL REFERENCES income_bands(id),
    generation_id VARCHAR(20) NOT NULL REFERENCES generations(id),
    geography_id INTEGER NOT NULL REFERENCES geography(id),
    panel_start_date DATE NOT NULL,
    panel_weight DECIMAL(10, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Panel weights indexed for fast lookup during market share calculations
-- FR-6.6: Panel weights sum to estimated total US consumer population
CREATE INDEX idx_panelists_weight ON panelists(panel_weight);
CREATE INDEX idx_panelists_income_band ON panelists(income_band_id);
CREATE INDEX idx_panelists_generation ON panelists(generation_id);
CREATE INDEX idx_panelists_geography ON panelists(geography_id);
CREATE INDEX idx_panelists_start_date ON panelists(panel_start_date);

-- ============================================================================
-- TRANSACTIONS TABLE (base schema - hypertable created in init-timescale.sql)
-- FR-6.1: 10M+ synthetic transactions
-- FR-6.2: TimescaleDB hypertable with daily chunk intervals
-- ============================================================================

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_timestamp TIMESTAMPTZ NOT NULL,

    -- Foreign keys
    panelist_id UUID NOT NULL REFERENCES panelists(id),
    brand_id INTEGER NOT NULL REFERENCES brands(id),
    category_id INTEGER NOT NULL REFERENCES categories(id),
    geography_id INTEGER NOT NULL REFERENCES geography(id),

    -- Panelist demographics (denormalized for query performance)
    generation_id VARCHAR(20) NOT NULL REFERENCES generations(id),
    income_band_id VARCHAR(20) NOT NULL REFERENCES income_bands(id),

    -- Transaction details
    transaction_amount DECIMAL(10, 2) NOT NULL CHECK (transaction_amount > 0),
    card_type VARCHAR(20) NOT NULL CHECK (card_type IN ('credit', 'debit', 'prepaid', 'corporate')),
    payment_network VARCHAR(20) NOT NULL CHECK (payment_network IN ('visa', 'mastercard', 'amex', 'discover')),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('online', 'in-store', 'mobile')),

    -- Time dimensions (for efficient aggregation without timezone conversion)
    day_of_week VARCHAR(10) NOT NULL,
    hour_of_day INTEGER NOT NULL CHECK (hour_of_day >= 0 AND hour_of_day <= 23),

    -- Tenant for future multi-tenancy support
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001',

    -- Audit timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Composite indexes for efficient filtering on common query patterns
-- FR-6.8: Composite indexes on (timestamp, brand_id, category_id)
CREATE INDEX idx_transactions_timestamp_brand ON transactions(transaction_timestamp, brand_id);
CREATE INDEX idx_transactions_timestamp_category ON transactions(transaction_timestamp, category_id);
CREATE INDEX idx_transactions_timestamp_geo ON transactions(transaction_timestamp, geography_id);
CREATE INDEX idx_transactions_timestamp_income ON transactions(transaction_timestamp, income_band_id);
CREATE INDEX idx_transactions_timestamp_generation ON transactions(transaction_timestamp, generation_id);

-- Indexes for dimension lookups
CREATE INDEX idx_transactions_panelist ON transactions(panelist_id);
CREATE INDEX idx_transactions_brand ON transactions(brand_id);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_geography ON transactions(geography_id);

-- ============================================================================
-- STATIC DATA: Generation definitions
-- FR-6.7: Generational preferences
-- ============================================================================

INSERT INTO generations (id, name, birth_year_start, birth_year_end) VALUES
    ('gen_z', 'Gen Z', 1997, 2012),
    ('millennial', 'Millennials', 1981, 1996),
    ('gen_x', 'Gen X', 1965, 1980),
    ('baby_boomer', 'Baby Boomers', 1946, 1964),
    ('silent', 'Silent Generation', 1928, 1945);

-- ============================================================================
-- STATIC DATA: Income band definitions
-- FR-6.6: Income multipliers
-- ============================================================================

INSERT INTO income_bands (id, name, min_income, max_income, income_multiplier) VALUES
    ('band_1', 'Under $25K', 0, 24999, 0.60),
    ('band_2', '$25K-$40K', 25000, 39999, 0.75),
    ('band_3', '$40K-$60K', 40000, 59999, 0.90),
    ('band_4', '$60K-$85K', 60000, 84999, 1.00),
    ('band_5', '$85K-$150K', 85000, 149999, 1.30),
    ('band_6', '$150K+', 150000, NULL, 1.70);

-- Migration 0010: TimescaleDB hypertable configuration and continuous aggregates
-- Unit 1: Database Infrastructure
-- FR Coverage: FR-6.2, FR-6.8

-- Enable TimescaleDB extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- CONVERT TRANSACTIONS TO HYPERTABLE
-- FR-6.2: Daily chunk intervals for TimescaleDB partitioning
-- TimescaleDB requires the partition column to be part of any unique index.
-- ============================================================================

-- Recreate PK as composite to include the partition column
ALTER TABLE transactions DROP CONSTRAINT transactions_pkey;
ALTER TABLE transactions ADD CONSTRAINT transactions_pkey PRIMARY KEY (id, transaction_timestamp);

SELECT create_hypertable('transactions', 'transaction_timestamp',
    chunk_time_interval => INTERVAL '1 day',
    migrate_data => true,
    if_not_exists => TRUE
);

-- Enable compression on the hypertable
-- Segment by brand_id for better compression and query performance
ALTER TABLE transactions SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'brand_id'
);

-- ============================================================================
-- COMPRESSION POLICY
-- FR-6.2: Compression enabled after 30 days with gzip
-- ============================================================================

SELECT add_compression_policy('transactions', INTERVAL '30 days', if_not_exists => TRUE);

-- ============================================================================
-- RETENTION POLICY
-- FR-6.2: Retention policy drops chunks older than 7 years
-- ============================================================================

SELECT add_retention_policy('transactions', INTERVAL '7 years', if_not_exists => TRUE);

-- ============================================================================
-- CONTINUOUS AGGREGATES
-- FR-6.8: Pre-computed rollups for efficient querying
-- ============================================================================

-- Daily rollup aggregate (90-day retention)
CREATE MATERIALIZED VIEW transactions_daily
WITH (timescaledb.continuous)
AS
SELECT
    time_bucket('1 day', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    transactions.geography_id,
    transactions.generation_id,
    transactions.income_band_id,
    card_type,
    payment_network,
    channel,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_spend,
    AVG(transaction_amount) AS avg_spend,
    MIN(transaction_amount) AS min_spend,
    MAX(transaction_amount) AS max_spend,
    COUNT(DISTINCT panelist_id) AS unique_panelists,
    SUM(panelists.panel_weight) AS total_panel_weight
FROM transactions
JOIN panelists ON transactions.panelist_id = panelists.id
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
WITH NO DATA;

CREATE INDEX idx_transactions_daily_bucket ON transactions_daily(bucket);
CREATE INDEX idx_transactions_daily_brand ON transactions_daily(brand_id);
CREATE INDEX idx_transactions_daily_category ON transactions_daily(category_id);
CREATE INDEX idx_transactions_daily_bucket_brand_cat ON transactions_daily(bucket, brand_id, category_id);

SELECT add_continuous_aggregate_policy('transactions_daily',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Weekly rollup aggregate (2-year retention)
CREATE MATERIALIZED VIEW transactions_weekly
WITH (timescaledb.continuous)
AS
SELECT
    time_bucket('7 days', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    transactions.geography_id,
    transactions.generation_id,
    transactions.income_band_id,
    card_type,
    payment_network,
    channel,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_spend,
    AVG(transaction_amount) AS avg_spend,
    MIN(transaction_amount) AS min_spend,
    MAX(transaction_amount) AS max_spend,
    COUNT(DISTINCT panelist_id) AS unique_panelists,
    SUM(panelists.panel_weight) AS total_panel_weight
FROM transactions
JOIN panelists ON transactions.panelist_id = panelists.id
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
WITH NO DATA;

CREATE INDEX idx_transactions_weekly_bucket ON transactions_weekly(bucket);
CREATE INDEX idx_transactions_weekly_brand ON transactions_weekly(brand_id);
CREATE INDEX idx_transactions_weekly_category ON transactions_weekly(category_id);
CREATE INDEX idx_transactions_weekly_bucket_brand_cat ON transactions_weekly(bucket, brand_id, category_id);

SELECT add_continuous_aggregate_policy('transactions_weekly',
    start_offset => INTERVAL '2 years',
    end_offset => INTERVAL '7 days',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Monthly rollup aggregate (7-year retention)
CREATE MATERIALIZED VIEW transactions_monthly
WITH (timescaledb.continuous)
AS
SELECT
    time_bucket('1 month', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    transactions.geography_id,
    transactions.generation_id,
    transactions.income_band_id,
    card_type,
    payment_network,
    channel,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_spend,
    AVG(transaction_amount) AS avg_spend,
    MIN(transaction_amount) AS min_spend,
    MAX(transaction_amount) AS max_spend,
    COUNT(DISTINCT panelist_id) AS unique_panelists,
    SUM(panelists.panel_weight) AS total_panel_weight
FROM transactions
JOIN panelists ON transactions.panelist_id = panelists.id
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
WITH NO DATA;

CREATE INDEX idx_transactions_monthly_bucket ON transactions_monthly(bucket);
CREATE INDEX idx_transactions_monthly_brand ON transactions_monthly(brand_id);
CREATE INDEX idx_transactions_monthly_category ON transactions_monthly(category_id);
CREATE INDEX idx_transactions_monthly_bucket_brand_cat ON transactions_monthly(bucket, brand_id, category_id);

SELECT add_continuous_aggregate_policy('transactions_monthly',
    start_offset => INTERVAL '7 years',
    end_offset => INTERVAL '1 month',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Market share daily aggregate (90-day retention)
-- Window functions in continuous aggregates require this setting
SET timescaledb.enable_cagg_window_functions = true;
CREATE MATERIALIZED VIEW market_share_daily
WITH (timescaledb.continuous)
AS
SELECT
    time_bucket('1 day', transaction_timestamp) AS bucket,
    category_id,
    brand_id,
    SUM(transaction_amount) AS brand_spend,
    SUM(SUM(transaction_amount)) OVER (
        PARTITION BY time_bucket('1 day', transaction_timestamp), category_id
    ) AS category_total_spend,
    (
        SUM(transaction_amount)::DECIMAL /
        NULLIF(SUM(SUM(transaction_amount)) OVER (
            PARTITION BY time_bucket('1 day', transaction_timestamp), category_id
        ), 0)
    ) * 100 AS market_share_pct,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT panelist_id) AS unique_panelists
FROM transactions
GROUP BY 1, 2, 3
WITH NO DATA;

CREATE INDEX idx_market_share_daily_bucket ON market_share_daily(bucket);
CREATE INDEX idx_market_share_daily_category ON market_share_daily(category_id);
CREATE INDEX idx_market_share_daily_brand ON market_share_daily(brand_id);
CREATE INDEX idx_market_share_daily_bucket_cat ON market_share_daily(bucket, category_id);

SELECT add_continuous_aggregate_policy('market_share_daily',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

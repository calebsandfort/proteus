-- ============================================================================
-- Continuous Aggregates for Pre-computed Rollups
-- Phase: Unit 1 - Database Infrastructure
-- Description: Materialized views for daily/weekly/monthly rollups with
--              automatic refresh policies
-- FR Coverage: FR-6.8
-- ============================================================================

-- Enable TimescaleDB extension if not already enabled
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================================================
-- DAILY ROLLUP AGGREGATE
-- FR-6.8: Daily rollups (90-day retention, compressed after 7 days)
-- ============================================================================

CREATE MATERIALIZED VIEW transactions_daily
WITH (timescaledb.continuous, timescaledb.continuous_aggregate)
AS
SELECT
    time_bucket('1 day', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    geography_id,
    generation_id,
    income_band_id,
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

-- Add indexes for efficient querying
CREATE INDEX idx_transactions_daily_bucket ON transactions_daily(bucket);
CREATE INDEX idx_transactions_daily_brand ON transactions_daily(brand_id);
CREATE INDEX idx_transactions_daily_category ON transactions_daily(category_id);
CREATE INDEX idx_transactions_daily_geo ON transactions_daily(geography_id);
CREATE INDEX idx_transactions_daily_bucket_brand_cat ON transactions_daily(bucket, brand_id, category_id);

-- Refresh policy: refresh continuously with 1-day lag
SELECT add_continuous_aggregate_policy(
    'transactions_daily',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- WEEKLY ROLLUP AGGREGATE
-- FR-6.8: Weekly rollups (2-year retention)
-- ============================================================================

CREATE MATERIALIZED VIEW transactions_weekly
WITH (timescaledb.continuous, timescaledb.continuous_aggregate)
AS
SELECT
    time_bucket('7 days', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    geography_id,
    generation_id,
    income_band_id,
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

-- Add indexes for efficient querying
CREATE INDEX idx_transactions_weekly_bucket ON transactions_weekly(bucket);
CREATE INDEX idx_transactions_weekly_brand ON transactions_weekly(brand_id);
CREATE INDEX idx_transactions_weekly_category ON transactions_weekly(category_id);
CREATE INDEX idx_transactions_weekly_bucket_brand_cat ON transactions_weekly(bucket, brand_id, category_id);

-- Refresh policy: refresh weekly with 7-day lag
SELECT add_continuous_aggregate_policy(
    'transactions_weekly',
    start_offset => INTERVAL '2 years',
    end_offset => INTERVAL '7 days',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- MONTHLY ROLLUP AGGREGATE
-- FR-6.8: Monthly rollups (7-year retention)
-- ============================================================================

CREATE MATERIALIZED VIEW transactions_monthly
WITH (timescaledb.continuous, timescaledb.continuous_aggregate)
AS
SELECT
    time_bucket('1 month', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    geography_id,
    generation_id,
    income_band_id,
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

-- Add indexes for efficient querying
CREATE INDEX idx_transactions_monthly_bucket ON transactions_monthly(bucket);
CREATE INDEX idx_transactions_monthly_brand ON transactions_monthly(brand_id);
CREATE INDEX idx_transactions_monthly_category ON transactions_monthly(category_id);
CREATE INDEX idx_transactions_monthly_bucket_brand_cat ON transactions_monthly(bucket, brand_id, category_id);

-- Refresh policy: refresh monthly with 1-month lag
SELECT add_continuous_aggregate_policy(
    'transactions_monthly',
    start_offset => INTERVAL '7 years',
    end_offset => INTERVAL '1 month',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- MARKET SHARE DAILY AGGREGATE
-- FR-6.8: Pre-computed market share percentage per brand within category
-- ============================================================================

CREATE MATERIALIZED VIEW market_share_daily
WITH (timescaledb.continuous, timescaledb.continuous_aggregate)
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

-- Add indexes for market share queries
CREATE INDEX idx_market_share_daily_bucket ON market_share_daily(bucket);
CREATE INDEX idx_market_share_daily_category ON market_share_daily(category_id);
CREATE INDEX idx_market_share_daily_brand ON market_share_daily(brand_id);
CREATE INDEX idx_market_share_daily_bucket_cat ON market_share_daily(bucket, category_id);

-- Refresh policy: refresh daily with 1-day lag
SELECT add_continuous_aggregate_policy(
    'market_share_daily',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- VERIFY CONTINUOUS AGGREGATES
-- ============================================================================

-- Check all continuous aggregates are properly configured
SELECT
    view_name,
    view_owner,
    materializer,
    refresher,
    compressed,
    materialized_only
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;

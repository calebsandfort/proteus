-- ============================================================================
-- Compression and Retention Policies
-- Phase: Unit 1 - Database Infrastructure
-- Description: Automated policies for chunk compression and data retention
-- FR Coverage: FR-6.2
-- ============================================================================

-- Enable TimescaleDB extension if not already enabled
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================================================
-- COMPRESSION POLICIES
-- FR-6.2: Compression enabled after 30 days with gzip
-- ============================================================================

-- Add compression policy for transactions hypertable
-- Chunks older than 30 days will be compressed
SELECT add_compression_policy(
    'transactions',
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Show current compression policy
SELECT
    hypertable_name,
    compression_arg,
    schedule_interval,
    next_start_time
FROM timescaledb_information Compression_Policies
WHERE hypertable_name = 'transactions';

-- ============================================================================
-- RETENTION POLICY
-- FR-6.2: Retention policy drops chunks older than 7 years
-- ============================================================================

-- Add retention policy for transactions hypertable
-- Chunks older than 7 years will be dropped
SELECT add_retention_policy(
    'transactions',
    INTERVAL '7 years',
    if_not_exists => TRUE
);

-- Show current retention policy
SELECT
    hypertable_name,
    drop_after,
    schedule_interval,
    next_start_time
FROM timescaledb_information Retention_Policies
WHERE hypertable_name = 'transactions';

-- ============================================================================
-- CHUNK INFORMATION
-- ============================================================================

-- View information about existing chunks
SELECT
    hypertable_name,
    chunk_name,
    table_bytes,
    index_bytes,
    toast_bytes,
    total_bytes,
    compressed,
    compression_status,
    range_start::DATE AS chunk_start,
    range_end::DATE AS chunk_end
FROM timescaledb_information.chunks
WHERE hypertable_name = 'transactions'
ORDER BY range_start DESC;

-- ============================================================================
-- CONTINUOUS AGGREGATE REFRESH POLICIES (for reference)
-- ============================================================================

-- View refresh policies for continuous aggregates
SELECT
    view_name,
    schedule_interval,
    refresh_lag,
    refresh_interval,
    next_refresh
FROM timescaledb_information.continuous_aggregate_policies
ORDER BY view_name;

-- ============================================================================
-- MANUAL POLICY MANAGEMENT (for maintenance)
-- ============================================================================

-- Remove a compression policy (if needed for maintenance)
-- CALL remove_compression_policy('transactions', if_not_exists => TRUE);

-- Remove a retention policy (if needed for maintenance)
-- CALL remove_retention_policy('transactions', if_not_exists => TRUE);

-- Force immediate compression of old chunks (for maintenance)
-- SELECT timescaledb_experimental.compress_chunk('_timescaledb_internal._hyper_1_몽 chunks');

-- Force refresh of a continuous aggregate (for maintenance)
-- CALL refresh_continuous_aggregate('transactions_daily', NULL, NULL);

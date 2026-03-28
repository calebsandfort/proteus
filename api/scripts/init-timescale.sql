-- ============================================================================
-- TimescaleDB Hypertable Configuration
-- Phase: Unit 1 - Database Infrastructure
-- Description: Convert transactions to hypertable with daily chunk intervals
-- FR Coverage: FR-6.2
-- ============================================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Verify TimescaleDB is available
SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';

-- ============================================================================
-- CONVERT TRANSACTIONS TO HYPERTABLE
-- FR-6.2: Daily chunk intervals for TimescaleDB partitioning
-- ============================================================================

-- Convert the transactions table to a TimescaleDB hypertable
-- Partitioned on transaction_timestamp with 1-day chunk intervals
-- migrate_data => true ensures existing data is migrated to chunks
SELECT create_hypertable(
    'transactions',
    'transaction_timestamp',
    chunk_interval => INTERVAL '1 day',
    migrate_data => true,
    if_not_exists => TRUE
);

-- Verify hypertable creation
SELECT hypertable_name, num_chunks, compression_enabled
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'transactions';

-- ============================================================================
-- CONFIGURE COMPRESSION
-- FR-6.2: Compression enabled after 30 days with gzip
-- ============================================================================

-- Enable compression on the hypertable
-- Segment by brand_id for better compression and query performance
ALTER TABLE transactions SET (
    timescaledb.compression,
    timescaledb.compression_segmentby = 'brand_id'
);

-- Show compression settings
SELECT
    hypertable_name,
    compression_state,
    segmentby_column,
    orderby_column,
    orderby_column_asc
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'transactions';

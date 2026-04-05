/**
 * Result Set Handler
 * Implements FR-5.7: Result Set Handling
 *
 * Pagination and aggregation logic based on row count thresholds.
 */

export interface ResultSetConfig {
  displayMode: 'full' | 'paginated' | 'aggregated'
  pageSize: number | undefined
  aggregationRequired: boolean
  rawDataAllowed: boolean
}

/**
 * Thresholds from FR-5.7:
 * - 1-100 rows: Full table display
 * - 101-1,000 rows: Paginated (50 rows/page) or virtual scrolling
 * - 1,001-10,000 rows: Aggregated view by default; raw data on demand
 * - 10,000+ rows: Aggregation mandatory; raw data requires explicit query parameter
 */
export function getResultSetConfig(rowCount: number): ResultSetConfig {
  if (rowCount <= 100) {
    return {
      displayMode: 'full',
      pageSize: undefined,
      aggregationRequired: false,
      rawDataAllowed: true,
    }
  }

  if (rowCount <= 1000) {
    return {
      displayMode: 'paginated',
      pageSize: 50,
      aggregationRequired: false,
      rawDataAllowed: true,
    }
  }

  if (rowCount <= 10000) {
    return {
      displayMode: 'aggregated',
      pageSize: undefined,
      aggregationRequired: true,
      rawDataAllowed: true,
    }
  }

  // 10,000+ rows
  return {
    displayMode: 'aggregated',
    pageSize: undefined,
    aggregationRequired: true,
    rawDataAllowed: false,
  }
}

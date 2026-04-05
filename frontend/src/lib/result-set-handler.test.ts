import { describe, it, expect } from 'vitest'
import { getResultSetConfig, type ResultSetConfig } from './result-set-handler'

describe('result-set-handler', () => {
  describe('getResultSetConfig', () => {
    describe('FR 5.7 — Result Set Handling', () => {
      describe('1-100 rows: Full table display', () => {
        it('test_fr_5_7_1_row_full_display', () => {
          const config = getResultSetConfig(1)
          expect(config.displayMode).toBe('full')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(false)
        })

        it('test_fr_5_7_50_rows_full_display', () => {
          const config = getResultSetConfig(50)
          expect(config.displayMode).toBe('full')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(false)
        })

        it('test_fr_5_7_100_rows_full_display', () => {
          const config = getResultSetConfig(100)
          expect(config.displayMode).toBe('full')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(false)
        })
      })

      describe('101-1,000 rows: Paginated or virtual scrolling', () => {
        it('test_fr_5_7_101_rows_paginated', () => {
          const config = getResultSetConfig(101)
          expect(config.displayMode).toBe('paginated')
          expect(config.pageSize).toBe(50)
          expect(config.aggregationRequired).toBe(false)
        })

        it('test_fr_5_7_500_rows_paginated', () => {
          const config = getResultSetConfig(500)
          expect(config.displayMode).toBe('paginated')
          expect(config.pageSize).toBe(50)
          expect(config.aggregationRequired).toBe(false)
        })

        it('test_fr_5_7_1000_rows_paginated', () => {
          const config = getResultSetConfig(1000)
          expect(config.displayMode).toBe('paginated')
          expect(config.pageSize).toBe(50)
          expect(config.aggregationRequired).toBe(false)
        })
      })

      describe('1,001-10,000 rows: Aggregated view by default; raw data on demand', () => {
        it('test_fr_5_7_1001_rows_aggregated', () => {
          const config = getResultSetConfig(1001)
          expect(config.displayMode).toBe('aggregated')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(true)
        })

        it('test_fr_5_7_5000_rows_aggregated', () => {
          const config = getResultSetConfig(5000)
          expect(config.displayMode).toBe('aggregated')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(true)
        })

        it('test_fr_5_7_10000_rows_aggregated', () => {
          const config = getResultSetConfig(10000)
          expect(config.displayMode).toBe('aggregated')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(true)
        })
      })

      describe('10,000+ rows: Aggregation mandatory; raw data requires explicit query parameter', () => {
        it('test_fr_5_7_10001_rows_mandatory_aggregation', () => {
          const config = getResultSetConfig(10001)
          expect(config.displayMode).toBe('aggregated')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(true)
          expect(config.rawDataAllowed).toBe(false)
        })

        it('test_fr_5_7_100000_rows_mandatory_aggregation', () => {
          const config = getResultSetConfig(100000)
          expect(config.displayMode).toBe('aggregated')
          expect(config.pageSize).toBeUndefined()
          expect(config.aggregationRequired).toBe(true)
          expect(config.rawDataAllowed).toBe(false)
        })
      })
    })

    describe('Boundary conditions', () => {
      it('handles zero rows', () => {
        const config = getResultSetConfig(0)
        expect(config.displayMode).toBe('full')
        expect(config.aggregationRequired).toBe(false)
      })

      it('handles boundary at 100', () => {
        const config = getResultSetConfig(100)
        expect(config.displayMode).toBe('full')
      })

      it('handles boundary at 101', () => {
        const config = getResultSetConfig(101)
        expect(config.displayMode).toBe('paginated')
      })

      it('handles boundary at 1000', () => {
        const config = getResultSetConfig(1000)
        expect(config.displayMode).toBe('paginated')
      })

      it('handles boundary at 1001', () => {
        const config = getResultSetConfig(1001)
        expect(config.displayMode).toBe('aggregated')
      })

      it('handles boundary at 10000', () => {
        const config = getResultSetConfig(10000)
        expect(config.displayMode).toBe('aggregated')
      })

      it('handles boundary at 10001', () => {
        const config = getResultSetConfig(10001)
        expect(config.displayMode).toBe('aggregated')
        expect(config.rawDataAllowed).toBe(false)
      })
    })
  })
})

import { describe, it, expect } from 'vitest'
import { selectChartType, type ChartSelectionInput } from './chart-selection'

describe('chart-selection', () => {
  describe('selectChartType', () => {
    describe('FR 5.1 — Auto Chart-Type Selection', () => {
      describe('KPI Card (average, total, sum + single value)', () => {
        it('test_fr_5_1_kpi_average', () => {
          const input: ChartSelectionInput = {
            queryText: 'What is the average market share for Chipotle?',
            resultShape: { rowCount: 1, hasTimeDimension: false, categoryCount: 0, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('kpi')
        })

        it('test_fr_5_1_kpi_total', () => {
          const input: ChartSelectionInput = {
            queryText: 'Show total sales for Q3',
            resultShape: { rowCount: 1, hasTimeDimension: false, categoryCount: 0, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('kpi')
        })

        it('test_fr_5_1_kpi_sum', () => {
          const input: ChartSelectionInput = {
            queryText: 'Sum of all transactions',
            resultShape: { rowCount: 1, hasTimeDimension: false, categoryCount: 0, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('kpi')
        })
      })

      describe('Line Chart (over time, trend, history)', () => {
        it('test_fr_5_1_line_over_time', () => {
          const input: ChartSelectionInput = {
            queryText: 'Show market share over time',
            resultShape: { rowCount: 10, hasTimeDimension: true, categoryCount: 1, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('line')
        })

        it('test_fr_5_1_line_trend', () => {
          const input: ChartSelectionInput = {
            queryText: 'What is the trend for Chipotle sales?',
            resultShape: { rowCount: 8, hasTimeDimension: true, categoryCount: 1, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('line')
        })

        it('test_fr_5_1_line_history', () => {
          const input: ChartSelectionInput = {
            queryText: 'Show historical performance',
            resultShape: { rowCount: 12, hasTimeDimension: true, categoryCount: 1, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('line')
        })
      })

      describe('Bar Chart (compare, vs, versus + 2-5 categories)', () => {
        it('test_fr_5_1_bar_compare', () => {
          const input: ChartSelectionInput = {
            queryText: 'Compare market share between brands',
            resultShape: { rowCount: 4, hasTimeDimension: false, categoryCount: 4, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('bar')
        })

        it('test_fr_5_1_bar_vs', () => {
          const input: ChartSelectionInput = {
            queryText: 'Chipotle vs McDonalds market share',
            resultShape: { rowCount: 2, hasTimeDimension: false, categoryCount: 2, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('bar')
        })

        it('test_fr_5_1_bar_versus', () => {
          const input: ChartSelectionInput = {
            queryText: 'Brand A versus Brand B versus Brand C',
            resultShape: { rowCount: 3, hasTimeDimension: false, categoryCount: 3, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('bar')
        })

        it('test_fr_5_1_bar_5_categories', () => {
          const input: ChartSelectionInput = {
            queryText: 'Compare 5 brands',
            resultShape: { rowCount: 5, hasTimeDimension: false, categoryCount: 5, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('bar')
        })
      })

      describe('Pie/Donut Chart (share, percentage, proportion)', () => {
        it('test_fr_5_1_pie_share', () => {
          const input: ChartSelectionInput = {
            queryText: 'What is the market share distribution?',
            resultShape: { rowCount: 5, hasTimeDimension: false, categoryCount: 5, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('pie')
        })

        it('test_fr_5_1_pie_percentage', () => {
          const input: ChartSelectionInput = {
            queryText: 'Show percentage by brand',
            resultShape: { rowCount: 4, hasTimeDimension: false, categoryCount: 4, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('pie')
        })

        it('test_fr_5_1_pie_proportion', () => {
          const input: ChartSelectionInput = {
            queryText: 'What proportion of sales does each brand have?',
            resultShape: { rowCount: 3, hasTimeDimension: false, categoryCount: 3, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('pie')
        })
      })

      describe('Stacked Bar or Heatmap (across, by, segmented + multiple dimensions)', () => {
        it('test_fr_5_1_stacked_bar_across', () => {
          const input: ChartSelectionInput = {
            queryText: 'Market share across regions and time',
            resultShape: { rowCount: 20, hasTimeDimension: true, categoryCount: 4, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('stacked_bar')
        })

        it('test_fr_5_1_stacked_bar_by_segmented', () => {
          const input: ChartSelectionInput = {
            queryText: 'Sales segmented by category and region',
            resultShape: { rowCount: 15, hasTimeDimension: false, categoryCount: 3, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('stacked_bar')
        })
      })

      describe('Scatter Plot (correlation, relationship)', () => {
        it('test_fr_5_1_scatter_correlation', () => {
          const input: ChartSelectionInput = {
            queryText: 'Show correlation between price and sales',
            resultShape: { rowCount: 50, hasTimeDimension: false, categoryCount: 0, valueCount: 2 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('scatter')
        })

        it('test_fr_5_1_scatter_relationship', () => {
          const input: ChartSelectionInput = {
            queryText: 'What is the relationship between marketing spend and revenue?',
            resultShape: { rowCount: 30, hasTimeDimension: false, categoryCount: 0, valueCount: 2 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('scatter')
        })
      })

      describe('Horizontal Bar Chart (ranking, top, bottom)', () => {
        it('test_fr_5_1_horizontal_bar_ranking', () => {
          const input: ChartSelectionInput = {
            queryText: 'Show ranking of brands by sales',
            resultShape: { rowCount: 10, hasTimeDimension: false, categoryCount: 10, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('horizontal_bar')
        })

        it('test_fr_5_1_horizontal_bar_top', () => {
          const input: ChartSelectionInput = {
            queryText: 'Top 10 brands by market share',
            resultShape: { rowCount: 10, hasTimeDimension: false, categoryCount: 10, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('horizontal_bar')
        })

        it('test_fr_5_1_horizontal_bar_bottom', () => {
          const input: ChartSelectionInput = {
            queryText: 'Bottom 5 brands by revenue',
            resultShape: { rowCount: 5, hasTimeDimension: false, categoryCount: 5, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('horizontal_bar')
        })
      })

      describe('Stacked Area Chart (share trend over time)', () => {
        it('test_fr_5_1_stacked_area_share_trend', () => {
          const input: ChartSelectionInput = {
            queryText: 'How did market share trend over time?',
            resultShape: { rowCount: 12, hasTimeDimension: true, categoryCount: 4, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('stacked_area')
        })
      })

      describe('Waterfall Chart (decomposition, driver, contribution)', () => {
        it('test_fr_5_1_waterfall_decomposition', () => {
          const input: ChartSelectionInput = {
            queryText: 'Decompose the change in market share',
            resultShape: { rowCount: 8, hasTimeDimension: false, categoryCount: 0, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('waterfall')
        })

        it('test_fr_5_1_waterfall_driver', () => {
          const input: ChartSelectionInput = {
            queryText: 'What are the drivers of revenue change?',
            resultShape: { rowCount: 6, hasTimeDimension: false, categoryCount: 0, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('waterfall')
        })

        it('test_fr_5_1_waterfall_contribution', () => {
          const input: ChartSelectionInput = {
            queryText: 'Show contribution of each factor',
            resultShape: { rowCount: 5, hasTimeDimension: false, categoryCount: 0, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('waterfall')
        })
      })

      describe('Bump Chart (ranking change, how did ranking evolve)', () => {
        it('test_fr_5_1_bump_ranking_change', () => {
          const input: ChartSelectionInput = {
            queryText: 'How did the ranking change over time?',
            resultShape: { rowCount: 8, hasTimeDimension: true, categoryCount: 5, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('bump')
        })

        it('test_fr_5_1_bump_ranking_evolve', () => {
          const input: ChartSelectionInput = {
            queryText: 'How did the brand rankings evolve over quarters?',
            resultShape: { rowCount: 12, hasTimeDimension: true, categoryCount: 6, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('bump')
        })
      })

      describe('Fallback to Table', () => {
        it('test_fr_5_1_table_fallback_no_matching_pattern', () => {
          const input: ChartSelectionInput = {
            queryText: 'Give me everything',
            resultShape: { rowCount: 100, hasTimeDimension: false, categoryCount: 1, valueCount: 1 }
          }
          const result = selectChartType(input)
          expect(result.chartType).toBe('table')
        })
      })
    })

    describe('Confidence scoring', () => {
      it('returns high confidence for clear KPI queries', () => {
        const input: ChartSelectionInput = {
          queryText: 'What is the total revenue?',
          resultShape: { rowCount: 1, hasTimeDimension: false, categoryCount: 0, valueCount: 1 }
        }
        const result = selectChartType(input)
        expect(result.confidence).toBeGreaterThan(0.8)
      })

      it('returns lower confidence for ambiguous queries', () => {
        const input: ChartSelectionInput = {
          queryText: 'Show data',
          resultShape: { rowCount: 10, hasTimeDimension: false, categoryCount: 1, valueCount: 1 }
        }
        const result = selectChartType(input)
        expect(result.confidence).toBeLessThan(0.8)
      })
    })
  })
})

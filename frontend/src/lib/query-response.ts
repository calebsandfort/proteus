/**
 * Query Response Type
 *
 * Interface for the query response from IU-3 API.
 * This is consumed by the visualization engine.
 */

export interface QueryResponse {
  data: Array<Record<string, unknown>>
  metadata: {
    tool: string
    row_count: number
    execution_time_ms: number
    pagination: {
      next_cursor: string | null
      has_more: boolean
    }
    aggregation_level: string
    metric_name?: string
    unit?: string
  }
}

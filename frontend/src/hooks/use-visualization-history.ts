'use client'

/**
 * Visualization History Hook
 * Implements FR-5.8: Visualization Updates
 *
 * Thumbnail generation and history management with localStorage persistence.
 */

import { useState, useCallback, useEffect } from 'react'

export interface VisualizationHistoryItem {
  id: string
  queryText: string
  timestamp: number
  thumbnail: string
  chartType: string
}

const STORAGE_KEY = 'proteus_visualization_history'
const MAX_HISTORY_ITEMS = 50

/**
 * Hook for managing visualization history and thumbnail generation
 */
export function useVisualizationHistory() {
  const [history, setHistory] = useState<VisualizationHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Load history from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as VisualizationHistoryItem[]
        setHistory(parsed)
      }
    } catch {
      console.error('Failed to load visualization history from localStorage')
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Generate a thumbnail from an ECharts instance
   * Uses the chart's getDataURL method to capture the visualization
   */
  const generateThumbnail = useCallback(
    async (chartInstance: unknown): Promise<string> => {
      return new Promise((resolve, reject) => {
        try {
          const chart = chartInstance as {
            getDataURL: (options?: { type?: string; pixelRatio?: number; backgroundColor?: string }) => string
          }

          if (!chart || typeof chart.getDataURL !== 'function') {
            throw new Error('Invalid chart instance: getDataURL not available')
          }

          const dataURL = chart.getDataURL({
            type: 'png',
            pixelRatio: 2, // Higher quality
            backgroundColor: '#ffffff',
          })

          resolve(dataURL)
        } catch (error) {
          reject(error)
        }
      })
    },
    []
  )

  /**
   * Add a new visualization to history
   */
  const addToHistory = useCallback(
    async (queryText: string, chartType: string, chartInstance?: unknown) => {
      const id = `viz_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`

      let thumbnail = ''
      if (chartInstance) {
        try {
          thumbnail = await generateThumbnail(chartInstance)
        } catch {
          // If thumbnail generation fails, use a placeholder
          thumbnail = ''
        }
      }

      const newItem: VisualizationHistoryItem = {
        id,
        queryText,
        timestamp: Date.now(),
        thumbnail,
        chartType,
      }

      setHistory((prev) => {
        const updated = [newItem, ...prev].slice(0, MAX_HISTORY_ITEMS)

        // Persist to localStorage
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        } catch {
          console.error('Failed to save visualization history to localStorage')
        }

        return updated
      })

      return id
    },
    [generateThumbnail]
  )

  /**
   * Remove a specific item from history
   */
  const removeFromHistory = useCallback((id: string) => {
    setHistory((prev) => {
      const updated = prev.filter((item) => item.id !== id)

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      } catch {
        console.error('Failed to update visualization history in localStorage')
      }

      return updated
    })
  }, [])

  /**
   * Clear all history
   */
  const clearHistory = useCallback(() => {
    setHistory([])

    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      console.error('Failed to clear visualization history from localStorage')
    }
  }, [])

  /**
   * Get a history item by ID
   */
  const getHistoryItem = useCallback(
    (id: string): VisualizationHistoryItem | undefined => {
      return history.find((item) => item.id === id)
    },
    [history]
  )

  return {
    history,
    isLoading,
    addToHistory,
    removeFromHistory,
    clearHistory,
    getHistoryItem,
    generateThumbnail,
  }
}

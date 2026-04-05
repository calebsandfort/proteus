"use client"

import { useState, useCallback, useEffect } from "react"

export interface ObservabilityState {
  level: 0 | 1 | 2 | 3
  isEnabled: boolean
}

const STORAGE_KEYS = {
  enabled: "proteus-observability-enabled",
  level: "proteus-observability-level",
} as const

function clampLevel(level: number): 0 | 1 | 2 | 3 {
  if (level < 0) return 0
  if (level > 3) return 0
  return level as 0 | 1 | 2 | 3
}

function loadFromStorage(key: string, defaultValue: boolean | number): boolean | number {
  if (typeof window === "undefined") return defaultValue

  try {
    const stored = localStorage.getItem(key)
    if (stored === null) return defaultValue

    if (key === STORAGE_KEYS.enabled) {
      return stored === "true"
    }

    if (key === STORAGE_KEYS.level) {
      const parsed = parseInt(stored, 10)
      if (isNaN(parsed)) return defaultValue
      return clampLevel(parsed)
    }

    return defaultValue
  } catch {
    return defaultValue
  }
}

function saveToStorage(key: string, value: boolean | number): void {
  if (typeof window === "undefined") return

  try {
    localStorage.setItem(key, String(value))
  } catch {
    // localStorage may be unavailable
  }
}

export function useObservability() {
  const [isEnabled, setIsEnabled] = useState<boolean>(() =>
    loadFromStorage(STORAGE_KEYS.enabled, false)
  )
  const [level, setLevelState] = useState<0 | 1 | 2 | 3>(() =>
    loadFromStorage(STORAGE_KEYS.level, 0) as 0 | 1 | 2 | 3
  )

  useEffect(() => {
    saveToStorage(STORAGE_KEYS.enabled, isEnabled)
  }, [isEnabled])

  useEffect(() => {
    saveToStorage(STORAGE_KEYS.level, level)
  }, [level])

  const toggle = useCallback(() => {
    setIsEnabled((prev) => !prev)
  }, [])

  const enable = useCallback(() => {
    setIsEnabled(true)
  }, [])

  const disable = useCallback(() => {
    setIsEnabled(false)
  }, [])

  const setLevel = useCallback((newLevel: 0 | 1 | 2 | 3) => {
    setLevelState(clampLevel(newLevel))
  }, [])

  return {
    isEnabled,
    level,
    toggle,
    enable,
    disable,
    setLevel,
  }
}

"use client"

import { useState, useCallback, useEffect } from "react"

const MOBILE_BREAKPOINT = 1024

interface UseSidebarOptions {
  onCollapseChange?: (isCollapsed: boolean) => void
}

export function useSidebar({ onCollapseChange }: UseSidebarOptions = {}) {
  const [isCollapsed, setIsCollapsed] = useState(true)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    if (typeof window === "undefined") return

    const mediaQuery = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)

    const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
      const mobile = e.matches
      setIsMobile(mobile)
      // Auto-collapse sidebar on mobile
      if (mobile) {
        setIsCollapsed(true)
        onCollapseChange?.(true)
      }
    }

    // Set initial state
    handleChange(mediaQuery)

    // Modern API
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener("change", handleChange)
      return () => mediaQuery.removeEventListener("change", handleChange)
    } else {
      // Legacy API
      mediaQuery.addListener(handleChange)
      return () => mediaQuery.removeListener(handleChange)
    }
  }, [onCollapseChange])

  const toggle = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev
      onCollapseChange?.(next)
      return next
    })
  }, [onCollapseChange])

  const open = useCallback(() => {
    setIsCollapsed(false)
    onCollapseChange?.(false)
  }, [onCollapseChange])

  const close = useCallback(() => {
    setIsCollapsed(true)
    onCollapseChange?.(true)
  }, [onCollapseChange])

  return {
    isCollapsed,
    isMobile,
    toggle,
    open,
    close,
  }
}

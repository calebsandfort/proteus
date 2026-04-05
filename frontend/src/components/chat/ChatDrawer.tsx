"use client"

import { cn } from "@/lib/utils"
import { FloatingActionButton } from "./FloatingActionButton"
import { useSidebar } from "@/hooks/use-sidebar"
import { useEffect } from "react"

interface ChatDrawerProps {
  children?: React.ReactNode
  width?: number
  className?: string
}

const DEFAULT_WIDTH = 400
const MIN_WIDTH = 380
const MAX_WIDTH = 420

export function ChatDrawer({ children, width = DEFAULT_WIDTH, className }: ChatDrawerProps) {
  const { isCollapsed, isMobile, toggle, open, close } = useSidebar()

  const clampedWidth = Math.min(Math.max(width, MIN_WIDTH), MAX_WIDTH)

  // Close drawer when switching to desktop
  useEffect(() => {
    if (!isMobile && !isCollapsed) {
      // On desktop, drawer content is not shown but sidebar is used
    }
  }, [isMobile, isCollapsed])

  if (!isMobile) {
    // On desktop, this component doesn't render anything
    // The parent should use ChatSidebar instead
    return null
  }

  return (
    <>
      <FloatingActionButton onClick={toggle} isOpen={!isCollapsed} />

      {/* Backdrop */}
      {!isCollapsed && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm"
          onClick={close}
          aria-hidden="true"
        />
      )}

      {/* Drawer panel */}
      <div
        data-testid="chat-drawer"
        className={cn(
          "fixed z-50 h-[calc(100vh-6rem)] w-full max-w-sm",
          "right-0 top-16 rounded-l-xl bg-white shadow-lg",
          "transform transition-transform duration-300 ease-in-out",
          isCollapsed ? "translate-x-full" : "translate-x-0",
          className
        )}
        style={{ maxWidth: clampedWidth }}
      >
        <div className="h-full flex flex-col">{children}</div>
      </div>
    </>
  )
}

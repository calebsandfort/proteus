"use client"

import { CopilotChat as CopilotChatUI } from "@copilotkit/react-ui"
import "@copilotkit/react-ui/styles.css"
import { cn } from "@/lib/utils"

interface ChatSidebarProps {
  width?: number
  isCollapsed?: boolean
  className?: string
}

const DEFAULT_WIDTH = 400
const MIN_WIDTH = 380
const MAX_WIDTH = 420

export function ChatSidebar({
  width = DEFAULT_WIDTH,
  isCollapsed = false,
  className,
}: ChatSidebarProps) {
  // Clamp width to valid range
  const clampedWidth = Math.min(Math.max(width, MIN_WIDTH), MAX_WIDTH)

  if (isCollapsed) {
    return null
  }

  return (
    <aside
      data-testid="chat-sidebar"
      className={cn(
        "flex flex-col h-full border-l border-slate-200 bg-white shadow-md",
        className
      )}
      style={{ width: clampedWidth, minWidth: clampedWidth, maxWidth: clampedWidth }}
    >
      <div className="flex-1 overflow-hidden">
        <CopilotChatUI
          labels={{
            title: "AI Assistant",
            initial: "Hi! How can I help you today?",
          }}
        />
      </div>
    </aside>
  )
}

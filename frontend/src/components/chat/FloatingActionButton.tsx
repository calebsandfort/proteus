"use client"

import { cn } from "@/lib/utils"
import { MessageSquarePlus, X } from "lucide-react"

interface FloatingActionButtonProps {
  onClick: () => void
  isOpen: boolean
  className?: string
  ariaLabel?: string
}

export function FloatingActionButton({
  onClick,
  isOpen,
  className,
  ariaLabel,
}: FloatingActionButtonProps) {
  return (
    <button
      data-testid="fab-button"
      type="button"
      onClick={onClick}
      aria-expanded={isOpen}
      aria-label={ariaLabel || (isOpen ? "Close chat" : "Open chat")}
      className={cn(
        "fixed bottom-6 right-6 z-50 flex items-center justify-center",
        "w-14 h-14 rounded-full shadow-lg transition-all duration-200",
        "bg-blue-600 hover:bg-blue-700 active:bg-blue-800",
        "text-white",
        isOpen && "bg-slate-600 hover:bg-slate-700",
        className
      )}
    >
      {isOpen ? (
        <X className="size-6" />
      ) : (
        <MessageSquarePlus className="size-6" />
      )}
    </button>
  )
}

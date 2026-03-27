import type { Metadata } from "next"
import { Toaster } from "@/components/ui/sonner"
import { CopilotProvider } from "@/components/providers/copilot-provider"
import "./globals.css"

export const metadata: Metadata = {
  title: "Proteus",
  description: "AI-powered financial ledger built with Next.js, FastAPI, and TimescaleDB",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <CopilotProvider>
          {children}
          <Toaster />
        </CopilotProvider>
      </body>
    </html>
  )
}

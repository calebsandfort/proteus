"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import {
  Brain,
  MessageSquare,
  BarChart3,
  History,
  ChevronRight,
  Menu,
  X,
  Zap,
  TrendingUp,
  Database,
} from "lucide-react"
import { Button } from "@/components/ui/button"

const features = [
  {
    icon: <MessageSquare size={24} />,
    title: "Natural Language Queries",
    description:
      "Ask questions about your data in plain English. Proteus translates your intent into precise SQL queries across your time-series data.",
    highlight: "blue",
  },
  {
    icon: <BarChart3 size={24} />,
    title: "Instant Visualizations",
    description:
      "Every answer comes rendered with the right chart. Line charts for trends, bar charts for comparisons, scatter plots for correlations.",
    highlight: "amber",
  },
  {
    icon: <History size={24} />,
    title: "Historical Analysis",
    description:
      "Travel through time across your data. Identify seasonal patterns, track long-term trends, and compare performance across any period.",
    highlight: "blue",
  },
]

const metrics = [
  { label: "Query Latency", value: "<200ms", trend: "positive" },
  { label: "Data Points", value: "2.4B", trend: "neutral" },
  { label: "Uptime", value: "99.99%", trend: "positive" },
]

export default function HomePage() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Navigation */}
      <nav className="fixed w-full z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-sm">
                <Brain size={16} className="text-white" />
              </div>
              <span className="text-xl font-semibold tracking-tight text-slate-900">
                Proteus
              </span>
            </div>

            <div className="hidden md:flex items-center gap-8">
              <a
                href="#features"
                className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors"
              >
                Features
              </a>
              <a
                href="#how-it-works"
                className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors"
              >
                How It Works
              </a>
              <a
                href="#metrics"
                className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors"
              >
                Performance
              </a>
              <Button variant="outline" asChild className="border-slate-200 text-slate-700 hover:border-blue-300 hover:text-blue-600">
                <Link href="/sign-in">Sign In</Link>
              </Button>
              <Button asChild className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm">
                <Link href="/sign-up">Get Started</Link>
              </Button>
            </div>

            <div className="md:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="p-2 text-slate-500 hover:text-slate-900"
                aria-label="Toggle menu"
              >
                {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>
        </div>

        {isMenuOpen && (
          <div className="md:hidden bg-white border-t border-slate-200 px-4 py-6 space-y-4">
            <a
              href="#features"
              className="block text-sm font-medium text-slate-600 hover:text-blue-600"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="block text-sm font-medium text-slate-600 hover:text-blue-600"
            >
              How It Works
            </a>
            <a
              href="#metrics"
              className="block text-sm font-medium text-slate-600 hover:text-blue-600"
            >
              Performance
            </a>
            <div className="flex gap-3 pt-2">
              <Button
                variant="outline"
                className="flex-1 border-slate-200 text-slate-700"
                asChild
              >
                <Link href="/sign-in">Sign In</Link>
              </Button>
              <Button
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                asChild
              >
                <Link href="/sign-up">Get Started</Link>
              </Button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-40 pb-24 lg:pt-52 lg:pb-32 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 relative z-10">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-medium mb-8">
              <Zap size={12} />
              Powered by AI
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-semibold tracking-tight text-slate-900 mb-6 leading-[1.1]">
              Ask your data.
              <br />
              <span className="text-blue-600">Get answers.</span>
            </h1>

            <p className="text-xl text-slate-600 mb-10 leading-relaxed max-w-2xl">
              Proteus transforms natural language questions into precise queries across your
              time-series data. No SQL required — just ask, and visualize.
            </p>

            <div className="flex flex-col sm:flex-row items-start gap-4">
              <Button asChild size="lg" className="bg-blue-600 hover:bg-blue-700 text-white shadow-md">
                <Link href="/sign-up">
                  Start for Free <ChevronRight size={18} className="ml-1" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" asChild className="border-slate-200 text-slate-700 hover:border-blue-300 hover:text-blue-600">
                <Link href="/chat">
                  Try the Demo
                </Link>
              </Button>
            </div>
          </div>
        </div>

        {/* Decorative background */}
        <div className="absolute top-0 right-0 w-1/2 h-full pointer-events-none overflow-hidden">
          <div className="absolute top-20 right-20 w-96 h-96 bg-blue-100 rounded-full opacity-50 blur-3xl" />
          <div className="absolute top-40 right-60 w-64 h-64 bg-amber-100 rounded-full opacity-40 blur-3xl" />
        </div>
      </section>

      {/* Metrics Strip */}
      <section id="metrics" className="py-12 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {metrics.map(({ label, value, trend }) => (
              <div key={label} className="flex flex-col items-center text-center">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400 mb-2">
                  {label}
                </p>
                <p className={`text-3xl font-semibold tabular-nums ${
                  trend === "positive" ? "text-emerald-600" : "text-slate-900"
                }`}>
                  {value}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-semibold tracking-tight text-slate-900 mb-4">
              Query anything. Understand everything.
            </h2>
            <p className="text-slate-600 max-w-xl mx-auto">
              Proteus connects to your TimescaleDB and translates natural language into
              optimized SQL — returning answers as clean charts and actionable metrics.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                title: "Ask in Plain English",
                description:
                  "Type your question as if you were talking to a data analyst. &quot;What was our revenue by region last quarter?&quot;",
                code: "What was Chipotle's market share in Texas last quarter?",
              },
              {
                step: "02",
                title: "Proteus Queries Your Data",
                description:
                  "Our AI interprets your intent, constructs an optimized SQL query, and executes it against your TimescaleDB.",
                code: "SELECT region, SUM(revenue) FROM sales WHERE brand = 'Chipotle' AND period = 'Q3' GROUP BY region",
              },
              {
                step: "03",
                title: "Get Instant Visualization",
                description:
                  "Every answer comes back as a clear chart — with the ability to drill down, filter, and explore further.",
                code: "chart.render(barChart, { dimensions: ['Texas'], metrics: [0.124] })",
              },
            ].map(({ step, title, description, code }) => (
              <div
                key={step}
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono font-medium text-blue-600 bg-blue-50 border border-blue-200 px-2 py-1 rounded">
                    {step}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
                <div className="rounded-lg bg-slate-50 border border-slate-100 p-3">
                  <code className="text-xs font-mono text-slate-600 leading-relaxed">
                    {code}
                  </code>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-semibold tracking-tight text-slate-900 mb-4">
              Built for analytical teams
            </h2>
            <p className="text-slate-600 max-w-xl mx-auto">
              From startup metrics to enterprise data warehouses, Proteus scales with your
              questions — not just your data.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map(({ icon, title, description, highlight }) => (
              <div
                key={title}
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow"
              >
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${
                    highlight === "blue"
                      ? "bg-blue-50 text-blue-600 border border-blue-200"
                      : "bg-amber-50 text-amber-600 border border-amber-200"
                  }`}
                >
                  {icon}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stack Section */}
      <section className="py-24 bg-slate-50 border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <h2 className="text-3xl font-semibold tracking-tight text-slate-900">
                  The complete analytical stack
                </h2>
                <p className="text-slate-600 text-lg leading-relaxed">
                  Proteus combines a Next.js frontend, FastAPI backend, and TimescaleDB into
                  a unified query experience — purpose-built for time-series data at any
                  scale.
                </p>
              </div>

              <div className="space-y-6">
                {[
                  {
                    icon: <Brain size={20} />,
                    title: "LangGraph Agent Pipeline",
                    description:
                      "Stateful AI orchestration handles multi-turn conversations and complex analytical workflows.",
                  },
                  {
                    icon: <Database size={20} />,
                    title: "TimescaleDB",
                    description:
                      "PostgreSQL with time-series extensions. Built for petabyte-scale analytics with native compression.",
                  },
                  {
                    icon: <TrendingUp size={20} />,
                    title: "CopilotKit Integration",
                    description:
                      "Pre-built chat UI with AG-UI protocol. Your users get ChatGPT-level interaction out of the box.",
                  },
                ].map(({ icon, title, description }) => (
                  <div key={title} className="flex gap-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center border border-blue-200">
                      {icon}
                    </div>
                    <div>
                      <h4 className="text-base font-medium text-slate-900">{title}</h4>
                      <p className="text-sm text-slate-600 mt-0.5">{description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Visual stack diagram */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <div className="space-y-3">
                {[
                  { label: "Frontend", tech: "Next.js + CopilotKit", color: "blue" },
                  { label: "Backend", tech: "FastAPI + LangGraph", color: "amber" },
                  { label: "Database", tech: "TimescaleDB", color: "blue" },
                ].map(({ label, tech, color }, index) => (
                  <div key={label}>
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-24 text-xs font-medium ${
                          color === "blue" ? "text-blue-600" : "text-amber-600"
                        }`}
                      >
                        {label}
                      </div>
                      <div className="flex-1 h-8 bg-slate-50 rounded-lg flex items-center px-3 border border-slate-200">
                        <span className="text-xs font-mono text-slate-600">{tech}</span>
                      </div>
                    </div>
                    {index < 2 && (
                      <div className="flex items-center">
                        <div className="w-24" />
                        <div className="flex items-center">
                          <ChevronRight size={14} className="text-slate-300" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-white border-t border-slate-200">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-slate-900 mb-4">
            Start querying in minutes
          </h2>
          <p className="text-slate-600 mb-10 text-lg">
            Connect your TimescaleDB, deploy the stack, and begin asking questions your
            data has never answered before.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" className="bg-blue-600 hover:bg-blue-700 text-white shadow-md">
              <Link href="/sign-up">
                Get Started Free <ChevronRight size={18} className="ml-1" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" asChild className="border-slate-200 text-slate-700 hover:border-blue-300 hover:text-blue-600">
              <Link href="/sign-in">Sign In</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-slate-50 border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Brain size={14} className="text-white" />
            </div>
            <span className="font-semibold text-slate-900 tracking-tight">Proteus</span>
          </div>
          <div className="text-sm text-slate-500 font-mono">
            AI-Powered Analytics on TimescaleDB
          </div>
          <div className="flex gap-8">
            <a
              href="#"
              className="text-sm font-medium text-slate-500 hover:text-blue-600 transition-colors"
            >
              Documentation
            </a>
            <a
              href="#"
              className="text-sm font-medium text-slate-500 hover:text-blue-600 transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}

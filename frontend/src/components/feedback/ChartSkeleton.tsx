"use client"

import { cn } from "@/lib/utils"

type ChartType = "bar" | "line" | "pie" | "area"

interface ChartSkeletonProps {
  chartType?: ChartType
  height?: number
  width?: number
  className?: string
}

const DEFAULT_HEIGHT = 256
const DEFAULT_WIDTH = 512

function BarChartSkeleton({ height }: { height: number }) {
  const bars = [65, 85, 45, 70, 55, 80, 60, 75]
  const barWidth = 100 / bars.length

  return (
    <div className="flex items-end justify-between h-full gap-2 px-4">
      {bars.map((barHeight, i) => (
        <div
          key={i}
          className="bg-slate-200 rounded-t animate-pulse"
          style={{
            height: `${barHeight}%`,
            width: `calc(${barWidth}% - 8px)`,
          }}
        />
      ))}
    </div>
  )
}

function LineChartSkeleton({ height }: { height: number }) {
  const points = [
    { x: 0, y: 60 },
    { x: 15, y: 40 },
    { x: 30, y: 70 },
    { x: 45, y: 30 },
    { x: 60, y: 55 },
    { x: 75, y: 35 },
    { x: 90, y: 50 },
  ]

  return (
    <svg
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      className="w-full h-full"
    >
      {/* Grid lines */}
      {[25, 50, 75].map((y) => (
        <line
          key={y}
          x1="0"
          y1={y}
          x2="100"
          y2={y}
          stroke="#e2e8f0"
          strokeWidth="0.5"
          strokeDasharray="2,2"
        />
      ))}

      {/* Area fill */}
      <path
        d="M0,60 L15,40 L30,70 L45,30 L60,55 L75,35 L90,50 L100,45 L100,100 L0,100 Z"
        fill="url(#shimmer-gradient)"
        opacity="0.3"
        className="animate-pulse"
      />

      {/* Line */}
      <path
        d="M0,60 L15,40 L30,70 L45,30 L60,55 L75,35 L90,50 L100,45"
        fill="none"
        stroke="#cbd5e1"
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="animate-pulse"
      />

      <defs>
        <linearGradient id="shimmer-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#e2e8f0" />
          <stop offset="50%" stopColor="#f1f5f9" />
          <stop offset="100%" stopColor="#e2e8f0" />
        </linearGradient>
      </defs>
    </svg>
  )
}

function PieChartSkeleton() {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className="w-3/4 h-3/4 rounded-full bg-slate-200 animate-pulse" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-1/2 h-1/2 rounded-full bg-slate-100 animate-pulse" />
      </div>
    </div>
  )
}

function AreaChartSkeleton() {
  return <LineChartSkeleton height={256} />
}

export function ChartSkeleton({
  chartType = "bar",
  height = DEFAULT_HEIGHT,
  width = DEFAULT_WIDTH,
  className,
}: ChartSkeletonProps) {
  return (
    <div
      data-testid="chart-skeleton"
      className={cn(
        "relative overflow-hidden rounded-lg bg-slate-50 border border-slate-100",
        "bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100",
        "bg-[length:200%_100%] animate-pulse",
        className
      )}
      style={{ height, width }}
    >
      {/* Chart shape overlay */}
      <div className="absolute inset-0 p-3">
        {chartType === "bar" && <BarChartSkeleton height={height - 24} />}
        {chartType === "line" && <LineChartSkeleton height={height - 24} />}
        {chartType === "pie" && <PieChartSkeleton />}
        {chartType === "area" && <AreaChartSkeleton />}
      </div>

      {/* Shimmer overlay */}
      <div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/60 to-transparent"
        style={{
          backgroundSize: "200% 100%",
          animation: "shimmer 1.5s infinite",
        }}
      />
    </div>
  )
}

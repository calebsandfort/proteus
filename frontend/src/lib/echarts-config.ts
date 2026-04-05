/**
 * ECharts Configuration
 * Base configurations for all chart types using the design system color palette.
 */

import type { EChartsOption } from 'echarts'

// Color sequence from AGENTS.md Design System
export const CHART_COLORS = [
  '#2563EB', // blue-600
  '#F59E0B', // amber-500
  '#10B981', // emerald-500
  '#8B5CF6', // violet-500
  '#EC4899', // pink-500
  '#6366F1', // indigo-500
]

// Tooltip style from AGENTS.md
export const TOOLTIP_STYLE = {
  backgroundColor: '#0F172A',
  textStyle: {
    color: '#FFFFFF',
    fontSize: 12,
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  borderWidth: 0,
  borderRadius: 8,
  padding: [12, 16],
}

// Grid style from AGENTS.md
export const GRID_STYLE = {
  left: '10%',
  right: '10%',
  top: '15%',
  bottom: '15%',
  containLabel: true,
}

// Base chart options with common styling
export const BASE_CHART_OPTIONS: EChartsOption = {
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    ...TOOLTIP_STYLE,
  },
  grid: GRID_STYLE,
  color: CHART_COLORS,
}

// Legend configuration
export const LEGEND_CONFIG = {
  bottom: 0,
  textStyle: {
    color: '#475569', // slate-600
    fontSize: 12,
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  itemWidth: 14,
  itemHeight: 10,
  itemGap: 20,
}

// Zoom configuration for time series (FR-5.6)
export const ZOOM_CONFIG = {
  type: 'inside' as const,
  start: 0,
  end: 100,
  zoomLock: false,
}

// Data zoom slider config
export const DATA_ZOOM_SLIDER_CONFIG = {
  type: 'slider' as const,
  show: true,
  bottom: 40,
  height: 20,
  borderColor: '#CBD5E1', // slate-300
  backgroundColor: '#F1F5F9', // slate-100
  fillerColor: 'rgba(37, 99, 235, 0.1)', // blue-600 with opacity
  handleStyle: {
    color: '#2563EB', // blue-600
    borderColor: '#2563EB',
  },
  textStyle: {
    color: '#94A3B8', // slate-400
    fontSize: 11,
  },
  dataBackground: {
    lineStyle: {
      color: '#CBD5E1', // slate-300
    },
    areaStyle: {
      color: 'rgba(37, 99, 235, 0.05)', // blue-600 with very low opacity
    },
  },
}

/**
 * Configure a line chart
 */
export function configureLineChart(
  data: { xAxis: string[]; series: Array<{ name: string; data: number[] }> },
  enableZoom = false
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    series: data.series.map((s, i) => ({
      name: s.name,
      type: 'line',
      data: s.data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 2 },
      areaStyle: i === 0 ? { color: 'rgba(37, 99, 235, 0.1)' } : undefined,
    })),
    legend: { ...LEGEND_CONFIG },
    dataZoom: enableZoom ? [ZOOM_CONFIG, DATA_ZOOM_SLIDER_CONFIG] : undefined,
  }
}

/**
 * Configure a vertical bar chart
 */
export function configureBarChart(
  data: { xAxis: string[]; series: Array<{ name: string; data: number[] }> }
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    series: data.series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      barWidth: '60%',
      itemStyle: { borderRadius: [4, 4, 0, 0] },
    })),
    legend: { ...LEGEND_CONFIG },
  }
}

/**
 * Configure a horizontal bar chart
 */
export function configureHorizontalBarChart(
  data: { yAxis: string[]; series: Array<{ name: string; data: number[] }> }
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    yAxis: {
      type: 'category',
      data: data.yAxis,
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    series: data.series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      barWidth: '60%',
      itemStyle: { borderRadius: [0, 4, 4, 0] },
    })),
    legend: { ...LEGEND_CONFIG },
  }
}

/**
 * Configure a pie chart
 */
export function configurePieChart(
  data: { name: string; value: number }[]
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          color: '#475569',
          fontSize: 11,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold' as const,
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        labelLine: {
          show: true,
          lineStyle: { color: '#94A3B8' },
        },
        data: data,
      },
    ],
  }
}

/**
 * Configure a donut chart (same as pie but with smaller inner radius)
 */
export function configureDonutChart(
  data: { name: string; value: number }[]
): EChartsOption {
  return {
    ...configurePieChart(data),
    series: [
      {
        type: 'pie',
        radius: ['55%', '75%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          color: '#475569',
          fontSize: 11,
          position: 'outside',
          formatter: '{b}: {d}%',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold' as const,
          },
        },
        labelLine: {
          show: true,
          lineStyle: { color: '#94A3B8' },
        },
        data: data,
      },
    ],
  }
}

/**
 * Configure a scatter plot
 */
export function configureScatterChart(
  data: { name: string; data: Array<[number, number]> }[]
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    series: data.map((s, i) => ({
      name: s.name,
      type: 'scatter',
      data: s.data,
      symbolSize: 10,
      itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    })),
    legend: { ...LEGEND_CONFIG },
  }
}

/**
 * Configure a stacked bar chart
 */
export function configureStackedBarChart(
  data: { xAxis: string[]; series: Array<{ name: string; data: number[] }> }
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    series: data.series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      stack: 'total',
      barWidth: '60%',
      itemStyle: { borderRadius: [0, 0, 0, 0] },
      emphasis: { focus: 'series' as const },
    })),
    legend: { ...LEGEND_CONFIG },
  }
}

/**
 * Configure a stacked area chart
 */
export function configureStackedAreaChart(
  data: { xAxis: string[]; series: Array<{ name: string; data: number[] }> },
  enableZoom = false
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    series: data.series.map((s, i) => ({
      name: s.name,
      type: 'line',
      data: s.data,
      stack: 'total',
      smooth: true,
      lineStyle: { width: 1 },
      areaStyle: {
        opacity: 0.6,
        color: CHART_COLORS[i % CHART_COLORS.length],
      },
      emphasis: { focus: 'series' as const },
    })),
    legend: { ...LEGEND_CONFIG },
    dataZoom: enableZoom ? [ZOOM_CONFIG, DATA_ZOOM_SLIDER_CONFIG] : undefined,
  }
}

/**
 * Configure a waterfall chart
 */
export function configureWaterfallChart(
  data: { name: string; value: number; type: 'increase' | 'decrease' | 'total' }[]
): EChartsOption {
  const processedData = data.map((item, index) => {
    if (item.type === 'total') {
      return {
        value: item.value,
        itemStyle: { color: CHART_COLORS[0] },
      }
    }
    return {
      value: item.type === 'increase' ? item.value : -item.value,
      itemStyle: {
        color: item.type === 'increase' ? CHART_COLORS[2] : CHART_COLORS[1], // emerald or amber
      },
    }
  })

  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'category',
      data: data.map((d) => d.name),
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
    },
    series: [
      {
        type: 'bar',
        data: processedData,
        barWidth: '50%',
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: {
          show: true,
          position: 'top',
          color: '#475569',
          fontSize: 11,
          formatter: (params: any) => Math.abs(params.value).toLocaleString(),
        },
      },
    ],
  }
}

/**
 * Configure a bump chart (for ranking changes over time)
 */
export function configureBumpChart(
  data: {
    xAxis: string[]
    series: Array<{ name: string; data: Array<{ value: number; rank: number }> }>
  }
): EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      inverse: true, // Lower rank = better, should be at top
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' as const } },
      min: 1,
    },
    series: data.series.map((s, i) => ({
      name: s.name,
      type: 'line',
      data: s.data.map((d) => d.rank),
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 2, color: CHART_COLORS[i % CHART_COLORS.length] },
      itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
      emphasis: {
        focus: 'series' as const,
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.3)' },
      },
    })),
    legend: { ...LEGEND_CONFIG },
  }
}

import { useEffect, useMemo, useRef, useState } from 'react'
import Plotly from 'plotly.js-dist-min'

import type { PlotlyChartPayload } from '@/types/chat'

interface PlotlyFigurePayload {
  data?: unknown[]
  layout?: Record<string, unknown>
  config?: Record<string, unknown>
}

interface PlotlyChartProps {
  chart: PlotlyChartPayload
}

function cloneMutable<T>(value: T): T {
  if (typeof structuredClone === 'function') {
    return structuredClone(value)
  }
  return JSON.parse(JSON.stringify(value)) as T
}

export function PlotlyChart({ chart }: PlotlyChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [renderError, setRenderError] = useState<string | null>(null)

  const figure = useMemo(
    () => chart.figure as PlotlyFigurePayload,
    [chart.figure],
  )

  useEffect(() => {
    const container = containerRef.current
    if (!container || !Array.isArray(figure.data) || figure.data.length === 0) {
      return
    }
    const chartData = figure.data

    let isDisposed = false
    let removeResizeListener = () => {}

    const mountChart = async () => {
      try {
        if (isDisposed || !containerRef.current) {
          return
        }

        const layout = {
          autosize: true,
          margin: { l: 40, r: 20, t: 40, b: 40 },
          ...(figure.layout || {}),
        }

        const config = {
          responsive: true,
          displaylogo: false,
          ...(figure.config || {}),
        }

        await Plotly.react(
          containerRef.current,
          cloneMutable(chartData),
          cloneMutable(layout),
          cloneMutable(config),
        )
        setRenderError(null)

        const handleResize = () => {
          if (containerRef.current) {
            void Plotly.Plots.resize(containerRef.current)
          }
        }

        window.addEventListener('resize', handleResize)
        removeResizeListener = () =>
          window.removeEventListener('resize', handleResize)
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : 'Unknown plotting error'
        setRenderError(`Unable to render chart: ${errorMessage}`)
      }
    }

    void mountChart()

    return () => {
      isDisposed = true
      removeResizeListener()
      Plotly.purge(container)
    }
  }, [figure])

  if (!Array.isArray(figure.data) || figure.data.length === 0) {
    return (
      <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
        Chart payload is empty.
      </div>
    )
  }

  if (renderError) {
    return (
      <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
        {renderError}
      </div>
    )
  }

  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="border-b border-slate-100 bg-slate-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
        {chart.title || `${chart.chart_type} chart`}
      </div>
      <div ref={containerRef} className="h-[320px] w-full" />
    </div>
  )
}

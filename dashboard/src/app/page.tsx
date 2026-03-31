'use client'

import { useEffect, useState, useCallback } from 'react'
import { fetchRuns, checkHealth } from '@/lib/data'
import type { RunData } from '@/lib/types'
import { HeatmapMatrix } from '@/components/HeatmapMatrix'
import { SweepControl, RefreshButton } from '@/components/SweepControl'

export default function Page() {
  const [runs, setRuns] = useState<RunData[]>([])
  const [loading, setLoading] = useState(true)
  const [apiConnected, setApiConnected] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [health, data] = await Promise.all([
        checkHealth().catch(() => null),
        fetchRuns().catch(() => []),
      ])
      setApiConnected(health?.status === 'ok')
      setRuns(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  return (
    <main className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Persona Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">
              UX friction heatmap across digital literacy personas and user flows.
              Click any cell to drill into confusion points and suggestions.
            </p>
          </div>
          <RefreshButton onRefresh={loadData} loading={loading} />
        </div>

        <SweepControl onSweepComplete={loadData} apiConnected={apiConnected} />

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-sm text-gray-400">Loading results...</div>
          </div>
        ) : (
          <HeatmapMatrix runs={runs} />
        )}
      </div>
    </main>
  )
}

import { readPersonaRuns, loadRunData } from '@/lib/data'
import type { RunData } from '@/lib/types'
import { HeatmapMatrix } from '@/components/HeatmapMatrix'

export default function Page() {
  const runIds = readPersonaRuns()
  const runs: RunData[] = runIds.map(id => ({
    runId: id,
    results: loadRunData(id),
  }))

  return (
    <main className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Persona Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            UX friction heatmap across digital literacy personas and user flows.
            Click any cell to drill into confusion points and suggestions.
          </p>
        </div>
        <HeatmapMatrix runs={runs} />
      </div>
    </main>
  )
}

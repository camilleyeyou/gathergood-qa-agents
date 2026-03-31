import { readPersonaRuns, loadRunData } from '@/lib/data'
import type { RunData } from '@/lib/types'

export default function Page() {
  const runIds = readPersonaRuns()
  const runs: RunData[] = runIds.map(id => ({
    runId: id,
    results: loadRunData(id),
  }))

  return (
    <main className="min-h-screen bg-gray-50 p-4 md:p-8">
      <h1 className="text-2xl font-bold mb-6">Persona Dashboard</h1>
      <p className="text-gray-500">
        {runs.length > 0
          ? `${runs.length} run(s) loaded`
          : 'No persona runs found. Run the persona sweep to generate data.'}
      </p>
    </main>
  )
}

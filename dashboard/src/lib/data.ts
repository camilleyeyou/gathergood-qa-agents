import type { PersonaResult, RunData } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchRuns(): Promise<RunData[]> {
  const res = await fetch(`${API_URL}/results`, { cache: 'no-store' })
  if (!res.ok) return []
  const data = await res.json()

  const runs: RunData[] = []
  for (const run of data.runs) {
    const detailRes = await fetch(`${API_URL}/results/${run.run_id}`, { cache: 'no-store' })
    if (!detailRes.ok) continue
    const detail = await detailRes.json()
    runs.push({
      runId: run.run_id,
      results: detail.results as PersonaResult[],
    })
  }
  return runs
}

export async function startSweep(personas?: string[], flows?: string[]): Promise<{ job_id: string }> {
  const res = await fetch(`${API_URL}/sweep`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ personas: personas ?? null, flows: flows ?? null }),
  })
  if (!res.ok) throw new Error(`Failed to start sweep: ${res.statusText}`)
  return res.json()
}

export async function pollSweepStatus(jobId: string): Promise<{
  status: string
  run_id: string | null
  error: string | null
  stdout: string | null
}> {
  const res = await fetch(`${API_URL}/sweep/${jobId}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to poll sweep: ${res.statusText}`)
  return res.json()
}

export async function checkHealth(): Promise<{ status: string; anthropic_key_configured: boolean }> {
  const res = await fetch(`${API_URL}/health`, { cache: 'no-store' })
  if (!res.ok) throw new Error('API unreachable')
  return res.json()
}

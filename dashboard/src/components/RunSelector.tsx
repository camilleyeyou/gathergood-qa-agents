'use client'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { DeltaBadge } from '@/components/DeltaBadge'
import { type RunData } from '@/lib/types'

interface RunSelectorProps {
  runs: RunData[]
  activeIndex: number
  onRunChange: (index: number) => void
}

/**
 * Format a run ID for display. If the runId looks like an ISO timestamp
 * (e.g. "2026-03-30T12-00-00"), convert dashes-in-time back to colons and
 * format as a readable date. Otherwise show raw ID.
 */
function formatRunId(runId: string): string {
  // Pattern: YYYY-MM-DDTHH-MM-SS (filesystem-safe ISO timestamp)
  const match = runId.match(/^(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})$/)
  if (match) {
    const [, date, hh, mm, ss] = match
    try {
      const iso = `${date}T${hh}:${mm}:${ss}Z`
      const d = new Date(iso)
      return d.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      // fall through to raw
    }
  }
  return runId
}

/**
 * Compute the average friction delta between run at `idx` and the next older
 * run at `idx + 1`. Returns `{ delta, direction }` from computeDelta.
 * When there is no older run, returns same/0.
 */
function aggregateDelta(
  runs: RunData[],
  idx: number
): { delta: number; direction: 'up' | 'down' | 'same' } {
  if (idx >= runs.length - 1) {
    return { delta: 0, direction: 'same' }
  }

  const current = runs[idx]
  const previous = runs[idx + 1]

  const prevScores: Record<string, number> = {}
  for (const r of previous.results) {
    prevScores[`${r.persona}__${r.flow}`] = r.friction_score
  }

  let totalDelta = 0
  let count = 0
  for (const r of current.results) {
    const prev = prevScores[`${r.persona}__${r.flow}`]
    if (prev !== undefined) {
      totalDelta += r.friction_score - prev
      count++
    }
  }

  if (count === 0) return { delta: 0, direction: 'same' }

  const avg = totalDelta / count
  if (avg === 0) return { delta: 0, direction: 'same' }
  return {
    delta: Math.abs(avg),
    direction: avg > 0 ? 'up' : 'down',
  }
}

export function RunSelector({ runs, activeIndex, onRunChange }: RunSelectorProps) {
  if (runs.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="text-sm font-medium text-gray-700 shrink-0">Run:</label>

      <Select
        value={String(activeIndex)}
        onValueChange={(value: string | null) => { if (value !== null) onRunChange(Number(value)) }}
        disabled={runs.length === 1}
      >
        <SelectTrigger className="w-auto min-w-[200px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {runs.map((run, idx) => {
            const { delta, direction } = aggregateDelta(runs, idx)
            return (
              <SelectItem key={run.runId} value={String(idx)}>
                <span className="flex items-center gap-2">
                  <span>{formatRunId(run.runId)}{idx === 0 ? ' (latest)' : ''}</span>
                  {delta > 0 && <DeltaBadge delta={delta} direction={direction} />}
                </span>
              </SelectItem>
            )
          })}
        </SelectContent>
      </Select>

      <span className="text-xs text-gray-500">
        Run {activeIndex + 1} of {runs.length}
        {runs.length > 1 ? '' : ' — no comparison available'}
      </span>
    </div>
  )
}

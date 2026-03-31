'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { DetailPanel } from '@/components/DetailPanel'
import { DeltaBadge } from '@/components/DeltaBadge'
import {
  ALL_PERSONAS,
  ALL_FLOWS,
  PERSONA_LABELS,
  FLOW_LABELS,
  type RunData,
  type PersonaResult,
} from '@/lib/types'
import { frictionClass, computeDelta } from '@/lib/utils'

interface HeatmapMatrixProps {
  runs: RunData[]
}

function buildResultMap(run: RunData): Record<string, PersonaResult> {
  const map: Record<string, PersonaResult> = {}
  for (const result of run.results) {
    map[`${result.persona}__${result.flow}`] = result
  }
  return map
}

export function HeatmapMatrix({ runs }: HeatmapMatrixProps) {
  const [selectedCell, setSelectedCell] = useState<{ persona: string; flow: string } | null>(null)
  const [activeRunIndex, setActiveRunIndex] = useState(0)

  const activeRun = runs[activeRunIndex]
  const previousRun = runs[activeRunIndex + 1]

  const resultMap = activeRun ? buildResultMap(activeRun) : {}
  const previousMap = previousRun ? buildResultMap(previousRun) : {}

  const selectedResult = selectedCell
    ? resultMap[`${selectedCell.persona}__${selectedCell.flow}`]
    : undefined

  return (
    <div className="space-y-4">
      {/* Run selector */}
      {runs.length > 1 && (
        <div className="flex items-center gap-3">
          <label htmlFor="run-selector" className="text-sm font-medium text-gray-700">
            Run:
          </label>
          <select
            id="run-selector"
            value={activeRunIndex}
            onChange={(e) => setActiveRunIndex(Number(e.target.value))}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {runs.map((run, idx) => (
              <option key={run.runId} value={idx}>
                {run.runId} {idx === 0 ? '(latest)' : ''}
              </option>
            ))}
          </select>
        </div>
      )}

      {runs.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No persona runs found. Run the persona sweep to generate data.
        </p>
      ) : (
        /* Heatmap table with horizontal scroll for mobile (P8-SC5) */
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
          <table className="border-collapse min-w-[640px]">
            <thead>
              <tr>
                {/* Empty corner cell */}
                <th className="bg-gray-50 p-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-200 min-w-[140px]">
                  Persona / Flow
                </th>
                {ALL_FLOWS.map((flow) => (
                  <th
                    key={flow}
                    className="bg-gray-50 p-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-200 min-w-[100px]"
                  >
                    {FLOW_LABELS[flow]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ALL_PERSONAS.map((persona) => (
                <tr key={persona} className="group">
                  {/* Persona row header */}
                  <td className="bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 border-b border-gray-200 whitespace-nowrap">
                    {PERSONA_LABELS[persona]}
                  </td>
                  {ALL_FLOWS.map((flow) => {
                    const key = `${persona}__${flow}`
                    const result = resultMap[key]
                    const prevResult = previousMap[key]

                    if (!result) {
                      return (
                        <td
                          key={flow}
                          className="border-b border-gray-200 bg-gray-100 text-center text-xs text-gray-400 p-2"
                        >
                          N/A
                        </td>
                      )
                    }

                    const { delta, direction } = computeDelta(
                      result.friction_score,
                      prevResult?.friction_score
                    )
                    const isSelected =
                      selectedCell?.persona === persona &&
                      selectedCell?.flow === flow

                    return (
                      <td
                        key={flow}
                        onClick={() => setSelectedCell({ persona, flow })}
                        className={[
                          frictionClass(result.friction_score),
                          'relative border-b border-gray-200',
                          'min-w-[100px] h-[80px]',
                          'cursor-pointer hover:opacity-80 transition-opacity',
                          isSelected ? 'ring-2 ring-inset ring-blue-500' : '',
                        ].join(' ')}
                      >
                        {/* Task completion badge — top right */}
                        <span className="absolute top-1.5 right-1.5">
                          {result.task_completed ? (
                            <CheckCircle2 className="size-4" />
                          ) : (
                            <XCircle className="size-4" />
                          )}
                        </span>

                        {/* Friction score — centered */}
                        <div className="flex flex-col items-center justify-center h-full px-2 pt-2">
                          <span className="text-2xl font-bold leading-none">
                            {result.friction_score}
                          </span>
                          {/* Delta badge */}
                          <DeltaBadge delta={delta} direction={direction} />
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Sheet slide-over — stays open when clicking different cells (D-08) */}
      <Sheet
        open={selectedCell !== null}
        onOpenChange={(open: boolean) => {
          if (!open) setSelectedCell(null)
        }}
      >
        <SheetContent
          side="right"
          className="w-full sm:w-[480px] sm:max-w-[480px] overflow-y-auto p-0"
        >
          <SheetHeader className="px-6 py-4 border-b">
            <SheetTitle>
              {selectedCell
                ? `${PERSONA_LABELS[selectedCell.persona]} — ${FLOW_LABELS[selectedCell.flow]}`
                : 'Details'}
            </SheetTitle>
          </SheetHeader>
          <div className="px-6 py-4">
            <DetailPanel result={selectedResult} />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}

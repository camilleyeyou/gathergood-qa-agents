'use client'

import { Badge } from '@/components/ui/badge'
import { PERSONA_LABELS, FLOW_LABELS, type PersonaResult } from '@/lib/types'
import { frictionClass, cn } from '@/lib/utils'

interface DetailPanelProps {
  result: PersonaResult | undefined
}

const SEVERITY_CLASSES: Record<'low' | 'medium' | 'high', string> = {
  low: 'border-l-4 border-l-green-400',
  medium: 'border-l-4 border-l-yellow-400',
  high: 'border-l-4 border-l-red-500',
}

export function DetailPanel({ result }: DetailPanelProps) {
  if (!result) {
    return (
      <p className="text-sm text-gray-500 text-center py-8">No data available</p>
    )
  }

  const stepRatio = (result.steps_taken / result.optimal_steps).toFixed(1)

  return (
    <div className="space-y-6 text-sm">
      {/* Header section */}
      <div className="space-y-2">
        <h2 className="text-base font-semibold text-gray-900">
          {PERSONA_LABELS[result.persona]} — {FLOW_LABELS[result.flow]}
        </h2>
        <div>
          {result.task_completed ? (
            <Badge variant="default" className="bg-green-600 text-white">
              Completed
            </Badge>
          ) : (
            <Badge variant="destructive">
              Failed
            </Badge>
          )}
        </div>
      </div>

      {/* Friction score breakdown */}
      <div className="space-y-2">
        <h3 className="font-medium text-gray-700 uppercase text-xs tracking-wider">
          Friction Score
        </h3>
        <div
          className={cn(
            frictionClass(result.friction_score),
            'inline-flex items-center justify-center rounded-lg w-14 h-14 text-2xl font-bold'
          )}
        >
          {result.friction_score}
        </div>
        <div className="space-y-1 text-gray-600">
          <p>
            <span className="font-medium">Steps:</span>{' '}
            {result.steps_taken} / {result.optimal_steps} optimal ({stepRatio}x)
          </p>
          <p>
            <span className="font-medium">Literacy level:</span>{' '}
            <Badge variant="secondary" className="ml-1">
              {result.literacy_level}
            </Badge>
          </p>
        </div>
      </div>

      {/* Confusion points */}
      <div className="space-y-3">
        <h3 className="font-medium text-gray-700 uppercase text-xs tracking-wider flex items-center gap-2">
          Confusion Points
          <Badge variant="outline">
            {result.confusion_points.length}
          </Badge>
        </h3>
        {result.confusion_points.length === 0 ? (
          <p className="text-gray-400 italic">No confusion points recorded</p>
        ) : (
          <ul className="space-y-3">
            {result.confusion_points.map((cp, idx) => (
              <li
                key={idx}
                className={cn(
                  'rounded-lg border border-gray-200 p-4',
                  SEVERITY_CLASSES[cp.severity]
                )}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <span className="font-medium text-gray-800">
                    Step {cp.step}
                  </span>
                  <SeverityBadge severity={cp.severity} />
                </div>
                <p className="text-gray-600">{cp.description}</p>
                {cp.screenshot_path && cp.screenshot_path.trim() !== '' ? (
                  <div className="mt-2">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={`/screenshots/${cp.screenshot_path.split('/').pop()}`}
                      alt={`Screenshot at step ${cp.step}`}
                      className="rounded border border-gray-200 max-w-full"
                    />
                  </div>
                ) : (
                  <p className="mt-2 text-xs text-gray-400 italic">No screenshot</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Suggestions */}
      <div className="space-y-2">
        <h3 className="font-medium text-gray-700 uppercase text-xs tracking-wider">
          Improvement Suggestions
        </h3>
        {result.suggestions.length === 0 ? (
          <p className="text-gray-400 italic">No suggestions</p>
        ) : (
          <ol className="list-decimal list-inside space-y-1.5 text-gray-600">
            {result.suggestions.map((suggestion, idx) => (
              <li key={idx}>{suggestion}</li>
            ))}
          </ol>
        )}
      </div>

      {/* Token usage footer */}
      <div className="pt-2 border-t border-gray-100">
        <p className="text-xs text-gray-400">
          Tokens used: {result.tokens_used.toLocaleString()}
        </p>
      </div>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: 'low' | 'medium' | 'high' }) {
  if (severity === 'high') {
    return <Badge variant="destructive">High</Badge>
  }
  if (severity === 'medium') {
    return (
      <Badge variant="outline" className="border-yellow-400 text-yellow-700 bg-yellow-50">
        Medium
      </Badge>
    )
  }
  return <Badge variant="secondary">Low</Badge>
}

'use client'

import { ArrowUp, ArrowDown } from 'lucide-react'

interface DeltaBadgeProps {
  delta: number
  direction: 'up' | 'down' | 'same'
}

export function DeltaBadge({ delta, direction }: DeltaBadgeProps) {
  if (direction === 'same' || delta === 0) return null

  if (direction === 'up') {
    // Friction increased — worse — red
    return (
      <span className="inline-flex items-center gap-0.5 text-xs text-red-600 font-medium">
        <ArrowUp className="size-3" />
        {delta.toFixed(1)}
      </span>
    )
  }

  // Friction decreased — better — green
  return (
    <span className="inline-flex items-center gap-0.5 text-xs text-green-600 font-medium">
      <ArrowDown className="size-3" />
      {delta.toFixed(1)}
    </span>
  )
}

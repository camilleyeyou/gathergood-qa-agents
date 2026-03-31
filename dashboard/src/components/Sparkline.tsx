'use client'

import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface SparklineProps {
  data: { run: string; score: number }[]
}

export function Sparkline({ data }: SparklineProps) {
  if (data.length < 2) {
    return <span className="text-xs text-gray-400">—</span>
  }

  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line
          type="monotone"
          dataKey="score"
          dot={false}
          strokeWidth={2}
          stroke="#6366f1"
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length > 0) {
              const point = payload[0]
              return (
                <div className="rounded border border-gray-200 bg-white px-2 py-1 text-xs shadow-sm">
                  <span className="font-medium">{point.value}</span>
                </div>
              )
            }
            return null
          }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

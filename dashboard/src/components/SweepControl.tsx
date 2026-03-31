'use client'

import { useState, useCallback } from 'react'
import { Play, Loader2, CheckCircle2, XCircle, RefreshCw } from 'lucide-react'
import { startSweep, pollSweepStatus } from '@/lib/data'

interface SweepControlProps {
  onSweepComplete: () => void
  apiConnected: boolean
}

export function SweepControl({ onSweepComplete, apiConnected }: SweepControlProps) {
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle')
  const [jobId, setJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [log, setLog] = useState<string | null>(null)

  const runSweep = useCallback(async () => {
    setStatus('running')
    setError(null)
    setLog(null)

    try {
      const { job_id } = await startSweep()
      setJobId(job_id)

      // Poll every 10 seconds
      const poll = setInterval(async () => {
        try {
          const result = await pollSweepStatus(job_id)
          if (result.stdout) setLog(result.stdout)

          if (result.status === 'completed') {
            clearInterval(poll)
            setStatus('completed')
            onSweepComplete()
          } else if (result.status === 'failed') {
            clearInterval(poll)
            setStatus('failed')
            setError(result.error || 'Sweep failed')
          }
        } catch (e) {
          clearInterval(poll)
          setStatus('failed')
          setError(e instanceof Error ? e.message : 'Polling failed')
        }
      }, 10000)
    } catch (e) {
      setStatus('failed')
      setError(e instanceof Error ? e.message : 'Failed to start sweep')
    }
  }, [onSweepComplete])

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Persona Sweep</h2>

        {!apiConnected ? (
          <span className="inline-flex items-center gap-1.5 text-xs text-red-600">
            <XCircle className="size-3.5" />
            API disconnected
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-xs text-green-600">
            <CheckCircle2 className="size-3.5" />
            API connected
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={runSweep}
          disabled={status === 'running' || !apiConnected}
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {status === 'running' ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="size-4" />
              Run Sweep
            </>
          )}
        </button>

        {status === 'completed' && (
          <span className="inline-flex items-center gap-1.5 text-sm text-green-600">
            <CheckCircle2 className="size-4" />
            Sweep complete — results loaded
          </span>
        )}

        {status === 'failed' && (
          <span className="inline-flex items-center gap-1.5 text-sm text-red-600">
            <XCircle className="size-4" />
            {error}
          </span>
        )}

        {jobId && status === 'running' && (
          <span className="text-xs text-gray-400">
            Job: {jobId.slice(0, 8)}...
          </span>
        )}
      </div>

      {log && (
        <details className="text-xs">
          <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
            Show output
          </summary>
          <pre className="mt-2 max-h-48 overflow-auto rounded bg-gray-900 p-3 text-gray-200 whitespace-pre-wrap">
            {log}
          </pre>
        </details>
      )}
    </div>
  )
}

interface RefreshButtonProps {
  onRefresh: () => void
  loading: boolean
}

export function RefreshButton({ onRefresh, loading }: RefreshButtonProps) {
  return (
    <button
      onClick={onRefresh}
      disabled={loading}
      className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
    >
      <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
      Refresh
    </button>
  )
}

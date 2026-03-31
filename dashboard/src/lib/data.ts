import fs from 'node:fs'
import path from 'node:path'
import type { PersonaResult } from './types'

const PERSONA_DIR = path.join(process.cwd(), '..', 'reports', 'persona')

export function readPersonaRuns(): string[] {
  if (!fs.existsSync(PERSONA_DIR)) return []
  return fs.readdirSync(PERSONA_DIR)
    .filter(name => {
      // Skip dotfiles like .gitkeep
      if (name.startsWith('.')) return false
      const fullPath = path.join(PERSONA_DIR, name)
      return fs.statSync(fullPath).isDirectory()
    })
    .sort()
    .reverse()  // Most recent first (D-05) — ISO timestamp IDs sort lexicographically
}

export function loadRunData(runId: string): PersonaResult[] {
  const runDir = path.join(PERSONA_DIR, runId)
  if (!fs.existsSync(runDir)) return []
  return fs.readdirSync(runDir)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      const content = fs.readFileSync(path.join(runDir, f), 'utf-8')
      return JSON.parse(content) as PersonaResult
    })
}

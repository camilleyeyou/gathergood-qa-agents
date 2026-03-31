export interface ConfusionPoint {
  step: number | string
  description: string
  severity: 'low' | 'medium' | 'high'
  screenshot_path?: string
}

export interface PersonaResult {
  persona: string
  flow: string
  literacy_level: number
  task_completed: boolean
  friction_score: number
  steps_taken: number
  optimal_steps: number
  confusion_points: ConfusionPoint[]
  suggestions: string[]
  tokens_used: number
}

export interface RunData {
  runId: string
  results: PersonaResult[]
}

// Canonical ordering — matches scripts/generate_persona_report.py
export const ALL_PERSONAS = ['tech_savvy', 'casual', 'low_literacy', 'non_native', 'impatient'] as const
export const ALL_FLOWS = ['registration', 'browsing', 'checkout'] as const

// Display labels for personas
export const PERSONA_LABELS: Record<string, string> = {
  tech_savvy: 'Tech-Savvy',
  casual: 'Casual',
  low_literacy: 'Low Literacy',
  non_native: 'Non-Native English',
  impatient: 'Impatient',
}

// Display labels for flows
export const FLOW_LABELS: Record<string, string> = {
  registration: 'Registration',
  browsing: 'Browsing',
  checkout: 'Checkout',
}

// Friction color hex values — exact match from templates/persona_report.html.j2
export const FRICTION_COLORS = {
  low:  { bg: '#d4edda', text: '#155724' },  // score 1-3
  mid:  { bg: '#fff3cd', text: '#856404' },  // score 4-6
  high: { bg: '#f8d7da', text: '#721c24' },  // score 7-10
} as const

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function frictionClass(score: number): string {
  if (score <= 3) return 'bg-friction-low text-friction-low-text'
  if (score <= 6) return 'bg-friction-mid text-friction-mid-text'
  return 'bg-friction-high text-friction-high-text'
}

export function computeDelta(
  current: number,
  previous: number | undefined
): { delta: number; direction: 'up' | 'down' | 'same' } {
  if (previous === undefined) return { delta: 0, direction: 'same' }
  const diff = current - previous
  if (diff === 0) return { delta: 0, direction: 'same' }
  return { delta: Math.abs(diff), direction: diff > 0 ? 'up' : 'down' }
}

import type { Topic, GenerateResult, Site, TopicInput } from './types'

const BASE = ''

export async function fetchTopics(): Promise<Topic[]> {
  const r = await fetch(`${BASE}/api/topics`)
  if (!r.ok) throw new Error('Failed to load topics')
  const data = await r.json()
  return data.topics ?? []
}

export async function fetchSites(): Promise<Site[]> {
  const r = await fetch(`${BASE}/api/sites`)
  if (!r.ok) throw new Error('Failed to load sites')
  const data = await r.json()
  return data.sites ?? []
}

export async function addSite(name: string, baseUrl: string, topics: TopicInput[]): Promise<{ id: string; name: string; topics_count: number }> {
  const r = await fetch(`${BASE}/api/sites`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, base_url: baseUrl, topics }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? 'Failed to add site')
  }
  return r.json()
}

export async function generateStudio(concept: string, aspectRatio: string = '16:9'): Promise<GenerateResult> {
  const fd = new FormData()
  fd.append('concept', concept)
  fd.append('aspect_ratio', aspectRatio)
  const r = await fetch(`${BASE}/studio/generate`, { method: 'POST', body: fd })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? r.statusText)
  }
  return r.json()
}

export async function narrate(text: string, voice: string = 'Kore'): Promise<{ audio_base64: string }> {
  const r = await fetch(`${BASE}/studio/narrate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? r.statusText)
  }
  return r.json()
}

export async function exportBlueprint(script: string, title: string, outputName: string): Promise<{ job_id: string }> {
  const fd = new FormData()
  fd.append('script', script)
  fd.append('title', title)
  fd.append('output_name', outputName)
  const r = await fetch(`${BASE}/studio/export-blueprint`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error('Export failed')
  return r.json()
}

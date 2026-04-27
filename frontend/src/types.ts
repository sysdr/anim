export interface TopicVideo {
  name: string
  path: string
  size_mb: number
}

export interface Topic {
  slug: string
  title: string
  description: string
  url: string
  studio_url: string
  video?: TopicVideo
  site_id?: string
  site_name?: string
  base_url?: string
}

export interface TopicInput {
  title: string
  url?: string
  description?: string
}

export interface Site {
  id: string
  name: string
  base_url: string
  topics: Topic[]
}

export interface TimelineStep {
  id?: string
  label: string
  narration?: string
  startTime: number
  duration: number
}

export interface WorkflowSpec {
  title?: string
  summary?: string
  input_type?: string
  acts?: Array<{ id?: string; title?: string; narrative_beat?: string; summary?: string }>
  parts?: Array<{ id?: string; name?: string; scale_hint?: string; responsibility?: string; description?: string }>
  actors?: Array<{ id?: string; name?: string; role?: string; description?: string }>
  entities?: Array<{ id?: string; name?: string; type?: string; description?: string }>
  components?: Array<{ id?: string; name?: string; responsibility?: string; description?: string }>
  communication?: Array<{ from_id?: string; to_id?: string; payload_or_event?: string; description?: string }>
  state_transitions?: Array<{ from_state?: string; to_state?: string; trigger?: string; description?: string }>
  steps?: Array<{ label?: string; part_id?: string; narration?: string; description?: string }>
  [key: string]: unknown
}

export interface GenerateResult {
  svg_source: string
  voiceover_script: string
  timeline: TimelineStep[]
  workflow_spec?: WorkflowSpec
}

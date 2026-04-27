import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { fetchSites, generateStudio, narrate, addSite } from '../api'
import type { Topic, GenerateResult, Site, TopicInput } from '../types'
import '../App.css'

const VOICES = ['Kore', 'Zephyr', 'Puck', 'Charon', 'Fenrir', 'Leda', 'Orus', 'Aoede']

type ThemePreset = {
  bg: string
  surface: string
  viewerBg: string
  panelBg: string
  panelHeaderBg: string
  overlayBg: string
  border: string
  text: string
  muted: string
  accent: string
}
const THEME_PRESETS: Record<string, ThemePreset> = {
  dark: {
    bg: '#0a0a0b',
    surface: 'rgba(0,0,0,0.35)',
    viewerBg: '#000',
    panelBg: '#18181b',
    panelHeaderBg: 'rgba(0,0,0,0.3)',
    overlayBg: 'rgba(0,0,0,0.82)',
    border: 'rgba(255,255,255,0.08)',
    text: '#e2e8f0',
    muted: '#94a3b8',
    accent: '#3b82f6',
  },
  light: {
    bg: '#f1f5f9',
    surface: 'rgba(255,255,255,0.85)',
    viewerBg: '#0f172a',
    panelBg: '#ffffff',
    panelHeaderBg: 'rgba(0,0,0,0.06)',
    overlayBg: 'rgba(15,23,42,0.92)',
    border: 'rgba(0,0,0,0.12)',
    text: '#0f172a',
    muted: '#64748b',
    accent: '#2563eb',
  },
  blueprint: {
    bg: 'linear-gradient(160deg, #0c1222 0%, #1a2744 50%, #0c1222 100%)',
    surface: 'rgba(26,39,68,0.6)',
    viewerBg: '#0f172a',
    panelBg: 'rgba(30,58,95,0.4)',
    panelHeaderBg: 'rgba(0,0,0,0.3)',
    overlayBg: 'rgba(15,23,42,0.9)',
    border: 'rgba(59,130,246,0.2)',
    text: '#e2e8f0',
    muted: '#94a3b8',
    accent: '#3b82f6',
  },
  forest: {
    bg: 'linear-gradient(145deg, #0d1f12 0%, #1a3324 50%, #0d1f12 100%)',
    surface: 'rgba(22,51,36,0.6)',
    viewerBg: '#0f172a',
    panelBg: 'rgba(34,68,51,0.5)',
    panelHeaderBg: 'rgba(0,0,0,0.25)',
    overlayBg: 'rgba(15,31,18,0.9)',
    border: 'rgba(34,197,94,0.2)',
    text: '#dcfce7',
    muted: '#86efac',
    accent: '#22c55e',
  },
  sunset: {
    bg: 'linear-gradient(145deg, #1c0a0a 0%, #431407 50%, #7c2d12 100%)',
    surface: 'rgba(67,20,7,0.6)',
    viewerBg: '#1c1917',
    panelBg: 'rgba(120,53,15,0.4)',
    panelHeaderBg: 'rgba(0,0,0,0.3)',
    overlayBg: 'rgba(44,25,15,0.92)',
    border: 'rgba(251,146,60,0.25)',
    text: '#ffedd5',
    muted: '#fdba74',
    accent: '#f59e0b',
  },
  ocean: {
    bg: 'linear-gradient(160deg, #0a1628 0%, #0e2a47 50%, #164e63 100%)',
    surface: 'rgba(14,42,71,0.6)',
    viewerBg: '#0f172a',
    panelBg: 'rgba(22,78,99,0.4)',
    panelHeaderBg: 'rgba(0,0,0,0.25)',
    overlayBg: 'rgba(12,74,110,0.9)',
    border: 'rgba(6,182,212,0.25)',
    text: '#e0f2fe',
    muted: '#7dd3fc',
    accent: '#06b6d4',
  },
  violet: {
    bg: 'linear-gradient(150deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%)',
    surface: 'rgba(49,46,129,0.5)',
    viewerBg: '#1e1b4b',
    panelBg: 'rgba(67,56,202,0.35)',
    panelHeaderBg: 'rgba(0,0,0,0.3)',
    overlayBg: 'rgba(49,46,129,0.92)',
    border: 'rgba(139,92,246,0.3)',
    text: '#ede9fe',
    muted: '#c4b5fd',
    accent: '#8b5cf6',
  },
  slate: {
    bg: '#0f172a',
    surface: 'rgba(30,41,59,0.8)',
    viewerBg: '#0f172a',
    panelBg: '#1e293b',
    panelHeaderBg: 'rgba(0,0,0,0.25)',
    overlayBg: 'rgba(15,23,42,0.92)',
    border: 'rgba(248,250,252,0.1)',
    text: '#f1f5f9',
    muted: '#94a3b8',
    accent: '#f59e0b',
  },
  neon: {
    bg: 'linear-gradient(160deg, #0a0a1a 0%, #0f1029 50%, #0a0a1a 100%)',
    surface: 'rgba(15,16,41,0.7)',
    viewerBg: '#0a0a1a',
    panelBg: 'rgba(20,20,50,0.6)',
    panelHeaderBg: 'rgba(0,0,0,0.4)',
    overlayBg: 'rgba(10,10,26,0.94)',
    border: 'rgba(99,102,241,0.2)',
    text: '#e2e8f0',
    muted: '#94a3b8',
    accent: '#6366f1',
  },
  aurora: {
    bg: 'linear-gradient(160deg, #0a1628 0%, #0d2137 30%, #0a2e3d 60%, #0d1f2d 100%)',
    surface: 'rgba(13,33,55,0.6)',
    viewerBg: '#0a1628',
    panelBg: 'rgba(10,46,61,0.4)',
    panelHeaderBg: 'rgba(0,0,0,0.3)',
    overlayBg: 'rgba(10,22,40,0.94)',
    border: 'rgba(6,214,160,0.2)',
    text: '#e0f7fa',
    muted: '#80cbc4',
    accent: '#06d6a0',
  },
  midnight: {
    bg: 'linear-gradient(145deg, #0c0c1d 0%, #141432 50%, #0c0c1d 100%)',
    surface: 'rgba(20,20,50,0.65)',
    viewerBg: '#0c0c1d',
    panelBg: 'rgba(25,25,60,0.5)',
    panelHeaderBg: 'rgba(0,0,0,0.35)',
    overlayBg: 'rgba(12,12,29,0.95)',
    border: 'rgba(139,92,246,0.2)',
    text: '#ede9fe',
    muted: '#a5b4fc',
    accent: '#a78bfa',
  },
  ember: {
    bg: 'linear-gradient(160deg, #1a0a0a 0%, #2d1215 40%, #1a0f0a 100%)',
    surface: 'rgba(45,18,21,0.6)',
    viewerBg: '#1a0a0a',
    panelBg: 'rgba(60,25,20,0.5)',
    panelHeaderBg: 'rgba(0,0,0,0.35)',
    overlayBg: 'rgba(26,10,10,0.95)',
    border: 'rgba(239,68,68,0.2)',
    text: '#fef2f2',
    muted: '#fca5a5',
    accent: '#ef4444',
  },
  glass: {
    bg: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
    surface: 'rgba(255,255,255,0.04)',
    viewerBg: '#0f172a',
    panelBg: 'rgba(255,255,255,0.03)',
    panelHeaderBg: 'rgba(255,255,255,0.05)',
    overlayBg: 'rgba(15,23,42,0.9)',
    border: 'rgba(255,255,255,0.08)',
    text: '#e2e8f0',
    muted: '#94a3b8',
    accent: '#38bdf8',
  },
  /* Google Analytics–style diagram (light, pure white default) — for SVG workflow only */
  google: {
    bg: '#ffffff',
    surface: '#ffffff',
    viewerBg: '#ffffff',
    panelBg: '#ffffff',
    panelHeaderBg: '#f8f9fa',
    overlayBg: 'rgba(32, 33, 36, 0.9)',
    border: 'rgba(0, 0, 0, 0.08)',
    text: '#202124',
    muted: '#5f6368',
    accent: '#1a73e8',
  },
}
const THEMES = Object.keys(THEME_PRESETS).map((value) => ({
  value,
  label: value.charAt(0).toUpperCase() + value.slice(1),
}))

const FONTS = [
  { value: 'Roboto', label: 'Roboto', font: '"Roboto", system-ui, sans-serif' },
  { value: 'Inter', label: 'Inter', font: 'Inter, system-ui, sans-serif' },
  { value: 'Space Grotesk', label: 'Space Grotesk', font: '"Space Grotesk", system-ui, sans-serif' },
  { value: 'Manrope', label: 'Manrope', font: '"Manrope", system-ui, sans-serif' },
  { value: 'Outfit', label: 'Outfit', font: '"Outfit", system-ui, sans-serif' },
  { value: 'Plus Jakarta Sans', label: 'Plus Jakarta Sans', font: '"Plus Jakarta Sans", system-ui, sans-serif' },
  { value: 'Sora', label: 'Sora', font: '"Sora", system-ui, sans-serif' },
  { value: 'DM Sans', label: 'DM Sans', font: '"DM Sans", system-ui, sans-serif' },
  { value: 'system', label: 'System', font: 'system-ui, -apple-system, sans-serif' },
  { value: 'Playfair Display', label: 'Playfair Display', font: '"Playfair Display", Georgia, serif' },
  { value: 'Merriweather', label: 'Merriweather', font: '"Merriweather", Georgia, serif' },
  { value: 'Lora', label: 'Lora', font: '"Lora", Georgia, serif' },
  { value: 'Source Sans', label: 'Source Sans', font: '"Source Sans 3", sans-serif' },
  { value: 'JetBrains Mono', label: 'JetBrains Mono', font: '"JetBrains Mono", monospace' },
  { value: 'IBM Plex Sans', label: 'IBM Plex Sans', font: '"IBM Plex Sans", sans-serif' },
  { value: 'IBM Plex Mono', label: 'IBM Plex Mono', font: '"IBM Plex Mono", monospace' },
]
const FONT_SIZES = [
  { value: 12, label: '12px' },
  { value: 13, label: '13px' },
  { value: 14, label: '14px' },
  { value: 15, label: '15px' },
  { value: 16, label: '16px' },
  { value: 18, label: '18px' },
  { value: 20, label: '20px' },
]

const ACCENT_COLORS = [
  { value: 'indigo', label: 'Indigo', hex: '#6366f1' },
  { value: 'blue', label: 'Blue', hex: '#3b82f6' },
  { value: 'cyan', label: 'Cyan', hex: '#06b6d4' },
  { value: 'teal', label: 'Teal', hex: '#14b8a6' },
  { value: 'emerald', label: 'Emerald', hex: '#06d6a0' },
  { value: 'violet', label: 'Violet', hex: '#8b5cf6' },
  { value: 'fuchsia', label: 'Fuchsia', hex: '#d946ef' },
  { value: 'green', label: 'Green', hex: '#22c55e' },
  { value: 'amber', label: 'Amber', hex: '#f59e0b' },
  { value: 'rose', label: 'Rose', hex: '#f43f5e' },
  { value: 'sky', label: 'Sky', hex: '#38bdf8' },
  { value: 'gold', label: 'Gold', hex: '#d4af37' },
]

/** Parse SVG source for interactive node group IDs (node-step-1, etc.) and return with optional labels from timeline. */
function getSvgNodeIds(svgSource: string | undefined, timeline: GenerateResult['timeline']): Array<{ id: string; label: string }> {
  if (!svgSource?.trim()) return []
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(svgSource, 'image/svg+xml')
    const groups = doc.querySelectorAll('g[id^="node-"]')
    const list: Array<{ id: string; label: string }> = []
    const stepIdToLabel = new Map<string, string>()
    if (timeline?.length) {
      timeline.forEach((step, i) => {
        const id = (step as { id?: string }).id ?? `step-${i + 1}`
        stepIdToLabel.set(id, step.label ?? id)
      })
    }
    groups.forEach((g) => {
      const id = g.getAttribute('id') ?? ''
      if (!id) return
      const stepId = id.startsWith('node-') ? id.slice(5) : id
      const label = stepIdToLabel.get(stepId) ?? stepId
      list.push({ id, label })
    })
    return list
  } catch {
    return []
  }
}

/** SVG animation CSS variables (used by generated SVG). Keys match backend/Gemini output. */
function getSvgAppearanceVars(opts: {
  theme: string
  accentColor: string
  customAccentHex: string | null
  fontFamily: string
  fontSize: number
  gradientStartHex: string
  useCustomGradient: boolean
  animationBgMode: 'theme' | 'solid' | 'gradient'
  animationBgSolid: string
  animationBgGradStart: string
  animationBgGradEnd: string
}): Record<string, string> {
  const preset = THEME_PRESETS[opts.theme] ?? THEME_PRESETS.dark
  const accentHex = opts.customAccentHex ?? (ACCENT_COLORS.find((a) => a.value === opts.accentColor)?.hex ?? preset.accent)
  const font = FONTS.find((f) => f.value === opts.fontFamily)?.font ?? FONTS[0].font
  const fontSizePx = `${opts.fontSize || 14}px`

  // Animation background: explicit solid/gradient or theme
  let bgCanvas: string
  if (opts.animationBgMode === 'solid') {
    bgCanvas = opts.animationBgSolid
  } else if (opts.animationBgMode === 'gradient') {
    bgCanvas = opts.animationBgGradStart
  } else {
    bgCanvas = opts.useCustomGradient ? opts.gradientStartHex : (preset.bg.startsWith('linear-gradient') ? '#0a0a0b' : preset.bg)
  }

  return {
    '--bg-canvas': bgCanvas,
    '--text-primary': preset.text,
    '--accent-primary': accentHex,
    '--border-dim': preset.border,
    '--node-bg': preset.panelBg,
    '--panel-bg': preset.panelBg,
    '--svg-font': font,
    '--svg-font-size': fontSizePx,
  }
}

const EXAMPLE_CHIPS: { label: string; concept: string }[] = [
  { label: 'OAuth 2.0', concept: 'How OAuth 2.0 authentication works' },
  { label: 'Kubernetes scheduling', concept: 'Kubernetes pod scheduling' },
  { label: 'React Lifecycle', concept: 'React component lifecycle' },
  { label: 'Message Queues', concept: 'Message Queues Explained with Café Analogies' },
  { label: 'Load Balancing', concept: 'Load Balancing 101: How Traffic Gets Distributed' },
  { label: 'Chat System', concept: 'Designing a Chat System: History, Read Receipts, Presence' },
]

/** Per-object overrides for animation elements (color, size, position, shape). */
export type ObjectOverride = {
  fill?: string
  stroke?: string
  opacity?: number
  scaleX?: number
  scaleY?: number
  x?: number
  y?: number
  borderRadius?: number
}

export default function Studio() {
  const [sites, setSites] = useState<Site[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [selectedTopicKey, setSelectedTopicKey] = useState<string>('')
  const [showAddSite, setShowAddSite] = useState(false)
  const [addSiteName, setAddSiteName] = useState('')
  const [addSiteBaseUrl, setAddSiteBaseUrl] = useState('')
  const [addSiteTopicsText, setAddSiteTopicsText] = useState('')
  const [addSiteSubmitting, setAddSiteSubmitting] = useState(false)
  const [addSiteError, setAddSiteError] = useState<string | null>(null)
  const [detailInput, setDetailInput] = useState('')
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16' | '1:1'>('16:9')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<GenerateResult | null>(null)
  const [voice, setVoice] = useState('Kore')
  const [theme, setTheme] = useState('google')
  const [accentColor, setAccentColor] = useState('indigo')
  const [customAccentHex, setCustomAccentHex] = useState<string | null>(null)
  const [fontFamily, setFontFamily] = useState('Roboto')
  const [fontSize, setFontSize] = useState(14)
  const [useCustomGradient, setUseCustomGradient] = useState(false)
  const [gradientStartHex, setGradientStartHex] = useState('#0f172a')
  const [gradientEndHex, setGradientEndHex] = useState('#1e3a5f')
  const [animationBgMode, setAnimationBgMode] = useState<'theme' | 'solid' | 'gradient'>('theme')
  const [animationBgSolid, setAnimationBgSolid] = useState('#0a0a0b')
  const [animationBgGradStart, setAnimationBgGradStart] = useState('#0f172a')
  const [animationBgGradEnd, setAnimationBgGradEnd] = useState('#1e3a5f')
  const [itemScales, setItemScales] = useState<Record<string, number>>({})
  const [showItemSizes, setShowItemSizes] = useState(false)
  const [narrating, setNarrating] = useState(false)
  const [narrationAudio, setNarrationAudio] = useState<HTMLAudioElement | null>(null)
  const [cachedNarrationDataUrl, setCachedNarrationDataUrl] = useState<string | null>(null)
  const [generatingAudio, setGeneratingAudio] = useState(false)
  const [downloadingAudio, setDownloadingAudio] = useState(false)
  const [panelOrder, setPanelOrder] = useState<('animation' | 'steps')[]>(['animation', 'steps'])
  const [panelSizes, setPanelSizes] = useState({ animation: 80, steps: 20 })
  const [isPlayingSync, setIsPlayingSync] = useState(false)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [selectedObjectIds, setSelectedObjectIds] = useState<string[]>([])
  const [objectOverrides, setObjectOverrides] = useState<Record<string, ObjectOverride>>({})
  const [selectionBox, setSelectionBox] = useState<{ left: number; top: number; width: number; height: number } | null>(null)
  const layoutRef = useRef<HTMLDivElement>(null)
  const panelResizeRef = useRef<{ index: number; startX: number; startSizes: [number, number] } | null>(null)
  const dragRef = useRef<{ id: 'animation' | 'steps'; index: number } | null>(null)
  const viewerContainerRef = useRef<HTMLDivElement>(null)
  const syncRafRef = useRef<number | null>(null)
  const syncAudioRef = useRef<HTMLAudioElement | null>(null)
  const objectDragRef = useRef<{ id: string; startX: number; startY: number; startOverrideX: number; startOverrideY: number } | null>(null)
  const resizeDragRef = useRef<{ id: string; corner: string; startX: number; startY: number; startScaleX: number; startScaleY: number } | null>(null)

  const applyAppearanceToSvg = useCallback(() => {
    const container = viewerContainerRef.current
    if (!container) return
    const root = container.querySelector('svg') ?? container.querySelector('[id="root"]')
    if (!root || !('style' in root)) return
    const svgEl = root as SVGSVGElement

    // Force SVG to fill the viewer container so it is always visible
    svgEl.style.width = '100%'
    svgEl.style.height = '100%'
    svgEl.style.maxWidth = '100%'
    svgEl.style.maxHeight = '100%'
    svgEl.style.display = 'block'
    svgEl.style.visibility = 'visible'
    svgEl.setAttribute('preserveAspectRatio', 'xMidYMid meet')

    const vars = getSvgAppearanceVars({
      theme,
      accentColor,
      customAccentHex,
      fontFamily,
      fontSize,
      gradientStartHex,
      useCustomGradient,
      animationBgMode,
      animationBgSolid,
      animationBgGradStart,
      animationBgGradEnd,
    })
    Object.entries(vars).forEach(([key, value]) => {
      svgEl.style.setProperty(key, value)
    })

    // Animation background
    const bgRect = Array.from(svgEl.querySelectorAll('rect')).find(
      (r) => r.getAttribute('width') === '100%' && r.getAttribute('height') === '100%'
    ) as SVGRectElement | undefined
    if (bgRect) {
      if (animationBgMode === 'gradient') {
        let defs = svgEl.getElementById('synapseflow-bg-defs') as SVGDefsElement | null
        if (!defs) {
          defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs')
          defs.id = 'synapseflow-bg-defs'
          svgEl.insertBefore(defs, svgEl.firstChild)
        }
        let grad = svgEl.getElementById('synapseflow-bg-gradient') as SVGLinearGradientElement | null
        if (!grad) {
          grad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient')
          grad.id = 'synapseflow-bg-gradient'
          grad.setAttribute('x1', '0%')
          grad.setAttribute('y1', '0%')
          grad.setAttribute('x2', '100%')
          grad.setAttribute('y2', '100%')
          defs.appendChild(grad)
        }
        grad.innerHTML = ''
        const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop')
        stop1.setAttribute('offset', '0%')
        stop1.setAttribute('stop-color', animationBgGradStart)
        const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop')
        stop2.setAttribute('offset', '100%')
        stop2.setAttribute('stop-color', animationBgGradEnd)
        grad.appendChild(stop1)
        grad.appendChild(stop2)
        bgRect.setAttribute('fill', 'url(#synapseflow-bg-gradient)')
      } else if (animationBgMode === 'solid') {
        bgRect.setAttribute('fill', animationBgSolid)
      } else {
        bgRect.setAttribute('fill', 'var(--bg-canvas)')
      }
    }

    // Font/style injection
    let styleEl = svgEl.getElementById('synapseflow-appearance-style') as SVGStyleElement | null
    if (!styleEl) {
      styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style') as SVGStyleElement
      styleEl.id = 'synapseflow-appearance-style'
      svgEl.insertBefore(styleEl, svgEl.firstChild)
    }
    const fontImportUrl = 'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap'
    styleEl.textContent = `
      @import url('${fontImportUrl}');
      svg text { font-family: var(--svg-font, 'Roboto', system-ui, sans-serif) !important; }
      svg text[font-size] { font-size: inherit; }
      .interactive-node { transition: opacity 0.3s ease; }
    `

    // Apply per-node: itemScales (legacy) + objectOverrides (fill, position, scale)
    const nodeList = getSvgNodeIds(result?.svg_source, result?.timeline ?? [])
    nodeList.forEach(({ id }) => {
      const el = svgEl.querySelector(`[id="${id}"]`) as SVGGElement | null
      if (!el) return
      const scale = itemScales[id] ?? 1
      const override = objectOverrides[id] ?? {}
      const sx = override.scaleX ?? scale
      const sy = override.scaleY ?? scale
      const tx = override.x ?? 0
      const ty = override.y ?? 0
      el.style.transformOrigin = 'center'
      const parts: string[] = []
      if (tx !== 0 || ty !== 0) parts.push(`translate(${tx}px, ${ty}px)`)
      if (sx !== 1 || sy !== 1) parts.push(`scale(${sx}, ${sy})`)
      el.style.transform = parts.length ? parts.join(' ') : ''
      if (override.fill != null) el.setAttribute('fill', override.fill)
      if (override.stroke != null) el.setAttribute('stroke', override.stroke)
      if (override.opacity != null) el.setAttribute('opacity', String(override.opacity))
      if (selectedObjectIds.includes(id)) el.classList.add('selected')
      else el.classList.remove('selected')
    })
  }, [theme, accentColor, customAccentHex, fontFamily, fontSize, gradientStartHex, useCustomGradient, animationBgMode, animationBgSolid, animationBgGradStart, animationBgGradEnd, itemScales, objectOverrides, selectedObjectIds, result?.svg_source, result?.timeline])

  useEffect(() => {
    if (!result?.svg_source) return
    const t = requestAnimationFrame(() => {
      applyAppearanceToSvg()
    })
    return () => cancelAnimationFrame(t)
  }, [result?.svg_source, applyAppearanceToSvg])

  // Update selection box for resize handles when selection or overrides change
  useEffect(() => {
    if (selectedObjectIds.length !== 1 || !viewerContainerRef.current) {
      setSelectionBox(null)
      return
    }
    const id = selectedObjectIds[0]
    const el = viewerContainerRef.current.querySelector(`[id="${id}"]`) as SVGGElement | null
    const container = viewerContainerRef.current
    if (!el) {
      setSelectionBox(null)
      return
    }
    const update = () => {
      const elRect = el.getBoundingClientRect()
      const contRect = container.getBoundingClientRect()
      setSelectionBox({
        left: elRect.left - contRect.left,
        top: elRect.top - contRect.top,
        width: elRect.width,
        height: elRect.height,
      })
    }
    update()
    const ro = new ResizeObserver(update)
    ro.observe(container)
    return () => ro.disconnect()
  }, [selectedObjectIds, objectOverrides])

  useEffect(() => {
    fetchSites()
      .then((sitesList) => {
        setSites(sitesList)
        const flat = sitesList.flatMap((s) =>
          s.topics.map((t) => ({ ...t, site_id: s.id, site_name: s.name }))
        )
        setTopics(flat)
      })
      .catch(() => setSites([]))
  }, [])

  useEffect(() => {
    setCachedNarrationDataUrl(null)
  }, [voice])

  useEffect(() => {
    setCachedNarrationDataUrl(null)
  }, [result?.voiceover_script])

  useEffect(() => {
    setCurrentStepIndex(0)
    setItemScales({})
    setSelectedObjectIds([])
    setObjectOverrides({})
    if (isPlayingSync) {
      syncAudioRef.current?.pause()
      if (syncRafRef.current != null) cancelAnimationFrame(syncRafRef.current)
      syncRafRef.current = null
      syncAudioRef.current = null
      setIsPlayingSync(false)
    }
  }, [result?.svg_source])

  const selectedTopic = topics.find(
    (t) => `${t.site_id ?? ''}:${t.slug}` === selectedTopicKey
  )

  const buildConcept = useCallback(() => {
    const parts: string[] = []
    if (selectedTopic) parts.push(selectedTopic.title)
    if (detailInput.trim()) parts.push(detailInput.trim())
    return parts.join('\n\n') || detailInput.trim()
  }, [selectedTopic, detailInput])

  const handleGenerate = async () => {
    const concept = buildConcept()
    if (!concept) {
      setError('Enter a topic or detailed description, or select a topic from the list.')
      return
    }
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await generateStudio(concept, aspectRatio)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  /** Returns cached audio data URL, or generates and caches it. Shows progress while generating. */
  const ensureNarrationAudio = useCallback(async (): Promise<string | null> => {
    if (!result?.voiceover_script) return null
    if (cachedNarrationDataUrl) return cachedNarrationDataUrl
    setGeneratingAudio(true)
    setError(null)
    try {
      const { audio_base64 } = await narrate(result.voiceover_script, voice)
      const dataUrl = `data:audio/wav;base64,${audio_base64}`
      setCachedNarrationDataUrl(dataUrl)
      return dataUrl
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Audio generation failed')
      return null
    } finally {
      setGeneratingAudio(false)
    }
  }, [result?.voiceover_script, voice, cachedNarrationDataUrl])

  const getStepIndexFromTime = useCallback((time: number): number => {
    if (!result?.timeline?.length) return 0
    for (let i = 0; i < result.timeline.length; i++) {
      const step = result.timeline[i]
      const start = Number(step.startTime) || 0
      const duration = Number(step.duration) || 3
      if (time >= start && time < start + duration) return i
    }
    if (time >= 0 && result.timeline.length) return result.timeline.length - 1
    return 0
  }, [result?.timeline])

  const setSvgTime = useCallback((t: number) => {
    try {
      const svgEl = viewerContainerRef.current?.querySelector('svg') as (SVGSVGElement & { setCurrentTime?: (x: number) => void }) | null
      if (svgEl?.setCurrentTime) svgEl.setCurrentTime(t)
      else viewerContainerRef.current?.querySelectorAll?.('animate, animateTransform').forEach((el) => {
        const a = el as SVGAnimateElement & { beginElement?: () => void }
        if (a.beginElement) a.beginElement()
      })
    } catch (_) {}
  }, [])

  const resetSvgToStart = useCallback(() => {
    try {
      const svgEl = viewerContainerRef.current?.querySelector('svg') as (SVGSVGElement & { pauseAnimations?: () => void; setCurrentTime?: (x: number) => void }) | null
      if (svgEl) {
        if (svgEl.pauseAnimations) svgEl.pauseAnimations()
        if (svgEl.setCurrentTime) svgEl.setCurrentTime(0)
      }
    } catch (_) {}
  }, [])

  const handleNarrate = useCallback(async () => {
    if (!result?.voiceover_script) {
      setError('No script to narrate. Generate first.')
      return
    }
    if (narrating && narrationAudio) {
      narrationAudio.pause()
      narrationAudio.currentTime = 0
      setNarrationAudio(null)
      setNarrating(false)
      return
    }
    if (isPlayingSync) {
      syncAudioRef.current?.pause()
      if (syncRafRef.current != null) cancelAnimationFrame(syncRafRef.current)
      syncRafRef.current = null
      syncAudioRef.current = null
      setIsPlayingSync(false)
    }
    const dataUrl = await ensureNarrationAudio()
    if (!dataUrl) return
    const audio = new Audio(dataUrl)
    audio.currentTime = 0
    audio.onended = () => {
      setNarrating(false)
      setNarrationAudio(null)
    }
    setNarrationAudio(audio)
    setNarrating(true)
    audio.play().catch((e) => {
      setError(e?.message || 'Playback failed')
      setNarrating(false)
      setNarrationAudio(null)
    })
  }, [result?.voiceover_script, narrating, narrationAudio, isPlayingSync, ensureNarrationAudio])

  const handlePlaySync = useCallback(async () => {
    if (!result?.voiceover_script) return
    if (isPlayingSync) {
      syncAudioRef.current?.pause()
      if (syncRafRef.current != null) cancelAnimationFrame(syncRafRef.current)
      syncRafRef.current = null
      syncAudioRef.current = null
      setIsPlayingSync(false)
      return
    }
    if (narrating && narrationAudio) {
      narrationAudio.pause()
      narrationAudio.currentTime = 0
      setNarrationAudio(null)
      setNarrating(false)
    }
    const dataUrl = await ensureNarrationAudio()
    if (!dataUrl) return
    setError(null)
    setCurrentStepIndex(0)
    resetSvgToStart()
    setSvgTime(0)
    const audio = new Audio(dataUrl)
    syncAudioRef.current = audio
    audio.currentTime = 0
    const duration = audio.duration && isFinite(audio.duration) ? audio.duration : (result.voiceover_script.split(/\s+/).length / 2.2)
    audio.onended = () => {
      syncAudioRef.current = null
      if (syncRafRef.current != null) cancelAnimationFrame(syncRafRef.current)
      syncRafRef.current = null
      setIsPlayingSync(false)
    }
    const tick = () => {
      if (!syncAudioRef.current) return
      const t = syncAudioRef.current.currentTime
      setCurrentStepIndex(getStepIndexFromTime(t))
      setSvgTime(t)
      if (t < duration) syncRafRef.current = requestAnimationFrame(tick)
    }
    syncRafRef.current = requestAnimationFrame(tick)
    setIsPlayingSync(true)
    audio.play().catch((e) => {
      setError(e?.message || 'Playback failed')
      setIsPlayingSync(false)
    })
  }, [result?.voiceover_script, result?.timeline, isPlayingSync, narrating, narrationAudio, ensureNarrationAudio, getStepIndexFromTime, setSvgTime, resetSvgToStart])

  const handleDownloadAudio = useCallback(async () => {
    if (!result?.voiceover_script) {
      setError('No script to download. Generate first.')
      return
    }
    setError(null)
    setDownloadingAudio(true)
    try {
      const dataUrl = await ensureNarrationAudio()
      if (!dataUrl) return
      const a = document.createElement('a')
      a.href = dataUrl
      a.download = 'narration.wav'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download failed')
    } finally {
      setDownloadingAudio(false)
    }
  }, [result?.voiceover_script, ensureNarrationAudio])

  /** Find node id from click target (closest g[id^="node-"]). */
  const getNodeIdFromTarget = useCallback((target: EventTarget | null): string | null => {
    let el = target as HTMLElement | null
    while (el && el !== viewerContainerRef.current) {
      if (el.id && el.id.startsWith('node-')) return el.id
      el = el.parentElement
    }
    return null
  }, [])

  const handleViewerClick = useCallback((e: React.MouseEvent) => {
    const id = getNodeIdFromTarget(e.target)
    if (!id) {
      setSelectedObjectIds([])
      return
    }
    if (e.shiftKey) {
      setSelectedObjectIds((prev) =>
        prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
      )
    } else {
      setSelectedObjectIds([id])
    }
  }, [getNodeIdFromTarget])

  /** Convert screen delta to SVG coordinate delta using viewer and SVG dimensions. */
  const screenDeltaToSvg = useCallback((deltaX: number, deltaY: number): { x: number; y: number } => {
    const container = viewerContainerRef.current
    if (!container) return { x: 0, y: 0 }
    const svgEl = container.querySelector('svg')
    if (!svgEl) return { x: 0, y: 0 }
    const cr = container.getBoundingClientRect()
    const vb = svgEl.viewBox?.baseVal
    const sw = vb?.width ?? svgEl.width?.baseVal?.value ?? cr.width
    const sh = vb?.height ?? svgEl.height?.baseVal?.value ?? cr.height
    const scaleX = sw / cr.width
    const scaleY = sh / cr.height
    return { x: deltaX * scaleX, y: deltaY * scaleY }
  }, [])

  const handleViewerMouseDown = useCallback((e: React.MouseEvent) => {
    const id = getNodeIdFromTarget(e.target)
    if (!id || !selectedObjectIds.includes(id)) return
    e.preventDefault()
    objectDragRef.current = {
      id,
      startX: e.clientX,
      startY: e.clientY,
      startOverrideX: objectOverrides[id]?.x ?? 0,
      startOverrideY: objectOverrides[id]?.y ?? 0,
    }
    document.body.style.cursor = 'grabbing'
    document.body.style.userSelect = 'none'
  }, [getNodeIdFromTarget, selectedObjectIds, objectOverrides])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (objectDragRef.current) {
        const { id, startX, startY, startOverrideX, startOverrideY } = objectDragRef.current
        const d = screenDeltaToSvg(e.clientX - startX, e.clientY - startY)
        setObjectOverrides((prev) => ({
          ...prev,
          [id]: { ...prev[id], x: startOverrideX + d.x, y: startOverrideY + d.y },
        }))
      }
      if (resizeDragRef.current) {
        const { id, startX, startY, startScaleX, startScaleY } = resizeDragRef.current
        const totalDelta = (e.clientX - startX + (e.clientY - startY)) * 0.008
        const factor = 1 + totalDelta
        setObjectOverrides((prev) => ({
          ...prev,
          [id]: {
            ...prev[id],
            scaleX: Math.max(0.2, Math.min(3, startScaleX * factor)),
            scaleY: Math.max(0.2, Math.min(3, startScaleY * factor)),
          },
        }))
      }
    }
    const onUp = () => {
      objectDragRef.current = null
      resizeDragRef.current = null
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
  }, [screenDeltaToSvg])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedObjectIds([])
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])

  const handlePanelResizeMouseDown = useCallback((betweenIndex: number, e: React.MouseEvent) => {
    e.preventDefault()
    const id1 = panelOrder[betweenIndex]
    const id2 = panelOrder[betweenIndex + 1]
    if (!id1 || !id2) return
    const total = panelSizes[id1] + panelSizes[id2]
    panelResizeRef.current = {
      index: betweenIndex,
      startX: e.clientX,
      startSizes: [panelSizes[id1], panelSizes[id2]],
    }
    const onMove = (e: MouseEvent) => {
      if (!panelResizeRef.current || !layoutRef.current) return
      const rect = layoutRef.current.getBoundingClientRect()
      const deltaPct = ((e.clientX - panelResizeRef.current.startX) / rect.width) * 100
      const [s1] = panelResizeRef.current.startSizes
      const newS1 = Math.min(total - 15, Math.max(15, s1 + deltaPct))
      const newS2 = total - newS1
      setPanelSizes((prev) => ({
        ...prev,
        [id1]: newS1,
        [id2]: newS2,
      }))
    }
    const onUp = () => {
      panelResizeRef.current = null
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.body.style.cursor = 'ew-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [panelOrder, panelSizes])

  const handlePanelDragStart = useCallback((id: 'animation' | 'steps', index: number) => {
    dragRef.current = { id, index }
  }, [])

  const handlePanelDragOver = useCallback((e: React.DragEvent, _targetIndex: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const handlePanelDrop = useCallback((e: React.DragEvent, targetIndex: number) => {
    e.preventDefault()
    const drag = dragRef.current
    if (!drag) return
    const fromIndex = panelOrder.indexOf(drag.id)
    if (fromIndex === -1 || fromIndex === targetIndex) return
    const next = [...panelOrder]
    const [removed] = next.splice(fromIndex, 1)
    next.splice(targetIndex, 0, removed)
    setPanelOrder(next)
    dragRef.current = null
  }, [panelOrder])

  const handlePanelDragEnd = useCallback(() => {
    dragRef.current = null
  }, [])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-left">
          <Link to="/" className="logo">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
            SynapseFlow
          </Link>
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--ga-main-text-secondary)' }}>Studio</span>
        </div>
        <div className="app-header-center">
          <input
            type="text"
            className="search-like"
            placeholder="Try searching 'Topics' or 'OAuth'"
            readOnly
            aria-label="Search"
          />
        </div>
        <div className="app-header-right">
          <nav className="nav-tabs">
            <Link to="/" className="nav-tab active">Studio</Link>
            <a href="/dashboard" className="nav-tab">Dashboard</a>
          </nav>
          <a href="https://ai.google.dev" target="_blank" rel="noopener noreferrer" className="badge">Powered by Gemini</a>
        </div>
      </header>

      <div className="app-body">
        <aside className="app-sidebar" aria-label="Main navigation">
          <nav className="app-sidebar-nav">
            <Link to="/" className="app-sidebar-item active" aria-current="page">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
              </svg>
              Reports snapshot
            </Link>
            <a href="/dashboard" className="app-sidebar-item">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Dashboard
            </a>
          </nav>
          <div className="app-sidebar-footer">
            <a href="/dashboard" className="app-sidebar-item" style={{ margin: 0 }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Settings
            </a>
          </div>
        </aside>

        <main className="app-main">
          <div className="main-content">
        <div className="studio-hero">
          <h1>Create your reports snapshot</h1>
          <p>Choose a topic or describe a process. Technology Architect builds the workflow → SVG animation + voiceover.</p>
        </div>

        <section className="briefing-section" aria-label="Create animation">
          <div className="input-card">
          <div className="topic-row">
            <div className="topic-select-wrap">
              <label htmlFor="topic-select">Topic for animation (optional)</label>
              <select
                id="topic-select"
                value={selectedTopicKey}
                onChange={(e) => setSelectedTopicKey(e.target.value)}
              >
                <option value="">— Choose a topic —</option>
                {sites.map((site) => (
                  <optgroup key={site.id} label={site.name}>
                    {site.topics.map((t) => (
                      <option key={`${site.id}:${t.slug}`} value={`${site.id}:${t.slug}`}>
                        {t.title}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <p className="source-hint">
                Topics from your added sites.{' '}
                <button type="button" className="link-button" onClick={() => setShowAddSite((s) => !s)}>
                  {showAddSite ? 'Cancel' : 'Add a site'}
                </button>
              </p>
            </div>
          </div>

          {showAddSite && (
            <div className="add-site-card">
              <h3>Add a site</h3>
              <p className="add-site-hint">Add a source (e.g. blog, newsletter) and list its topics. Each topic can be used to generate an animation.</p>
              <label htmlFor="add-site-name">Site name</label>
              <input
                id="add-site-name"
                type="text"
                placeholder="e.g. My Tech Blog"
                value={addSiteName}
                onChange={(e) => setAddSiteName(e.target.value)}
              />
              <label htmlFor="add-site-url">Base URL (optional)</label>
              <input
                id="add-site-url"
                type="url"
                placeholder="https://example.com/"
                value={addSiteBaseUrl}
                onChange={(e) => setAddSiteBaseUrl(e.target.value)}
              />
              <label htmlFor="add-site-topics">Topics (one per line: Title | URL or Title | URL | Description)</label>
              <textarea
                id="add-site-topics"
                className="add-site-topics-textarea"
                placeholder="OAuth 2.0 Explained | https://example.com/oauth"
                value={addSiteTopicsText}
                onChange={(e) => setAddSiteTopicsText(e.target.value)}
                rows={5}
              />
              {addSiteError && <div className="error-box" role="alert">{addSiteError}</div>}
              <div className="add-site-actions">
                <button
                  type="button"
                  className="gen-btn secondary"
                  onClick={() => { setShowAddSite(false); setAddSiteError(null) }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="gen-btn"
                  disabled={addSiteSubmitting || !addSiteName.trim()}
                  onClick={async () => {
                    const lines = addSiteTopicsText.trim().split(/\n/).filter(Boolean)
                    const topicInputs: TopicInput[] = lines
                      .map((line) => {
                        const parts = line.split('|').map((s) => s.trim())
                        return { title: parts[0] ?? '', url: parts[1] ?? '', description: parts[2] ?? '' }
                      })
                      .filter((t) => t.title)
                    if (!topicInputs.length) {
                      setAddSiteError('Add at least one topic (Title | URL).')
                      return
                    }
                    setAddSiteError(null)
                    setAddSiteSubmitting(true)
                    try {
                      await addSite(addSiteName.trim(), addSiteBaseUrl.trim(), topicInputs)
                      const sitesList = await fetchSites()
                      setSites(sitesList)
                      setTopics(sitesList.flatMap((s) => s.topics.map((t) => ({ ...t, site_id: s.id, site_name: s.name }))))
                      setShowAddSite(false)
                      setAddSiteName('')
                      setAddSiteBaseUrl('')
                      setAddSiteTopicsText('')
                    } catch (e) {
                      setAddSiteError(e instanceof Error ? e.message : 'Failed to add site')
                    } finally {
                      setAddSiteSubmitting(false)
                    }
                  }}
                >
                  {addSiteSubmitting ? 'Adding…' : 'Add site'}
                </button>
              </div>
            </div>
          )}

          <label htmlFor="detail-input">Detailed input (topic, description, or paste article)</label>
          <textarea
            id="detail-input"
            className="detail-textarea"
            placeholder="e.g. How OAuth 2.0 works · or paste steps: Step 1: Request → Step 2: Auth → …"
            value={detailInput}
            onChange={(e) => setDetailInput(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault()
                handleGenerate()
              }
            }}
          />

          <div className="ratio-toggles">
            {(['16:9', '9:16', '1:1'] as const).map((r) => (
              <button
                key={r}
                type="button"
                className={`ratio-btn ${aspectRatio === r ? 'active' : ''}`}
                onClick={() => setAspectRatio(r)}
              >
                {r}
              </button>
            ))}
          </div>

          <button
            type="button"
            className="gen-btn"
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? 'Generating…' : 'Generate'}
          </button>
        </div>
        </section>

        {topics.length > 0 && (
          <div className="input-card" style={{ marginTop: '0.5rem' }}>
            <label>Quick pick (click to fill)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
              {EXAMPLE_CHIPS.map(({ label, concept }) => (
                <button
                  key={label}
                  type="button"
                  className="ratio-btn"
                  onClick={() => {
                    setDetailInput(concept)
                    setSelectedTopicKey('')
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}

        {loading && (
          <div className="loading-card">
            <div className="spinner" />
            <p style={{ color: 'var(--muted)', margin: 0 }}>Researching, architecting workflow, designing flow and script…</p>
          </div>
        )}

        {result && !loading && (
          <section className="screening-room" aria-label="Preview and controls">
          <div className="screening-room-label" aria-hidden>Live preview</div>
            <div
              className="result-area"
            >
            <div className="toolbar">
              {generatingAudio && (
                <div className="toolbar-progress" role="status" aria-live="polite">
                  <span className="toolbar-progress-spinner" aria-hidden />
                  <span>Generating audio…</span>
                </div>
              )}
              <div className="toolbar-actions">
                <button
                  type="button"
                  className="primary"
                  title={isPlayingSync ? 'Pause' : cachedNarrationDataUrl ? 'Play animation + narration from start' : 'Generate audio then play'}
                  disabled={!result?.voiceover_script || generatingAudio}
                  onClick={handlePlaySync}
                >
                  {isPlayingSync ? '⏸ Pause' : generatingAudio ? '…' : '▶ Play'}
                </button>
                <button
                  type="button"
                  className="primary"
                  onClick={() => {
                    if (!result?.svg_source) return
                    const w = window.open('', '_blank')
                    if (!w) return
                    w.document.write(result.svg_source)
                    w.document.close()
                  }}
                >
                  Open SVG
                </button>
                <button
                  type="button"
                  onClick={handleNarrate}
                  disabled={!result?.voiceover_script || generatingAudio}
                  title={narrating ? 'Stop playback' : 'Play narration from start (generates audio if needed)'}
                >
                  {narrating ? '⏹ Stop' : generatingAudio ? '…' : '🔊 Narrate'}
                </button>
                <button
                  type="button"
                  onClick={handleDownloadAudio}
                  disabled={!result?.voiceover_script || generatingAudio || downloadingAudio}
                  title="Download narration as WAV (generates audio if needed)"
                >
                  {downloadingAudio ? '…' : generatingAudio ? '…' : 'Download audio'}
                </button>
                <label className="toolbar-label">
                  Voice
                  <select value={voice} onChange={(e) => setVoice(e.target.value)}>
                    {VOICES.map((v) => (
                      <option key={v} value={v}>{v}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="diagram-appearance-toolbar">
                <label className="diagram-toolbar-label">
                  Theme
                  <select value={theme} onChange={(e) => setTheme(e.target.value)}>
                    {THEMES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </label>
                <label className="diagram-toolbar-label">
                  Font
                  <select value={fontFamily} onChange={(e) => setFontFamily(e.target.value)}>
                    {FONTS.map((f) => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </label>
                <label className="diagram-toolbar-label">
                  Size
                  <select value={fontSize} onChange={(e) => setFontSize(Number(e.target.value))}>
                    {FONT_SIZES.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </label>
                <label className="diagram-toolbar-label">
                  Accent
                  <select
                    value={customAccentHex ? 'custom' : accentColor}
                    onChange={(e) => {
                      const v = e.target.value
                      if (v === 'custom') {
                        const hex = ACCENT_COLORS.find((a) => a.value === accentColor)?.hex ?? '#3b82f6'
                        setCustomAccentHex(hex)
                        return
                      }
                      setCustomAccentHex(null)
                      setAccentColor(v)
                    }}
                  >
                    {ACCENT_COLORS.map((a) => (
                      <option key={a.value} value={a.value}>{a.label}</option>
                    ))}
                    <option value="custom">Custom…</option>
                  </select>
                </label>
                {customAccentHex !== null && (
                  <span className="diagram-toolbar-inline">
                    <input
                      type="color"
                      value={customAccentHex}
                      onChange={(e) => setCustomAccentHex(e.target.value)}
                      title="Accent color"
                      className="diagram-toolbar-color"
                    />
                    <input
                      type="text"
                      className="diagram-toolbar-hex"
                      value={customAccentHex}
                      onChange={(e) => setCustomAccentHex(e.target.value)}
                      placeholder="#hex"
                    />
                    <button type="button" className="diagram-toolbar-reset" onClick={() => setCustomAccentHex(null)} title="Use preset">↩</button>
                  </span>
                )}
                <div className="diagram-toolbar-ratio">
                  <span className="diagram-toolbar-ratio-label">Ratio</span>
                  <div className="ratio-toggles">
                    {(['16:9', '9:16', '1:1'] as const).map((r) => (
                      <button
                        key={r}
                        type="button"
                        className={`ratio-btn ${aspectRatio === r ? 'active' : ''}`}
                        onClick={() => setAspectRatio(r)}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>
                <label className="diagram-toolbar-label">
                  Bg
                  <select
                    value={animationBgMode}
                    onChange={(e) => setAnimationBgMode(e.target.value as 'theme' | 'solid' | 'gradient')}
                  >
                    <option value="theme">Theme</option>
                    <option value="solid">Solid</option>
                    <option value="gradient">Gradient</option>
                  </select>
                </label>
                {animationBgMode === 'solid' && (
                  <span className="diagram-toolbar-inline">
                    <input type="color" value={animationBgSolid} onChange={(e) => setAnimationBgSolid(e.target.value)} title="Background" className="diagram-toolbar-color" />
                    <input type="text" className="diagram-toolbar-hex" value={animationBgSolid} onChange={(e) => setAnimationBgSolid(e.target.value)} placeholder="#fff" />
                  </span>
                )}
                {animationBgMode === 'gradient' && (
                  <span className="diagram-toolbar-inline">
                    <input type="color" value={animationBgGradStart} onChange={(e) => setAnimationBgGradStart(e.target.value)} title="Start" className="diagram-toolbar-color" />
                    <input type="color" value={animationBgGradEnd} onChange={(e) => setAnimationBgGradEnd(e.target.value)} title="End" className="diagram-toolbar-color" />
                  </span>
                )}
                <div className="diagram-toolbar-item-sizes">
                  <button
                    type="button"
                    className="appearance-toggle-inner"
                    onClick={() => setShowItemSizes((s) => !s)}
                    aria-expanded={showItemSizes}
                  >
                    📐 Item sizes {showItemSizes ? '▾' : '▸'}
                  </button>
                  {showItemSizes && result?.svg_source && (
                    <div className="item-sizes-dropdown">
                      {getSvgNodeIds(result.svg_source, result.timeline).length === 0 ? (
                        <p className="item-sizes-empty">No resizable nodes.</p>
                      ) : (
                        <ul className="item-sizes-list">
                          {getSvgNodeIds(result.svg_source, result.timeline).map(({ id, label }) => (
                            <li key={id} className="item-size-row">
                              <span className="item-size-label" title={id}>{label.length > 20 ? label.slice(0, 17) + '…' : label}</span>
                              <div className="item-size-control">
                                <input
                                  type="range"
                                  min={0.5}
                                  max={2}
                                  step={0.05}
                                  value={itemScales[id] ?? 1}
                                  onChange={(e) => setItemScales((prev) => ({ ...prev, [id]: Number(e.target.value) }))}
                                  title={`Scale ${(itemScales[id] ?? 1).toFixed(2)}`}
                                />
                                <span className="item-size-value">{(itemScales[id] ?? 1).toFixed(2)}×</span>
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
                <label className="diagram-toolbar-label appearance-check">
                  <input
                    type="checkbox"
                    checked={useCustomGradient}
                    onChange={(e) => setUseCustomGradient(e.target.checked)}
                  />
                  <span>Custom gradient</span>
                </label>
                {useCustomGradient && (
                  <span className="diagram-toolbar-inline">
                    <input type="color" value={gradientStartHex} onChange={(e) => setGradientStartHex(e.target.value)} title="Start" className="diagram-toolbar-color" />
                    <input type="color" value={gradientEndHex} onChange={(e) => setGradientEndHex(e.target.value)} title="End" className="diagram-toolbar-color" />
                  </span>
                )}
              </div>
            </div>

            {selectedObjectIds.length > 0 && (
              <div className="properties-panel" role="region" aria-label="Object properties">
                <div aria-live="polite" aria-atomic className="sr-only">
                  {selectedObjectIds.length === 1
                    ? `Object selected: ${getSvgNodeIds(result?.svg_source, result?.timeline ?? []).find((n) => n.id === selectedObjectIds[0])?.label ?? selectedObjectIds[0]}. Use Properties to edit color, position, and size. Press Escape to clear selection.`
                    : `${selectedObjectIds.length} objects selected. Press Escape to clear selection.`}
                </div>
                <h3>Object properties</h3>
                <div className="properties-grid">
                  {selectedObjectIds.slice(0, 3).map((id) => {
                    const override = objectOverrides[id] ?? {}
                    return (
                      <React.Fragment key={id}>
                        <div className="prop-group">
                          <label htmlFor={`prop-fill-${id}`}>Fill</label>
                          <div className="prop-color-row">
                            <input
                              id={`prop-fill-${id}`}
                              type="color"
                              value={override.fill ?? '#3b82f6'}
                              onChange={(e) => setObjectOverrides((prev) => ({ ...prev, [id]: { ...prev[id], fill: e.target.value } }))}
                              title="Fill color"
                            />
                            <input
                              type="text"
                              className="hex-input"
                              value={override.fill ?? ''}
                              onChange={(e) => setObjectOverrides((prev) => ({ ...prev, [id]: { ...prev[id], fill: e.target.value || undefined } }))}
                              placeholder="#hex"
                            />
                          </div>
                        </div>
                        <div className="prop-group">
                          <label htmlFor={`prop-x-${id}`}>X</label>
                          <input
                            id={`prop-x-${id}`}
                            type="number"
                            value={override.x ?? 0}
                            onChange={(e) => setObjectOverrides((prev) => ({ ...prev, [id]: { ...prev[id], x: Number(e.target.value) || 0 } }))}
                          />
                        </div>
                        <div className="prop-group">
                          <label htmlFor={`prop-y-${id}`}>Y</label>
                          <input
                            id={`prop-y-${id}`}
                            type="number"
                            value={override.y ?? 0}
                            onChange={(e) => setObjectOverrides((prev) => ({ ...prev, [id]: { ...prev[id], y: Number(e.target.value) || 0 } }))}
                          />
                        </div>
                        <div className="prop-group">
                          <label htmlFor={`prop-scaleX-${id}`}>Scale X</label>
                          <input
                            id={`prop-scaleX-${id}`}
                            type="number"
                            min={0.2}
                            max={3}
                            step={0.1}
                            value={override.scaleX ?? itemScales[id] ?? 1}
                            onChange={(e) => setObjectOverrides((prev) => ({ ...prev, [id]: { ...prev[id], scaleX: Number(e.target.value) || 1 } }))}
                          />
                        </div>
                        <div className="prop-group">
                          <label htmlFor={`prop-scaleY-${id}`}>Scale Y</label>
                          <input
                            id={`prop-scaleY-${id}`}
                            type="number"
                            min={0.2}
                            max={3}
                            step={0.1}
                            value={override.scaleY ?? itemScales[id] ?? 1}
                            onChange={(e) => setObjectOverrides((prev) => ({ ...prev, [id]: { ...prev[id], scaleY: Number(e.target.value) || 1 } }))}
                          />
                        </div>
                      </React.Fragment>
                    )
                  })}
                </div>
                {selectedObjectIds.length > 1 && <p style={{ fontSize: '0.8rem', color: 'var(--muted)', margin: '0.5rem 0 0' }}>Editing first 3 selected. Use inputs to sync.</p>}
              </div>
            )}

            <div
              ref={layoutRef}
              className="preview-layout preview-layout-70-30"
              style={{ minHeight: 320, height: 'min(85vh, calc(100vh - 220px))' }}
            >
              {/* Top row: Animation 70% | Steps 30% */}
              {panelOrder.map((id, index) => {
                const size = panelSizes[id]
                const isLast = index === panelOrder.length - 1
                return (
                  <React.Fragment key={id}>
                    <div
                      className={`layout-panel ${isLast ? 'panel-grow' : ''}`}
                      style={isLast ? { minWidth: '20%', flex: '1 1 0' } : { flex: `0 0 ${size}%` }}
                      onDragOver={(e) => handlePanelDragOver(e, index)}
                      onDrop={(e) => handlePanelDrop(e, index)}
                    >
                      {id === 'animation' && (
                        <div className="dock-panel" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                          <div
                            className="panel-header"
                            draggable
                            onDragStart={() => handlePanelDragStart('animation', index)}
                            onDragEnd={handlePanelDragEnd}
                          >
                            <span className="panel-drag-handle" title="Drag to reorder">⋮⋮</span>
                            Animation
                          </div>
                          <div className="viewer-wrap viewer-area" style={{ flex: 1, minHeight: 0 }}>
                            <div className={`viewer-container ratio-${aspectRatio.replace(':', '-')}`}>
                              {result.svg_source && (
                                <div
                                  ref={viewerContainerRef}
                                  className="viewer-inline-wrap"
                                  onClick={handleViewerClick}
                                  onMouseDown={handleViewerMouseDown}
                                  role="img"
                                  aria-label="Animation canvas"
                                >
                                  <div dangerouslySetInnerHTML={{ __html: result.svg_source }} />
                                  {selectedObjectIds.length > 0 && (
                                    <div className="selection-handles" aria-hidden>
                                      {selectedObjectIds.length === 1 && selectionBox && (
                                        <>
                                          <div
                                            className="handle resize-nw"
                                            style={{ left: selectionBox.left, top: selectionBox.top }}
                                            onMouseDown={(ev) => {
                                              ev.stopPropagation()
                                              const id = selectedObjectIds[0]
                                              const scale = objectOverrides[id]?.scaleX ?? itemScales[id] ?? 1
                                              resizeDragRef.current = { id, corner: 'nw', startX: ev.clientX, startY: ev.clientY, startScaleX: scale, startScaleY: objectOverrides[id]?.scaleY ?? scale }
                                              document.body.style.cursor = 'nw-resize'
                                              document.body.style.userSelect = 'none'
                                            }}
                                          />
                                          <div
                                            className="handle resize-ne"
                                            style={{ left: selectionBox.left + selectionBox.width - 10, top: selectionBox.top }}
                                            onMouseDown={(ev) => {
                                              ev.stopPropagation()
                                              const id = selectedObjectIds[0]
                                              const scale = objectOverrides[id]?.scaleX ?? itemScales[id] ?? 1
                                              resizeDragRef.current = { id, corner: 'ne', startX: ev.clientX, startY: ev.clientY, startScaleX: scale, startScaleY: objectOverrides[id]?.scaleY ?? scale }
                                              document.body.style.cursor = 'ne-resize'
                                              document.body.style.userSelect = 'none'
                                            }}
                                          />
                                          <div
                                            className="handle resize-sw"
                                            style={{ left: selectionBox.left, top: selectionBox.top + selectionBox.height - 10 }}
                                            onMouseDown={(ev) => {
                                              ev.stopPropagation()
                                              const id = selectedObjectIds[0]
                                              const scale = objectOverrides[id]?.scaleX ?? itemScales[id] ?? 1
                                              resizeDragRef.current = { id, corner: 'sw', startX: ev.clientX, startY: ev.clientY, startScaleX: scale, startScaleY: objectOverrides[id]?.scaleY ?? scale }
                                              document.body.style.cursor = 'sw-resize'
                                              document.body.style.userSelect = 'none'
                                            }}
                                          />
                                          <div
                                            className="handle resize-se"
                                            style={{ left: selectionBox.left + selectionBox.width - 10, top: selectionBox.top + selectionBox.height - 10 }}
                                            onMouseDown={(ev) => {
                                              ev.stopPropagation()
                                              const id = selectedObjectIds[0]
                                              const scale = objectOverrides[id]?.scaleX ?? itemScales[id] ?? 1
                                              resizeDragRef.current = { id, corner: 'se', startX: ev.clientX, startY: ev.clientY, startScaleX: scale, startScaleY: objectOverrides[id]?.scaleY ?? scale }
                                              document.body.style.cursor = 'se-resize'
                                              document.body.style.userSelect = 'none'
                                            }}
                                          />
                                        </>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )}
                              {result.timeline?.length ? (
                                <div className="step-overlay" aria-live="polite">
                                  <div className="step-overlay-label">
                                    Step {Math.min(currentStepIndex + 1, result.timeline.length)}: {result.timeline[Math.min(currentStepIndex, result.timeline.length - 1)]?.label ?? '—'}
                                  </div>
                                  {result.timeline[Math.min(currentStepIndex, result.timeline.length - 1)]?.narration && (
                                    <div className="step-overlay-narration">
                                      {result.timeline[Math.min(currentStepIndex, result.timeline.length - 1)].narration!.slice(0, 120)}
                                      {(result.timeline[Math.min(currentStepIndex, result.timeline.length - 1)].narration?.length ?? 0) > 120 ? '…' : ''}
                                    </div>
                                  )}
                                </div>
                              ) : null}
                            </div>
                          </div>
                        </div>
                      )}
                      {id === 'steps' && (
                        <div className="dock-panel" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                          <div
                            className="panel-header"
                            draggable
                            onDragStart={() => handlePanelDragStart('steps', index)}
                            onDragEnd={handlePanelDragEnd}
                          >
                            <span className="panel-drag-handle" title="Drag to reorder">⋮⋮</span>
                            Steps
                          </div>
                          <div className="panel-body" style={{ overflow: 'auto' }}>
                            {result.timeline?.length ? (
                              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                                {result.timeline.map((step, i) => (
                                  <li
                                    key={i}
                                    style={{
                                      marginBottom: '0.5rem',
                                      fontWeight: i === currentStepIndex ? 600 : 400,
                                      color: i === currentStepIndex ? 'var(--ga-primary)' : undefined,
                                    }}
                                  >
                                    Step {i + 1}: {step.label ?? step.id ?? '—'}
                                    {i === currentStepIndex && step.narration && (
                                      <div style={{ fontSize: '0.8rem', color: 'var(--ga-main-text-secondary)', marginTop: '0.25rem' }}>
                                        {step.narration.slice(0, 200)}{(step.narration?.length ?? 0) > 200 ? '…' : ''}
                                      </div>
                                    )}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <span style={{ color: 'var(--ga-main-text-secondary)' }}>No steps</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    {!isLast && (
                      <div
                        className="resize-handle resize-handle-h"
                        title="Drag to resize panels"
                        onMouseDown={(e) => handlePanelResizeMouseDown(index, e)}
                        style={{ flexShrink: 0 }}
                      />
                    )}
                  </React.Fragment>
                )
              })}
            </div>

            {/* Bottom: Description full width */}
            <div className="preview-layout description-bottom">
              <div className="dock-panel description-panel" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="panel-header">
                  Script / Description
                </div>
                <div className="panel-body">{result.voiceover_script || '—'}</div>
              </div>
            </div>
          </div>
          </section>
        )}
          </div>
        </main>
      </div>
    </div>
  )
}

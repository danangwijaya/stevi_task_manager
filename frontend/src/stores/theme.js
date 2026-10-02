import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // Available font options
  const fontOptions = [
    {
      id: 'jakarta',
      name: 'Plus Jakarta Sans',
      badge: 'Rekomendasi',
      category: 'Modern Enterprise / Government',
      description: 'Font resmi modern, kurva halus, proporsional dan sangat berwibawa.',
      fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      tracking: '-0.012em',
      headingTracking: '-0.02em'
    },
    {
      id: 'barlow',
      name: 'Barlow',
      badge: 'GIS Technical',
      category: 'Field-Instrument & Navigation',
      description: 'Font ringkas ala instrumen navigasi lapangan. Hemat ruang horizontal dan tajam.',
      fontFamily: "'Barlow', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      tracking: '0.005em',
      headingTracking: '-0.01em'
    },
    {
      id: 'inter',
      name: 'Inter',
      badge: 'Global UI',
      category: 'International UI Standard',
      description: 'Standar emas global aplikasi web modern (Figma, GitHub, Mapbox). Netral dan presisi.',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      tracking: '-0.011em',
      headingTracking: '-0.02em'
    }
  ]

  // Available UI Density options
  const densityOptions = [
    {
      id: 'compact',
      name: 'Ringkas GIS (Desktop Density)',
      badge: 'QGIS / ArcGIS Style',
      description: 'Padding lebih hemat, tombol dan panel rapat agar area peta maksimal.'
    },
    {
      id: 'comfortable',
      name: 'Standar Lapang (Comfortable)',
      badge: 'Modern Web',
      description: 'Spasi dan jarak elemen lebih lega, ideal untuk layar besar.'
    }
  ]

  // Available Base Font Size options
  const fontSizeOptions = [
    { id: 'compact', name: 'Kecil / Ringkas', size: '13.5px', description: 'Informasi padat untuk laptop/layar sedang' },
    { id: 'normal', name: 'Standar Normal', size: '14.5px', description: 'Ukuran optimal standar GEOSTEVIA' },
    { id: 'large', name: 'Besar & Jelas', size: '15.5px', description: 'Keterbacaan maksimal untuk proyektor/presentasi' }
  ]

  // Available Border Radius options
  const radiusOptions = [
    { id: 'sharp', name: 'Sudut Tegas (4px)', value: '4px', description: 'Gaya presisi teknis desktop GIS klasik' },
    { id: 'medium', name: 'Sudut Halus (8px)', value: '8px', description: 'Standar modern seimbang dan rapi' },
    { id: 'soft', name: 'Sudut Membulat (12px)', value: '12px', description: 'Kesan aplikasi modern kekinian' }
  ]

  // Available Accent Color options
  const accentOptions = [
    { id: 'rose', name: 'GEOSTEVIA Crimson', hex: '#e11d48', bgClass: 'bg-rose-600', ringClass: 'ring-rose-500' },
    { id: 'emerald', name: 'Forest Emerald', hex: '#059669', bgClass: 'bg-emerald-600', ringClass: 'ring-emerald-500' },
    { id: 'slate', name: 'Neutral Monokrom GIS', hex: '#334155', bgClass: 'bg-slate-700', ringClass: 'ring-slate-500' },
    { id: 'indigo', name: 'Deep Maritime Indigo', hex: '#4f46e5', bgClass: 'bg-indigo-600', ringClass: 'ring-indigo-500' }
  ]

  // Current active states
  const fontFamily = ref('jakarta')
  const fontSize = ref('normal')
  const density = ref('compact')
  const borderRadius = ref('medium')
  const accentColor = ref('rose')
  const showStatusBar = ref(true)
  const showShortcuts = ref(true)

  const activeFont = computed(() => {
    return fontOptions.find(f => f.id === fontFamily.value) || fontOptions[0]
  })

  const activeFontSize = computed(() => {
    return fontSizeOptions.find(s => s.id === fontSize.value) || fontSizeOptions[1]
  })

  // Apply state to DOM & document CSS variables
  const applyTheme = () => {
    const root = document.documentElement
    const body = document.body

    // 1. Font Family & Tracking
    const font = activeFont.value
    root.style.setProperty('--app-font-family', font.fontFamily)
    root.style.setProperty('--app-font-tracking', font.tracking)
    root.style.setProperty('--app-heading-tracking', font.headingTracking)

    // Remove legacy font classes
    body.classList.remove('font-jakarta', 'font-barlow', 'font-inter')
    body.classList.add(`font-${font.id}`)

    // 2. Base Font Size
    const fs = activeFontSize.value
    root.style.setProperty('--app-base-font-size', fs.size)

    // 3. Border Radius
    const r = radiusOptions.find(x => x.id === borderRadius.value) || radiusOptions[1]
    root.style.setProperty('--app-border-radius', r.value)

    // 4. UI Density Class
    body.classList.remove('density-compact', 'density-comfortable')
    body.classList.add(`density-${density.value}`)

    // 5. Save to localStorage
    const payload = {
      fontFamily: fontFamily.value,
      fontSize: fontSize.value,
      density: density.value,
      borderRadius: borderRadius.value,
      accentColor: accentColor.value,
      showStatusBar: showStatusBar.value,
      showShortcuts: showShortcuts.value
    }
    localStorage.setItem('geostevia_ui_theme', JSON.stringify(payload))
  }

  // Load from localStorage or set defaults
  const loadTheme = () => {
    try {
      const raw = localStorage.getItem('geostevia_ui_theme')
      if (raw) {
        const data = JSON.parse(raw)
        if (data.fontFamily) fontFamily.value = data.fontFamily
        if (data.fontSize) fontSize.value = data.fontSize
        if (data.density) density.value = data.density
        if (data.borderRadius) borderRadius.value = data.borderRadius
        if (data.accentColor) accentColor.value = data.accentColor
        if (data.showStatusBar !== undefined) showStatusBar.value = data.showStatusBar
        if (data.showShortcuts !== undefined) showShortcuts.value = data.showShortcuts
      }
    } catch (e) {
      console.warn('Gagal membaca preferensi UI:', e)
    }
    applyTheme()
  }

  // Reset to original default settings
  const resetDefaults = () => {
    fontFamily.value = 'jakarta'
    fontSize.value = 'normal'
    density.value = 'compact'
    borderRadius.value = 'medium'
    accentColor.value = 'rose'
    showStatusBar.value = true
    showShortcuts.value = true
    applyTheme()
  }

  return {
    fontOptions,
    densityOptions,
    fontSizeOptions,
    radiusOptions,
    accentOptions,
    fontFamily,
    fontSize,
    density,
    borderRadius,
    accentColor,
    showStatusBar,
    showShortcuts,
    activeFont,
    activeFontSize,
    applyTheme,
    loadTheme,
    resetDefaults
  }
})

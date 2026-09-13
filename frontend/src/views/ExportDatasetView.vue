<template>
  <div class="p-6 max-w-5xl mx-auto space-y-6 font-sans">
    <!-- Header -->
    <div class="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center gap-2.5 flex-wrap">
          <div class="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center text-lg font-bold shadow-xs">
            <Package :size="20" />
          </div>
          <div>
            <h1 class="text-xl font-extrabold text-slate-900 tracking-tight">Deep Learning U-Net Dataset Exporter</h1>
            <span class="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full font-extrabold font-mono shadow-2xs">
              1024×1024 px
            </span>
          </div>
        </div>
        <p class="text-xs text-slate-500 max-w-xl leading-relaxed">
          Otomatisasi pemotongan citra Sentinel-2 (Multi-spectral + Indeks + GLCM) dan rasterisasi poligon menjadi pasangan gambar & mask siap latih.
        </p>
      </div>

      <button
        @click="triggerExport"
        :disabled="exporting"
        class="bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-xs px-6 py-3 rounded-2xl shadow-md shadow-emerald-600/20 flex items-center gap-2 transition-all shrink-0 disabled:opacity-50 cursor-pointer"
      >
        <RotateCw v-if="exporting" :size="16" class="animate-spin text-white" />
        <Zap v-else :size="16" class="text-amber-300 fill-amber-300" />
        <span>{{ exporting ? 'Sedang Memproses Dataset...' : 'Generate & Export Dataset U-Net' }}</span>
      </button>
    </div>

    <!-- Pipeline Spec Cards (Light Theme) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-white border border-slate-200 p-4 rounded-2xl shadow-xs">
        <div class="text-slate-500 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5">
          <Grid :size="14" class="text-slate-400" />
          <span>Ukuran Patch & Resolusi</span>
        </div>
        <div class="text-lg font-extrabold text-slate-900 mt-1">1024 × 1024 Pixel</div>
        <div class="text-[11px] text-teal-700 font-semibold mt-0.5">10m GSD (10.24km × 10.24km Ground Area)</div>
      </div>

      <div class="bg-white border border-slate-200 p-4 rounded-2xl shadow-xs">
        <div class="text-slate-500 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5">
          <Cpu :size="14" class="text-slate-400" />
          <span>Multi-Spectral Tensor Channels</span>
        </div>
        <div class="text-lg font-extrabold text-teal-700 mt-1">20 Bands Feature Stack</div>
        <div class="text-[11px] text-slate-500 mt-0.5 font-medium">S2 (B2-B12) + NDVI/MNDWI + GLCM + Fenologi</div>
      </div>

      <div class="bg-white border border-slate-200 p-4 rounded-2xl shadow-xs">
        <div class="text-slate-500 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5">
          <PieChart :size="14" class="text-slate-400" />
          <span>Data Partition Split</span>
        </div>
        <div class="text-lg font-extrabold text-purple-700 mt-1">70% / 15% / 15%</div>
        <div class="text-[11px] text-purple-700/80 mt-0.5 font-semibold">Train / Validation / Test (Tile-level split)</div>
      </div>
    </div>

    <!-- Export Result Card (if exported) -->
    <div v-if="exportResult" class="bg-emerald-50 border border-emerald-300 p-6 rounded-3xl shadow-sm space-y-4">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center justify-center text-xl shadow-2xs">
            <PackageOpen :size="20" />
          </div>
          <div>
            <div class="text-sm font-extrabold text-emerald-900">Dataset Berhasil Di-Generate!</div>
            <div class="text-xs text-emerald-800/90">{{ exportResult.message }}</div>
          </div>
        </div>

        <a
          :href="exportResult.download_url"
          download
          class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-sm flex items-center gap-2 transition-all cursor-pointer"
        >
          <Download :size="14" />
          <span>Download ZIP Dataset</span>
        </a>
      </div>

      <!-- Split Breakdown -->
      <div class="grid grid-cols-3 gap-3 pt-2">
        <div class="bg-white border border-emerald-200 p-3 rounded-xl text-center shadow-2xs">
          <div class="text-[11px] text-slate-500 font-semibold">Training Patches (70%)</div>
          <div class="text-lg font-extrabold text-slate-900">{{ exportResult.splits?.train || 0 }} Patches</div>
        </div>
        <div class="bg-white border border-emerald-200 p-3 rounded-xl text-center shadow-2xs">
          <div class="text-[11px] text-slate-500 font-semibold">Validation Patches (15%)</div>
          <div class="text-lg font-extrabold text-slate-900">{{ exportResult.splits?.val || 0 }} Patches</div>
        </div>
        <div class="bg-white border border-emerald-200 p-3 rounded-xl text-center shadow-2xs">
          <div class="text-[11px] text-slate-500 font-semibold">Test Patches (15%)</div>
          <div class="text-lg font-extrabold text-slate-900">{{ exportResult.splits?.test || 0 }} Patches</div>
        </div>
      </div>
    </div>

    <!-- Interactive Spatial Split Map Preview -->
    <div class="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <MapPin :size="14" class="text-teal-600" />
            <span>Distribusi Spasial Partisi Sampel Data Latih</span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">
            Peta sebaran acak berstrata (spatial split) untuk memastikan independensi spasial dataset U-Net.
          </p>
        </div>

        <!-- Split Legend Indicators -->
        <div class="flex items-center gap-3 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold">
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded bg-emerald-500 inline-block border border-emerald-600"></span>
            <span class="text-slate-700">Train (70%)</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded bg-blue-500 inline-block border border-blue-600"></span>
            <span class="text-slate-700">Val (15%)</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded bg-amber-500 inline-block border border-amber-600"></span>
            <span class="text-slate-700">Test (15%)</span>
          </div>
        </div>
      </div>

      <!-- Map Container -->
      <div class="h-80 w-full rounded-2xl overflow-hidden border border-slate-200 relative shadow-inner">
        <div id="split-map-container" class="w-full h-full z-0"></div>
      </div>
    </div>

    <!-- Dataset Structure Preview -->
    <div class="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-3">
      <div class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
        <FolderTree :size="14" class="text-slate-400" />
        <span>Struktur File Dataset yang Dihasilkan</span>
      </div>

      <pre class="bg-slate-50 p-4 rounded-2xl text-xs font-mono text-slate-800 overflow-x-auto border border-slate-200 leading-relaxed">
dataset_sentinel2_unet/
├── metadata.json                 # Metadata lengkap & statistik piksel
├── train/
│   ├── images/
│   │   ├── patch_SB_R00_C00_2026.tif  (Tensor 20-band Sentinel-2)
│   │   └── ...
│   ├── masks/
│   │   ├── patch_SB_R00_C00_2026.png  (Mask integer 0..12)
│   │   └── ...
│   └── masks_color/
│       └── patch_SB_R00_C00_2026_color.png (Visual RGB Mask untuk QC)
├── val/
│   ├── images/
│   └── masks/
└── test/
    ├── images/
    └── masks/
      </pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import {
  Package,
  RotateCw,
  Zap,
  Grid,
  Cpu,
  PieChart,
  PackageOpen,
  Download,
  MapPin,
  FolderTree
} from 'lucide-vue-next'
import api from '../services/api'
import { useTasksStore } from '../stores/tasks'


const tasksStore = useTasksStore()
const exporting = ref(false)
const exportResult = ref(null)

let splitMap = null
let splitGridLayer = null

// Deterministic partition hash for a grid
const getGridSplit = (gridCode) => {
  let hash = 0
  for (let i = 0; i < gridCode.length; i++) {
    hash = (hash * 31 + gridCode.charCodeAt(i)) % 100
  }
  if (hash < 70) return { name: 'Train', color: '#10b981', fill: '#34d399' }
  if (hash < 85) return { name: 'Validation', color: '#2563eb', fill: '#60a5fa' }
  return { name: 'Test', color: '#f59e0b', fill: '#fbbf24' }
}

onMounted(async () => {
  await tasksStore.fetchProjects()
  await tasksStore.fetchTasks()
  await nextTick()
  initSplitMap()
})

onUnmounted(() => {
  if (splitMap) {
    splitMap.remove()
    splitMap = null
  }
})

const initSplitMap = () => {
  const mapEl = document.getElementById('split-map-container')
  if (!mapEl) return

  if (splitMap) {
    splitMap.remove()
    splitMap = null
  }

  splitMap = L.map('split-map-container', {
    center: [-0.750, 100.500],
    zoom: 8,
    zoomControl: false
  })

  L.control.zoom({ position: 'bottomright' }).addTo(splitMap)

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: '© Esri Satellite Imagery'
  }).addTo(splitMap)

  splitGridLayer = L.featureGroup().addTo(splitMap)

  renderSplitGrids()
}

const renderSplitGrids = () => {
  if (!splitGridLayer || !splitMap) return
  splitGridLayer.clearLayers()

  const tasksToRender = tasksStore.tasks.length > 0 ? tasksStore.tasks : []

  tasksToRender.forEach((task) => {
    const split = getGridSplit(task.grid_code)
    const bounds = [
      [task.min_lat, task.min_lon],
      [task.max_lat, task.max_lon]
    ]

    const rect = L.rectangle(bounds, {
      color: split.color,
      weight: 1.8,
      fillColor: split.fill,
      fillOpacity: 0.6
    })

    rect.bindTooltip(
      `<div class="p-1 font-sans">
        <div class="font-bold text-xs font-mono">${task.grid_code}</div>
        <div class="text-[11px]">Partisi: <b style="color: ${split.color}">${split.name} Set</b></div>
        <div class="text-[10px] text-slate-500">Status: ${task.status}</div>
      </div>`,
      { direction: 'top', sticky: true, className: 'hot-osm-light-tooltip' }
    )

    splitGridLayer.addLayer(rect)
  })

  if (tasksToRender.length > 0) {
    try {
      splitMap.fitBounds(splitGridLayer.getBounds(), { padding: [20, 20] })
    } catch (e) {
      // ignore
    }
  }
}

const triggerExport = async () => {
  exporting.value = true
  exportResult.value = null
  try {
    const response = await api.triggerExport(2026, false)
    exportResult.value = response.data
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal mengekspor dataset.')
  } finally {
    exporting.value = false
  }
}
</script>

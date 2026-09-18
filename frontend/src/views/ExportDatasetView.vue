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
            <h1 class="text-xl font-extrabold text-slate-900 tracking-tight">Dataset Export</h1>
            <span class="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full font-extrabold font-mono shadow-2xs">
              1024×1024 px
            </span>
          </div>
        </div>
        <p class="text-xs text-slate-500 max-w-xl leading-relaxed">
          Otomatisasi pemotongan citra Sentinel-2 (Multi-spectral) dan rasterisasi poligon menjadi pasangan gambar & mask siap latih.
        </p>
      </div>

      <button
        @click="triggerExport"
        :disabled="exporting"
        class="bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-xs px-6 py-3 rounded-2xl shadow-md shadow-emerald-600/20 flex items-center gap-2 transition-all shrink-0 disabled:opacity-50 cursor-pointer"
      >
        <RotateCw v-if="exporting" :size="16" class="animate-spin text-white" />
        <Zap v-else :size="16" class="text-amber-300 fill-amber-300" />
        <span>{{ exporting ? 'Sedang Memproses Dataset...' : 'Generate & Export Dataset' }}</span>
      </button>
    </div>

    <!-- ========================================================================= -->
    <!-- SECTION 1: DOWNLOAD VECTOR DATASET (GEOJSON & SHAPEFILE)                 -->
    <!-- ========================================================================= -->
    <div class="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-5">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-teal-50 text-teal-600 border border-teal-200 flex items-center justify-center shadow-2xs">
              <Layers :size="16" />
            </div>
            <h2 class="text-base font-extrabold text-slate-900">Ekspor Vektor Training Sample (Digitasi On-Screen)</h2>
          </div>
          <p class="text-xs text-slate-500 max-w-2xl leading-relaxed">
            Unduh data poligon hasil digitasi on-screen dalam format GeoJSON atau ESRI Shapefile (.shp zip), lengkap dengan atribut Penutupan Lahan, kode kelas, informasi mapper, dan luas area.
          </p>
        </div>

        <!-- Filter Controls -->
        <div class="flex items-center gap-2.5 flex-wrap">
          <!-- Filter Tahun -->
          <div class="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs font-semibold text-slate-600">
            <Calendar :size="14" class="text-slate-400" />
            <label class="text-[11px] text-slate-400 font-bold uppercase">Tahun:</label>
            <select
              v-model="vectorFilterYear"
              @change="fetchVectorSummary"
              class="bg-transparent border-0 text-slate-800 text-xs font-bold focus:outline-hidden cursor-pointer"
            >
              <option value="">Semua Tahun</option>
              <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>

          <!-- Filter Hanya Approved -->
          <button
            @click="toggleOnlyApproved"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
            :class="vectorOnlyApproved ? 'bg-emerald-50 text-emerald-700 border-emerald-300 shadow-2xs' : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'"
          >
            <CheckCircle2 :size="14" :class="vectorOnlyApproved ? 'text-emerald-600' : 'text-slate-400'" />
            <span>{{ vectorOnlyApproved ? 'Hanya Disetujui (Approved)' : 'Semua Sampel' }}</span>
          </button>
        </div>
      </div>

      <!-- Live Summary Bar -->
      <div v-if="vectorSummary" class="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div class="bg-slate-50 border border-slate-200 p-3.5 rounded-2xl">
          <div class="text-[11px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <Layers :size="13" class="text-slate-400" />
            <span>Total Poligon Sampel</span>
          </div>
          <div class="text-xl font-extrabold text-slate-900 mt-1">
            {{ vectorSummary.total_samples || 0 }} <span class="text-xs font-normal text-slate-500">poligon</span>
          </div>
          <div class="text-[11px] text-teal-700 font-semibold mt-0.5">
            Tersebar di {{ vectorSummary.total_grids || 0 }} grid petak
          </div>
        </div>

        <div class="bg-slate-50 border border-slate-200 p-3.5 rounded-2xl">
          <div class="text-[11px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <PieChart :size="13" class="text-slate-400" />
            <span>Total Luas Area</span>
          </div>
          <div class="text-xl font-extrabold text-teal-700 mt-1">
            {{ formatNumber(vectorSummary.total_area_ha) }} <span class="text-xs font-normal text-slate-500">Ha</span>
          </div>
          <div class="text-[11px] text-slate-500 font-medium mt-0.5">
            {{ formatNumber((vectorSummary.total_area_ha || 0) * 10000) }} m²
          </div>
        </div>

        <div class="bg-slate-50 border border-slate-200 p-3.5 rounded-2xl col-span-2 sm:col-span-1">
          <div class="text-[11px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <Database :size="13" class="text-slate-400" />
            <span>Kelas Tutupan Terisi</span>
          </div>
          <div class="text-xl font-extrabold text-purple-700 mt-1">
            {{ vectorSummary.classes?.length || 0 }} <span class="text-xs font-normal text-slate-500">Kelas PL</span>
          </div>
          <div class="text-[11px] text-slate-500 font-medium mt-0.5">
            Sesuai nomenklatur SNI / GEOSTEVIA
          </div>
        </div>
      </div>

      <!-- Download Option Cards (GeoJSON & Shapefile) -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- GeoJSON Card -->
        <div class="border border-slate-200 hover:border-emerald-300 rounded-2xl p-4 bg-gradient-to-br from-white to-emerald-50/20 transition-all shadow-xs flex flex-col justify-between gap-3">
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-xl bg-emerald-100/70 text-emerald-700 border border-emerald-200 flex items-center justify-center">
                  <FileCode :size="16" />
                </div>
                <div class="font-extrabold text-sm text-slate-900">GeoJSON (.geojson)</div>
              </div>
              <span class="text-[10px] font-mono font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-md">
                WGS 84 (EPSG:4326)
              </span>
            </div>
            <p class="text-xs text-slate-500 leading-relaxed">
              Format standar spasial berbasis JSON dengan struktur FeatureCollection. Kompatibel langsung dengan QGIS, ArcGIS Pro, Google Earth Engine, dan library Python (GeoPandas, Shapely).
            </p>
          </div>

          <button
            @click="downloadGeoJSON"
            :disabled="downloadingGeojson"
            class="w-full bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-xs flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <RotateCw v-if="downloadingGeojson" :size="15" class="animate-spin" />
            <Download v-else :size="15" />
            <span>{{ downloadingGeojson ? 'Mengunduh GeoJSON...' : 'Download GeoJSON (.geojson)' }}</span>
          </button>
        </div>

        <!-- Shapefile Card -->
        <div class="border border-slate-200 hover:border-teal-300 rounded-2xl p-4 bg-gradient-to-br from-white to-teal-50/20 transition-all shadow-xs flex flex-col justify-between gap-3">
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-xl bg-teal-100/70 text-teal-700 border border-teal-200 flex items-center justify-center">
                  <FolderArchive :size="16" />
                </div>
                <div class="font-extrabold text-sm text-slate-900">ESRI Shapefile (.zip)</div>
              </div>
              <span class="text-[10px] font-mono font-bold bg-teal-100 text-teal-800 px-2 py-0.5 rounded-md">
                SHP + DBF + PRJ + SHX
              </span>
            </div>
            <p class="text-xs text-slate-500 leading-relaxed">
              Paket arsip ZIP berisi format standar ESRI Shapefile lengkap (.shp, .shx, .dbf, .prj, .cpg) dengan tabel atribut Penutupan Lahan dan file proyeksi EPSG:4326.
            </p>
          </div>

          <button
            @click="downloadShapefile"
            :disabled="downloadingShp"
            class="w-full bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-xs flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <RotateCw v-if="downloadingShp" :size="15" class="animate-spin" />
            <Download v-else :size="15" />
            <span>{{ downloadingShp ? 'Mengunduh Shapefile...' : 'Download Shapefile (.zip)' }}</span>
          </button>
        </div>
      </div>

      <!-- Atribut Data Vektor Included -->
      <div class="bg-slate-50/90 border border-slate-200 p-4 rounded-2xl space-y-2.5">
        <div class="text-xs font-bold text-slate-700 flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Sliders :size="13" class="text-slate-500" />
            <span>Atribut Penutupan Lahan & Metadata yang Disertakan:</span>
          </div>
          <span class="text-[11px] text-slate-400 font-normal">Format kolom standar SIG</span>
        </div>

        <div class="flex flex-wrap gap-2 text-[11px] font-mono">
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">KODE_PL</span>: ID Kelas (0..12)
          </span>
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">NAMA_PL / PENUTUPAN</span>: Nama Tutupan Lahan
          </span>
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">GRID_CODE</span>: ID Petak Grid
          </span>
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">TAHUN</span>: Tahun Citra
          </span>
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">STATUS</span>: Status QC
          </span>
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">MAPPER</span>: Nama Operator
          </span>
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">LUAS_HA</span>: Luas (Hektar)
          </span>
          <span class="bg-white border border-slate-200 px-2 py-1 rounded-lg text-slate-800 shadow-2xs font-semibold">
            <span class="text-teal-600 font-bold">LUAS_M2</span>: Luas (m²)
          </span>
        </div>

        <!-- Land Cover Class Breakdown Chips -->
        <div v-if="vectorSummary?.classes?.length" class="pt-2 border-t border-slate-200/80">
          <div class="text-[11px] font-bold text-slate-500 mb-1.5">Sebaran Kelas Penutupan Lahan pada Sampel Vektor:</div>
          <div class="flex flex-wrap gap-1.5">
            <div
              v-for="c in vectorSummary.classes"
              :key="c.class_id"
              class="inline-flex items-center gap-1.5 bg-white border border-slate-200 px-2 py-0.5 rounded-lg text-[11px] font-medium text-slate-700 shadow-2xs"
            >
              <span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: c.color }"></span>
              <span>{{ c.class_name }}:</span>
              <span class="font-bold text-slate-900">{{ c.count }} poligon</span>
              <span class="text-[10px] text-slate-400 font-mono">({{ c.total_area_ha }} Ha)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- SECTION 2: MULTI-SPECTRAL RASTER PIPELINE & SPECS                         -->
    <!-- ========================================================================= -->
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
        <div class="text-lg font-extrabold text-teal-700 mt-1">Multi-spectral Feature Stack</div>
        <div class="text-[11px] text-slate-500 mt-0.5 font-medium">Sentinel-2 Surface Reflectance (Multi-spectral)</div>
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
            Peta sebaran acak berstrata (spatial split) untuk memastikan independensi spasial dataset.
          </p>
        </div>

        <!-- Split Legend Indicators -->
        <div class="flex items-center gap-3 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold">
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-sm bg-emerald-500 inline-block border border-emerald-600"></span>
            <span class="text-slate-700">Train (70%)</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-sm bg-blue-500 inline-block border border-blue-600"></span>
            <span class="text-slate-700">Val (15%)</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-sm bg-amber-500 inline-block border border-amber-600"></span>
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
dataset_sentinel2/
├── metadata.json                 # Metadata lengkap & statistik piksel
├── train/
│   ├── images/
│   │   ├── patch_SB_R00_C00_2026.tif  (Tensor Multi-spectral Sentinel-2)
│   │   └── ...
│   ├── masks/
│   │   ├── patch_SB_R00_C00_2026.png  (Mask integer kelas 0..12)
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
  FolderTree,
  Layers,
  FileCode,
  FolderArchive,
  Calendar,
  CheckCircle2,
  Database,
  Sliders
} from 'lucide-vue-next'
import api from '../services/api'
import { useTasksStore } from '../stores/tasks'

const tasksStore = useTasksStore()
const exporting = ref(false)
const exportResult = ref(null)

// Vector Export States
const vectorSummary = ref(null)
const vectorFilterYear = ref('')
const vectorOnlyApproved = ref(false)
const availableYears = ref([])
const downloadingGeojson = ref(false)
const downloadingShp = ref(false)

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

const formatNumber = (val) => {
  if (val === null || val === undefined) return '0'
  return Number(val).toLocaleString('id-ID', { maximumFractionDigits: 2 })
}

const fetchVectorSummary = async () => {
  try {
    const params = {}
    if (vectorFilterYear.value) params.year = vectorFilterYear.value
    if (vectorOnlyApproved.value) params.only_approved = true

    const res = await api.getVectorExportSummary(params)
    vectorSummary.value = res.data
    if (res.data.available_years?.length) {
      availableYears.value = res.data.available_years
    }
  } catch (err) {
    console.error('Failed to fetch vector export summary:', err)
  }
}

const toggleOnlyApproved = () => {
  vectorOnlyApproved.value = !vectorOnlyApproved.value
  fetchVectorSummary()
}

const downloadGeoJSON = async () => {
  downloadingGeojson.value = true
  try {
    const params = {}
    if (vectorFilterYear.value) params.year = vectorFilterYear.value
    if (vectorOnlyApproved.value) params.only_approved = true

    const response = await api.downloadVectorGeoJson(params)
    const blob = new Blob([response.data], { type: 'application/geo+json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `training_samples_penutupan_lahan_${vectorFilterYear.value || 'all'}.geojson`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal mengunduh file GeoJSON.')
  } finally {
    downloadingGeojson.value = false
  }
}

const downloadShapefile = async () => {
  downloadingShp.value = true
  try {
    const params = {}
    if (vectorFilterYear.value) params.year = vectorFilterYear.value
    if (vectorOnlyApproved.value) params.only_approved = true

    const response = await api.downloadVectorShapefile(params)
    const blob = new Blob([response.data], { type: 'application/zip' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `training_samples_penutupan_lahan_${vectorFilterYear.value || 'all'}_shp.zip`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal mengunduh file Shapefile.')
  } finally {
    downloadingShp.value = false
  }
}

onMounted(async () => {
  document.title = 'Dataset Export - GEOSTEVIA'
  await Promise.all([
    tasksStore.fetchProjects(),
    tasksStore.fetchTasks(),
    fetchVectorSummary()
  ])
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

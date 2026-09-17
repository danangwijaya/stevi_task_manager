<template>
  <div class="p-4 sm:p-6 max-w-[1600px] mx-auto space-y-5 font-sans">
    
    <!-- Top Header Banner -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-3xl shadow-sm">
      <div class="space-y-1">
        <div class="flex items-center gap-2.5 flex-wrap">
          <div class="p-2 bg-rose-50 text-rose-600 rounded-2xl border border-rose-100">
            <ShieldCheck :size="22" />
          </div>
          <h1 class="text-xl font-extrabold text-slate-900 tracking-tight">Quality Control (QC) & Review Studio</h1>
          <span
            class="text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider border shadow-2xs flex items-center gap-1.5"
            :class="authStore.isReviewer ? 'bg-amber-50 text-amber-800 border-amber-300' : 'bg-rose-50 text-rose-700 border-rose-200'"
          >
            <ShieldCheck v-if="authStore.isReviewer" :size="13" class="text-amber-600" />
            <Eye v-else :size="13" class="text-rose-600" />
            <span>{{ authStore.isReviewer ? (authStore.isAdmin ? 'Akses Admin' : 'Akses Supervisi') : 'Mode Lihat Kontributor' }}</span>
          </span>
        </div>
        <p class="text-xs text-slate-500 max-w-2xl leading-relaxed">
          Inspeksi visual peta hasil digitasi secara langsung dengan citra Sentinel-2, periksa kepatuhan topologi, dan berikan persetujuan atau catatan revisi tanpa perlu membuka studio terpisah.
        </p>
      </div>

      <div class="flex items-center gap-2.5 flex-wrap">
        <span class="text-xs font-mono bg-orange-50 text-orange-800 px-3.5 py-2 rounded-xl border border-orange-200 font-bold shadow-2xs flex items-center gap-2">
          <Clock :size="14" class="text-orange-600" />
          <span>{{ queueTasks.length }} Grid Menunggu QC</span>
        </span>
        <button
          @click="loadTasks"
          class="bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-bold px-3.5 py-2 rounded-xl transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
        >
          <RotateCw :size="13" :class="loadingTasks ? 'animate-spin' : ''" />
          <span>Segarkan</span>
        </button>
      </div>
    </div>

    <!-- Informational Banner for Non-Reviewer -->
    <div v-if="!authStore.isReviewer" class="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 flex items-center justify-between gap-3 shadow-2xs">
      <div class="flex items-center gap-2">
        <Info :size="16" class="text-amber-700 shrink-0" />
        <span><b>Mode Pantau Kontributor:</b> Anda dapat melihat visualisasi peta dan status antrean QC. Hak persetujuan (Approve) dan permintaan revisi hanya dimiliki oleh Tim Supervisi / Administrator.</span>
      </div>
    </div>

    <!-- Main Grid: Queue on Left, Live Map & QC Studio on Right -->
    <div class="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
      
      <!-- LEFT COLUMN: Task Queue (4 cols) -->
      <div class="xl:col-span-4 bg-white border border-slate-200 rounded-3xl p-4 sm:p-5 shadow-sm flex flex-col gap-3">
        <!-- Filter Tabs -->
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <span class="text-xs font-extrabold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
            <ClipboardList :size="14" class="text-slate-500" />
            <span>Antrean Tugas</span>
          </span>
          <span class="text-[11px] font-mono text-slate-400 font-bold">Total: {{ queueTasks.length }}</span>
        </div>

        <!-- Status Filter Pills -->
        <div class="grid grid-cols-3 gap-1 bg-slate-100 p-1 rounded-xl text-center text-xs font-bold">
          <button
            @click="statusFilter = 'SUBMITTED'"
            class="py-1 rounded-lg transition-all cursor-pointer"
            :class="statusFilter === 'SUBMITTED' ? 'bg-white text-orange-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            Review ({{ countByStatus('SUBMITTED') }})
          </button>
          <button
            @click="statusFilter = 'REVISION_NEEDED'"
            class="py-1 rounded-lg transition-all cursor-pointer"
            :class="statusFilter === 'REVISION_NEEDED' ? 'bg-white text-rose-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            Revisi ({{ countByStatus('REVISION_NEEDED') }})
          </button>
          <button
            @click="statusFilter = 'APPROVED'"
            class="py-1 rounded-lg transition-all cursor-pointer"
            :class="statusFilter === 'APPROVED' ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            Approved ({{ countByStatus('APPROVED') }})
          </button>
        </div>

        <!-- Task List Items -->
        <div v-if="filteredTasks.length === 0" class="text-center py-12 text-slate-400 text-xs">
          Tidak ada tugas pada filter status ini.
        </div>

        <div class="space-y-2 overflow-y-auto max-h-[640px] pr-1">
          <div
            v-for="task in filteredTasks"
            :key="task.id"
            @click="selectTask(task)"
            class="p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-col gap-2 shadow-2xs"
            :class="selectedTask?.id === task.id
              ? 'bg-rose-50/90 border-rose-400 shadow-xs ring-2 ring-rose-400/40'
              : 'bg-slate-50/70 border-slate-200 hover:border-slate-300 hover:bg-white'"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <span class="font-mono text-xs font-black text-slate-900">{{ task.grid_code }}</span>
                <span class="text-[10px] font-mono text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200 font-bold">
                  {{ task.year }}
                </span>
              </div>
              <span
                class="text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-2xs"
                :class="getStatusBadgeClass(task.status)"
              >
                {{ formatStatus(task.status) }}
              </span>
            </div>

            <div class="text-xs font-bold text-slate-800 truncate">{{ task.study_area_name }}</div>

            <div class="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-200/60">
              <span class="flex items-center gap-1.5 truncate max-w-[160px]">
                <User :size="12" class="text-slate-400 shrink-0" />
                <b class="text-slate-800 font-semibold truncate">{{ task.assigned_user_name || 'Tanpa Nama' }}</b>
              </span>
              <span class="font-mono text-purple-700 font-bold bg-purple-50 px-2 py-0.5 rounded-lg border border-purple-200 flex items-center gap-1 shrink-0 text-[10px]">
                <Shapes :size="11" /> {{ task.annotation_count || 0 }} Poligon
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: Embedded Live Map & Review Inspector (8 cols) -->
      <div class="xl:col-span-8 bg-white border border-slate-200 rounded-3xl p-5 sm:p-6 shadow-sm flex flex-col gap-4">
        
        <div v-if="!selectedTask" class="text-center py-28 text-slate-400 text-xs flex flex-col items-center gap-3">
          <div class="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center text-slate-300">
            <FileSearch :size="32" />
          </div>
          <div>
            <div class="font-bold text-slate-700 text-sm">Pilih Grid untuk Memulai Review</div>
            <p class="text-slate-400 text-xs mt-0.5">Pilih salah satu grid task dari antrean di sebelah kiri untuk melihat peta interaktif.</p>
          </div>
        </div>

        <div v-else class="space-y-4">
          
          <!-- Inspection Task Top Bar -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3.5 border-b border-slate-100 gap-3">
            <div>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-mono text-lg font-black text-slate-900">{{ selectedTask.grid_code }}</span>
                <span class="text-xs bg-rose-50 text-rose-700 px-2.5 py-0.5 rounded-lg border border-rose-200 font-bold font-mono">
                  Tahun {{ selectedTask.year }}
                </span>
                <span
                  class="text-[11px] font-bold px-2.5 py-0.5 rounded-full border shadow-2xs"
                  :class="getStatusBadgeClass(selectedTask.status)"
                >
                  {{ formatStatus(selectedTask.status) }}
                </span>
              </div>
              <div class="text-xs text-slate-500 mt-1">
                Wilayah: <b class="text-slate-800">{{ selectedTask.study_area_name }}</b> • Kontributor: <b class="text-slate-800">{{ selectedTask.assigned_user_name }}</b>
              </div>
            </div>

            <!-- Quick Action: Open in Full Digitizer Studio -->
            <router-link
              :to="{ path: '/map', query: { taskId: selectedTask.id } }"
              class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-2 shadow-xs cursor-pointer shrink-0"
              title="Buka grid ini di Studio Digitasi Lengkap untuk mengedit poligon"
            >
              <ExternalLink :size="14" />
              <span>Buka di Studio Lengkap</span>
            </router-link>
          </div>

          <!-- 🛰️ EMBEDDED LIVE QC MAP VIEWER -->
          <div class="relative w-full rounded-2xl overflow-hidden border border-slate-300 shadow-inner bg-slate-900">
            <!-- Floating Map Layer & Opacity Controls on Top Bar -->
            <div class="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 bg-white/95 backdrop-blur-md p-2 rounded-2xl shadow-lg border border-slate-200/80 text-xs">
              
              <!-- Basemap Selector -->
              <div class="flex items-center gap-1.5 overflow-x-auto max-w-full py-0.5">
                <button
                  v-for="layer in layerOptions"
                  :key="layer.id"
                  @click="setQCLayer(layer.id)"
                  class="px-2.5 py-1 rounded-xl text-[11px] font-bold transition-all flex items-center gap-1.5 cursor-pointer shrink-0 border"
                  :class="qcLayer === layer.id
                    ? 'bg-rose-600 text-white border-rose-600 shadow-xs'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'"
                >
                  <component :is="layer.icon" :size="12" />
                  <span>{{ layer.name }}</span>
                </button>
              </div>

              <!-- Opacity Slider & Topology Button -->
              <div class="flex items-center gap-3 shrink-0">
                <div class="flex items-center gap-1.5 text-[11px] text-slate-600 font-bold">
                  <span>Opasitas:</span>
                  <input
                    type="range"
                    min="0.1"
                    max="0.95"
                    step="0.05"
                    v-model="qcOpacity"
                    @input="updateQCOpacity"
                    class="w-16 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-600"
                  />
                  <span class="font-mono text-rose-600 w-8 text-right">{{ Math.round(qcOpacity * 100) }}%</span>
                </div>

                <button
                  @click="runQCTopologyCheck"
                  :disabled="checkingTopology"
                  class="px-3 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-xl text-[11px] font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
                  title="Jalankan validasi topologi geometri"
                >
                  <RotateCw v-if="checkingTopology" :size="12" class="animate-spin text-purple-600" />
                  <ShieldCheck v-else :size="12" class="text-purple-600" />
                  <span>Cek Topologi</span>
                </button>
              </div>
            </div>

            <!-- Leaflet Map Container -->
            <div id="qc-map-container" class="w-full h-[400px] z-0"></div>

            <!-- Active Feature Info Pill on Map Bottom -->
            <div
              v-if="hoveredFeature"
              class="absolute bottom-3 left-3 z-10 bg-slate-900/90 backdrop-blur-md text-white px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 border border-slate-700 shadow-lg animate-in fade-in"
            >
              <div class="w-3 h-3 rounded-sm" :style="{ backgroundColor: hoveredFeature.color }"></div>
              <span>{{ hoveredFeature.class_name }} (~{{ hoveredFeature.areaHa }} Ha)</span>
            </div>
          </div>

          <!-- Topology Result Banner (if checked) -->
          <div
            v-if="qcTopologyResult && !qcTopologyResult.valid"
            class="bg-rose-50 border border-rose-200 p-3 rounded-2xl text-xs text-rose-900 space-y-1 shadow-2xs"
          >
            <div class="flex items-center justify-between font-bold text-rose-800">
              <span class="flex items-center gap-1.5">
                <AlertTriangle :size="14" class="text-rose-600" />
                <span>Masalah Topologi Terdeteksi ({{ qcTopologyResult.errors.length }} Masalah):</span>
              </span>
              <button @click="qcTopologyResult = null" class="text-rose-400 hover:text-rose-600 cursor-pointer"><X :size="14" /></button>
            </div>
            <ul class="ml-5 space-y-0.5 text-[11px] list-disc text-rose-700">
              <li v-for="(err, idx) in qcTopologyResult.errors.slice(0, 4)" :key="idx">
                <span class="font-mono text-rose-600 font-bold">[{{ err.type }}]</span> {{ err.message }}
              </li>
            </ul>
          </div>

          <div
            v-if="qcTopologyResult && qcTopologyResult.valid"
            class="bg-emerald-50 border border-emerald-200 p-3 rounded-2xl text-xs text-emerald-900 flex items-center justify-between shadow-2xs"
          >
            <div class="flex items-center gap-2 font-bold text-emerald-800">
              <CheckCircle2 :size="15" class="text-emerald-600" />
              <span>Topologi Sempurna! Cakupan 100% tanpa tumpang tindih maupun celah kosong.</span>
            </div>
            <button @click="qcTopologyResult = null" class="text-emerald-400 hover:text-emerald-600 cursor-pointer"><X :size="14" /></button>
          </div>

          <!-- Bottom Split: Polygon List & Review Action Panel -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 pt-1">
            
            <!-- Polygon Breakdown (5 cols) -->
            <div class="lg:col-span-5 bg-slate-50/70 border border-slate-200 p-3.5 rounded-2xl space-y-2">
              <div class="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center justify-between">
                <span>Daftar Poligon ({{ taskFeatures.length }})</span>
                <span class="text-purple-700 font-mono text-[11px] font-bold">Total: ~{{ totalAreaHa }} Ha</span>
              </div>

              <div class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                <div
                  v-for="(poly, idx) in taskFeatures"
                  :key="idx"
                  class="p-2 bg-white border border-slate-200 rounded-xl flex items-center justify-between text-xs transition-all hover:border-indigo-300"
                >
                  <div class="flex items-center gap-2">
                    <div
                      class="w-3 h-3 rounded-sm border border-slate-300 shrink-0 shadow-2xs"
                      :style="{ backgroundColor: getClassColor(poly.properties?.class_id) }"
                    ></div>
                    <span class="font-bold text-slate-800 truncate text-[11px]">{{ poly.properties?.class_name || 'Belum Terklasifikasi' }}</span>
                  </div>
                  <span class="text-[10px] text-slate-500 font-mono bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200 shrink-0">
                    {{ Math.round((poly.properties?.area_sqm || 10000) / 10000) }} Ha
                  </span>
                </div>
              </div>
            </div>

            <!-- Review Actions & Decision Form (7 cols) -->
            <div class="lg:col-span-7 space-y-3">
              <!-- Quick Feedback Template Buttons -->
              <div v-if="authStore.isReviewer" class="space-y-1">
                <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Zap :size="12" class="text-amber-500 fill-amber-500" />
                  <span>Template Catatan Reviewer:</span>
                </div>
                <div class="flex flex-wrap gap-1">
                  <button
                    @click="reviewerNotes = 'Anotasi telah divalidasi, batas poligon rapi dan kelas sesuai citra Sentinel-2.'"
                    class="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded-lg border border-slate-200 font-medium transition-colors cursor-pointer"
                  >
                    Poligon Rapi & Sesuai
                  </button>
                  <button
                    @click="reviewerNotes = 'Batas antara Hutan Lahan Kering dan Perkebunan Sawit masih kurang presisi, harap disempurnakan.'"
                    class="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded-lg border border-slate-200 font-medium transition-colors cursor-pointer"
                  >
                    Batas Hutan & Sawit Kurang Presisi
                  </button>
                  <button
                    @click="reviewerNotes = 'Area permukiman dan tubuh air belum terdigitasi lengkap pada sisi barat grid.'"
                    class="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded-lg border border-slate-200 font-medium transition-colors cursor-pointer"
                  >
                    Lengkapi Permukiman & Air
                  </button>
                </div>
              </div>

              <!-- Notes Textarea -->
              <div class="space-y-1">
                <label class="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                  Catatan Evaluasi Reviewer:
                </label>
                <textarea
                  v-model="reviewerNotes"
                  rows="2"
                  placeholder="Tuliskan catatan evaluasi atau instruksi perbaikan..."
                  :disabled="!authStore.isReviewer"
                  class="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-500 focus:bg-white shadow-2xs font-sans"
                ></textarea>
              </div>

              <!-- Approval / Rejection Action Buttons -->
              <div class="flex items-center justify-end gap-2.5 pt-1">
                <button
                  @click="rejectWithNotes"
                  :disabled="loadingAction || !authStore.isReviewer"
                  class="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-1.5 disabled:opacity-50 shadow-2xs cursor-pointer"
                >
                  <RotateCcw :size="13" />
                  <span>Minta Revisi Grid</span>
                </button>

                <button
                  @click="approveTask"
                  :disabled="loadingAction || !authStore.isReviewer"
                  class="bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-bold px-5 py-2 rounded-xl shadow-md shadow-emerald-600/20 transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                >
                  <CheckCircle2 :size="14" />
                  <span>Setujui (Approve)</span>
                </button>
              </div>
            </div>

          </div>

        </div>

      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import L from 'leaflet'
import {
  ShieldCheck,
  Eye,
  Clock,
  Info,
  ClipboardList,
  RotateCw,
  User,
  Shapes,
  FileSearch,
  Zap,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  X,
  ExternalLink,
  Satellite,
  Flame,
  Sprout,
  TrendingUp,
  Globe2,
  Globe
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import { useAnnotationsStore } from '../stores/annotations'
import api from '../services/api'

const authStore = useAuthStore()
const tasksStore = useTasksStore()
const annotationsStore = useAnnotationsStore()

const selectedTask = ref(null)
const taskFeatures = ref([])
const reviewerNotes = ref('')
const loadingAction = ref(false)
const loadingTasks = ref(false)
const statusFilter = ref('SUBMITTED') // 'SUBMITTED' | 'REVISION_NEEDED' | 'APPROVED'

// Live Map Variables
let qcMap = null
let qcTileLayer = null
let qcFeatureGroup = null
let qcGridBoundingLayer = null

const qcLayer = ref('local_s2_rgb')
const qcOpacity = ref(0.65)
const hoveredFeature = ref(null)
const qcTopologyResult = ref(null)
const checkingTopology = ref(false)

const layerOptions = [
  { id: 'local_s2_rgb', name: 'Sentinel-2 Lokal (RGB)', icon: Satellite },
  { id: 'local_s2_cir', name: 'Sentinel-2 Lokal (NIR)', icon: Flame },
  { id: 'google_sat', name: 'Google Sat', icon: Globe2 },
  { id: 'esri_sat', name: 'Esri Sat', icon: Globe },
  { id: 'false_color_nir', name: 'False NIR', icon: Flame },
  { id: 'swir', name: 'SWIR', icon: Sprout },
  { id: 'ndvi', name: 'NDVI', icon: TrendingUp }
]

const getTileUrl = (layerType, year) => {
  const googleSat = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
  const esriSatellite = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

  switch (layerType) {
    case 'google_sat':
      return { url: googleSat, maxNativeZoom: 20, filter: 'none', attr: 'Google Satellite Ultra-HD' }
    case 'esri_sat':
      return { url: esriSatellite, maxNativeZoom: 19, filter: 'none', attr: 'Esri World Imagery' }
    case 'true_color':
      return { url: googleSat, maxNativeZoom: 20, filter: 'none', attr: `Citra Satelit Resolusi Tinggi (${year})` }
    case 'false_color_nir':
      return { url: esriSatellite, maxNativeZoom: 19, filter: 'hue-rotate(290deg) saturate(320%) contrast(125%) brightness(105%)', attr: `NIR (${year})` }
    case 'swir':
      return { url: esriSatellite, maxNativeZoom: 19, filter: 'hue-rotate(65deg) saturate(240%) contrast(135%) brightness(110%)', attr: `SWIR (${year})` }
    case 'ndvi':
      return { url: esriSatellite, maxNativeZoom: 19, filter: 'invert(15%) hue-rotate(95deg) saturate(350%) contrast(140%) brightness(105%)', attr: `NDVI (${year})` }
    default:
      return { url: googleSat, maxNativeZoom: 20, filter: 'none', attr: 'Google Satellite' }
  }
}

const queueTasks = computed(() => {
  return tasksStore.tasks.filter(t => t.status === 'SUBMITTED' || t.status === 'REVISION_NEEDED' || t.status === 'APPROVED')
})

const filteredTasks = computed(() => {
  return queueTasks.value.filter(t => t.status === statusFilter.value)
})

const countByStatus = (status) => {
  return queueTasks.value.filter(t => t.status === status).length
}

const totalAreaHa = computed(() => {
  const totalSqm = taskFeatures.value.reduce((acc, curr) => acc + (curr.properties?.area_sqm || 0), 0)
  return Math.round(totalSqm / 10000)
})

onMounted(async () => {
  await annotationsStore.fetchClasses()
  await loadTasks()
})

onUnmounted(() => {
  if (qcMap) {
    qcMap.remove()
    qcMap = null
  }
})

const loadTasks = async () => {
  loadingTasks.value = true
  try {
    await tasksStore.fetchTasks()
    if (filteredTasks.value.length > 0 && !selectedTask.value) {
      await selectTask(filteredTasks.value[0])
    }
  } finally {
    loadingTasks.value = false
  }
}

const selectTask = async (task) => {
  selectedTask.value = task
  reviewerNotes.value = task.reviewer_notes || ''
  qcTopologyResult.value = null
  hoveredFeature.value = null

  const features = await annotationsStore.fetchGridAnnotations(task.id)
  taskFeatures.value = features

  await nextTick()
  initOrUpdateQCMap(task, features)
}

const initOrUpdateQCMap = (task, features) => {
  if (!qcMap) {
    const container = document.getElementById('qc-map-container')
    if (!container) return

    qcMap = L.map('qc-map-container', {
      center: [-0.947, 100.370],
      zoom: 13,
      zoomControl: false
    })

    L.control.zoom({ position: 'bottomright' }).addTo(qcMap)
    L.control.scale({
      position: 'bottomleft',
      metric: true,
      imperial: false,
      maxWidth: 150
    }).addTo(qcMap)
    qcFeatureGroup = L.featureGroup().addTo(qcMap)
  }

  updateQCTileLayer(task.year || 2025)

  // Draw Grid Bounding Box
  if (qcGridBoundingLayer) qcMap.removeLayer(qcGridBoundingLayer)
  const bounds = [[task.min_lat, task.min_lon], [task.max_lat, task.max_lon]]
  qcGridBoundingLayer = L.rectangle(bounds, {
    color: '#ffffff',
    weight: 2.5,
    dashArray: '5, 5',
    fillOpacity: 0.0,
    interactive: false
  }).addTo(qcMap)

  // Render Polygons
  qcFeatureGroup.clearLayers()
  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  features.forEach(feat => {
    const cls = classesMap[feat.properties?.class_id]
    const color = cls?.color || '#9CA3AF'
    const areaHa = Math.round((feat.properties?.area_sqm || 10000) / 10000)

    const layer = L.geoJSON(feat, {
      style: () => ({
        color: '#ffffff',
        weight: 1.5,
        fillColor: color,
        fillOpacity: qcOpacity.value
      })
    })

    layer.eachLayer(l => {
      l.on('mouseover', () => {
        hoveredFeature.value = {
          class_name: cls?.name || feat.properties?.class_name || 'Belum Terklasifikasi',
          color: color,
          areaHa: areaHa
        }
        l.setStyle({ weight: 3, color: '#facc15', fillOpacity: 0.85 })
      })

      l.on('mouseout', () => {
        l.setStyle({ weight: 1.5, color: '#ffffff', fillOpacity: qcOpacity.value })
      })

      l.bindTooltip(`<b>${cls?.name || feat.properties?.class_name}</b><br>~${areaHa} Ha`, {
        sticky: true,
        className: 'text-xs'
      })

      qcFeatureGroup.addLayer(l)
    })
  })

  qcMap.fitBounds(bounds, { padding: [30, 30] })
}

const updateQCTileLayer = (year = 2025) => {
  if (!qcMap) return
  if (qcTileLayer) qcMap.removeLayer(qcTileLayer)

  if (qcLayer.value === 'local_s2_rgb' || qcLayer.value === 'local_s2_cir') {
    const mode = qcLayer.value === 'local_s2_cir' ? 'cir' : 'rgb'
    const gridCode = selectedTask.value?.grid_code
    const tileUrl = gridCode
      ? api.getGridRasterTileUrl(year, gridCode, mode)
      : api.getMosaicRasterTileUrl(year, mode)

    qcTileLayer = L.tileLayer(tileUrl, {
      maxZoom: 20,
      maxNativeZoom: 16,
      attribution: `Citra Sentinel-2 Sumbar (${year}) 10m COG`
    }).addTo(qcMap)
    qcTileLayer.bringToBack()
    return
  }

  const conf = getTileUrl(qcLayer.value, year)
  qcTileLayer = L.tileLayer(conf.url, {
    maxZoom: 20,
    maxNativeZoom: conf.maxNativeZoom,
    attribution: conf.attr
  }).addTo(qcMap)

  if (qcTileLayer.getContainer()) {
    qcTileLayer.getContainer().style.filter = conf.filter
  }

  qcTileLayer.bringToBack()
}

const setQCLayer = (layerId) => {
  qcLayer.value = layerId
  updateQCTileLayer(selectedTask.value?.year || 2025)
}

const updateQCOpacity = () => {
  if (!qcFeatureGroup) return
  qcFeatureGroup.eachLayer(l => {
    l.setStyle({ fillOpacity: qcOpacity.value })
  })
}

const runQCTopologyCheck = async () => {
  if (!selectedTask.value) return
  checkingTopology.value = true
  try {
    const res = await api.validateTopology(selectedTask.value.id)
    qcTopologyResult.value = res.data
  } catch (err) {
    alert('Gagal menjalankan validasi topologi.')
  } finally {
    checkingTopology.value = false
  }
}

const getClassColor = (classId) => {
  const cls = annotationsStore.classes.find(c => c.id === classId)
  return cls?.color || '#9CA3AF'
}

const formatStatus = (status) => {
  switch (status) {
    case 'SUBMITTED': return 'Review QC'
    case 'APPROVED': return 'Approved'
    case 'REVISION_NEEDED': return 'Perlu Revisi'
    default: return status || 'Tersedia'
  }
}

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'APPROVED': return 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold'
    case 'SUBMITTED': return 'bg-orange-100 text-orange-800 border-orange-300 font-bold'
    case 'REVISION_NEEDED': return 'bg-rose-100 text-rose-800 border-rose-300 font-bold'
    default: return 'bg-slate-100 text-slate-600 border-slate-300'
  }
}

const approveTask = async () => {
  if (!selectedTask.value) return
  loadingAction.value = true
  try {
    const ok = await tasksStore.updateStatus(
      selectedTask.value.id,
      'APPROVED',
      reviewerNotes.value || 'Anotasi telah divalidasi dan disetujui untuk dataset U-Net.'
    )
    if (ok) {
      alert('Grid berhasil disetujui (APPROVED) dan siap untuk pipeline U-Net!')
      selectedTask.value = null
      await loadTasks()
    }
  } finally {
    loadingAction.value = false
  }
}

const rejectWithNotes = async () => {
  if (!selectedTask.value) return
  if (!reviewerNotes.value.trim()) {
    alert('Harap berikan catatan evaluasi/revisi agar kontributor mengetahui bagian mana yang perlu diperbaiki.')
    return
  }
  loadingAction.value = true
  try {
    const ok = await tasksStore.updateStatus(
      selectedTask.value.id,
      'REVISION_NEEDED',
      reviewerNotes.value
    )
    if (ok) {
      alert('Status tugas diubah menjadi REVISION_NEEDED dan catatan telah dikirim ke kontributor!')
      selectedTask.value = null
      await loadTasks()
    }
  } finally {
    loadingAction.value = false
  }
}
</script>

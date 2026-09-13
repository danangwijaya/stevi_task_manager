<template>
  <div class="h-[calc(100vh-57px)] w-full flex flex-col md:flex-row bg-slate-100 relative overflow-hidden font-sans">
    <!-- Left Sidebar: HOT OSM Tasking Manager Controls & Grid Inspector -->
    <div class="w-full md:w-[420px] bg-white border-r border-slate-200 flex flex-col z-20 shadow-lg overflow-y-auto shrink-0">
      
      <!-- Project / AOI Header -->
      <div class="p-4 border-b border-slate-200 space-y-3 bg-slate-50/70">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl bg-rose-100 text-rose-600 border border-rose-200 flex items-center justify-center font-bold text-sm shadow-sm">
              <Grid :size="16" />
            </div>
            <div>
              <h2 class="text-sm font-extrabold text-slate-900 tracking-tight">Tasking Manager Grid</h2>
              <p class="text-[11px] text-slate-500">Pilih patch 1024px (~10.24km) untuk digitasi data training</p>
            </div>
          </div>
          <span class="text-[10px] bg-rose-50 text-rose-700 font-bold px-2 py-0.5 rounded-full border border-rose-200 uppercase tracking-wider">
            HOT-OSM
          </span>
        </div>

        <!-- Dynamic Area of Interest (AOI) Switcher -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Proyek Wilayah Kajian (AOI):</label>
            <span v-if="tasksStore.projects.length" class="text-[10px] font-mono text-slate-400">
              {{ tasksStore.projects.length }} Proyek
            </span>
          </div>

          <div class="relative">
            <select
              v-model="activeAreaId"
              @change="onProjectSelectChange"
              class="w-full px-3 py-2 text-xs font-bold text-[#1f242e] bg-white border border-slate-300 rounded-xl focus:outline-none focus:border-rose-600 shadow-2xs appearance-none pr-8 cursor-pointer"
            >
              <option v-for="proj in tasksStore.projects" :key="proj.id" :value="proj.id">
                📍 {{ proj.name }} ({{ proj.total_tasks }} grid)
              </option>
            </select>
            <ChevronDown :size="12" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        </div>

        <!-- Search Bar Grid Code -->
        <div class="space-y-1">
          <div class="relative">
            <input
              v-model="searchQuery"
              @keyup.enter="searchAndFlyToGrid"
              type="text"
              placeholder="Cari kode grid (cth: SB_015, KL_040)..."
              class="w-full pl-8 pr-20 py-2 text-xs text-[#1f242e] bg-white border border-slate-300 rounded-xl focus:outline-none focus:border-rose-600 placeholder-slate-400 shadow-2xs"
            />
            <Search :size="13" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <button
              @click="searchAndFlyToGrid"
              class="absolute right-1 top-1/2 -translate-y-1/2 px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-[10px] font-bold transition-colors cursor-pointer"
            >
              Cari
            </button>
          </div>
          <div v-if="searchFeedback" class="text-[10px] font-medium text-rose-600 px-1">
            {{ searchFeedback }}
          </div>
        </div>

        <!-- Filter Pills Bar -->
        <div class="flex items-center gap-1.5 overflow-x-auto pb-0.5 pt-1">
          <button
            v-for="flt in filterPills"
            :key="flt.id"
            @click="activeStatusFilter = flt.id; renderGridTilesOnMap()"
            class="px-2.5 py-1 rounded-lg text-[10px] font-bold whitespace-nowrap transition-all border flex items-center gap-1 cursor-pointer"
            :class="activeStatusFilter === flt.id
              ? 'bg-rose-600 text-white border-rose-600 shadow-xs'
              : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50'"
          >
            <component :is="flt.icon" :size="10" />
            <span>{{ flt.label }}</span>
          </button>
        </div>

        <!-- Year Toggle & Random Button -->
        <div class="flex items-center justify-between pt-1 gap-2">
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Tahun:</span>
            <div class="flex items-center bg-white p-0.5 rounded-lg border border-slate-200 shadow-sm">
              <button
                @click="switchYear(null)"
                class="px-2 py-0.5 text-[10px] font-bold rounded-md transition-colors cursor-pointer"
                :class="selectedYear === null ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
              >
                Semua
              </button>
              <button
                @click="switchYear(2017)"
                class="px-2 py-0.5 text-[10px] font-bold rounded-md transition-colors cursor-pointer"
                :class="selectedYear === 2017 ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
              >
                2017
              </button>
              <button
                @click="switchYear(2021)"
                class="px-2 py-0.5 text-[10px] font-bold rounded-md transition-colors cursor-pointer"
                :class="selectedYear === 2021 ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
              >
                2021
              </button>
              <button
                @click="switchYear(2025)"
                class="px-2 py-0.5 text-[10px] font-bold rounded-md transition-colors cursor-pointer"
                :class="selectedYear === 2025 ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
              >
                2025
              </button>
            </div>
          </div>

          <!-- Iconic HOT OSM "Map a Random Task" Button -->
          <button
            @click="pickRandomTask"
            class="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
            title="Pilihkan satu grid acak yang belum dikerjakan"
          >
            <Dice5 :size="14" class="text-amber-600" />
            <span>Grid Acak</span>
          </button>
        </div>
      </div>

      <!-- HOT OSM Overall Progress Bar & Breakdown -->
      <div class="p-4 border-b border-slate-200 space-y-2.5 bg-white">
        <div class="flex justify-between text-xs font-bold text-slate-800">
          <span class="flex items-center gap-2">
            <TrendingUp :size="14" class="text-slate-500" />
            <span>Progres Pemetaan Area</span>
          </span>
          <span class="text-emerald-600 font-mono font-extrabold">{{ progressPercent }}% Selesai</span>
        </div>

        <!-- Multi-colored segment progress bar ala HOT OSM -->
        <div class="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex shadow-inner border border-slate-200">
          <div :style="{ width: `${approvedPercent}%` }" class="bg-emerald-500 transition-all" title="Approved (Disetujui)"></div>
          <div :style="{ width: `${submittedPercent}%` }" class="bg-orange-500 transition-all" title="Submitted (Menunggu Review)"></div>
          <div :style="{ width: `${inProgressPercent}%` }" class="bg-amber-400 transition-all" title="In Progress (Dikerjakan)"></div>
          <div :style="{ width: `${revisionPercent}%` }" class="bg-rose-500 transition-all" title="Needs Revision (Perlu Revisi)"></div>
        </div>

        <!-- Progress stats breakdown cards -->
        <div class="grid grid-cols-4 gap-1.5 text-[10px] text-center pt-1">
          <div class="bg-slate-50 p-2 rounded-xl border border-slate-200">
            <div class="text-slate-500 font-medium">Tersedia</div>
            <div class="font-extrabold text-slate-800 text-xs mt-0.5">{{ unassignedCount }}</div>
          </div>
          <div class="bg-amber-50/70 p-2 rounded-xl border border-amber-200">
            <div class="text-amber-700 font-medium">Dikerjakan</div>
            <div class="font-extrabold text-amber-800 text-xs mt-0.5">{{ inProgressCount }}</div>
          </div>
          <div class="bg-orange-50/70 p-2 rounded-xl border border-orange-200">
            <div class="text-orange-700 font-medium">Review</div>
            <div class="font-extrabold text-orange-800 text-xs mt-0.5">{{ submittedCount }}</div>
          </div>
          <div class="bg-emerald-50/70 p-2 rounded-xl border border-emerald-200">
            <div class="text-emerald-700 font-medium">Approved</div>
            <div class="font-extrabold text-emerald-800 text-xs mt-0.5">{{ approvedCount }}</div>
          </div>
        </div>
      </div>

      <!-- Selected Grid Tile Inspector Panel -->
      <div class="flex-1 p-4 space-y-4">
        <div v-if="!selectedTask" class="text-center py-12 text-slate-400 text-xs flex flex-col items-center gap-2.5">
          <div class="w-12 h-12 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 shadow-xs">
            <Grid :size="24" />
          </div>
          <span class="font-medium max-w-[240px] text-slate-600">
            Ketik kode grid di pencarian atau klik salah satu kotak pada peta untuk mulai digitasi!
          </span>
        </div>

        <div v-else class="space-y-3.5">
          <!-- Grid Detail Card -->
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2.5 shadow-xs">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="font-mono text-sm font-extrabold text-slate-900">{{ selectedTask.grid_code }}</span>
                <span class="text-[10px] text-slate-500 font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
                  Thn {{ selectedTask.year }}
                </span>
              </div>
              <span
                class="text-[10px] font-bold px-2.5 py-0.5 rounded-full border shadow-xs"
                :class="getStatusBadgeClass(selectedTask.status)"
              >
                {{ formatStatus(selectedTask.status) }}
              </span>
            </div>

            <div class="text-xs text-slate-700 font-bold">{{ selectedTask.study_area_name }}</div>
            
            <div class="text-[11px] text-slate-600 space-y-1.5 pt-2 border-t border-slate-200">
              <div class="flex justify-between items-center">
                <span class="text-slate-500">Penanggung Jawab:</span>
                <b class="text-slate-800 font-semibold bg-white px-2 py-0.5 rounded border border-slate-200">
                  {{ selectedTask.assigned_user_name || 'Belum Diambil (Tersedia)' }}
                </b>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-slate-500">Jumlah Poligon:</span>
                <b class="text-purple-700 font-mono font-bold bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                  {{ selectedTask.annotation_count }} Poligon
                </b>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-slate-500">Ukuran Patch:</span>
                <span class="text-slate-600 font-mono">10.24km × 10.24km (1024px)</span>
              </div>
            </div>

            <!-- Notes if any -->
            <div v-if="selectedTask.reviewer_notes" class="text-[11px] text-amber-900 bg-amber-50 border border-amber-200 p-2.5 rounded-xl mt-2 space-y-0.5">
              <div class="font-bold flex items-center gap-1.5 text-amber-800">
                <MessageSquare :size="12" />
                <span>Catatan Reviewer QC:</span>
              </div>
              <p class="italic text-amber-900/90">"{{ selectedTask.reviewer_notes }}"</p>
            </div>
          </div>

          <!-- HOT OSM Action Buttons (Strict Grid Locking) -->
          <div class="space-y-2 pt-1">
            <!-- If task is UNASSIGNED → allow claim -->
            <button
              v-if="selectedTask.status === 'UNASSIGNED'"
              @click="claimSelectedTask"
              :disabled="actionLoading"
              class="w-full bg-gradient-to-r from-rose-600 to-red-500 hover:from-rose-500 hover:to-red-400 text-white text-xs font-bold py-2.5 px-4 rounded-xl shadow-md shadow-rose-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <Rocket :size="14" />
              <span>Ambil & Kerjakan Grid Ini</span>
            </button>

            <!-- If grid is locked (not UNASSIGNED) and not mine → show locked info -->
            <div
              v-if="selectedTask.status !== 'UNASSIGNED' && selectedTask.assigned_user_id && selectedTask.assigned_user_id !== authStore.user?.id && !authStore.isAdmin"
              class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800 flex items-center gap-2"
            >
              <Lock :size="14" class="text-amber-600 shrink-0" />
              <span>Grid ini sedang dikerjakan oleh <b>{{ selectedTask.assigned_user_name }}</b>. Pilih grid lain yang berstatus "Tersedia".</span>
            </div>

            <!-- Direct Jump to Map Studio (only for assignee or admin) -->
            <button
              v-if="selectedTask.assigned_user_id === authStore.user?.id || authStore.isAdmin"
              @click="openInStudio"
              class="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold py-2.5 px-4 rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <Shapes :size="14" />
              <span>Buka di Studio Digitasi</span>
            </button>

            <!-- If task is submitted and user is Admin, quick link to QC -->
            <button
              v-if="authStore.isAdmin && (selectedTask.status === 'SUBMITTED' || selectedTask.status === 'REVISION_NEEDED')"
              @click="router.push('/qc')"
              class="w-full bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 text-xs font-bold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <ClipboardCheck :size="14" />
              <span>Periksa & Review di Menu QC</span>
            </button>

            <!-- Release/Unclaim button — ADMIN ONLY -->
            <button
              v-if="authStore.isAdmin && selectedTask.assigned_user_id"
              @click="unclaimSelectedTask"
              :disabled="actionLoading"
              class="w-full bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold py-2 px-3 rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <LockOpen :size="14" />
              <span>Lepas Grid ke Antrean Umum (Admin)</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Full-Screen Interactive HOT OSM Grid Map -->
    <div class="flex-1 relative w-full h-full">
      <div id="hot-map-container" class="w-full h-full z-0"></div>

      <!-- HOT OSM Floating Status Legend (Light Mode) -->
      <div class="absolute bottom-6 right-6 z-10 bg-white/95 border border-slate-200 p-3.5 rounded-2xl shadow-xl backdrop-blur-md space-y-2 min-w-[210px]">
        <div class="text-[11px] font-extrabold text-slate-700 uppercase tracking-wider pb-1.5 border-b border-slate-100 flex items-center justify-between">
          <span class="flex items-center gap-2">
            <Palette :size="14" class="text-slate-400" />
            <span>Status Grid HOT OSM</span>
          </span>
          <span class="text-[9px] text-slate-400 font-mono">HOT TM4</span>
        </div>
        <div class="space-y-1.5 text-xs font-medium">
          <div class="flex items-center gap-2.5">
            <div class="w-3.5 h-3.5 rounded-sm bg-slate-100 border border-slate-400 shadow-2xs"></div>
            <span class="text-slate-700">Tersedia (Ready)</span>
          </div>
          <div class="flex items-center gap-2.5">
            <div class="w-3.5 h-3.5 rounded-sm bg-amber-300 border border-amber-500 shadow-2xs"></div>
            <span class="text-slate-700">Sedang Dikerjakan</span>
          </div>
          <div class="flex items-center gap-2.5">
            <div class="w-3.5 h-3.5 rounded-sm bg-orange-400 border border-orange-600 shadow-2xs"></div>
            <span class="text-slate-700">Menunggu Review</span>
          </div>
          <div class="flex items-center gap-2.5">
            <div class="w-3.5 h-3.5 rounded-sm bg-emerald-400 border border-emerald-600 shadow-2xs"></div>
            <span class="text-slate-700">Disetujui (Approved)</span>
          </div>
          <div class="flex items-center gap-2.5">
            <div class="w-3.5 h-3.5 rounded-sm bg-rose-400 border border-rose-600 shadow-2xs"></div>
            <span class="text-slate-700">Perlu Revisi</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import {
  Grid,
  ChevronDown,
  Search,
  Dice5,
  TrendingUp,
  MessageSquare,
  Rocket,
  Shapes,
  ClipboardCheck,
  LockOpen,
  Lock,
  Palette,
  Layers,
  UserCheck,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Clock,
  ShieldCheck
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const tasksStore = useTasksStore()

const activeAreaId = ref(1)
const selectedYear = ref(2025)
const selectedTask = ref(null)
const actionLoading = ref(false)

// Search & Filter State
const searchQuery = ref('')
const searchFeedback = ref('')
const activeStatusFilter = ref('ALL')

const filterPills = [
  { id: 'ALL', label: 'Semua', icon: Layers },
  { id: 'MY_TASKS', label: 'Grid Saya', icon: UserCheck },
  { id: 'REVISION_NEEDED', label: 'Perlu Revisi', icon: AlertTriangle },
  { id: 'UNASSIGNED', label: 'Tersedia', icon: CheckCircle2 },
  { id: 'IN_PROGRESS', label: 'Dikerjakan', icon: Loader2 },
  { id: 'SUBMITTED', label: 'Review', icon: Clock },
  { id: 'APPROVED', label: 'Disetujui', icon: ShieldCheck },
]


let map = null
let gridLayerGroup = null

// Status Colors ala HOT OSM (Light & Clear for Satellite Basemap)
const HOT_OSM_COLORS = {
  UNASSIGNED: { stroke: '#94a3b8', fill: '#f8fafc', opacity: 0.2 },
  ASSIGNED: { stroke: '#f59e0b', fill: '#fde68a', opacity: 0.45 },
  IN_PROGRESS: { stroke: '#f59e0b', fill: '#fde68a', opacity: 0.45 },
  SUBMITTED: { stroke: '#ea580c', fill: '#fb923c', opacity: 0.55 },
  APPROVED: { stroke: '#10b981', fill: '#34d399', opacity: 0.65 },
  REVISION_NEEDED: { stroke: '#e11d48', fill: '#f87171', opacity: 0.55 }
}

const filteredTasks = computed(() => {
  let list = tasksStore.tasks
  if (selectedYear.value) {
    list = list.filter(t => t.year === selectedYear.value)
  }
  if (activeStatusFilter.value === 'MY_TASKS') {
    if (authStore.user) {
      list = list.filter(t => t.assigned_user_id === authStore.user.id)
    }
  } else if (activeStatusFilter.value !== 'ALL') {
    list = list.filter(t => t.status === activeStatusFilter.value)
  }
  return list
})

onMounted(async () => {
  await tasksStore.fetchProjects()
  if (tasksStore.projects.length > 0 && !tasksStore.projects.some(p => p.id === activeAreaId.value)) {
    activeAreaId.value = tasksStore.projects[0].id
  }
  await tasksStore.fetchStats()
  await loadTasksForArea()
  await nextTick()
  initMap()
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

const loadTasksForArea = async () => {
  tasksStore.selectedArea = activeAreaId.value
  tasksStore.selectedYear = selectedYear.value
  await tasksStore.fetchTasks()
  renderGridTilesOnMap()
}

const onProjectSelectChange = async () => {
  selectedTask.value = null
  const selectedProj = tasksStore.projects.find(p => p.id === activeAreaId.value)
  await loadTasksForArea()
  if (map && selectedProj) {
    map.flyTo([selectedProj.center_lat, selectedProj.center_lon], selectedProj.default_zoom || 8, { duration: 1.2 })
  }
}

const switchYear = async (yr) => {
  selectedYear.value = yr
  await loadTasksForArea()
}

const searchAndFlyToGrid = () => {
  searchFeedback.value = ''
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return

  const target = tasksStore.tasks.find(t => t.grid_code.toLowerCase().includes(q))
  if (target) {
    selectedTask.value = target
    highlightTaskOnMap(target)
    searchFeedback.value = `Ditemukan: ${target.grid_code}`
    setTimeout(() => searchFeedback.value = '', 4000)
  } else {
    searchFeedback.value = `Grid dengan kode "${searchQuery.value}" tidak ditemukan di area ini.`
    setTimeout(() => searchFeedback.value = '', 4000)
  }
}

const pickRandomTask = () => {
  const unassigned = tasksStore.tasks.filter(t => t.status === 'UNASSIGNED')
  let target = null
  if (unassigned.length > 0) {
    target = unassigned[Math.floor(Math.random() * unassigned.length)]
  } else if (tasksStore.tasks.length > 0) {
    target = tasksStore.tasks[Math.floor(Math.random() * tasksStore.tasks.length)]
  }

  if (target) {
    selectedTask.value = target
    highlightTaskOnMap(target)
  }
}

const initMap = () => {
  if (map) return

  const initialProj = tasksStore.projects.find(p => p.id === activeAreaId.value)
  const centerLat = initialProj ? initialProj.center_lat : -0.750
  const centerLon = initialProj ? initialProj.center_lon : 100.500
  const zoom = initialProj ? initialProj.default_zoom : 8

  map = L.map('hot-map-container', {
    center: [centerLat, centerLon],
    zoom: zoom,
    zoomControl: false
  })

  L.control.zoom({ position: 'bottomleft' }).addTo(map)

  // Satellite Base Layer
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Satellite Imagery © Esri'
  }).addTo(map)

  // Local Sentinel-2 COG Mosaic Layer (2025 10m)
  L.tileLayer(api.getMosaicRasterTileUrl(2025, 'rgb'), {
    maxZoom: 18,
    attribution: 'Sentinel-2 Sumbar (2025) 10m COG'
  }).addTo(map)

  gridLayerGroup = L.featureGroup().addTo(map)
  renderGridTilesOnMap()
}

const highlightTaskOnMap = (task) => {
  if (!gridLayerGroup || !map) return
  gridLayerGroup.eachLayer((layer) => {
    if (layer.taskRef) {
      const isSelected = layer.taskRef.id === task.id
      const lStyle = HOT_OSM_COLORS[layer.taskRef.status] || HOT_OSM_COLORS.UNASSIGNED
      layer.setStyle({
        color: isSelected ? '#ffffff' : lStyle.stroke,
        weight: isSelected ? 3.5 : 1.8,
        fillOpacity: isSelected ? 0.75 : lStyle.opacity
      })
      if (isSelected) {
        map.flyToBounds(layer.getBounds(), { maxZoom: 14, duration: 0.8, padding: [40, 40] })
      }
    }
  })
}

const renderGridTilesOnMap = () => {
  if (!gridLayerGroup || !map) return
  gridLayerGroup.clearLayers()

  filteredTasks.value.forEach((task) => {
    const styleConf = HOT_OSM_COLORS[task.status] || HOT_OSM_COLORS.UNASSIGNED
    const bounds = [
      [task.min_lat, task.min_lon],
      [task.max_lat, task.max_lon]
    ]

    const isSelected = selectedTask.value && selectedTask.value.id === task.id

    const rect = L.rectangle(bounds, {
      color: isSelected ? '#ffffff' : styleConf.stroke,
      weight: isSelected ? 3.5 : 1.8,
      fillColor: styleConf.fill,
      fillOpacity: isSelected ? 0.75 : styleConf.opacity
    })

    // Hover Tooltip
    rect.bindTooltip(
      `<div class="p-1">
        <div class="font-bold text-xs text-slate-900 font-mono">${task.grid_code}</div>
        <div class="text-[11px] text-slate-600">Status: <span class="font-semibold">${formatStatus(task.status)}</span></div>
        <div class="text-[11px] text-slate-600">User: <span class="font-semibold">${task.assigned_user_name || 'Tersedia'}</span></div>
        <div class="text-[10px] text-purple-700 font-mono font-bold mt-0.5">${task.annotation_count || 0} Poligon</div>
      </div>`,
      { direction: 'top', sticky: true, className: 'hot-osm-light-tooltip' }
    )

    rect.on('mouseover', function () {
      this.setStyle({ weight: 3.5, color: '#ffffff', fillOpacity: 0.8 })
    })

    rect.on('mouseout', function () {
      const curSelected = selectedTask.value && selectedTask.value.id === task.id
      this.setStyle({
        weight: curSelected ? 3.5 : 1.8,
        color: curSelected ? '#ffffff' : styleConf.stroke,
        fillOpacity: curSelected ? 0.75 : styleConf.opacity
      })
    })

    rect.on('click', () => {
      selectedTask.value = task
      gridLayerGroup.eachLayer((layer) => {
        if (layer.taskRef) {
          const lStyle = HOT_OSM_COLORS[layer.taskRef.status] || HOT_OSM_COLORS.UNASSIGNED
          layer.setStyle({ color: lStyle.stroke, weight: 1.8, fillOpacity: lStyle.opacity })
        }
      })
      rect.setStyle({ color: '#ffffff', weight: 3.5, fillOpacity: 0.75 })
    })

    rect.taskRef = task
    gridLayerGroup.addLayer(rect)
  })
}

const claimSelectedTask = async () => {
  if (!selectedTask.value) return
  actionLoading.value = true
  try {
    const response = await api.claimTask(selectedTask.value.id)
    alert(response.data.message)
    await loadTasksForArea()
    selectedTask.value = tasksStore.tasks.find(t => t.id === selectedTask.value.id) || null
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal mengklaim grid.')
  } finally {
    actionLoading.value = false
  }
}

const unclaimSelectedTask = async () => {
  if (!selectedTask.value) return
  actionLoading.value = true
  try {
    const response = await api.unclaimTask(selectedTask.value.id)
    alert(response.data.message)
    await loadTasksForArea()
    selectedTask.value = tasksStore.tasks.find(t => t.id === selectedTask.value.id) || null
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal melepas grid.')
  } finally {
    actionLoading.value = false
  }
}

const openInStudio = () => {
  if (!selectedTask.value) return
  router.push({ path: '/map', query: { taskId: selectedTask.value.id } })
}

// Progress Metrics
const totalCount = computed(() => tasksStore.tasks.length || 1)
const unassignedCount = computed(() => tasksStore.tasks.filter(t => t.status === 'UNASSIGNED').length)
const inProgressCount = computed(() => tasksStore.tasks.filter(t => t.status === 'IN_PROGRESS' || t.status === 'ASSIGNED').length)
const submittedCount = computed(() => tasksStore.tasks.filter(t => t.status === 'SUBMITTED').length)
const approvedCount = computed(() => tasksStore.tasks.filter(t => t.status === 'APPROVED').length)
const revisionCount = computed(() => tasksStore.tasks.filter(t => t.status === 'REVISION_NEEDED').length)

const progressPercent = computed(() => Math.round((approvedCount.value / totalCount.value) * 100))
const approvedPercent = computed(() => (approvedCount.value / totalCount.value) * 100)
const submittedPercent = computed(() => (submittedCount.value / totalCount.value) * 100)
const inProgressPercent = computed(() => (inProgressCount.value / totalCount.value) * 100)
const revisionPercent = computed(() => (revisionCount.value / totalCount.value) * 100)

const formatStatus = (status) => {
  switch (status) {
    case 'UNASSIGNED': return 'Tersedia'
    case 'ASSIGNED': return 'Diambil'
    case 'IN_PROGRESS': return 'Dikerjakan'
    case 'SUBMITTED': return 'Review'
    case 'APPROVED': return 'Approved'
    case 'REVISION_NEEDED': return 'Revisi'
    default: return status || 'Tersedia'
  }
}

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'APPROVED': return 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold'
    case 'SUBMITTED': return 'bg-orange-100 text-orange-800 border-orange-300 font-bold'
    case 'IN_PROGRESS':
    case 'ASSIGNED': return 'bg-amber-100 text-amber-800 border-amber-300 font-bold'
    case 'REVISION_NEEDED': return 'bg-rose-100 text-rose-800 border-rose-300 font-bold'
    default: return 'bg-slate-100 text-slate-600 border-slate-300 font-semibold'
  }
}
</script>

<style>
.hot-osm-light-tooltip {
  background-color: #ffffff !important;
  color: #0f172a !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 10px !important;
  font-size: 11px !important;
  padding: 4px 8px !important;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15) !important;
}
.hot-osm-light-tooltip::before {
  border-top-color: #ffffff !important;
}
</style>

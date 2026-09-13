<template>
  <div class="h-[calc(100vh-57px)] w-full flex flex-col lg:flex-row bg-white text-[#2c3038] font-sans overflow-hidden selection:bg-[#d73f3f] selection:text-white">

    <!-- LEFT SIDEBAR: Fixed header + tabs, scrollable content below -->
    <div class="w-full lg:w-[480px] xl:w-[540px] bg-white border-r border-[#e4e7eb] flex flex-col h-full shrink-0 z-10 shadow-sm overflow-hidden">
      
      <!-- Project Header Card — FIXED, does not scroll -->
      <div class="p-6 border-b border-[#e4e7eb] space-y-3 bg-slate-50/50 shrink-0">
        <div class="flex items-center justify-between">
          <span class="text-xs text-[#707a8a] font-mono font-medium">
            #{{ projectId === 2 ? '62542' : '62541' }} | STEVI · {{ projectArea }}
          </span>
          <span class="text-[10px] font-bold px-2.5 py-0.5 rounded-full border border-[#f59e0b] bg-amber-50 text-[#b45309] uppercase tracking-wider flex items-center gap-1">
            <Clock :size="10" />
            <span>PRIORITY HIGH</span>
          </span>
        </div>

        <div class="space-y-1">
          <h1 class="text-2xl font-black text-[#1f242e] tracking-tight uppercase leading-tight font-heading">
            {{ projectTitle }}
          </h1>
          <p class="text-xs text-[#707a8a] leading-relaxed">
            Data Latih Sentinel-2 (2026/2017) · Resolusi 10m · {{ projectArea }} · Patch 1024px
          </p>
        </div>
      </div>

      <!-- Tabs Navigation — FIXED below header, does not scroll -->
      <div class="px-6 border-b border-[#e4e7eb] bg-white flex items-center gap-4 text-xs font-black uppercase tracking-wider shrink-0 shadow-2xs">
        <button
          @click="activeTab = 'instructions'"
          class="py-3.5 transition-colors relative whitespace-nowrap cursor-pointer"
          :class="activeTab === 'instructions' ? 'text-[#d73f3f] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2.5px] after:bg-[#d73f3f]' : 'text-[#707a8a] hover:text-[#1f242e]'"
        >
          PETUNJUK & INSTRUKSI
        </button>

        <button
          @click="activeTab = 'tasks'"
          class="py-3.5 transition-colors relative whitespace-nowrap cursor-pointer"
          :class="activeTab === 'tasks' ? 'text-[#d73f3f] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2.5px] after:bg-[#d73f3f]' : 'text-[#707a8a] hover:text-[#1f242e]'"
        >
          STATUS GRID
        </button>

        <button
          @click="activeTab = 'contributions'"
          class="py-3.5 transition-colors relative whitespace-nowrap cursor-pointer"
          :class="activeTab === 'contributions' ? 'text-[#d73f3f] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2.5px] after:bg-[#d73f3f]' : 'text-[#707a8a] hover:text-[#1f242e]'"
        >
          KONTRIBUTOR PROYEK
        </button>
      </div>

      <!-- TAB CONTENT AREA — Scrolls independently below the fixed tabs -->
      <div class="flex-1 overflow-y-auto">
        <div class="p-6 space-y-6">

          <!-- TAB 1: INSTRUCTIONS -->
          <div v-if="activeTab === 'instructions'" class="space-y-6 text-xs text-[#2c3038] leading-relaxed">
            <div class="space-y-3">
              <h3 class="text-sm font-black text-[#1f242e] uppercase font-heading">Catatan Khusus Panduan Digitasi</h3>

              <ul class="space-y-3 list-disc pl-4 text-[#555d6b]">
                <li>
                  <b class="text-[#1f242e]">Pilihan Citra Satelit:</b> Gunakan citra komposit <b>Sentinel-2 Cloudless (10m)</b> atau <b>Google Satellite HD</b> sebagai layer utama. Anda dapat mengganti ke layer <b>False Color NIR (8-4-3)</b> atau <b>SWIR (11-8-2)</b> untuk membedakan vegetasi lebat, perkebunan kelapa sawit, dan sawah.
                </li>
                <li>
                  <b class="text-[#1f242e]">Kerapian Batas Objek:</b> Buat poligon tutupan lahan tepat di dalam batas kotak grid 1024px yang sedang dikerjakan. Hindari poligon bertumpuk (overlap) yang saling menabrak tanpa keteraturan.
                </li>
                <li>
                  <b class="text-[#1f242e]">Penyelesaian & Submit Tugas:</b> Simpan draf pekerjaan Anda secara bertahap dengan tombol <i>Simpan Draf</i>, lalu klik <i>Submit Review QC</i> jika seluruh area pada grid tersebut telah selesai dipetakan.
                </li>
                <li>
                  <b class="text-[#1f242e]">Standar 12 Kelas Tutupan Lahan (SNI/LULC):</b>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-2 text-[11px]">
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#006400]"></span>
                      <span>1. Hutan Lahan Kering</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#2E8B57]"></span>
                      <span>2. Hutan Mangrove / Rawa</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#9ACD32]"></span>
                      <span>3. Semak & Belukar</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#FFD700]"></span>
                      <span>4. Pertanian Lahan Kering</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#808000]"></span>
                      <span>5. Perkebunan Kelapa Sawit</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#FF0000]"></span>
                      <span>6. Bangunan & Permukiman</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#D2B48C]"></span>
                      <span>7. Lahan Terbuka</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#8B4513]"></span>
                      <span>8. Pertambangan</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#0000FF]"></span>
                      <span>9. Tubuh Air</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#00FFFF]"></span>
                      <span>10. Sawah Lahan Basah</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#F0E68C]"></span>
                      <span>11. Savanna</span>
                    </div>
                    <div class="flex items-center gap-2 p-1.5 bg-[#f8f9fa] rounded border border-[#e4e7eb]">
                      <span class="w-3 h-3 rounded-xs bg-[#008B8B]"></span>
                      <span>12. Tambak Pesisir</span>
                    </div>
                  </div>
                </li>
              </ul>
            </div>

            <div class="pt-2 border-t border-[#e4e7eb] space-y-2">
              <h3 class="text-sm font-black text-[#1f242e] uppercase font-heading">Validasi & Quality Control oleh Reviewer</h3>
              <p class="text-[#555d6b]">
                Semua hasil anotasi kontributor akan divalidasi oleh Reviewer QC melalui menu <b>Review QC</b>. Tugas yang disetujui (Approved) akan langsung masuk ke antrean generator dataset GeoAI.
              </p>
            </div>
          </div>

          <!-- TAB 2: TASKS OVERVIEW -->
          <div v-else-if="activeTab === 'tasks'" class="space-y-5 text-xs text-[#2c3038]">
            <p class="text-[#555d6b] leading-relaxed">
              Wilayah kajian dibagi ke dalam ribuan grid tile berukuran 1024 × 1024 pixel (~10.24km per tile). Klik salah satu tile pada peta di sebelah kanan untuk melihat detail.
            </p>

            <!-- Selected Task Card -->
            <div v-if="selectedTask" class="p-4 bg-slate-50 border border-slate-300 rounded-2xl space-y-2.5 shadow-xs">
              <div class="flex items-center justify-between">
                <span class="font-mono font-bold text-slate-900 text-sm">{{ selectedTask.grid_code }}</span>
                <span class="text-[10px] font-bold px-2.5 py-0.5 rounded-full" :class="getStatusBadgeClass(selectedTask.status)">
                  {{ selectedTask.status }}
                </span>
              </div>
              <div class="text-slate-600">
                Annotator: <span class="font-bold text-slate-900">{{ selectedTask.assigned_user_name || 'Belum Ditugaskan (Tersedia)' }}</span>
              </div>
              <div class="text-purple-700 font-mono font-bold">
                {{ selectedTask.annotation_count || 0 }} Poligon Terdigitasi
              </div>
              <router-link
                :to="`/map?taskId=${selectedTask.id}`"
                class="inline-block w-full bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold py-2.5 px-4 rounded-xl text-center uppercase tracking-wider transition-colors shadow-sm"
              >
                Buka Grid di Studio Digitasi →
              </router-link>
            </div>

            <!-- Progress summary -->
            <div class="space-y-2 pt-2 border-t border-[#e4e7eb]">
              <div class="flex items-center justify-between text-xs font-bold text-[#707a8a]">
                <span>Progress Pemetaan Grid</span>
                <span class="font-mono text-emerald-600">68% Selesai</span>
              </div>
              <div class="w-full h-2 bg-[#e4e7eb] rounded-full overflow-hidden flex">
                <div style="width: 45%" class="bg-[#10b981]"></div>
                <div style="width: 15%" class="bg-[#ea580c]"></div>
                <div style="width: 8%" class="bg-[#f59e0b]"></div>
              </div>
            </div>
          </div>

          <!-- TAB 3: KONTRIBUTOR PROYEK -->
          <div v-else-if="activeTab === 'contributions'" class="space-y-3 text-xs text-[#2c3038]">
            <!-- Sub-header -->
            <div class="flex items-center justify-between pb-2 border-b border-[#e4e7eb]">
              <span class="text-xs font-bold text-[#707a8a] uppercase tracking-wider">Kontributor Terdaftar</span>
              <span class="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                {{ tasksStore.stats?.student_contributions?.length || 0 }} Akun
              </span>
            </div>

            <!-- Ranked contributor list -->
            <div v-if="tasksStore.stats?.student_contributions?.length" class="space-y-2">
              <div
                v-for="(student, idx) in tasksStore.stats.student_contributions"
                :key="student.user_id || idx"
                class="p-3.5 bg-[#f8f9fa] border border-[#e4e7eb] rounded-2xl flex items-center justify-between hover:bg-white hover:border-[#cfd4dc] transition-all shadow-2xs"
              >
                <div class="flex items-center gap-3">
                  <span
                    class="w-7 h-7 rounded-xl font-black text-xs flex items-center justify-center shrink-0"
                    :class="idx === 0 
                      ? 'bg-amber-100 text-amber-800 border border-amber-300' 
                      : idx === 1 
                      ? 'bg-slate-200 text-slate-700 border border-slate-300' 
                      : idx === 2 
                      ? 'bg-amber-50 text-amber-700 border border-amber-200' 
                      : 'bg-white text-slate-600 border border-slate-200'"
                  >
                    <span v-if="idx === 0">🥇</span>
                    <span v-else-if="idx === 1">🥈</span>
                    <span v-else-if="idx === 2">🥉</span>
                    <span v-else class="font-mono">{{ idx + 1 }}</span>
                  </span>
                  <div class="min-w-0">
                    <div class="font-bold text-sm text-[#1f242e] truncate">{{ student.name }}</div>
                    <div class="text-[11px] text-[#707a8a] flex items-center gap-1.5 mt-0.5">
                      <span class="font-mono text-slate-400">@{{ student.username }}</span>
                      <span class="text-slate-300">·</span>
                      <span class="text-emerald-700 font-semibold">{{ student.approved_tasks || 0 }} Disetujui</span>
                    </div>
                  </div>
                </div>
                <div class="text-right shrink-0 ml-2">
                  <div class="font-mono font-black text-sm text-purple-700">{{ student.total_polygons || 0 }}</div>
                  <div class="text-[10px] text-slate-400 font-bold uppercase">Poligon</div>
                </div>
              </div>
            </div>

            <div v-else class="p-6 bg-[#f8f9fa] border border-dashed border-[#e4e7eb] rounded-2xl text-center text-slate-400 text-xs">
              Belum ada data kontributor pada proyek ini.
            </div>
          </div>

        </div>

        <!-- Bottom action bar inside scrollable area -->
        <div class="p-4 border-t border-[#e4e7eb] bg-slate-50/80">
          <router-link
            to="/tasking"
            class="w-full bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs py-2.5 px-4 rounded-xl transition-colors uppercase tracking-wider flex items-center justify-center gap-2 shadow-sm cursor-pointer"
          >
            <Grid :size="14" />
            <span>Buka Semua Grid di Tasking Map</span>
          </router-link>
        </div>
      </div>

    </div>

    <!-- RIGHT SECTION: Full Interactive Leaflet Grid Map -->
    <div class="flex-1 relative w-full h-[500px] lg:h-full bg-slate-200 overflow-hidden min-h-[400px]">
      <!-- Leaflet Map Container with explicit absolute fill -->
      <div id="project-overview-map" class="absolute inset-0 w-full h-full z-0"></div>

      <!-- ZOOM TO TASKS Button -->
      <div class="absolute top-4 left-4 z-10">
        <button
          @click="fitProjectBounds"
          class="bg-white/95 hover:bg-white text-[#1f242e] text-xs font-black px-4 py-2.5 rounded-xl shadow-md border border-[#cfd4dc] uppercase tracking-wider flex items-center gap-2 backdrop-blur-xs transition-all cursor-pointer"
        >
          <LocateFixed :size="14" class="text-rose-600" />
          <span>ZOOM TO TASKS</span>
        </button>
      </div>

      <!-- Floating Status Legend -->
      <div class="absolute bottom-6 right-6 z-10 bg-white/95 border border-[#cfd4dc] p-3.5 rounded-2xl shadow-xl backdrop-blur-md space-y-1.5 text-xs min-w-[200px]">
        <div class="font-bold text-[#1f242e] text-[11px] uppercase tracking-wider flex items-center justify-between pb-1 border-b border-[#e4e7eb]">
          <span>LEGENDA STATUS GRID</span>
          <Layers :size="13" class="text-[#707a8a]" />
        </div>
        <div class="space-y-1 text-[11px] text-[#555d6b]">
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 border border-[#94a3b8] bg-[#f8fafc] rounded-xs shrink-0"></span>
            <span>Tersedia untuk Digitasi</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 border border-[#f59e0b] bg-[#fde68a] rounded-xs shrink-0"></span>
            <span>Sedang Dikerjakan</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 border border-[#ea580c] bg-[#fb923c] rounded-xs shrink-0"></span>
            <span>Menunggu Review QC</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 border border-[#10b981] bg-[#34d399] rounded-xs shrink-0"></span>
            <span>Disetujui (Approved)</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3.5 h-3.5 border border-[#e11d48] bg-[#f87171] rounded-xs shrink-0"></span>
            <span>Perlu Revisi</span>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Clock, Grid, LocateFixed, Layers } from 'lucide-vue-next'
import L from 'leaflet'

import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import { useAnnotationsStore } from '../stores/annotations'

const route = useRoute()
const authStore = useAuthStore()
const tasksStore = useTasksStore()
const annotationsStore = useAnnotationsStore()

const activeTab = ref(route.query.tab || 'instructions')
const projectId = computed(() => parseInt(route.params.id) || 1)
const selectedTask = ref(null)

const defaultStudentsList = [
  { user_id: 2, name: 'Ahmad Fauzi (Mahasiswa 1)', username: 'mahasiswa1', assigned_tasks: 8, submitted_tasks: 2, approved_tasks: 6, total_polygons: 142 },
  { user_id: 3, name: 'Budi Santoso (Mahasiswa 2)', username: 'mahasiswa2', assigned_tasks: 7, submitted_tasks: 1, approved_tasks: 6, total_polygons: 118 },
  { user_id: 4, name: 'Citra Dewi (Mahasiswa 3)', username: 'mahasiswa3', assigned_tasks: 6, submitted_tasks: 1, approved_tasks: 5, total_polygons: 96 },
  { user_id: 5, name: 'Dian Pratama (Mahasiswa 4)', username: 'mahasiswa4', assigned_tasks: 5, submitted_tasks: 2, approved_tasks: 3, total_polygons: 84 },
  { user_id: 6, name: 'Eko Prasetyo (Mahasiswa 5)', username: 'mahasiswa5', assigned_tasks: 4, submitted_tasks: 1, approved_tasks: 3, total_polygons: 72 },
  { user_id: 7, name: 'Fitri Anggraini (Mahasiswa 6)', username: 'mahasiswa6', assigned_tasks: 4, submitted_tasks: 0, approved_tasks: 4, total_polygons: 65 },
  { user_id: 8, name: 'Gita Permata (Mahasiswa 7)', username: 'mahasiswa7', assigned_tasks: 3, submitted_tasks: 1, approved_tasks: 2, total_polygons: 58 },
  { user_id: 9, name: 'Hadi Wijaya (Mahasiswa 8)', username: 'mahasiswa8', assigned_tasks: 3, submitted_tasks: 0, approved_tasks: 3, total_polygons: 49 },
  { user_id: 10, name: 'Indah Lestari (Mahasiswa 9)', username: 'mahasiswa9', assigned_tasks: 2, submitted_tasks: 1, approved_tasks: 1, total_polygons: 38 },
  { user_id: 11, name: 'Joko Nugroho (Mahasiswa 10)', username: 'mahasiswa10', assigned_tasks: 2, submitted_tasks: 0, approved_tasks: 2, total_polygons: 32 }
]

// Fallback dummy grid boxes (1024px ~10.24km, step = 0.0922 deg)
const generateFallbackGrids = (areaId) => {
  const isPadang = areaId === 1
  const originLat = isPadang ? 0.20 : 3.50
  const originLon = isPadang ? 98.80 : 109.50
  const size = 0.0922
  const grids = []

  for (let r = 0; r < 6; r++) {
    for (let c = 0; c < 8; c++) {
      const min_lat = originLat - (r * size)
      const max_lat = min_lat + size
      const min_lon = originLon + (c * size)
      const max_lon = min_lon + size
      const code = `${isPadang ? 'SB' : 'KL'}_R${r+1}_C${c+1}_2026`
      
      let status = 'UNASSIGNED'
      let annCount = 0
      let user_name = null
      if (r === 0 || (r === 1 && c < 4)) {
        status = 'APPROVED'
        annCount = 18 + (c * 3)
        user_name = defaultStudentsList[c % 10].name
      } else if (r === 1 || r === 2) {
        status = 'SUBMITTED'
        annCount = 11 + c
        user_name = defaultStudentsList[(c + 2) % 10].name
      } else if (r === 3 || r === 4) {
        status = 'IN_PROGRESS'
        annCount = 6 + c
        user_name = defaultStudentsList[(c + 4) % 10].name
      }

      grids.push({
        id: (areaId * 1000) + (r * 10) + c + 1,
        study_area_id: areaId,
        grid_code: code,
        min_lat,
        min_lon,
        max_lat,
        max_lon,
        status,
        annotation_count: annCount,
        assigned_user_name: user_name
      })
    }
  }
  return grids
}

const currentProject = computed(() => {
  return tasksStore.projects.find(p => p.id === projectId.value) || null
})

const projectTitle = computed(() => {
  if (currentProject.value) return currentProject.value.name.toUpperCase()
  return projectId.value === 2
    ? 'MAPPING PULAU KALIMANTAN : SELURUH WILAYAH'
    : 'MAPPING PROVINSI SUMATERA BARAT : SELURUH WILAYAH'
})

const projectArea = computed(() => {
  if (currentProject.value) return currentProject.value.name
  return projectId.value === 2 ? 'Pulau Kalimantan' : 'Provinsi Sumatera Barat'
})

let map = null
let gridLayerGroup = null

onMounted(async () => {
  try {
    tasksStore.selectedArea = projectId.value
    await Promise.allSettled([
      tasksStore.fetchProjects(),
      annotationsStore.fetchClasses(),
      tasksStore.fetchTasks(),
      tasksStore.fetchStatsSummary()
    ])
  } catch (e) {
    console.warn('Data fetch warning:', e)
  }
  await nextTick()
  initMap()
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

const initMap = () => {
  const mapEl = document.getElementById('project-overview-map')
  if (!mapEl) return

  if (map) {
    map.remove()
    map = null
  }

  const proj = currentProject.value
  const centerLat = proj ? proj.center_lat : (projectId.value === 2 ? 0.000 : -0.750)
  const centerLon = proj ? proj.center_lon : (projectId.value === 2 ? 114.000 : 100.500)
  const zoomLevel = proj ? proj.default_zoom : (projectId.value === 2 ? 6 : 8)
  
  map = L.map('project-overview-map', {
    zoomControl: false
  }).setView([centerLat, centerLon], zoomLevel)

  L.control.zoom({ position: 'topright' }).addTo(map)

  // Satellite Imagery Layer (Esri & OpenStreetMap fallback)
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: '© Esri Satellite Imagery'
  }).addTo(map)

  gridLayerGroup = L.layerGroup().addTo(map)
  renderGrids()

  // Invalidate size multiple times to ensure full canvas rendering
  setTimeout(() => {
    map?.invalidateSize()
    fitProjectBounds()
  }, 150)

  setTimeout(() => {
    map?.invalidateSize()
  }, 500)
}

const renderGrids = () => {
  if (!gridLayerGroup || !map) return
  gridLayerGroup.clearLayers()

  const targetAreaId = projectId.value === 2 ? 2 : 1
  let filtered = tasksStore.tasks.filter(t => t.study_area_id === targetAreaId)
  
  // If no tasks from backend yet, use fallback generated grid boxes
  if (!filtered || filtered.length === 0) {
    filtered = generateFallbackGrids(targetAreaId)
  }

  filtered.forEach(task => {
    if (task.min_lat !== undefined && task.min_lon !== undefined && task.max_lat !== undefined && task.max_lon !== undefined) {
      const bounds = [
        [task.min_lat, task.min_lon],
        [task.max_lat, task.max_lon]
      ]

      const stroke = getGridStrokeColor(task.status)
      const fill = getGridFillColor(task.status)

      const rect = L.rectangle(bounds, {
        color: stroke,
        weight: 1.5,
        fillColor: fill,
        fillOpacity: 0.55
      })

      rect.bindTooltip(
        `<div class="p-1 text-xs font-sans">
          <div class="font-bold text-slate-900 font-mono">${task.grid_code}</div>
          <div class="text-[11px] text-slate-600">Status: <b class="text-slate-800">${task.status}</b></div>
          <div class="text-[11px] text-slate-600">User: ${task.assigned_user_name || 'Tersedia'}</div>
          <div class="text-[10px] text-purple-700 font-mono font-bold mt-0.5">${task.annotation_count || 0} Poligon</div>
        </div>`,
        { direction: 'top', sticky: true }
      )

      rect.on('mouseover', function () {
        this.setStyle({ weight: 3, color: '#ffffff', fillOpacity: 0.85 })
      })

      rect.on('mouseout', function () {
        const isSelected = selectedTask.value && selectedTask.value.id === task.id
        this.setStyle({
          weight: isSelected ? 3 : 1.5,
          color: isSelected ? '#ffffff' : stroke,
          fillOpacity: isSelected ? 0.8 : 0.55
        })
      })

      rect.on('click', () => {
        selectedTask.value = task
        activeTab.value = 'tasks'
        gridLayerGroup.eachLayer(layer => {
          if (layer.taskData) {
            layer.setStyle({
              color: getGridStrokeColor(layer.taskData.status),
              weight: 1.5,
              fillOpacity: 0.55
            })
          }
        })
        rect.setStyle({ color: '#ffffff', weight: 3.5, fillOpacity: 0.85 })
      })

      rect.taskData = task
      gridLayerGroup.addLayer(rect)
    }
  })

  // Fit bounds if we have layers
  if (gridLayerGroup.getLayers().length > 0) {
    const groupBounds = L.featureGroup(gridLayerGroup.getLayers()).getBounds()
    if (groupBounds.isValid()) {
      map.fitBounds(groupBounds, { padding: [30, 30] })
    }
  }
}

const fitProjectBounds = () => {
  if (!map || !gridLayerGroup) return
  const layers = gridLayerGroup.getLayers()
  if (layers.length > 0) {
    const groupBounds = L.featureGroup(layers).getBounds()
    if (groupBounds.isValid()) {
      map.fitBounds(groupBounds, { padding: [30, 30] })
    }
  } else {
    const center = projectId.value === 2 ? [-1.120, 116.880] : [-0.947, 100.370]
    map.setView(center, 12)
  }
}

const getGridStrokeColor = (status) => {
  switch (status) {
    case 'IN_PROGRESS':
    case 'ASSIGNED': return '#f59e0b'
    case 'SUBMITTED': return '#ea580c'
    case 'APPROVED': return '#10b981'
    case 'REVISION_NEEDED': return '#e11d48'
    default: return '#94a3b8'
  }
}

const getGridFillColor = (status) => {
  switch (status) {
    case 'IN_PROGRESS':
    case 'ASSIGNED': return '#fde68a'
    case 'SUBMITTED': return '#fb923c'
    case 'APPROVED': return '#34d399'
    case 'REVISION_NEEDED': return '#f87171'
    default: return '#f8fafc'
  }
}

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'APPROVED': return 'bg-emerald-100 text-emerald-800'
    case 'SUBMITTED': return 'bg-orange-100 text-orange-800'
    case 'IN_PROGRESS':
    case 'ASSIGNED': return 'bg-amber-100 text-amber-800'
    case 'REVISION_NEEDED': return 'bg-rose-100 text-rose-800'
    default: return 'bg-slate-100 text-slate-700'
  }
}
</script>

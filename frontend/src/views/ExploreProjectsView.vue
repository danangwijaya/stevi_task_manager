<template>
  <div class="min-h-full w-full bg-[#f6f8fa] text-[#2c3038] font-sans selection:bg-[#d73f3f] selection:text-white pb-20">
    
    <!-- TOP HEADER / HERO BANNER -->
    <div class="bg-[#1a1f2c] text-white border-b border-slate-800 relative overflow-hidden">
      <div
        class="absolute inset-0 bg-cover bg-center opacity-20 mix-blend-luminosity"
        style="background-image: url('https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=2000&q=80');"
      ></div>
      <div class="absolute inset-0 bg-gradient-to-r from-[#0f131a]/95 via-[#0f131a]/85 to-transparent"></div>

      <div class="max-w-7xl mx-auto px-6 lg:px-12 py-10 relative z-10">
        <div class="max-w-3xl space-y-2">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 text-xs font-bold uppercase tracking-wider border border-rose-500/30">
            <Compass :size="13" />
            <span>Katalog Proyek Pemetaan Terbuka</span>
          </div>
          <h1 class="text-3xl sm:text-4xl font-black tracking-tight uppercase leading-tight font-heading text-white">
            Explore Projects
          </h1>
          <p class="text-sm sm:text-base text-[#cfd4dc] font-normal leading-relaxed">
            Pilih project kawasan studi spasial di bawah ini untuk memulai pemetaan patch citra satelit Sentinel-2, validasi tutupan lahan, dan analisis jasa ekosistem.
          </p>
        </div>
      </div>
    </div>

    <!-- FILTER & SEARCH TOOLBAR -->
    <div class="bg-white border-b border-[#e4e7eb] sticky top-[57px] z-30 shadow-xs">
      <div class="max-w-7xl mx-auto px-6 lg:px-12 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        <!-- Search Input -->
        <div class="relative flex-1 max-w-md">
          <Search :size="16" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Cari nama project, pulau, atau lokasi..."
            class="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition-all"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
          >
            <X :size="14" />
          </button>
        </div>

        <!-- Filters (Priority & Difficulty & Sorting) -->
        <div class="flex items-center flex-wrap gap-2.5">
          <!-- Priority Filter -->
          <div class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold">
            <button
              @click="selectedPriority = 'ALL'"
              class="px-3 py-1.5 rounded-lg transition-all"
              :class="selectedPriority === 'ALL' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'"
            >
              Semua Prioritas
            </button>
            <button
              @click="selectedPriority = 'URGENT'"
              class="px-3 py-1.5 rounded-lg transition-all flex items-center gap-1"
              :class="selectedPriority === 'URGENT' ? 'bg-rose-500 text-white shadow-2xs' : 'text-rose-700 hover:bg-rose-50'"
            >
              <Flame :size="12" />
              <span>Urgent</span>
            </button>
            <button
              @click="selectedPriority = 'HIGH'"
              class="px-3 py-1.5 rounded-lg transition-all flex items-center gap-1"
              :class="selectedPriority === 'HIGH' ? 'bg-amber-500 text-white shadow-2xs' : 'text-amber-700 hover:bg-amber-50'"
            >
              <Clock :size="12" />
              <span>High</span>
            </button>
          </div>

          <!-- Difficulty Filter Dropdown -->
          <select
            v-model="selectedDifficulty"
            class="bg-slate-50 border border-slate-200 text-xs font-bold text-slate-700 py-2.5 px-3 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-rose-500/20"
          >
            <option value="ALL">Semua Kesulitan</option>
            <option value="Beginner">Beginner (Pemula)</option>
            <option value="Moderate">Moderate (Menengah)</option>
            <option value="Challenging">Challenging (Mahir)</option>
          </select>

          <!-- Sort Dropdown -->
          <select
            v-model="sortBy"
            class="bg-slate-50 border border-slate-200 text-xs font-bold text-slate-700 py-2.5 px-3 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-rose-500/20"
          >
            <option value="id_asc">Urutkan: ID Default</option>
            <option value="tasks_desc">Grid Terbanyak</option>
            <option value="contributors_desc">Kontributor Terbanyak</option>
            <option value="progress_desc">Progress Tertinggi</option>
          </select>
        </div>
      </div>
    </div>

    <!-- MAIN CONTENT AREA -->
    <div class="max-w-7xl mx-auto px-6 lg:px-12 py-8 space-y-6">
      
      <!-- Counter Bar (matches HOT OSM: "showing 14 of 1,406 projects") -->
      <div class="flex items-center justify-between text-xs text-[#707a8a] border-b border-slate-200 pb-3">
        <div class="font-medium">
          Menampilkan <span class="font-bold text-slate-900">{{ filteredProjects.length }}</span> dari 
          <span class="font-bold text-slate-900">{{ projects.length }}</span> project pemetaan
        </div>
        <div class="flex items-center gap-4 text-[11px]">
          <span class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block"></span> Selesai (QC Approved)
          </span>
          <span class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-sm bg-rose-500 inline-block"></span> Dikerjakan / Review
          </span>
          <span class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-sm bg-slate-300 inline-block"></span> Tersedia
          </span>
        </div>
      </div>

      <!-- Loading State Skeleton -->
      <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="i in 4" :key="i" class="bg-white border border-slate-200 rounded-xl p-5 space-y-4 animate-pulse">
          <div class="flex justify-between items-center">
            <div class="w-8 h-8 bg-slate-200 rounded-lg"></div>
            <div class="w-16 h-5 bg-slate-200 rounded"></div>
          </div>
          <div class="w-24 h-4 bg-slate-200 rounded"></div>
          <div class="w-3/4 h-6 bg-slate-200 rounded"></div>
          <div class="w-full h-12 bg-slate-100 rounded"></div>
          <div class="w-full h-3 bg-slate-200 rounded"></div>
          <div class="flex justify-between items-center pt-2">
            <div class="w-16 h-4 bg-slate-200 rounded"></div>
            <div class="w-20 h-4 bg-slate-200 rounded"></div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredProjects.length === 0" class="text-center py-20 bg-white rounded-2xl border border-slate-200 space-y-4 shadow-xs">
        <div class="w-16 h-16 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
          <FolderSearch :size="28" />
        </div>
        <div>
          <h3 class="text-base font-extrabold text-slate-800">Tidak ada project yang sesuai filter</h3>
          <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Coba gunakan kata kunci lain atau ubah filter prioritas dan tingkat kesulitan di bagian atas.
          </p>
        </div>
        <button
          @click="resetFilters"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-700 transition-colors"
        >
          <RotateCcw :size="13" />
          <span>Reset Semua Filter</span>
        </button>
      </div>

      <!-- HOT OSM STYLE CARDS GRID -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div
          v-for="project in filteredProjects"
          :key="project.id"
          class="bg-white border border-[#e4e7eb] hover:border-slate-400 hover:shadow-lg rounded-xl overflow-hidden flex flex-col justify-between transition-all duration-200 group cursor-pointer"
          @click="selectProject(project)"
        >
          <div class="p-5 space-y-3.5">
            
            <!-- Top Row: Project Icon + Priority Badge -->
            <div class="flex items-center justify-between">
              <!-- Org / Project Icon -->
              <div class="w-8 h-8 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-center text-[#d73f3f] group-hover:scale-105 transition-transform">
                <Globe :size="18" />
              </div>

              <!-- Priority Pill -->
              <span
                v-if="project.priority === 'URGENT'"
                class="border border-red-500 text-red-600 font-extrabold text-[10px] px-2 py-0.5 rounded tracking-wider uppercase flex items-center gap-1"
              >
                <Flame :size="10" />
                <span>URGENT</span>
              </span>
              <span
                v-else-if="project.priority === 'HIGH'"
                class="border border-amber-500 text-amber-600 font-extrabold text-[10px] px-2 py-0.5 rounded tracking-wider uppercase flex items-center gap-1"
              >
                <Clock :size="10" />
                <span>HIGH</span>
              </span>
              <span
                v-else
                class="border border-blue-400 text-blue-600 font-extrabold text-[10px] px-2 py-0.5 rounded tracking-wider uppercase"
              >
                MEDIUM
              </span>
            </div>

            <!-- Project ID & System Tag -->
            <div class="flex items-center justify-between text-[11px] font-mono text-[#707a8a]">
              <span>#{{ 64060 + project.id }}</span>
              <span class="font-bold text-[10px] uppercase tracking-wider text-slate-500">GEOSTEVIA</span>
            </div>

            <!-- Title -->
            <div>
              <h2 class="text-base font-extrabold text-[#1f242e] group-hover:text-[#d73f3f] transition-colors line-clamp-2 leading-snug font-heading">
                {{ project.name }}
              </h2>
            </div>

            <!-- Description -->
            <p class="text-xs text-[#555d6b] leading-relaxed line-clamp-3 min-h-[48px]">
              {{ project.description || 'Kawasan pemetaan data latih tutupan lahan citra satelit Sentinel-2 komposit multi-temporal.' }}
            </p>

            <!-- Contributors Count -->
            <div class="text-xs text-[#707a8a] font-medium flex items-center gap-1.5 pt-1">
              <Users :size="13" class="text-slate-400" />
              <span>{{ project.contributors_count || 0 }} total contributors</span>
            </div>

            <!-- Segmented Progress Bar -->
            <div class="space-y-1 pt-1">
              <div class="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden flex">
                <!-- Approved % (Green) -->
                <div
                  class="bg-emerald-500 h-full transition-all duration-300"
                  :style="{ width: `${getApprovedPercent(project)}%` }"
                  :title="`Disetujui: ${getApprovedPercent(project)}%`"
                ></div>
                <!-- In Progress / Submitted % (Red/Coral) -->
                <div
                  class="bg-[#d73f3f] h-full transition-all duration-300"
                  :style="{ width: `${getInProgressPercent(project)}%` }"
                  :title="`Sedang dipetakan/review: ${getInProgressPercent(project)}%`"
                ></div>
              </div>
              <div class="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <span>{{ project.approved_tasks || 0 }} / {{ project.total_tasks || 0 }} Grids</span>
                <span>{{ Math.round((project.approved_tasks || 0) / (project.total_tasks || 1) * 100) }}% Selesai</span>
              </div>
            </div>

          </div>

          <!-- Card Bottom Bar -->
          <div class="px-5 py-3 bg-slate-50/70 border-t border-[#e4e7eb] flex items-center justify-between text-xs text-[#707a8a]">
            <!-- Difficulty -->
            <div class="font-medium text-slate-700 flex items-center gap-1">
              <span class="text-[11px]">{{ project.difficulty || 'Moderate' }}</span>
            </div>

            <!-- Action Button -->
            <div class="flex items-center gap-1 text-xs font-bold text-[#d73f3f] group-hover:translate-x-0.5 transition-transform">
              <span>Mulai Mapping</span>
              <ArrowRight :size="14" />
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Compass,
  Search,
  X,
  Flame,
  Clock,
  RotateCcw,
  Globe,
  Users,
  ArrowRight,
  FolderSearch
} from 'lucide-vue-next'
import { useTasksStore } from '../stores/tasks'

const router = useRouter()
const tasksStore = useTasksStore()

const loading = ref(false)
const searchQuery = ref('')
const selectedPriority = ref('ALL')
const selectedDifficulty = ref('ALL')
const sortBy = ref('id_asc')

onMounted(async () => {
  loading.value = true
  try {
    await tasksStore.fetchProjects()
  } catch (err) {
    console.error('Failed to load projects:', err)
  } finally {
    loading.value = false
  }
})

const projects = computed(() => {
  return tasksStore.projects || []
})

const filteredProjects = computed(() => {
  let list = [...projects.value]

  // Search filter
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(p => 
      p.name.toLowerCase().includes(q) ||
      (p.description && p.description.toLowerCase().includes(q))
    )
  }

  // Priority filter
  if (selectedPriority.value !== 'ALL') {
    list = list.filter(p => p.priority === selectedPriority.value)
  }

  // Difficulty filter
  if (selectedDifficulty.value !== 'ALL') {
    list = list.filter(p => (p.difficulty || 'Moderate') === selectedDifficulty.value)
  }

  // Sorting
  if (sortBy.value === 'tasks_desc') {
    list.sort((a, b) => (b.total_tasks || 0) - (a.total_tasks || 0))
  } else if (sortBy.value === 'contributors_desc') {
    list.sort((a, b) => (b.contributors_count || 0) - (a.contributors_count || 0))
  } else if (sortBy.value === 'progress_desc') {
    list.sort((a, b) => {
      const pA = (a.approved_tasks || 0) / (a.total_tasks || 1)
      const pB = (b.approved_tasks || 0) / (b.total_tasks || 1)
      return pB - pA
    })
  } else {
    list.sort((a, b) => a.id - b.id)
  }

  return list
})

const resetFilters = () => {
  searchQuery.value = ''
  selectedPriority.value = 'ALL'
  selectedDifficulty.value = 'ALL'
  sortBy.value = 'id_asc'
}

const getApprovedPercent = (project) => {
  if (!project.total_tasks) return 0
  return Math.min(100, Math.round(((project.approved_tasks || 0) / project.total_tasks) * 100))
}

const getInProgressPercent = (project) => {
  if (!project.total_tasks) return 0
  const active = (project.in_progress_tasks || 0) + (project.submitted_tasks || 0)
  return Math.min(100 - getApprovedPercent(project), Math.round((active / project.total_tasks) * 100))
}

const selectProject = (project) => {
  // Sets active project in store and navigates to Project Detail instructions
  tasksStore.selectedArea = project.id
  router.push(`/project/${project.id}`)
}
</script>

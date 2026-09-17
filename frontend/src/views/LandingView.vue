<template>
  <div class="min-h-full w-full bg-white text-[#2c3038] font-sans selection:bg-[#d73f3f] selection:text-white">

    <!-- HERO SECTION (High-Impact Satellite Imagery Banner) -->
    <section class="relative bg-[#1a1f2c] text-white min-h-[420px] lg:min-h-[460px] flex items-center overflow-hidden">
      <!-- High-res Satellite Imagery Background -->
      <div
        class="absolute inset-0 bg-cover bg-center opacity-35 mix-blend-luminosity scale-105"
        style="background-image: url('https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=2000&q=80');"
      ></div>
      <div class="absolute inset-0 bg-gradient-to-r from-[#0f131a]/95 via-[#0f131a]/80 to-transparent"></div>

      <!-- Vector polygon annotation overlays -->
      <svg class="absolute right-12 top-12 w-[600px] h-[400px] opacity-30 pointer-events-none hidden lg:block" viewBox="0 0 600 400" fill="none">
        <polygon points="50,40 220,20 270,160 100,190" stroke="#d73f3f" stroke-width="3" fill="#d73f3f" fill-opacity="0.3" />
        <polygon points="240,30 450,60 410,230 280,180" stroke="#ffffff" stroke-width="2.5" fill="#ffffff" fill-opacity="0.15" />
        <polygon points="120,210 300,190 340,360 160,380" stroke="#d73f3f" stroke-width="3" fill="#d73f3f" fill-opacity="0.3" />
        <circle cx="50" cy="40" r="4" fill="#ffffff" />
        <circle cx="220" cy="20" r="4" fill="#ffffff" />
        <circle cx="270" cy="160" r="4" fill="#ffffff" />
        <circle cx="100" cy="190" r="4" fill="#ffffff" />
      </svg>

      <div class="max-w-7xl mx-auto px-6 lg:px-12 py-16 relative z-10 w-full">
        <div class="max-w-xl space-y-5">
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight uppercase leading-none font-heading">
            MAP FOR AI & DEEP LEARNING
          </h1>

          <p class="text-base sm:text-lg text-[#cfd4dc] font-normal leading-relaxed">
            Platform kolaboratif berbasis spasial untuk pembuatan Dataset Ground Truth dan Training Sample Tutupan Lahan menggunakan citra satelit untuk training model kecerdasan buatan (GeoAI).
          </p>

          <div class="pt-2 flex items-center gap-4">
            <router-link
              to="/project/1"
              class="inline-block bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-sm px-6 py-3 rounded-xl transition-all shadow-md uppercase tracking-wider"
            >
              Mulai Memetakan
            </router-link>
            <router-link
              to="/tasking"
              class="inline-block bg-slate-800/80 hover:bg-slate-700 text-white font-bold text-sm px-6 py-3 rounded-xl transition-all border border-slate-600 uppercase tracking-wider"
            >
              Lihat Tasks Grid
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- LIVE STATISTICS BAR -->
    <section class="border-b border-[#e4e7eb] bg-white py-8 px-6 lg:px-12">
      <div class="max-w-7xl mx-auto space-y-4">
        <!-- Disclaimer pill box -->
        <div class="inline-flex items-center gap-2 bg-[#f0f2f5] text-[#555d6b] text-xs px-3 py-1 rounded-lg">
          <Info :size="13" class="text-[#707a8a]" />
          <span>Statistik dataset training sample diperbarui secara real-time dari database spasial</span>
        </div>

        <!-- 5 Big Metric Numbers -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-6 pt-2 text-left md:text-center">
          <div>
            <div class="text-4xl lg:text-5xl font-black text-[#d73f3f] tracking-tight font-heading">
              {{ tasksStore.stats?.total_tasks ? tasksStore.stats.total_tasks.toLocaleString() : '180' }}
            </div>
            <div class="text-xs font-bold text-[#2c3038] uppercase tracking-wider mt-1">Grid Patches (1024px)</div>
          </div>

          <div>
            <div class="text-4xl lg:text-5xl font-black text-[#d73f3f] tracking-tight font-heading">10.24 km</div>
            <div class="text-xs font-bold text-[#2c3038] uppercase tracking-wider mt-1">Ukuran Per Tile</div>
          </div>

          <div>
            <div class="text-4xl lg:text-5xl font-black text-[#d73f3f] tracking-tight font-heading">12</div>
            <div class="text-xs font-bold text-[#2c3038] uppercase tracking-wider mt-1">Kelas Tutupan Lahan</div>
          </div>

          <div>
            <div class="text-4xl lg:text-5xl font-black text-[#d73f3f] tracking-tight font-heading">
              {{ tasksStore.stats?.student_contributions?.length || 0 }}
            </div>
            <div class="text-xs font-bold text-[#2c3038] uppercase tracking-wider mt-1">Kontributor Terdaftar</div>
          </div>

          <div class="col-span-2 md:col-span-1">
            <div class="text-4xl lg:text-5xl font-black text-[#d73f3f] tracking-tight font-heading">
              {{ tasksStore.stats?.approved || 0 }}
            </div>
            <div class="text-xs font-bold text-[#2c3038] uppercase tracking-wider mt-1">Grid Selesai & Lulus QC</div>
          </div>
        </div>
      </div>
    </section>

    <!-- EXPLORE PROJECTS SECTION -->
    <section class="py-12 px-6 lg:px-12 max-w-7xl mx-auto w-full space-y-8">
      <div class="flex items-center justify-between border-b border-[#e4e7eb] pb-4">
        <div>
          <h2 class="text-xl lg:text-2xl font-black text-[#1f242e] uppercase tracking-tight font-heading">Kawasan Prioritas Pemetaan</h2>
          <p class="text-xs text-[#707a8a] mt-0.5">Pilih wilayah kajian untuk membaca petunjuk digitasi dan mulai mengerjakan grid 1024x1024px.</p>
        </div>
        <router-link to="/tasking" class="text-xs font-bold text-[#d73f3f] hover:underline uppercase tracking-wider">
          Buka Peta Tasking Grid →
        </router-link>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        <div
          v-for="(proj, idx) in dynamicProjects"
          :key="proj.id"
          class="border border-[#e4e7eb] rounded-2xl overflow-hidden bg-white hover:border-[#cfd4dc] transition-all flex flex-col justify-between shadow-xs"
        >
          <div class="p-6 space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-[#707a8a]">#{{ 62541 + idx }} | {{ proj.name }}</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded border border-[#f59e0b] text-[#b45309] uppercase tracking-wider">
                Priority: {{ idx === 0 ? 'High' : 'Medium' }}
              </span>
            </div>

            <div>
              <h3 class="text-lg font-black text-[#1f242e] uppercase leading-tight hover:text-[#d73f3f] transition-colors font-heading">
                <router-link :to="`/project/${proj.id}`">{{ proj.name.toUpperCase() }}</router-link>
              </h3>
              <div class="text-xs text-[#707a8a] mt-1">Sentinel-2 Multi-Spectral · {{ proj.total_tasks?.toLocaleString() || 0 }} Grid Patches (1024px)</div>
            </div>

            <p class="text-xs text-[#555d6b] leading-relaxed line-clamp-3">
              {{ proj.description || 'Platform kolaboratif anotasi citra satelit tutupan lahan untuk pembuatan ground truth AI.' }}
            </p>

            <!-- Types of mapping icons -->
            <div class="pt-2">
              <div class="text-[10px] font-bold text-[#707a8a] uppercase tracking-wider mb-1.5">Kategori Objek</div>
              <div class="flex items-center gap-3 text-base text-[#555d6b]">
                <Trees :size="18" class="text-emerald-600" title="Vegetasi & Hutan" />
                <Droplets :size="18" class="text-cyan-600" title="Tubuh Air" />
                <Building2 :size="18" class="text-rose-600" title="Bangunan" />
                <Wheat :size="18" class="text-amber-600" title="Pertanian & Sawah" />
              </div>
            </div>

            <!-- Progress line -->
            <div class="space-y-1 pt-2">
              <div class="flex justify-between text-xs font-bold text-[#2c3038]">
                <span>Progress Pemetaan</span>
                <span class="text-emerald-600 font-mono">
                  {{ proj.total_tasks > 0 ? Math.round((proj.approved_tasks / proj.total_tasks) * 100) : 0 }}% Selesai
                </span>
              </div>
              <div class="w-full h-2 bg-[#e4e7eb] rounded-full overflow-hidden flex">
                <div
                  class="bg-[#10b981] h-full"
                  :style="{ width: `${proj.total_tasks > 0 ? (proj.approved_tasks / proj.total_tasks) * 100 : 0}%` }"
                ></div>
                <div
                  class="bg-[#ea580c] h-full"
                  :style="{ width: `${proj.total_tasks > 0 ? (proj.in_progress_tasks / proj.total_tasks) * 100 : 0}%` }"
                ></div>
              </div>
            </div>
          </div>

          <div class="bg-[#f8f9fa] border-t border-[#e4e7eb] px-6 py-3.5 flex items-center justify-between">
            <span class="text-xs text-[#707a8a]"><b>{{ proj.total_tasks?.toLocaleString() || 0 }}</b> Grid Tiles (1024px)</span>
            <router-link
              :to="`/project/${proj.id}`"
              class="bg-[#d73f3f] hover:bg-[#c23434] text-white text-xs font-bold px-4 py-2 rounded-xl transition-colors uppercase tracking-wider"
            >
              Lihat Petunjuk & Mulai
            </router-link>
          </div>
        </div>

      </div>
    </section>

    <!-- LEADERBOARD PREVIEW SECTION -->
    <section class="py-10 px-6 lg:px-12 bg-slate-50 border-t border-[#e4e7eb]">
      <div class="max-w-7xl mx-auto space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 class="text-xl lg:text-2xl font-black text-[#1f242e] uppercase tracking-tight font-heading flex items-center gap-2">
              <Trophy :size="22" class="text-amber-500" />
              <span>Klasemen Kontributor Teratas</span>
            </h2>
            <p class="text-xs text-[#707a8a]">Aktivitas digitasi kontributor / mappers terdepan dalam pembuatan data latih.</p>
          </div>
          <router-link
            to="/dashboard"
            class="text-xs font-bold text-[#d73f3f] hover:underline uppercase tracking-wider flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Buka Leaderboard Lengkap</span>
            <ArrowRight :size="12" />
          </router-link>
        </div>

        <!-- Top 3 Podium Cards (from API) -->
        <div v-if="topThree.length > 0" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div
            v-for="(s, idx) in topThree"
            :key="s.user_id || idx"
            class="p-4 bg-white border border-[#e4e7eb] rounded-2xl flex items-center justify-between shadow-2xs hover:border-[#cfd4dc] transition-all"
          >
            <div class="flex items-center gap-3">
              <span class="text-2xl">{{ ['🥇','🥈','🥉'][idx] }}</span>
              <div>
                <div class="font-bold text-sm text-slate-900">{{ s.name }}</div>
                <div class="text-xs text-emerald-600 font-medium">{{ s.approved_tasks || 0 }} Grid Disetujui</div>
              </div>
            </div>
            <div class="text-right">
              <div class="font-black text-sm text-purple-700 font-mono">{{ s.total_polygons || 0 }}</div>
              <div class="text-[10px] text-slate-400 uppercase font-bold">Poligon</div>
            </div>
          </div>
        </div>

        <!-- Clean empty state if no annotations exist yet -->
        <div v-else class="p-8 bg-white border border-dashed border-slate-300 rounded-2xl text-center space-y-2">
          <div class="text-slate-400 text-sm font-medium">Belum ada kontribusi digitasi yang disetujui.</div>
          <p class="text-xs text-slate-500">Mulai ambil grid di halaman Tasking Grid untuk menjadi kontributor pertama!</p>
        </div>
      </div>
    </section>

    <!-- FOOTER (Adapted for STEVI Task Manager) -->
    <footer class="bg-[#1f242e] text-[#cfd4dc] py-8 px-6 lg:px-12 border-t border-[#2d3442] text-xs mt-auto">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="flex items-center gap-3">
          <img
            src="https://koboegis.app/klh-logo.png?v=2026|g"
            alt="STEVI Logo"
            class="h-8 w-auto object-contain"
          />
          <div>
            <div class="text-white font-bold text-sm font-heading">STEVI Task Manager</div>
            <div class="text-[11px] text-[#8c96a5]">Platform Kolaborasi Pembuatan Training Sample</div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-6 text-xs text-[#8c96a5]">
          <router-link to="/project/1" class="hover:text-white transition-colors">Petunjuk</router-link>
          <router-link to="/tasking" class="hover:text-white transition-colors">Tasking Grid</router-link>
          <router-link to="/map" class="hover:text-white transition-colors">Studio GIS</router-link>
          <router-link to="/dashboard" class="hover:text-white transition-colors">Leaderboard</router-link>
          <router-link to="/export" class="hover:text-white transition-colors">Ekspor Dataset</router-link>
        </div>

        <div class="text-[#8c96a5] text-center md:text-right">
          <div>© 2026 STEVI Task Manager</div>
          <div class="text-xs text-[#616b7c] mt-0.5">Powered by GeoAI Training System & STEVI Grid Engine</div>
        </div>
      </div>
    </footer>

  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import {
  Info,
  Trees,
  Droplets,
  Building2,
  Wheat,
  Trophy,
  ArrowRight
} from 'lucide-vue-next'
import { useTasksStore } from '../stores/tasks'

const tasksStore = useTasksStore()

const dynamicProjects = computed(() => {
  return tasksStore.projects || []
})

const topThree = computed(() => {
  const list = tasksStore.stats?.student_contributions || []
  return list.filter(item => item.total_polygons > 0 || item.approved_tasks > 0).slice(0, 3)
})

onMounted(async () => {
  try {
    await Promise.allSettled([
      tasksStore.fetchProjects(),
      tasksStore.fetchStatsSummary()
    ])
  } catch (e) {
    // handled gracefully
  }
})
</script>

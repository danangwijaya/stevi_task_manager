<template>
  <div class="min-h-full bg-slate-50 text-slate-800 font-sans p-6 lg:p-10 space-y-8 max-w-7xl mx-auto">
    
    <!-- Welcome Header & Quick Action -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-6 lg:p-8 rounded-3xl shadow-sm relative overflow-hidden">
      <div class="space-y-1.5 z-10">
        <div class="flex items-center gap-3 flex-wrap">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight font-heading">
            Dashboard & Leaderboard Tim
          </h1>
          <span
            class="text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider border shadow-2xs flex items-center gap-1.5"
            :class="authStore.isAdmin 
              ? 'bg-amber-50 text-amber-800 border-amber-300' 
              : 'bg-rose-50 text-rose-700 border-rose-200'"
          >
            <ShieldCheck v-if="authStore.isAdmin" :size="14" class="text-amber-600" />
            <GraduationCap v-else :size="14" class="text-rose-600" />
            <span>{{ authStore.isAdmin ? 'Lead Administrator (QC)' : 'Kontributor / Mapper' }}</span>
          </span>
        </div>
        <p class="text-sm text-slate-500 max-w-2xl leading-relaxed">
          Monitoring progres pengerjaan data latih, persetujuan mutu digitasi, dan peringkat kontribusi mapper.
        </p>
      </div>

      <div class="flex items-center gap-3 z-10 flex-wrap">
        <router-link
          to="/tasking"
          class="bg-[#d73f3f] hover:bg-[#c23434] text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md shadow-rose-500/20 flex items-center gap-2 transition-all uppercase tracking-wider cursor-pointer"
        >
          <Grid :size="14" />
          <span>Buka Tasking Grid</span>
        </router-link>
        <router-link
          to="/map"
          class="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-bold px-4 py-2.5 rounded-xl flex items-center gap-2 transition-all shadow-xs uppercase tracking-wider cursor-pointer"
        >
          <Shapes :size="14" class="text-rose-600" />
          <span>Studio Digitasi</span>
        </router-link>
      </div>
    </div>

    <!-- 5 Big Stat Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div class="bg-white border border-slate-200 p-5 rounded-2xl shadow-xs">
        <div class="text-slate-500 text-xs font-bold uppercase tracking-wider flex items-center justify-between">
          <span>Total Grid Patch</span>
          <Grid :size="18" class="text-slate-400" />
        </div>
        <div class="text-3xl font-black text-slate-900 mt-2 font-heading">{{ tasksStore.stats?.total_tasks || 0 }}</div>
        <div class="text-xs text-slate-500 mt-0.5 font-medium">Patch 1024px × 1024px</div>
      </div>

      <div class="bg-white border border-emerald-200 p-5 rounded-2xl shadow-xs bg-emerald-50/20">
        <div class="text-emerald-700 text-xs font-bold uppercase tracking-wider flex items-center justify-between">
          <span>Disetujui (Approved)</span>
          <CheckCircle2 :size="18" class="text-emerald-600" />
        </div>
        <div class="text-3xl font-black text-emerald-600 mt-2 font-heading">{{ tasksStore.stats?.approved || 0 }}</div>
        <div class="text-xs text-emerald-700/80 mt-0.5 font-semibold">Siap Ekspor Data Latih</div>
      </div>

      <div class="bg-white border border-orange-200 p-5 rounded-2xl shadow-xs bg-orange-50/20">
        <div class="text-orange-700 text-xs font-bold uppercase tracking-wider flex items-center justify-between">
          <span>Menunggu Review</span>
          <Clock :size="18" class="text-orange-600" />
        </div>
        <div class="text-3xl font-black text-orange-600 mt-2 font-heading">{{ tasksStore.stats?.submitted || 0 }}</div>
        <div class="text-xs text-orange-700/80 mt-0.5 font-semibold">Perlu dicek Reviewer QC</div>
      </div>

      <div class="bg-white border border-amber-200 p-5 rounded-2xl shadow-xs bg-amber-50/20">
        <div class="text-amber-700 text-xs font-bold uppercase tracking-wider flex items-center justify-between">
          <span>Dalam Pengerjaan</span>
          <PenTool :size="18" class="text-amber-600" />
        </div>
        <div class="text-3xl font-black text-amber-600 mt-2 font-heading">{{ tasksStore.stats?.in_progress || 0 }}</div>
        <div class="text-xs text-amber-700/80 mt-0.5 font-semibold">Sedang didigitasi</div>
      </div>

      <div class="bg-white border border-purple-200 p-5 rounded-2xl shadow-xs bg-purple-50/20">
        <div class="text-purple-700 text-xs font-bold uppercase tracking-wider flex items-center justify-between">
          <span>Total Poligon</span>
          <Shapes :size="18" class="text-purple-600" />
        </div>
        <div class="text-3xl font-black text-purple-600 mt-2 font-heading">{{ tasksStore.stats?.total_polygons || 0 }}</div>
        <div class="text-xs text-purple-700/80 mt-0.5 font-semibold">12 Kelas Tutupan Lahan</div>
      </div>
    </div>

    <!-- LEADERBOARD SECTION (Dedicated Full-Width Visual Ranking) -->
    <div class="bg-white border border-slate-200 rounded-3xl p-6 lg:p-8 shadow-sm space-y-6">
      
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
        <div>
          <h2 class="text-xl font-black text-slate-900 tracking-tight font-heading flex items-center gap-2.5">
            <Trophy :size="22" class="text-amber-500" />
            <span>Peringkat Kontribusi Mapper</span>
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">Klasemen real-time berdasarkan jumlah poligon terdigitasi dan grid yang disetujui reviewer.</p>
        </div>
        <span class="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-full font-bold self-start sm:self-auto">
          ● Live Tracking Aktif
        </span>
      </div>

      <!-- Top 3 Podium Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        
        <!-- Rank 2: Silver -->
        <div v-if="tasksStore.stats?.student_contributions?.[1]" class="bg-gradient-to-b from-slate-100/80 to-white border border-slate-300 rounded-2xl p-5 text-center flex flex-col items-center justify-between relative shadow-xs order-2 md:order-1">
          <div class="w-10 h-10 rounded-full bg-slate-200 border-2 border-slate-400 flex items-center justify-center font-black text-slate-700 text-base shadow-sm">
            🥈
          </div>
          <div class="mt-3">
            <div class="font-extrabold text-base text-slate-900">{{ tasksStore.stats.student_contributions[1].name }}</div>
            <div class="text-xs text-slate-500 font-mono">Peringkat 2</div>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-200 w-full flex items-center justify-around text-xs">
            <div>
              <div class="font-black text-sm text-slate-800 font-mono">{{ tasksStore.stats.student_contributions[1].total_polygons }}</div>
              <div class="text-[10px] text-slate-500 uppercase">Poligon</div>
            </div>
            <div>
              <div class="font-black text-sm text-emerald-600 font-mono">{{ tasksStore.stats.student_contributions[1].approved_tasks }}</div>
              <div class="text-[10px] text-slate-500 uppercase">Approved</div>
            </div>
          </div>
        </div>

        <!-- Rank 1: Gold (Champion) -->
        <div v-if="tasksStore.stats?.student_contributions?.[0]" class="bg-gradient-to-b from-amber-50 to-white border-2 border-amber-400 rounded-2xl p-6 text-center flex flex-col items-center justify-between relative shadow-md order-1 md:order-2">
          <span class="absolute -top-3 bg-amber-500 text-white font-extrabold text-[10px] uppercase tracking-wider px-3 py-0.5 rounded-full shadow-sm">
            Top Contributor
          </span>
          <div class="w-12 h-12 rounded-full bg-amber-100 border-2 border-amber-500 flex items-center justify-center font-black text-amber-700 text-xl shadow-sm mt-1">
            👑
          </div>
          <div class="mt-3">
            <div class="font-black text-lg text-slate-900 font-heading">{{ tasksStore.stats.student_contributions[0].name }}</div>
            <div class="text-xs text-amber-700 font-bold">Juara 1 Klasemen</div>
          </div>
          <div class="mt-4 pt-3 border-t border-amber-200/60 w-full flex items-center justify-around text-xs">
            <div>
              <div class="font-black text-base text-purple-700 font-mono">{{ tasksStore.stats.student_contributions[0].total_polygons }}</div>
              <div class="text-[10px] text-slate-500 uppercase">Poligon</div>
            </div>
            <div>
              <div class="font-black text-base text-emerald-600 font-mono">{{ tasksStore.stats.student_contributions[0].approved_tasks }}</div>
              <div class="text-[10px] text-slate-500 uppercase">Approved</div>
            </div>
          </div>
        </div>

        <!-- Rank 3: Bronze -->
        <div v-if="tasksStore.stats?.student_contributions?.[2]" class="bg-gradient-to-b from-amber-50/50 to-white border border-amber-300 rounded-2xl p-5 text-center flex flex-col items-center justify-between relative shadow-xs order-3 md:order-3">
          <div class="w-10 h-10 rounded-full bg-amber-100 border-2 border-amber-400 flex items-center justify-center font-black text-amber-800 text-base shadow-sm">
            🥉
          </div>
          <div class="mt-3">
            <div class="font-extrabold text-base text-slate-900">{{ tasksStore.stats.student_contributions[2].name }}</div>
            <div class="text-xs text-slate-500 font-mono">Peringkat 3</div>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-200 w-full flex items-center justify-around text-xs">
            <div>
              <div class="font-black text-sm text-slate-800 font-mono">{{ tasksStore.stats.student_contributions[2].total_polygons }}</div>
              <div class="text-[10px] text-slate-500 uppercase">Poligon</div>
            </div>
            <div>
              <div class="font-black text-sm text-emerald-600 font-mono">{{ tasksStore.stats.student_contributions[2].approved_tasks }}</div>
              <div class="text-[10px] text-slate-500 uppercase">Approved</div>
            </div>
          </div>
        </div>

      </div>

      <!-- Complete Leaderboard Table -->
      <div class="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-2xs">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th class="p-3.5 text-center w-14">Rank</th>
                <th class="p-3.5">Nama Kontributor / Mapper</th>
                <th class="p-3.5 text-center">Tugas Diambil</th>
                <th class="p-3.5 text-center">Menunggu Review</th>
                <th class="p-3.5 text-center">Disetujui (Approved)</th>
                <th class="p-3.5 text-right pr-6">Total Poligon</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="(student, idx) in tasksStore.stats?.student_contributions"
                :key="student.user_id"
                class="hover:bg-slate-50 transition-colors"
                :class="idx < 3 ? 'bg-amber-50/20 font-medium' : ''"
              >
                <td class="p-3.5 text-center font-bold font-mono text-xs">
                  <span v-if="idx === 0">🥇 1</span>
                  <span v-else-if="idx === 1">🥈 2</span>
                  <span v-else-if="idx === 2">🥉 3</span>
                  <span v-else class="text-slate-400">#{{ idx + 1 }}</span>
                </td>
                <td class="p-3.5 font-bold text-slate-900 text-sm">
                  {{ student.name }}
                </td>
                <td class="p-3.5 text-center font-mono font-medium text-slate-600">
                  {{ student.assigned_tasks }}
                </td>
                <td class="p-3.5 text-center font-mono font-bold text-orange-600">
                  {{ student.submitted_tasks }}
                </td>
                <td class="p-3.5 text-center font-mono font-bold text-emerald-600">
                  {{ student.approved_tasks }}
                </td>
                <td class="p-3.5 text-right pr-6 font-mono font-black text-purple-700 text-sm">
                  {{ student.total_polygons }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import {
  ShieldCheck,
  GraduationCap,
  Grid,
  Shapes,
  CheckCircle2,
  Clock,
  PenTool,
  Trophy
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'

const authStore = useAuthStore()
const tasksStore = useTasksStore()

onMounted(async () => {
  await tasksStore.fetchStatsSummary()
  await tasksStore.fetchTasks()
})
</script>


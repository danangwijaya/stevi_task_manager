<template>
  <div class="space-y-5">
    <!-- Header & Action Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/80 shadow-xs">
      <div>
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 text-teal-700 flex items-center justify-center shadow-xs shrink-0">
            <FileSpreadsheet :size="20" />
          </div>
          <div>
            <h2 class="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Rekap Monitoring Progres Anotasi</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-teal-100 text-teal-800 border border-teal-200">
                Sinkron Real-time
              </span>
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">
              Monitoring status tugas per kontributor, verifikasi QC berjenjang (QC 1, QC 2), dan finishing dataset.
            </p>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap items-center gap-2">
        <button
          type="button"
          @click="fetchData"
          :disabled="loading"
          class="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50"
          title="Muat Ulang Data Terbaru"
        >
          <RefreshCw :size="13" :class="{ 'animate-spin': loading }" />
          <span>Refresh</span>
        </button>

        <button
          type="button"
          @click="handleExportCsv"
          :disabled="downloadingCsv || loading"
          class="px-3 py-1.5 rounded-xl border border-slate-300 hover:bg-slate-100 bg-white text-slate-800 text-xs font-bold flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer disabled:opacity-50"
          title="Download Rekap Format CSV"
        >
          <Download :size="13" />
          <span>{{ downloadingCsv ? 'Mengunduh...' : 'Unduh CSV' }}</span>
        </button>

        <button
          type="button"
          @click="handleExportExcel"
          :disabled="downloadingExcel || loading"
          class="px-3.5 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm shadow-emerald-700/20 cursor-pointer disabled:opacity-50"
          title="Download Template Rekap Format Microsoft Excel (.xlsx)"
        >
          <FileSpreadsheet :size="14" />
          <span>{{ downloadingExcel ? 'Membuat File Excel...' : 'Unduh Excel (.xlsx)' }}</span>
        </button>
      </div>
    </div>

    <!-- KPI Summary Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
      <div class="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs">
        <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Kontributor</div>
        <div class="text-lg font-black text-slate-900 mt-0.5 flex items-baseline gap-1">
          <span>{{ summary.total_mappers }}</span>
          <span class="text-[10px] font-medium text-slate-400">Orang</span>
        </div>
        <div class="text-[9px] text-slate-400">Aktif di proyek</div>
      </div>

      <div class="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs">
        <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Grid</div>
        <div class="text-lg font-black text-slate-900 mt-0.5 flex items-baseline gap-1">
          <span>{{ summary.total_grids }}</span>
          <span class="text-[10px] font-medium text-slate-400">Unit</span>
        </div>
        <div class="text-[9px] text-slate-400">Grid ditugaskan</div>
      </div>

      <div class="bg-white p-3 rounded-xl border border-amber-200/80 bg-amber-50/20 shadow-2xs">
        <div class="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Dalam Proses</div>
        <div class="text-lg font-black text-amber-900 mt-0.5 flex items-baseline gap-1">
          <span>{{ summary.in_progress_count }}</span>
          <span class="text-[10px] font-medium text-amber-700">Grid</span>
        </div>
        <div class="text-[9px] text-amber-600/80">Sedang dikerjakan</div>
      </div>

      <div class="bg-white p-3 rounded-xl border border-sky-200/80 bg-sky-50/20 shadow-2xs">
        <div class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Review QC</div>
        <div class="text-lg font-black text-sky-900 mt-0.5 flex items-baseline gap-1">
          <span>{{ summary.review_qc_count }}</span>
          <span class="text-[10px] font-medium text-sky-700">Grid</span>
        </div>
        <div class="text-[9px] text-sky-600/80">Menunggu validasi</div>
      </div>

      <div class="bg-white p-3 rounded-xl border border-indigo-200/80 bg-indigo-50/20 shadow-2xs">
        <div class="text-[10px] font-bold text-indigo-700 uppercase tracking-wider">QC 1 (Approved)</div>
        <div class="text-lg font-black text-indigo-900 mt-0.5 flex items-baseline gap-1">
          <span>{{ summary.qc1_count }}</span>
          <span class="text-[10px] font-medium text-indigo-700">Grid</span>
        </div>
        <div class="text-[9px] text-indigo-600/80">Lolos tahap 1</div>
      </div>

      <div class="bg-white p-3 rounded-xl border border-purple-200/80 bg-purple-50/20 shadow-2xs">
        <div class="text-[10px] font-bold text-purple-700 uppercase tracking-wider">QC 2 (Approved)</div>
        <div class="text-lg font-black text-purple-900 mt-0.5 flex items-baseline gap-1">
          <span>{{ summary.qc2_count }}</span>
          <span class="text-[10px] font-medium text-purple-700">Grid</span>
        </div>
        <div class="text-[9px] text-purple-600/80">Lolos tahap 2</div>
      </div>

      <div class="bg-white p-3 rounded-xl border border-emerald-300 bg-emerald-50/30 shadow-2xs">
        <div class="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">Finishing Selesai</div>
        <div class="text-lg font-black text-emerald-900 mt-0.5 flex items-baseline gap-1">
          <span>{{ summary.finishing_count }}</span>
          <span class="text-[10px] font-medium text-emerald-700">Grid</span>
        </div>
        <div class="text-[9px] text-emerald-600/90 font-semibold">{{ summary.completion_percentage }}% selesai</div>
      </div>
    </div>

    <!-- Filter Controls Bar -->
    <div class="bg-white p-3.5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Wilayah Filter -->
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-bold text-slate-600 flex items-center gap-1">
            <MapPin :size="13" class="text-slate-400" />
            <span>Wilayah:</span>
          </label>
          <select
            v-model="filters.study_area_id"
            @change="fetchData"
            class="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer"
          >
            <option :value="null">Semua Wilayah Spasial</option>
            <option v-for="sa in studyAreas" :key="sa.id" :value="sa.id">
              {{ sa.name }}
            </option>
          </select>
        </div>

        <!-- Tahun Filter -->
        <div class="flex items-center gap-1.5">
          <label class="text-xs font-bold text-slate-600 flex items-center gap-1">
            <Calendar :size="13" class="text-slate-400" />
            <span>Tahun:</span>
          </label>
          <select
            v-model="filters.year"
            @change="fetchData"
            class="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer"
          >
            <option :value="null">Semua Tahun</option>
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
      </div>

      <!-- Search Input -->
      <div class="relative w-full sm:w-64">
        <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
        <input
          type="text"
          v-model="filters.search"
          @input="handleSearchDebounced"
          placeholder="Cari nama, NIM, atau nomor grid..."
          class="w-full text-xs pl-8 pr-7 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-500 text-slate-800 placeholder-slate-400"
        />
        <button
          v-if="filters.search"
          @click="filters.search = ''; fetchData()"
          class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Spreadsheet-Style Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
      <div class="overflow-x-auto max-h-[650px]">
        <table class="w-full text-left text-xs border-collapse">
          <!-- Header Level 1 & 2 -->
          <thead class="sticky top-0 z-10 bg-slate-900 text-white font-bold select-none shadow-xs">
            <tr class="text-[11px] border-b border-slate-700">
              <th rowspan="2" class="px-4 py-2.5 border-r border-slate-800 w-[210px]">Nama</th>
              <th rowspan="2" class="px-3 py-2.5 border-r border-slate-800 text-center w-[150px]">NIM</th>
              <th rowspan="2" class="px-2 py-2.5 border-r border-slate-800 text-center w-[50px]">L/P</th>
              <th rowspan="2" class="px-3 py-2.5 border-r border-slate-800 w-[190px]">Program Studi</th>
              <th colspan="2" class="px-3 py-1.5 border-r border-slate-800 text-center bg-teal-800/90 text-teal-100">
                {{ selectedAreaName }}
              </th>
              <th rowspan="2" class="px-3 py-2.5 border-r border-slate-800 text-center w-[110px]">
                Status Dalam Proses
              </th>
              <th rowspan="2" class="px-3 py-2.5 border-r border-slate-800 text-center w-[110px]">
                Status Review QC
              </th>
              <th rowspan="2" class="px-3 py-2.5 border-r border-slate-800 text-center w-[110px]">
                QC 1 (Approved)
              </th>
              <th rowspan="2" class="px-3 py-2.5 border-r border-slate-800 text-center w-[110px]">
                QC 2 (Approved)
              </th>
              <th rowspan="2" class="px-3 py-2.5 border-r border-slate-800 text-center w-[130px]">
                Finishing<br>
                <span class="text-[9px] font-normal text-slate-300">(Mas Danang & Habib)</span>
              </th>
              <th rowspan="2" class="px-4 py-2.5 border-r border-slate-800 w-[170px]">Keterangan</th>
              <th rowspan="2" class="px-3 py-2.5 text-center w-[80px]">Aksi</th>
            </tr>
            <tr class="text-[10px] bg-slate-800 text-slate-200 border-b border-slate-700">
              <th class="px-2.5 py-1.5 border-r border-slate-700 text-center w-[65px]">GRID</th>
              <th class="px-2.5 py-1.5 border-r border-slate-700 text-center w-[55px]">Tahun</th>
            </tr>
          </thead>

          <!-- Table Body -->
          <tbody v-if="!loading && records.length > 0" class="divide-y divide-slate-200/80">
            <template v-for="(rec, rIdx) in records" :key="rec.user_id">
              <tr
                v-for="(g, gIdx) in rec.grids"
                :key="g.task_id"
                class="hover:bg-slate-50/80 transition-colors"
                :class="[
                  gIdx === 0 && rIdx > 0 ? 'border-t-2 border-slate-300' : '',
                  rIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50/30'
                ]"
              >
                <!-- Student Grouped Info (Rowspan on first grid) -->
                <td
                  v-if="gIdx === 0"
                  :rowspan="rec.grids.length"
                  class="px-4 py-2.5 align-top border-r border-slate-200 font-bold text-slate-900 bg-white"
                >
                  <div class="flex items-start gap-2">
                    <div class="w-6 h-6 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center font-extrabold text-[11px] text-slate-700 shrink-0 mt-0.5">
                      {{ rec.nama.charAt(0) }}
                    </div>
                    <div>
                      <div class="font-bold text-slate-900 leading-tight">{{ rec.nama }}</div>
                      <div class="text-[10px] text-slate-400 font-mono mt-0.5">{{ rec.email }}</div>
                      <div class="mt-1">
                        <span class="text-[10px] font-semibold px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded">
                          {{ rec.grids.length }} Grid Ditugaskan
                        </span>
                      </div>
                    </div>
                  </div>
                </td>

                <td
                  v-if="gIdx === 0"
                  :rowspan="rec.grids.length"
                  class="px-3 py-2.5 align-top border-r border-slate-200 text-center font-mono text-[11px] text-slate-600 bg-white"
                >
                  {{ rec.nim }}
                </td>

                <td
                  v-if="gIdx === 0"
                  :rowspan="rec.grids.length"
                  class="px-2 py-2.5 align-top border-r border-slate-200 text-center font-bold text-slate-700 bg-white"
                >
                  <span
                    class="px-1.5 py-0.2 rounded text-[10px]"
                    :class="rec.gender === 'L' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-rose-50 text-rose-700 border border-rose-200'"
                  >
                    {{ rec.gender }}
                  </span>
                </td>

                <td
                  v-if="gIdx === 0"
                  :rowspan="rec.grids.length"
                  class="px-3 py-2.5 align-top border-r border-slate-200 text-slate-700 text-xs bg-white"
                >
                  <div class="font-medium text-slate-800 leading-tight">{{ rec.prodi }}</div>
                  <div class="text-[10px] text-slate-400 mt-0.5">{{ rec.institution }}</div>
                </td>

                <!-- Grid Columns -->
                <td class="px-2.5 py-2 border-r border-slate-200 text-center font-mono font-bold text-slate-900">
                  <span class="px-2 py-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200 text-xs">
                    {{ g.grid_number || g.grid_code }}
                  </span>
                </td>

                <td class="px-2.5 py-2 border-r border-slate-200 text-center font-mono text-slate-600 text-[11px]">
                  {{ g.year }}
                </td>

                <!-- Status Dalam Proses -->
                <td class="px-3 py-2 border-r border-slate-200 text-center">
                  <span
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="g.in_progress ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-slate-100 text-slate-400'"
                  >
                    <Check v-if="g.in_progress" :size="11" />
                    <span>{{ g.in_progress ? 'TRUE' : 'FALSE' }}</span>
                  </span>
                </td>

                <!-- Status Review QC -->
                <td class="px-3 py-2 border-r border-slate-200 text-center">
                  <span
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="g.review_qc ? 'bg-sky-100 text-sky-800 border border-sky-300' : 'bg-slate-100 text-slate-400'"
                  >
                    <Check v-if="g.review_qc" :size="11" />
                    <span>{{ g.review_qc ? 'TRUE' : 'FALSE' }}</span>
                  </span>
                </td>

                <!-- QC 1 (Approved) -->
                <td class="px-3 py-2 border-r border-slate-200 text-center">
                  <button
                    v-if="canReview"
                    type="button"
                    @click="toggleStage(g, 'qc1_approved')"
                    :disabled="g.updating"
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold cursor-pointer transition-all hover:scale-105 active:scale-95"
                    :class="g.qc1_approved ? 'bg-indigo-100 text-indigo-800 border border-indigo-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-400'"
                    :title="g.qc1_approved ? 'Klik untuk membatalkan QC 1' : 'Klik untuk menyetujui QC 1'"
                  >
                    <Check v-if="g.qc1_approved" :size="11" />
                    <span>{{ g.qc1_approved ? 'TRUE' : 'FALSE' }}</span>
                  </button>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="g.qc1_approved ? 'bg-indigo-100 text-indigo-800 border border-indigo-300' : 'bg-slate-100 text-slate-400'"
                  >
                    <Check v-if="g.qc1_approved" :size="11" />
                    <span>{{ g.qc1_approved ? 'TRUE' : 'FALSE' }}</span>
                  </span>
                </td>

                <!-- QC 2 (Approved) -->
                <td class="px-3 py-2 border-r border-slate-200 text-center">
                  <button
                    v-if="canReview"
                    type="button"
                    @click="toggleStage(g, 'qc2_approved')"
                    :disabled="g.updating"
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold cursor-pointer transition-all hover:scale-105 active:scale-95"
                    :class="g.qc2_approved ? 'bg-purple-100 text-purple-800 border border-purple-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-400'"
                    :title="g.qc2_approved ? 'Klik untuk membatalkan QC 2' : 'Klik untuk menyetujui QC 2'"
                  >
                    <Check v-if="g.qc2_approved" :size="11" />
                    <span>{{ g.qc2_approved ? 'TRUE' : 'FALSE' }}</span>
                  </button>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="g.qc2_approved ? 'bg-purple-100 text-purple-800 border border-purple-300' : 'bg-slate-100 text-slate-400'"
                  >
                    <Check v-if="g.qc2_approved" :size="11" />
                    <span>{{ g.qc2_approved ? 'TRUE' : 'FALSE' }}</span>
                  </span>
                </td>

                <!-- Finishing (Mas Danang & Mas Habib) -->
                <td class="px-3 py-2 border-r border-slate-200 text-center">
                  <button
                    v-if="canReview"
                    type="button"
                    @click="toggleStage(g, 'finishing_approved')"
                    :disabled="g.updating"
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold cursor-pointer transition-all hover:scale-105 active:scale-95"
                    :class="g.finishing_approved ? 'bg-emerald-600 text-white border border-emerald-700 shadow-xs' : 'bg-slate-100 hover:bg-slate-200 text-slate-400'"
                    :title="g.finishing_approved ? 'Klik untuk membatalkan Finishing' : 'Klik untuk menandai Finishing Selesai'"
                  >
                    <Check v-if="g.finishing_approved" :size="11" />
                    <span>{{ g.finishing_approved ? 'TRUE' : 'FALSE' }}</span>
                  </button>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="g.finishing_approved ? 'bg-emerald-600 text-white border border-emerald-700 shadow-xs' : 'bg-slate-100 text-slate-400'"
                  >
                    <Check v-if="g.finishing_approved" :size="11" />
                    <span>{{ g.finishing_approved ? 'TRUE' : 'FALSE' }}</span>
                  </span>
                </td>

                <!-- Keterangan -->
                <td class="px-4 py-2 border-r border-slate-200 text-slate-600 text-xs">
                  <div v-if="editingNoteTaskId === g.task_id" class="flex items-center gap-1.5">
                    <input
                      type="text"
                      v-model="editingNoteValue"
                      @keydown.enter="saveNote(g)"
                      @keydown.esc="editingNoteTaskId = null"
                      class="text-xs px-2 py-1 border border-teal-500 rounded bg-white w-full focus:outline-none"
                      autofocus
                    />
                    <button @click="saveNote(g)" class="text-emerald-600 hover:text-emerald-800 text-xs font-bold">✓</button>
                    <button @click="editingNoteTaskId = null" class="text-slate-400 hover:text-slate-600 text-xs">✕</button>
                  </div>
                  <div
                    v-else
                    @dblclick="canReview ? startEditNote(g) : null"
                    class="flex items-center justify-between group min-h-[20px]"
                    :title="canReview ? 'Klik dua kali untuk edit keterangan' : ''"
                  >
                    <span class="truncate max-w-[140px]">{{ g.keterangan || '-' }}</span>
                    <button
                      v-if="canReview"
                      @click="startEditNote(g)"
                      class="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-700 text-[10px] p-0.5"
                    >
                      <Edit3 :size="10" />
                    </button>
                  </div>
                </td>

                <!-- Aksi: Buka di Peta -->
                <td class="px-3 py-2 text-center">
                  <router-link
                    :to="`/map?task_id=${g.task_id}`"
                    class="inline-flex items-center gap-1 text-[11px] font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 border border-teal-200 px-2 py-0.5 rounded transition-colors"
                    title="Buka kanvas digitasi peta grid ini"
                  >
                    <MapPin :size="11" />
                    <span>Peta</span>
                  </router-link>
                </td>
              </tr>
            </template>
          </tbody>

          <!-- Loading State -->
          <tbody v-else-if="loading">
            <tr>
              <td colspan="13" class="px-6 py-12 text-center text-slate-500">
                <div class="flex flex-col items-center justify-center gap-2">
                  <RefreshCw :size="20" class="animate-spin text-teal-600" />
                  <span class="text-xs font-semibold text-slate-700">Mengambil data rekapitulasi progres...</span>
                </div>
              </td>
            </tr>
          </tbody>

          <!-- Empty State -->
          <tbody v-else>
            <tr>
              <td colspan="13" class="px-6 py-12 text-center text-slate-500">
                <div class="flex flex-col items-center justify-center gap-2">
                  <AlertCircle :size="26" class="text-slate-300" />
                  <div class="text-xs font-bold text-slate-700">Tidak ada data ditemukan</div>
                  <div class="text-[11px] text-slate-400">Silakan sesuaikan filter wilayah, tahun, atau kata kunci pencarian.</div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  FileSpreadsheet,
  Download,
  RefreshCw,
  MapPin,
  Calendar,
  Search,
  Check,
  Edit3,
  AlertCircle
} from 'lucide-vue-next'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const canReview = computed(() => {
  return authStore.isAdmin || authStore.isDosen || authStore.isSupervisi
})

const loading = ref(false)
const downloadingExcel = ref(false)
const downloadingCsv = ref(false)

const filters = reactive({
  study_area_id: 1, // Default ke Provinsi Sumatera Barat
  year: null,
  search: ''
})

const studyAreas = ref([])
const years = ref([])
const selectedAreaName = ref('Seluruh Wilayah')

const summary = reactive({
  total_mappers: 0,
  total_grids: 0,
  in_progress_count: 0,
  review_qc_count: 0,
  qc1_count: 0,
  qc2_count: 0,
  finishing_count: 0,
  completion_percentage: 0
})

const records = ref([])

const editingNoteTaskId = ref(null)
const editingNoteValue = ref('')

let searchTimeout = null
const handleSearchDebounced = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchData()
  }, 350)
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.study_area_id) params.study_area_id = filters.study_area_id
    if (filters.year) params.year = filters.year
    if (filters.search) params.search = filters.search

    const res = await api.getProgressTable(params)
    const data = res.data

    selectedAreaName.value = data.selected_area_name || 'Seluruh Wilayah'
    studyAreas.value = data.study_areas || []
    years.value = data.years || []
    
    Object.assign(summary, data.summary || {})
    
    records.value = (data.data || []).map(r => ({
      ...r,
      grids: (r.grids || []).map(g => ({
        ...g,
        updating: false
      }))
    }))
  } catch (err) {
    console.error('Gagal mengambil data rekap:', err)
  } finally {
    loading.value = false
  }
}

const toggleStage = async (gridItem, stageKey) => {
  if (!canReview.value || gridItem.updating) return

  const originalVal = gridItem[stageKey]
  const newVal = !originalVal

  gridItem[stageKey] = newVal
  gridItem.updating = true

  try {
    const payload = {
      [stageKey]: newVal
    }
    await api.updateTaskStage(gridItem.task_id, payload)
    
    if (stageKey === 'qc1_approved') {
      summary.qc1_count += newVal ? 1 : -1
    } else if (stageKey === 'qc2_approved') {
      summary.qc2_count += newVal ? 1 : -1
    } else if (stageKey === 'finishing_approved') {
      summary.finishing_count += newVal ? 1 : -1
      summary.completion_percentage = summary.total_grids > 0
        ? Math.round((summary.finishing_count / summary.total_grids) * 100 * 10) / 10
        : 0
    }
  } catch (err) {
    console.error(`Gagal memperbarui ${stageKey}:`, err)
    gridItem[stageKey] = originalVal
    alert('Gagal memperbarui tahapan QC: ' + (err.response?.data?.detail || err.message))
  } finally {
    gridItem.updating = false
  }
}

const startEditNote = (g) => {
  editingNoteTaskId.value = g.task_id
  editingNoteValue.value = g.keterangan || ''
}

const saveNote = async (g) => {
  const newVal = editingNoteValue.value
  try {
    await api.updateTaskStage(g.task_id, { reviewer_notes: newVal })
    g.keterangan = newVal
    editingNoteTaskId.value = null
  } catch (err) {
    console.error('Gagal menyimpan keterangan:', err)
    alert('Gagal menyimpan keterangan.')
  }
}

const handleExportExcel = async () => {
  downloadingExcel.value = true
  try {
    const params = {}
    if (filters.study_area_id) params.study_area_id = filters.study_area_id
    if (filters.year) params.year = filters.year
    if (filters.search) params.search = filters.search

    const response = await api.downloadProgressExcel(params)
    
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Rekap_Progres_Training_Sample_${new Date().toISOString().slice(0, 10)}.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Gagal mengunduh Excel:', err)
    alert('Gagal mengunduh file Excel.')
  } finally {
    downloadingExcel.value = false
  }
}

const handleExportCsv = async () => {
  downloadingCsv.value = true
  try {
    const params = {}
    if (filters.study_area_id) params.study_area_id = filters.study_area_id
    if (filters.year) params.year = filters.year
    if (filters.search) params.search = filters.search

    const response = await api.downloadProgressCsv(params)
    
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Rekap_Progres_Training_Sample_${new Date().toISOString().slice(0, 10)}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Gagal mengunduh CSV:', err)
    alert('Gagal mengunduh file CSV.')
  } finally {
    downloadingCsv.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

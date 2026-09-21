<template>
  <div class="p-4 sm:p-6 max-w-[1680px] mx-auto space-y-5 font-sans">
    
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
        <p class="text-xs text-slate-500 max-w-3xl leading-relaxed">
          Platform inspeksi dan kendali mutu anotasi spasial Sentinel-2. Pantau semua hasil digitasi per grid, tinjau capaian kontribusi per mapper, verifikasi topologi, dan evaluasi hasil pemetaan.
        </p>
      </div>

      <div class="flex items-center gap-2.5 flex-wrap">
        <!-- View Scope Mode Toggle: Single vs Mosaic -->
        <div class="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200 text-xs font-bold shadow-2xs">
          <button
            @click="switchViewScope('single')"
            class="px-3.5 py-1.5 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer"
            :class="viewScope === 'single' ? 'bg-white text-rose-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            <Focus :size="14" />
            <span>Fokus Grid</span>
          </button>
          <button
            @click="switchViewScope('mosaic')"
            class="px-3.5 py-1.5 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer"
            :class="viewScope === 'mosaic' ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            <Layers :size="14" />
            <span>Mosaik Semua Grid</span>
          </button>
        </div>

        <button
          @click="refreshAllData"
          class="bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-bold px-3.5 py-2 rounded-xl transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
          title="Segarkan data antrean & overview digitasi"
        >
          <RotateCw :size="13" :class="loadingTasks || loadingOverview ? 'animate-spin' : ''" />
          <span>Segarkan</span>
        </button>
      </div>
    </div>

    <!-- 📊 TOP STATS CARDS: Rangkuman Seluruh Hasil Digitasi -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3.5">
      <!-- Stat 1: Total Poligon -->
      <div class="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs flex items-center gap-3.5">
        <div class="w-11 h-11 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center shrink-0 border border-purple-100">
          <Shapes :size="20" />
        </div>
        <div class="min-w-0">
          <div class="text-xl font-black text-slate-900 font-heading">
            {{ overviewData.summary?.total_annotations || 0 }}
          </div>
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider truncate">
            Total Poligon Terdigitasi
          </div>
        </div>
      </div>

      <!-- Stat 2: Grid Terdigitasi -->
      <div class="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs flex items-center gap-3.5">
        <div class="w-11 h-11 rounded-2xl bg-blue-50 text-blue-700 flex items-center justify-center shrink-0 border border-blue-100">
          <Grid :size="20" />
        </div>
        <div class="min-w-0">
          <div class="text-xl font-black text-slate-900 font-heading">
            {{ overviewData.summary?.total_grids_digitized || 0 }} <span class="text-xs font-normal text-slate-400">Grid</span>
          </div>
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider truncate">
            Grid Memiliki Data
          </div>
        </div>
      </div>

      <!-- Stat 3: Total Luas Ha -->
      <div class="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs flex items-center gap-3.5">
        <div class="w-11 h-11 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0 border border-emerald-100">
          <Sprout :size="20" />
        </div>
        <div class="min-w-0">
          <div class="text-xl font-black text-slate-900 font-heading">
            ~{{ formatNumber(overviewData.summary?.total_area_ha || 0) }} <span class="text-xs font-normal text-slate-400">Ha</span>
          </div>
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider truncate">
            Luas Tutupan Terlatih
          </div>
        </div>
      </div>

      <!-- Stat 4: Mapper Aktif -->
      <div class="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs flex items-center gap-3.5">
        <div class="w-11 h-11 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center shrink-0 border border-amber-100">
          <Users :size="20" />
        </div>
        <div class="min-w-0">
          <div class="text-xl font-black text-slate-900 font-heading">
            {{ overviewData.by_mapper?.length || 0 }} <span class="text-xs font-normal text-slate-400">Mapper</span>
          </div>
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider truncate">
            Mahasiswa Berkontribusi
          </div>
        </div>
      </div>
    </div>

    <!-- Informational Banner for Non-Reviewer -->
    <div v-if="!authStore.isReviewer" class="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 flex items-center justify-between gap-3 shadow-2xs">
      <div class="flex items-center gap-2">
        <Info :size="16" class="text-amber-700 shrink-0" />
        <span><b>Mode Pantau Kontributor:</b> Anda dapat melihat seluruh hasil digitasi, mosaik peta, dan status antrean QC. Hak persetujuan (Approve) dan permintaan revisi hanya dimiliki oleh Tim Supervisi / Administrator.</span>
      </div>
    </div>

    <!-- MAIN INTERACTIVE WORKSPACE: Left Segments (4 cols) & Right Map Studio (8 cols) -->
    <div class="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
      
      <!-- LEFT COLUMN: Segmented Overview & Task Queue (4 cols) -->
      <div class="xl:col-span-4 bg-white border border-slate-200 rounded-3xl p-4 sm:p-5 shadow-sm flex flex-col gap-3.5">
        
        <!-- Segment Tabs Header -->
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <span class="text-xs font-extrabold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
            <ClipboardList :size="14" class="text-slate-500" />
            <span>Segmen Tinjauan</span>
          </span>
          <span class="text-[11px] font-mono text-slate-400 font-bold">
            {{ activeSegment === 'grids' ? `${displayGridList.length} Grid` : (activeSegment === 'mappers' ? `${overviewData.by_mapper?.length || 0} Mapper` : `${overviewData.by_class?.length || 0} Kelas`) }}
          </span>
        </div>

        <!-- Segment Selector Tabs -->
        <div class="grid grid-cols-3 gap-1 bg-slate-100 p-1 rounded-2xl text-center text-xs font-bold">
          <button
            @click="activeSegment = 'grids'"
            class="py-1.5 rounded-xl transition-all cursor-pointer flex items-center justify-center gap-1"
            :class="activeSegment === 'grids' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            <Grid :size="13" />
            <span>Per Grid</span>
          </button>
          <button
            @click="activeSegment = 'mappers'"
            class="py-1.5 rounded-xl transition-all cursor-pointer flex items-center justify-center gap-1"
            :class="activeSegment === 'mappers' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            <Users :size="13" />
            <span>Mapper</span>
          </button>
          <button
            @click="activeSegment = 'classes'"
            class="py-1.5 rounded-xl transition-all cursor-pointer flex items-center justify-center gap-1"
            :class="activeSegment === 'classes' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            <PieChart :size="13" />
            <span>Per Kelas</span>
          </button>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- SEGMEN 1: PER GRID (Semua Grid Terdigitasi & Antrean Review)         -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="activeSegment === 'grids'" class="space-y-3">
          <!-- Search Box -->
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Cari kode grid / nama mapper..."
              class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 pl-8 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-400 focus:bg-white"
            />
            <FileSearch :size="13" class="absolute left-2.5 top-2.5 text-slate-400" />
            <button
              v-if="searchQuery"
              @click="searchQuery = ''"
              class="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
            >
              <X :size="12" />
            </button>
          </div>

          <!-- Year Filter Pills (Default: Latest year 2025, selectable to other years) -->
          <div class="space-y-1">
            <div class="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider px-0.5">
              <span>Filter Tahun Citra:</span>
              <span class="font-mono text-rose-600 bg-rose-50 px-1.5 py-0.2 rounded border border-rose-200">
                {{ selectedYear === 'ALL' ? 'Semua Tahun' : selectedYear }}
              </span>
            </div>
            <div class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-center text-[10px] font-bold overflow-x-auto">
              <button
                v-for="yr in availableQcYears"
                :key="yr"
                @click="setQcYear(yr)"
                class="flex-1 py-1 px-2 rounded-lg transition-all cursor-pointer whitespace-nowrap"
                :class="selectedYear === yr ? 'bg-white text-rose-700 shadow-xs border border-slate-200' : 'text-slate-600 hover:text-slate-900'"
              >
                {{ yr === 'ALL' ? 'Semua' : yr }}
              </button>
            </div>
          </div>

          <!-- Status Filter Pills -->
          <div class="flex flex-wrap gap-1 bg-slate-50 p-1 rounded-xl border border-slate-200 text-center text-[10px] font-bold">
            <button
              @click="statusFilter = 'ALL'"
              class="px-2 py-1 rounded-lg transition-all cursor-pointer shrink-0"
              :class="statusFilter === 'ALL' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            >
              Semua ({{ allDigitizedGrids.length }})
            </button>
            <button
              @click="statusFilter = 'SUBMITTED'"
              class="px-2 py-1 rounded-lg transition-all cursor-pointer shrink-0"
              :class="statusFilter === 'SUBMITTED' ? 'bg-orange-600 text-white shadow-xs' : 'text-orange-700 hover:bg-orange-50'"
            >
              Review ({{ countByStatus('SUBMITTED') }})
            </button>
            <button
              @click="statusFilter = 'REVISION_NEEDED'"
              class="px-2 py-1 rounded-lg transition-all cursor-pointer shrink-0"
              :class="statusFilter === 'REVISION_NEEDED' ? 'bg-rose-600 text-white shadow-xs' : 'text-rose-700 hover:bg-rose-50'"
            >
              Revisi ({{ countByStatus('REVISION_NEEDED') }})
            </button>
            <button
              @click="statusFilter = 'APPROVED'"
              class="px-2 py-1 rounded-lg transition-all cursor-pointer shrink-0"
              :class="statusFilter === 'APPROVED' ? 'bg-emerald-600 text-white shadow-xs' : 'text-emerald-700 hover:bg-emerald-50'"
            >
              Approved ({{ countByStatus('APPROVED') }})
            </button>
            <button
              @click="statusFilter = 'IN_PROGRESS'"
              class="px-2 py-1 rounded-lg transition-all cursor-pointer shrink-0"
              :class="statusFilter === 'IN_PROGRESS' ? 'bg-blue-600 text-white shadow-xs' : 'text-blue-700 hover:bg-blue-50'"
            >
              Proses ({{ countByStatus('IN_PROGRESS') }})
            </button>
          </div>

          <!-- Empty State -->
          <div v-if="displayGridList.length === 0" class="text-center py-10 text-slate-400 text-xs">
            <Shapes :size="32" class="mx-auto mb-2 opacity-30" />
            <p class="font-bold">Tidak ada grid yang sesuai filter</p>
            <p class="text-[11px] text-slate-400 mt-0.5">Belum ada poligon terdigitasi atau filter pencarian terlalu spesifik.</p>
          </div>

          <!-- Grid Cards List -->
          <div class="space-y-2 overflow-y-auto max-h-[580px] pr-1">
            <div
              v-for="grid in displayGridList"
              :key="grid.task_id || grid.id"
              @click="selectTaskByGridItem(grid)"
              class="p-3 rounded-2xl border transition-all cursor-pointer flex flex-col gap-2 shadow-2xs hover:shadow-xs group"
              :class="selectedTask?.id === (grid.task_id || grid.id)
                ? 'bg-rose-50/90 border-rose-400 shadow-xs ring-2 ring-rose-400/30'
                : 'bg-slate-50/70 border-slate-200/90 hover:border-slate-300 hover:bg-white'"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <span class="font-mono text-xs font-black text-slate-900 group-hover:text-rose-600 transition-colors">
                    {{ grid.grid_code }}
                  </span>
                  <span class="text-[10px] font-mono text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200 font-bold">
                    {{ grid.year }}
                  </span>
                </div>
                <span
                  class="text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-2xs"
                  :class="getStatusBadgeClass(grid.status)"
                >
                  {{ formatStatus(grid.status) }}
                </span>
              </div>

              <!-- Classes indicator dots -->
              <div v-if="grid.classes && grid.classes.length > 0" class="flex items-center gap-1 flex-wrap">
                <span
                  v-for="cls in grid.classes"
                  :key="cls.class_id"
                  class="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded-md border font-semibold"
                  :style="{ backgroundColor: `${cls.color}15`, borderColor: `${cls.color}40`, color: '#1e293b' }"
                  :title="`${cls.class_name}: ${cls.count} poligon (~${cls.area_ha} Ha)`"
                >
                  <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ backgroundColor: cls.color }"></span>
                  <span>{{ cls.class_name }} ({{ cls.count }})</span>
                </span>
              </div>

              <!-- Footer: Mapper & Stats -->
              <div class="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-200/60">
                <span class="flex items-center gap-1.5 truncate max-w-[170px]" :title="grid.assigned_user_name">
                  <User :size="11" class="text-slate-400 shrink-0" />
                  <b class="text-slate-800 font-semibold truncate text-[10.5px]">{{ grid.assigned_user_name || 'Belum Diambil' }}</b>
                </span>
                <div class="flex items-center gap-1.5 shrink-0">
                  <span class="font-mono text-purple-700 font-bold bg-purple-50 px-1.5 py-0.5 rounded-md border border-purple-200 flex items-center gap-1 text-[10px]">
                    <Shapes :size="10" /> {{ grid.annotation_count || 0 }}
                  </span>
                  <span class="font-mono text-slate-600 font-bold bg-slate-100 px-1.5 py-0.5 rounded-md border border-slate-200 text-[10px]">
                    ~{{ grid.total_area_ha || 0 }} Ha
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- SEGMEN 2: PER MAPPER / MAHASISWA (Rangkuman Capaian Kontributor)   -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-else-if="activeSegment === 'mappers'" class="space-y-3">
          <div class="text-xs text-slate-500 leading-relaxed">
            Daftar mahasiswa yang telah mendigitasi poligon. Klik salah satu grid di bawah nama mereka untuk langsung membuka dan memeriksa hasilnya.
          </div>

          <div v-if="overviewData.by_mapper?.length === 0" class="text-center py-10 text-slate-400 text-xs">
            <Users :size="32" class="mx-auto mb-2 opacity-30" />
            <p class="font-bold">Belum ada data kontributor</p>
          </div>

          <div class="space-y-2.5 overflow-y-auto max-h-[600px] pr-1">
            <div
              v-for="mapper in overviewData.by_mapper"
              :key="mapper.user_id"
              class="p-3.5 bg-slate-50/80 border border-slate-200 rounded-2xl space-y-2.5 hover:bg-white hover:border-slate-300 transition-all shadow-2xs"
            >
              <!-- Mapper Header -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-rose-500 to-amber-500 text-white font-black text-xs flex items-center justify-center shadow-xs">
                    {{ (mapper.full_name?.charAt(0) || 'M').toUpperCase() }}
                  </div>
                  <div>
                    <div class="font-bold text-slate-900 text-xs truncate max-w-[180px]">{{ mapper.full_name }}</div>
                    <div class="text-[10px] text-slate-500 font-mono">
                      {{ mapper.nim_nip ? `NIM: ${mapper.nim_nip}` : `@${mapper.username}` }}
                    </div>
                  </div>
                </div>

                <div class="text-right">
                  <span class="text-xs font-black text-rose-600 font-mono">{{ mapper.polygon_count }}</span>
                  <span class="text-[10px] text-slate-400 block">poligon</span>
                </div>
              </div>

              <!-- Summary Badges -->
              <div class="grid grid-cols-2 gap-2 text-[10px] font-mono font-bold bg-white p-2 rounded-xl border border-slate-200/80">
                <div class="text-slate-600 flex items-center gap-1">
                  <Grid :size="11" class="text-blue-500" />
                  <span>{{ mapper.grids_count }} Grid Dikerjakan</span>
                </div>
                <div class="text-slate-600 flex items-center gap-1 justify-end">
                  <Sprout :size="11" class="text-emerald-500" />
                  <span>~{{ mapper.total_area_ha }} Ha Luas</span>
                </div>
              </div>

              <!-- Grid Pills List -->
              <div class="space-y-1">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Grid yang Dikerjakan:</span>
                <div class="flex flex-wrap gap-1">
                  <button
                    v-for="code in mapper.grids_list"
                    :key="code"
                    @click="findAndSelectGridByCode(code)"
                    class="px-2 py-0.5 bg-slate-100 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-300 border border-slate-200 text-slate-700 font-mono text-[10px] font-bold rounded-lg transition-all cursor-pointer flex items-center gap-1"
                    :title="`Buka grid ${code}`"
                  >
                    <span>{{ code }}</span>
                    <ExternalLink :size="9" class="opacity-60" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- SEGMEN 3: PER KELAS TUTUPAN LAHAN (Distribusi 12 Kelas)            -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-else-if="activeSegment === 'classes'" class="space-y-3">
          <div class="text-xs text-slate-500 leading-relaxed">
            Distribusi 12 skema kelas tutupan lahan yang berhasil didigitasi pada seluruh grid training sample.
          </div>

          <div v-if="overviewData.by_class?.length === 0" class="text-center py-10 text-slate-400 text-xs">
            <PieChart :size="32" class="mx-auto mb-2 opacity-30" />
            <p class="font-bold">Belum ada poligon tutupan lahan</p>
          </div>

          <div class="space-y-2 overflow-y-auto max-h-[600px] pr-1">
            <div
              v-for="cls in overviewData.by_class"
              :key="cls.class_id"
              class="p-3 bg-slate-50/80 border border-slate-200 rounded-2xl space-y-1.5 hover:bg-white transition-all shadow-2xs"
            >
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                  <span class="w-3.5 h-3.5 rounded-md shrink-0 shadow-2xs border border-slate-300" :style="{ backgroundColor: cls.color }"></span>
                  <span class="font-bold text-slate-800 text-[11px]">{{ cls.name }}</span>
                </div>
                <span class="font-mono text-slate-900 font-black text-xs">{{ cls.count }} Poligon</span>
              </div>

              <!-- Progress bar -->
              <div class="w-full bg-slate-200/80 h-2 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="{ width: `${cls.percentage}%`, backgroundColor: cls.color }"
                ></div>
              </div>

              <div class="flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>Luas: <b>~{{ cls.total_area_ha }} Ha</b></span>
                <span class="font-bold text-slate-700">{{ cls.percentage }}% dari total</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- RIGHT COLUMN: Embedded Live Map & Review Inspector (8 cols) -->
      <div class="xl:col-span-8 bg-white border border-slate-200 rounded-3xl p-5 sm:p-6 shadow-sm flex flex-col gap-4">
        
        <!-- Inspection Top Bar -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-mono text-lg font-black text-slate-900">
                {{ viewScope === 'mosaic' ? 'Mosaik Global Seluruh Grid' : (selectedTask?.grid_code || 'Pilih Grid') }}
              </span>
              <span
                v-if="viewScope === 'single' && selectedTask"
                class="text-xs bg-rose-50 text-rose-700 px-2.5 py-0.5 rounded-lg border border-rose-200 font-bold font-mono"
              >
                Tahun {{ selectedTask.year }}
              </span>
              <span
                v-if="viewScope === 'single' && selectedTask"
                class="text-[11px] font-bold px-2.5 py-0.5 rounded-full border shadow-2xs"
                :class="getStatusBadgeClass(selectedTask.status)"
              >
                {{ formatStatus(selectedTask.status) }}
              </span>
              <span
                v-if="viewScope === 'mosaic'"
                class="text-xs bg-purple-50 text-purple-700 px-2.5 py-0.5 rounded-lg border border-purple-200 font-bold font-mono flex items-center gap-1"
              >
                <Layers :size="12" />
                <span>{{ allMosaicFeatures.length }} Poligon Aktif di Peta</span>
              </span>
            </div>
            <div class="text-xs text-slate-500 mt-1">
              <template v-if="viewScope === 'single' && selectedTask">
                Wilayah: <b class="text-slate-800">{{ selectedTask.study_area_name }}</b> • Kontributor: <b class="text-slate-800">{{ selectedTask.assigned_user_name || 'Belum Diambil' }}</b>
              </template>
              <template v-else-if="viewScope === 'mosaic'">
                Menampilkan seluruh hasil digitasi dari seluruh grid secara terpadu di atas citra satelit Sentinel-2. Klik pada poligon mana saja untuk melihat detail atau mereview grid terkait.
              </template>
              <template v-else>
                Pilih salah satu grid task dari antrean di sebelah kiri untuk melihat peta interaktif.
              </template>
            </div>
          </div>

          <!-- Quick Action: Open in Full Digitizer Studio (when single task selected) -->
          <div class="flex items-center gap-2 shrink-0">
            <button
              @click="fitMapBounds"
              class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs"
              title="Sesuaikan zoom peta dengan cakupan poligon"
            >
              <Maximize2 :size="13" />
              <span>Zoom Pas</span>
            </button>

            <router-link
              v-if="selectedTask"
              :to="{ path: '/map', query: { taskId: selectedTask.id } }"
              class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-2 shadow-xs cursor-pointer shrink-0"
              title="Buka grid ini di Studio Digitasi Lengkap untuk mengedit poligon"
            >
              <ExternalLink :size="14" />
              <span>Buka di Studio Lengkap</span>
            </router-link>
          </div>
        </div>

        <!-- 🛰️ EMBEDDED LIVE QC MAP VIEWER -->
        <div class="relative w-full rounded-2xl overflow-hidden border border-slate-300 shadow-inner bg-slate-900">
          
          <!-- Floating Map Layer & Controls Top Bar -->
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

            <!-- Context Toggle & Opacity Slider -->
            <div class="flex items-center gap-3 shrink-0 flex-wrap">
              <!-- Checkbox: Show other grids context during single grid mode -->
              <label
                v-if="viewScope === 'single'"
                class="flex items-center gap-1.5 text-[11px] font-bold text-slate-700 cursor-pointer select-none bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200"
                title="Tampilkan poligon grid lain di sekitar sebagai referensi batas kontinuitas"
              >
                <input
                  type="checkbox"
                  v-model="showContextPolygons"
                  @change="toggleContextLayers"
                  class="rounded text-rose-600 focus:ring-rose-500 cursor-pointer"
                />
                <span>Poligon Sekitar</span>
              </label>

              <!-- Opacity Slider -->
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

              <!-- Topology Check Button (Single mode) -->
              <button
                v-if="viewScope === 'single' && selectedTask"
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
          <div id="qc-map-container" class="w-full h-[460px] z-0"></div>

          <!-- Active Feature Info Pill on Map Bottom -->
          <div
            v-if="hoveredFeature"
            class="absolute bottom-3 left-3 z-10 bg-slate-900/90 backdrop-blur-md text-white px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 border border-slate-700 shadow-lg animate-in fade-in"
          >
            <div class="w-3 h-3 rounded-sm shrink-0" :style="{ backgroundColor: hoveredFeature.color }"></div>
            <span>{{ hoveredFeature.class_name }} (~{{ hoveredFeature.areaHa }} Ha)</span>
            <span v-if="hoveredFeature.grid_code" class="text-[10px] font-mono text-slate-400">
              • Grid {{ hoveredFeature.grid_code }} ({{ hoveredFeature.author_name }})
            </span>
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

        <!-- Bottom Split: Polygon List & Review Action Panel (When task is selected) -->
        <div v-if="selectedTask" class="grid grid-cols-1 lg:grid-cols-12 gap-4 pt-1">
          
          <!-- Polygon Breakdown (5 cols) -->
          <div class="lg:col-span-5 bg-slate-50/70 border border-slate-200 p-3.5 rounded-2xl space-y-2">
            <div class="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center justify-between">
              <span>Daftar Poligon Grid Ini ({{ taskFeatures.length }})</span>
              <span class="text-purple-700 font-mono text-[11px] font-bold">Total: ~{{ totalAreaHa }} Ha</span>
            </div>

            <div v-if="taskFeatures.length === 0" class="text-center py-8 text-slate-400 text-xs">
              Belum ada poligon didigitasi pada grid ini.
            </div>

            <div v-else class="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              <div
                v-for="(poly, idx) in taskFeatures"
                :key="idx"
                class="p-2 bg-white border border-slate-200 rounded-xl flex items-center justify-between text-xs transition-all hover:border-indigo-300"
              >
                <div class="flex items-center gap-2 truncate">
                  <div
                    class="w-3 h-3 rounded-sm border border-slate-300 shrink-0 shadow-2xs"
                    :style="{ backgroundColor: getClassColor(poly.properties?.class_id) }"
                  ></div>
                  <span class="font-bold text-slate-800 truncate text-[11px]">{{ poly.properties?.class_name || 'Belum Terklasifikasi' }}</span>
                </div>
                <span class="text-[10px] text-slate-500 font-mono bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200 shrink-0">
                  ~{{ Math.round((poly.properties?.area_sqm || 10000) / 10000) }} Ha
                </span>
              </div>
            </div>
          </div>

          <!-- Review Actions & Decision Form (7 cols) -->
          <div class="lg:col-span-7 bg-white border border-slate-200 p-4 rounded-2xl flex flex-col justify-between gap-3 shadow-2xs">
            
            <!-- Admin / Reviewer Assign Grid to Account -->
            <div v-if="authStore.isReviewer || authStore.isAdmin" class="p-3 bg-indigo-50/70 border border-indigo-200 rounded-xl space-y-1.5 shadow-2xs">
              <div class="flex items-center justify-between text-[11px] font-bold text-indigo-950">
                <span class="flex items-center gap-1.5"><UserCheck :size="13" class="text-indigo-600" /> Penugasan Grid Ini:</span>
                <span class="text-indigo-700 font-semibold truncate max-w-[200px]">{{ selectedTask.assigned_user_name || 'Belum Ditugaskan' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <select
                  v-model="selectedAssignUserId"
                  class="flex-1 bg-white border border-indigo-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                >
                  <option :value="null">-- Lepas Penugasan (Tersedia) --</option>
                  <option v-for="u in userList" :key="u.id" :value="u.id">
                    {{ u.full_name || u.username }} ({{ u.role }})
                  </option>
                </select>
                <button
                  @click="assignCurrentTaskToUser"
                  :disabled="loadingAction"
                  class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer shrink-0 disabled:opacity-50"
                >
                  Tugaskan
                </button>
              </div>
            </div>

            <div v-if="authStore.isReviewer" class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <Edit3 :size="13" class="text-slate-500" />
                  <span>Catatan Evaluasi Reviewer:</span>
                </span>
                
                <!-- Quick Template Buttons -->
                <div class="flex items-center gap-1 text-[10px]">
                  <button
                    @click="reviewerNotes = 'Anotasi telah divalidasi, batas poligon rapi dan kelas sesuai citra Sentinel-2.'"
                    class="px-2 py-0.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-md border border-emerald-200 cursor-pointer"
                  >
                    Rapi & Sesuai
                  </button>
                  <button
                    @click="reviewerNotes = 'Batas antara Hutan Lahan Kering dan Perkebunan Sawit masih kurang presisi, harap disempurnakan.'"
                    class="px-2 py-0.5 bg-amber-50 text-amber-700 hover:bg-amber-100 rounded-md border border-amber-200 cursor-pointer"
                  >
                    Batas Kurang Presisi
                  </button>
                  <button
                    @click="reviewerNotes = 'Area permukiman dan tubuh air belum terdigitasi lengkap pada sisi barat grid.'"
                    class="px-2 py-0.5 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-md border border-rose-200 cursor-pointer"
                  >
                    Belum Lengkap
                  </button>
                </div>
              </div>

              <textarea
                v-model="reviewerNotes"
                rows="2"
                placeholder="Tulis catatan evaluasi atau instruksi perbaikan spesifik untuk mapper..."
                class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-400 focus:bg-white resize-none"
              ></textarea>
            </div>

            <!-- Decision Buttons (Approve / Request Revision) -->
            <div v-if="authStore.isReviewer" class="flex items-center justify-between gap-3 pt-2 border-t border-slate-100">
              <button
                @click="rejectWithNotes"
                :disabled="loadingAction"
                class="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs disabled:opacity-50"
                title="Kembalikan grid ini ke kontributor dengan catatan perbaikan"
              >
                <RotateCcw :size="13" />
                <span>Minta Revisi</span>
              </button>

              <button
                @click="approveTask"
                :disabled="loadingAction"
                class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-6 py-2 rounded-xl transition-all flex items-center gap-2 cursor-pointer shadow-sm hover:shadow-md disabled:opacity-50"
                title="Setujui grid ini dan masukkan poligon ke data training U-Net"
              >
                <CheckCircle2 :size="15" />
                <span>Setujui (Approve)</span>
              </button>
            </div>

            <div v-else class="text-xs text-slate-500 italic text-center py-4 bg-slate-50 rounded-xl">
              Anda sedang dalam Mode Pantau. Tombol persetujuan (Approve/Revisi) dinonaktifkan.
            </div>
          </div>
        </div>

        <!-- Fallback message when in Mosaic Mode and no task selected -->
        <div v-else-if="viewScope === 'mosaic'" class="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between text-xs text-slate-600">
          <div class="flex items-center gap-2">
            <Sparkles :size="16" class="text-purple-600 shrink-0" />
            <span><b>Mode Mosaik Aktif:</b> Anda dapat mengklik poligon mana saja di peta untuk melihat ringkasan detailnya atau mengklik tombol <i>"Review Grid Ini"</i> pada popup.</span>
          </div>
          <span class="font-mono text-slate-400 text-[11px]">Total {{ allMosaicFeatures.length }} Poligon</span>
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
  Globe,
  Layers,
  Grid,
  Users,
  PieChart,
  Focus,
  Maximize2,
  Edit3,
  Sparkles,
  UserCheck
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import { useAnnotationsStore } from '../stores/annotations'
import api from '../services/api'

const authStore = useAuthStore()
const tasksStore = useTasksStore()
const annotationsStore = useAnnotationsStore()

// View Scope: 'single' (Inspect selected grid) | 'mosaic' (View all digitized grids seamlessly)
const viewScope = ref('single')

// Segment selection in left column: 'grids' | 'mappers' | 'classes'
const activeSegment = ref('grids')

const selectedTask = ref(null)
const taskFeatures = ref([])
const reviewerNotes = ref('')
// Loading & state indicators
const loadingTasks = ref(false)
const loadingOverview = ref(false)
const loadingAction = ref(false)
const userList = ref([])
const selectedAssignUserId = ref(null)
const statusFilter = ref('ALL') // 'ALL' | 'SUBMITTED' | 'REVISION_NEEDED' | 'APPROVED' | 'IN_PROGRESS'
const searchQuery = ref('')

// Overview data from API
const overviewData = ref({
  summary: { total_annotations: 0, total_grids_digitized: 0, total_area_ha: 0 },
  by_grid: [],
  by_mapper: [],
  by_class: []
})

// All mosaic features cache
const allMosaicFeatures = ref([])
const showContextPolygons = ref(true)

// Live Map Variables
let qcMap = null
let qcTileLayer = null
let qcFeatureGroup = null
let qcContextFeatureGroup = null
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

// ── Year Filter State ─────────────────────────────────────────
const selectedYear = ref(2025)

const availableQcYears = computed(() => {
  const years = new Set([2025, 2024, 2023, 2022, 2021, 2018])
  tasksStore.tasks.forEach(t => { if (t.year) years.add(t.year) })
  if (overviewData.value.by_grid) {
    overviewData.value.by_grid.forEach(g => { if (g.year) years.add(g.year) })
  }
  const sorted = Array.from(years).sort((a, b) => b - a)
  return [...sorted, 'ALL']
})

const setQcYear = async (yr) => {
  selectedYear.value = yr
  await refreshAllData()
}

// All digitized grids (merged from overviewData.by_grid and tasksStore)
const allDigitizedGrids = computed(() => {
  let list = []
  if (overviewData.value.by_grid && overviewData.value.by_grid.length > 0) {
    list = overviewData.value.by_grid
  } else {
    list = tasksStore.tasks.filter(t => (t.annotation_count || 0) > 0 || ['SUBMITTED', 'REVISION_NEEDED', 'APPROVED'].includes(t.status))
  }
  if (selectedYear.value !== 'ALL') {
    list = list.filter(g => g.year === selectedYear.value)
  }
  return list
})

// Filtered grid list for display in Segment 1
const displayGridList = computed(() => {
  let list = allDigitizedGrids.value

  // Status filter
  if (statusFilter.value !== 'ALL') {
    list = list.filter(g => g.status === statusFilter.value)
  }

  // Search filter
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(g =>
      (g.grid_code || '').toLowerCase().includes(q) ||
      (g.assigned_user_name || '').toLowerCase().includes(q) ||
      (g.study_area_name || '').toLowerCase().includes(q)
    )
  }

  return list
})

const countByStatus = (status) => {
  return allDigitizedGrids.value.filter(t => t.status === status).length
}

const totalAreaHa = computed(() => {
  const totalSqm = taskFeatures.value.reduce((acc, curr) => acc + (curr.properties?.area_sqm || 0), 0)
  return Math.round(totalSqm / 10000)
})

const formatNumber = (val) => {
  if (!val) return '0'
  return Number(val).toLocaleString('id-ID')
}

onMounted(async () => {
  await annotationsStore.fetchClasses()
  if (authStore.isReviewer || authStore.isAdmin) {
    try {
      userList.value = await authStore.fetchAllUsers()
    } catch (_) {}
  }
  await refreshAllData()
})

onUnmounted(() => {
  if (qcMap) {
    qcMap.remove()
    qcMap = null
  }
})

const refreshAllData = async () => {
  loadingTasks.value = true
  loadingOverview.value = true
  const yrParam = selectedYear.value === 'ALL' ? null : selectedYear.value
  try {
    tasksStore.selectedYear = yrParam
    await Promise.all([
      tasksStore.fetchTasks(),
      loadOverviewData(yrParam),
      loadMosaicFeatures(yrParam)
    ])

    // Update QC tile layer to selected year if map ready
    const tileYr = yrParam || selectedTask.value?.year || 2025
    if (qcMap) {
      updateQCTileLayer(tileYr)
    }

    // Auto-select first grid if none selected or current selection not in year
    if (displayGridList.value.length > 0) {
      const curId = selectedTask.value?.id
      const stillInList = displayGridList.value.find(g => (g.task_id || g.id) === curId)
      if (!stillInList) {
        await selectTaskByGridItem(displayGridList.value[0])
      }
    } else {
      selectedTask.value = null
      taskFeatures.value = []
      if (qcFeatureGroup) qcFeatureGroup.clearLayers()
      if (qcGridBoundingLayer) {
        qcMap.removeLayer(qcGridBoundingLayer)
        qcGridBoundingLayer = null
      }
    }
  } finally {
    loadingTasks.value = false
    loadingOverview.value = false
  }
}

const loadOverviewData = async (year = null) => {
  try {
    const data = await annotationsStore.fetchAnnotationsOverview(year ? { year } : {})
    if (data && data.summary) {
      overviewData.value = data
    }
  } catch (e) {
    console.error('Error loading overview data:', e)
  }
}

const loadMosaicFeatures = async (year = null) => {
  try {
    const feats = await annotationsStore.fetchAllAnnotationsFeatures(year ? { year } : {})
    allMosaicFeatures.value = feats || []
  } catch (e) {
    console.error('Error loading mosaic features:', e)
  }
}

const switchViewScope = async (scope) => {
  viewScope.value = scope
  await nextTick()

  if (scope === 'mosaic') {
    renderMosaicOnMap()
  } else if (scope === 'single') {
    if (selectedTask.value) {
      await selectTask(selectedTask.value)
    } else if (displayGridList.value.length > 0) {
      await selectTaskByGridItem(displayGridList.value[0])
    }
  }
}

const selectTaskByGridItem = async (gridItem) => {
  const taskId = gridItem.task_id || gridItem.id
  let fullTask = tasksStore.tasks.find(t => t.id === taskId)
  if (!fullTask) {
    fullTask = gridItem
  }
  await selectTask(fullTask)
}

const findAndSelectGridByCode = async (gridCode) => {
  const target = tasksStore.tasks.find(t => t.grid_code === gridCode) ||
    overviewData.value.by_grid.find(g => g.grid_code === gridCode)
  if (target) {
    activeSegment.value = 'grids'
    await selectTaskByGridItem(target)
  }
}

const selectTask = async (task) => {
  selectedTask.value = task
  selectedAssignUserId.value = task.assigned_user_id || null
  reviewerNotes.value = task.reviewer_notes || ''
  qcTopologyResult.value = null
  hoveredFeature.value = null

  if (viewScope.value === 'mosaic') {
    viewScope.value = 'single'
  }

  const features = await annotationsStore.fetchGridAnnotations(task.id)
  taskFeatures.value = features

  await nextTick()
  initOrUpdateQCMap(task, features)
}

const initOrUpdateQCMap = (task, features) => {
  ensureMapInitialized()

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

  // Render Polygons for active grid
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
        weight: 2,
        fillColor: color,
        fillOpacity: qcOpacity.value
      })
    })

    layer.eachLayer(l => {
      l.on('mouseover', () => {
        hoveredFeature.value = {
          class_name: cls?.name || feat.properties?.class_name || 'Belum Terklasifikasi',
          color: color,
          areaHa: areaHa,
          grid_code: task.grid_code,
          author_name: task.assigned_user_name
        }
        l.setStyle({ weight: 3.5, color: '#facc15', fillOpacity: 0.88 })
      })

      l.on('mouseout', () => {
        l.setStyle({ weight: 2, color: '#ffffff', fillOpacity: qcOpacity.value })
      })

      l.bindTooltip(`<b>${cls?.name || feat.properties?.class_name}</b><br>~${areaHa} Ha`, {
        sticky: true,
        className: 'text-xs'
      })

      qcFeatureGroup.addLayer(l)
    })
  })

  // Render context polygons from other grids if enabled
  renderContextPolygons(task.id)

  qcMap.fitBounds(bounds, { padding: [30, 30] })
}

const renderContextPolygons = (currentTaskId) => {
  if (!qcContextFeatureGroup) return
  qcContextFeatureGroup.clearLayers()

  if (!showContextPolygons.value || allMosaicFeatures.value.length === 0) return

  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  const otherFeatures = allMosaicFeatures.value.filter(f => f.properties?.task_grid_id !== currentTaskId)

  otherFeatures.forEach(feat => {
    const cls = classesMap[feat.properties?.class_id]
    const color = cls?.color || feat.properties?.color_hex || '#9CA3AF'

    const layer = L.geoJSON(feat, {
      style: () => ({
        color: '#ffffff',
        weight: 1,
        dashArray: '3, 3',
        fillColor: color,
        fillOpacity: Math.max(0.2, qcOpacity.value * 0.45)
      })
    })

    layer.eachLayer(l => {
      l.bindTooltip(`[Grid Tetangga ${feat.properties?.grid_code}] ${feat.properties?.class_name}`, {
        sticky: true,
        className: 'text-[11px]'
      })
      qcContextFeatureGroup.addLayer(l)
    })
  })
}

const toggleContextLayers = () => {
  if (selectedTask.value && viewScope.value === 'single') {
    renderContextPolygons(selectedTask.value.id)
  }
}

// 🗺️ Render all mosaic features across all grids
const renderMosaicOnMap = () => {
  ensureMapInitialized()

  if (qcGridBoundingLayer) {
    qcMap.removeLayer(qcGridBoundingLayer)
    qcGridBoundingLayer = null
  }
  if (qcContextFeatureGroup) qcContextFeatureGroup.clearLayers()
  qcFeatureGroup.clearLayers()

  const mosaicYear = selectedYear.value !== 'ALL' ? Number(selectedYear.value) : 2025
  updateQCTileLayer(mosaicYear)

  if (allMosaicFeatures.value.length === 0) return

  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  allMosaicFeatures.value.forEach(feat => {
    const cls = classesMap[feat.properties?.class_id]
    const color = cls?.color || feat.properties?.color_hex || '#9CA3AF'
    const areaHa = feat.properties?.area_ha || Math.round((feat.properties?.area_sqm || 10000) / 10000)
    const gridCode = feat.properties?.grid_code || 'Grid'
    const authorName = feat.properties?.author_name || 'Mapper'
    const taskStatus = feat.properties?.task_status || 'UNKNOWN'

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
          class_name: feat.properties?.class_name || cls?.name || 'Tutupan Lahan',
          color: color,
          areaHa: areaHa,
          grid_code: gridCode,
          author_name: authorName
        }
        l.setStyle({ weight: 3, color: '#facc15', fillOpacity: 0.9 })
      })

      l.on('mouseout', () => {
        l.setStyle({ weight: 1.5, color: '#ffffff', fillOpacity: qcOpacity.value })
      })

      // Interactive popup
      const popupHtml = document.createElement('div')
      popupHtml.className = 'p-1 text-xs space-y-2'
      popupHtml.innerHTML = `
        <div class="flex items-center gap-2 pb-1.5 border-b border-slate-200">
          <span style="display:inline-block;width:12px;height:12px;border-radius:3px;background-color:${color};border:1px solid rgba(0,0,0,0.15)"></span>
          <b class="text-slate-900 text-xs">${feat.properties?.class_name || 'Tutupan Lahan'}</b>
        </div>
        <div class="space-y-0.5 text-[11px] text-slate-600">
          <div>Luas: <b class="text-slate-900 font-mono">~${areaHa} Ha</b></div>
          <div>Grid: <b class="text-slate-900 font-mono">${gridCode}</b> (${feat.properties?.year || 2025})</div>
          <div>Mapper: <b class="text-slate-900">${authorName}</b></div>
          <div>Status: <span class="font-bold font-mono text-slate-800">${taskStatus}</span></div>
        </div>
        <button id="btn-popup-review-${feat.properties?.id}" class="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-1 px-2 rounded-lg text-[10px] cursor-pointer shadow-xs transition-colors">
          🎯 Review Grid Ini
        </button>
      `

      l.bindPopup(popupHtml, { maxWidth: 220 })

      l.on('popupopen', () => {
        const btn = document.getElementById(`btn-popup-review-${feat.properties?.id}`)
        if (btn) {
          btn.onclick = () => {
            const tId = feat.properties?.task_grid_id
            const target = tasksStore.tasks.find(t => t.id === tId) ||
              overviewData.value.by_grid.find(g => g.task_id === tId)
            if (target) {
              selectTaskByGridItem(target)
            }
          }
        }
      })

      qcFeatureGroup.addLayer(l)
    })
  })

  // Fit bounds to all mosaic features
  if (qcFeatureGroup.getLayers().length > 0) {
    qcMap.fitBounds(qcFeatureGroup.getBounds(), { padding: [30, 30] })
  }
}

const ensureMapInitialized = () => {
  if (!qcMap) {
    const container = document.getElementById('qc-map-container')
    if (!container) return

    qcMap = L.map('qc-map-container', {
      center: [-0.947, 100.370],
      zoom: 12,
      zoomControl: false
    })

    L.control.zoom({ position: 'bottomright' }).addTo(qcMap)
    L.control.scale({
      position: 'bottomleft',
      metric: true,
      imperial: false,
      maxWidth: 150
    }).addTo(qcMap)

    // Context layer group (background)
    qcContextFeatureGroup = L.featureGroup().addTo(qcMap)
    // Primary layer group (foreground)
    qcFeatureGroup = L.featureGroup().addTo(qcMap)
  }
}

const fitMapBounds = () => {
  if (!qcMap) return
  if (viewScope.value === 'single' && selectedTask.value) {
    const bounds = [[selectedTask.value.min_lat, selectedTask.value.min_lon], [selectedTask.value.max_lat, selectedTask.value.max_lon]]
    qcMap.fitBounds(bounds, { padding: [30, 30] })
  } else if (qcFeatureGroup && qcFeatureGroup.getLayers().length > 0) {
    qcMap.fitBounds(qcFeatureGroup.getBounds(), { padding: [30, 30] })
  }
}

const updateQCTileLayer = (year = 2025) => {
  if (!qcMap) return
  if (qcTileLayer) qcMap.removeLayer(qcTileLayer)

  if (qcLayer.value === 'local_s2_rgb' || qcLayer.value === 'local_s2_cir') {
    const mode = qcLayer.value === 'local_s2_cir' ? 'cir' : 'rgb'
    const gridCode = viewScope.value === 'single' ? selectedTask.value?.grid_code : null
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
  if (qcFeatureGroup) {
    qcFeatureGroup.eachLayer(l => {
      l.setStyle({ fillOpacity: qcOpacity.value })
    })
  }
  if (qcContextFeatureGroup) {
    qcContextFeatureGroup.eachLayer(l => {
      l.setStyle({ fillOpacity: Math.max(0.15, qcOpacity.value * 0.45) })
    })
  }
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
    case 'IN_PROGRESS': return 'Dalam Proses'
    default: return status || 'Tersedia'
  }
}

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'APPROVED': return 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold'
    case 'SUBMITTED': return 'bg-orange-100 text-orange-800 border-orange-300 font-bold'
    case 'REVISION_NEEDED': return 'bg-rose-100 text-rose-800 border-rose-300 font-bold'
    case 'IN_PROGRESS': return 'bg-blue-100 text-blue-800 border-blue-300 font-bold'
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
      await refreshAllData()
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
      await refreshAllData()
    }
  } finally {
    loadingAction.value = false
  }
}
const assignCurrentTaskToUser = async () => {
  if (!selectedTask.value) return
  loadingAction.value = true
  try {
    const res = await api.assignTask(selectedTask.value.id, selectedAssignUserId.value)
    alert(res.data.message || 'Penugasan grid berhasil diperbarui!')
    selectedTask.value.assigned_user_id = selectedAssignUserId.value
    if (res.data.assigned_user_name !== undefined) {
      selectedTask.value.assigned_user_name = res.data.assigned_user_name
    }
    if (res.data.status) {
      selectedTask.value.status = res.data.status
    }
    await refreshAllData()
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal mengubah penugasan grid.')
  } finally {
    loadingAction.value = false
  }
}
</script>

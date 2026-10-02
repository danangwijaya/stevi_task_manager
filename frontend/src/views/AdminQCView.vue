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
    <div class="grid grid-cols-1 xl:grid-cols-12 gap-5 items-stretch">
      
      <!-- LEFT COLUMN: Segmented Overview & Task Queue (4 cols, full matched height) -->
      <div v-if="!isSidebarCollapsed" class="xl:col-span-4 bg-white border border-slate-200 rounded-3xl p-4 sm:p-5 shadow-sm flex flex-col gap-3.5 h-full">
        
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

          <!-- Project / Wilayah Selector -->
          <div class="space-y-1.5">
            <label for="qc-project-filter" class="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider px-0.5">
              <span class="flex items-center gap-1.5">
                <Globe :size="12" class="text-indigo-600" />
                <span>Proyek / Wilayah:</span>
              </span>
              <span class="font-mono text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200 text-[10px] truncate max-w-[160px]">
                {{ activeProjectName }}
              </span>
            </label>
            <div class="relative">
              <select
                id="qc-project-filter"
                v-model="selectedProjectId"
                @change="onProjectChange"
                class="w-full appearance-none bg-white border border-slate-300 hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-400/20 rounded-xl px-3 py-2 pr-8 text-xs font-bold text-slate-800 transition-all cursor-pointer shadow-2xs focus:outline-none"
              >
                <option :value="null">🌐 Semua Wilayah Proyek</option>
                <option v-for="proj in tasksStore.projects" :key="proj.id" :value="proj.id">
                  {{ proj.name }} ({{ (proj.available_years || []).join(', ') }})
                </option>
              </select>
              <div class="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none text-slate-400">
                <ChevronDown :size="14" />
              </div>
            </div>
          </div>

          <!-- Year Filter Dropdown List (Dynamic based on selected project) -->
          <div class="space-y-1.5">
            <label for="qc-year-filter" class="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider px-0.5">
              <span class="flex items-center gap-1.5">
                <Calendar :size="12" class="text-rose-600" />
                <span>Filter Tahun Citra:</span>
              </span>
              <span class="font-mono text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200 text-[10px]">
                {{ selectedYear === 'ALL' ? 'Semua Tahun' : `Tahun ${selectedYear}` }}
              </span>
            </label>
            <div class="relative">
              <select
                id="qc-year-filter"
                :value="selectedYear"
                @change="setQcYear($event.target.value === 'ALL' ? 'ALL' : Number($event.target.value))"
                class="w-full appearance-none bg-white border border-slate-300 hover:border-rose-400 focus:border-rose-500 focus:ring-2 focus:ring-rose-400/20 rounded-xl px-3 py-2 pr-8 text-xs font-bold text-slate-800 transition-all cursor-pointer shadow-2xs focus:outline-none"
              >
                <option v-for="yr in availableQcYears" :key="yr" :value="yr">
                  {{ yr === 'ALL' ? '🌐 Semua Tahun (Mosaik Global)' : `📅 Tahun ${yr} ${yr === latestAvailableYear ? '(Terbaru / Aktif)' : ''}` }}
                </option>
              </select>
              <div class="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none text-slate-400">
                <ChevronDown :size="14" />
              </div>
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
          <div class="space-y-2 overflow-y-auto flex-1 min-h-[350px] max-h-[750px] xl:max-h-[860px] pr-1">
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

      <!-- RIGHT COLUMN: Embedded Live Map & Review Inspector (8 or 12 cols, matched height) -->
      <div
        :class="isSidebarCollapsed ? 'xl:col-span-12' : 'xl:col-span-8'"
        class="bg-white border border-slate-200 rounded-3xl p-5 sm:p-6 shadow-sm flex flex-col gap-4 transition-all duration-300 h-full"
      >
        
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

          <!-- Quick Actions & View Controls -->
          <div class="flex items-center gap-2 shrink-0 flex-wrap">
            <!-- Sidebar Collapse / Expand Toggle Button -->
            <button
              @click="toggleSidebarCollapse"
              class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs"
              :title="isSidebarCollapsed ? 'Tampilkan Antrean Grid' : 'Ciutkan Antrean untuk Memperlebar Peta (100% Layar)'"
            >
              <component :is="isSidebarCollapsed ? PanelLeft : PanelLeftClose" :size="14" />
              <span>{{ isSidebarCollapsed ? 'Buka Antrean' : 'Perluas Peta (100%)' }}</span>
            </button>

            <!-- Map Height Toggle Button -->
            <button
              @click="toggleMapFullHeight"
              class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs"
              :title="isMapFullHeight ? 'Kembalikan Tinggi Standar Peta' : 'Perbesar Kanvas Peta Sangat Tinggi (800px)'"
            >
              <Maximize2 :size="13" />
              <span>{{ isMapFullHeight ? 'Tinggi Standar' : 'Peta Tinggi (800px)' }}</span>
            </button>

            <button
              @click="fitMapBounds"
              class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-3 py-2 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs"
              title="Sesuaikan zoom peta dengan cakupan poligon"
            >
              <Focus :size="13" />
              <span>Zoom Pas</span>
            </button>

            <router-link
              v-if="selectedTask"
              :to="{ path: '/map', query: { taskId: selectedTask.id } }"
              class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-2 shadow-xs cursor-pointer shrink-0"
              title="Buka grid ini di Studio Digitasi Lengkap untuk mengedit poligon"
            >
              <ExternalLink :size="14" />
              <span>Buka di Studio</span>
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

              <!-- QC Repair Toolbox Button (Single mode) -->
              <button
                v-if="viewScope === 'single' && selectedTask"
                @click="openRepairToolboxModal"
                class="px-3 py-1 bg-gradient-to-r from-violet-50 to-indigo-50 hover:from-violet-100 hover:to-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-[11px] font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
                title="Buka kotak alat perbaikan topologi dengan konfigurasi opsi"
              >
                <Sliders :size="12" class="text-indigo-600" />
                <span>Kotak Alat QC</span>
              </button>

              <!-- Version History Button (Single mode) -->
              <button
                v-if="viewScope === 'single' && selectedTask"
                @click="openHistoryModal"
                class="px-3 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-[11px] font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
                title="Lihat riwayat versi snapshot poligon dan pemulihan (Rollback)"
              >
                <History :size="12" class="text-indigo-600" />
                <span>Riwayat Versi</span>
              </button>

              <!-- Add Review Pin Button (Single mode) -->
              <button
                v-if="viewScope === 'single' && selectedTask"
                @click="toggleAddPinMode"
                class="px-3 py-1 rounded-xl text-[11px] font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs border"
                :class="isAddPinMode
                  ? 'bg-amber-600 text-white border-amber-600 ring-2 ring-amber-400/40'
                  : 'bg-amber-50 hover:bg-amber-100 text-amber-800 border-amber-200'"
                title="Klik peta untuk menaruh pin / tanda catatan revisi untuk mapper"
              >
                <MapPin :size="12" />
                <span>{{ isAddPinMode ? 'Mode Pin Aktif (Klik Peta)' : 'Tambah Pin Revisi' }}</span>
              </button>
            </div>
          </div>

          <!-- Leaflet Map Container (Enlarged for High-Detail QC) -->
          <div
            id="qc-map-container"
            class="w-full z-0 transition-[height] duration-300"
            :class="isMapFullHeight ? 'h-[780px] xl:h-[820px]' : 'h-[620px] xl:h-[680px]'"
          ></div>

          <!-- Pin Mode Active Indicator on Map -->
          <div
            v-if="isAddPinMode"
            class="absolute top-4 left-1/2 -translate-x-1/2 z-30 bg-slate-900/95 backdrop-blur-md text-slate-100 px-3.5 py-1.5 rounded-xl shadow-xl flex items-center gap-2.5 text-xs font-semibold border border-slate-700 animate-in fade-in slide-in-from-top-2"
          >
            <MapPin :size="14" class="text-amber-400 shrink-0" />
            <span>Klik pada posisi peta untuk menaruh pin revisi</span>
            <button
              @click="toggleAddPinMode"
              class="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-[10px] font-bold cursor-pointer transition-colors border border-slate-600"
            >
              Batal (Esc)
            </button>
          </div>

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
          class="bg-rose-50 border border-rose-300 p-3.5 rounded-2xl text-xs text-rose-950 space-y-2.5 shadow-sm"
        >
          <div class="flex items-center justify-between font-bold text-rose-900 border-b border-rose-200/80 pb-2">
            <span class="flex items-center gap-2">
              <AlertTriangle :size="16" class="text-rose-600 shrink-0" />
              <span>Daftar Masalah Topologi ({{ qcTopologyResult.errors.length }} Masalah Ditemukan):</span>
            </span>
            <div class="flex items-center gap-2">
              <button
                @click="openRepairToolboxModal"
                class="px-2.5 py-1 bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-300 rounded-lg text-[10px] font-bold flex items-center gap-1.5 shadow-2xs transition-all cursor-pointer"
                title="Buka kotak alat perbaikan topologi (pilih metode, prioritas klip, dan toleransi)"
              >
                <Sliders :size="12" class="text-indigo-600" />
                <span>Opsi Perbaikan...</span>
              </button>
              <button
                @click="handleAutoHealTopology"
                :disabled="isAutoHealing"
                class="px-2.5 py-1 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 disabled:opacity-50 text-white rounded-lg text-[10px] font-bold flex items-center gap-1.5 shadow-xs transition-all cursor-pointer"
                title="Perbaiki self-intersection, bersihkan serpihan sliver, dan rapikan geometri otomatis"
              >
                <Wand2 :size="12" :class="{ 'animate-spin': isAutoHealing }" />
                <span>{{ isAutoHealing ? 'Memperbaiki...' : '⚡ Perbaiki Cepat' }}</span>
              </button>
              <button @click="qcTopologyResult = null" class="text-rose-400 hover:text-rose-700 cursor-pointer p-0.5 rounded">
                <X :size="15" />
              </button>
            </div>
          </div>

          <!-- Stepper Navigator Top Bar -->
          <div class="flex items-center justify-between bg-white/95 border border-rose-200/90 rounded-xl px-3 py-1.5 text-xs shadow-2xs">
            <div class="flex items-center gap-2 font-bold text-slate-700">
              <span class="text-rose-700 flex items-center gap-1">
                <MapPin :size="12" />
                <span>Navigator Masalah:</span>
              </span>
              <span class="font-mono text-slate-900 font-black bg-rose-50 text-rose-700 px-2 py-0.5 rounded-lg border border-rose-200">
                {{ currentErrorIndex + 1 }} / {{ qcTopologyResult.errors.length }}
              </span>
              <span v-if="qcTopologyResult.errors[currentErrorIndex]" class="text-[11px] font-semibold text-slate-500 truncate max-w-[200px] sm:max-w-xs">
                ({{ qcTopologyResult.errors[currentErrorIndex].type }})
              </span>
            </div>
            <div class="flex items-center gap-1.5">
              <button
                @click="prevError"
                class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer transition-colors shadow-2xs"
                title="Sorot masalah sebelumnya"
              >
                <ChevronLeft :size="13" />
                <span>Sebelumnya</span>
              </button>
              <button
                @click="nextError"
                class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer transition-colors shadow-2xs"
                title="Sorot masalah berikutnya"
              >
                <span>Selanjutnya</span>
                <ChevronRight :size="13" />
              </button>
            </div>
          </div>

          <!-- Interactive Error List -->
          <div class="space-y-1.5 max-h-64 overflow-y-auto pr-1">
            <div
              v-for="(err, idx) in qcTopologyResult.errors"
              :key="idx"
              :id="'qc-err-' + idx"
              @click="focusTopologyError(err)"
              class="p-2.5 rounded-xl transition-all cursor-pointer shadow-2xs group flex flex-col md:flex-row md:items-center justify-between gap-2 border"
              :class="activeQcInspectorError === err
                ? 'border-rose-500 bg-rose-100/70 shadow-sm ring-2 ring-rose-400'
                : 'bg-white border-rose-200 hover:border-rose-400 hover:bg-rose-50/50'"
            >
              <div class="flex items-start gap-2.5 min-w-0">
                <span
                  class="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase shrink-0 border"
                  :class="err.type === 'SELF_INTERSECTION'
                    ? 'bg-rose-100 text-rose-800 border-rose-300'
                    : err.type === 'OVERLAP'
                    ? 'bg-amber-100 text-amber-800 border-amber-300'
                    : 'bg-red-100 text-red-800 border-red-300'"
                >
                  {{ err.type }}
                </span>

                <div class="min-w-0 space-y-0.5">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span v-if="err.annotation_id" class="font-bold text-slate-900 font-mono text-[11px]">
                      Poligon #{{ err.annotation_id }}
                    </span>
                    <span v-else-if="err.annotation_ids" class="font-bold text-slate-900 font-mono text-[11px]">
                      Poligon #{{ err.annotation_ids.join(' & #') }}
                    </span>
                    <span v-if="err.class_name" class="text-[10px] font-medium text-slate-600 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200">
                      {{ err.class_name }}
                    </span>
                    <span v-else-if="err.class_names" class="text-[10px] font-medium text-slate-600 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200">
                      {{ err.class_names.join(', ') }}
                    </span>
                  </div>
                  <p class="text-[11px] text-rose-800 break-words leading-relaxed">
                    {{ err.message }}
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-1.5 shrink-0 self-end md:self-center flex-wrap justify-end">
                <!-- Tombol Sorot -->
                <button
                  @click.stop="focusTopologyError(err)"
                  class="px-2 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                  title="Sorot dan Zoom Detil (< 100m) ke Masalah Ini"
                >
                  <MapPin :size="11" />
                  <span>Sorot</span>
                </button>

                <!-- Tombol 1-Click: Jadikan Pin Revisi untuk Mapper -->
                <button
                  @click.stop="convertErrorToReviewPin(err)"
                  class="px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                  title="Tandai koordinat masalah ini sebagai Pin Catatan Revisi untuk dikerjakan Mapper"
                >
                  <MessageSquarePlus :size="11" />
                  <span>Jadikan Pin Revisi</span>
                </button>

                <!-- Tool Khusus: Atasi Overlap Berpilihan -->
                <button
                  v-if="err.type === 'OVERLAP' && err.annotation_ids && err.annotation_ids.length >= 2"
                  @click.stop="openResolveOverlapModal(err)"
                  class="px-2 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                  title="Pilih cara mengatasi overlap (potong A oleh B, potong B oleh A, atau gabungkan)"
                >
                  <Scissors :size="11" />
                  <span>Atasi Overlap...</span>
                </button>

                <!-- Tool Khusus: Gabung Cepat (Merge) jika 2 poligon -->
                <button
                  v-if="err.annotation_ids && err.annotation_ids.length >= 2"
                  @click.stop="executeQcInspectorMerge"
                  :disabled="isQcInspectorLoading"
                  class="px-2 py-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                  title="Gabung poligon yang tumpang tindih ini menjadi satu poligon utuh"
                >
                  <Combine :size="11" />
                  <span>Gabung</span>
                </button>

                <!-- Tool Khusus: Rapikan Geometri Invalid / Self-Intersection -->
                <button
                  v-if="(err.type === 'SELF_INTERSECTION' || err.type === 'INVALID_GEOM') && err.annotation_id"
                  @click.stop="handleRepairSingleGeometry(err.annotation_id)"
                  :disabled="isRepairingSingleGeom[err.annotation_id]"
                  class="px-2 py-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                  title="Rapikan simpul melintir dan perbaiki geometri poligon ini"
                >
                  <Wand2 :size="11" :class="{ 'animate-spin': isRepairingSingleGeom[err.annotation_id] }" />
                  <span>{{ isRepairingSingleGeom[err.annotation_id] ? 'Merapikan...' : 'Rapikan Geometri' }}</span>
                </button>

                <!-- Tool Khusus: Assign Kelas untuk Unclassified -->
                <button
                  v-if="err.type === 'UNCLASSIFIED' && err.annotation_ids && err.annotation_ids.length > 0"
                  @click.stop="openAssignClassModal(err.annotation_ids[0])"
                  class="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                  title="Tetapkan kelas tutupan lahan untuk poligon ini"
                >
                  <Tag :size="11" />
                  <span>Pilih Kelas</span>
                </button>

                <!-- Tool Khusus: Isi Celah Kosong (Gap) -->
                <button
                  v-if="err.type === 'GAP' || err.type === 'SMALL_GAP'"
                  @click.stop="openFillGapsModal"
                  class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-[10px] font-bold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                  title="Tutup area kosong pada grid dengan poligon baru"
                >
                  <Layers :size="11" />
                  <span>Isi Celah</span>
                </button>

                <button
                  v-if="err.annotation_id && taskFeatures.find(f => f.id === err.annotation_id)"
                  @click.stop="handleDeleteProblematicAnnotation(err.annotation_id)"
                  class="px-2 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-[10px] font-bold flex items-center gap-1 transition-colors cursor-pointer"
                  title="Hapus Poligon Cacat Ini"
                >
                  <Trash2 :size="11" />
                  <span>Hapus</span>
                </button>
              </div>
            </div>
          </div>
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
                :key="poly.id || idx"
                :id="'qc-poly-' + poly.id"
                @click="selectPolygon(poly)"
                @mouseenter="highlightPolygonOnMap(poly.id, true)"
                @mouseleave="highlightPolygonOnMap(poly.id, false)"
                class="p-2 rounded-xl flex items-center justify-between text-xs transition-all cursor-pointer border group"
                :class="selectedPolygonId === poly.id
                  ? 'bg-cyan-50/90 border-cyan-400 shadow-xs ring-2 ring-cyan-400/40'
                  : hasTopologyError(poly.id)
                  ? 'bg-rose-50/50 border-rose-300 hover:border-rose-400 hover:bg-rose-50 ring-1 ring-rose-300/50'
                  : 'bg-white border-slate-200 hover:border-cyan-300 hover:bg-slate-50/80'"
              >
                <div class="flex items-center gap-2 truncate">
                  <div
                    class="w-3 h-3 rounded-sm border border-slate-300 shrink-0 shadow-2xs"
                    :style="{ backgroundColor: getClassColor(poly.properties?.class_id) }"
                  ></div>
                  <span class="font-bold text-slate-800 truncate text-[11px]">{{ poly.properties?.class_name || 'Belum Teridentifikasi' }}</span>
                  <!-- Topology Error Warning Badge -->
                  <span
                    v-if="hasTopologyError(poly.id)"
                    class="flex items-center gap-0.5 px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 bg-rose-100 text-rose-800 border border-rose-300 animate-pulse"
                    :title="getTopologyErrorsForPolygon(poly.id).map(e => e.message).join('\n')"
                  >
                    <AlertTriangle :size="10" />
                    <span>Error Topologi</span>
                  </span>
                  <!-- Review Pin Badge on Polygon -->
                  <span
                    v-if="getPolygonPins(poly.id).length > 0"
                    class="flex items-center gap-0.5 px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0"
                    :class="getPolygonPins(poly.id).every(p => p.status === 'RESOLVED')
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800 animate-pulse'"
                    :title="`${getPolygonPins(poly.id).length} catatan revisi pada poligon ini`"
                  >
                    <MapPin :size="10" />
                    <span>{{ getPolygonPins(poly.id).length }}</span>
                  </span>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <span class="text-[10px] text-slate-500 font-mono bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200">
                    ~{{ Math.round((poly.properties?.area_sqm || 10000) / 10000) }} Ha
                  </span>
                  <button
                    @click.stop="openAssignClassModal(poly.id, poly.properties?.class_id)"
                    class="p-1 text-slate-400 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-emerald-200"
                    title="Ubah Kelas Tutupan Lahan Poligon Ini"
                  >
                    <Tag :size="13" />
                  </button>
                  <button
                    @click.stop="handleRepairSingleGeometry(poly.id)"
                    :disabled="isRepairingSingleGeom[poly.id]"
                    class="p-1 text-slate-400 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-purple-200"
                    title="Perbaiki / Rapikan Geometri Poligon Ini"
                  >
                    <Wand2 :size="13" :class="{ 'animate-spin': isRepairingSingleGeom[poly.id] }" />
                  </button>
                  <button
                    @click.stop="openPinModalForPolygon(poly)"
                    class="p-1 text-slate-400 hover:text-amber-700 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-amber-200"
                    title="Beri Catatan Revisi untuk Poligon Ini"
                  >
                    <MessageSquarePlus :size="13" />
                  </button>
                  <button
                    @click.stop="handleDeleteProblematicAnnotation(poly.id)"
                    class="p-1 text-slate-400 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-rose-200"
                    title="Hapus Poligon Ini"
                  >
                    <Trash2 :size="13" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Review Pins List for Active Grid -->
            <div class="mt-3 pt-3 border-t border-slate-200 space-y-2">
              <div class="flex items-center justify-between text-xs font-bold text-slate-700">
                <span class="flex items-center gap-1.5">
                  <MapPin :size="13" class="text-rose-600" />
                  <span>Catatan Revisi Supervisi ({{ tasksStore.currentTaskReviewPins.length }})</span>
                </span>
                <span
                  v-if="tasksStore.currentTaskReviewPins.length > 0"
                  class="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold"
                  :class="allPinsResolved ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'"
                >
                  {{ resolvedPinsCount }}/{{ tasksStore.currentTaskReviewPins.length }} Selesai
                </span>
              </div>

              <div v-if="tasksStore.currentTaskReviewPins.length === 0" class="text-slate-400 text-[11px] italic py-2 text-center">
                Belum ada tanda catatan revisi pada grid ini.
              </div>

              <div v-else class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                <div
                  v-for="pin in tasksStore.currentTaskReviewPins"
                  :key="pin.id"
                  class="p-2 rounded-xl border text-xs flex flex-col gap-1 transition-all shadow-2xs"
                  :class="pin.status === 'RESOLVED' ? 'bg-emerald-50/60 border-emerald-200' : 'bg-rose-50/60 border-rose-200'"
                >
                  <div class="flex items-center justify-between">
                    <span
                      class="font-bold flex items-center gap-1 text-[11px]"
                      :class="pin.status === 'RESOLVED' ? 'text-emerald-800' : 'text-rose-800'"
                    >
                      <CheckCircle2 v-if="pin.status === 'RESOLVED'" :size="12" class="text-emerald-600" />
                      <AlertTriangle v-else :size="12" class="text-rose-600" />
                      <span>{{ pin.status === 'RESOLVED' ? 'Selesai Dikerjakan' : 'Perlu Revisi' }}</span>
                    </span>
                    <div class="flex items-center gap-1">
                      <button
                        @click="focusOnPin(pin)"
                        class="p-1 text-slate-500 hover:text-indigo-600 hover:bg-white rounded transition-colors cursor-pointer"
                        title="Lihat Titik di Peta"
                      >
                        <Focus :size="12" />
                      </button>
                      <button
                        @click="deleteReviewPin(pin.id)"
                        class="p-1 text-slate-400 hover:text-rose-600 hover:bg-white rounded transition-colors cursor-pointer"
                        title="Hapus Catatan"
                      >
                        <Trash2 :size="12" />
                      </button>
                    </div>
                  </div>
                  <p class="text-[11px] text-slate-800 italic leading-snug">"{{ pin.note }}"</p>
                  <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-0.5">
                    <span>Oleh: {{ pin.reviewer_name || 'Reviewer' }}</span>
                    <span v-if="pin.resolved_by_name" class="text-emerald-700 font-sans font-bold">
                      ✓ {{ pin.resolved_by_name }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Review Actions & Decision Form (7 cols) -->
          <div class="lg:col-span-7 bg-white border border-slate-200 p-4 rounded-2xl flex flex-col justify-between gap-3 shadow-2xs">
            
            <!-- Admin / Reviewer Assign Grid to Account -->
            <div v-if="authStore.isReviewer || authStore.isAdmin" class="p-3 bg-indigo-50/70 border border-indigo-200 rounded-xl space-y-1.5 shadow-2xs overflow-hidden">
              <div class="flex items-center justify-between text-[11px] font-bold text-indigo-950">
                <span class="flex items-center gap-1.5"><UserCheck :size="13" class="text-indigo-600" /> Penugasan Grid Ini:</span>
                <span class="text-indigo-700 font-semibold truncate max-w-[200px]">{{ selectedTask.assigned_user_name || 'Belum Ditugaskan' }}</span>
              </div>
              <div class="flex items-center gap-2 min-w-0">
                <select
                  v-model="selectedAssignUserId"
                  class="flex-1 min-w-0 bg-white border border-indigo-200 hover:border-indigo-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium truncate focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
                >
                  <option :value="null">-- Lepas Penugasan (Tersedia) --</option>
                  <option v-for="u in userList" :key="u.id" :value="u.id">
                    {{ u.full_name || u.username }} ({{ u.role }})
                  </option>
                </select>
                <button
                  @click="assignCurrentTaskToUser"
                  :disabled="loadingAction"
                  class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer shrink-0 whitespace-nowrap disabled:opacity-50 shadow-xs"
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

    <!-- Modal: Beri Catatan Revisi / Pin Baru -->
    <div
      v-if="showPinModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in"
    >
      <div class="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl border border-slate-100 space-y-4 animate-in zoom-in-95 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-2xl bg-gradient-to-tr from-amber-500 to-rose-500 text-white flex items-center justify-center shadow-md">
              <MapPin :size="18" />
            </div>
            <div>
              <h3 class="font-extrabold text-slate-900 text-sm tracking-tight">Catatan Evaluasi / Pin Revisi</h3>
              <p class="text-[11px] text-slate-500">
                {{ pinModalData.annotation_id ? `Terkait poligon ${pinModalData.class_name}` : 'Pin bebas di titik koordinat peta' }}
              </p>
            </div>
          </div>
          <button
            @click="showPinModal = false"
            class="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="space-y-3 text-xs">
          <!-- Koordinat & Lokasi -->
          <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-slate-600 space-y-1 font-mono text-[11px]">
            <div class="flex justify-between items-center">
              <span class="font-sans text-slate-500 font-medium">📍 Koordinat Pin:</span>
              <span class="font-bold text-slate-900 bg-white px-2 py-0.5 rounded-md border border-slate-200">{{ pinModalData.lat }}, {{ pinModalData.lon }}</span>
            </div>
            <div class="flex justify-between items-center font-sans">
              <span class="text-slate-500 font-medium">Konteks Lokasi:</span>
              <span v-if="pinModalData.annotation_id" class="font-bold text-indigo-700 text-xs">
                Poligon {{ pinModalData.class_name }} (#{{ pinModalData.annotation_id }})
              </span>
              <span v-else class="text-emerald-700 font-medium text-xs">
                Area Bebas (Tidak terikat poligon)
              </span>
            </div>
          </div>

          <!-- Kategori Isu / Evaluasi -->
          <div class="space-y-1">
            <label class="font-bold text-slate-700 block">Kategori Evaluasi:</label>
            <div class="grid grid-cols-3 gap-1 text-[11px]">
              <button
                v-for="cat in ['Batas Kurang Pas', 'Salah Label Kelas', 'Objek Terlewat', 'Celah / Overlap', 'Kerapian Poligon', 'Catatan Umum']"
                :key="cat"
                type="button"
                @click="pinModalData.category = cat"
                class="px-2 py-1.5 rounded-xl border text-center font-bold transition-all cursor-pointer truncate"
                :class="pinModalData.category === cat
                  ? 'bg-amber-50 border-amber-400 text-amber-900 ring-2 ring-amber-400/30'
                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'"
              >
                {{ cat }}
              </button>
            </div>
          </div>

          <!-- Input Note -->
          <div class="space-y-1">
            <label class="font-bold text-slate-700">Pesan / Instruksi Revisi untuk Mapper:</label>
            <textarea
              v-model="pinModalData.note"
              rows="3"
              placeholder="Contoh: Batas poligon tolong disesuaikan dengan kenampakan citra satelit terbaru..."
              class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-amber-500 focus:outline-none text-xs text-slate-800 font-medium leading-relaxed"
            ></textarea>
          </div>

          <!-- Template Cepat -->
          <div class="flex flex-wrap gap-1 text-[10px]">
            <button
              type="button"
              @click="pinModalData.note = 'Batas poligon masih kurang rapi, harap disesuaikan dengan kenampakan citra.'; pinModalData.category = 'Batas Kurang Pas'"
              class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 rounded border text-slate-600 cursor-pointer"
            >
              Batas kurang rapi
            </button>
            <button
              type="button"
              @click="pinModalData.note = 'Kelas tutupan lahan tidak sesuai, mohon dicek ulang interpretasinya.'; pinModalData.category = 'Salah Label Kelas'"
              class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 rounded border text-slate-600 cursor-pointer"
            >
              Salah kelas
            </button>
            <button
              type="button"
              @click="pinModalData.note = 'Ada area yang terlewat dan belum terdigitasi di titik ini.'; pinModalData.category = 'Objek Terlewat'"
              class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 rounded border text-slate-600 cursor-pointer"
            >
              Area belum terdigitasi
            </button>
            <button
              type="button"
              @click="pinModalData.note = 'Terdapat celah / tumpang tindih poligon pada titik ini, tolong dirapikan.'; pinModalData.category = 'Celah / Overlap'"
              class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 rounded border text-slate-600 cursor-pointer"
            >
              Celah / Overlap
            </button>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <button
            @click="showPinModal = false"
            class="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            Batal
          </button>
          <button
            @click="saveNewReviewPin"
            :disabled="submittingPin || !pinModalData.note.trim()"
            class="px-4 py-2 bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-700 hover:to-rose-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <RotateCw v-if="submittingPin" :size="13" class="animate-spin" />
            <MapPin v-else :size="13" />
            <span>Simpan Catatan Pin</span>
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 1: Toolbox Perbaikan Topologi Grid (Dengan Pilihan Konfigurasi Lengkap) -->
    <div
      v-if="showRepairToolboxModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in"
    >
      <div class="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl border border-slate-100 space-y-5 animate-in zoom-in-95 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3.5">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 text-white flex items-center justify-center shadow-md">
              <Sliders :size="18" />
            </div>
            <div>
              <h3 class="font-extrabold text-slate-900 text-sm tracking-tight">Kotak Alat Perbaikan Topologi</h3>
              <p class="text-[11px] text-slate-500 font-mono">
                Grid: {{ selectedTask?.grid_code || 'Belum Dipilih' }} (Pilih aksi yang ingin diterapkan)
              </p>
            </div>
          </div>
          <button
            @click="showRepairToolboxModal = false"
            class="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="space-y-4 text-xs">
          <!-- Opsi 1: Duplikat -->
          <div class="p-3.5 rounded-2xl border transition-all" :class="repairOptions.remove_duplicates ? 'bg-violet-50/60 border-violet-200' : 'bg-slate-50 border-slate-200'">
            <label class="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                v-model="repairOptions.remove_duplicates"
                class="mt-0.5 rounded text-violet-600 focus:ring-violet-500 w-4 h-4 cursor-pointer"
              />
              <div class="space-y-0.5">
                <span class="font-bold text-slate-900 block">1. Bersihkan Layer Duplikat Bertumpuk (>90%)</span>
                <span class="text-[11px] text-slate-500 block leading-relaxed">
                  Menghapus poligon bayangan yang menumpuk persis di area yang sama, mengutamakan kelas spesifik dibanding kelas latar belakang / Belum Teridentifikasi.
                </span>
              </div>
            </label>
          </div>

          <!-- Opsi 2: Geometri Rusak & Self-Intersection -->
          <div class="p-3.5 rounded-2xl border transition-all" :class="repairOptions.heal_geometries ? 'bg-indigo-50/60 border-indigo-200' : 'bg-slate-50 border-slate-200'">
            <label class="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                v-model="repairOptions.heal_geometries"
                class="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
              />
              <div class="space-y-0.5">
                <span class="font-bold text-slate-900 block">2. Perbaiki Geometri Rusak & Self-Intersection</span>
                <span class="text-[11px] text-slate-500 block leading-relaxed">
                  Merapikan simpul melintir (*bow-tie*), garis batas saling silang, dan lubang dalam kolaps menggunakan algoritma Shapely <code>make_valid</code>.
                </span>
              </div>
            </label>
          </div>

          <!-- Opsi 3: Pangkas Overlap & Pilihan Prioritas -->
          <div class="p-3.5 rounded-2xl border transition-all space-y-2.5" :class="repairOptions.clip_overlaps ? 'bg-amber-50/60 border-amber-200' : 'bg-slate-50 border-slate-200'">
            <label class="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                v-model="repairOptions.clip_overlaps"
                class="mt-0.5 rounded text-amber-600 focus:ring-amber-500 w-4 h-4 cursor-pointer"
              />
              <div class="space-y-0.5">
                <span class="font-bold text-slate-900 block">3. Pangkas Irisan Tumpang Tindih (Auto-Clip Overlap)</span>
                <span class="text-[11px] text-slate-500 block leading-relaxed">
                  Memotong bagian irisan yang bertabrakan agar batas poligon saling menempel rapi tanpa tumpang tindih.
                </span>
              </div>
            </label>

            <!-- Sub-options: Prioritas Pemotongan -->
            <div v-if="repairOptions.clip_overlaps" class="pl-7 space-y-1.5 pt-1 border-t border-amber-200/60">
              <div class="text-[11px] font-bold text-amber-900">Prioritas Pemotongan (Objek mana yang diutamakan utuh?):</div>
              <div class="space-y-1 text-[11px]">
                <label class="flex items-center gap-2 cursor-pointer p-1.5 rounded-lg hover:bg-amber-100/50">
                  <input
                    type="radio"
                    value="smaller_first"
                    v-model="repairOptions.overlap_priority"
                    class="text-amber-600 focus:ring-amber-500"
                  />
                  <span><b>Poligon Kecil Memotong Poligon Besar</b> (Disarankan — detail jalan, sungai, & bangunan tetap utuh)</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer p-1.5 rounded-lg hover:bg-amber-100/50">
                  <input
                    type="radio"
                    value="specific_class_first"
                    v-model="repairOptions.overlap_priority"
                    class="text-amber-600 focus:ring-amber-500"
                  />
                  <span><b>Kelas Spesifik Memotong Kelas Umum</b> (Mempertahankan objek bermakna di atas latar belakang hutan/lahan terbuka)</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer p-1.5 rounded-lg hover:bg-amber-100/50">
                  <input
                    type="radio"
                    value="larger_first"
                    v-model="repairOptions.overlap_priority"
                    class="text-amber-600 focus:ring-amber-500"
                  />
                  <span><b>Poligon Besar Memotong Poligon Kecil</b></span>
                </label>
              </div>
            </div>
          </div>

          <!-- Opsi 4: Bersihkan Serpihan Kecil -->
          <div class="p-3.5 rounded-2xl border transition-all space-y-2" :class="repairOptions.remove_slivers ? 'bg-rose-50/60 border-rose-200' : 'bg-slate-50 border-slate-200'">
            <label class="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                v-model="repairOptions.remove_slivers"
                class="mt-0.5 rounded text-rose-600 focus:ring-rose-500 w-4 h-4 cursor-pointer"
              />
              <div class="space-y-0.5">
                <span class="font-bold text-slate-900 block">4. Bersihkan Serpihan Mikroskopis (Sliver Polygons)</span>
                <span class="text-[11px] text-slate-500 block leading-relaxed">
                  Menghapus poligon renik tak sengaja hasil irisan garis atau sisa potongan yang tidak berguna untuk AI training.
                </span>
              </div>
            </label>
            <div v-if="repairOptions.remove_slivers" class="pl-7 flex items-center gap-2 pt-1">
              <span class="text-[11px] font-bold text-slate-600">Ambang Batas Luas:</span>
              <div class="flex items-center gap-1">
                <button
                  v-for="sqm in [0.5, 2.0, 5.0, 10.0]"
                  :key="sqm"
                  type="button"
                  @click="repairOptions.min_sliver_area_sqm = sqm"
                  class="px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-all cursor-pointer"
                  :class="repairOptions.min_sliver_area_sqm === sqm ? 'bg-rose-600 text-white border-rose-600 shadow-xs' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'"
                >
                  &lt; {{ sqm }} m²
                </button>
              </div>
            </div>
          </div>

          <!-- Opsi 5: Tutup Celah Kosong (Gap Filling) -->
          <div class="p-3.5 rounded-2xl border transition-all space-y-2" :class="repairOptions.fill_gaps ? 'bg-emerald-50/60 border-emerald-200' : 'bg-slate-50 border-slate-200'">
            <label class="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                v-model="repairOptions.fill_gaps"
                class="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
              />
              <div class="space-y-0.5">
                <span class="font-bold text-slate-900 block">5. Tutup Sisa Celah Kosong (Fill Residual Gaps)</span>
                <span class="text-[11px] text-slate-500 block leading-relaxed">
                  Secara otomatis membuat poligon baru pada area grid yang masih bolong / belum tercakup digitasi.
                </span>
              </div>
            </label>
            <div v-if="repairOptions.fill_gaps" class="pl-7 space-y-1 pt-1">
              <span class="text-[11px] font-bold text-slate-700">Tugaskan Kelas Tutupan Lahan untuk Celah:</span>
              <select
                v-model="repairOptions.fill_gap_class_id"
                class="w-full p-2 bg-white border border-emerald-300 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option v-for="cls in annotationsStore.classes" :key="cls.id" :value="cls.id">
                  {{ cls.id }}. {{ cls.name }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
          <button
            @click="showRepairToolboxModal = false"
            class="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            Batal
          </button>
          <button
            @click="handleApplyRepairOptions"
            :disabled="isApplyingRepairOptions"
            class="px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer flex items-center gap-2 disabled:opacity-50"
          >
            <RotateCw v-if="isApplyingRepairOptions" :size="13" class="animate-spin" />
            <Sliders v-else :size="13" />
            <span>{{ isApplyingRepairOptions ? 'Menerapkan Perbaikan...' : '🚀 Terapkan Opsi Perbaikan' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 2: Selesaikan Masalah Overlap Antar Dua Poligon Spesifik -->
    <div
      v-if="showOverlapModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in"
    >
      <div class="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl border border-slate-100 space-y-4 animate-in zoom-in-95">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-2xl bg-amber-500 text-white flex items-center justify-center shadow-md">
              <Scissors :size="18" />
            </div>
            <div>
              <h3 class="font-extrabold text-slate-900 text-sm tracking-tight">Atasi Tumpang Tindih (Overlap)</h3>
              <p class="text-[11px] text-slate-500">Pilih bagaimana cara memisahkan dua poligon yang saling bertabrakan</p>
            </div>
          </div>
          <button
            @click="showOverlapModal = false"
            class="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Info Dua Poligon Terkait -->
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div class="p-3 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-1">
            <span class="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">Poligon A</span>
            <div class="font-bold text-slate-900 text-sm font-mono">#{{ overlapModalData.ann_a?.id }}</div>
            <div class="text-[11px] text-slate-700 font-medium truncate">{{ overlapModalData.ann_a?.class_name }}</div>
          </div>

          <div class="p-3 bg-blue-50/70 border border-blue-200 rounded-2xl space-y-1">
            <span class="text-[10px] font-bold text-blue-800 uppercase tracking-wider block">Poligon B</span>
            <div class="font-bold text-slate-900 text-sm font-mono">#{{ overlapModalData.ann_b?.id }}</div>
            <div class="text-[11px] text-slate-700 font-medium truncate">{{ overlapModalData.ann_b?.class_name }}</div>
          </div>
        </div>

        <!-- Pilihan Aksi Interaktif -->
        <div class="space-y-2 pt-1 text-xs">
          <!-- Opsi 1: Potong A oleh B -->
          <button
            type="button"
            @click="executeResolveOverlap('clip_a_by_b')"
            :disabled="overlapModalData.isResolving"
            class="w-full text-left p-3 rounded-2xl border border-slate-200 hover:border-amber-400 hover:bg-amber-50/50 transition-all flex items-start gap-3 cursor-pointer group"
          >
            <div class="p-2 rounded-xl bg-amber-100 text-amber-800 shrink-0 group-hover:bg-amber-500 group-hover:text-white transition-colors">
              <Scissors :size="16" />
            </div>
            <div class="min-w-0">
              <div class="font-bold text-slate-900">Potong Poligon #{{ overlapModalData.ann_a?.id }} oleh Poligon #{{ overlapModalData.ann_b?.id }}</div>
              <div class="text-[11px] text-slate-500 leading-relaxed">
                Irisan dipotong dari Poligon #{{ overlapModalData.ann_a?.id }}. Bentuk Poligon #{{ overlapModalData.ann_b?.id }} <b>dipertahankan utuh 100%</b>.
              </div>
            </div>
          </button>

          <!-- Opsi 2: Potong B oleh A -->
          <button
            type="button"
            @click="executeResolveOverlap('clip_b_by_a')"
            :disabled="overlapModalData.isResolving"
            class="w-full text-left p-3 rounded-2xl border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 transition-all flex items-start gap-3 cursor-pointer group"
          >
            <div class="p-2 rounded-xl bg-blue-100 text-blue-800 shrink-0 group-hover:bg-blue-500 group-hover:text-white transition-colors">
              <Scissors :size="16" />
            </div>
            <div class="min-w-0">
              <div class="font-bold text-slate-900">Potong Poligon #{{ overlapModalData.ann_b?.id }} oleh Poligon #{{ overlapModalData.ann_a?.id }}</div>
              <div class="text-[11px] text-slate-500 leading-relaxed">
                Irisan dipotong dari Poligon #{{ overlapModalData.ann_b?.id }}. Bentuk Poligon #{{ overlapModalData.ann_a?.id }} <b>dipertahankan utuh 100%</b>.
              </div>
            </div>
          </button>

          <!-- Opsi 3: Gabungkan (Merge) -->
          <div class="p-3 rounded-2xl border border-slate-200 hover:border-purple-400 hover:bg-purple-50/40 transition-all space-y-2">
            <div class="flex items-start gap-3">
              <div class="p-2 rounded-xl bg-purple-100 text-purple-800 shrink-0">
                <Combine :size="16" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="font-bold text-slate-900">Gabungkan Kedua Poligon (Merge)</div>
                <div class="text-[11px] text-slate-500 leading-relaxed">
                  Menyatukan #{{ overlapModalData.ann_a?.id }} dan #{{ overlapModalData.ann_b?.id }} menjadi satu kesatuan poligon utuh.
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2 pl-11">
              <select
                v-model="overlapModalData.target_class_id"
                class="p-1.5 bg-white border border-purple-300 rounded-xl text-xs font-bold text-slate-800 focus:outline-none"
              >
                <option v-for="cls in annotationsStore.classes" :key="cls.id" :value="cls.id">
                  Kelas Gabungan: {{ cls.name }}
                </option>
              </select>
              <button
                type="button"
                @click="executeResolveOverlap('merge_into_a', overlapModalData.target_class_id)"
                :disabled="overlapModalData.isResolving"
                class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
              >
                Gabung Sekarang
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <button
            @click="showOverlapModal = false"
            class="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 3: Assign / Ubah Kelas Tutupan Lahan Cepat -->
    <div
      v-if="showAssignClassModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in"
    >
      <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-100 space-y-4 animate-in zoom-in-95">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-2xl bg-emerald-600 text-white flex items-center justify-center shadow-md">
              <Tag :size="18" />
            </div>
            <div>
              <h3 class="font-extrabold text-slate-900 text-sm tracking-tight">Assign / Ubah Kelas Tutupan Lahan</h3>
              <p class="text-[11px] text-slate-500 font-mono">Poligon #{{ assignClassModalData.annotation_id }}</p>
            </div>
          </div>
          <button
            @click="showAssignClassModal = false"
            class="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="space-y-1.5 max-h-72 overflow-y-auto pr-1">
          <div
            v-for="cls in annotationsStore.classes"
            :key="cls.id"
            @click="assignClassModalData.target_class_id = cls.id"
            class="p-2.5 rounded-xl border flex items-center justify-between text-xs cursor-pointer transition-all"
            :class="assignClassModalData.target_class_id === cls.id ? 'bg-emerald-50 border-emerald-400 ring-2 ring-emerald-400/30' : 'bg-slate-50/70 border-slate-200 hover:bg-white'"
          >
            <div class="flex items-center gap-2.5">
              <div class="w-3.5 h-3.5 rounded-md shadow-xs shrink-0" :style="{ backgroundColor: cls.color }"></div>
              <div>
                <span class="font-bold text-slate-900 block">{{ cls.name }}</span>
                <span class="text-[10px] text-slate-400 block">{{ cls.description }}</span>
              </div>
            </div>
            <Check v-if="assignClassModalData.target_class_id === cls.id" :size="16" class="text-emerald-600 shrink-0" />
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
          <button
            @click="showAssignClassModal = false"
            class="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            Batal
          </button>
          <button
            @click="executeAssignClass"
            :disabled="assignClassModalData.isAssigning"
            class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <RotateCw v-if="assignClassModalData.isAssigning" :size="13" class="animate-spin" />
            <Tag v-else :size="13" />
            <span>Simpan Perubahan Kelas</span>
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 4: Tutup Celah Kosong (Fill Grid Gaps) -->
    <div
      v-if="showFillGapsModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in"
    >
      <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-100 space-y-4 animate-in zoom-in-95">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-2xl bg-blue-600 text-white flex items-center justify-center shadow-md">
              <Layers :size="18" />
            </div>
            <div>
              <h3 class="font-extrabold text-slate-900 text-sm tracking-tight">Tutup Celah Kosong (Fill Gaps)</h3>
              <p class="text-[11px] text-slate-500 font-mono">Grid {{ selectedTask?.grid_code }}</p>
            </div>
          </div>
          <button
            @click="showFillGapsModal = false"
            class="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="space-y-3 text-xs">
          <p class="text-slate-600 leading-relaxed">
            Sistem akan menghitung area pada grid yang belum tertutup poligon anotasi, kemudian membuat poligon baru penutup celah secara otomatis.
          </p>

          <div class="space-y-1">
            <label class="font-bold text-slate-700">Tugaskan Kelas untuk Celah:</label>
            <select
              v-model="fillGapsModalData.class_id"
              class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="cls in annotationsStore.classes" :key="cls.id" :value="cls.id">
                {{ cls.name }}
              </option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="font-bold text-slate-700">Abaikan Celah Lebih Kecil Dari:</label>
            <div class="flex items-center gap-2">
              <input
                type="number"
                step="0.5"
                min="0.1"
                v-model="fillGapsModalData.min_gap_area_sqm"
                class="w-24 p-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono font-bold text-slate-800"
              />
              <span class="text-slate-500 font-medium">m² (meter persegi)</span>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
          <button
            @click="showFillGapsModal = false"
            class="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            Batal
          </button>
          <button
            @click="executeFillGaps"
            :disabled="fillGapsModalData.isFilling"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <RotateCw v-if="fillGapsModalData.isFilling" :size="13" class="animate-spin" />
            <Layers v-else :size="13" />
            <span>{{ fillGapsModalData.isFilling ? 'Mengisi Celah...' : '🧩 Tutup Celah Sekarang' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL: Riwayat Versi & Snapshot Pemulihan QC -->
    <div
      v-if="showHistoryModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden flex flex-col max-h-[85vh]">
        <!-- Header -->
        <div class="px-6 py-4 bg-gradient-to-r from-indigo-50 to-slate-50 border-b border-indigo-100 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-500/20">
              <History :size="20" />
            </div>
            <div>
              <h3 class="font-extrabold text-sm text-slate-800">Riwayat Versi Poligon</h3>
              <p class="text-[11px] text-slate-500 font-mono">{{ selectedTask?.grid_code }} • Cadangan Snapshot</p>
            </div>
          </div>
          <button
            @click="showHistoryModal = false"
            class="text-slate-400 hover:text-slate-600 p-1.5 rounded-xl hover:bg-white transition-colors cursor-pointer"
          >
            <X :size="18" />
          </button>
        </div>

        <!-- Body -->
        <div class="p-6 overflow-y-auto space-y-3 divide-y divide-slate-100">
          <div v-if="loadingSnapshots" class="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
            <RotateCw :size="24" class="animate-spin text-indigo-500" />
            <span class="text-xs">Memuat riwayat versi...</span>
          </div>

          <div v-else-if="snapshotsList.length === 0" class="py-12 text-center text-slate-400 space-y-2">
            <History :size="32" class="mx-auto text-slate-300" />
            <p class="text-xs">Belum ada riwayat snapshot untuk grid ini.</p>
            <p class="text-[10px] text-slate-400">Snapshot dibuat otomatis setiap kali mapper menyimpan draf atau reviewer menjalankan auto-heal.</p>
          </div>

          <div
            v-else
            v-for="(snap, idx) in snapshotsList"
            :key="snap.id"
            class="pt-3 first:pt-0 flex items-center justify-between gap-3 group"
          >
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 rounded-md font-mono font-bold text-xs bg-indigo-100 text-indigo-800">
                  v{{ snap.version_number }}
                </span>
                <span v-if="idx === 0" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                  Terkini
                </span>
                <span class="text-xs font-bold text-slate-700">{{ snap.note || 'Draf Disimpan' }}</span>
              </div>
              <div class="flex items-center gap-3 text-[11px] text-slate-400">
                <span>{{ snap.features_count }} Poligon</span>
                <span>•</span>
                <span>{{ snap.author_name }}</span>
                <span>•</span>
                <span>{{ formatDateTime(snap.created_at) }}</span>
              </div>
            </div>

            <button
              @click="handleRestoreSnapshot(snap)"
              :disabled="restoringSnapshot"
              class="px-3 py-1.5 rounded-xl text-xs font-bold border border-slate-300 bg-white hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 text-slate-700 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer shrink-0 disabled:opacity-50"
              title="Pulihkan data poligon ke versi ini"
            >
              <RotateCcw :size="12" />
              <span>Pulihkan</span>
            </button>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
          <span>Total {{ snapshotsList.length }} versi tersimpan</span>
          <button
            @click="showHistoryModal = false"
            class="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold rounded-xl cursor-pointer"
          >
            Tutup
          </button>
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
  UserCheck,
  Calendar,
  ChevronDown,
  MapPin,
  MessageSquarePlus,
  Trash2,
  Check,
  CheckCheck,
  MessageCircle,
  Wand2,
  Scissors,
  Combine,
  Tag,
  Sliders,
  Settings2,
  History,
  PanelLeftClose,
  PanelLeft,
  ChevronLeft,
  ChevronRight
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

// Review Pins (Supervisi / QC notes per polygon & map point)
const isAddPinMode = ref(false)
const showPinModal = ref(false)
const pinModalData = ref({ lat: null, lon: null, note: '', annotation_id: null, class_name: '' })
const submittingPin = ref(false)
let qcReviewPinsLayer = null
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
const selectedPolygonId = ref(null)
let polygonLayersMap = new Map()
const qcTopologyResult = ref(null)
const checkingTopology = ref(false)

// QC Layout & Error Stepper State
const isSidebarCollapsed = ref(false)
const isMapFullHeight = ref(false)
const currentErrorIndex = ref(0)

// QC Topology Inspector State (Docked high-detail repair)
const showQcTopologyInspector = ref(false)
const activeQcInspectorError = ref(null)
const qcInspectorPolygons = ref([])
const activeQcInspectorBounds = ref(null)
const isQcInspectorLoading = ref(false)

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

// ── Project & Year Filter State ──────────────────────────────
const selectedProjectId = ref(null)
const selectedYear = ref(2025)

const activeProject = computed(() => {
  if (!selectedProjectId.value) return null
  return tasksStore.projects.find(p => p.id === selectedProjectId.value) || null
})

const activeProjectName = computed(() => {
  return activeProject.value ? activeProject.value.name : 'Semua Wilayah'
})

const latestAvailableYear = computed(() => {
  const yrs = availableQcYears.value.filter(y => y !== 'ALL')
  return yrs.length > 0 ? yrs[0] : null
})

const availableQcYears = computed(() => {
  const years = new Set()

  if (activeProject.value) {
    // 1. Ambil tahun dari konfigurasi project yang dibuat
    if (Array.isArray(activeProject.value.available_years)) {
      activeProject.value.available_years.forEach(y => { if (y) years.add(Number(y)) })
    }
    // 2. Ambil tahun dari tasks yang terdaftar pada project ini
    tasksStore.tasks.forEach(t => {
      if (t.study_area_id === activeProject.value.id && t.year) {
        years.add(Number(t.year))
      }
    })
    if (overviewData.value.by_grid) {
      overviewData.value.by_grid.forEach(g => {
        if (g.study_area_id === activeProject.value.id && g.year) {
          years.add(Number(g.year))
        }
      })
    }
  } else {
    // Jika Semua Wilayah dipilih, kumpulkan dari seluruh project yang ada
    if (tasksStore.projects && tasksStore.projects.length > 0) {
      tasksStore.projects.forEach(p => {
        if (Array.isArray(p.available_years)) {
          p.available_years.forEach(y => { if (y) years.add(Number(y)) })
        }
      })
    }
    tasksStore.tasks.forEach(t => { if (t.year) years.add(Number(t.year)) })
    if (overviewData.value.by_grid) {
      overviewData.value.by_grid.forEach(g => { if (g.year) years.add(Number(g.year)) })
    }
  }

  // Fallback jika belum ada data sama sekali
  if (years.size === 0) {
    years.add(2025)
  }

  const sorted = Array.from(years).sort((a, b) => b - a)
  return [...sorted, 'ALL']
})

const onProjectChange = async () => {
  tasksStore.selectedArea = selectedProjectId.value
  const yrs = availableQcYears.value.filter(y => y !== 'ALL')
  if (yrs.length > 0) {
    selectedYear.value = yrs[0]
  } else {
    selectedYear.value = 'ALL'
  }
  await refreshAllData()

  // Map auto-focus: jika proyek punya center_lat / center_lon
  await nextTick()
  if (activeProject.value && qcMap) {
    if (activeProject.value.center_lat && activeProject.value.center_lon) {
      qcMap.setView(
        [activeProject.value.center_lat, activeProject.value.center_lon],
        activeProject.value.default_zoom || 10
      )
    }
  }
}

const setQcYear = async (yr) => {
  selectedYear.value = yr
  await refreshAllData()

  // Pindahkan peta ke cakupan poligon atau grid tahun yang dipilih
  await nextTick()
  if (qcMap) {
    if (viewScope.value === 'single' && selectedTask.value) {
      fitMapBounds()
    } else if (viewScope.value === 'mosaic') {
      renderMosaicOnMap()
    } else {
      const targetGrids = allDigitizedGrids.value.length > 0
        ? allDigitizedGrids.value
        : tasksStore.tasks.filter(t => yr === 'ALL' || t.year === Number(yr))

      if (targetGrids.length > 0) {
        let minLat = Infinity, minLon = Infinity, maxLat = -Infinity, maxLon = -Infinity
        targetGrids.forEach(g => {
          if (g.min_lat != null && g.min_lon != null) {
            minLat = Math.min(minLat, g.min_lat)
            minLon = Math.min(minLon, g.min_lon)
            maxLat = Math.max(maxLat, g.max_lat)
            maxLon = Math.max(maxLon, g.max_lon)
          }
        })
        if (minLat !== Infinity && isFinite(minLat)) {
          qcMap.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [40, 40], maxZoom: 15 })
        }
      }
    }
  }
}

// All digitized grids (merged from overviewData.by_grid and tasksStore)
const allDigitizedGrids = computed(() => {
  const byGridMap = new Map()
  if (overviewData.value.by_grid) {
    overviewData.value.by_grid.forEach(g => {
      byGridMap.set(g.task_id || g.id, g)
    })
  }

  const pId = selectedProjectId.value ? Number(selectedProjectId.value) : null
  const targetYr = selectedYear.value !== 'ALL' ? Number(selectedYear.value) : null

  let list = []
  if (tasksStore.tasks && tasksStore.tasks.length > 0) {
    tasksStore.tasks.forEach(t => {
      const gOverview = byGridMap.get(t.id)
      list.push({
        task_id: t.id,
        id: t.id,
        grid_code: t.grid_code,
        year: t.year,
        study_area_id: t.study_area_id,
        study_area_name: t.study_area_name,
        status: t.status,
        assigned_user_id: t.assigned_user_id,
        assigned_user_name: t.assigned_user_name || (t.assignee?.full_name) || 'Belum Diambil',
        annotation_count: gOverview?.annotation_count != null ? gOverview.annotation_count : (t.annotation_count || 0),
        total_area_ha: gOverview?.total_area_ha || 0,
        min_lat: t.min_lat,
        min_lon: t.min_lon,
        max_lat: t.max_lat,
        max_lon: t.max_lon,
        bounds: t.min_lat != null ? [[t.min_lat, t.min_lon], [t.max_lat, t.max_lon]] : (gOverview?.bounds || null),
        classes: gOverview?.classes || []
      })
    })
  } else if (overviewData.value.by_grid) {
    list = [...overviewData.value.by_grid]
  }

  if (pId) {
    list = list.filter(g => {
      const aId = g.study_area_id != null ? Number(g.study_area_id) : null
      return aId != null ? aId === pId : true
    })
  }

  if (targetYr != null) {
    list = list.filter(g => Number(g.year) === targetYr)
  }

  // Prioritas grid yang memiliki digitasi / status SUBMITTED / REVISION di urutan teratas
  list.sort((a, b) => {
    const aAnns = a.annotation_count || 0
    const bAnns = b.annotation_count || 0
    if (bAnns !== aAnns) return bAnns - aAnns
    if (a.status === 'SUBMITTED' && b.status !== 'SUBMITTED') return -1
    if (b.status === 'SUBMITTED' && a.status !== 'SUBMITTED') return 1
    return (a.grid_code || '').localeCompare(b.grid_code || '')
  })

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

// Review Pins computed statistics
const resolvedPinsCount = computed(() => {
  const pins = tasksStore.currentTaskReviewPins || []
  return pins.filter(p => p.status === 'RESOLVED').length
})

const allPinsResolved = computed(() => {
  const pins = tasksStore.currentTaskReviewPins || []
  return pins.length > 0 && pins.every(p => p.status === 'RESOLVED')
})

const getPolygonPins = (annotationId) => {
  if (!annotationId) return []
  return (tasksStore.currentTaskReviewPins || []).filter(p => p.annotation_id === annotationId)
}

onMounted(async () => {
  await annotationsStore.fetchClasses()
  const projects = await tasksStore.fetchProjects()

  // Sinkronkan default ke proyek Sumatera Barat atau proyek pertama
  if (projects && projects.length > 0) {
    const defaultProj = projects.find(p => p.name?.toLowerCase().includes('sumatera barat')) || projects[0]
    selectedProjectId.value = defaultProj.id
    tasksStore.selectedArea = defaultProj.id

    const yrs = Array.isArray(defaultProj.available_years) ? defaultProj.available_years.filter(Boolean) : []
    if (yrs.length > 0) {
      selectedYear.value = yrs[0]
    }
  }

  if (authStore.isReviewer || authStore.isAdmin) {
    try {
      userList.value = await authStore.fetchAllUsers()
    } catch (_) {}
  }

  await nextTick()
  ensureMapInitialized()
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
  const yrParam = selectedYear.value === 'ALL' ? null : Number(selectedYear.value)
  try {
    tasksStore.selectedYear = yrParam
    tasksStore.selectedArea = selectedProjectId.value ? Number(selectedProjectId.value) : null
    tasksStore.selectedStatus = null
    tasksStore.filterMyTasks = false
    await Promise.all([
      tasksStore.fetchTasks(),
      loadOverviewData(yrParam),
      loadMosaicFeatures(yrParam)
    ])

    await nextTick()
    ensureMapInitialized()

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
      } else {
        await selectTaskByGridItem(stillInList)
      }
    } else {
      selectedTask.value = null
      taskFeatures.value = []
      if (qcFeatureGroup) qcFeatureGroup.clearLayers()
      if (qcGridBoundingLayer) {
        qcMap.removeLayer(qcGridBoundingLayer)
        qcGridBoundingLayer = null
      }
      if (activeProject.value && qcMap) {
        qcMap.setView(
          [activeProject.value.center_lat, activeProject.value.center_lon],
          activeProject.value.default_zoom || 9
        )
      }
    }
  } finally {
    loadingTasks.value = false
    loadingOverview.value = false
  }
}

const loadOverviewData = async (year = null) => {
  try {
    const params = {}
    if (year) params.year = year
    if (selectedProjectId.value) params.study_area_id = selectedProjectId.value
    const data = await annotationsStore.fetchAnnotationsOverview(params)
    if (data && data.summary) {
      overviewData.value = data
    }
  } catch (e) {
    console.error('Error loading overview data:', e)
  }
}

const loadMosaicFeatures = async (year = null) => {
  try {
    const params = {}
    if (year) params.year = year
    if (selectedProjectId.value) params.study_area_id = selectedProjectId.value
    const feats = await annotationsStore.fetchAllAnnotationsFeatures(params)
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
  selectedPolygonId.value = null

  if (viewScope.value === 'mosaic') {
    viewScope.value = 'single'
  }

  const features = await annotationsStore.fetchGridAnnotations(task.id)
  taskFeatures.value = features

  await tasksStore.fetchReviewPins(task.id)

  await nextTick()
  initOrUpdateQCMap(task, features)
  renderQCReviewPins()
}

const initOrUpdateQCMap = (task, features) => {
  ensureMapInitialized()

  const tileYr = task.year || (selectedYear.value !== 'ALL' ? Number(selectedYear.value) : 2025)
  updateQCTileLayer(tileYr)

  // Extract coordinates safely
  let minLat = task.min_lat
  let minLon = task.min_lon
  let maxLat = task.max_lat
  let maxLon = task.max_lon

  if ((minLat == null || isNaN(minLat)) && task.bounds && task.bounds.length === 2) {
    minLat = task.bounds[0][0]
    minLon = task.bounds[0][1]
    maxLat = task.bounds[1][0]
    maxLon = task.bounds[1][1]
  }

  // Draw Grid Bounding Box
  if (qcGridBoundingLayer && qcMap) {
    qcMap.removeLayer(qcGridBoundingLayer)
    qcGridBoundingLayer = null
  }

  let gridBounds = null
  if (minLat != null && minLon != null && maxLat != null && maxLon != null && !isNaN(minLat) && !isNaN(minLon)) {
    gridBounds = [[minLat, minLon], [maxLat, maxLon]]
    qcGridBoundingLayer = L.rectangle(gridBounds, {
      color: '#ffffff',
      weight: 2.5,
      dashArray: '5, 5',
      fillOpacity: 0.0,
      interactive: false
    }).addTo(qcMap)

    qcMap.fitBounds(gridBounds, { padding: [30, 30] })
  }

  // Render Polygons for active grid
  qcFeatureGroup.clearLayers()
  polygonLayersMap.clear()
  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  features.forEach(feat => {
    const cls = classesMap[feat.properties?.class_id]
    const color = cls?.color || '#9CA3AF'
    const areaHa = Math.round((feat.properties?.area_sqm || 10000) / 10000)
    const isSelected = selectedPolygonId.value === feat.id

    const layer = L.geoJSON(feat, {
      style: () => ({
        color: isSelected ? '#06b6d4' : '#ffffff',
        weight: isSelected ? 4.5 : 2,
        fillColor: color,
        fillOpacity: isSelected ? (qcOpacity.value > 0 ? Math.min(qcOpacity.value + 0.15, 0.5) : 0) : qcOpacity.value
      })
    })

    layer.eachLayer(l => {
      polygonLayersMap.set(feat.id, l)

      l.on('mouseover', () => {
        hoveredFeature.value = {
          class_name: cls?.name || feat.properties?.class_name || 'Belum Teridentifikasi',
          color: color,
          areaHa: areaHa,
          grid_code: task.grid_code,
          author_name: task.assigned_user_name
        }
        if (selectedPolygonId.value !== feat.id) {
          // Hollow: pertahankan opasitas pengguna (hanya garis batas kuning yang menyala)
          l.setStyle({ weight: 3.5, color: '#facc15', fillOpacity: qcOpacity.value })
          l.bringToFront()
        }
      })

      l.on('mouseout', () => {
        if (selectedPolygonId.value !== feat.id) {
          l.setStyle({ weight: 2, color: '#ffffff', fillOpacity: qcOpacity.value })
        }
      })

      l.on('click', (e) => {
        L.DomEvent.stopPropagation(e)
        if (isAddPinMode.value) {
          handleQCMapClickForPin(e, feat)
          return
        }
        selectPolygon(feat)
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

  if (gridBounds && qcMap) {
    qcMap.fitBounds(gridBounds, { padding: [30, 30] })
  }
}

// ─────────────────────────────────────────────
// BIDIRECTIONAL POLYGON SELECTION & HIGHLIGHTING
// ─────────────────────────────────────────────

const selectPolygon = (poly) => {
  if (!poly) return
  selectedPolygonId.value = poly.id

  // Highlight selected polygon on the map with glowing cyan border
  polygonLayersMap.forEach((lyr, id) => {
    const isTarget = id === poly.id
    const featObj = taskFeatures.value.find(f => f.id === id)
    const cls = annotationsStore.classes.find(c => c.id === featObj?.properties?.class_id)
    const color = cls?.color || '#9CA3AF'

    lyr.setStyle({
      weight: isTarget ? 4.5 : 2,
      color: isTarget ? '#06b6d4' : '#ffffff',
      fillColor: color,
      fillOpacity: isTarget ? (qcOpacity.value > 0 ? Math.min(qcOpacity.value + 0.15, 0.5) : 0) : qcOpacity.value
    })

    if (isTarget) {
      lyr.bringToFront()
      if (lyr.getBounds && qcMap) {
        qcMap.fitBounds(lyr.getBounds(), { padding: [60, 60], maxZoom: 16 })
      }
    }
  })

  // Scroll corresponding card into view in sidebar smoothly
  nextTick(() => {
    const el = document.getElementById('qc-poly-' + poly.id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}

const highlightPolygonOnMap = (polyId, isHover) => {
  if (selectedPolygonId.value === polyId) return
  const layer = polygonLayersMap.get(polyId)
  if (!layer) return

  if (isHover) {
    layer.setStyle({ weight: 3.5, color: '#facc15', fillOpacity: qcOpacity.value })
    layer.bringToFront()
  } else {
    const featObj = taskFeatures.value.find(f => f.id === polyId)
    const cls = annotationsStore.classes.find(c => c.id === featObj?.properties?.class_id)
    layer.setStyle({ weight: 2, color: '#ffffff', fillOpacity: qcOpacity.value, fillColor: cls?.color || '#9CA3AF' })
  }
}

// ─────────────────────────────────────────────
// TOPOLOGY ERROR INSPECTION & HIGHLIGHT
// ─────────────────────────────────────────────

const getTopologyErrorsForPolygon = (polyId) => {
  if (!qcTopologyResult.value?.errors || !polyId) return []
  return qcTopologyResult.value.errors.filter(err => {
    if (err.annotation_id && err.annotation_id === polyId) return true
    if (Array.isArray(err.annotation_ids) && err.annotation_ids.includes(polyId)) return true
    return false
  })
}

const hasTopologyError = (polyId) => {
  return getTopologyErrorsForPolygon(polyId).length > 0
}

const toggleSidebarCollapse = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  nextTick(() => {
    setTimeout(() => {
      qcMap?.invalidateSize()
    }, 250)
  })
}

const toggleMapFullHeight = () => {
  isMapFullHeight.value = !isMapFullHeight.value
  nextTick(() => {
    setTimeout(() => {
      qcMap?.invalidateSize()
    }, 250)
  })
}

const nextError = () => {
  if (!qcTopologyResult.value?.errors?.length) return
  currentErrorIndex.value = (currentErrorIndex.value + 1) % qcTopologyResult.value.errors.length
  focusTopologyError(qcTopologyResult.value.errors[currentErrorIndex.value])
}

const prevError = () => {
  if (!qcTopologyResult.value?.errors?.length) return
  currentErrorIndex.value = (currentErrorIndex.value - 1 + qcTopologyResult.value.errors.length) % qcTopologyResult.value.errors.length
  focusTopologyError(qcTopologyResult.value.errors[currentErrorIndex.value])
}

const convertErrorToReviewPin = (err) => {
  if (!err || !selectedTask.value) return
  const targetId = err.annotation_id || (Array.isArray(err.annotation_ids) ? err.annotation_ids[0] : null)
  let targetLat = selectedTask.value.min_lat || 0
  let targetLon = selectedTask.value.min_lon || 0

  if (targetId) {
    const lyr = polygonLayersMap.get(targetId)
    if (lyr && lyr.getBounds) {
      const center = lyr.getBounds().getCenter()
      targetLat = Number(center.lat.toFixed(6))
      targetLon = Number(center.lng.toFixed(6))
    } else {
      const feat = taskFeatures.value.find(f => f.id === targetId)
      if (feat?.geometry?.coordinates?.[0]) {
        let sumLat = 0, sumLon = 0, count = 0
        feat.geometry.coordinates[0].forEach(pt => {
          sumLon += pt[0]
          sumLat += pt[1]
          count++
        })
        if (count > 0) {
          targetLat = Number((sumLat / count).toFixed(6))
          targetLon = Number((sumLon / count).toFixed(6))
        }
      }
    }
  }

  const errorType = err.type || 'TOPOLOGI'
  const polyLabel = targetId ? `Poligon #${targetId}` : (err.annotation_ids ? `Poligon #${err.annotation_ids.join(' & #')}` : 'Batas')

  pinModalData.value = {
    lat: targetLat,
    lon: targetLon,
    note: `[Revisi ${errorType}] ${polyLabel}: ${err.message}`,
    category: 'Batas Kurang Pas',
    annotation_id: targetId,
    class_name: err.class_name || ''
  }
  showPinModal.value = true
  showToast(`📌 Menyiapkan pin revisi untuk ${polyLabel}`)
}

const focusTopologyError = (err) => {
  if (!err) return
  const targetId = err.annotation_id || (Array.isArray(err.annotation_ids) ? err.annotation_ids[0] : null)
  if (!targetId) {
    showToast(err.message)
    return
  }

  const feat = taskFeatures.value.find(f => f.id === targetId)
  if (feat) {
    selectPolygon(feat)
  }

  // Highlight all involved layers in flashing warning red and combine bounds
  const involvedIds = err.annotation_ids || (err.annotation_id ? [err.annotation_id] : [])
  let combinedBounds = null
  involvedIds.forEach(id => {
    const lyr = polygonLayersMap.get(id)
    if (lyr) {
      lyr.setStyle({
        weight: 5,
        color: '#ef4444',
        fillColor: '#f43f5e',
        fillOpacity: 0.85
      })
      lyr.bringToFront()
      if (lyr.getBounds) {
        const b = lyr.getBounds()
        combinedBounds = combinedBounds ? combinedBounds.extend(b) : b
      }
    }
  })

  if (combinedBounds && qcMap) {
    qcMap.fitBounds(combinedBounds, { padding: [100, 100], maxZoom: 19 })
  }

  // Update active error and polygons
  activeQcInspectorError.value = err
  activeQcInspectorBounds.value = combinedBounds
  qcInspectorPolygons.value = involvedIds.map(id => {
    const f = taskFeatures.value.find(feat => feat.id === id)
    return f || { id, properties: { id } }
  })
  showQcTopologyInspector.value = false

  // Keep currentErrorIndex in sync
  if (qcTopologyResult.value?.errors) {
    const foundIdx = qcTopologyResult.value.errors.indexOf(err)
    if (foundIdx !== -1) currentErrorIndex.value = foundIdx
  }

  // Smooth scroll corresponding card in list
  nextTick(() => {
    const el = document.getElementById('qc-err-' + currentErrorIndex.value)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}

// QC Topology Inspector Actions (Docked)
const executeQcInspectorZoomDetail = () => {
  if (activeQcInspectorBounds.value && qcMap) {
    qcMap.fitBounds(activeQcInspectorBounds.value, { padding: [100, 100], maxZoom: 19 })
  }
}

const executeQcInspectorDelete = async (polyId) => {
  if (!polyId) return
  if (!confirm(`Hapus poligon #${polyId}?`)) return
  isQcInspectorLoading.value = true
  try {
    await api.deleteAnnotation(polyId)
    showToast(`Poligon #${polyId} berhasil dihapus!`)
    showQcTopologyInspector.value = false
    activeQcInspectorError.value = null
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('QC delete error:', err)
    alert(err.response?.data?.detail || 'Gagal menghapus poligon.')
  } finally {
    isQcInspectorLoading.value = false
  }
}

const executeQcInspectorMerge = async () => {
  if (qcInspectorPolygons.value.length < 2 || !selectedTask.value) return
  isQcInspectorLoading.value = true
  const ids = qcInspectorPolygons.value.map(p => p.id || p.properties?.id).filter(Boolean)
  const targetClassId = qcInspectorPolygons.value[0]?.properties?.class_id || 1
  try {
    const res = await api.mergePolygons(selectedTask.value.id, ids, targetClassId)
    showToast(res.data?.message || 'Poligon berhasil digabungkan!')
    showQcTopologyInspector.value = false
    activeQcInspectorError.value = null
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('QC merge error:', err)
    alert(err.response?.data?.detail || 'Gagal menggabungkan poligon.')
  } finally {
    isQcInspectorLoading.value = false
  }
}

const executeQcInspectorClip = async () => {
  if (qcInspectorPolygons.value.length < 2 || !selectedTask.value) return
  isQcInspectorLoading.value = true
  const idA = qcInspectorPolygons.value[0].id || qcInspectorPolygons.value[0].properties?.id
  const idB = qcInspectorPolygons.value[1].id || qcInspectorPolygons.value[1].properties?.id
  try {
    await api.resolveOverlap(selectedTask.value.id, {
      action: 'clip_b_by_a',
      id_a: idA,
      id_b: idB
    })
    showToast('Overlap berhasil dipotong!')
    showQcTopologyInspector.value = false
    activeQcInspectorError.value = null
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('QC clip error:', err)
    alert(err.response?.data?.detail || 'Gagal memotong overlap.')
  } finally {
    isQcInspectorLoading.value = false
  }
}

const executeQcInspectorHeal = async () => {
  const err = activeQcInspectorError.value
  const targetId = err?.annotation_id || (err?.annotation_ids?.[0])
  if (!targetId) return
  isQcInspectorLoading.value = true
  try {
    await handleRepairSingleGeometry(targetId)
    showToast('Simpul melintir berhasil dirapikan!')
    showQcTopologyInspector.value = false
    activeQcInspectorError.value = null
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (healErr) {
    console.error('QC heal error:', healErr)
    alert('Gagal merapikan geometri.')
  } finally {
    isQcInspectorLoading.value = false
  }
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
        l.setStyle({ weight: 3.5, color: '#facc15', fillOpacity: qcOpacity.value })
        l.bringToFront()
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

    const centerLat = activeProject.value?.center_lat || -0.75
    const centerLon = activeProject.value?.center_lon || 100.5
    const zoom = activeProject.value?.default_zoom || 9

    qcMap = L.map('qc-map-container', {
      center: [centerLat, centerLon],
      zoom: zoom,
      maxZoom: 22,
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
    // Review Pins layer group
    qcReviewPinsLayer = L.layerGroup().addTo(qcMap)

    const tileYr = selectedYear.value !== 'ALL' ? Number(selectedYear.value) : 2025
    updateQCTileLayer(tileYr)
  }
}

// ─────────────────────────────────────────────
// REVIEW PINS METHODS (Supervisi / QC notes per polygon & map point)
// ─────────────────────────────────────────────

const renderQCReviewPins = () => {
  if (!qcReviewPinsLayer || !qcMap) return
  qcReviewPinsLayer.clearLayers()

  if (viewScope.value !== 'single' || !selectedTask.value) return

  const pins = tasksStore.currentTaskReviewPins || []
  pins.forEach(pin => {
    const isResolved = pin.status === 'RESOLVED'

    const markerHtml = isResolved
      ? `<div class="relative flex items-center justify-center w-7 h-7 rounded-full bg-emerald-600 text-white shadow-md border-2 border-white cursor-pointer hover:scale-110 transition-transform" title="Selesai diperbaiki">
           <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
         </div>`
      : `<div class="relative flex items-center justify-center w-8 h-8 rounded-full bg-rose-600 text-white shadow-lg border-2 border-white cursor-pointer animate-pulse hover:scale-110 transition-transform" title="Perlu Revisi">
           <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
           <span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full border border-white"></span>
         </div>`

    const customIcon = L.divIcon({
      html: markerHtml,
      className: 'qc-review-pin-marker',
      iconSize: [32, 32],
      iconAnchor: [16, 16],
      popupAnchor: [0, -18]
    })

    const marker = L.marker([pin.lat, pin.lon], { icon: customIcon })

    const statusBadge = isResolved
      ? `<span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300">✓ Sudah Selesai</span>`
      : `<span class="bg-rose-100 text-rose-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-rose-300 animate-pulse">● Perlu Revisi</span>`

    const resolverInfo = isResolved && pin.resolved_by_name
      ? `<div class="text-[11px] text-emerald-700 bg-emerald-50 p-1.5 rounded-lg border border-emerald-200 mt-1">
           <b>Diselesaikan oleh:</b> ${pin.resolved_by_name}
           ${pin.resolved_at ? `<div class="text-[10px] text-slate-500 font-mono">${new Date(pin.resolved_at).toLocaleString('id-ID')}</div>` : ''}
         </div>`
      : ''

    const popupContent = `
      <div class="p-2 space-y-1.5 min-w-[220px] max-w-[280px] font-sans text-slate-800">
        <div class="flex items-center justify-between gap-2 border-b border-slate-200 pb-1">
          <span class="text-xs font-bold text-slate-700 flex items-center gap-1">📍 Catatan Revisi</span>
          ${statusBadge}
        </div>
        <div class="text-xs text-slate-900 bg-slate-50 p-2 rounded-lg border border-slate-200 font-medium leading-relaxed">
          "${pin.note}"
        </div>
        <div class="text-[10px] text-slate-500 flex items-center justify-between">
          <span>Oleh: <b>${pin.reviewer_name || 'Reviewer'}</b></span>
          <span class="font-mono">${new Date(pin.created_at).toLocaleDateString('id-ID')}</span>
        </div>
        ${resolverInfo}
        <div class="pt-1 flex items-center justify-end gap-1 border-t border-slate-100 mt-2">
          <button onclick="window._qcDeletePin(${pin.id})" class="text-rose-600 hover:text-rose-800 text-[10px] font-bold px-2 py-1 rounded bg-rose-50 hover:bg-rose-100 border border-rose-200 cursor-pointer">
            Hapus Catatan
          </button>
        </div>
      </div>
    `

    marker.bindPopup(popupContent, { maxWidth: 300, className: 'custom-qc-pin-popup' })
    qcReviewPinsLayer.addLayer(marker)
  })
}

// Global hook for deleting pin from leaflet popup
if (typeof window !== 'undefined') {
  window._qcDeletePin = (pinId) => deleteReviewPin(pinId)
}

const toggleAddPinMode = (forceState) => {
  if (!qcMap) return
  isAddPinMode.value = forceState !== undefined ? forceState : !isAddPinMode.value
  const mapElem = document.getElementById('qc-map-container')
  if (isAddPinMode.value) {
    if (mapElem) mapElem.style.cursor = 'crosshair'
    qcMap.on('click', handleQCMapClickForPin)
    window.addEventListener('keydown', handleEscKeyForPin)
  } else {
    if (mapElem) mapElem.style.cursor = ''
    qcMap.off('click', handleQCMapClickForPin)
    window.removeEventListener('keydown', handleEscKeyForPin)
  }
}

const handleEscKeyForPin = (e) => {
  if (e.key === 'Escape' && isAddPinMode.value) {
    toggleAddPinMode(false)
  }
}

const handleQCMapClickForPin = (e, poly = null) => {
  if (!isAddPinMode.value) return
  pinModalData.value = {
    lat: Number(e.latlng.lat.toFixed(6)),
    lon: Number(e.latlng.lng.toFixed(6)),
    note: '',
    category: 'Batas Kurang Pas',
    annotation_id: poly ? (poly.id || poly.properties?.id || null) : null,
    class_name: poly?.properties?.class_name || ''
  }
  showPinModal.value = true
  toggleAddPinMode(false)
}

const openPinModalForPolygon = (poly) => {
  let lat = selectedTask.value?.min_lat
  let lon = selectedTask.value?.min_lon

  try {
    const coords = poly.geometry?.coordinates
    if (coords && coords[0]) {
      let sumLat = 0, sumLon = 0, count = 0
      const ring = coords[0]
      ring.forEach(pt => {
        sumLon += pt[0]
        sumLat += pt[1]
        count++
      })
      if (count > 0) {
        lat = Number((sumLat / count).toFixed(6))
        lon = Number((sumLon / count).toFixed(6))
      }
    }
  } catch (_) {}

  pinModalData.value = {
    lat: lat,
    lon: lon,
    note: '',
    category: 'Batas Kurang Pas',
    annotation_id: poly.id,
    class_name: poly.properties?.class_name || ''
  }
  showPinModal.value = true
}

const saveNewReviewPin = async () => {
  if (!pinModalData.value.note.trim() || !selectedTask.value) return
  submittingPin.value = true
  try {
    const rawNote = pinModalData.value.note.trim()
    const finalNote = pinModalData.value.category && !rawNote.startsWith('[')
      ? `[${pinModalData.value.category}] ${rawNote}`
      : rawNote

    await tasksStore.createReviewPin(selectedTask.value.id, {
      lat: pinModalData.value.lat,
      lon: pinModalData.value.lon,
      note: finalNote,
      annotation_id: pinModalData.value.annotation_id
    })
    showPinModal.value = false
    renderQCReviewPins()
  } catch (err) {
    console.error('Failed to create review pin:', err)
  } finally {
    submittingPin.value = false
  }
}

const deleteReviewPin = async (pinId) => {
  if (!confirm('Hapus tanda catatan revisi ini?')) return
  try {
    await tasksStore.deleteReviewPin(selectedTask.value.id, pinId)
    renderQCReviewPins()
  } catch (err) {
    console.error('Failed to delete review pin:', err)
  }
}

const focusOnPin = (pin) => {
  if (!qcMap) return
  qcMap.setView([pin.lat, pin.lon], Math.max(qcMap.getZoom(), 15), { animate: true })
}

const fitMapBounds = () => {
  if (!qcMap) return
  if (viewScope.value === 'single' && selectedTask.value) {
    let minLat = selectedTask.value.min_lat
    let minLon = selectedTask.value.min_lon
    let maxLat = selectedTask.value.max_lat
    let maxLon = selectedTask.value.max_lon

    if ((minLat == null || isNaN(minLat)) && selectedTask.value.bounds && selectedTask.value.bounds.length === 2) {
      minLat = selectedTask.value.bounds[0][0]
      minLon = selectedTask.value.bounds[0][1]
      maxLat = selectedTask.value.bounds[1][0]
      maxLon = selectedTask.value.bounds[1][1]
    }

    if (minLat != null && minLon != null && !isNaN(minLat) && !isNaN(minLon)) {
      const bounds = [[minLat, minLon], [maxLat, maxLon]]
      qcMap.fitBounds(bounds, { padding: [30, 30] })
    }
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
      maxZoom: 22,
      maxNativeZoom: 16,
      attribution: `Citra Sentinel-2 Sumbar (${year}) 10m COG`
    }).addTo(qcMap)
    qcTileLayer.bringToBack()
    return
  }

  const conf = getTileUrl(qcLayer.value, year)
  qcTileLayer = L.tileLayer(conf.url, {
    maxZoom: 22,
    maxNativeZoom: conf.maxNativeZoom || 18,
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
    currentErrorIndex.value = 0
    if (res.data?.errors?.length > 0) {
      activeQcInspectorError.value = res.data.errors[0]
    } else {
      activeQcInspectorError.value = null
    }
  } catch (err) {
    alert('Gagal menjalankan validasi topologi.')
  } finally {
    checkingTopology.value = false
  }
}

const isAutoHealing = ref(false)

// --- QC REPAIR TOOLBOX & INTERACTIVE ACTIONS ---
const showRepairToolboxModal = ref(false)
const repairOptions = ref({
  remove_duplicates: true,
  heal_geometries: true,
  clip_overlaps: true,
  overlap_priority: 'smaller_first',
  remove_slivers: true,
  min_sliver_area_sqm: 0.5,
  fill_gaps: false,
  fill_gap_class_id: 1
})
const isApplyingRepairOptions = ref(false)

const openRepairToolboxModal = () => {
  if (!selectedTask.value) {
    alert('Pilih salah satu grid terlebih dahulu sebelum membuka kotak alat perbaikan.')
    return
  }
  showRepairToolboxModal.value = true
}

const handleApplyRepairOptions = async () => {
  if (!selectedTask.value?.id) return
  isApplyingRepairOptions.value = true
  try {
    const res = await api.autoHealTopology(selectedTask.value.id, repairOptions.value)
    alert(res.data?.message || 'Pilihan perbaikan topologi berhasil diterapkan!')
    showRepairToolboxModal.value = false
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Apply repair options error:', err)
    alert(err.response?.data?.detail || 'Gagal menerapkan perbaikan topologi.')
  } finally {
    isApplyingRepairOptions.value = false
  }
}

// Modal: Riwayat Versi Poligon & Rollback
const showHistoryModal = ref(false)
const snapshotsList = ref([])
const loadingSnapshots = ref(false)
const restoringSnapshot = ref(false)

const openHistoryModal = async () => {
  if (!selectedTask.value?.id) {
    alert('Pilih salah satu grid terlebih dahulu sebelum membuka riwayat versi.')
    return
  }
  showHistoryModal.value = true
  loadingSnapshots.value = true
  try {
    const res = await api.getGridSnapshots(selectedTask.value.id)
    snapshotsList.value = res.data || []
  } catch (err) {
    console.error('Failed to load snapshots:', err)
    alert('Gagal memuat riwayat versi.')
  } finally {
    loadingSnapshots.value = false
  }
}

const handleRestoreSnapshot = async (snap) => {
  const confirmed = confirm(
    `⚠️ KONFIRMASI PEMULIHAN VERSI:\n\n` +
    `Apakah Anda yakin ingin mengembalikan poligon grid ke versi v${snap.version_number} (${snap.features_count} poligon)?\n\n` +
    `Catatan: Sistem secara otomatis mencadangkan kondisi saat ini sebelum pemulihan dilakukan, sehingga Anda dapat kembali lagi kapan saja.`
  )
  if (!confirmed) return

  restoringSnapshot.value = true
  try {
    await api.restoreGridSnapshot(selectedTask.value.id, snap.id)
    alert(`✅ Berhasil memulihkan poligon ke versi v${snap.version_number}!`)
    showHistoryModal.value = false
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Failed to restore snapshot:', err)
    alert(err.response?.data?.detail || 'Gagal memulihkan snapshot.')
  } finally {
    restoringSnapshot.value = false
  }
}

const formatDateTime = (dtStr) => {
  if (!dtStr) return '-'
  try {
    const d = new Date(dtStr)
    return d.toLocaleString('id-ID', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (_) {
    return dtStr
  }
}

// Modal: Resolve Specific Overlap Pair
const showOverlapModal = ref(false)
const overlapModalData = ref({
  ann_a: null,
  ann_b: null,
  target_class_id: 1,
  isResolving: false
})

const openResolveOverlapModal = (err) => {
  const idA = err.annotation_ids?.[0]
  const idB = err.annotation_ids?.[1]
  const featureA = taskFeatures.value.find(f => f.id === idA)
  const featureB = taskFeatures.value.find(f => f.id === idB)

  overlapModalData.value = {
    ann_a: {
      id: idA,
      class_id: featureA?.properties?.class_id || 0,
      class_name: featureA?.properties?.class_name || err.class_names?.[0] || 'Poligon A'
    },
    ann_b: {
      id: idB,
      class_id: featureB?.properties?.class_id || 0,
      class_name: featureB?.properties?.class_name || err.class_names?.[1] || 'Poligon B'
    },
    target_class_id: featureA?.properties?.class_id || featureB?.properties?.class_id || 1,
    isResolving: false
  }
  showOverlapModal.value = true
}

const executeResolveOverlap = async (action, targetClassId = null) => {
  if (!selectedTask.value?.id) return
  overlapModalData.value.isResolving = true
  try {
    const res = await api.resolveOverlap({
      task_grid_id: selectedTask.value.id,
      ann_id_a: overlapModalData.value.ann_a.id,
      ann_id_b: overlapModalData.value.ann_b.id,
      action: action,
      target_class_id: targetClassId
    })
    alert(res.data?.message || 'Overlap berhasil diselesaikan!')
    showOverlapModal.value = false
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Resolve overlap error:', err)
    alert(err.response?.data?.detail || 'Gagal menyelesaikan overlap.')
  } finally {
    overlapModalData.value.isResolving = false
  }
}

// Single Geometry Repair
const isRepairingSingleGeom = ref({})
const handleRepairSingleGeometry = async (annId) => {
  if (!annId) return
  isRepairingSingleGeom.value[annId] = true
  try {
    const res = await api.repairAnnotationGeometry(annId)
    alert(res.data?.message || `Geometri poligon #${annId} berhasil dirapikan!`)
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Repair single geom error:', err)
    alert(err.response?.data?.detail || 'Gagal merapikan geometri poligon.')
  } finally {
    isRepairingSingleGeom.value[annId] = false
  }
}

// Quick Assign / Change Class Modal
const showAssignClassModal = ref(false)
const assignClassModalData = ref({
  annotation_id: null,
  target_class_id: 1,
  isAssigning: false
})

const openAssignClassModal = (annId, currentClassId = 0) => {
  assignClassModalData.value = {
    annotation_id: annId,
    target_class_id: currentClassId || 1,
    isAssigning: false
  }
  showAssignClassModal.value = true
}

const executeAssignClass = async () => {
  if (!assignClassModalData.value.annotation_id) return
  assignClassModalData.value.isAssigning = true
  try {
    await api.updateAnnotationClass(
      assignClassModalData.value.annotation_id,
      assignClassModalData.value.target_class_id
    )
    alert(`Kelas poligon #${assignClassModalData.value.annotation_id} berhasil diubah!`)
    showAssignClassModal.value = false
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Update class error:', err)
    alert(err.response?.data?.detail || 'Gagal mengubah kelas poligon.')
  } finally {
    assignClassModalData.value.isAssigning = false
  }
}

// Quick Fill Gaps Modal
const showFillGapsModal = ref(false)
const fillGapsModalData = ref({
  class_id: 1,
  min_gap_area_sqm: 1.0,
  isFilling: false
})

const openFillGapsModal = () => {
  if (!selectedTask.value) return
  fillGapsModalData.value = {
    class_id: 1,
    min_gap_area_sqm: 1.0,
    isFilling: false
  }
  showFillGapsModal.value = true
}

const executeFillGaps = async () => {
  if (!selectedTask.value?.id) return
  fillGapsModalData.value.isFilling = true
  try {
    const res = await api.fillGridGaps(
      selectedTask.value.id,
      fillGapsModalData.value.class_id,
      fillGapsModalData.value.min_gap_area_sqm
    )
    alert(res.data?.message || 'Celah kosong berhasil diisi!')
    showFillGapsModal.value = false
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Fill gaps error:', err)
    alert(err.response?.data?.detail || 'Gagal mengisi celah kosong.')
  } finally {
    fillGapsModalData.value.isFilling = false
  }
}

const handleAutoHealTopology = async () => {
  if (!selectedTask.value?.id) return
  if (!confirm('Jalankan perbaikan topologi cepat? Sistem akan menggunakan konfigurasi standar (membersihkan duplikat, merapikan geometri, dan auto-clip overlap).')) return

  isAutoHealing.value = true
  try {
    const res = await api.autoHealTopology(selectedTask.value.id)
    alert(res.data?.message || 'Topologi berhasil diperbaiki otomatis!')
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Auto heal error:', err)
    alert(err.response?.data?.detail || 'Gagal memperbaiki topologi otomatis.')
  } finally {
    isAutoHealing.value = false
  }
}

const handleDeleteProblematicAnnotation = async (annId) => {
  if (!confirm(`Hapus poligon #${annId}? Tindakan ini akan menghapus poligon yang cacat dari grid ini.`)) return
  try {
    await api.deleteAnnotation(annId)
    alert(`Poligon #${annId} berhasil dihapus!`)
    await selectTask(selectedTask.value)
    await runQCTopologyCheck()
  } catch (err) {
    console.error('Delete annotation error:', err)
    alert(err.response?.data?.detail || 'Gagal menghapus poligon.')
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

<template>
  <div class="h-full min-h-full w-full flex bg-slate-100 text-slate-800 overflow-hidden font-sans">
    
    <!-- LEFT SIDEBAR: Task Selector, Sentinel-2 Layers, Settings -->
    <aside
      class="h-full max-h-full min-h-0 bg-white border-r border-slate-200 flex flex-col z-10 shadow-sm shrink-0 overflow-y-auto select-none"
      :style="{ width: `${leftSidebarWidth}px` }"
    >
      <!-- Task Selection Header -->
      <div class="p-3.5 border-b border-slate-200 space-y-2 bg-slate-50/70">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Pilih Grid Task</span>
          <router-link to="/tasking" class="text-[10px] text-rose-600 hover:text-rose-700 hover:underline flex items-center gap-1.5 font-bold">
            <Grid :size="12" />
            <span>Grid Map</span>
          </router-link>
        </div>

        <select
          v-model="selectedTaskId"
          @change="onTaskChange"
          class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 font-bold focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 font-mono shadow-xs cursor-pointer"
        >
          <option :value="null">-- {{ selectableTasks.length > 0 ? 'Pilih Grid' : 'Belum Ada Grid Diambil' }} --</option>
          <option v-for="t in selectableTasks" :key="t.id" :value="t.id">
            {{ t.grid_code }} - {{ t.study_area_name?.split(' ')[0] }} ({{ formatStatus(t.status) }})
          </option>
        </select>

        <!-- Current Task Badge & Assignee -->
        <div v-if="tasksStore.currentTask" class="pt-1 text-[11px] space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-slate-500">Status:</span>
            <span
              class="text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-2xs"
              :class="getStatusBadgeClass(tasksStore.currentTask.status)"
            >
              {{ formatStatus(tasksStore.currentTask.status) }}
            </span>
          </div>
          <div class="flex items-center justify-between text-slate-500">
            <span>Penanggung Jawab:</span>
            <b class="text-slate-800 truncate max-w-[140px] font-semibold">{{ tasksStore.currentTask.assigned_user_name || 'Tersedia' }}</b>
          </div>
        </div>
      </div>

      <!-- Year Selector -->
      <div class="px-3.5 pt-2 pb-1 bg-slate-50/50 border-b border-slate-200">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Tahun Komposit</span>
          <span class="text-[10px] font-mono font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">{{ currentYear }}</span>
        </div>
        <div class="flex items-center gap-1 bg-slate-200/70 p-1 rounded-xl">
          <button
            v-for="yr in availableRasterYears"
            :key="yr"
            @click="setYear(yr)"
            class="flex-1 py-1 text-[11px] font-bold rounded-lg transition-all cursor-pointer text-center"
            :class="currentYear === yr ? 'bg-white text-rose-600 shadow-xs border border-slate-200/80' : 'text-slate-600 hover:text-slate-900'"
          >
            {{ yr }}
          </button>
        </div>
      </div>

      <!-- Quick Action: Clone/Copy from another year -->
      <div class="px-3.5 py-2 border-b border-slate-200 bg-slate-50/30">
        <button
          @click="openCopyModal"
          class="w-full py-1.5 px-2.5 rounded-xl border border-indigo-200 bg-indigo-50/70 hover:bg-indigo-100/80 text-indigo-700 text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all shadow-2xs cursor-pointer"
          title="Salin poligon dari tahun 2017/2021 untuk diedit pada tahun ini"
        >
          <Copy :size="13" />
          <span>Salin Poligon dari Tahun Lain</span>
        </button>
      </div>

      <!-- General Task Revision Notes (if any) -->
      <div
        v-if="tasksStore.currentTask?.reviewer_notes && tasksStore.currentTask?.status === 'REVISION_NEEDED'"
        class="m-3 p-3 bg-rose-50 border border-rose-200 rounded-xl text-[11px] text-rose-800 space-y-1 shadow-2xs"
      >
        <div class="font-bold flex items-center gap-1.5 text-rose-700">
          <AlertTriangle :size="14" />
          <span>Catatan Revisi Umum:</span>
        </div>
        <div class="text-[11px] text-rose-900/90 leading-tight italic">"{{ tasksStore.currentTask.reviewer_notes }}"</div>
      </div>

      <!-- Interactive Review Pins / Catatan Supervisi di Peta -->
      <div
        v-if="tasksStore.currentTaskReviewPins.length > 0"
        class="m-3 p-3 bg-amber-50/90 border border-amber-200 rounded-2xl text-[11px] text-amber-900 space-y-2 shadow-2xs"
      >
        <div class="flex items-center justify-between font-bold text-amber-950">
          <span class="flex items-center gap-1.5">
            <MapPin :size="14" class="text-rose-600" />
            <span>Catatan Evaluasi / QC ({{ tasksStore.currentTaskReviewPins.length }})</span>
          </span>
          <div class="flex items-center gap-1.5">
            <button
              @click="toggleReviewPinsVisibility"
              class="px-2 py-0.5 rounded-lg text-[10px] font-semibold border flex items-center gap-1 transition-colors cursor-pointer"
              :class="showReviewPins ? 'bg-white text-slate-700 border-amber-300 hover:bg-amber-100' : 'bg-slate-200 text-slate-500 border-slate-300 hover:bg-slate-300'"
              :title="showReviewPins ? 'Sembunyikan Pin QC di Peta (Shortcut: Q)' : 'Tampilkan Pin QC di Peta (Shortcut: Q)'"
            >
              <Eye v-if="showReviewPins" :size="11" class="text-amber-800" />
              <EyeOff v-else :size="11" class="text-slate-500" />
              <span>{{ showReviewPins ? 'Pin Aktif (Q)' : 'Sembunyi (Q)' }}</span>
            </button>
            <span
              class="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold shadow-2xs"
              :class="allPinsResolved ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-rose-100 text-rose-800 border border-rose-300 animate-pulse'"
            >
              {{ resolvedPinsCount }}/{{ tasksStore.currentTaskReviewPins.length }}
            </span>
          </div>
        </div>

        <div class="space-y-1.5 max-h-56 overflow-y-auto pr-1">
          <div
            v-for="pin in tasksStore.currentTaskReviewPins"
            :key="pin.id"
            class="p-2.5 rounded-xl border text-xs flex flex-col gap-1.5 transition-all shadow-2xs"
            :class="pin.status === 'RESOLVED' ? 'bg-emerald-50/70 border-emerald-200' : 'bg-white border-rose-200'"
          >
            <div class="flex items-center justify-between gap-1">
              <span
                class="font-bold flex items-center gap-1 text-[11px]"
                :class="pin.status === 'RESOLVED' ? 'text-emerald-800' : 'text-rose-800'"
              >
                <CheckCircle2 v-if="pin.status === 'RESOLVED'" :size="12" class="text-emerald-600" />
                <AlertTriangle v-else :size="12" class="text-rose-600" />
                <span>{{ pin.status === 'RESOLVED' ? 'Selesai' : 'Perlu Diperbaiki' }}</span>
              </span>
              <button
                @click="focusOnReviewPin(pin)"
                class="px-2 py-0.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 rounded text-[10px] font-bold text-slate-600 flex items-center gap-1 transition-colors cursor-pointer"
                title="Arahkan peta ke titik ini"
              >
                <Focus :size="11" />
                <span>Peta</span>
              </button>
            </div>

            <p class="text-[11px] text-slate-800 italic leading-snug">"{{ pin.note }}"</p>

            <div class="flex items-center justify-between pt-1 border-t border-slate-100 gap-1">
              <span class="text-[10px] text-slate-500 font-mono truncate">
                {{ pin.reviewer_name || 'Petugas' }}
              </span>
              <div class="flex items-center gap-1 shrink-0">
                <button
                  @click="deleteEvaluationPin(pin.id)"
                  class="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors cursor-pointer"
                  title="Hapus pin catatan ini"
                >
                  <Trash2 :size="12" />
                </button>
                <button
                  @click="togglePinResolved(pin)"
                  class="px-2 py-1 rounded-lg text-[10px] font-bold transition-all cursor-pointer flex items-center gap-1"
                  :class="pin.status === 'RESOLVED'
                    ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                    : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs'"
                >
                  <Check v-if="pin.status !== 'RESOLVED'" :size="11" />
                  <RotateCcw v-else :size="11" />
                  <span>{{ pin.status === 'RESOLVED' ? 'Batal' : 'Selesai' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Workflow Guide -->
      <div class="px-3.5 py-2 border-b border-slate-200 bg-slate-50/30">
        <button
          @click="showGuide = !showGuide"
          class="w-full text-left text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between"
        >
          <span class="flex items-center gap-1.5"><BookOpen :size="12" class="text-slate-400" /> Panduan Digitasi Split/Cut</span>
          <ChevronDown :size="12" :class="showGuide ? 'rotate-180' : ''" class="transition-transform text-slate-400" />
        </button>
        <div v-if="showGuide" class="mt-2 space-y-1.5 text-[10px] text-slate-600 leading-relaxed">
          <div class="flex items-start gap-1.5">
            <span class="text-rose-600 font-black text-[11px]">1.</span>
            <span><b>Potong Garis (Split Blade)</b>: Tarik garis melintasi poligon dari batas ke batas untuk membaginya menjadi 2 poligon terpisah.</span>
          </div>
          <div class="flex items-start gap-1.5">
            <span class="text-rose-600 font-black text-[11px]">2.</span>
            <span><b>Potong Area (Cookie Cutter)</b>: Gambar poligon area di dalam grid untuk memisahkan bagian dalam & luar tanpa ada area yang hilang/terhapus.</span>
          </div>
          <div class="flex items-start gap-1.5">
            <span class="text-rose-600 font-black text-[11px]">3.</span>
            <span><b>Klik Poligon</b> di peta untuk langsung memilih & mengganti jenis tutupan lahannya.</span>
          </div>
          <div class="flex items-start gap-1.5">
            <span class="text-rose-600 font-black text-[11px]">4.</span>
            <span><b>Gabung (Merge)</b>: Pilih 2 poligon bersebelahan untuk disatukan menjadi 1 poligon utuh.</span>
          </div>
        </div>
      </div>

      <!-- Sentinel-2 Layer Control Section -->
      <div class="p-3.5 space-y-3 shrink-0">
        <div class="flex items-center justify-between pb-1.5 border-b border-slate-200">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Satellite :size="13" class="text-slate-400" />
            <span>Pilihan Layer Komposit</span>
          </span>
          <span class="text-[9px] font-bold text-slate-400">Sentinel-2 & Basemap</span>
        </div>

        <!-- Layer Buttons -->
        <div class="space-y-1.5">
          <button
            v-for="layer in layerOptions"
            :key="layer.id"
            @click="setLayer(layer.id)"
            class="w-full text-left p-2 rounded-xl transition-all border flex items-center justify-between group cursor-pointer"
            :class="currentLayer === layer.id
              ? 'bg-rose-50/80 border-rose-400 text-rose-900 shadow-xs ring-1 ring-rose-400/40'
              : 'bg-slate-50/60 border-slate-200 text-slate-700 hover:bg-white hover:border-slate-300 hover:shadow-2xs'"
          >
            <div class="flex items-center gap-2.5">
              <component :is="layer.icon" :size="16" :class="layer.colorClass" class="shrink-0" />
              <div>
                <div class="text-xs font-bold leading-tight">{{ layer.name }}</div>
                <div class="text-[9px] text-slate-500 leading-tight">{{ layer.desc }}</div>
              </div>
            </div>
            <div
              class="w-2.5 h-2.5 rounded-full border shrink-0"
              :class="currentLayer === layer.id ? 'bg-rose-500 border-rose-600' : 'border-slate-300 bg-white'"
            ></div>
          </button>
        </div>
      </div>
    </aside>

    <!-- LEFT RESIZER DRAG HANDLE -->
    <div
      @mousedown="startResizeLeft"
      class="w-1.5 hover:w-2 bg-transparent hover:bg-rose-500/40 active:bg-rose-600 transition-all cursor-col-resize z-20 shrink-0 relative -mr-1 flex items-center justify-center group select-none"
      title="Tarik untuk mengatur lebar sidebar kiri"
    >
      <div class="w-0.5 h-8 bg-slate-300 group-hover:bg-rose-500 rounded-full transition-colors"></div>
    </div>

    <!-- CENTER: GIS Map Workspace -->
    <main class="flex-1 flex flex-col relative h-full overflow-hidden">
      <!-- Top Floating Map Header Action Bar -->
      <div class="bg-white/95 border-b border-slate-200 px-4 py-2 flex items-center justify-between gap-3 z-10 backdrop-blur-md shrink-0 shadow-xs">
        <div class="flex items-center gap-3">
          <span class="font-mono text-xs font-extrabold text-slate-900 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 flex items-center gap-1.5">
            <Crosshair :size="13" class="text-rose-600" />
            <span>{{ tasksStore.currentTask?.grid_code || 'Pilih Grid' }}</span>
          </span>
          <span class="text-xs text-slate-600 font-medium hidden sm:inline">
            <b>{{ features.length }}</b> Poligon Tergambar
          </span>

          <!-- Area Coverage Meter (%) -->
          <div class="flex items-center gap-2 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200 shadow-2xs">
            <PieChart :size="13" class="text-slate-400" />
            <span class="text-[11px] font-bold text-slate-600 hidden md:inline">Cakupan Grid:</span>
            <span class="font-mono text-xs font-black" :class="coveragePercent >= 70 ? 'text-emerald-600' : 'text-amber-600'">
              {{ coveragePercent }}%
            </span>
            <div class="w-16 sm:w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-300"
                :style="{ width: `${coveragePercent}%` }"
                :class="coveragePercent >= 70 ? 'bg-emerald-500' : 'bg-amber-500'"
              ></div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center gap-2">
          <!-- Undo & Redo Group -->
          <div class="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200">
            <button
              @click="undo"
              :disabled="!canUndo"
              class="px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
              :class="canUndo ? 'text-slate-700 hover:bg-white hover:shadow-xs' : 'text-slate-400'"
              title="Undo (Ctrl+Z / Cmd+Z)"
            >
              <Undo2 :size="13" />
              <span class="hidden md:inline">Undo</span>
            </button>
            <button
              @click="redo"
              :disabled="!canRedo"
              class="px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
              :class="canRedo ? 'text-slate-700 hover:bg-white hover:shadow-xs' : 'text-slate-400'"
              title="Redo (Ctrl+Y / Cmd+Y)"
            >
              <Redo2 :size="13" />
              <span class="hidden md:inline">Redo</span>
            </button>
          </div>

          <!-- Offline & Auto-save Status Pill -->
          <div
            class="px-2.5 py-1.5 rounded-xl text-xs font-medium flex items-center gap-1.5 border shadow-2xs"
            :class="isNetworkOnline ? 'bg-slate-50 text-slate-700 border-slate-200' : 'bg-amber-50 text-amber-800 border-amber-300'"
            :title="isNetworkOnline ? (localDraftStatus ? `Draf lokal tersimpan (${localDraftStatus.polygonCount} poligon)` : 'Koneksi Online — Auto-save IndexedDB Aktif') : 'Mode Offline — Perubahan disimpan di browser lokal'"
          >
            <Wifi v-if="isNetworkOnline" :size="13" class="text-emerald-600" />
            <WifiOff v-else :size="13" class="text-amber-600 animate-pulse" />
            <span class="text-[11px] font-bold hidden xl:inline">{{ isNetworkOnline ? 'Online' : 'Offline' }}</span>
            <span v-if="localDraftStatus" class="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200 hidden lg:inline">💾 Draf Aman</span>
          </div>


          <!-- Tombol Buka Panel Citra & Spektral -->
          <button
            @click="showImageryPanel = !showImageryPanel"
            class="px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 border shadow-xs cursor-pointer"
            :class="showImageryPanel ? 'bg-rose-50 text-rose-700 border-rose-300 ring-2 ring-rose-400/20' : 'bg-white text-slate-700 hover:bg-slate-50 border-slate-300'"
            title="Buka Pengaturan Komposit Citra, Kontras, Gamma & Spektral"
          >
            <SlidersHorizontal :size="13" :class="showImageryPanel ? 'text-rose-600' : 'text-slate-500'" />
            <span class="hidden md:inline">Atur Citra & Kontras</span>
            <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 font-bold hidden lg:inline">{{ currentLayerBadge }}</span>
          </button>

          <!-- Topology Check Button -->
          <button
            @click="runTopologyCheck"
            :disabled="topologyLoading"
            class="bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-bold px-3 py-1.5 rounded-xl border border-purple-200 transition-all flex items-center gap-1.5 shadow-xs cursor-pointer"
          >
            <RotateCw v-if="topologyLoading" :size="13" class="animate-spin text-purple-500" />
            <ShieldCheck v-else :size="13" class="text-purple-500" />
            <span class="hidden sm:inline">Cek Topologi</span>
          </button>

          <!-- Reset Grid Polygons Button -->
          <button
            v-if="selectedTaskId && (authStore.isAdmin || tasksStore.currentTask?.assigned_user_id === authStore.user?.id)"
            @click="resetCurrentGridAnnotations"
            class="bg-amber-50 hover:bg-amber-100 text-amber-900 text-xs font-bold px-3 py-1.5 rounded-xl border border-amber-300 transition-all flex items-center gap-1.5 shadow-xs cursor-pointer"
            title="Hapus seluruh poligon pada grid ini dan mulai digitasi dari awal"
          >
            <Trash2 :size="13" class="text-amber-600" />
            <span class="hidden sm:inline">Reset Grid</span>
          </button>

          <!-- Riwayat Versi / Snapshots Button -->
          <button
            v-if="selectedTaskId"
            @click="openHistoryModal"
            class="bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium px-3 py-1.5 rounded-md border border-slate-300 transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
            title="Lihat riwayat versi cadangan dan pulihkan poligon sebelumnya (Rollback)"
          >
            <History :size="13" class="text-slate-500" />
            <span class="hidden sm:inline">Riwayat Versi</span>
          </button>

          <button
            @click="saveAnnotations"
            :disabled="annotationsStore.saving"
            class="bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium px-3.5 py-1.5 rounded-md border border-slate-300 transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
            title="Simpan perubahan poligon (Ctrl+S)"
          >
            <RotateCw v-if="annotationsStore.saving" :size="13" class="animate-spin text-slate-500" />
            <Save v-else :size="13" class="text-slate-500" />
            <span class="hidden sm:inline">Simpan Draf</span>
          </button>

          <button
            v-if="tasksStore.currentTask && tasksStore.currentTask.status !== 'APPROVED'"
            @click="submitForReview"
            class="bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold px-4 py-1.5 rounded-md shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <Send :size="13" />
            <span>Kirim Review QC</span>
          </button>
        </div>
      </div>

      <!-- Prominent Revision Warning Banner if status is REVISION_NEEDED -->
      <div
        v-if="tasksStore.currentTask?.status === 'REVISION_NEEDED'"
        class="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center justify-between text-xs text-amber-900 z-10 shrink-0 shadow-xs"
      >
        <div class="flex items-center gap-2">
          <AlertTriangle :size="16" class="text-amber-600" />
          <span><b>Catatan Review QC:</b> <i class="text-amber-800">"{{ tasksStore.currentTask.reviewer_notes || 'Mohon periksa dan perbaiki kerapian batas poligon tutupan lahan pada grid ini.' }}"</i></span>
        </div>
        <span class="text-[10px] bg-amber-200 text-amber-900 font-extrabold px-2 py-0.5 rounded uppercase tracking-wider shrink-0">
          Perlu Revisi
        </span>
      </div>

      <!-- Slim Topology Indicator Bar (Preserves 100% Main Map Height - Shadcn Alert Style) -->
      <div
        v-if="topologyResult && !topologyResult.valid"
        role="alert"
        class="bg-rose-50/95 text-rose-950 px-4 py-2 text-xs z-10 shrink-0 shadow-xs flex items-center justify-between gap-3 border-b border-rose-200/90 backdrop-blur-md animate-in fade-in duration-150"
      >
        <div class="flex items-center gap-2.5 font-medium min-w-0">
          <div class="w-6 h-6 rounded-md bg-rose-100/90 border border-rose-200 flex items-center justify-center text-rose-600 shrink-0">
            <AlertTriangle :size="13" />
          </div>
          <div class="truncate">
            <span class="font-bold text-rose-950">
              Ditemukan <span class="underline decoration-rose-400 font-mono text-rose-700 font-extrabold">{{ topologyResult.errors.length }} Masalah Topologi</span>
            </span>
            <span class="text-rose-700/80 text-[11px] font-normal hidden md:inline ml-1.5">(Tumpang tindih, celah batas, atau simpul melilit)</span>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            @click="openTopologySurgeryModal"
            class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white rounded-md text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
            title="Buka Studio Popup untuk perbaikan topologi dengan kanvas zoom tak terbatas dan tools lengkap"
          >
            <Maximize2 :size="13" />
            <span>Buka Studio Perbaikan Topologi</span>
          </button>
          <button
            @click="handleCleanSlivers"
            :disabled="isCleaningSlivers"
            class="px-2.5 py-1.5 bg-white hover:bg-rose-100/70 text-rose-800 border border-rose-200 rounded-md text-xs font-medium hidden lg:flex items-center gap-1 shadow-2xs cursor-pointer transition-colors"
            title="Rapatkan sliver celah batas"
          >
            <Sparkles :size="12" :class="{ 'animate-spin': isCleaningSlivers }" />
            <span>Rapatkan Sliver</span>
          </button>
          <button
            @click="handleAutoHeal"
            :disabled="isHealingTopology"
            class="px-2.5 py-1.5 bg-white hover:bg-rose-100/70 text-rose-800 border border-rose-200 rounded-md text-xs font-medium hidden sm:flex items-center gap-1 shadow-2xs cursor-pointer transition-colors"
            title="Koreksi otomatis cepat"
          >
            <Wand2 :size="12" :class="{ 'animate-spin': isHealingTopology }" />
            <span>Auto-Koreksi</span>
          </button>
          <button
            @click="topologyResult = null"
            class="text-rose-400 hover:text-rose-700 hover:bg-rose-100/80 p-1 rounded-md cursor-pointer transition-colors"
            title="Tutup banner ini"
          >
            <X :size="15" />
          </button>
        </div>
      </div>

      <!-- Topology Success Banner -->
      <div
        v-if="topologyResult && topologyResult.valid"
        class="bg-emerald-50 border-b border-emerald-200 px-4 py-2 flex items-center justify-between text-xs text-emerald-900 z-10 shrink-0 shadow-xs"
      >
        <div class="flex items-center gap-2">
          <CheckCircle2 :size="14" class="text-emerald-600" />
          <span><b>Topologi Valid!</b> Coverage {{ topologyResult.coverage_percent }}% — {{ topologyResult.polygon_count }} poligon tervalidasi.</span>
        </div>
        <button @click="topologyResult = null" class="text-emerald-400 hover:text-emerald-600 cursor-pointer">
          <X :size="14" />
        </button>
      </div>

      <!-- Smart Multi-Year Copy Banner (Shown when current grid has 0 annotations, but another year has annotations) -->
      <div
        v-if="bestCopyCandidate && showSmartCopyBanner"
        class="bg-indigo-50 border-b border-indigo-200 px-4 py-2.5 flex items-center justify-between text-xs text-indigo-950 z-10 shrink-0 shadow-xs animate-in fade-in duration-200"
      >
        <div class="flex items-center gap-2.5">
          <div class="p-1.5 bg-indigo-100 text-indigo-700 rounded-xl shrink-0">
            <Copy :size="15" />
          </div>
          <div>
            <span class="font-bold text-indigo-950">Grid {{ currentYear }} Masih Kosong.</span>
            <span class="text-indigo-800 text-[11px] ml-1">
              Tersedia hasil digitasi dari tahun <b>{{ bestCopyCandidate.year }}</b> ({{ bestCopyCandidate.annotation_count }} poligon). Ingin salin sebagai acuan edit?
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            @click="quickCopyFromSibling(bestCopyCandidate)"
            :disabled="copyingAnnotations"
            class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm cursor-pointer disabled:opacity-50"
          >
            <RotateCw v-if="copyingAnnotations" :size="12" class="animate-spin" />
            <Copy v-else :size="12" />
            <span>Salin dari Tahun {{ bestCopyCandidate.year }}</span>
          </button>
          <button
            @click="showSmartCopyBanner = false"
            class="px-2.5 py-1 text-slate-500 hover:text-slate-800 text-xs font-medium cursor-pointer rounded-lg hover:bg-indigo-100/50 transition-colors"
            title="Biarkan grid kosong untuk menggambar dari nol"
          >
            Mulai dari Grid Kosong
          </button>
        </div>
      </div>

      <!-- Map & Floating Toolbox -->
      <div class="flex-1 relative w-full h-full">
        <!-- Floating Custom GIS Toolbar on Map Top-Left -->
        <div
          class="absolute top-4 left-4 z-20 bg-white/95 backdrop-blur-md rounded-lg shadow-md border border-slate-300 p-1 flex flex-col gap-1 transition-all duration-200 select-none"
          :class="isToolboxCollapsed ? 'w-auto' : 'w-48'"
        >
          <!-- Header Bar with Title & Collapse/Expand Button -->
          <div class="flex items-center justify-between px-2 py-1 border-b border-slate-200 mb-0.5 bg-slate-50/80 rounded-t-sm">
            <button
              @click="isToolboxCollapsed = !isToolboxCollapsed"
              class="flex items-center gap-1.5 text-slate-700 hover:text-slate-900 transition-colors cursor-pointer w-full justify-between"
              :title="isToolboxCollapsed ? 'Buka panel alat digitasi' : 'Ciutkan panel alat digitasi'"
            >
              <div class="flex items-center gap-1.5">
                <PenTool :size="13" class="text-slate-700 shrink-0" />
                <span v-if="!isToolboxCollapsed" class="text-[10px] font-bold uppercase tracking-wider text-slate-700">Alat Digitasi</span>
                <span v-else class="text-[10px] font-bold text-slate-700">Alat</span>
              </div>
              <ChevronDown v-if="isToolboxCollapsed" :size="13" class="text-slate-500 shrink-0" />
              <ChevronUp v-else :size="13" class="text-slate-500 shrink-0" />
            </button>
          </div>

          <!-- Collapsed Summary: Mini Icon Button -->
          <div v-if="isToolboxCollapsed" class="flex flex-col gap-1 items-center py-0.5">
            <button
              @click="isToolboxCollapsed = false"
              class="p-2 rounded-md bg-slate-50 hover:bg-slate-100 text-slate-700 text-[10px] font-medium flex items-center justify-center cursor-pointer transition-all border border-slate-200"
              title="Klik untuk membuka alat digitasi"
            >
              <Scissors v-if="activeTool === 'split_line'" :size="15" class="text-slate-800" />
              <Layers v-else-if="activeTool === 'split_poly'" :size="15" class="text-slate-800" />
              <LassoSelect v-else-if="activeTool === 'freehand_cut'" :size="15" class="text-slate-800" />
              <Combine v-else-if="activeTool === 'merge'" :size="15" class="text-slate-800" />
              <Edit3 v-else-if="activeTool === 'edit'" :size="15" class="text-slate-800" />
              <Trash2 v-else-if="activeTool === 'delete'" :size="15" class="text-red-700" />
              <MousePointer v-else :size="15" class="text-slate-700" />
            </button>
          </div>

          <!-- Expanded Content: Full Tools & Transparency Controls -->
          <template v-else>
            <!-- Tool: Select / Pointer -->
            <button
              @click="setDigitizeMode(null)"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="activeTool === null ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-700 hover:bg-slate-100'"
              title="Pilih Objek (Shortcut: V)"
            >
              <div class="flex items-center gap-2">
                <MousePointer :size="14" />
                <span class="text-[11px]">Pilih Poligon</span>
              </div>
              <span class="text-[9px] font-mono opacity-60 font-semibold">V</span>
            </button>

            <!-- Tool: Split with Line (Blade) -->
            <button
              @click="setDigitizeMode('split_line')"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="activeTool === 'split_line' ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-700 hover:bg-slate-100'"
              title="Potong dengan Garis (Shortcut: C)"
            >
              <div class="flex items-center gap-2">
                <Scissors :size="14" />
                <span class="text-[11px]">Potong Garis</span>
              </div>
              <span class="text-[9px] font-mono opacity-60 font-semibold">C</span>
            </button>

            <!-- Tool: Split with Polygon (Cookie Cutter) -->
            <button
              @click="setDigitizeMode('split_poly')"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="activeTool === 'split_poly' ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-700 hover:bg-slate-100'"
              title="Potong Poligon (Shortcut: X)"
            >
              <div class="flex items-center gap-2">
                <Layers :size="14" />
                <span class="text-[11px]">Potong Area</span>
              </div>
              <span class="text-[9px] font-mono opacity-60 font-semibold">X</span>
            </button>

            <!-- Tool: Freehand Cut (Lasso) -->
            <button
              @click="setDigitizeMode('freehand_cut')"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="activeTool === 'freehand_cut' ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-700 hover:bg-slate-100'"
              title="Pemotong Bebas Lasso (Shortcut: L)"
            >
              <div class="flex items-center gap-2">
                <LassoSelect :size="14" />
                <span class="text-[11px]">Potong Bebas</span>
              </div>
              <span class="text-[9px] font-mono opacity-60 font-semibold">L</span>
            </button>

            <!-- Tool: Merge Polygons -->
            <button
              @click="setDigitizeMode('merge')"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="activeTool === 'merge' ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-700 hover:bg-slate-100'"
              title="Gabung Poligon Bersebelahan (Shortcut: M)"
            >
              <div class="flex items-center gap-2">
                <Combine :size="14" />
                <span class="text-[11px]">Gabung Poligon</span>
              </div>
              <span class="text-[9px] font-mono opacity-60 font-semibold">M</span>
            </button>

            <!-- Tool: Edit Vertices -->
            <button
              @click="setDigitizeMode('edit')"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="activeTool === 'edit' ? 'bg-slate-800 text-white shadow-xs' : 'text-slate-700 hover:bg-slate-100'"
              title="Edit Titik Simpul (Shortcut: E)"
            >
              <div class="flex items-center gap-2">
                <Edit3 :size="14" />
                <span class="text-[11px]">Edit Titik</span>
              </div>
              <span class="text-[9px] font-mono opacity-60 font-semibold">E</span>
            </button>

            <!-- Tool: Delete Polygon -->
            <button
              @click="setDigitizeMode('delete')"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="activeTool === 'delete' ? 'bg-red-50 text-red-700 border border-red-300 shadow-2xs' : 'text-slate-700 hover:bg-slate-100'"
              title="Hapus Poligon Terpilih"
            >
              <div class="flex items-center gap-2">
                <Trash2 :size="14" />
                <span class="text-[11px]">Hapus</span>
              </div>
            </button>

            <!-- Tool: Snapping Toggle -->
            <button
              @click="toggleSnapping"
              class="px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition-all cursor-pointer text-left"
              :class="isSnappingEnabled ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'text-slate-500 hover:bg-slate-100'"
              :title="isSnappingEnabled ? 'Snapping Sudut Aktif (Tekan S untuk matikan)' : 'Snapping Mati / Mode Cepat (Tekan S untuk aktifkan)'"
            >
              <div class="flex items-center gap-2">
                <Magnet :size="14" :class="isSnappingEnabled ? 'text-indigo-600' : 'text-slate-400'" />
                <span class="text-[11px]">Snap Sudut: {{ isSnappingEnabled ? 'ON' : 'OFF' }}</span>
              </div>
              <span class="text-[9px] font-mono opacity-60 font-semibold">S</span>
            </button>

            <!-- Quick Undo & Redo in Toolbox -->
            <div class="grid grid-cols-2 gap-1 pt-1 border-t border-slate-200 mt-0.5">
              <button
                @click="undo"
                :disabled="!canUndo"
                class="py-1 px-1.5 rounded-md text-[10px] font-medium flex items-center justify-center gap-1 transition-all cursor-pointer border border-slate-200 bg-slate-50 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed"
                title="Batalkan perubahan (Ctrl+Z)"
              >
                <Undo2 :size="12" />
                <span>Undo</span>
              </button>
              <button
                @click="redo"
                :disabled="!canRedo"
                class="py-1 px-1.5 rounded-md text-[10px] font-medium flex items-center justify-center gap-1 transition-all cursor-pointer border border-slate-200 bg-slate-50 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed"
                title="Terapkan kembali (Ctrl+Y)"
              >
                <Redo2 :size="12" />
                <span>Redo</span>
              </button>
            </div>

            <div class="border-t border-slate-200 my-0.5"></div>

            <!-- Active Selected Class Indicator in Toolbar -->
            <div class="p-1.5 bg-slate-50 rounded-md border border-slate-200 text-[10px] space-y-1">
              <div class="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Kelas Aktif:</div>
              <div class="flex items-center gap-1.5">
                <div class="w-3 h-3 rounded-xs shrink-0 border border-slate-300" :style="{ backgroundColor: annotationsStore.selectedClass?.color || '#006400' }"></div>
                <span class="font-semibold truncate text-slate-800 text-[10px]">{{ annotationsStore.selectedClass?.name || 'Hutan Lahan Kering' }}</span>
              </div>
            </div>

            <!-- Opacity & Transparency Control inside Toolbar -->
            <div class="p-1.5 bg-slate-50 rounded-md border border-slate-200 text-[10px] space-y-1">
              <div class="flex items-center justify-between text-[9px] font-bold text-slate-600">
                <span class="uppercase tracking-wider">Transparansi:</span>
                <span class="font-mono text-slate-800 font-bold">{{ Math.round(polygonOpacity * 100) }}%</span>
              </div>
              <div class="flex items-center gap-1.5">
                <button
                  @click="togglePeekVisibility"
                  class="p-0.5 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-200 cursor-pointer"
                  :title="isPeekHidden ? 'Tampilkan kembali poligon' : 'Intip citra satelit (sembunyikan poligon)'"
                >
                  <EyeOff v-if="isPeekHidden" :size="12" class="text-slate-800" />
                  <Eye v-else :size="12" class="text-slate-500" />
                </button>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  v-model="polygonOpacity"
                  @input="updateOpacity"
                  class="w-full h-1 bg-slate-200 rounded-md appearance-none cursor-pointer accent-slate-800"
                  title="Atur transparansi kenampakan hasil digitasi poligon"
                />
              </div>
              <!-- Presets -->
              <div class="grid grid-cols-3 gap-1 pt-0.5">
                <button
                  @click="setOpacityPreset(0)"
                  class="py-0.5 rounded-sm text-[9px] font-medium border transition-all cursor-pointer text-center"
                  :class="polygonOpacity === 0 ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                  title="Transparan 100% (hanya garis batas)"
                >
                  0%
                </button>
                <button
                  @click="setOpacityPreset(0.5)"
                  class="py-0.5 rounded-sm text-[9px] font-medium border transition-all cursor-pointer text-center"
                  :class="polygonOpacity === 0.5 ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                  title="Transparansi Sedang 50%"
                >
                  50%
                </button>
                <button
                  @click="setOpacityPreset(0.85)"
                  class="py-0.5 rounded-sm text-[9px] font-medium border transition-all cursor-pointer text-center"
                  :class="polygonOpacity === 0.85 ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                  title="Solid 85%"
                >
                  85%
                </button>
              </div>
            </div>

            <!-- Kontrol Transparansi Grid Sebelah / Luar Grid -->
            <div class="p-1.5 bg-slate-50 rounded-md border border-slate-200 text-[10px] space-y-1">
              <div class="flex items-center justify-between text-[9px] font-bold text-slate-500">
                <span class="uppercase">Citra Luar Grid:</span>
                <span class="font-mono text-slate-700 font-bold">{{ outsideDimOpacity === 0 ? 'Jernih (0% Dim)' : `${Math.round(outsideDimOpacity * 100)}% Dim` }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <input
                  type="range"
                  min="0.0"
                  max="0.8"
                  step="0.05"
                  v-model.number="outsideDimOpacity"
                  @input="updateOutsideMask"
                  class="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-600"
                  title="Atur tingkat transparansi/kegelapan area di luar grid untuk melihat citra di grid sebelah"
                />
              </div>
            </div>

            <!-- Fitur Edge-Matching: Intip Poligon Grid Sebelah -->
            <div class="p-2 bg-slate-50 rounded-md border border-slate-200 text-[10px] space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5 font-bold text-slate-800">
                  <component :is="showNeighborPolygons ? Eye : EyeOff" :size="12" class="text-slate-600" />
                  <span>Poligon Grid Sebelah</span>
                </div>
                <button
                  @click="toggleNeighborPolygons"
                  type="button"
                  class="relative inline-flex h-4 w-7 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                  :class="showNeighborPolygons ? 'bg-slate-800' : 'bg-slate-300'"
                  title="Aktifkan untuk mengintip hasil digitasi grid sekitar agar batas tutupan lahan pas tersambung (Edge-Matching)"
                >
                  <span
                    class="pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                    :class="showNeighborPolygons ? 'translate-x-3' : 'translate-x-0'"
                  />
                </button>
              </div>

              <!-- Status Penjelasan & Badge -->
              <div class="flex items-center justify-between text-[9px] text-slate-500">
                <span>Edge-Matching</span>
                <span v-if="isLoadingNeighbors" class="text-slate-600 animate-pulse font-semibold">Memuat...</span>
                <span v-else-if="showNeighborPolygons" class="text-slate-700 font-semibold bg-slate-200/80 px-1 py-0.2 rounded text-[8.5px]">
                  {{ neighborFeaturesCount }} Poligon
                </span>
                <span v-else class="text-slate-400">Non-Aktif</span>
              </div>

              <!-- Slider Transparansi Poligon Tetangga (jika aktif) -->
              <div v-if="showNeighborPolygons" class="space-y-1.5 pt-1 border-t border-slate-200">
                <div class="flex items-center justify-between text-[9px] text-slate-800">
                  <span class="text-slate-500">Transparansi:</span>
                  <span class="font-mono font-bold">{{ Math.round(neighborPolygonsOpacity * 100) }}%</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.8"
                  step="0.05"
                  v-model.number="neighborPolygonsOpacity"
                  @input="updateNeighborOpacity"
                  class="w-full h-1 bg-slate-200 rounded-md appearance-none cursor-pointer accent-slate-800"
                  title="Atur transparansi warna poligon grid sebelah"
                />

                <!-- Toggle Snapping ke Batas Grid Tetangga -->
                <div class="pt-1 border-t border-slate-200 flex items-center justify-between text-[9px]">
                  <span class="text-slate-600 font-medium flex items-center gap-1">
                    <Magnet :size="10" :class="isNeighborSnappingEnabled ? 'text-indigo-600' : 'text-slate-400'" />
                    <span>Snap Grid Tetangga:</span>
                  </span>
                  <button
                    @click="toggleNeighborSnapping"
                    class="px-1.5 py-0.5 rounded text-[8.5px] font-bold border transition-colors cursor-pointer"
                    :class="isNeighborSnappingEnabled ? 'bg-indigo-600 text-white border-indigo-600 shadow-2xs' : 'bg-white text-slate-500 border-slate-300'"
                    title="Aktifkan agar kursor menempel ke titik sudut poligon grid sebelah saat memotong atau membuat poligon"
                  >
                    {{ isNeighborSnappingEnabled ? 'ON' : 'OFF' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Keyboard Quick Tips (Smooth GIS Experience) -->
            <div class="px-2 py-1.5 bg-slate-50 rounded-md text-[9px] text-slate-500 leading-tight space-y-1 border border-slate-200">
              <div class="flex items-center justify-between">
                <span>Tahan <kbd class="px-1 py-0.2 bg-white rounded border border-slate-300 font-mono text-slate-700 font-semibold">Spasi</kbd></span>
                <span class="text-slate-400">Intip Citra</span>
              </div>
              <div class="flex items-center justify-between">
                <span><kbd class="px-1 py-0.2 bg-white rounded border border-slate-300 font-mono text-slate-700 font-semibold">Del</kbd></span>
                <span class="text-slate-400">Undo Titik</span>
              </div>
              <div class="flex items-center justify-between">
                <span><kbd class="px-1 py-0.2 bg-white rounded border border-slate-300 font-mono text-slate-700 font-semibold">Ctrl+S</kbd></span>
                <span class="text-slate-400">Simpan Draf</span>
              </div>
            </div>
          </template>
        </div>

        <!-- Merge Mode Floating Bar (Centered at top so it never overlaps left toolbar or right controls) -->
        <div v-if="activeTool === 'merge'" class="absolute top-4 left-1/2 -translate-x-1/2 z-30 bg-slate-900/95 backdrop-blur-md text-white rounded-md shadow-xl px-3.5 py-1.5 flex items-center gap-3 border border-slate-700 animate-in fade-in slide-in-from-top-2 flex-wrap">
          <div class="text-xs flex items-center gap-1.5">
            <Combine :size="14" class="text-slate-300" />
            <span class="font-bold text-slate-200">Mode Gabung:</span>
            <span class="bg-slate-800 text-slate-200 px-2 py-0.5 rounded text-[11px] font-semibold border border-slate-700">
              {{ selectedForMerge.length }} terpilih
            </span>
          </div>

          <!-- Class Selector for Merged Result -->
          <div v-if="selectedForMerge.length >= 2" class="flex items-center gap-1.5 bg-slate-800 px-2 py-1 rounded border border-slate-700">
            <span class="text-[11px] text-slate-300 font-medium whitespace-nowrap">Hasil Kelas:</span>
            <select
              v-model="mergeTargetClassId"
              class="bg-slate-900 text-white text-xs rounded px-2 py-0.5 font-semibold border border-slate-600 focus:outline-none focus:ring-1 focus:ring-emerald-400 cursor-pointer max-w-[210px] sm:max-w-[270px]"
            >
              <optgroup label="Poligon yang Dipilih">
                <option
                  v-for="c in mergeParticipantClasses"
                  :key="'participant-' + c.id"
                  :value="c.id"
                >
                  {{ c.name }} ({{ formatArea(c.totalArea) }}){{ c.id === largestMergePolygon?.properties?.class_id ? ' ★ Terbesar' : '' }}
                </option>
              </optgroup>
              <optgroup label="Kelas Lainnya">
                <option
                  v-for="c in annotationsStore.classes.filter(cls => !mergeParticipantClasses.some(p => p.id === cls.id))"
                  :key="'other-' + c.id"
                  :value="c.id"
                >
                  {{ c.name }}
                </option>
              </optgroup>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="executeMerge"
              :disabled="selectedForMerge.length < 2 || mergeLoading"
              class="px-3 py-1 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40 disabled:hover:bg-emerald-700 text-white rounded-md text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer shadow-xs active:scale-95"
            >
              <Combine :size="13" />
              <span>{{ mergeLoading ? 'Menggabungkan...' : 'Gabung Poligon' }}</span>
            </button>
            <button @click="cancelMerge" class="px-2 py-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md text-xs font-medium cursor-pointer transition-colors">
              Batal
            </button>
          </div>
        </div>

        <!-- Edit Vertices Floating Bar: Finish & Close Polygon Immediately -->
        <div v-if="activeTool === 'edit'" class="absolute top-4 left-1/2 -translate-x-1/2 z-30 bg-slate-900/95 backdrop-blur-md text-white rounded-md shadow-xl px-3.5 py-1.5 flex items-center gap-3 border border-slate-700 animate-in fade-in slide-in-from-top-2 flex-wrap">
          <div class="text-xs flex items-center gap-1.5">
            <Edit3 :size="14" class="text-amber-400" />
            <span class="font-bold text-slate-200">Mode Edit Titik Simpul</span>
            <span class="text-[10px] text-slate-400 hidden sm:inline">• Geser titik simpul atau klik garis untuk tambah titik</span>
          </div>

          <button
            type="button"
            @click="enableTopologicalEditing = !enableTopologicalEditing; showToast(enableTopologicalEditing ? '🧲 Edit Topologis Aktif: Titik batas bersama bergerak bersamaan tanpa celah.' : 'Edit Topologis dinonaktifkan.')"
            class="px-2.5 py-1 rounded-md text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer border shadow-xs"
            :class="enableTopologicalEditing ? 'bg-indigo-600/90 border-indigo-400 text-white ring-1 ring-indigo-400/50' : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-slate-200'"
            :title="enableTopologicalEditing ? 'Edit Topologis Aktif: Titik batas bersama bergerak serentak tanpa celah' : 'Klik untuk mengaktifkan Edit Topologis'"
          >
            <Magnet :size="13" :class="enableTopologicalEditing ? 'text-amber-300 animate-pulse' : 'text-slate-400'" />
            <span>{{ enableTopologicalEditing ? 'Edit Topologis (Anti-Celah)' : 'Edit Biasa' }}</span>
          </button>

          <button
            @click="closeAndFinishVertexEdit"
            class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-xs active:scale-95"
            title="Tutup dan simpan perubahan titik simpul secara rapat"
          >
            <Check :size="13" />
            <span>Selesai & Tutup Poligon</span>
          </button>
        </div>

        <!-- Floating Map Top-Right Controls: Imagery & Spectral Adjustment Panel -->
        <div class="absolute top-4 right-4 z-20 flex flex-col flex-nowrap items-end gap-2 pointer-events-auto">
          <!-- Trigger Button on Map -->
          <button
            @click="showImageryPanel = !showImageryPanel"
            class="flex items-center gap-2 px-3 py-1.5 bg-white/95 hover:bg-white text-slate-800 rounded-md shadow-md border border-slate-300 backdrop-blur-md text-xs font-semibold transition-all cursor-pointer"
            :class="showImageryPanel ? 'ring-2 ring-slate-800 text-slate-900 bg-slate-100' : ''"
            title="Buka Pengaturan Citra, Komposit, Kontras & Gamma"
          >
            <SlidersHorizontal :size="14" class="text-slate-600" />
            <span class="font-bold">Citra & Spektral</span>
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-bold border border-slate-200/80">{{ currentYear }}</span>
          </button>

          <!-- Floating Panel Citra & Spektral -->
          <div
            v-if="showImageryPanel"
            class="w-[360px] sm:w-[380px] max-w-[calc(100vw-32px)] bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col flex-nowrap max-h-[80vh] text-slate-800 text-xs animate-in fade-in zoom-in-95 duration-150"
          >
            <!-- Panel Header -->
            <div class="px-3.5 py-2.5 bg-slate-50/90 border-b border-slate-200 flex items-center justify-between shrink-0">
              <div class="flex items-center gap-2 text-rose-700 font-bold">
                <Satellite :size="15" />
                <span class="text-xs text-slate-900 font-extrabold">Kontrol Citra & Spektral</span>
              </div>
              <div class="flex items-center gap-1.5">
                <button
                  @click="resetImagerySettings"
                  class="px-2 py-1 text-[10px] font-bold text-slate-600 hover:text-rose-600 rounded-lg hover:bg-slate-200/60 transition-colors flex items-center gap-1 cursor-pointer"
                  title="Reset Kontras, Kecerahan & Gamma ke Standar"
                >
                  <RefreshCcw :size="11" />
                  <span>Reset Visual</span>
                </button>
                <button
                  @click="showImageryPanel = false"
                  class="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer"
                >
                  <X :size="14" />
                </button>
              </div>
            </div>

            <!-- Tab Switcher -->
            <div class="p-1.5 bg-slate-100/80 border-b border-slate-200 flex items-center gap-1 shrink-0 text-[11px] font-bold">
              <button
                @click="imageryActiveTab = 'layers'"
                class="flex-1 py-1.5 rounded-lg transition-all text-center flex items-center justify-center gap-1.5 cursor-pointer"
                :class="imageryActiveTab === 'layers' ? 'bg-white text-rose-600 shadow-2xs' : 'text-slate-600 hover:text-slate-900'"
              >
                <Layers :size="13" />
                <span>Pilihan Komposit ({{ layerOptions.length }})</span>
              </button>
              <button
                @click="imageryActiveTab = 'contrast'"
                class="flex-1 py-1.5 rounded-lg transition-all text-center flex items-center justify-center gap-1.5 cursor-pointer"
                :class="imageryActiveTab === 'contrast' ? 'bg-white text-rose-600 shadow-2xs' : 'text-slate-600 hover:text-slate-900'"
              >
                <Sliders :size="13" />
                <span>Kontras, Gamma & Visual</span>
              </button>
            </div>

            <!-- Panel Body (Scrollable) -->
            <div class="flex-1 min-h-0 overflow-y-auto p-3.5 space-y-4 flex flex-col flex-nowrap">
              <!-- TAB 1: Pilihan Layer Komposit -->
              <div v-if="imageryActiveTab === 'layers'" class="space-y-3">
                <!-- Tahun Komposit -->
                <div class="bg-slate-50/80 p-2.5 rounded-xl border border-slate-200">
                  <div class="flex items-center justify-between mb-1.5 text-[11px]">
                    <span class="font-bold text-slate-700">Tahun Citra Sentinel-2:</span>
                    <span class="font-mono font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">{{ currentYear }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <button
                      v-for="yr in availableRasterYears"
                      :key="yr"
                      @click="setYear(yr)"
                      class="flex-1 py-1 text-xs font-bold rounded-lg transition-all cursor-pointer text-center"
                      :class="currentYear === yr ? 'bg-rose-600 text-white shadow-xs' : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'"
                    >
                      {{ yr }}
                    </button>
                  </div>
                </div>

                <!-- Layer Choices -->
                <div class="space-y-1.5">
                  <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Pilih Komposit Spektral:</div>
                  <button
                    v-for="layer in layerOptions"
                    :key="layer.id"
                    @click="setLayer(layer.id)"
                    class="w-full text-left p-2.5 rounded-xl transition-all border flex items-center justify-between group cursor-pointer"
                    :class="currentLayer === layer.id
                      ? 'bg-rose-50/90 border-rose-400 text-rose-900 shadow-xs ring-1 ring-rose-400/50'
                      : 'bg-white/80 border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'"
                  >
                    <div class="flex items-center gap-2.5">
                      <component :is="layer.icon" :size="16" :class="layer.colorClass" class="shrink-0" />
                      <div>
                        <div class="text-xs font-bold leading-tight">{{ layer.name }}</div>
                        <div class="text-[9px] text-slate-500 leading-tight mt-0.5">{{ layer.desc }}</div>
                      </div>
                    </div>
                    <div
                      class="w-3 h-3 rounded-full border shrink-0 flex items-center justify-center"
                      :class="currentLayer === layer.id ? 'bg-rose-600 border-rose-700 text-white' : 'border-slate-300 bg-white'"
                    >
                      <Check v-if="currentLayer === layer.id" :size="9" class="stroke-[3]" />
                    </div>
                  </button>
                </div>
              </div>

              <!-- TAB 2: Kontras, Gamma & Visual Adjustments -->
              <div v-if="imageryActiveTab === 'contrast'" class="space-y-4">
                <!-- Preset Cepat -->
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between text-[11px] font-bold text-slate-700">
                    <span class="flex items-center gap-1.5"><Sparkles :size="13" class="text-amber-500" /> Preset Spektral Cepat:</span>
                  </div>
                  <div class="grid grid-cols-2 gap-1.5 text-[11px]">
                    <button
                      @click="applyPreset('normal')"
                      class="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-bold text-left flex items-center justify-between cursor-pointer"
                    >
                      <span>🔄 Normal</span>
                      <span class="text-[9px] text-slate-400">100%</span>
                    </button>
                    <button
                      @click="applyPreset('high_contrast')"
                      class="p-2 rounded-xl border border-rose-200 bg-rose-50/50 hover:bg-rose-50 text-rose-700 font-bold text-left flex items-center justify-between cursor-pointer"
                    >
                      <span>⚡ Kontras Tinggi</span>
                      <span class="text-[9px] text-rose-500">Tegas</span>
                    </button>
                    <button
                      @click="applyPreset('vegetation')"
                      class="p-2 rounded-xl border border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50 text-emerald-800 font-bold text-left flex items-center justify-between cursor-pointer"
                    >
                      <span>🌲 Penguat Vegetasi</span>
                      <span class="text-[9px] text-emerald-600">Sawit/Hutan</span>
                    </button>
                    <button
                      @click="applyPreset('haze')"
                      class="p-2 rounded-xl border border-blue-200 bg-blue-50/50 hover:bg-blue-50 text-blue-800 font-bold text-left flex items-center justify-between cursor-pointer"
                    >
                      <span>⛅ Tembus Kabut</span>
                      <span class="text-[9px] text-blue-600">Awan Tipis</span>
                    </button>
                    <button
                      @click="applyPreset('water')"
                      class="col-span-2 p-2 rounded-xl border border-cyan-200 bg-cyan-50/50 hover:bg-cyan-50 text-cyan-900 font-bold text-left flex items-center justify-between cursor-pointer"
                    >
                      <span>💧 Fokus Air, Sungai & Tambak</span>
                      <span class="text-[9px] text-cyan-600">Basah</span>
                    </button>
                  </div>
                </div>

                <!-- Sliders Section -->
                <div class="bg-slate-50/80 p-3 rounded-xl border border-slate-200 space-y-3.5">
                  <!-- Kontras Slider -->
                  <div class="space-y-1">
                    <div class="flex items-center justify-between text-xs font-bold">
                      <span class="text-slate-700 flex items-center gap-1.5">
                        <Contrast :size="13" class="text-slate-500" />
                        <span>Kontras (Contrast):</span>
                      </span>
                      <span class="font-mono text-rose-600 font-extrabold bg-white px-2 py-0.5 rounded border border-slate-200">{{ imagerySettings.contrast }}%</span>
                    </div>
                    <input
                      type="range"
                      min="50"
                      max="200"
                      step="2"
                      v-model.number="imagerySettings.contrast"
                      class="w-full accent-rose-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                    <div class="flex justify-between text-[9px] text-slate-400 font-mono">
                      <span>50% (Lembut)</span>
                      <span>100% (Standar)</span>
                      <span>200% (Ekstrem)</span>
                    </div>
                  </div>

                  <!-- Kecerahan Slider -->
                  <div class="space-y-1">
                    <div class="flex items-center justify-between text-xs font-bold">
                      <span class="text-slate-700 flex items-center gap-1.5">
                        <Sun :size="13" class="text-amber-500" />
                        <span>Kecerahan (Brightness):</span>
                      </span>
                      <span class="font-mono text-amber-600 font-extrabold bg-white px-2 py-0.5 rounded border border-slate-200">{{ imagerySettings.brightness }}%</span>
                    </div>
                    <input
                      type="range"
                      min="50"
                      max="200"
                      step="2"
                      v-model.number="imagerySettings.brightness"
                      class="w-full accent-amber-500 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                    <div class="flex justify-between text-[9px] text-slate-400 font-mono">
                      <span>50% (Gelap)</span>
                      <span>100%</span>
                      <span>200% (Terang)</span>
                    </div>
                  </div>

                  <!-- Gamma Radiometrik Slider -->
                  <div class="space-y-1">
                    <div class="flex items-center justify-between text-xs font-bold">
                      <span class="text-slate-700 flex items-center gap-1.5">
                        <SlidersHorizontal :size="13" class="text-indigo-500" />
                        <span>Koreksi Gamma:</span>
                      </span>
                      <span class="font-mono text-indigo-600 font-extrabold bg-white px-2 py-0.5 rounded border border-slate-200">{{ imagerySettings.gamma.toFixed(2) }}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="2.5"
                      step="0.05"
                      v-model.number="imagerySettings.gamma"
                      class="w-full accent-indigo-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                    <div class="flex justify-between text-[9px] text-slate-400 font-mono">
                      <span>0.5x (Tekan Sorotan)</span>
                      <span>1.0x</span>
                      <span>2.5x (Angkat Bayangan)</span>
                    </div>
                  </div>

                  <!-- Saturasi Warna Slider -->
                  <div class="space-y-1">
                    <div class="flex items-center justify-between text-xs font-bold">
                      <span class="text-slate-700 flex items-center gap-1.5">
                        <Palette :size="13" class="text-emerald-500" />
                        <span>Saturasi Warna:</span>
                      </span>
                      <span class="font-mono text-emerald-600 font-extrabold bg-white px-2 py-0.5 rounded border border-slate-200">{{ imagerySettings.saturation }}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="250"
                      step="5"
                      v-model.number="imagerySettings.saturation"
                      class="w-full accent-emerald-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                    <div class="flex justify-between text-[9px] text-slate-400 font-mono">
                      <span>0% (Hitam Putih)</span>
                      <span>100%</span>
                      <span>250% (Sangat Pekat)</span>
                    </div>
                  </div>

                  <!-- Opasitas Citra -->
                  <div class="space-y-1">
                    <div class="flex items-center justify-between text-xs font-bold">
                      <span class="text-slate-700 flex items-center gap-1.5">
                        <Eye :size="13" class="text-slate-500" />
                        <span>Opasitas Layer Citra:</span>
                      </span>
                      <span class="font-mono text-slate-700 font-extrabold bg-white px-2 py-0.5 rounded border border-slate-200">{{ imagerySettings.opacity }}%</span>
                    </div>
                    <input
                      type="range"
                      min="20"
                      max="100"
                      step="5"
                      v-model.number="imagerySettings.opacity"
                      class="w-full accent-slate-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                  </div>

                  <!-- Opasitas Poligon Anotasi -->
                  <div class="space-y-1 pt-2 border-t border-slate-200">
                    <div class="flex items-center justify-between text-xs font-bold">
                      <span class="text-slate-700 flex items-center gap-1.5">
                        <Shapes :size="13" class="text-purple-500" />
                        <span>Opasitas Poligon Anotasi:</span>
                      </span>
                      <span class="font-mono text-purple-600 font-extrabold bg-white px-2 py-0.5 rounded border border-slate-200">{{ Math.round(polygonOpacity * 100) }}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      v-model.number="polygonOpacity"
                      class="w-full accent-purple-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                    <div class="flex items-center gap-1 pt-1">
                      <button
                        @click="setOpacityPreset(0)"
                        class="flex-1 py-1 rounded text-[10px] font-bold border transition-all cursor-pointer text-center"
                        :class="polygonOpacity === 0 ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                      >
                        0% (Garis)
                      </button>
                      <button
                        @click="setOpacityPreset(0.5)"
                        class="flex-1 py-1 rounded text-[10px] font-bold border transition-all cursor-pointer text-center"
                        :class="polygonOpacity === 0.5 ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                      >
                        50%
                      </button>
                      <button
                        @click="setOpacityPreset(0.85)"
                        class="flex-1 py-1 rounded text-[10px] font-bold border transition-all cursor-pointer text-center"
                        :class="polygonOpacity === 0.85 ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                      >
                        85%
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Leaflet Map Container -->
        <div id="map-container" class="w-full h-full z-0"></div>

        <!-- Floating Banner: Mode Tambah Pin Catatan Aktif -->
        <div
          v-if="isAddEvaluationPinMode"
          class="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-slate-900/95 text-white px-4 py-2 rounded-md shadow-xl flex items-center gap-3 text-xs font-medium border border-slate-700 backdrop-blur-md animate-in fade-in slide-in-from-top-2 duration-150"
        >
          <div class="w-6 h-6 rounded bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
            <MapPin :size="15" />
          </div>
          <div>
            <div class="font-bold text-xs text-white">Mode Tambah Catatan Evaluasi</div>
            <div class="text-[10px] text-slate-300">Klik lokasi pada peta untuk meletakkan catatan</div>
          </div>
          <button
            @click="toggleAddEvaluationPinMode(false)"
            class="ml-2 px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded text-xs font-medium transition-all cursor-pointer flex items-center gap-1 shrink-0 border border-slate-600"
          >
            <X :size="12" />
            <span>Batal (Esc)</span>
          </button>
        </div>

        <!-- Floating Banner: Pulihkan Draf Offline / Lokal (Poin 1) -->
        <div
          v-if="showDraftRestorePrompt && pendingDraftToRestore"
          class="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-white/95 text-slate-800 px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-3 text-xs border border-amber-300 backdrop-blur-md animate-in fade-in slide-in-from-top-2"
        >
          <div class="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
            <Save :size="16" />
          </div>
          <div>
            <div class="font-bold text-xs text-slate-900">Ditemukan Draf Lokal di Browser</div>
            <div class="text-[11px] text-slate-600">
              Terdapat cadangan offline dari jam {{ new Date(pendingDraftToRestore.updatedAt).toLocaleTimeString() }} ({{ pendingDraftToRestore.features?.length || 0 }} poligon).
            </div>
          </div>
          <div class="flex items-center gap-1.5 ml-2">
            <button
              @click="restoreOfflineDraft"
              class="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition-all shadow-2xs cursor-pointer"
            >
              Pulihkan Draf
            </button>
            <button
              @click="discardOfflineDraftPrompt"
              class="px-2 py-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg text-xs font-medium cursor-pointer"
            >
              Abaikan
            </button>
          </div>
        </div>

        <!-- SVG Gamma Filter Definition for Leaflet Tile GPU Filtering -->
        <svg class="sr-only" aria-hidden="true" style="position: absolute; width: 0; height: 0; pointer-events: none; overflow: hidden;">
          <filter id="raster-gamma-filter" color-interpolation-filters="sRGB">
            <feComponentTransfer>
              <feFuncR type="gamma" :exponent="imagerySettings.gamma ? (1 / imagerySettings.gamma).toFixed(3) : 1" amplitude="1" offset="0" />
              <feFuncG type="gamma" :exponent="imagerySettings.gamma ? (1 / imagerySettings.gamma).toFixed(3) : 1" amplitude="1" offset="0" />
              <feFuncB type="gamma" :exponent="imagerySettings.gamma ? (1 / imagerySettings.gamma).toFixed(3) : 1" amplitude="1" offset="0" />
            </feComponentTransfer>
          </filter>
        </svg>

        <!-- GIS Bottom Status Bar (Clean Light Theme, No AI Slop) -->
        <div class="absolute bottom-0 left-0 right-0 z-10 bg-white/95 text-slate-600 backdrop-blur-md border-t border-slate-200/90 px-3.5 py-1.5 flex items-center justify-between text-[11px] font-mono select-none pointer-events-auto overflow-hidden shadow-2xs">
          <div class="flex items-center gap-3 overflow-hidden">
            <div class="flex items-center gap-1.5 text-slate-500">
              <span class="text-slate-400 font-semibold text-[10px] tracking-wider uppercase">Zoom:</span>
              <span class="text-slate-800 font-semibold">{{ mapZoom }}</span>
            </div>
            <span class="text-slate-200">|</span>
            <div class="flex items-center gap-1.5 text-slate-500">
              <span class="text-slate-400 font-semibold text-[10px] tracking-wider uppercase">Skala:</span>
              <span class="text-slate-800 font-semibold">{{ mapScaleRatio }}</span>
            </div>
            <template v-if="cursorCoords.lat">
              <span class="text-slate-200">|</span>
              <div class="flex items-center gap-1.5 text-slate-500">
                <span class="text-slate-400 font-semibold text-[10px] tracking-wider uppercase">Koordinat:</span>
                <span class="text-slate-700 font-medium">{{ cursorCoords.lat }}°, {{ cursorCoords.lng }}°</span>
              </div>
            </template>
            <span class="text-slate-200 hidden lg:inline">|</span>
            <div class="hidden lg:flex items-center gap-1.5 text-slate-500">
              <span class="text-slate-400 font-semibold text-[10px] tracking-wider uppercase">Proyeksi:</span>
              <span class="text-slate-600">WGS 84 (EPSG:4326)</span>
            </div>
          </div>
          <div class="flex items-center gap-3 shrink-0 pl-2">
            <div class="flex items-center gap-1.5 text-slate-500">
              <span class="text-slate-400 font-semibold text-[10px] tracking-wider uppercase">Objek:</span>
              <span class="text-slate-800 font-semibold">{{ features.length }} Poligon</span>
            </div>
            <span class="text-slate-200 hidden sm:inline">|</span>
            <div class="hidden sm:flex items-center gap-1.5 text-slate-500">
              <span class="text-slate-400 font-semibold text-[10px] tracking-wider uppercase">Total Luas:</span>
              <span class="text-slate-800 font-semibold">{{ formatArea(totalAreaSqm) }}</span>
            </div>
          </div>
        </div>

        <!-- Floating Multi-Selection Action Toolbar -->
        <div
          v-if="selectedPolyUiIds.size > 0"
          class="absolute bottom-10 left-1/2 -translate-x-1/2 z-40 bg-white/95 text-slate-800 px-3.5 py-1.5 rounded-lg shadow-xl border border-slate-200 backdrop-blur-md flex items-center gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-150"
        >
          <div class="flex items-center gap-1.5 pr-2.5 border-r border-slate-200 text-xs font-mono font-medium text-slate-700">
            <span>{{ selectedPolyUiIds.size }} Poligon Terpilih</span>
          </div>

          <!-- Action 1: Hapus Massal -->
          <button
            @click="batchDeleteSelectedPolygons"
            class="bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium px-2.5 py-1 rounded-md shadow-2xs transition-colors flex items-center gap-1 cursor-pointer"
            title="Hapus semua poligon terpilih"
          >
            <Trash2 :size="13" />
            <span>Hapus</span>
          </button>

          <!-- Action 2: Gabung Massal -->
          <button
            @click="batchMergeSelectedPolygons"
            :disabled="selectedPolyUiIds.size < 2"
            class="bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 border border-slate-200 text-xs font-medium px-2.5 py-1 rounded-md shadow-2xs transition-colors flex items-center gap-1 cursor-pointer"
            title="Gabungkan semua poligon terpilih menjadi 1 poligon utuh"
          >
            <Combine :size="13" />
            <span>Gabung</span>
          </button>

          <!-- Action 3: Batal -->
          <button
            @click="clearPolygonSelection"
            class="text-slate-400 hover:text-slate-700 p-1 rounded-md hover:bg-slate-100 transition-colors cursor-pointer"
            title="Batal seleksi"
          >
            <X :size="14" />
          </button>
        </div>

        <!-- Empty Grid State Banner -->
        <div
          v-if="!selectedTaskId"
          class="absolute inset-0 z-30 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4"
        >
          <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-200 text-center space-y-4">
            <div class="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto border border-rose-100">
              <Grid :size="28" />
            </div>
            <div class="space-y-1">
              <h3 class="text-base font-extrabold text-slate-900">Pilih Grid untuk Mulai Digitasi</h3>
              <p class="text-xs text-slate-500 leading-relaxed">
                {{ selectableTasks.length > 0 ? 'Pilih salah satu grid Anda pada dropdown di sidebar kiri.' : 'Anda belum mengambil grid tugas digitasi. Buka Grid Map untuk memilih dan mengklaim grid yang tersedia.' }}
              </p>
            </div>
            <div class="pt-2 flex items-center justify-center gap-3">
              <router-link
                to="/tasks"
                class="bg-gradient-to-r from-rose-600 to-red-500 hover:from-rose-500 hover:to-red-400 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-md shadow-rose-500/20 transition-all flex items-center gap-2"
              >
                <Rocket :size="14" />
                <span>Buka Grid Map & Klaim Grid</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Toast Notification -->
      <div
        v-if="toastMessage"
        class="absolute bottom-8 left-1/2 -translate-x-1/2 bg-white text-slate-800 border border-slate-200 px-4 py-2 rounded-lg shadow-xl z-30 text-xs font-medium flex items-center gap-2 backdrop-blur-md animate-in fade-in slide-in-from-bottom-2 duration-150"
      >
        <CheckCircle2 :size="15" class="text-emerald-600" />
        <span>{{ toastMessage }}</span>
      </div>
    </main>

    <!-- RIGHT RESIZER DRAG HANDLE -->
    <div
      @mousedown="startResizeRight"
      class="w-1.5 hover:w-2 bg-transparent hover:bg-rose-500/40 active:bg-rose-600 transition-all cursor-col-resize z-20 shrink-0 relative -ml-1 flex items-center justify-center group select-none"
      title="Tarik untuk mengatur lebar sidebar kanan"
    >
      <div class="w-0.5 h-8 bg-slate-300 group-hover:bg-rose-500 rounded-full transition-colors"></div>
    </div>

    <!-- RIGHT SIDEBAR: 12 Land Cover Classes & Polygons List -->
    <aside
      class="h-full max-h-full min-h-0 bg-white border-l border-slate-200 flex flex-col z-10 shadow-sm shrink-0 overflow-y-auto select-none"
      :style="{ width: `${rightSidebarWidth}px` }"
    >
      <!-- Tabs: 12 Kelas vs Poligon List -->
      <div class="flex border-b border-slate-200 bg-slate-50/70 p-1">
        <button
          @click="rightTab = 'classes'"
          class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all text-center flex items-center justify-center gap-1.5 cursor-pointer"
          :class="rightTab === 'classes' ? 'bg-white text-rose-600 shadow-xs border border-slate-200' : 'text-slate-500 hover:text-slate-900'"
        >
          <Palette :size="13" />
          <span>Kelas</span>
        </button>
        <button
          @click="rightTab = 'polygons'"
          class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all text-center flex items-center justify-center gap-1.5 cursor-pointer"
          :class="rightTab === 'polygons' ? 'bg-white text-rose-600 shadow-xs border border-slate-200' : 'text-slate-500 hover:text-slate-900'"
        >
          <Shapes :size="13" />
          <span>Poligon ({{ features.length }})</span>
        </button>
      </div>

      <!-- Selected Polygon Info & 1-Click Class Switcher (when a polygon is clicked) -->
      <div v-if="clickedFeatureIdx !== null" class="p-3 bg-indigo-50/90 border-b border-indigo-200 space-y-2.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <div class="w-3.5 h-3.5 rounded-sm border border-slate-300" :style="{ backgroundColor: features[clickedFeatureIdx]?.properties?.color || '#9CA3AF' }"></div>
            <span class="text-xs font-extrabold text-indigo-950">Poligon #{{ clickedFeatureIdx + 1 }}</span>
          </div>
          <button @click="clickedFeatureIdx = null" class="text-indigo-400 hover:text-indigo-600 cursor-pointer"><X :size="14" /></button>
        </div>

        <div class="text-[11px] text-indigo-900 flex justify-between items-center bg-white/70 p-2 rounded-xl border border-indigo-100">
          <span>Kelas Saat Ini:</span>
          <b class="font-bold text-slate-800">{{ features[clickedFeatureIdx]?.properties?.class_name || 'Belum Teridentifikasi' }}</b>
        </div>

        <div class="space-y-1">
          <div class="text-[10px] font-bold text-indigo-800 uppercase tracking-wider">
            Ganti Jenis Tutupan Lahan:
          </div>
          <div class="grid grid-cols-2 gap-1 max-h-48 overflow-y-auto pr-1">
            <button
              v-for="cls in annotationsStore.classes"
              :key="cls.id"
              @click="reassignClassToClickedPolygon(cls)"
              class="text-left p-1.5 rounded-lg transition-all border flex items-center gap-1.5 cursor-pointer text-[10px]"
              :class="features[clickedFeatureIdx]?.properties?.class_id === cls.id
                ? 'bg-indigo-600 text-white border-indigo-600 font-bold shadow-xs'
                : 'bg-white border-slate-200 text-slate-700 hover:border-indigo-300 hover:bg-indigo-50/50'"
            >
              <div class="w-2.5 h-2.5 rounded-xs shrink-0 border border-slate-300" :style="{ backgroundColor: cls.color }"></div>
              <span class="truncate">{{ cls.name }}</span>
            </button>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-1 border-t border-indigo-200/60">
          <button
            @click="handleSmartDeleteSelected"
            :disabled="features.length <= 1"
            class="flex-1 py-1.5 px-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-xs disabled:opacity-40 disabled:cursor-not-allowed"
            title="Hapus poligon ini"
          >
            <Trash2 :size="12" />
            <span>Hapus</span>
          </button>
          <button
            @click="flyToFeature(clickedFeatureIdx)"
            class="py-1.5 px-3 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-xs"
            title="Pusatkan peta ke poligon ini"
          >
            <Crosshair :size="12" />
            <span>Zoom</span>
          </button>
        </div>
      </div>

      <!-- Tab Content 1: Land Cover Classes (for active drawing / splitting) -->
      <div v-show="rightTab === 'classes'" class="flex-1 p-3 space-y-1.5 overflow-y-auto">
        <div class="text-[10px] text-slate-500 pb-1 font-bold flex justify-between uppercase tracking-wider">
          <span>PILIH KELAS AKTIF:</span>
          <span class="text-rose-600 font-mono">U-Net 1024px</span>
        </div>

        <button
          v-for="cls in annotationsStore.classes"
          :key="cls.id"
          @click="annotationsStore.setSelectedClass(cls)"
          class="w-full text-left p-2 rounded-xl transition-all border flex items-center justify-between group cursor-pointer"
          :class="annotationsStore.selectedClass?.id === cls.id 
            ? 'bg-rose-50/90 border-rose-400 shadow-xs ring-1 ring-rose-400/50' 
            : 'bg-slate-50/60 border-slate-200 hover:bg-white hover:border-slate-300'"
        >
          <div class="flex items-center gap-2.5 min-w-0">
            <div
              class="w-4 h-4 rounded-md shrink-0 border border-slate-300 shadow-2xs"
              :style="{ backgroundColor: cls.color }"
            ></div>
            <div class="truncate">
              <div class="text-xs font-bold text-slate-800 group-hover:text-slate-900 leading-tight truncate">
                {{ cls.name }}
              </div>
              <div class="text-[9px] text-slate-500 truncate">{{ cls.description }}</div>
            </div>
          </div>
          <div class="flex items-center gap-1.5 shrink-0 pl-1">
            <span
              v-if="classCounts[cls.id]"
              class="text-[9px] font-mono px-1.5 py-0.2 rounded-full bg-rose-100 text-rose-700 font-bold border border-rose-200"
            >
              {{ classCounts[cls.id] }}
            </span>
            <span class="text-[9px] font-mono text-slate-400 bg-white px-1 py-0.5 rounded border border-slate-200">#{{ cls.id }}</span>
          </div>
        </button>
      </div>

      <!-- Tab Content 2: List of Drawn Polygons with Multi-Selection -->
      <div v-show="rightTab === 'polygons'" class="flex-1 p-3 space-y-2.5 overflow-y-auto flex flex-col">
        <div v-if="features.length === 0" class="text-center py-12 text-slate-400 text-xs">
          Belum ada poligon yang digambar.<br>Gunakan tool Potong / Gambar di kiri atas peta!
        </div>

        <div v-else class="space-y-2">
          <!-- Selection Header Controls -->
          <div class="flex items-center justify-between pb-2 border-b border-slate-200 text-xs">
            <label class="flex items-center gap-2 cursor-pointer font-bold text-slate-700 select-none">
              <input
                type="checkbox"
                :checked="isAllSelected"
                @change="toggleSelectAll"
                class="w-4 h-4 rounded border-slate-300 text-rose-600 focus:ring-rose-500 cursor-pointer"
              />
              <span>Pilih Semua ({{ features.length }})</span>
            </label>
            <span
              v-if="selectedPolyUiIds.size > 0"
              class="text-[11px] font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200"
            >
              {{ selectedPolyUiIds.size }} terpilih
            </span>
          </div>

          <!-- Quick Action Buttons for Selection -->
          <div v-if="selectedPolyUiIds.size > 0" class="flex items-center gap-1.5 p-1.5 bg-indigo-50/80 border border-indigo-200 rounded-xl">
            <button
              @click="batchDeleteSelectedPolygons"
              class="flex-1 bg-rose-600 hover:bg-rose-700 text-white text-[11px] font-bold py-1.5 px-2 rounded-lg transition-all flex items-center justify-center gap-1 cursor-pointer shadow-xs"
              title="Hapus semua poligon terpilih"
            >
              <Trash2 :size="12" />
              <span>Hapus ({{ selectedPolyUiIds.size }})</span>
            </button>
            <button
              @click="batchMergeSelectedPolygons"
              :disabled="selectedPolyUiIds.size < 2"
              class="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white text-[11px] font-bold py-1.5 px-2 rounded-lg transition-all flex items-center justify-center gap-1 cursor-pointer shadow-xs"
              title="Gabungkan poligon terpilih menjadi 1 poligon utuh"
            >
              <Combine :size="12" />
              <span>Gabung ({{ selectedPolyUiIds.size }})</span>
            </button>
            <button
              @click="clearPolygonSelection"
              class="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-200/60 transition-colors cursor-pointer"
              title="Batalkan seleksi"
            >
              <X :size="13" />
            </button>
          </div>

          <!-- Search Filter for Polygons -->
          <div class="relative">
            <input
              v-model="polySearchQuery"
              type="text"
              placeholder="Cari kelas / nomor poligon (misal: #10)..."
              class="w-full bg-slate-50 border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-indigo-400 focus:bg-white transition-all shadow-2xs font-sans"
            />
            <Search :size="13" class="absolute left-2.5 top-2.5 text-slate-400 pointer-events-none" />
          </div>

          <!-- Pagination Bar (if total > pageSize) -->
          <div v-if="filteredAndPagedFeatures.totalPages > 1" class="flex items-center justify-between text-[11px] text-slate-500 bg-slate-50/80 px-2.5 py-1 rounded-xl border border-slate-200/80 font-mono">
            <span>Hal {{ polyListPage }}/{{ filteredAndPagedFeatures.totalPages }} ({{ filteredAndPagedFeatures.total }} item)</span>
            <div class="flex items-center gap-1">
              <button
                @click="polyListPage = Math.max(1, polyListPage - 1)"
                :disabled="polyListPage <= 1"
                class="p-1 rounded-md hover:bg-slate-200 text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                title="Halaman Sebelumnya"
              >
                <ChevronLeft :size="13" />
              </button>
              <button
                @click="polyListPage = Math.min(filteredAndPagedFeatures.totalPages, polyListPage + 1)"
                :disabled="polyListPage >= filteredAndPagedFeatures.totalPages"
                class="p-1 rounded-md hover:bg-slate-200 text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                title="Halaman Berikutnya"
              >
                <ChevronRight :size="13" />
              </button>
            </div>
          </div>

          <!-- Polygon Cards (Virtualized Window) -->
          <div
            v-for="item in filteredAndPagedFeatures.items"
            :key="item.feat._uiId || item.originalIdx"
            @mouseenter="highlightFeatureOnMap(item.originalIdx, true)"
            @mouseleave="highlightFeatureOnMap(item.originalIdx, false)"
            @click="toggleSelectPolygon(item.feat._uiId); flyToFeature(item.originalIdx)"
            class="p-2.5 bg-slate-50 border rounded-xl space-y-1 transition-all text-xs cursor-pointer select-none"
            :class="[
              selectedPolyUiIds.has(item.feat._uiId)
                ? 'bg-cyan-50/90 border-cyan-400 shadow-xs ring-2 ring-cyan-400/40 text-cyan-950'
                : (clickedFeatureIdx === item.originalIdx ? 'ring-2 ring-indigo-500 border-indigo-400 bg-indigo-50/40' : 'border-slate-200 hover:border-slate-300 hover:bg-white')
            ]"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <input
                  type="checkbox"
                  :checked="selectedPolyUiIds.has(item.feat._uiId)"
                  @click.stop="toggleSelectPolygon(item.feat._uiId)"
                  class="w-4 h-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500 cursor-pointer shrink-0"
                />
                <div
                  class="w-3 h-3 rounded-sm border border-slate-300 shrink-0"
                  :style="{ backgroundColor: item.feat.properties?.color || '#9CA3AF' }"
                ></div>
                <span class="font-bold text-slate-800 truncate max-w-[140px]">{{ item.feat.properties?.class_name || 'Belum Teridentifikasi' }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span v-if="selectedPolyUiIds.has(item.feat._uiId)" class="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" title="Terpilih di peta"></span>
                <span class="text-[10px] text-slate-400 font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">#{{ item.originalIdx + 1 }}</span>
              </div>
            </div>

            <div class="flex items-center justify-between text-[10px] text-slate-500 pt-0.5 pl-6">
              <span class="font-mono">Luas: ~{{ Math.round((item.feat.properties?.area_sqm || 10000) / 10000) }} Ha</span>
              <span v-if="item.feat.properties?.class_id === 0" class="text-amber-600 font-bold">⚠️ Belum di-assign</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Modal: Salin Poligon dari Tahun Lain -->
    <div
      v-if="showCopyModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div class="flex items-center gap-2 text-indigo-700">
            <Copy :size="18" />
            <h3 class="text-sm font-bold text-slate-800">Salin Poligon dari Tahun Lain</h3>
          </div>
          <button
            @click="showCopyModal = false"
            class="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="p-5 space-y-4 text-xs">
          <p class="text-slate-600 leading-relaxed">
            Fitur ini memungkinkan Anda menduplikasi seluruh poligon anotasi dari tahun sebelumnya (misal <b>2017</b> atau <b>2021</b>) ke grid aktif saat ini (<b>{{ tasksStore.currentTask?.grid_code }} - {{ currentYear }}</b>).
          </p>

          <div class="space-y-1.5">
            <label class="font-bold text-slate-700 block">Pilih Grid Sumber (Tahun Baseline):</label>
            <select
              v-model="selectedSourceTaskId"
              class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs font-bold text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              <option v-for="t in candidateSourceTasks" :key="t.id" :value="t.id">
                {{ t.grid_code }} (Tahun {{ t.year }}) - {{ t.annotation_count }} Poligon
              </option>
            </select>
            <p v-if="candidateSourceTasks.length === 0" class="text-[11px] text-amber-600 font-semibold pt-1">
              Belum ditemukan grid lain yang memiliki poligon anotasi tersimpan.
            </p>
          </div>

          <div class="p-3 bg-amber-50 rounded-xl border border-amber-200/80 text-[11px] text-amber-900 leading-tight">
            <b>Catatan:</b> Poligon yang disalin dapat langsung Anda edit, potong, atau diubah jenis tutupan lahannya menyesuaikan citra tahun {{ currentYear }}.
          </div>
        </div>

        <div class="px-5 py-3.5 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
          <button
            @click="showCopyModal = false"
            class="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 rounded-xl hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            Batal
          </button>
          <button
            @click="handleCopyAnnotations"
            :disabled="!selectedSourceTaskId || copyingAnnotations"
            class="px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl transition-all shadow-md shadow-indigo-600/20 flex items-center gap-1.5 cursor-pointer"
          >
            <Copy :size="14" />
            <span>{{ copyingAnnotations ? 'Menyalin...' : 'Terapkan & Salin' }}</span>
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
                Grid: {{ tasksStore.currentTask?.grid_code || 'Belum Dipilih' }} (Pilih aksi yang ingin diterapkan)
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
              <p class="text-[11px] text-slate-500 font-mono">Grid {{ tasksStore.currentTask?.grid_code }}</p>
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

    <!-- MODAL 5: Tambah Catatan Evaluasi Per Pin (Bebas di Lokasi Mana Saja pada Peta) -->
    <div
      v-if="showEvaluationPinModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in"
    >
      <div class="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl border border-slate-100 space-y-4 animate-in zoom-in-95 max-h-[90vh] overflow-y-auto">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-slate-100 pb-3.5">
          <div class="flex items-center gap-2.5">
            <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 to-rose-500 text-white flex items-center justify-center shadow-md">
              <MapPin :size="20" />
            </div>
            <div>
              <h3 class="font-extrabold text-slate-900 text-sm tracking-tight">Tambah Pin Catatan Evaluasi</h3>
              <p class="text-[11px] text-slate-500">Pin ditempatkan di titik koordinat yang Anda klik (bebas tanpa harus poligon)</p>
            </div>
          </div>
          <button
            @click="showEvaluationPinModal = false"
            class="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Lokasi & Konteks -->
        <div class="bg-slate-50 p-3 rounded-2xl border border-slate-200 text-slate-600 space-y-1.5 text-xs font-mono">
          <div class="flex items-center justify-between">
            <span class="text-slate-500 font-sans font-medium">📍 Koordinat Titik:</span>
            <span class="font-bold text-slate-900 bg-white px-2 py-0.5 rounded-lg border border-slate-200">
              {{ evaluationPinModalData.lat }}, {{ evaluationPinModalData.lon }}
            </span>
          </div>
          <div class="flex items-center justify-between font-sans">
            <span class="text-slate-500 font-medium">Konteks Lokasi:</span>
            <span v-if="evaluationPinModalData.annotation_id" class="font-bold text-indigo-700 text-xs">
              Di atas poligon: {{ evaluationPinModalData.class_name || 'Anotasi' }} (#{{ evaluationPinModalData.annotation_id }})
            </span>
            <span v-else class="text-emerald-700 font-medium text-xs">
              Area Bebas (Tidak terikat poligon)
            </span>
          </div>
        </div>

        <!-- Pilihan Kategori Masalah / Evaluasi -->
        <div class="space-y-1.5 text-xs">
          <label class="font-bold text-slate-700 block">Kategori Evaluasi / Isu:</label>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-[11px]">
            <button
              v-for="cat in [
                { id: 'Batas Kurang Pas', label: 'Batas Kurang Pas', icon: '📏' },
                { id: 'Salah Label Kelas', label: 'Salah Label Kelas', icon: '🏷️' },
                { id: 'Objek Terlewat', label: 'Objek Terlewat', icon: '🔍' },
                { id: 'Celah / Overlap', label: 'Celah / Overlap', icon: '⚡' },
                { id: 'Kerapian Poligon', label: 'Kerapian Poligon', icon: '✨' },
                { id: 'Catatan Umum', label: 'Catatan Umum', icon: '💬' }
              ]"
              :key="cat.id"
              type="button"
              @click="evaluationPinModalData.category = cat.id"
              class="p-2 rounded-xl border text-left flex items-center gap-1.5 font-bold transition-all cursor-pointer truncate"
              :class="evaluationPinModalData.category === cat.id
                ? 'bg-amber-50 border-amber-400 text-amber-900 ring-2 ring-amber-400/30'
                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'"
            >
              <span>{{ cat.icon }}</span>
              <span class="truncate">{{ cat.label }}</span>
            </button>
          </div>
        </div>

        <!-- Input Textarea Catatan Review -->
        <div class="space-y-1.5 text-xs">
          <div class="flex items-center justify-between">
            <label class="font-bold text-slate-700">Isi Catatan / Instruksi Review:</label>
            <span class="text-[10px] text-slate-400">Wajib diisi</span>
          </div>
          <textarea
            v-model="evaluationPinModalData.note"
            rows="3"
            placeholder="Tuliskan catatan evaluasi, bagian mana yang perlu diperbaiki atau dicek kembali..."
            class="w-full p-3 bg-slate-50 border border-slate-200 rounded-2xl focus:bg-white focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 focus:outline-none text-xs text-slate-900 font-medium placeholder:text-slate-400 leading-relaxed"
          ></textarea>
        </div>

        <!-- Template Cepat / Contoh Catatan -->
        <div class="space-y-1 text-xs">
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Template Cepat:</span>
          <div class="flex flex-wrap gap-1 text-[10px]">
            <button
              type="button"
              @click="evaluationPinModalData.note = 'Batas poligon di titik ini masih kurang pas dengan citra satelit, mohon disesuaikan kembali.'; evaluationPinModalData.category = 'Batas Kurang Pas'"
              class="px-2.5 py-1 bg-slate-100 hover:bg-amber-50 hover:text-amber-800 rounded-lg border border-slate-200 text-slate-600 transition-colors cursor-pointer"
            >
              Batas kurang pas
            </button>
            <button
              type="button"
              @click="evaluationPinModalData.note = 'Interpretasi tutupan lahan di area ini kurang tepat, mohon verifikasi kembali kelasnya.'; evaluationPinModalData.category = 'Salah Label Kelas'"
              class="px-2.5 py-1 bg-slate-100 hover:bg-amber-50 hover:text-amber-800 rounded-lg border border-slate-200 text-slate-600 transition-colors cursor-pointer"
            >
              Verifikasi kelas
            </button>
            <button
              type="button"
              @click="evaluationPinModalData.note = 'Terdapat objek tutupan lahan di sekitar titik ini yang belum terdigitasi.'; evaluationPinModalData.category = 'Objek Terlewat'"
              class="px-2.5 py-1 bg-slate-100 hover:bg-amber-50 hover:text-amber-800 rounded-lg border border-slate-200 text-slate-600 transition-colors cursor-pointer"
            >
              Objek terlewat
            </button>
            <button
              type="button"
              @click="evaluationPinModalData.note = 'Terdapat celah kosong / tumpang tindih poligon di titik ini, mohon dirapikan topologinya.'; evaluationPinModalData.category = 'Celah / Overlap'"
              class="px-2.5 py-1 bg-slate-100 hover:bg-amber-50 hover:text-amber-800 rounded-lg border border-slate-200 text-slate-600 transition-colors cursor-pointer"
            >
              Celah / overlap
            </button>
          </div>
        </div>

        <!-- Tombol Footer -->
        <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
          <button
            type="button"
            @click="showEvaluationPinModal = false"
            class="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            Batal
          </button>
          <button
            type="button"
            @click="saveNewEvaluationPin"
            :disabled="submittingEvaluationPin || !evaluationPinModalData.note.trim()"
            class="px-5 py-2.5 bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-700 hover:to-rose-700 text-white rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <RotateCw v-if="submittingEvaluationPin" :size="14" class="animate-spin" />
            <MapPin v-else :size="14" />
            <span>{{ submittingEvaluationPin ? 'Menyimpan...' : 'Simpan Pin Catatan' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 6: Riwayat Versi & Snapshot Pemulihan (Rollback) -->
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
              <p class="text-[11px] text-slate-500 font-mono">{{ tasksStore.currentTask?.grid_code }} • Cadangan Snapshot</p>
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
            <p class="text-[10px] text-slate-400">Snapshot dibuat otomatis setiap kali Anda menekan tombol "Simpan Draf" atau aksi perbaikan QC.</p>
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

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TOPOLOGY CORRECTION MODAL (Clean Light Theme, No AI Slop)          -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <div
      v-if="showTopologySurgeryModal"
      class="fixed inset-0 z-[9999] bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-2 sm:p-5 animate-in fade-in duration-150"
    >
      <div class="w-full max-w-6xl h-[92vh] max-h-[900px] bg-white border border-slate-200 rounded-xl shadow-2xl flex flex-col overflow-hidden text-slate-800">
        
        <!-- Modal Header -->
        <div class="px-5 py-3 bg-white border-b border-slate-200 flex items-center justify-between gap-3 shrink-0">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 shrink-0">
              <Wrench :size="16" />
            </div>
            <div class="min-w-0">
              <span class="font-bold text-sm text-slate-900 tracking-tight">Perbaikan Topologi</span>
              <p class="text-xs text-slate-500 truncate hidden sm:block">
                Periksa dan selesaikan tumpang tindih serta kesalahan batas poligon
              </p>
            </div>
          </div>

          <!-- Stepper Navigator -->
          <div class="flex items-center gap-2 shrink-0">
            <div class="flex items-center bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 gap-1.5 text-xs text-slate-600">
              <span class="text-[11px] hidden sm:inline">Masalah</span>
              <span class="font-mono font-bold text-slate-900">
                {{ (surgeryErrorIndex + 1) }} / {{ topologyResult?.errors?.length || 0 }}
              </span>
            </div>

            <div class="flex items-center gap-1">
              <button
                @click="prevSurgeryError"
                :disabled="surgeryIsProcessing || !topologyResult?.errors?.length"
                class="px-2.5 py-1 bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors cursor-pointer border border-slate-200 shadow-2xs"
                title="Lihat masalah sebelumnya"
              >
                <ChevronLeft :size="14" />
                <span class="hidden md:inline">Sebelumnya</span>
              </button>
              <button
                @click="nextSurgeryError"
                :disabled="surgeryIsProcessing || !topologyResult?.errors?.length"
                class="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-lg text-xs font-medium flex items-center gap-1 transition-colors cursor-pointer shadow-xs"
                title="Lihat masalah berikutnya"
              >
                <span class="hidden md:inline">Selanjutnya</span>
                <ChevronRight :size="14" />
              </button>
            </div>

            <button
              @click="closeTopologySurgeryModal"
              class="ml-1 p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg cursor-pointer transition-colors"
              title="Tutup"
            >
              <X :size="18" />
            </button>
          </div>
        </div>

        <!-- Body: Split View (Map Canvas + Control Panel) -->
        <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 bg-slate-100">
          
          <!-- LEFT / CENTER: Map Canvas (col-span-8) -->
          <div class="lg:col-span-8 h-full relative border-r border-slate-200 overflow-hidden flex flex-col bg-slate-100">
            
            <div
              id="topology-surgery-map-canvas"
              :class="{ 'delete-vertex-active': surgeryVertexModeActive && surgeryVertexAction === 'delete' }"
              class="w-full h-full min-h-[480px] flex-1 z-0 bg-slate-100"
            ></div>

            <!-- In-place loading spinner during surgery / revalidation -->
            <div
              v-if="surgeryIsProcessing || topologyLoading"
              class="absolute inset-0 z-30 bg-white/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2.5 transition-opacity"
            >
              <div class="w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></div>
              <div class="text-center">
                <p class="text-xs font-semibold text-slate-900">Menyinkronkan Perbaikan Topologi...</p>
                <p class="text-[11px] text-slate-500 mt-0.5">Memperbarui geometri dan memvalidasi ulang</p>
              </div>
            </div>

            <!-- Floating Overlay: Zoom Badge & Reset -->
            <div class="absolute top-3 left-3 z-20 flex items-center gap-2">
              <div class="bg-white/95 backdrop-blur-md border border-slate-200 px-2.5 py-1 rounded-lg text-xs font-mono font-medium text-slate-700 shadow-sm flex items-center gap-1.5">
                <Focus :size="12" class="text-slate-500" />
                <span>Zoom: {{ surgeryCurrentZoom }}x</span>
              </div>
              <button
                @click="resetSurgeryZoom"
                class="bg-white/95 hover:bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg text-xs font-medium text-slate-700 shadow-sm cursor-pointer transition-colors flex items-center gap-1"
                title="Reset zoom kembali pas ke batas poligon"
              >
                <RotateCcw :size="11" />
                <span>Reset</span>
              </button>
            </div>

            <!-- Floating Overlay: Vertex Edit Toolbar -->
            <div class="absolute bottom-3 left-3 z-20 flex items-center gap-2 flex-wrap max-w-[95%]">
              <div class="flex items-center bg-white/95 backdrop-blur-md border border-slate-200 rounded-lg p-1 gap-1 shadow-md">
                <!-- Toggle Edit Simpul Button -->
                <button
                  @click="toggleSurgeryVertexEdit"
                  class="px-2.5 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 cursor-pointer"
                  :class="surgeryVertexModeActive
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'hover:bg-slate-100 text-slate-700'"
                >
                  <Edit3 :size="13" />
                  <span>{{ surgeryVertexModeActive ? 'Edit Simpul Aktif' : 'Edit Simpul' }}</span>
                </button>

                <!-- Shift helper button for multi-select -->
                <template v-if="surgeryVertexModeActive">
                  <div class="h-4 w-px bg-slate-200 mx-0.5"></div>
                  <button
                    @click="toggleSurgeryMultiSelect"
                    class="px-2 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1 cursor-pointer"
                    :class="surgeryMultiSelectActive
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100'"
                    title="Tahan Shift di keyboard atau aktifkan tombol ini untuk memilih beberapa titik"
                  >
                    <Check :size="12" />
                    <span>{{ surgeryMultiSelectActive ? 'Shift Aktif' : 'Tahan Shift' }}</span>
                  </button>
                </template>
              </div>

              <!-- When 1 or more vertices are selected -->
              <div
                v-if="surgeryVertexModeActive && selectedSurgeryVertices.length > 0"
                class="flex items-center bg-blue-50 border border-blue-200 rounded-lg p-1 gap-1.5 shadow-md animate-in fade-in duration-150"
              >
                <div class="px-2 py-0.5 text-xs font-mono font-semibold text-blue-900 flex items-center gap-1.5">
                  <span class="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                  <span>{{ selectedSurgeryVertices.length }} Terpilih</span>
                </div>

                <button
                  @click="deleteSelectedSurgeryVertices"
                  class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-md text-xs font-medium transition-colors shadow-2xs flex items-center gap-1 cursor-pointer"
                  title="Hapus titik simpul yang terpilih (Shortcut: Delete / Backspace)"
                >
                  <Trash2 :size="12" />
                  <span>Hapus [Del]</span>
                </button>

                <button
                  @click="clearSurgeryVertexSelection"
                  class="p-1 text-slate-400 hover:text-slate-700 rounded-md cursor-pointer transition-colors"
                  title="Batal pilihan titik (Esc)"
                >
                  <X :size="13" />
                </button>
              </div>

              <!-- Save Changes Button -->
              <button
                v-if="surgeryVertexModeActive && hasSurgeryVertexEdits"
                @click="saveSurgeryVertexEdits"
                :disabled="surgeryIsProcessing"
                class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-medium transition-colors shadow-sm flex items-center gap-1 cursor-pointer"
              >
                <Save :size="13" />
                <span>Simpan Titik</span>
              </button>

              <!-- Cancel Changes Button -->
              <button
                v-if="surgeryVertexModeActive && hasSurgeryVertexEdits"
                @click="cancelSurgeryVertexEdits"
                :disabled="surgeryIsProcessing"
                class="px-2 py-1 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-md text-xs font-medium transition-colors shadow-2xs flex items-center gap-1 cursor-pointer"
                title="Batal dan kembalikan titik simpul semula"
              >
                <RotateCcw :size="12" />
                <span>Batal</span>
              </button>
            </div>

            <!-- Legend Overlay Bottom Right -->
            <div class="absolute bottom-3 right-3 z-20 bg-white/95 backdrop-blur-md border border-slate-200 px-3 py-2 rounded-lg text-xs text-slate-700 shadow-sm space-y-1 hidden sm:block">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-xs border border-amber-400 bg-amber-200"></span>
                <span class="font-medium text-slate-800">Poligon A</span>
              </div>
              <div v-if="surgeryCurrentError?.annotation_ids?.length >= 2" class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-xs border border-cyan-400 bg-cyan-200"></span>
                <span class="font-medium text-slate-800">Poligon B</span>
              </div>
            </div>

          </div>

          <!-- RIGHT: Control Panel (col-span-4) -->
          <div class="lg:col-span-4 h-full bg-slate-50/70 overflow-y-auto p-4 flex flex-col justify-between gap-4 border-t lg:border-t-0 border-slate-200">
            
            <div class="space-y-3.5">
              <!-- Current Error Diagnostic Card -->
              <div class="bg-white border border-slate-200 rounded-xl p-3.5 space-y-2.5 shadow-2xs">
                <div class="flex items-center justify-between">
                  <span
                    class="text-[11px] font-mono font-bold uppercase px-2 py-0.5 rounded-md border tracking-wider"
                    :class="surgeryCurrentError?.type === 'OVERLAP'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : surgeryCurrentError?.type === 'SELF_INTERSECTION'
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-indigo-50 text-indigo-700 border-indigo-200'"
                  >
                    {{ surgeryCurrentError?.type || 'MASALAH GEOMETRI' }}
                  </span>
                  <span v-if="surgeryCurrentError?.area_sqm" class="text-xs font-mono text-slate-500">
                    Luas: <b class="text-slate-800">{{ (surgeryCurrentError.area_sqm).toFixed(2) }} m²</b>
                  </span>
                </div>

                <div>
                  <h4 class="text-xs font-semibold text-slate-800">Keterangan:</h4>
                  <p class="text-xs text-slate-600 mt-0.5 leading-relaxed">
                    {{ surgeryCurrentError?.message || 'Geometri poligon memerlukan perbaikan topologi.' }}
                  </p>
                </div>

                <!-- Involved Polygons Specs -->
                <div class="pt-2 border-t border-slate-100 space-y-1.5 text-xs">
                  <div v-for="(poly, pIdx) in surgeryInvolvedPolygons" :key="poly.id" class="p-2 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ backgroundColor: poly.color || (pIdx === 0 ? '#F59E0B' : '#06B6D4') }"></span>
                      <div class="truncate">
                        <span class="font-mono font-bold text-slate-900 text-xs">#{{ poly.id }}</span>
                        <span class="text-slate-500 text-[11px] ml-1.5">({{ poly.class_name }})</span>
                      </div>
                    </div>
                    <span class="text-[11px] font-mono text-slate-600 shrink-0">
                      {{ poly.area_sqm ? `${poly.area_sqm.toFixed(1)} m²` : '' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Available Surgery Operations -->
              <div class="space-y-2">
                <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Layers :size="13" />
                  <span>Tindakan Koreksi</span>
                </span>

                <!-- Overlap Actions -->
                <template v-if="surgeryCurrentError?.type === 'OVERLAP' && surgeryInvolvedPolygons.length >= 2">
                  <button
                    @click="executeSurgeryClip('clip_b_by_a')"
                    :disabled="surgeryIsProcessing"
                    class="w-full p-3 rounded-xl bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 text-left transition-colors cursor-pointer group disabled:opacity-50 shadow-2xs"
                  >
                    <div class="flex items-center justify-between text-xs font-semibold text-slate-900">
                      <span class="flex items-center gap-1.5">
                        <Scissors :size="14" class="text-amber-600" />
                        <span>Potong Poligon B (#{{ surgeryInvolvedPolygons[1]?.id }})</span>
                      </span>
                      <span class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">Pertahankan A</span>
                    </div>
                    <p class="text-[11px] text-slate-500 mt-1 leading-normal">
                      Pangkas bagian tumpang tindih dari Poligon B sehingga bentuk Poligon A (#{{ surgeryInvolvedPolygons[0]?.id }}) tetap utuh.
                    </p>
                  </button>

                  <button
                    @click="executeSurgeryClip('clip_a_by_b')"
                    :disabled="surgeryIsProcessing"
                    class="w-full p-3 rounded-xl bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 text-left transition-colors cursor-pointer group disabled:opacity-50 shadow-2xs"
                  >
                    <div class="flex items-center justify-between text-xs font-semibold text-slate-900">
                      <span class="flex items-center gap-1.5">
                        <Scissors :size="14" class="text-cyan-600" />
                        <span>Potong Poligon A (#{{ surgeryInvolvedPolygons[0]?.id }})</span>
                      </span>
                      <span class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">Pertahankan B</span>
                    </div>
                    <p class="text-[11px] text-slate-500 mt-1 leading-normal">
                      Pangkas bagian tumpang tindih dari Poligon A sehingga bentuk Poligon B (#{{ surgeryInvolvedPolygons[1]?.id }}) tetap utuh.
                    </p>
                  </button>

                  <button
                    @click="executeSurgeryMerge"
                    :disabled="surgeryIsProcessing"
                    class="w-full p-3 rounded-xl bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 text-left transition-colors cursor-pointer group disabled:opacity-50 shadow-2xs"
                  >
                    <div class="flex items-center justify-between text-xs font-semibold text-slate-900">
                      <span class="flex items-center gap-1.5">
                        <Combine :size="14" class="text-indigo-600" />
                        <span>Gabung Kedua Poligon (Union)</span>
                      </span>
                      <span class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">Merge</span>
                    </div>
                    <p class="text-[11px] text-slate-500 mt-1 leading-normal">
                      Satukan Poligon #{{ surgeryInvolvedPolygons[0]?.id }} dan #{{ surgeryInvolvedPolygons[1]?.id }} menjadi satu bidang utuh.
                    </p>
                  </button>
                </template>

                <!-- Self-Intersection or Invalid Geometry -->
                <template v-else-if="surgeryCurrentError?.type === 'SELF_INTERSECTION' || surgeryCurrentError?.type === 'INVALID_GEOM'">
                  <button
                    @click="executeSurgeryHeal"
                    :disabled="surgeryIsProcessing"
                    class="w-full p-3 rounded-xl bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 text-left transition-colors cursor-pointer group disabled:opacity-50 shadow-2xs"
                  >
                    <div class="flex items-center justify-between text-xs font-semibold text-slate-900">
                      <span class="flex items-center gap-1.5">
                        <Wrench :size="14" class="text-emerald-600" />
                        <span>Perbaiki Geometri (Buffer 0)</span>
                      </span>
                      <span class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">Koreksi</span>
                    </div>
                    <p class="text-[11px] text-slate-500 mt-1 leading-normal">
                      Urai simpul geometri yang melilit secara otomatis dengan topologi buffer standar.
                    </p>
                  </button>
                </template>

                <!-- Vertex Edit Section -->
                <div class="p-3.5 rounded-xl bg-white border border-slate-200 space-y-3 shadow-2xs">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <div class="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-200">
                        <Edit3 :size="14" />
                      </div>
                      <span class="text-xs font-bold text-slate-900">Edit Titik Simpul</span>
                    </div>
                    <span
                      class="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md"
                      :class="surgeryVertexModeActive
                        ? (selectedSurgeryVertices.length > 0 ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200')
                        : 'bg-slate-100 text-slate-600 border border-slate-200'"
                    >
                      {{ surgeryVertexModeActive ? (selectedSurgeryVertices.length > 0 ? `${selectedSurgeryVertices.length} TITIK TERPILIH` : 'AKTIF') : 'NONAKTIF' }}
                    </span>
                  </div>

                  <!-- Quick Toggle if not active -->
                  <div v-if="!surgeryVertexModeActive" class="pt-0.5">
                    <button
                      @click="toggleSurgeryVertexEdit"
                      class="w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs flex items-center justify-center gap-1.5 shadow-xs transition-colors cursor-pointer"
                    >
                      <Edit3 :size="13" />
                      <span>Aktifkan Edit Titik Simpul</span>
                    </button>
                  </div>

                  <!-- Multi-Select Action Banner when vertices are selected -->
                  <div
                    v-if="surgeryVertexModeActive && selectedSurgeryVertices.length > 0"
                    class="p-2.5 rounded-lg bg-blue-50 border border-blue-200 space-y-2 animate-in fade-in duration-150"
                  >
                    <div class="flex items-center justify-between text-xs font-semibold text-blue-900">
                      <span class="flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                        <span>{{ selectedSurgeryVertices.length }} Titik Terpilih</span>
                      </span>
                      <button
                        @click="clearSurgeryVertexSelection"
                        class="text-[11px] text-blue-600 hover:text-blue-800 underline cursor-pointer"
                      >
                        Batal (Esc)
                      </button>
                    </div>

                    <p class="text-[11px] text-blue-800/80 leading-tight">
                      Geser salah satu titik untuk memindahkan bersamaan, atau hapus:
                    </p>

                    <button
                      @click="deleteSelectedSurgeryVertices"
                      class="w-full py-1.5 px-3 bg-rose-600 hover:bg-rose-700 text-white rounded-md text-xs font-medium flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer transition-colors"
                    >
                      <Trash2 :size="13" />
                      <span>Hapus {{ selectedSurgeryVertices.length }} Titik [Del]</span>
                    </button>
                  </div>

                  <!-- Guide -->
                  <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 space-y-1.5">
                    <div class="flex items-center justify-between text-[11px] font-semibold text-slate-800">
                      <span class="flex items-center gap-1">
                        <Info :size="12" />
                        <span>Panduan</span>
                      </span>
                      <button
                        v-if="surgeryVertexModeActive"
                        @click="toggleSurgeryMultiSelect"
                        class="px-2 py-0.5 rounded text-[10px] font-medium cursor-pointer transition-colors border"
                        :class="surgeryMultiSelectActive
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'"
                      >
                        {{ surgeryMultiSelectActive ? '✓ Shift Aktif' : 'Tahan Shift' }}
                      </button>
                    </div>

                    <ul class="space-y-1 text-[11px] text-slate-600 leading-snug">
                      <li class="flex items-start gap-1.5">
                        <span class="text-slate-400 font-bold">•</span>
                        <span><b>Pilih:</b> Klik titik sudut pada poligon.</span>
                      </li>
                      <li class="flex items-start gap-1.5">
                        <span class="text-slate-400 font-bold">•</span>
                        <span><b>Pilih Banyak:</b> Tahan <code>Shift</code> lalu klik titik lain.</span>
                      </li>
                      <li class="flex items-start gap-1.5">
                        <span class="text-slate-400 font-bold">•</span>
                        <span><b>Geser:</b> Tarik simpul untuk memindahkan posisi.</span>
                      </li>
                      <li class="flex items-start gap-1.5">
                        <span class="text-slate-400 font-bold">•</span>
                        <span><b>Hapus:</b> Tekan tombol <code>Delete</code> di keyboard.</span>
                      </li>
                    </ul>
                  </div>

                  <!-- In-card Save / Cancel Actions -->
                  <div v-if="surgeryVertexModeActive && hasSurgeryVertexEdits" class="flex items-center gap-2 pt-1">
                    <button
                      @click="saveSurgeryVertexEdits"
                      :disabled="surgeryIsProcessing"
                      class="flex-1 py-1.5 px-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer transition-colors"
                    >
                      <Save :size="13" />
                      <span>Simpan Titik</span>
                    </button>
                    <button
                      @click="cancelSurgeryVertexEdits"
                      :disabled="surgeryIsProcessing"
                      class="py-1.5 px-3 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-md text-xs font-medium flex items-center justify-center gap-1 cursor-pointer transition-colors shadow-2xs"
                      title="Kembalikan geometri sebelum diedit"
                    >
                      <RotateCcw :size="12" />
                      <span>Batal</span>
                    </button>
                  </div>
                </div>

                <!-- Delete Polygon Option -->
                <div v-if="surgeryInvolvedPolygons.length" class="pt-1 border-t border-slate-200 flex items-center gap-2">
                  <button
                    v-for="poly in surgeryInvolvedPolygons"
                    :key="'del-' + poly.id"
                    @click="executeSurgeryDelete(poly.id)"
                    :disabled="surgeryIsProcessing"
                    class="flex-1 py-1.5 px-2 bg-white hover:bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-[11px] font-medium flex items-center justify-center gap-1 transition-colors cursor-pointer disabled:opacity-50 shadow-2xs"
                    :title="`Hapus Poligon #${poly.id} dari database`"
                  >
                    <Trash2 :size="12" />
                    <span>Hapus #{{ poly.id }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Footer Actions -->
            <div class="pt-3 border-t border-slate-200 space-y-2.5">
              <div class="flex items-center justify-between text-xs text-slate-600 px-1">
                <span>Lanjut otomatis ke masalah berikutnya</span>
                <input
                  v-model="surgeryAutoAdvance"
                  type="checkbox"
                  class="w-4 h-4 rounded text-slate-900 border-slate-300 focus:ring-slate-900 cursor-pointer"
                />
              </div>

              <div class="flex items-center gap-2">
                <button
                  @click="handleAutoHealRemaining"
                  :disabled="surgeryIsProcessing"
                  class="flex-1 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-medium flex items-center justify-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50 shadow-2xs"
                >
                  <Wrench :size="13" />
                  <span>Koreksi Otomatis Sisa</span>
                </button>

                <button
                  @click="closeTopologySurgeryModal"
                  class="flex-1 py-2 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer shadow-xs"
                >
                  <CheckCircle2 :size="14" />
                  <span>Selesai & Tutup</span>
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
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import L from 'leaflet'
import '@geoman-io/leaflet-geoman-free'
import {
  Grid,
  AlertTriangle,
  Satellite,
  Crosshair,
  PieChart,
  Save,
  Send,
  CheckCircle2,
  Palette,
  Shapes,
  Flame,
  Sprout,
  Globe2,
  Globe,
  Map,
  RotateCw,
  TrendingUp,
  Copy,
  Check,
  X,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Wrench,
  ShieldCheck,
  Scissors,
  Layers,
  PenTool,
  Spline,
  LassoSelect,
  Combine,
  Edit3,
  Trash2,
  Undo2,
  Redo2,
  MousePointer,
  Eye,
  EyeOff,
  Compass,
  SlidersHorizontal,
  Sun,
  Contrast,
  Sliders,
  Sparkles,
  RefreshCcw,
  MapPin,
  Focus,
  RotateCcw,
  Wand2,
  Tag,
  History,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  Move,
  Info,
  Magnet,
  Search,
  Wifi,
  WifiOff,
  Trophy,
  Split
} from 'lucide-vue-next'
import * as turf from '@turf/turf'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import { useAnnotationsStore } from '../stores/annotations'
import api from '../services/api'
import { imageMapLayer } from 'esri-leaflet'
import { saveTaskDraft, getTaskDraft, clearTaskDraft } from '../services/offlineStorage'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const tasksStore = useTasksStore()
const annotationsStore = useAnnotationsStore()

const selectedTaskId = ref(null)
const currentLayer = ref('local_s2_rgb')
const currentYear = ref(2025)
const availableRasterYears = ref([2025, 2022])
const polygonOpacity = ref(0.6)
const isToolboxCollapsed = ref(false)
const rightTab = ref('classes') // 'classes' | 'polygons'
const isSnappingEnabled = ref(true)
const polyListPage = ref(1)
const polyListPageSize = 40
const polySearchQuery = ref('')

// ─── OFFLINE DRAFT & NETWORK RESILIENCE (POIN 1) ─────────────
const isNetworkOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const localDraftStatus = ref(null) // { updatedAt, polygonCount }
const showDraftRestorePrompt = ref(false)
const pendingDraftToRestore = ref(null)

// ─── TEMPORAL COMPARISON SWIPE MAP (POIN 2) ─────────────────
const isSwipeMode = ref(false)
const swipeLeftYear = ref(2022)
const swipeRightYear = ref(2025)
const swipePosition = ref(50) // percentage 0 - 100
const isDraggingSwipe = ref(false)

// ─── AI-ASSISTED DIGITIZING (POIN 3) ────────────────────────
const isAiSegmenting = ref(false)
const aiWandTolerance = ref(28.0)
const aiSegmentCandidate = ref(null)

// ─── EDGE-MATCHING & NEIGHBOR SNAPPING (POIN 4) ─────────────
const isNeighborSnappingEnabled = ref(true)

// ─── MAPPER LEADERBOARD (POIN 6) ────────────────────────────
const showLeaderboardModal = ref(false)
const leaderboardLoading = ref(false)
const leaderboardList = ref([])

const filteredAndPagedFeatures = computed(() => {
  let list = (features.value || []).map((f, i) => ({ feat: f, originalIdx: i }))
  if (polySearchQuery.value && polySearchQuery.value.trim()) {
    const q = polySearchQuery.value.toLowerCase().trim()
    list = list.filter(item => {
      const cName = (item.feat.properties?.class_name || '').toLowerCase()
      const idxStr = String(item.originalIdx + 1)
      return cName.includes(q) || idxStr === q || `#${idxStr}` === q
    })
  }
  const total = list.length
  const totalPages = Math.max(1, Math.ceil(total / polyListPageSize))
  const page = Math.min(Math.max(1, polyListPage.value), totalPages)
  const start = (page - 1) * polyListPageSize
  const items = list.slice(start, start + polyListPageSize)
  return {
    items,
    total,
    totalPages
  }
})

// ─── IMAGERY ENHANCEMENT & SPECTRAL CONTROLS ─────────────
const showImageryPanel = ref(false)
const imageryActiveTab = ref('layers') // 'layers' | 'contrast'
const imagerySettings = ref({
  brightness: 100, // 50% - 200%
  contrast: 100,   // 50% - 200%
  gamma: 1.0,      // 0.5 - 2.5
  saturation: 100, // 0% - 250%
  opacity: 100     // 20% - 100%
})

const currentLayerBadge = computed(() => {
  const match = layerOptions.find(l => l.id === currentLayer.value)
  return match ? match.name.split(' ')[0] : 'S2 RGB'
})

// ─── FLEXIBLE DRAGGABLE SIDEBARS ─────────────────────────
const leftSidebarWidth = ref(280)
const rightSidebarWidth = ref(320)

const startResizeLeft = (e) => {
  e.preventDefault()
  const startX = e.clientX
  const startW = leftSidebarWidth.value
  const onMouseMove = (moveEvent) => {
    const newW = Math.max(220, Math.min(480, startW + (moveEvent.clientX - startX)))
    leftSidebarWidth.value = newW
    if (map) map.invalidateSize()
  }
  const onMouseUp = () => {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    if (map) map.invalidateSize()
  }
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

const startResizeRight = (e) => {
  e.preventDefault()
  const startX = e.clientX
  const startW = rightSidebarWidth.value
  const onMouseMove = (moveEvent) => {
    const newW = Math.max(240, Math.min(520, startW - (moveEvent.clientX - startX)))
    rightSidebarWidth.value = newW
    if (map) map.invalidateSize()
  }
  const onMouseUp = () => {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    if (map) map.invalidateSize()
  }
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}
const toastMessage = ref('')
const showCopyModal = ref(false)
const selectedSourceTaskId = ref(null)
const copyingAnnotations = ref(false)
const taskSiblings = ref([])
const showSmartCopyBanner = ref(true)
const showGuide = ref(false)
const clickedFeatureIdx = ref(null)
const topologyResult = ref(null)
const topologyLoading = ref(false)
const currentTopologyErrorIndex = ref(0)
const activeTopologyError = ref(null)

// Active GIS Digitize Mode
const activeTool = ref(null) // null | 'split_line' | 'split_poly' | 'draw_poly' | 'merge' | 'edit' | 'delete'
const selectedForMerge = ref([]) // array of selected feature objects
const mergeLoading = ref(false)
const mergeTargetClassId = ref(null)

// Dedicated Topology Surgery Studio Modal (Unlimited Zoom & Focused Workbench)
const showTopologySurgeryModal = ref(false)
const surgeryErrorIndex = ref(0)
const surgeryCurrentZoom = ref(20)
const surgeryVertexModeActive = ref(false)
const surgeryVertexAction = ref('drag') // 'drag' | 'delete'
const hasSurgeryVertexEdits = ref(false)
const surgeryAutoAdvance = ref(true)
const surgeryIsProcessing = ref(false)
const surgeryInvolvedPolygons = ref([])
const selectedSurgeryVertices = ref([]) // array of { marker, layer, latlng }
const surgeryMultiSelectActive = ref(false) // touch/mobile multi-select without physical Shift
let surgeryMapInstance = null
let surgeryLayerGroup = null

const getPolygonArea = (feat) => {
  if (!feat) return 0
  if (feat.properties?.area_sqm != null && !isNaN(feat.properties.area_sqm)) {
    return Number(feat.properties.area_sqm)
  }
  try {
    return turf.area(feat)
  } catch (e) {
    return 0
  }
}

const formatArea = (sqm) => {
  if (!sqm || isNaN(sqm)) return '0 m²'
  if (sqm >= 10000) {
    return `${(sqm / 10000).toFixed(2)} ha`
  }
  return `${Math.round(sqm).toLocaleString('id-ID')} m²`
}

const totalAreaSqm = computed(() => {
  if (!features.value || features.value.length === 0) return 0
  return features.value.reduce((acc, feat) => {
    return acc + getPolygonArea(feat)
  }, 0)
})

// Compute the polygon with the largest area among selected polygons
const largestMergePolygon = computed(() => {
  if (!selectedForMerge.value || selectedForMerge.value.length === 0) return null
  let maxArea = -1
  let largest = null
  for (const feat of selectedForMerge.value) {
    const area = getPolygonArea(feat)
    if (area > maxArea) {
      maxArea = area
      largest = feat
    }
  }
  return largest
})

// Unique classes present among the polygons selected for merge
const mergeParticipantClasses = computed(() => {
  if (!selectedForMerge.value || selectedForMerge.value.length === 0) return []
  const classSummary = {}
  for (const feat of selectedForMerge.value) {
    const classId = feat.properties?.class_id
    if (classId !== undefined && classId !== null) {
      const area = getPolygonArea(feat)
      const existing = classSummary[classId]
      if (existing) {
        existing.totalArea += area
        existing.count += 1
      } else {
        const cls = annotationsStore.classes.find(c => c.id === classId)
        classSummary[classId] = {
          id: classId,
          name: cls?.name || feat.properties?.class_name || `Kelas #${classId}`,
          color: cls?.color || feat.properties?.color || '#3b82f6',
          totalArea: area,
          count: 1
        }
      }
    }
  }
  return Object.values(classSummary).sort((a, b) => b.totalArea - a.totalArea)
})

// Watch largest polygon to automatically update default selected target class
watch(largestMergePolygon, (newVal) => {
  if (newVal?.properties?.class_id) {
    mergeTargetClassId.value = newVal.properties.class_id
  }
})

let _featureUiCounter = 0
const getFeatureUiId = (feat) => {
  if (!feat) return 'f_' + (++_featureUiCounter)
  if (feat._uiId) return feat._uiId
  const id = feat.id || feat.properties?.id
  const uiId = id ? `f_id_${id}` : `f_tmp_${Date.now()}_${++_featureUiCounter}`
  feat._uiId = uiId
  return uiId
}

// STRICT SINGLEPART GUARANTEE:
// Explodes any MultiPolygon or GeometryCollection into distinct singlepart Polygon features
const explodeGeoJsonFeature = (feat) => {
  if (!feat) return []
  const geom = feat.geometry || feat
  if (!geom) return [feat]

  if (geom.type === 'MultiPolygon' && Array.isArray(geom.coordinates)) {
    return geom.coordinates.map((polyCoords, idx) => {
      const baseProps = feat.properties ? { ...feat.properties } : {}
      const rawId = feat.id || baseProps.id
      const subId = rawId ? `${rawId}_p${idx + 1}` : undefined
      const subFeat = {
        type: 'Feature',
        id: subId,
        geometry: {
          type: 'Polygon',
          coordinates: polyCoords
        },
        properties: {
          ...baseProps,
          id: subId
        }
      }
      subFeat._uiId = getFeatureUiId(subFeat)
      return subFeat
    })
  } else if (geom.type === 'GeometryCollection' && Array.isArray(geom.geometries)) {
    const list = []
    geom.geometries.forEach((subGeom) => {
      if (subGeom.type === 'Polygon' || subGeom.type === 'MultiPolygon') {
        const dummyFeat = { type: 'Feature', geometry: subGeom, properties: { ...(feat.properties || {}) } }
        list.push(...explodeGeoJsonFeature(dummyFeat))
      }
    })
    return list.length > 0 ? list : [feat]
  }

  if (!feat._uiId) feat._uiId = getFeatureUiId(feat)
  return [feat]
}

const selectableTasks = computed(() => {
  if (authStore.isAdmin) return tasksStore.tasks
  return tasksStore.tasks.filter(t => t.assigned_user_id === authStore.user?.id)
})

const selectedPolyUiIds = ref(new Set())
const hoverFeatureIdx = ref(null)

const isAllSelected = computed(() => {
  if (features.value.length === 0) return false
  return features.value.every(f => selectedPolyUiIds.value.has(f._uiId))
})

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedPolyUiIds.value = new Set()
  } else {
    const next = new Set()
    features.value.forEach(f => {
      const uId = f._uiId || getFeatureUiId(f)
      next.add(uId)
    })
    selectedPolyUiIds.value = next
  }
  refreshMapStyles()
}

const toggleSelectPolygon = (uiId) => {
  const next = new Set(selectedPolyUiIds.value)
  if (next.has(uiId)) {
    next.delete(uiId)
  } else {
    next.add(uiId)
  }
  selectedPolyUiIds.value = next
  refreshMapStyles()
}

const clearPolygonSelection = () => {
  selectedPolyUiIds.value = new Set()
  refreshMapStyles()
}

const highlightFeatureOnMap = (idx, isHover) => {
  hoverFeatureIdx.value = isHover ? idx : null
  refreshMapStyles()
}

const resetCurrentGridAnnotations = async () => {
  if (!selectedTaskId.value) return
  const gridCode = tasksStore.currentTask?.grid_code || `Grid #${selectedTaskId.value}`
  const confirmed = confirm(
    `Apakah Anda yakin ingin mereset seluruh poligon pada grid [${gridCode}]?\n\n` +
    `⚠️ Tindakan ini akan menghapus SEMUA poligon yang sudah digambar di grid ini agar Anda dapat memulai digitasi dari awal.\n` +
    `Status grid tetap ditugaskan kepada Anda dan grid lain TIDAK terpengaruh.`
  )
  if (!confirmed) return

  try {
    const res = await api.resetTaskAnnotations(selectedTaskId.value)
    showToast(res.data?.message || 'Grid berhasil direset bersih!')
    selectedPolyUiIds.value.clear()
    await loadTaskData(selectedTaskId.value, false)
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal mereset poligon grid')
  }
}

const batchDeleteSelectedPolygons = async () => {
  if (selectedPolyUiIds.value.size === 0 || !selectedTaskId.value) return
  const count = selectedPolyUiIds.value.size
  const toDelete = features.value.filter(f => selectedPolyUiIds.value.has(f._uiId))
  const remaining = features.value.filter(f => !selectedPolyUiIds.value.has(f._uiId))

  if (remaining.length === 0) {
    const emptyConfirmed = confirm(
      `Semua poligon di grid ini terpilih (${count} poligon).\n\n` +
      `⚠️ Menghapus semua poligon akan mengosongkan grid tile ini.\n\n` +
      `Lanjutkan?`
    )
    if (!emptyConfirmed) return
  } else {
    const confirmed = confirm(
      `Hapus ${count} poligon terpilih?\n\n` +
      `💡 Areanya akan otomatis disatukan ke poligon tetangga agar tidak berlubang (bolong).\n\n` +
      `Lanjutkan?`
    )
    if (!confirmed) return
  }

  showToast(`Menghapus ${count} poligon terpilih...`)

  // Smart absorption into touching neighbors so no holes are left behind
  if (remaining.length > 0 && toDelete.length > 0) {
    let unabsorbed = [...toDelete]
    let maxPasses = unabsorbed.length + 3

    while (unabsorbed.length > 0 && maxPasses-- > 0) {
      let progress = false
      const nextUnabsorbed = []

      for (const targetFeat of unabsorbed) {
        let targetPoly = null
        try {
          targetPoly = turf.cleanCoords(turf.feature(targetFeat.geometry))
        } catch (_) {
          targetPoly = turf.feature(targetFeat.geometry)
        }

        let bestNeighborIdx = -1
        let maxSharedScore = -1

        for (let rIdx = 0; rIdx < remaining.length; rIdx++) {
          let remPoly = null
          try {
            remPoly = turf.feature(remaining[rIdx].geometry)
          } catch (_) {
            continue
          }

          let sharedScore = 0
          try {
            const isTouching = turf.booleanTouches(targetPoly, remPoly)
            const isOverlap = turf.booleanOverlap(targetPoly, remPoly)

            if (isTouching || isOverlap) {
              try {
                const inter = turf.intersect(turf.featureCollection([targetPoly, remPoly]))
                if (inter) {
                  sharedScore = (inter.geometry && inter.geometry.type.includes('Line'))
                    ? turf.length(inter)
                    : turf.area(inter)
                } else {
                  sharedScore = 1.0
                }
              } catch (_) {
                sharedScore = 1.0
              }
            } else {
              // Buffer check (~0.5m) to catch vertices touching with snapping tolerance
              const buffered = turf.buffer(targetPoly, 0.000008, { units: 'kilometers' })
              if (turf.booleanIntersects(buffered, remPoly)) {
                sharedScore = 0.1
              }
            }
          } catch (_) {}

          if (sharedScore > maxSharedScore && sharedScore > 0) {
            maxSharedScore = sharedScore
            bestNeighborIdx = rIdx
          }
        }

        if (bestNeighborIdx !== -1) {
          try {
            const hostFeat = remaining[bestNeighborIdx]
            const hostPoly = turf.feature(hostFeat.geometry)
            const unioned = turf.union(turf.featureCollection([hostPoly, targetPoly]))
            if (unioned && unioned.geometry) {
              const cleaned = cleanSliversFromGeometry(unioned.geometry)
              if (cleaned) {
                hostFeat.geometry = cleaned
                hostFeat.properties.area_sqm = turf.area(turf.feature(cleaned))
                progress = true
                continue
              }
            }
          } catch (e) {
            console.warn('Absorption union error:', e)
          }
        }
        nextUnabsorbed.push(targetFeat)
      }

      if (!progress && nextUnabsorbed.length > 0 && remaining.length > 0) {
        // Fallback: absorb first unabsorbed polygon into closest neighbor
        const targetFeat = nextUnabsorbed.shift()
        const targetPoly = turf.feature(targetFeat.geometry)
        let minDist = Infinity
        let bestR = 0
        for (let rIdx = 0; rIdx < remaining.length; rIdx++) {
          try {
            const d = turf.distance(turf.centroid(targetPoly), turf.centroid(turf.feature(remaining[rIdx].geometry)))
            if (d < minDist) {
              minDist = d
              bestR = rIdx
            }
          } catch (_) {}
        }
        try {
          const hostFeat = remaining[bestR]
          const hostPoly = turf.feature(hostFeat.geometry)
          const unioned = turf.union(turf.featureCollection([hostPoly, targetPoly]))
          if (unioned && unioned.geometry) {
            const cleaned = cleanSliversFromGeometry(unioned.geometry)
            if (cleaned) {
              hostFeat.geometry = cleaned
              hostFeat.properties.area_sqm = turf.area(turf.feature(cleaned))
            }
          }
        } catch (_) {}
      }

      unabsorbed = nextUnabsorbed
    }
  }

  selectedPolyUiIds.value = new Set()
  restoreFeaturesToMap(remaining)
  pushHistory()

  try {
    await annotationsStore.saveGridAnnotations(selectedTaskId.value, remaining)
    showToast(`🗑️ ${count} poligon berhasil dihapus & diserap ke tetangga!`)
    try { await loadTaskData(selectedTaskId.value, true) } catch (_) {}
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal menyimpan perubahan hapus poligon')
  }
}

const batchMergeSelectedPolygons = async () => {
  if (selectedPolyUiIds.value.size < 2 || !selectedTaskId.value) return
  const toMerge = features.value.filter(f => selectedPolyUiIds.value.has(f._uiId))
  if (toMerge.length < 2) return

  const targetClass = annotationsStore.selectedClass || annotationsStore.classes.find(c => c.id !== 0) || annotationsStore.classes[0]
  const targetClassId = targetClass?.id || 1
  const targetClassName = targetClass?.name || 'Hutan Lahan Kering'

  try {
    const validPolys = toMerge.map(f => {
      try {
        return turf.cleanCoords(turf.feature(f.geometry))
      } catch (_) {
        return turf.feature(f.geometry)
      }
    })

    let mergedPoly = validPolys[0]
    for (let i = 1; i < validPolys.length; i++) {
      mergedPoly = turf.union(turf.featureCollection([mergedPoly, validPolys[i]]))
    }

    if (!mergedPoly || !mergedPoly.geometry) {
      alert('Poligon terpilih tidak dapat digabungkan. Pastikan poligon saling bersentuhan atau bertampalan.')
      return
    }

    const mergedGeom = cleanSliversFromGeometry(mergedPoly.geometry)
    if (!mergedGeom) {
      alert('Hasil penggabungan tidak valid.')
      return
    }

    const remaining = features.value.filter(f => !selectedPolyUiIds.value.has(f._uiId))
    const newUiId = 'f_merged_' + Date.now() + '_' + (++_featureUiCounter)
    const newFeat = {
      type: 'Feature',
      _uiId: newUiId,
      geometry: mergedGeom,
      properties: {
        class_id: targetClassId,
        class_name: targetClassName,
        color: targetClass?.color || '#006400',
        area_sqm: turf.area(turf.feature(mergedGeom))
      }
    }

    remaining.push(newFeat)
    selectedPolyUiIds.value.clear()
    restoreFeaturesToMap(remaining)
    pushHistory()

    await annotationsStore.saveGridAnnotations(selectedTaskId.value, remaining)
    showToast(`🧩 ${toMerge.length} poligon berhasil digabung menjadi [${targetClassName}]!`)
    try { await loadTaskData(selectedTaskId.value, true) } catch (_) {}
  } catch (err) {
    console.error('Batch merge error:', err)
    alert('Gagal menggabungkan poligon terpilih.')
  }
}

const findFeatureIndexForLayer = (layer) => {
  if (!features.value || features.value.length === 0) return -1

  // 1. Direct object identity
  let idx = features.value.findIndex(f => f === layer.feature)
  if (idx >= 0) return idx

  // 2. _uiId match
  const layerUiId = layer._uiId || layer.feature?._uiId
  if (layerUiId) {
    idx = features.value.findIndex(f => f._uiId === layerUiId)
    if (idx >= 0) return idx
  }

  // 3. Database ID match
  const featId = layer.feature?.id || layer.feature?.properties?.id
  if (featId) {
    idx = features.value.findIndex(f => (f.id && f.id === featId) || (f.properties?.id && f.properties.id === featId))
    if (idx >= 0) return idx
  }

  // 4. Layer order in featureGroup
  if (featureGroup) {
    let currentIdx = 0
    let matchedIdx = -1
    featureGroup.eachLayer(l => {
      if (l === layer && currentIdx < features.value.length) {
        matchedIdx = currentIdx
      }
      currentIdx++
    })
    if (matchedIdx >= 0) return matchedIdx
  }

  return -1
}

const isFeatureSelectedForMerge = (feat, layer) => {
  if (!selectedForMerge.value || selectedForMerge.value.length === 0) return false
  const layerUiId = layer?._uiId || layer?.feature?._uiId
  const featUiId = feat?._uiId || feat?.id || feat?.properties?.id
  const featId = feat?.id || feat?.properties?.id || layer?.feature?.id || layer?.feature?.properties?.id

  return selectedForMerge.value.some(m => {
    if (m === feat || (layer && m === layer.feature)) return true
    if (m._uiId && ((layerUiId && m._uiId === layerUiId) || (featUiId && m._uiId === featUiId))) return true
    const mId = m.id || m.properties?.id
    if (mId && featId && mId === featId) return true
    return false
  })
}

// ─── UNDO / REDO HISTORY STACK ───────────────────────────
const history = ref([])
const historyIndex = ref(-1)
const MAX_HISTORY = 40

const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

const pushHistory = () => {
  const snapshot = JSON.parse(JSON.stringify(features.value))
  
  // Truncate future redo stack if branched
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  
  history.value.push(snapshot)
  if (history.value.length > MAX_HISTORY) {
    history.value.shift()
  }
  historyIndex.value = history.value.length - 1
  queueOfflineDraftSave()
}

const undo = async () => {
  if (!canUndo.value) return
  historyIndex.value--
  const snapshot = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  restoreFeaturesToMap(snapshot)
  showToast('Undo: Perubahan dibatalkan')
  queueOfflineDraftSave()
}

const redo = async () => {
  if (!canRedo.value) return
  historyIndex.value++
  const snapshot = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  restoreFeaturesToMap(snapshot)
  showToast('Redo: Perubahan diterapkan kembali')
  queueOfflineDraftSave()
}

const restoreFeaturesToMap = (snapshotFeatures) => {
  if (!featureGroup || !map) return
  clickedFeatureIdx.value = null
  selectedPolyUiIds.value.clear()
  map.closePopup()

  // Clean Geoman drawing / editing states if active
  try {
    if (map.pm && map.pm.globalDrawModeEnabled()) {
      map.pm.disableDraw()
    }
  } catch (_) {}

  const wasEditEnabled = map.pm && map.pm.globalEditEnabled()
  if (wasEditEnabled) {
    try {
      map.pm.disableGlobalEditMode()
    } catch (_) {}
  }

  // Remove any dangling temporary Geoman layers on map
  map.eachLayer(l => {
    if (l._pmTempLayer || l._pmDrawLayer || (l.options && l.options.isTempMarker)) {
      try { map.removeLayer(l) } catch (_) {}
    }
  })

  featureGroup.clearLayers()
  const singlepartSnapshot = []
  snapshotFeatures.forEach(feat => {
    singlepartSnapshot.push(...explodeGeoJsonFeature(feat))
  })
  features.value = singlepartSnapshot

  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  singlepartSnapshot.forEach(feat => {
    feat._uiId = getFeatureUiId(feat)
    const geojsonLayer = L.geoJSON(feat, {
      style: () => {
        const cls = classesMap[feat.properties?.class_id]
        const color = cls?.color || feat.properties?.color || '#9CA3AF'
        return { color, fillColor: color, fillOpacity: polygonOpacity.value, weight: 2 }
      }
    })

    geojsonLayer.eachLayer((l) => {
      l.feature = feat
      l._uiId = feat._uiId
      l._preEditGeom = JSON.parse(JSON.stringify(feat.geometry))
      const cls = classesMap[feat.properties?.class_id]
      if (cls) l.feature.properties.color = cls.color
      else l.feature.properties.color = feat.properties?.color || '#9CA3AF'
      bindLayerEvents(l)
      featureGroup.addLayer(l)
    })
  })

  if (wasEditEnabled) {
    try {
      map.pm.enableGlobalEditMode({
        snappable: true,
        snapDistance: 10,
        allowSelfIntersection: true,
        tooltips: false
      })
    } catch (_) {}
  }
}

// Global Keyboard Shortcuts & Micro-Interactions
let isSpacePeeking = false
let savedOpacityBeforePeek = 0.6

const handleKeydown = (e) => {
  // If user is typing in an input, textarea, or select, don't hijack shortcuts
  const activeTag = document.activeElement?.tagName?.toLowerCase()
  if (activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select') {
    return
  }

  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
  const cmdOrCtrl = isMac ? e.metaKey : e.ctrlKey

  // 1. Quick Peek Satellite: Hold Space to temporarily hide polygons
  if (e.code === 'Space' && !e.repeat && !isSpacePeeking) {
    e.preventDefault()
    isSpacePeeking = true
    savedOpacityBeforePeek = polygonOpacity.value > 0 ? polygonOpacity.value : 0.6
    polygonOpacity.value = 0
    updateOpacity()
    showToast('Tahan Spasi untuk melihat citra satelit')
    return
  }

  // 2. Single-Vertex Undo: Backspace / Delete during active polygon or line drawing
  if (e.key === 'Backspace' || e.key === 'Delete') {
    // If inside Studio Perbaikan Topologi and vertices are selected, delete them
    if (showTopologySurgeryModal.value && selectedSurgeryVertices.value.length > 0) {
      e.preventDefault()
      deleteSelectedSurgeryVertices()
      return
    }

    if (map && map.pm && map.pm.Draw) {
      const activeShape = map.pm.Draw.getActiveShape?.()
      if (activeShape && map.pm.Draw[activeShape]?._removeLastVertex) {
        e.preventDefault()
        map.pm.Draw[activeShape]._removeLastVertex()
        showToast('Titik sudut terakhir dibatalkan')
        return
      }
    }
  }

  // 2b. Enter key: accept AI Magic Wand candidate if available
  if (e.key === 'Enter') {
    if (aiSegmentCandidate.value) {
      e.preventDefault()
      acceptAiCandidate()
      return
    }
  }

  // 3. Escape key: cancel AI candidate, draw mode, clear vertex selection, or reset to pointer
  if (e.key === 'Escape') {
    if (aiSegmentCandidate.value) {
      cancelAiCandidate()
      return
    }

    if (showTopologySurgeryModal.value && selectedSurgeryVertices.value.length > 0) {
      clearSurgeryVertexSelection()
      showToast('Pilihan titik simpul dibatalkan')
      return
    }

    if (activeTool.value) {
      setDigitizeMode(null)
      showToast('Mode dinonaktifkan')
      return
    }
  }

  // 4. History Undo / Redo
  if (cmdOrCtrl && e.key.toLowerCase() === 'z') {
    e.preventDefault()
    if (e.shiftKey) {
      redo()
    } else {
      undo()
    }
    return
  } else if (cmdOrCtrl && e.key.toLowerCase() === 'y') {
    e.preventDefault()
    redo()
    return
  }

  // 5. Save Shortcut: Ctrl+S / Cmd+S
  if (cmdOrCtrl && e.key.toLowerCase() === 's') {
    e.preventDefault()
    saveAnnotations()
    return
  }

  // 6. Direct Tool Shortcuts (single keys when no modifiers held)
  if (!cmdOrCtrl && !e.altKey) {
    const k = e.key.toLowerCase()
    if (k === 'v') {
      setDigitizeMode(null)
    } else if (k === 'c') {
      setDigitizeMode('split_line')
    } else if (k === 'x') {
      setDigitizeMode('split_poly')
    } else if (k === 'l') {
      setDigitizeMode('freehand_cut')
    } else if (k === 'm') {
      setDigitizeMode('merge')
    } else if (k === 'e') {
      setDigitizeMode('edit')
    } else if (k === 's') {
      toggleSnapping()
    } else if (k === 'q') {
      toggleReviewPinsVisibility()
    }
  }
}

const handleKeyup = (e) => {
  if (e.code === 'Space' && isSpacePeeking) {
    e.preventDefault()
    isSpacePeeking = false
    polygonOpacity.value = savedOpacityBeforePeek > 0 ? savedOpacityBeforePeek : 0.6
    updateOpacity()
  }
}

let map = null
let tileLayer = null
let arcgisLayer = null
let focusMaskLayer = null
let gridBoundingLayer = null
let neighboringGridsLayer = null
let neighborPolygonsLayer = null
let featureGroup = null
let reviewPinsLayerGroup = null
let swipeLeftTileLayer = null
let swipeRightTileLayer = null
let aiCandidatePreviewLayer = null
let draftAutoSaveTimer = null
const features = ref([])
const outsideDimOpacity = ref(0.12) // Default lembut agar citra grid sebelah terlihat jernih
const showNeighborPolygons = ref(false) // Default OFF agar kanvas bersih, mapper bisa aktifkan saat perlu edge-matching
const neighborPolygonsOpacity = ref(0.4)
const neighborFeaturesCount = ref(0)
const isLoadingNeighbors = ref(false)

// Review Pins (Catatan Supervisi / QC)
const showReviewPins = ref(true)

function toggleReviewPinsVisibility() {
  showReviewPins.value = !showReviewPins.value
  renderReviewPinsOnMap()
  showToast(showReviewPins.value ? '📍 Pin Evaluasi QC Ditampilkan (Q)' : '👁️ Pin Evaluasi QC Disembunyikan (Q)')
}

const resolvedPinsCount = computed(() => {
  const pins = tasksStore.currentTaskReviewPins || []
  return pins.filter(p => p.status === 'RESOLVED').length
})

const allPinsResolved = computed(() => {
  const pins = tasksStore.currentTaskReviewPins || []
  return pins.length > 0 && pins.every(p => p.status === 'RESOLVED')
})

// Evaluation Pin Mode & Modal
const isAddEvaluationPinMode = ref(false)
const showEvaluationPinModal = ref(false)
const submittingEvaluationPin = ref(false)
const evaluationPinModalData = ref({
  lat: 0,
  lon: 0,
  note: '',
  category: 'Batas Kurang Pas',
  annotation_id: null,
  class_name: ''
})

const updateOutsideMask = () => {
  if (focusMaskLayer) {
    focusMaskLayer.setStyle({ fillOpacity: outsideDimOpacity.value })
  }
}

const updateNeighborOpacity = () => {
  if (neighborPolygonsLayer) {
    neighborPolygonsLayer.setStyle((feature) => {
      const color = feature?.properties?.color_hex || '#9CA3AF'
      return {
        color: color,
        weight: 1.8,
        dashArray: '5, 5',
        fillColor: color,
        fillOpacity: neighborPolygonsOpacity.value
      }
    })
  }
}

const loadNeighborPolygons = async (taskId) => {
  if (!map || !taskId) return
  if (neighborPolygonsLayer) {
    map.removeLayer(neighborPolygonsLayer)
    neighborPolygonsLayer = null
  }

  if (!showNeighborPolygons.value) {
    neighborFeaturesCount.value = 0
    return
  }

  try {
    isLoadingNeighbors.value = true
    const res = await api.getNeighborAnnotations(taskId)
    const fc = res.data || { type: 'FeatureCollection', features: [] }
    const feats = fc.features || []
    neighborFeaturesCount.value = feats.length

    if (!showNeighborPolygons.value) return

    neighborPolygonsLayer = L.geoJSON(fc, {
      style: (feature) => {
        const color = feature?.properties?.color_hex || '#9CA3AF'
        return {
          color: color,
          weight: 1.8,
          dashArray: '5, 5',
          fillColor: color,
          fillOpacity: neighborPolygonsOpacity.value,
          interactive: true
        }
      },
      onEachFeature: (feature, layer) => {
        layer.options.pmIgnore = false
        layer.options.snapIgnore = !isNeighborSnappingEnabled.value
        if (isNeighborSnappingEnabled.value && layer.pm) {
          layer.pm.enable({ snappable: true, allowSelfIntersection: false })
          layer.pm.disable()
        }
        const p = feature.properties || {}
        layer.bindTooltip(`
          <div class="text-xs font-sans">
            <div class="flex items-center gap-1.5 font-bold text-slate-800 border-b border-slate-200 pb-1 mb-1">
              <span class="inline-block w-2.5 h-2.5 rounded-sm" style="background-color: ${p.color_hex || '#9CA3AF'}"></span>
              <span>${p.class_name || 'Tutupan Lahan'}</span>
            </div>
            <div class="text-[10px] text-slate-600 space-y-0.5 font-mono">
              <div>Grid: <b class="text-indigo-700">${p.grid_code || '-'}</b></div>
              <div>Luas: <b>${p.area_ha || 0} ha</b></div>
            </div>
            <div class="mt-1 text-[9px] font-medium text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
              🔒 Referensi Grid Sebelah (Read-Only)
            </div>
          </div>
        `, { sticky: true })

        layer.on('click', (e) => {
          L.DomEvent.stopPropagation(e)
          showToast(`🔒 Poligon Grid Sebelah [${p.grid_code || 'Tetangga'}]: ${p.class_name} (Hanya Referensi Edge-Matching)`)
        })
      }
    })

    if (showNeighborPolygons.value) {
      neighborPolygonsLayer.addTo(map)
      if (featureGroup) featureGroup.bringToFront()
      if (gridBoundingLayer) gridBoundingLayer.bringToFront()
    }
  } catch (err) {
    console.warn('Gagal memuat poligon grid tetangga:', err)
  } finally {
    isLoadingNeighbors.value = false
  }
}

const toggleNeighborPolygons = async () => {
  showNeighborPolygons.value = !showNeighborPolygons.value
  const currentTaskId = selectedTaskId.value || tasksStore.currentTask?.id
  if (showNeighborPolygons.value) {
    if (currentTaskId) {
      await loadNeighborPolygons(currentTaskId)
    }
  } else {
    if (neighborPolygonsLayer && map) {
      map.removeLayer(neighborPolygonsLayer)
      neighborPolygonsLayer = null
    }
  }
}

const toggleNeighborSnapping = () => {
  isNeighborSnappingEnabled.value = !isNeighborSnappingEnabled.value
  if (neighborPolygonsLayer) {
    neighborPolygonsLayer.eachLayer(l => {
      l.options.pmIgnore = false
      l.options.snapIgnore = !isNeighborSnappingEnabled.value
      if (isNeighborSnappingEnabled.value && l.pm) {
        l.pm.enable({ snappable: true, allowSelfIntersection: false })
        l.pm.disable()
      }
    })
  }
  showToast(`Snap ke Batas Grid Tetangga: ${isNeighborSnappingEnabled.value ? 'AKTIF' : 'NONAKTIF'}`)
}

const getArcgisRasterFunction = (layerId) => {
  switch (layerId) {
    case 'arcgis_s2_natural': return 'Natural Color with DRA'
    case 'arcgis_s2_nir': return 'Color Infrared for Visualization'
    case 'arcgis_s2_agri': return 'Agriculture for Visualization'
    case 'arcgis_s2_urban': return 'Urban for Visualization'
    case 'arcgis_s2_swir': return 'Short-wave Infrared for Visualization'
    case 'arcgis_s2_ndvi': return 'NDVI Colorized for Visualization'
    case 'arcgis_s2_ndmi': return 'NDMI Colorized for Visualization'
    case 'arcgis_s2_ndwi': return 'NDWI Colorized for Visualization'
    case 'arcgis_s2_scl': return 'Scene Classification Map'
    default: return 'Natural Color with DRA'
  }
}

const layerOptions = [
  { id: 'local_s2_rgb', name: 'Sentinel-2 Sumbar (Warna Asli RGB)', desc: 'Citra lokal komposit 10m Cloud-Optimized GeoTIFF — Acuan Utama Digitasi', icon: Satellite, colorClass: 'text-emerald-700 font-bold' },
  { id: 'local_s2_cir', name: 'Sentinel-2 Sumbar (Infrared / NIR False Color)', desc: 'Citra lokal B8-B4-B3 (NIR) — Membedakan Hutan, Sawit, Sawah & Air', icon: Flame, colorClass: 'text-rose-600 font-bold' },
  { id: 'arcgis_s2_natural', name: 'Sentinel-2 L2A (ArcGIS Natural Color DRA)', desc: 'Esri Living Atlas • Warna alami 10m BOA dengan Dynamic Range Adjustment', icon: Satellite, colorClass: 'text-emerald-700' },
  { id: 'arcgis_s2_nir', name: 'Sentinel-2 L2A (ArcGIS False Color NIR)', desc: 'Esri Living Atlas • B8-B4-B3 vegetasi merah menyala (Hutan vs Semak)', icon: Flame, colorClass: 'text-rose-600' },
  { id: 'arcgis_s2_agri', name: 'Sentinel-2 L2A (ArcGIS Agriculture SWIR)', desc: 'Esri Living Atlas • B11-B8-B2 pemilah sawah, kelapa sawit & tanah', icon: Sprout, colorClass: 'text-amber-600' },
  { id: 'arcgis_s2_urban', name: 'Sentinel-2 L2A (ArcGIS Urban Terbangun)', desc: 'Esri Living Atlas • B12-B11-B4 kontras bangunan, aspal & pemukiman', icon: Shapes, colorClass: 'text-red-600' },
  { id: 'arcgis_s2_swir', name: 'Sentinel-2 L2A (ArcGIS Short-wave SWIR)', desc: 'Esri Living Atlas • B12-B8A-B4 singkapan geologi, tambang & tanah', icon: Layers, colorClass: 'text-orange-600' },
  { id: 'arcgis_s2_ndvi', name: 'Sentinel-2 L2A (ArcGIS NDVI Colorized)', desc: 'Esri Living Atlas • Indeks kerapatan klorofil terhitung di server', icon: TrendingUp, colorClass: 'text-teal-600' },
  { id: 'arcgis_s2_ndmi', name: 'Sentinel-2 L2A (ArcGIS NDMI Kelembaban)', desc: 'Esri Living Atlas • Indeks kelembaban kanopi & tanah basah', icon: Sprout, colorClass: 'text-cyan-600' },
  { id: 'arcgis_s2_ndwi', name: 'Sentinel-2 L2A (ArcGIS NDWI Air & Tambak)', desc: 'Esri Living Atlas • Indeks air pemisah tegas danau, sungai & tambak', icon: Globe2, colorClass: 'text-blue-600' },
  { id: 'arcgis_s2_scl', name: 'Sentinel-2 L2A (Scene Classification Map)', desc: 'Esri Living Atlas • Peta klasifikasi otomatis Sen2Cor ESA', icon: Palette, colorClass: 'text-purple-600' },
  { id: 'true_color', name: 'Sentinel-2 EOX Cloudless (ESA)', desc: 'Komposit bebas awan tahunan ESA Copernicus EOX', icon: Satellite, colorClass: 'text-blue-700' },
  { id: 'google_sat', name: 'Google Satellite Ultra-HD', desc: 'Citra satelit resolusi sangat tinggi zoom 20+', icon: Globe2, colorClass: 'text-blue-600' },
  { id: 'esri_sat', name: 'Esri World Imagery', desc: 'Citra satelit global resolusi tinggi jernih', icon: Globe, colorClass: 'text-slate-600' },
  { id: 'osm', name: 'OpenStreetMap Base', desc: 'Peta jalan & batas wilayah administrasi', icon: Map, colorClass: 'text-slate-500' }
]

const getTileUrl = (layerType, year) => {
  let s2Year = 's2cloudless-2024_3857'
  if (year === 2017) s2Year = 's2cloudless-2017_3857'
  else if (year === 2021) s2Year = 's2cloudless-2021_3857'
  else s2Year = 's2cloudless-2024_3857'

  const s2Url = `https://tiles.maps.eox.at/wmts/1.0.0/${s2Year}/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg`
  const googleSat = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
  const esriSatellite = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
  const osmUrl = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

  switch (layerType) {
    case 'true_color':
      return { url: s2Url, maxNativeZoom: 16, filter: 'contrast(106%) brightness(104%)', attr: `Sentinel-2 Cloudless (${year}) © EOX / ESA Copernicus` }
    case 'false_color_nir':
      return { url: s2Url, maxNativeZoom: 16, filter: 'hue-rotate(290deg) saturate(320%) contrast(125%) brightness(100%)', attr: `Sentinel-2 False Color NIR (${year})` }
    case 'swir':
      return { url: s2Url, maxNativeZoom: 16, filter: 'hue-rotate(65deg) saturate(240%) contrast(135%) brightness(105%)', attr: `Sentinel-2 Agriculture SWIR (${year})` }
    case 'ndvi':
      return { url: s2Url, maxNativeZoom: 16, filter: 'invert(15%) hue-rotate(95deg) saturate(350%) contrast(140%) brightness(105%)', attr: `Sentinel-2 NDVI Colorized (${year})` }
    case 'google_sat':
      return { url: googleSat, maxNativeZoom: 20, filter: 'none', attr: 'Google Satellite Ultra-HD' }
    case 'esri_sat':
      return { url: esriSatellite, maxNativeZoom: 19, filter: 'none', attr: 'Esri World Imagery' }
    case 'osm':
      return { url: osmUrl, maxNativeZoom: 19, filter: 'none', attr: '© OpenStreetMap contributors' }
    default:
      return { url: s2Url, maxNativeZoom: 16, filter: 'none', attr: `Sentinel-2 (${year})` }
  }
}

const applyImageryFilter = () => {
  const { brightness, contrast, saturation, opacity } = imagerySettings.value
  const container = tileLayer?.getContainer?.() || arcgisLayer?.getContainer?.()
  if (container) {
    container.style.filter = `url(#raster-gamma-filter) brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`
    container.style.opacity = `${opacity / 100}`
  }
}

const resetImagerySettings = () => {
  imagerySettings.value = {
    brightness: 100,
    contrast: 100,
    gamma: 1.0,
    saturation: 100,
    opacity: 100
  }
  applyImageryFilter()
  showToast('Pengaturan visual citra direset ke standar.')
}

const applyPreset = (preset) => {
  if (preset === 'normal') {
    imagerySettings.value = { brightness: 100, contrast: 100, gamma: 1.0, saturation: 100, opacity: 100 }
    showToast('Preset: Normal')
  } else if (preset === 'high_contrast') {
    imagerySettings.value = { brightness: 105, contrast: 145, gamma: 0.9, saturation: 120, opacity: 100 }
    showToast('Preset: Kontras Tinggi Aktif')
  } else if (preset === 'vegetation') {
    imagerySettings.value = { brightness: 102, contrast: 130, gamma: 1.15, saturation: 160, opacity: 100 }
    showToast('Preset: Penguat Vegetasi Aktif')
  } else if (preset === 'haze') {
    imagerySettings.value = { brightness: 92, contrast: 160, gamma: 0.8, saturation: 115, opacity: 100 }
    showToast('Preset: Tembus Kabut / Awan Tipis')
  } else if (preset === 'water') {
    imagerySettings.value = { brightness: 95, contrast: 150, gamma: 1.25, saturation: 85, opacity: 100 }
    showToast('Preset: Fokus Air & Lahan Basah')
  }
  applyImageryFilter()
}

watch(
  imagerySettings,
  () => {
    applyImageryFilter()
  },
  { deep: true }
)

const updateTileLayer = async () => {
  if (!map) return

  if (tileLayer) {
    map.removeLayer(tileLayer)
    tileLayer = null
  }
  if (arcgisLayer) {
    map.removeLayer(arcgisLayer)
    arcgisLayer = null
  }

  // 1. If user selected Local Sentinel-2 COG Raster Layer
  if (currentLayer.value === 'local_s2_rgb' || currentLayer.value === 'local_s2_cir') {
    const mode = currentLayer.value === 'local_s2_cir' ? 'cir' : 'rgb'
    const yr = currentYear.value || 2025
    const currentGrid = tasksStore.currentTask?.grid_code
    const tileUrl = currentGrid
      ? api.getGridRasterTileUrl(yr, currentGrid, mode, imagerySettings.value.gamma)
      : api.getMosaicRasterTileUrl(yr, mode, imagerySettings.value.gamma)

    tileLayer = L.tileLayer(tileUrl, {
      maxZoom: 16,
      maxNativeZoom: 16,
      attribution: `Citra Sentinel-2 Sumbar (${yr}) 10m Cloud-Optimized GeoTIFF`
    }).addTo(map)
    tileLayer.bringToBack()
    applyImageryFilter()
    return
  }

  // 2. If user selected an ArcGIS Sentinel-2 L2A ImageServer layer
  if (currentLayer.value.startsWith('arcgis_s2_')) {
    try {
      const res = await api.getArcgisToken()
      const token = res.data.token
      const rasterFunc = getArcgisRasterFunction(currentLayer.value)
      const yr = currentYear.value || 2025
      const fromDate = new Date(`${yr}-01-01T00:00:00Z`)
      const toDate = new Date(`${yr}-12-31T23:59:59Z`)

      arcgisLayer = imageMapLayer({
        url: 'https://sentinel.imagery1.arcgis.com/arcgis/rest/services/Sentinel2L2A/ImageServer',
        token: token,
        from: fromDate,
        to: toDate,
        renderingRule: {
          rasterFunction: rasterFunc
        },
        mosaicRule: {
          mosaicMethod: 'esriMosaicAttribute',
          sortField: 'cloudcover',
          sortValue: '0'
        },
        format: 'jpgpng',
        maxZoom: 16,
        attribution: `ArcGIS Sentinel-2 L2A ${yr} (10m) © European Space Agency & Esri Living Atlas`
      }).addTo(map)

      arcgisLayer.bringToBack()
      applyImageryFilter()
      return
    } catch (err) {
      console.warn('Failed to load ArcGIS Sentinel-2 layer, falling back to EOX Sentinel-2:', err)
      showToast('Gagal memuat ArcGIS Sentinel-2, beralih ke EOX...')
    }
  }

  // 3. Standard Tile Layers (EOX Sentinel-2, Google Satellite, Esri World Imagery, OSM)
  const conf = getTileUrl(currentLayer.value, currentYear.value)
  tileLayer = L.tileLayer(conf.url, {
    maxZoom: 16,
    maxNativeZoom: conf.maxNativeZoom || 18,
    attribution: conf.attr
  }).addTo(map)

  tileLayer.bringToBack()
  applyImageryFilter()
}

const classCounts = computed(() => {
  const counts = {}
  features.value.forEach(f => {
    const cid = f.properties?.class_id
    if (cid !== undefined) counts[cid] = (counts[cid] || 0) + 1
  })
  return counts
})

const showToast = (msg) => {
  toastMessage.value = msg
  setTimeout(() => { toastMessage.value = '' }, 3500)
}

const onNetworkOnline = () => {
  isNetworkOnline.value = true
  showToast('🌐 Koneksi internet kembali aktif!')
}

const onNetworkOffline = () => {
  isNetworkOnline.value = false
  showToast('⚠️ Koneksi terputus — Perubahan otomatis disimpan di browser (IndexedDB).')
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('keyup', handleKeyup)
  window.addEventListener('online', onNetworkOnline)
  window.addEventListener('offline', onNetworkOffline)
  
  // Fetch available dynamic raster years (2025, 2022, 2018+)
  try {
    const resYears = await api.getRasterYears()
    if (resYears.data?.available_years?.length > 0) {
      availableRasterYears.value = resYears.data.available_years
      if (!availableRasterYears.value.includes(currentYear.value)) {
        currentYear.value = resYears.data.default_year
      }
    }
  } catch (err) {
    console.warn('Could not fetch dynamic raster years:', err)
  }

  await annotationsStore.fetchClasses()
  tasksStore.selectedYear = currentYear.value
  await tasksStore.fetchTasks()
  if (tasksStore.tasks.length === 0) {
    tasksStore.selectedYear = null
    await tasksStore.fetchTasks()
  }

  // Default selected class to first real class (Hutan Lahan Kering)
  const realClasses = annotationsStore.classes.filter(c => c.id !== 0)
  if (realClasses.length > 0 && (!annotationsStore.selectedClass || annotationsStore.selectedClass.id === 0)) {
    annotationsStore.setSelectedClass(realClasses[0])
  }

  const queryTaskId = route.query.taskId ? parseInt(route.query.taskId) : null
  if (queryTaskId) {
    selectedTaskId.value = queryTaskId
  } else if (tasksStore.tasks.length > 0) {
    if (authStore.isAdmin) {
      selectedTaskId.value = tasksStore.tasks[0].id
    } else {
      const myTask = tasksStore.tasks.find(t => t.assigned_user_id === authStore.user?.id)
      selectedTaskId.value = myTask ? myTask.id : null
    }
  }

  await nextTick()
  initMap()

  if (selectedTaskId.value) {
    await loadTaskData(selectedTaskId.value)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('keyup', handleKeyup)
  window.removeEventListener('mouseup', onMapMouseUp)
  window.removeEventListener('online', onNetworkOnline)
  window.removeEventListener('offline', onNetworkOffline)
  window.removeEventListener('mousemove', onSwipeMouseMove)
  window.removeEventListener('mouseup', onSwipeMouseUp)
  destroySwipeLayers()
  if (draftAutoSaveTimer) clearTimeout(draftAutoSaveTimer)
  if (map) {
    map.remove()
    map = null
  }
})

// ── Map Scale & Coordinate Tracking ──────────────────────────────────────────
const mapZoom = ref(13)
const mapScaleRatio = ref('1:50,000')
const cursorCoords = ref({ lat: null, lng: null })

function updateMapScaleInfo() {
  if (!map) return
  mapZoom.value = map.getZoom()
  const centerLat = map.getCenter().lat
  // Resolution in meters/pixel: 156543.03392 * cos(lat) / 2^zoom
  const metersPerPixel = 156543.03392 * Math.cos((centerLat * Math.PI) / 180) / Math.pow(2, mapZoom.value)
  // At 96 DPI: 1 m = 3779.528 px
  const scaleDenom = Math.round(metersPerPixel * (96 / 0.0254))
  mapScaleRatio.value = `1:${scaleDenom.toLocaleString('id-ID')}`
}

let lastCoordThrottleTime = 0
function onMapMouseMove(e) {
  const now = performance.now()
  if (now - lastCoordThrottleTime < 60) return // Throttled to ~16 FPS to prevent Vue reactivity lockup
  lastCoordThrottleTime = now
  if (e && e.latlng) {
    cursorCoords.value = {
      lat: e.latlng.lat.toFixed(5),
      lng: e.latlng.lng.toFixed(5)
    }
  }
}

function updateSnappingOptions() {
  if (!map || !map.pm) return
  map.pm.setGlobalOptions({
    snappable: isSnappingEnabled.value,
    snapDistance: 12,
    snapSegment: isSnappingEnabled.value,
    snapVertex: true,
    snapMiddleMarkers: false,
    allowSelfIntersection: true,
    tooltips: false
  })
}

function toggleSnapping() {
  isSnappingEnabled.value = !isSnappingEnabled.value
  updateSnappingOptions()
  showToast(isSnappingEnabled.value ? '🧲 Snapping Sudut & Garis Aktif' : '⭕ Snapping Dinonaktifkan (Mode Cepat)')
}

const initMap = () => {
  if (map) return

  const effectiveMaxZoom = 16 // Batasi zoom maksimal di skala 300 meter (Level 16)
  map = L.map('map-container', {
    center: [-0.947, 100.370],
    zoom: 13,
    maxZoom: effectiveMaxZoom,
    minZoom: 9,
    zoomControl: false,
    attributionControl: false
  })

  L.control.zoom({ position: 'bottomright' }).addTo(map)

  // Leaflet Graphical Scale Bar (Metric: m & km)
  L.control.scale({
    position: 'bottomleft',
    metric: true,
    imperial: false,
    maxWidth: 160
  }).addTo(map)

  // Event Listeners for Dynamic Scale and Coordinates
  map.on('zoomend moveend', updateMapScaleInfo)
  map.on('zoomend', () => {
    renderReviewPinsOnMap()
  })
  map.on('mousemove', onMapMouseMove)
  updateMapScaleInfo()

  // Satellite Basemap
  updateTileLayer()

  // Feature Group for actively drawn/editable polygons
  featureGroup = L.featureGroup().addTo(map)
  // Review Pins Layer Group
  reviewPinsLayerGroup = L.layerGroup().addTo(map)

  // Direct map click for Evaluation Pins & AI Magic Wand:
  map.on('click', (e) => {
    if (isAddEvaluationPinMode.value) {
      onMapClickForEvaluationPin(e)
      return
    }
    if (activeTool.value === 'ai_wand') {
      onMapClickForAiWand(e)
      return
    }
  })

  updateSnappingOptions()

  // Freehand / Stream mode mouse bindings
  map.on('mousedown', onMapMouseDown)
  map.on('mousemove', onMapMouseMoveFreehand)
  map.on('mouseup', onMapMouseUp)
  window.addEventListener('mouseup', onMapMouseUp)

  // Hook creation events from Geoman
  map.on('pm:create', async (e) => {
    const layer = e.layer
    const layerGeoJSON = layer.toGeoJSON()

    // Immediately disable draw mode to avoid lingering double-click vertices
    try {
      if (map.pm?.globalDrawModeEnabled?.()) {
        map.pm.disableDraw()
      }
    } catch (_) {}

    // 1. If in split_line mode (LineString drawn)
    if (activeTool.value === 'split_line') {
      map.removeLayer(layer)
      const cleanGeom = cleanLineCoordinates(layerGeoJSON.geometry)
      await handleSplitByLine(cleanGeom)
      return
    }

    // 2. If in split_poly mode (Polygon drawn)
    if (activeTool.value === 'split_poly') {
      map.removeLayer(layer)
      await handleSplitByPolygon(layerGeoJSON.geometry)
      return
    }

    // 3. Prevent raw overlay polygon creation that causes overlap
    map.removeLayer(layer)
    showToast('Gunakan alat Potong Garis atau Potong Area untuk membagi poligon.')
  })

  map.on('pm:remove', () => {
    clickedFeatureIdx.value = null
    syncFeaturesFromMap()
    pushHistory()
  })

  // Single-fire auto-clip on drag end (not continuous per-pixel edit)
  map.on('pm:dragend', (e) => {
    if (e && e.layer) {
      applyAutoClipAndHealOnEdit(e.layer)
    } else {
      syncFeaturesFromMap()
      pushHistory()
    }
  })
}

// ── FREEHAND & MARQUEE BOX SELECTION ─────────────────────
let isDrawingFreehand = false
let freehandPoints = []
let freehandPolyline = null

let isShiftSelecting = false
let shiftSelectStartLatLng = null
let shiftSelectRect = null

const onMapMouseDown = (e) => {
  // 1. Shift + Drag marquee box selection
  if (e.originalEvent && e.originalEvent.shiftKey && e.originalEvent.button === 0) {
    isShiftSelecting = true
    shiftSelectStartLatLng = e.latlng
    if (map) map.dragging.disable()
    if (shiftSelectRect && map) {
      map.removeLayer(shiftSelectRect)
    }
    shiftSelectRect = L.rectangle([e.latlng, e.latlng], {
      color: '#4f46e5',
      weight: 2,
      dashArray: '4, 4',
      fillColor: '#818cf8',
      fillOpacity: 0.25,
      interactive: false
    }).addTo(map)
    return
  }

  // 2. Freehand digitizing mode (Lasso Cut)
  if (activeTool.value !== 'freehand_cut') return
  if (e.originalEvent && e.originalEvent.button !== 0) return

  isDrawingFreehand = true
  if (map) map.dragging.disable()
  freehandPoints = [e.latlng]

  if (freehandPolyline && map) {
    map.removeLayer(freehandPolyline)
  }

  freehandPolyline = L.polyline([e.latlng], {
    color: '#E11D48',
    weight: 3.5,
    dashArray: '4, 4',
    opacity: 0.95
  }).addTo(map)
}

const onMapMouseMoveFreehand = (e) => {
  if (isShiftSelecting && shiftSelectStartLatLng && shiftSelectRect) {
    const bounds = L.latLngBounds(shiftSelectStartLatLng, e.latlng)
    shiftSelectRect.setBounds(bounds)
    return
  }

  if (!isDrawingFreehand || activeTool.value !== 'freehand_cut' || !freehandPolyline || !map) return

  const lastPoint = freehandPoints[freehandPoints.length - 1]
  const p1 = map.latLngToLayerPoint(lastPoint)
  const p2 = map.latLngToLayerPoint(e.latlng)

  // Record point every 6 screen pixels for silky smooth natural curves
  if (p1.distanceTo(p2) >= 6) {
    freehandPoints.push(e.latlng)
    freehandPolyline.setLatLngs(freehandPoints)
  }
}

const onMapMouseUp = async (e) => {
  if (isShiftSelecting) {
    isShiftSelecting = false
    if (map) map.dragging.enable()
    if (shiftSelectRect && map) {
      const bounds = shiftSelectRect.getBounds()
      map.removeLayer(shiftSelectRect)
      shiftSelectRect = null

      const sw = bounds.getSouthWest()
      const ne = bounds.getNorthEast()
      const dLat = Math.abs(ne.lat - sw.lat)
      const dLng = Math.abs(ne.lng - sw.lng)

      if (dLat > 0.00005 && dLng > 0.00005) {
        const boxPoly = turf.bboxPolygon([
          Math.min(sw.lng, ne.lng),
          Math.min(sw.lat, ne.lat),
          Math.max(sw.lng, ne.lng),
          Math.max(sw.lat, ne.lat)
        ])

        const next = new Set(selectedPolyUiIds.value)
        let newlySelectedCount = 0
        features.value.forEach(feat => {
          try {
            const fPoly = turf.feature(feat.geometry)
            if (turf.booleanIntersects(fPoly, boxPoly)) {
              const uId = feat._uiId || getFeatureUiId(feat)
              next.add(uId)
              newlySelectedCount++
            }
          } catch (_) {}
        })

        selectedPolyUiIds.value = next
        refreshMapStyles()

        if (newlySelectedCount > 0) {
          showToast(`📌 ${selectedPolyUiIds.value.size} poligon terseleksi`)
          rightTab.value = 'polygons'
        }
      }
    }
    return
  }

  if (!isDrawingFreehand || activeTool.value !== 'freehand_cut') return
  isDrawingFreehand = false
  if (map) map.dragging.enable()

  if (freehandPolyline && map) {
    map.removeLayer(freehandPolyline)
    freehandPolyline = null
  }

  if (freehandPoints.length < 3) {
    freehandPoints = []
    return
  }

  try {
    const coords = freehandPoints.map(p => [p.lng, p.lat])
    // Close polygon ring
    coords.push([coords[0][0], coords[0][1]])

    let polyGeoJSON = turf.polygon([coords])
    polyGeoJSON = turf.cleanCoords(polyGeoJSON)

    // Unkink if there were minor self-intersections during freehand drawing
    const unkinked = turf.unkinkPolygon(polyGeoJSON)
    if (unkinked.features && unkinked.features.length > 0) {
      let largest = unkinked.features[0]
      let maxArea = turf.area(largest)
      for (let i = 1; i < unkinked.features.length; i++) {
        const a = turf.area(unkinked.features[i])
        if (a > maxArea) {
          maxArea = a
          largest = unkinked.features[i]
        }
      }
      polyGeoJSON = largest
    }

    // Micro-jitter smoothing filter: removes hand tremors while preserving true natural bounds
    try {
      polyGeoJSON = turf.simplify(polyGeoJSON, { tolerance: 0.00002, highQuality: true })
    } catch (simpErr) {
      console.warn('Simplification skipped:', simpErr)
    }

    // Potong Poligon berbasis Lasso/Freehand
    await handleSplitByPolygon(polyGeoJSON.geometry)
  } catch (err) {
    console.error('Failed to process freehand action:', err)
    showToast('Gagal memproses freehand. Silakan coba kembali.')
  } finally {
    freehandPoints = []
  }
}

// ─── GIS DIGITIZE TOOL MODES ─────────────────────────────
const setDigitizeMode = (mode, force = false) => {
  if (!map) return

  // Reset freehand drawing state
  if (isDrawingFreehand) {
    isDrawingFreehand = false
    map.dragging.enable()
  }
  if (freehandPolyline) {
    map.removeLayer(freehandPolyline)
    freehandPolyline = null
  }
  if (map.getContainer()) {
    map.getContainer().style.cursor = ['freehand_poly', 'freehand_cut'].includes(mode) ? 'crosshair' : ''
    map.getContainer().style.cursor = mode === 'freehand_cut' ? 'crosshair' : ''
  }

  // Always close any open popup and clear selection
  try { map.closePopup() } catch (_) {}

  // Safely disable any active Geoman modes
  try { if (map.pm?.globalDrawModeEnabled?.()) map.pm.disableDraw() } catch (_) {}
  try { if (map.pm?.globalEditEnabled?.()) map.pm.disableGlobalEditMode() } catch (_) {}
  try { if (map.pm?.globalRemovalModeEnabled?.()) map.pm.disableGlobalRemovalMode() } catch (_) {}
  try { if (map.pm?.globalDragModeEnabled?.()) map.pm.disableGlobalDragMode() } catch (_) {}

  if (!force && activeTool.value === mode) {
    activeTool.value = null
    renderReviewPinsOnMap()
    showToast('Alat Aktif: Pilih Poligon')
    return
  }

  activeTool.value = mode
  selectedForMerge.value = []
  if (['split_line', 'split_poly', 'freehand_cut'].includes(mode)) {
    if (selectedPolyUiIds.value && selectedPolyUiIds.value.size > 1) {
      selectedPolyUiIds.value.clear()
    }
  }
  renderReviewPinsOnMap()

  switch (mode) {
    case null:
      showToast('Alat Aktif: Pilih Poligon')
      break

    case 'freehand_cut':
      showToast('Alat Aktif: Pemotong Bebas (Lasso). Tarik garis melingkar.')
      break

    case 'split_line':
      showToast('Alat Aktif: Potong Garis (Split). Tarik garis melintasi poligon.')
      map.pm.enableDraw('Line', {
        snappable: isSnappingEnabled.value,
        snapDistance: 12,
        snapSegment: isSnappingEnabled.value,
        snapVertex: true,
        tooltips: false
      })
      break

    case 'split_poly':
      showToast('Alat Aktif: Potong Poligon (Cookie Cutter).')
      map.pm.enableDraw('Polygon', {
        snappable: isSnappingEnabled.value,
        snapDistance: 12,
        snapSegment: isSnappingEnabled.value,
        snapVertex: true,
        tooltips: false
      })
      break

    case 'edit':
      showToast('Alat Aktif: Edit Titik Simpul.')
      if (clickedFeatureIdx.value !== null && features.value[clickedFeatureIdx.value]) {
        const targetFeat = features.value[clickedFeatureIdx.value]
        const targetUiId = targetFeat._uiId || targetFeat.id
        let targetLyr = null
        if (featureGroup) {
          featureGroup.eachLayer(l => {
            if ((l._uiId || l.feature?.id) === targetUiId) targetLyr = l
          })
        }
        if (targetLyr && targetLyr.pm) {
          map.pm.disableGlobalEditMode()
          try {
            targetLyr._preEditGeom = JSON.parse(JSON.stringify(targetLyr.toGeoJSON().geometry))
          } catch (_) {}
          targetLyr.pm.enable({
            snappable: isSnappingEnabled.value,
            snapDistance: 15,
            snapSegment: false,
            snapVertex: true,
            snapMiddleMarkers: false,
            allowSelfIntersection: true
          })
          targetLyr.bringToFront()
          showToast(`Mode Edit Titik aktif untuk Poligon #${clickedFeatureIdx.value + 1}. Geser titik untuk mengubah bentuk.`)
          break
        }
      }
      if (features.value.length > 50) {
        showToast('Pilih salah satu poligon di peta terlebih dahulu untuk mengedit titik simpulnya.')
        break
      }
      if (featureGroup) {
        featureGroup.eachLayer(l => {
          try {
            l._preEditGeom = JSON.parse(JSON.stringify(l.toGeoJSON().geometry))
          } catch (_) {}
        })
      }
      map.pm.enableGlobalEditMode({
        snappable: isSnappingEnabled.value,
        snapDistance: 12,
        snapSegment: false,
        snapVertex: true,
        snapMiddleMarkers: false,
        allowSelfIntersection: true,
        tooltips: false
      })
      break

    case 'ai_wand':
      showToast('Alat Aktif: 🪄 AI Magic Wand. Klik area pada citra untuk segmentasi otomatis.')
      if (map && map.getContainer()) {
        map.getContainer().style.cursor = 'crosshair'
      }
      break

    case 'delete':
      showToast('Alat Aktif: Hapus Poligon. Klik objek yang ingin dihapus.')
      break

    case 'merge':
      showToast('Alat Aktif: Gabung Poligon. Pilih 2 atau lebih poligon bersebelahan.')
      break
  }
}

// ─── OFFLINE DRAFT & INDEXEDDB AUTO-SAVE (POIN 1) ─────────────
const queueOfflineDraftSave = () => {
  if (!selectedTaskId.value || !features.value) return
  if (draftAutoSaveTimer) clearTimeout(draftAutoSaveTimer)
  draftAutoSaveTimer = setTimeout(async () => {
    try {
      await saveTaskDraft(selectedTaskId.value, features.value)
      localDraftStatus.value = {
        updatedAt: new Date().toISOString(),
        polygonCount: features.value.length
      }
    } catch (err) {
      console.warn('Gagal auto-save draf lokal ke IndexedDB:', err)
    }
  }, 1000)
}

const restoreOfflineDraft = () => {
  if (!pendingDraftToRestore.value) return
  const draftFeats = pendingDraftToRestore.value.features || []
  restoreFeaturesToMap(draftFeats)
  pushHistory()
  showDraftRestorePrompt.value = false
  showToast(`✓ Draf lokal offline (${draftFeats.length} poligon) berhasil dipulihkan!`)
}

const discardOfflineDraftPrompt = () => {
  showDraftRestorePrompt.value = false
  if (selectedTaskId.value) {
    clearTaskDraft(selectedTaskId.value)
  }
  pendingDraftToRestore.value = null
  localDraftStatus.value = null
  showToast('Draf offline diabaikan.')
}

// ─── TEMPORAL COMPARISON SWIPE MAP (POIN 2) ─────────────────
const toggleSwipeMode = () => {
  isSwipeMode.value = !isSwipeMode.value
  if (isSwipeMode.value) {
    if (tileLayer && map) {
      map.removeLayer(tileLayer)
      tileLayer = null
    }
    if (arcgisLayer && map) {
      map.removeLayer(arcgisLayer)
      arcgisLayer = null
    }
    initSwipeLayers()
    showToast('Mode Swipe aktif: Geser garis pembagi untuk membandingkan citra')
  } else {
    destroySwipeLayers()
    updateTileLayer()
    showToast('Mode Swipe ditutup, kembali ke citra tunggal')
  }
}

const initSwipeLayers = () => {
  if (!map) return
  destroySwipeLayers()

  const currentGrid = tasksStore.currentTask?.grid_code
  const leftUrl = currentGrid
    ? api.getGridRasterTileUrl(swipeLeftYear.value, currentGrid, 'rgb', imagerySettings.value.gamma)
    : api.getMosaicRasterTileUrl(swipeLeftYear.value, 'rgb', imagerySettings.value.gamma)
  const rightUrl = currentGrid
    ? api.getGridRasterTileUrl(swipeRightYear.value, currentGrid, 'rgb', imagerySettings.value.gamma)
    : api.getMosaicRasterTileUrl(swipeRightYear.value, 'rgb', imagerySettings.value.gamma)

  swipeLeftTileLayer = L.tileLayer(leftUrl, {
    maxZoom: 16,
    maxNativeZoom: 16,
    attribution: `Sentinel-2 Sumbar (${swipeLeftYear.value})`
  }).addTo(map)

  swipeRightTileLayer = L.tileLayer(rightUrl, {
    maxZoom: 16,
    maxNativeZoom: 16,
    attribution: `Sentinel-2 Sumbar (${swipeRightYear.value})`
  }).addTo(map)

  swipeLeftTileLayer.bringToBack()
  swipeRightTileLayer.bringToBack()

  swipeLeftTileLayer.on('load', updateSwipeClip)
  swipeRightTileLayer.on('load', updateSwipeClip)
  setTimeout(updateSwipeClip, 50)
}

const updateSwipeLayers = () => {
  if (isSwipeMode.value) {
    initSwipeLayers()
  }
}

const destroySwipeLayers = () => {
  if (swipeLeftTileLayer && map) {
    map.removeLayer(swipeLeftTileLayer)
    swipeLeftTileLayer = null
  }
  if (swipeRightTileLayer && map) {
    map.removeLayer(swipeRightTileLayer)
    swipeRightTileLayer = null
  }
}

const updateSwipeClip = () => {
  const pos = swipePosition.value
  if (swipeLeftTileLayer && swipeLeftTileLayer.getContainer) {
    const el = swipeLeftTileLayer.getContainer()
    if (el) el.style.clipPath = `polygon(0% 0%, ${pos}% 0%, ${pos}% 100%, 0% 100%)`
  }
  if (swipeRightTileLayer && swipeRightTileLayer.getContainer) {
    const el = swipeRightTileLayer.getContainer()
    if (el) el.style.clipPath = `polygon(${pos}% 0%, 100% 0%, 100% 100%, ${pos}% 100%)`
  }
}

const onSwipeMouseDown = (e) => {
  e.preventDefault()
  isDraggingSwipe.value = true
  window.addEventListener('mousemove', onSwipeMouseMove)
  window.addEventListener('mouseup', onSwipeMouseUp)
}

const onSwipeMouseMove = (e) => {
  if (!isDraggingSwipe.value) return
  const container = document.getElementById('map-container')
  if (!container) return
  const rect = container.getBoundingClientRect()
  const x = e.clientX - rect.left
  const pct = Math.max(5, Math.min(95, (x / rect.width) * 100))
  swipePosition.value = Math.round(pct)
  updateSwipeClip()
}

const onSwipeMouseUp = () => {
  if (isDraggingSwipe.value) {
    isDraggingSwipe.value = false
    window.removeEventListener('mousemove', onSwipeMouseMove)
    window.removeEventListener('mouseup', onSwipeMouseUp)
  }
}

// ─── AI-ASSISTED DIGITIZING (POIN 3) ────────────────────────
const onMapClickForAiWand = async (e) => {
  if (isAiSegmenting.value) return
  const lat = e.latlng.lat
  const lon = e.latlng.lng
  const gridCode = tasksStore.currentTask?.grid_code
  const year = currentYear.value || 2025

  if (!gridCode) {
    showToast('Pilih grid tugas terlebih dahulu untuk menggunakan AI Magic Wand.')
    return
  }

  try {
    isAiSegmenting.value = true
    const res = await api.requestAISegment({
      task_grid_id: selectedTaskId.value || tasksStore.currentTask?.id,
      grid_code: gridCode,
      year: year,
      lat: lat,
      lon: lon,
      tolerance: aiWandTolerance.value
    })
    const feat = res.data?.feature || (res.data?.geometry ? res.data : null)
    if (feat && feat.geometry) {
      if (!feat.properties) feat.properties = {}
      if (feat.properties.suggested_class_name && !feat.properties.class_name) {
        feat.properties.class_name = feat.properties.suggested_class_name
        feat.properties.class_id = feat.properties.suggested_class_id
      }
      aiSegmentCandidate.value = feat

      if (aiCandidatePreviewLayer && map) {
        map.removeLayer(aiCandidatePreviewLayer)
      }

      aiCandidatePreviewLayer = L.geoJSON(feat, {
        style: {
          color: '#6366f1',
          weight: 3,
          dashArray: '6, 6',
          fillColor: '#818cf8',
          fillOpacity: 0.6
        }
      }).addTo(map)

      showToast(`🪄 AI Segmentasi terdeteksi: ${feat.properties?.class_name || 'Poligon'} (${feat.properties?.area_ha || 0} ha, ${Math.round((feat.properties?.confidence || 0.8) * 100)}% yakin). Tekan Enter untuk menerima.`)
    } else {
      showToast('AI tidak menemukan batas area homogen yang cukup jelas. Coba klik di lokasi lain.')
    }
  } catch (err) {
    console.error('Error running AI segment:', err)
    showToast('Gagal AI Magic Wand: ' + (err.response?.data?.detail || err.message))
  } finally {
    isAiSegmenting.value = false
  }
}

const acceptAiCandidate = () => {
  if (!aiSegmentCandidate.value || !map) return
  const candidate = aiSegmentCandidate.value

  let assignedClassId = annotationsStore.selectedClass?.id
  if (!assignedClassId && candidate.properties?.class_id) {
    assignedClassId = candidate.properties.class_id
  }
  if (!assignedClassId && annotationsStore.classes.length > 0) {
    assignedClassId = annotationsStore.classes[0].id
  }
  const matchedCls = annotationsStore.classes.find(c => c.id === assignedClassId)

  candidate.properties = {
    ...candidate.properties,
    class_id: assignedClassId,
    class_name: matchedCls ? matchedCls.name : 'Tutupan Lahan',
    color: matchedCls ? matchedCls.color : '#9CA3AF'
  }
  candidate._uiId = getFeatureUiId(candidate)

  if (aiCandidatePreviewLayer && map) {
    map.removeLayer(aiCandidatePreviewLayer)
    aiCandidatePreviewLayer = null
  }

  const newLyr = L.geoJSON(candidate, {
    style: () => {
      const color = candidate.properties.color || '#9CA3AF'
      return { color, fillColor: color, fillOpacity: polygonOpacity.value, weight: 2 }
    }
  })

  newLyr.eachLayer(l => {
    l.feature = candidate
    l._uiId = candidate._uiId
    bindLayerEvents(l)
    featureGroup.addLayer(l)
  })

  features.value.push(candidate)
  aiSegmentCandidate.value = null
  pushHistory()
  queueOfflineDraftSave()
  showToast(`✓ Poligon AI [${candidate.properties.class_name}] berhasil dimasukkan!`)
}

const cancelAiCandidate = () => {
  if (aiCandidatePreviewLayer && map) {
    map.removeLayer(aiCandidatePreviewLayer)
    aiCandidatePreviewLayer = null
  }
  aiSegmentCandidate.value = null
  showToast('Pratinjau poligon AI dibatalkan.')
}

// ─── MAPPER LEADERBOARD (POIN 6) ────────────────────────────
const openLeaderboardModal = async () => {
  showLeaderboardModal.value = true
  leaderboardLoading.value = true
  try {
    const res = await api.getMapperLeaderboard()
    leaderboardList.value = res.data?.leaderboard || []
  } catch (err) {
    console.error('Gagal mengambil data leaderboard:', err)
    showToast('Gagal memuat statistik leaderboard.')
  } finally {
    leaderboardLoading.value = false
  }
}

// ─── HIGH-PERFORMANCE DELTA STATE UPDATER ─────────────────
// Avoids full network re-fetch & complete DOM teardown of 800+ polygons
const applyDeltaUpdate = (deletedIds = [], createdFeatures = [], updatedFeatures = []) => {
  if (!featureGroup || !map) return false

  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  // 1. Remove deleted layers from Leaflet map & local features array
  if (deletedIds && deletedIds.length > 0) {
    const delStrSet = new Set(deletedIds.map(id => String(id)))
    const getBaseId = (str) => {
      if (!str) return str
      const s = String(str)
      if (s.includes('_p')) return s.split('_p')[0]
      if (s.includes('_')) return s.split('_')[0]
      return s
    }
    const layersToRemove = []
    featureGroup.eachLayer(l => {
      const fid = l.feature?.id ?? l.feature?.properties?.id
      if (fid !== undefined && fid !== null) {
        const fidStr = String(fid)
        const baseId = getBaseId(fidStr)
        if (delStrSet.has(fidStr) || delStrSet.has(baseId)) {
          layersToRemove.push(l)
          return
        }
      }
      if (l._uiId) {
        for (const delId of delStrSet) {
          if (l._uiId === `f_id_${delId}` || l._uiId.startsWith(`f_id_${delId}_`)) {
            layersToRemove.push(l)
            break
          }
        }
      }
    })

    layersToRemove.forEach(l => {
      try {
        if (map && map.pm) l.pm?.disable()
        featureGroup.removeLayer(l)
        if (map.hasLayer(l)) map.removeLayer(l)
      } catch (_) {}
    })

    features.value = features.value.filter(f => {
      const fid = f.id ?? f.properties?.id
      if (fid !== undefined && fid !== null) {
        const fidStr = String(fid)
        const baseId = getBaseId(fidStr)
        if (delStrSet.has(fidStr) || delStrSet.has(baseId)) return false
      }
      if (f._uiId) {
        for (const delId of delStrSet) {
          if (f._uiId === `f_id_${delId}` || f._uiId.startsWith(`f_id_${delId}_`)) return false
        }
      }
      return true
    })
  }

  // 2. Handle updated features (e.g. reclassified polygons)
  if (updatedFeatures && updatedFeatures.length > 0) {
    const upMap = new Map()
    updatedFeatures.forEach(uf => {
      const fid = uf.id ?? uf.properties?.id
      if (fid !== undefined && fid !== null) upMap.set(String(fid), uf)
    })

    featureGroup.eachLayer(l => {
      const fid = l.feature?.id ?? l.feature?.properties?.id
      if (fid !== undefined && fid !== null && upMap.has(String(fid))) {
        const uf = upMap.get(String(fid))
        l.feature = uf
        const cls = classesMap[uf.properties?.class_id]
        const color = cls?.color || '#9CA3AF'
        if (l.setStyle) {
          l.setStyle({ color, fillColor: color, fillOpacity: polygonOpacity.value, weight: 2 })
        }
      }
    })

    features.value = features.value.map(f => {
      const fid = f.id ?? f.properties?.id
      if (fid !== undefined && fid !== null && upMap.has(String(fid))) {
        return upMap.get(String(fid))
      }
      return f
    })
  }

  // 3. Add created features (STRICT SINGLEPART: unpack any MultiPolygon!)
  if (createdFeatures && createdFeatures.length > 0) {
    const strictCreated = []
    createdFeatures.forEach(feat => {
      strictCreated.push(...explodeGeoJsonFeature(feat))
    })

    strictCreated.forEach(feat => {
      feat._uiId = getFeatureUiId(feat)
      const geojsonLayer = L.geoJSON(feat, {
        style: () => {
          const cls = classesMap[feat.properties?.class_id]
          const color = cls?.color || '#9CA3AF'
          return { color, fillColor: color, fillOpacity: polygonOpacity.value, weight: 2 }
        }
      })

      geojsonLayer.eachLayer((l) => {
        l.feature = feat
        l._uiId = feat._uiId
        const cls = classesMap[feat.properties?.class_id]
        if (cls) l.feature.properties.color = cls.color
        else l.feature.properties.color = '#9CA3AF'
        bindLayerEvents(l)
        featureGroup.addLayer(l)
      })

      features.value.push(feat)
    })
  }

  // 4. Sync store reference and update history stack
  annotationsStore.currentFeatures = features.value
  clickedFeatureIdx.value = null
  selectedPolyUiIds.value.clear()
  if (selectedTaskId.value) {
    saveTaskDraft(selectedTaskId.value, features.value).catch(() => {})
  }
  pushHistory()
  return true
}

// Helper to find target polygon for line/polygon split
const findTargetPolygonForCut = (cutGeom) => {
  if (!features.value || features.value.length === 0 || !cutGeom) return { feat: null, annId: null }

  try {
    const cutFeat = cutGeom.type === 'LineString' ? turf.lineString(cutGeom.coordinates) : turf.polygon(cutGeom.coordinates)
    const lineLen = cutGeom.type === 'LineString' ? turf.length(cutFeat) : 0

    // Sample interior points along the cut line (10%, 20%, ..., 90%)
    const samplePoints = []
    if (cutGeom.type === 'LineString' && lineLen > 0) {
      for (let i = 1; i <= 9; i++) {
        try {
          samplePoints.push(turf.along(cutFeat, (lineLen * i) / 10))
        } catch (_) {}
      }
    }

    const extractNumericId = (f) => {
      if (!f) return null
      const candidates = [f.properties?.id, f.id, f._uiId]
      for (const c of candidates) {
        if (c === null || c === undefined) continue
        if (typeof c === 'number' && !isNaN(c) && c > 0) return c
        const str = String(c).trim()
        if (str.startsWith('f_tmp_')) continue
        if (str.startsWith('f_id_')) {
          const sub = str.slice(5).split('_')[0]
          const n = parseInt(sub, 10)
          if (!isNaN(n) && n > 0) return n
        }
        const clean = str.split('_p')[0].split('_')[0]
        const n = parseInt(clean, 10)
        if (!isNaN(n) && n > 0) return n
      }
      return null
    }

    const testIntersects = (feat) => {
      if (!feat || !feat.geometry) return false
      try {
        if (turf.booleanIntersects(cutFeat, feat)) return true
      } catch (_) {}
      try {
        const buff = turf.buffer(feat, 0.0005, { units: 'kilometers' })
        if (turf.booleanIntersects(cutFeat, buff)) return true
      } catch (_) {}
      return false
    }

    // 1. Priority 1: User explicitly selected polygon(s) in multi-selection or sidebar list
    if (selectedPolyUiIds.value && selectedPolyUiIds.value.size > 0) {
      const selectedFeatures = features.value.filter(f => f && (selectedPolyUiIds.value.has(f._uiId) || selectedPolyUiIds.value.has(getFeatureUiId(f))))

      let bestSelFeat = null
      let bestSelScore = -1

      for (const sf of selectedFeatures) {
        if (testIntersects(sf)) {
          let score = 1
          if (cutGeom.type === 'LineString') {
            for (const pt of samplePoints) {
              try {
                if (turf.booleanPointInPolygon(pt, sf)) score += 10
              } catch (_) {}
            }
          } else {
            try {
              const inter = turf.intersect(turf.featureCollection([cutFeat, sf]))
              score = inter ? turf.area(inter) : 1
            } catch (_) {
              score = 1
            }
          }
          if (score > bestSelScore) {
            bestSelScore = score
            bestSelFeat = sf
          }
        }
      }

      if (bestSelFeat) {
        const annId = extractNumericId(bestSelFeat)
        return { feat: bestSelFeat, annId }
      }
    }

    // 2. Priority 2: User clicked a polygon on the map (clickedFeatureIdx)
    if (clickedFeatureIdx.value !== null && features.value[clickedFeatureIdx.value]) {
      const cf = features.value[clickedFeatureIdx.value]
      if (testIntersects(cf)) {
        let isRealTarget = false
        if (cutGeom.type === 'LineString') {
          for (const pt of samplePoints) {
            try {
              if (turf.booleanPointInPolygon(pt, cf)) {
                isRealTarget = true
                break
              }
            } catch (_) {}
          }
        } else {
          try {
            const inter = turf.intersect(turf.featureCollection([cutFeat, cf]))
            if (inter && turf.area(inter) > 0.05 * turf.area(cutFeat)) isRealTarget = true
          } catch (_) {}
        }
        if (isRealTarget) {
          const annId = extractNumericId(cf)
          return { feat: cf, annId }
        }
      }
    }

    // 3. Priority 3: Search all features, prioritizing polygon containing the body/interior of the blade
    let bestFeat = null
    let bestAnnId = null
    let maxIntersectionScore = -1

    for (const feat of features.value) {
      if (!feat || !feat.geometry) continue
      if (!testIntersects(feat)) continue

      const annId = extractNumericId(feat)

      if (cutGeom.type === 'LineString') {
        let pointsInside = 0
        for (const pt of samplePoints) {
          try {
            if (turf.booleanPointInPolygon(pt, feat)) {
              pointsInside++
            }
          } catch (_) {}
        }
        let count = 0
        try {
          const inter = turf.lineIntersect(cutFeat, feat)
          count = inter?.features?.length || 0
        } catch (_) {}

        // Heavily weight interior sample points (100x) over boundary intersections
        const score = (pointsInside * 100) + count

        if (score > maxIntersectionScore) {
          maxIntersectionScore = score
          bestFeat = feat
          bestAnnId = annId
        }
      } else {
        let score = 0
        try {
          const inter = turf.intersect(turf.featureCollection([cutFeat, feat]))
          score = inter ? turf.area(inter) : 0
        } catch (_) {
          score = 1
        }
        if (score > maxIntersectionScore) {
          maxIntersectionScore = score
          bestFeat = feat
          bestAnnId = annId
        }
      }
    }

    if (bestFeat) {
      return { feat: bestFeat, annId: bestAnnId }
    }
  } catch (_) {}

  return { feat: null, annId: null }
}

// Clean duplicate or micro-jitter coordinates from LineString (e.g. from mouse double-clicks)
const cleanLineCoordinates = (lineGeom) => {
  if (!lineGeom || !lineGeom.coordinates || lineGeom.coordinates.length < 2) return lineGeom
  const raw = lineGeom.coordinates
  const cleaned = [raw[0]]
  for (let i = 1; i < raw.length; i++) {
    const prev = cleaned[cleaned.length - 1]
    const curr = raw[i]
    const dist = Math.hypot(curr[0] - prev[0], curr[1] - prev[1])
    if (dist > 1e-6) {
      cleaned.push(curr)
    }
  }
  if (cleaned.length < 2 && raw.length >= 2) {
    cleaned.push(raw[raw.length - 1])
  }
  return {
    ...lineGeom,
    coordinates: cleaned
  }
}

// Handle Line Split
const handleSplitByLine = async (lineGeom) => {
  if (!selectedTaskId.value) return
  showToast('Memproses pemotongan garis...')

  // Detect target polygon under cut line
  const { feat: targetFeat, annId: targetAnnId } = findTargetPolygonForCut(lineGeom)

  // If user selected an active class, pass it so the new sliced piece receives it
  const targetClassId = annotationsStore.selectedClass?.id || 0

  try {
    const res = await api.splitByLine(selectedTaskId.value, lineGeom, targetAnnId, targetClassId)
    showToast(res.data?.message || 'Poligon berhasil dipotong!')
    if (res.data?.deleted_ids || res.data?.created_features) {
      applyDeltaUpdate(res.data.deleted_ids || [], res.data.created_features || [], res.data.updated_features || [])
      // Auto-select the newly created cut piece so user can see it and edit its class immediately
      if (res.data.created_features && res.data.created_features.length > 1) {
        const newSlice = res.data.created_features[1]
        const newSliceId = newSlice.id ?? newSlice.properties?.id
        const foundIdx = features.value.findIndex(f => (f.id ?? f.properties?.id) === newSliceId)
        if (foundIdx !== -1) {
          clickedFeatureIdx.value = foundIdx
        }
      }
    } else {
      await loadTaskData(selectedTaskId.value, true)
    }
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal memotong poligon. Pastikan garis melintasi batas poligon.')
  } finally {
    setDigitizeMode(null)
  }
}

// Handle Polygon Cut / Split
const handleSplitByPolygon = async (cuttingGeom) => {
  if (!selectedTaskId.value) return
  showToast('Memproses pemisahan area poligon...')

  const { feat: targetFeat, annId: targetAnnId } = findTargetPolygonForCut(cuttingGeom)
  // Use user's active class if selected (e.g. Semak & Belukar), so the cut cookie area is immediately assigned
  const targetClassId = annotationsStore.selectedClass?.id || 0

  try {
    const res = await api.splitByPolygon(selectedTaskId.value, cuttingGeom, targetAnnId, targetClassId)
    showToast(res.data?.message || 'Poligon berhasil dipisah menjadi bagian mandiri!')
    if (res.data?.deleted_ids || res.data?.created_features) {
      applyDeltaUpdate(res.data.deleted_ids || [], res.data.created_features || [], res.data.updated_features || [])
      // Auto-select the newly cut area piece
      if (res.data.created_features && res.data.created_features.length > 0) {
        const newFeat = res.data.created_features[res.data.created_features.length - 1]
        const newFeatId = newFeat.id ?? newFeat.properties?.id
        const foundIdx = features.value.findIndex(f => (f.id ?? f.properties?.id) === newFeatId)
        if (foundIdx !== -1) {
          clickedFeatureIdx.value = foundIdx
        }
      }
    } else {
      await loadTaskData(selectedTaskId.value, true)
    }
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal memotong area. Pastikan poligon pemotong beririsan dengan poligon target.')
  } finally {
    setDigitizeMode(null)
  }
}

// Clean turnaround spikes, collinear duplicate edges, and collapsed holes from GeoJSON Polygon
const cleanPolygonSpikesAndRings = (featureOrGeom) => {
  if (!featureOrGeom) return featureOrGeom
  let geom = featureOrGeom.geometry || featureOrGeom
  if (!geom || (geom.type !== 'Polygon' && geom.type !== 'MultiPolygon')) return featureOrGeom

  const cleanRing = (coords) => {
    if (!coords || coords.length < 3) return coords
    let ring = [...coords]

    // 1. Iterative turnaround spike removal (A -> B -> A)
    let changed = true
    let iterations = 0
    while (changed && ring.length > 3 && iterations < 8) {
      changed = false
      iterations++
      const n = ring.length - (ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1] ? 1 : 0)
      const toKeep = []
      for (let i = 0; i < n; i++) {
        const prev = ring[(i - 1 + n) % n]
        const curr = ring[i]
        const next = ring[(i + 1) % n]
        const dLng = Math.abs(prev[0] - next[0])
        const dLat = Math.abs(prev[1] - next[1])
        if (dLng < 1e-8 && dLat < 1e-8) {
          changed = true
          // Skip curr point because it's a spike back-and-forth
        } else {
          toKeep.push(curr)
        }
      }
      if (changed && toKeep.length >= 3) {
        toKeep.push([toKeep[0][0], toKeep[0][1]])
        ring = toKeep
      }
    }

    // 2. Strict closure enforcement
    if (ring.length >= 3) {
      const first = ring[0]
      const last = ring[ring.length - 1]
      if (first[0] !== last[0] || first[1] !== last[1]) {
        ring.push([first[0], first[1]])
      }
    }
    return ring
  }

  if (geom.type === 'Polygon') {
    const cleanedRings = []
    if (geom.coordinates && geom.coordinates.length > 0) {
      cleanedRings.push(cleanRing(geom.coordinates[0]))
      for (let h = 1; h < geom.coordinates.length; h++) {
        const holeRing = cleanRing(geom.coordinates[h])
        if (holeRing && holeRing.length >= 4) {
          try {
            const hArea = turf.area(turf.polygon([holeRing]))
            if (hArea > 0.05) {
              cleanedRings.push(holeRing)
            }
          } catch (_) {}
        }
      }
      geom.coordinates = cleanedRings
    }
  } else if (geom.type === 'MultiPolygon') {
    geom.coordinates = geom.coordinates.map(polyCoords => {
      return polyCoords.map(cleanRing)
    })
  }
  return featureOrGeom
}

// Handle Merge Polygons
const executeMerge = async () => {
  if (selectedForMerge.value.length < 2 || !selectedTaskId.value) return
  mergeLoading.value = true

  // Determine target class:
  // Priority:
  // 1. Explicitly chosen in dropdown (mergeTargetClassId)
  // 2. Class of the largest selected polygon
  // 3. Fallback to active class in store
  const chosenClassId = mergeTargetClassId.value 
    || largestMergePolygon.value?.properties?.class_id 
    || annotationsStore.selectedClass?.id 
    || 1
  const targetClass = annotationsStore.classes.find(c => c.id === chosenClassId)
  const targetClassId = targetClass?.id || chosenClassId
  const targetClassName = targetClass?.name || 'Tutupan Lahan'
  const targetColor = targetClass?.color || '#006400'

  const annotationIds = selectedForMerge.value.map(f => f.id || f.properties?.id).filter(Boolean)
  const selectedUiIds = new Set(selectedForMerge.value.map(f => f._uiId).filter(Boolean))
  const allAreDbIntegers = annotationIds.length === selectedForMerge.value.length &&
    annotationIds.every(id => Number.isInteger(Number(id)) && !String(id).includes('_'))

  try {
    // If backend integer IDs exist for all selected polygons, use backend merge API
    if (allAreDbIntegers) {
      const res = await api.mergePolygons(selectedTaskId.value, annotationIds.map(Number), targetClassId)
      showToast(res.data?.message || `Poligon berhasil digabungkan menjadi '${targetClassName}'!`)

      // Explicitly purge selected layers immediately from Leaflet map & memory
      featureGroup.eachLayer(l => {
        const lUiId = l._uiId || l.feature?._uiId
        const lId = l.feature?.id || l.feature?.properties?.id
        if ((lUiId && selectedUiIds.has(lUiId)) || (lId && annotationIds.map(String).includes(String(lId)))) {
          try {
            featureGroup.removeLayer(l)
            if (map && map.hasLayer(l)) map.removeLayer(l)
          } catch (_) {}
        }
      })

      if (res.data?.deleted_ids || res.data?.created_features) {
        applyDeltaUpdate(res.data.deleted_ids || [], res.data.created_features || [], res.data.updated_features || [])
      } else {
        await loadTaskData(selectedTaskId.value, true)
      }
    } else {
      // Fallback: merge using Turf client-side union
      const validPolys = selectedForMerge.value.map(f => {
        let p = f.type === 'Feature' ? f : turf.feature(f.geometry || f)
        return p
      })
      const fc = turf.featureCollection(validPolys)
      let unioned = turf.union(fc)

      // If union resulted in MultiPolygon, try micro-buffer bridge (~1.5 meters)
      if (unioned && unioned.geometry?.type === 'MultiPolygon') {
        try {
          const bufferedFc = turf.featureCollection(validPolys.map(p => turf.buffer(p, 0.0015, { units: 'kilometers' })))
          const bUnion = turf.union(bufferedFc)
          if (bUnion) {
            const deflated = turf.buffer(bUnion, -0.0015, { units: 'kilometers' })
            if (deflated && deflated.geometry?.type === 'Polygon') {
              unioned = deflated
            }
          }
        } catch (_) {}
      }

      if (!unioned || unioned.geometry?.type === 'MultiPolygon') {
        throw new Error('Poligon yang dipilih tidak bersebelahan atau tidak bersentuhan. Hanya poligon yang bersentuhan yang dapat digabungkan.')
      }
      unioned = cleanPolygonSpikesAndRings(unioned)

      unioned.properties = {
        class_id: targetClassId,
        class_name: targetClassName,
        color: targetColor
      }

      // Remove merged polygons from current features list
      const mergeUiIds = new Set(selectedForMerge.value.map(f => f._uiId || f.id || f.properties?.id))
      const remaining = features.value.filter(f => !mergeUiIds.has(f._uiId || f.id || f.properties?.id))
      
      const newFeaturesList = [...remaining, unioned]
      await annotationsStore.saveGridAnnotations(selectedTaskId.value, newFeaturesList)
      showToast(`Poligon berhasil digabungkan menjadi '${targetClassName}'!`)
      await loadTaskData(selectedTaskId.value, true)
    }
    selectedForMerge.value = []
    mergeTargetClassId.value = null
    activeTool.value = null
  } catch (err) {
    console.error('Merge error:', err)
    alert(err.response?.data?.detail || err.message || 'Gagal menggabungkan poligon.')
  } finally {
    mergeLoading.value = false
    refreshMapStyles()
  }
}

const cancelMerge = () => {
  selectedForMerge.value = []
  mergeTargetClassId.value = null
  activeTool.value = null
  refreshMapStyles()
}

const isHealingTopology = ref(false)
const enableLiveAutoClip = ref(false) // Controlled: default false so editing is smooth without unexpected clipping

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
  if (!selectedTaskId.value) {
    showToast('Pilih salah satu grid terlebih dahulu!')
    return
  }
  showRepairToolboxModal.value = true
}

const handleApplyRepairOptions = async () => {
  if (!selectedTaskId.value) return
  isApplyingRepairOptions.value = true
  try {
    const res = await api.autoHealTopology(selectedTaskId.value, repairOptions.value)
    showToast(res.data?.message || 'Pilihan perbaikan topologi berhasil diterapkan!')
    showRepairToolboxModal.value = false
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck()
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
  if (!selectedTaskId.value) {
    showToast('Pilih salah satu grid terlebih dahulu!')
    return
  }
  showHistoryModal.value = true
  loadingSnapshots.value = true
  try {
    const res = await api.getGridSnapshots(selectedTaskId.value)
    snapshotsList.value = res.data || []
  } catch (err) {
    console.error('Failed to load snapshots:', err)
    showToast('Gagal memuat riwayat versi.')
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
    await api.restoreGridSnapshot(selectedTaskId.value, snap.id)
    showToast(`✅ Berhasil memulihkan poligon ke versi v${snap.version_number}!`)
    showHistoryModal.value = false
    await loadTaskData(selectedTaskId.value, true)
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
  const featureA = features.value.find(f => (f.id || f.properties?.id) === idA)
  const featureB = features.value.find(f => (f.id || f.properties?.id) === idB)

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
  if (!selectedTaskId.value) return
  overlapModalData.value.isResolving = true
  try {
    const res = await api.resolveOverlap({
      task_grid_id: selectedTaskId.value,
      ann_id_a: overlapModalData.value.ann_a.id,
      ann_id_b: overlapModalData.value.ann_b.id,
      action: action,
      target_class_id: targetClassId
    })
    showToast(res.data?.message || 'Overlap berhasil diselesaikan!')
    showOverlapModal.value = false
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck()
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
    showToast(res.data?.message || `Geometri poligon #${annId} berhasil dirapikan!`)
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck()
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
    showToast(`Kelas poligon #${assignClassModalData.value.annotation_id} berhasil diubah!`)
    showAssignClassModal.value = false
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck()
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
  if (!selectedTaskId.value) return
  fillGapsModalData.value = {
    class_id: 1,
    min_gap_area_sqm: 1.0,
    isFilling: false
  }
  showFillGapsModal.value = true
}

const executeFillGaps = async () => {
  if (!selectedTaskId.value) return
  fillGapsModalData.value.isFilling = true
  try {
    const res = await api.fillGridGaps(
      selectedTaskId.value,
      fillGapsModalData.value.class_id,
      fillGapsModalData.value.min_gap_area_sqm
    )
    showToast(res.data?.message || 'Celah kosong berhasil diisi!')
    showFillGapsModal.value = false
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck()
  } catch (err) {
    console.error('Fill gaps error:', err)
    alert(err.response?.data?.detail || 'Gagal mengisi celah kosong.')
  } finally {
    fillGapsModalData.value.isFilling = false
  }
}

// Focus error on map with extreme zoom (< 50m)
const focusErrorPolygon = (err) => {
  if (!err) return
  activeTopologyError.value = err
  if (topologyResult.value?.errors) {
    const idx = topologyResult.value.errors.indexOf(err)
    if (idx !== -1) currentTopologyErrorIndex.value = idx
  }

  // Collect all annotation IDs from the error (single or multi)
  const targetIds = []
  if (err.annotation_id) targetIds.push(err.annotation_id)
  if (err.annotation_ids?.length) {
    err.annotation_ids.forEach(id => {
      if (!targetIds.includes(id)) targetIds.push(id)
    })
  }

  if (targetIds.length === 0 || !featureGroup || !map) {
    if (err.geometry && map) {
      try {
        const errLayer = L.geoJSON(err.geometry, {
          style: { color: '#FF0000', fillColor: '#EF4444', fillOpacity: 0.65, weight: 3, dashArray: '5, 5' }
        }).addTo(map)
        const errBounds = errLayer.getBounds()
        if (errBounds.isValid()) {
          map.flyToBounds(errBounds, { padding: [120, 120], maxZoom: 20, duration: 0.5 })
        }
        setTimeout(() => { if (map && errLayer) map.removeLayer(errLayer) }, 6000)
        showToast(`⚠️ Menyorot area: ${err.message || err.type}`)
        return
      } catch (_) {}
    }
    showToast('⚠️ Tidak ada ID poligon untuk disorot')
    return
  }

  const matchedLayers = []
  featureGroup.eachLayer(l => {
    const lid = l.feature?.id ?? l.feature?.properties?.id
    if (lid != null && targetIds.includes(lid)) {
      matchedLayers.push(l)
    }
  })

  if (matchedLayers.length === 0) {
    if (err.geometry && map) {
      try {
        const errLayer = L.geoJSON(err.geometry, {
          style: { color: '#FF0000', fillColor: '#EF4444', fillOpacity: 0.65, weight: 3, dashArray: '5, 5' }
        }).addTo(map)
        const errBounds = errLayer.getBounds()
        if (errBounds.isValid()) {
          map.flyToBounds(errBounds, { padding: [120, 120], maxZoom: 20, duration: 0.5 })
        }
        setTimeout(() => { if (map && errLayer) map.removeLayer(errLayer) }, 6000)
        showToast(`⚠️ Menyorot lokasi masalah: ${err.message}`)
        return
      } catch (_) {}
    }
    showToast(`⚠️ Poligon #${targetIds.join(', #')} tidak ditemukan di peta. Coba jalankan ulang Cek Topologi.`)
    return
  }

  // Build combined bounds from all matched layers
  let combinedBounds = null
  matchedLayers.forEach(layer => {
    if (layer.getBounds) {
      const b = layer.getBounds()
      combinedBounds = combinedBounds ? combinedBounds.extend(b) : b
    }
  })

  if (combinedBounds) {
    // Extreme close-up zoom < 50m (maxZoom: 20) with smooth flyToBounds
    map.flyToBounds(combinedBounds, { padding: [120, 120], maxZoom: 20, duration: 0.5 })
  }

  // Flash highlight effect on matched layers
  matchedLayers.forEach(layer => {
    const origStyle = layer.options ? { ...layer.options } : {}
    const origColor = origStyle.color || '#9CA3AF'
    const origFillColor = origStyle.fillColor || origColor
    const origFillOpacity = origStyle.fillOpacity ?? 0.4
    const origWeight = origStyle.weight ?? 2

    // Flash 3 times with bright red/yellow
    let flashCount = 0
    const flashInterval = setInterval(() => {
      if (flashCount % 2 === 0) {
        layer.setStyle({ color: '#FF0000', fillColor: '#FBBF24', fillOpacity: 0.7, weight: 4 })
      } else {
        layer.setStyle({ color: origColor, fillColor: origFillColor, fillOpacity: origFillOpacity, weight: origWeight })
      }
      flashCount++
      if (flashCount >= 6) {
        clearInterval(flashInterval)
        layer.setStyle({ color: origColor, fillColor: origFillColor, fillOpacity: origFillOpacity, weight: origWeight })
      }
    }, 250)
  })

  // Open popup on the first matched layer
  if (matchedLayers[0]?.openPopup) {
    matchedLayers[0].openPopup()
  }

  // Populate Topology Inspector data
  activeInspectorError.value = err
  activeInspectorBounds.value = combinedBounds
  inspectorPolygons.value = matchedLayers.map(l => {
    const feat = l.feature || l.toGeoJSON()
    const p = feat.properties || {}
    const cId = p.class_id
    const cls = annotationsStore.classes.find(c => c.id === cId)
    return {
      id: feat.id || p.id,
      properties: {
        ...p,
        class_name: p.class_name || cls?.name || 'Belum Terklasifikasi',
        color: p.color || cls?.color || '#9CA3AF',
        area_sqm: p.area_sqm || getPolygonArea(feat)
      }
    }
  })
  showTopologyInspector.value = false

  // Smooth scroll corresponding card in list
  nextTick(() => {
    const el = document.getElementById('studio-err-' + currentTopologyErrorIndex.value)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })

  showToast(`📍 Menyorot ${matchedLayers.length} poligon: #${targetIds.join(', #')} (Skala Detil < 50m)`)
}

const nextTopologyError = () => {
  if (!topologyResult.value?.errors?.length) return
  currentTopologyErrorIndex.value = (currentTopologyErrorIndex.value + 1) % topologyResult.value.errors.length
  focusErrorPolygon(topologyResult.value.errors[currentTopologyErrorIndex.value])
}

const prevTopologyError = () => {
  if (!topologyResult.value?.errors?.length) return
  currentTopologyErrorIndex.value = (currentTopologyErrorIndex.value - 1 + topologyResult.value.errors.length) % topologyResult.value.errors.length
  focusErrorPolygon(topologyResult.value.errors[currentTopologyErrorIndex.value])
}

const startDirectVertexEditForError = (err) => {
  if (!err) return
  focusErrorPolygon(err)
  const targetId = err.annotation_id || (err.annotation_ids?.[0])
  if (targetId) {
    setTimeout(() => {
      executeInspectorEdit(targetId)
    }, 250)
  }
}

// ════════════════════════════════════════════════════════════════════════
// DEDICATED TOPOLOGY SURGERY STUDIO METHODS (High Precision Workbench)
// ════════════════════════════════════════════════════════════════════════
const surgeryCurrentError = computed(() => {
  if (!topologyResult.value?.errors?.length) return null
  return topologyResult.value.errors[surgeryErrorIndex.value] || null
})

const openTopologySurgeryModal = () => {
  if (!topologyResult.value?.errors?.length) {
    showToast('Tidak ada masalah topologi terdeteksi.')
    return
  }
  showTopologySurgeryModal.value = true
  if (surgeryErrorIndex.value >= topologyResult.value.errors.length) {
    surgeryErrorIndex.value = 0
  }
  nextTick(() => {
    initSurgeryMap()
    // Give Leaflet container time to settle after modal transition animation
    setTimeout(() => {
      if (surgeryMapInstance) {
        surgeryMapInstance.invalidateSize()
        loadSurgeryError(surgeryErrorIndex.value)
      }
    }, 200)
  })
}

const closeTopologySurgeryModal = () => {
  showTopologySurgeryModal.value = false
  clearSurgeryVertexSelection()
  if (surgeryMapInstance) {
    surgeryMapInstance.remove()
    surgeryMapInstance = null
    surgeryLayerGroup = null
  }
  surgeryVertexModeActive.value = false
  surgeryVertexAction.value = 'drag'
  surgeryMultiSelectActive.value = false
  hasSurgeryVertexEdits.value = false
}

const initSurgeryMap = () => {
  const container = document.getElementById('topology-surgery-map-canvas')
  if (!container) return
  if (surgeryMapInstance) {
    surgeryMapInstance.remove()
    surgeryMapInstance = null
    surgeryLayerGroup = null
  }

  // Pre-calculate fallback center & zoom from task grid or main map so canvas is NEVER pitch black!
  const taskCenter = tasksStore.currentTask
    ? [(tasksStore.currentTask.min_lat + tasksStore.currentTask.max_lat) / 2, (tasksStore.currentTask.min_lon + tasksStore.currentTask.max_lon) / 2]
    : (map ? map.getCenter() : [-0.5, 100.5])
  const taskZoom = map ? Math.max(map.getZoom(), 17) : 18

  surgeryMapInstance = L.map('topology-surgery-map-canvas', {
    center: taskCenter,
    zoom: taskZoom,
    maxZoom: 24,
    minZoom: 2,
    zoomControl: true,
    attributionControl: false
  })

  // Google Satellite with tile overzooming
  const googleSat = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
  L.tileLayer(googleSat, {
    maxZoom: 24,
    maxNativeZoom: 20,
    attribution: 'Google Satellite'
  }).addTo(surgeryMapInstance)

  surgeryLayerGroup = L.featureGroup().addTo(surgeryMapInstance)

  // Clicking empty canvas deselects all vertices (QGIS / Figma style)
  surgeryMapInstance.on('click', () => {
    if (selectedSurgeryVertices.value.length > 0) {
      clearSurgeryVertexSelection()
    }
  })

  surgeryMapInstance.on('zoomend', () => {
    if (surgeryMapInstance) {
      surgeryCurrentZoom.value = surgeryMapInstance.getZoom()
    }
  })

  requestAnimationFrame(() => {
    if (surgeryMapInstance) {
      surgeryMapInstance.invalidateSize()
    }
  })
}
const refreshSurgeryState = () => {
  if (!topologyResult.value?.errors?.length) {
    closeTopologySurgeryModal()
    showToast('🎉 Semua masalah topologi telah terselesaikan!')
    return
  }
  surgeryErrorIndex.value = Math.min(surgeryErrorIndex.value, topologyResult.value.errors.length - 1)
  if (surgeryErrorIndex.value < 0) surgeryErrorIndex.value = 0
  loadSurgeryError(surgeryErrorIndex.value)
}

const loadSurgeryError = (idx) => {
  const container = document.getElementById('topology-surgery-map-canvas')
  if (!container) return

  // Ensure surgery map instance is alive and mounted to live container
  if (!surgeryMapInstance || !surgeryMapInstance._container || surgeryMapInstance._container !== container) {
    initSurgeryMap()
  }

  if (!surgeryMapInstance || !surgeryLayerGroup || !topologyResult.value?.errors?.length) return
  surgeryMapInstance.invalidateSize()
  surgeryLayerGroup.clearLayers()
  clearSurgeryVertexSelection()
  hasSurgeryVertexEdits.value = false
  surgeryVertexModeActive.value = false

  const err = topologyResult.value.errors[idx]
  if (!err) return

  let targetIds = []
  if (err.annotation_ids && Array.isArray(err.annotation_ids)) {
    targetIds = [...err.annotation_ids]
  } else if (err.annotation_id != null) {
    targetIds = [err.annotation_id]
  }

  surgeryInvolvedPolygons.value = []
  const layersToFit = []

  targetIds.forEach((polyId, pIndex) => {
    let geojson = null
    let cId = null

    // 1. Try finding in active Leaflet featureGroup
    if (featureGroup) {
      featureGroup.eachLayer(l => {
        const lid = l.feature?.id ?? l.feature?.properties?.id
        if (lid != null && String(lid) === String(polyId)) {
          geojson = l.toGeoJSON ? l.toGeoJSON() : l.feature
          cId = geojson?.properties?.class_id
        }
      })
    }

    // 2. Fallback: try finding in features store array
    if (!geojson && features.value) {
      const feat = features.value.find(f => String(f.id ?? f.properties?.id) === String(polyId))
      if (feat) {
        geojson = JSON.parse(JSON.stringify(feat))
        cId = geojson.properties?.class_id
      }
    }

    if (geojson) {
      const cls = annotationsStore.classes.find(c => c.id === cId)
      const color = pIndex === 0 ? '#F59E0B' : '#06B6D4'

      surgeryInvolvedPolygons.value.push({
        id: polyId,
        class_name: cls?.name || 'Poligon',
        color: cls?.color || color,
        area_sqm: getPolygonArea(geojson),
        geojson: geojson
      })

      const surgeryPoly = L.geoJSON(geojson, {
        style: {
          color: color,
          weight: 4,
          fillColor: color,
          fillOpacity: 0.45
        }
      }).addTo(surgeryLayerGroup)

      layersToFit.push(surgeryPoly)
    }
  })

  // Render error geometry if exists (overlap or gap highlight)
  if (err.geometry) {
    try {
      const errLayer = L.geoJSON(err.geometry, {
        style: {
          color: '#EF4444',
          weight: 4,
          fillColor: '#EF4444',
          fillOpacity: 0.65,
          dashArray: '5, 5'
        }
      }).addTo(surgeryLayerGroup)
      errLayer.bindTooltip(`⚠️ ${err.message || 'Area Masalah Topologi'}`, { sticky: true })
      layersToFit.push(errLayer)
    } catch (e) {
      console.warn('Could not draw error geometry:', e)
    }
  }

  if (layersToFit.length > 0) {
    const bounds = surgeryLayerGroup.getBounds()
    if (bounds.isValid()) {
      surgeryMapInstance.fitBounds(bounds, { padding: [90, 90], maxZoom: 22 })
      setTimeout(() => {
        if (surgeryMapInstance) {
          surgeryMapInstance.invalidateSize()
          surgeryCurrentZoom.value = surgeryMapInstance.getZoom()
        }
      }, 100)
    }
  } else {
    // Guaranteed fallback: If no specific polygon layers were found (e.g. general gap or sync delay),
    // center and fit to task grid bounds so map canvas is NEVER blank or pitch black!
    if (tasksStore.currentTask) {
      const t = tasksStore.currentTask
      surgeryMapInstance.fitBounds([[t.min_lat, t.min_lon], [t.max_lat, t.max_lon]], { padding: [40, 40] })
    } else if (map) {
      surgeryMapInstance.setView(map.getCenter(), Math.max(map.getZoom(), 17))
    }
    setTimeout(() => {
      if (surgeryMapInstance) {
        surgeryMapInstance.invalidateSize()
        surgeryCurrentZoom.value = surgeryMapInstance.getZoom()
      }
    }, 100)
  }

  if (surgeryInvolvedPolygons.value.length === 0 && topologyResult.value?.errors?.length && targetIds.length > 0) {
    // If features were still populating after save/reload, retry once
    setTimeout(() => {
      if (surgeryMapInstance && surgeryInvolvedPolygons.value.length === 0) {
        let retriedCount = 0
        targetIds.forEach((polyId, pIndex) => {
          let geojson = null
          let cId = null
          if (featureGroup) {
            featureGroup.eachLayer(l => {
              const lid = l.feature?.id ?? l.feature?.properties?.id
              if (lid != null && String(lid) === String(polyId)) {
                geojson = l.toGeoJSON ? l.toGeoJSON() : l.feature
                cId = geojson?.properties?.class_id
              }
            })
          }
          if (!geojson && features.value) {
            const feat = features.value.find(f => String(f.id ?? f.properties?.id) === String(polyId))
            if (feat) {
              geojson = JSON.parse(JSON.stringify(feat))
              cId = geojson.properties?.class_id
            }
          }
          if (geojson) {
            retriedCount++
            const cls = annotationsStore.classes.find(c => c.id === cId)
            const color = pIndex === 0 ? '#F59E0B' : '#06B6D4'
            surgeryInvolvedPolygons.value.push({
              id: polyId,
              class_name: cls?.name || 'Poligon',
              color: cls?.color || color,
              area_sqm: getPolygonArea(geojson),
              geojson: geojson
            })
            const surgeryPoly = L.geoJSON(geojson, {
              style: { color, weight: 4, fillColor: color, fillOpacity: 0.45 }
            }).addTo(surgeryLayerGroup)
            layersToFit.push(surgeryPoly)
          }
        })
        if (retriedCount > 0 && layersToFit.length > 0 && surgeryMapInstance) {
          const bounds = surgeryLayerGroup.getBounds()
          if (bounds.isValid()) {
            surgeryMapInstance.fitBounds(bounds, { padding: [90, 90], maxZoom: 22 })
          }
        }
      }
    }, 150)
  }
}

const onSurgeryLayerEdit = () => {
  hasSurgeryVertexEdits.value = true
}

const onSurgeryVertexRemoved = () => {
  hasSurgeryVertexEdits.value = true
  showToast('🗑️ Titik simpul berhasil dihapus. Jangan lupa klik "Simpan Perubahan Titik".')
}

// ─── TOPOLOGICAL EDITING & SHARED NODE HELPERS ─────────────
const enableTopologicalEditing = ref(true)

const extractPolygonRings = (layer) => {
  if (!layer || !layer.getLatLngs) return []
  const latlngs = layer.getLatLngs()
  if (!latlngs || !latlngs.length) return []
  const rings = []
  const traverse = (arr) => {
    if (!Array.isArray(arr) || !arr.length) return
    if (arr[0] && (arr[0].lat !== undefined || typeof arr[0].lat === 'number')) {
      rings.push(arr)
    } else {
      arr.forEach(sub => traverse(sub))
    }
  }
  traverse(latlngs)
  return rings
}

const getNormalizedLatLng = (p) => {
  if (!p) return null
  if (typeof p.lat === 'number' && typeof p.lng === 'number') {
    return { lat: p.lat, lng: p.lng }
  }
  if (Array.isArray(p) && p.length >= 2) {
    if (Math.abs(p[0]) > 60) {
      return { lat: Number(p[1]), lng: Number(p[0]) }
    }
    return { lat: Number(p[0]), lng: Number(p[1]) }
  }
  return null
}

const isCoincidentLatLng = (p1, p2, tolerance = 0.00003) => {
  const norm1 = getNormalizedLatLng(p1)
  const norm2 = getNormalizedLatLng(p2)
  if (!norm1 || !norm2) return false
  return Math.abs(norm1.lat - norm2.lat) <= tolerance && Math.abs(norm1.lng - norm2.lng) <= tolerance
}

const findSharedTopologicalNodes = (sourceLayer, pivotLatLng, searchGroup, tolerance = 0.00003) => {
  const shared = []
  if (!searchGroup || !pivotLatLng || !enableTopologicalEditing.value) return shared

  searchGroup.eachLayer(otherLyr => {
    if (otherLyr === sourceLayer || !otherLyr.getLatLngs) return
    const rings = extractPolygonRings(otherLyr)

    rings.forEach((ring) => {
      if (!Array.isArray(ring)) return
      ring.forEach((pt, ptIdx) => {
        if (isCoincidentLatLng(pt, pivotLatLng, tolerance)) {
          let otherMarker = null
          if (otherLyr.pm && otherLyr.pm._markerGroup) {
            otherLyr.pm._markerGroup.eachLayer(m => {
              if (isCornerVertexMarker(m) && isCoincidentLatLng(m.getLatLng(), pivotLatLng, tolerance)) {
                otherMarker = m
              }
            })
          }
          shared.push({
            layer: otherLyr,
            ring,
            index: ptIdx,
            startLat: pt.lat,
            startLng: pt.lng,
            marker: otherMarker
          })
        }
      })
    })
  })
  return shared
}

const isCornerVertexMarker = (m) => {
  if (!m || !m.options) return false
  if (m.leftM && m.rightM) return false
  const className = m.options.icon?.options?.className || ''
  return !className.includes('marker-icon-middle')
}

const toggleSurgeryMultiSelect = () => {
  surgeryMultiSelectActive.value = !surgeryMultiSelectActive.value
  if (surgeryMultiSelectActive.value) {
    if (!surgeryVertexModeActive.value) {
      surgeryVertexModeActive.value = true
      applySurgeryVertexMode()
    }
    showToast('🖱️ Shift Aktif: Klik beberapa titik simpul untuk memilihnya, tarik untuk menggeser bersamaan, atau tekan Delete.')
  } else {
    showToast('Shift dinonaktifkan. Anda tetap bisa tahan tombol Shift di keyboard untuk memilih banyak titik.')
  }
}

const getCoordsRingForMarker = (layer, marker) => {
  const coords = layer.getLatLngs()
  if (!layer.pm || !layer.pm._markers) {
    if (Array.isArray(coords[0])) return { ring: coords[0], parentPath: [0], index: -1 }
    return { ring: coords, parentPath: [], index: -1 }
  }
  const found = L.PM.Utils.findDeepMarkerIndex(layer.pm._markers, marker)
  if (!found || !found.indexPath) {
    if (Array.isArray(coords[0])) return { ring: coords[0], parentPath: [0], index: -1 }
    return { ring: coords, parentPath: [], index: -1 }
  }
  let current = coords
  for (let i = 0; i < found.parentPath.length; i++) {
    current = current[found.parentPath[i]]
  }
  return { ring: current, parentPath: found.parentPath, index: found.index }
}

const refreshSurgeryVertexMarkerStyles = () => {
  if (!surgeryLayerGroup) return
  surgeryLayerGroup.eachLayer(layer => {
    const processLayer = (target) => {
      if (!target.pm || !target.pm._markerGroup) return
      target.pm._markerGroup.eachLayer(marker => {
        if (!isCornerVertexMarker(marker)) return
        const isSelected = selectedSurgeryVertices.value.some(
          item => item.marker === marker || (item.marker?._leaflet_id && item.marker._leaflet_id === marker._leaflet_id)
        )
        if (marker._icon) {
          if (isSelected) {
            marker._icon.classList.add('selected-vertex-marker')
          } else {
            marker._icon.classList.remove('selected-vertex-marker')
          }
        }
      })
    }
    if (layer.eachLayer) layer.eachLayer(processLayer)
    else processLayer(layer)
  })
}

const clearSurgeryVertexSelection = () => {
  selectedSurgeryVertices.value.forEach(item => {
    if (item.marker?._icon) {
      item.marker._icon.classList.remove('selected-vertex-marker')
    }
  })
  selectedSurgeryVertices.value = []
}

const toggleSurgeryVertexSelection = (target, marker) => {
  const existingIdx = selectedSurgeryVertices.value.findIndex(
    item => item.marker === marker || (item.marker?._leaflet_id && item.marker._leaflet_id === marker._leaflet_id)
  )

  if (existingIdx >= 0) {
    selectedSurgeryVertices.value.splice(existingIdx, 1)
    if (marker._icon) {
      marker._icon.classList.remove('selected-vertex-marker')
    }
  } else {
    selectedSurgeryVertices.value.push({
      marker,
      layer: target,
      latlng: marker.getLatLng()
    })
    if (marker._icon) {
      marker._icon.classList.add('selected-vertex-marker')
    }
  }
}

let surgeryDragPivot = null
let surgeryDragStartPos = null
let surgeryDragInitialItems = []
let surgerySharedNodes = []
let surgeryIsDragging = false

const attachSurgeryVertexSelectionListeners = (target) => {
  if (!target.pm || !target.pm._markerGroup) return

  target.pm._markerGroup.eachLayer(m => {
    if (!isCornerVertexMarker(m)) return
    if (m._surgeryEventsAttached) return
    m._surgeryEventsAttached = true

    // Track drag events for multi-vertex move (QGIS / Figma / ArcGIS style)
    m.on('dragstart', () => {
      surgeryIsDragging = true
      surgeryDragPivot = m
      surgeryDragStartPos = m.getLatLng()

      // If dragged marker is not already in selection, select it
      const isInSelection = selectedSurgeryVertices.value.some(
        item => item.marker === m || (item.marker?._leaflet_id && item.marker._leaflet_id === m._leaflet_id)
      )

      if (!isInSelection) {
        clearSurgeryVertexSelection()
        selectedSurgeryVertices.value.push({
          marker: m,
          layer: target,
          latlng: m.getLatLng()
        })
        if (m._icon) m._icon.classList.add('selected-vertex-marker')
      }

      // Record snapshot of all selected vertices and their ring coordinates
      surgeryDragInitialItems = selectedSurgeryVertices.value.map(item => {
        const { ring, index } = getCoordsRingForMarker(item.layer, item.marker)
        const pos = item.marker.getLatLng()
        return {
          marker: item.marker,
          layer: item.layer,
          startLat: pos.lat,
          startLng: pos.lng,
          ring,
          index
        }
      })

      // Also find and link coincident shared nodes in other layers of surgeryLayerGroup (Topological Editing)
      surgerySharedNodes = []
      if (enableTopologicalEditing.value && surgeryLayerGroup) {
        const verticesToCheck = selectedSurgeryVertices.value.length > 0
          ? selectedSurgeryVertices.value
          : [{ layer: target, marker: m }]

        verticesToCheck.forEach(sel => {
          const found = findSharedTopologicalNodes(sel.layer, sel.marker.getLatLng(), surgeryLayerGroup)
          found.forEach(fn => {
            if (!surgerySharedNodes.some(sn => sn.layer === fn.layer && sn.index === fn.index)) {
              surgerySharedNodes.push(fn)
            }
          })
        })
      }
    })

    m.on('drag', () => {
      if (!surgeryIsDragging || !surgeryDragStartPos) {
        return
      }

      const currentPos = m.getLatLng()
      const dLat = currentPos.lat - surgeryDragStartPos.lat
      const dLng = currentPos.lng - surgeryDragStartPos.lng

      // Shift other selected markers simultaneously
      if (surgeryDragInitialItems.length > 1) {
        surgeryDragInitialItems.forEach(item => {
          if (item.marker !== m) {
            const newLat = item.startLat + dLat
            const newLng = item.startLng + dLng
            item.marker.setLatLng([newLat, newLng])

            // Update coordinate in polygon ring
            if (item.ring && item.index >= 0 && item.index < item.ring.length) {
              item.ring[item.index].lat = newLat
              item.ring[item.index].lng = newLng
              item.layer.redraw?.()
            }
          }
        })
      }

      // Shift topological shared nodes in adjacent polygon layers simultaneously
      if (surgerySharedNodes.length > 0) {
        surgerySharedNodes.forEach(item => {
          const newLat = item.startLat + dLat
          const newLng = item.startLng + dLng
          if (item.ring && item.index >= 0 && item.index < item.ring.length) {
            item.ring[item.index].lat = newLat
            item.ring[item.index].lng = newLng
            item.layer.redraw?.()
          }
          if (item.marker && item.marker !== m) {
            item.marker.setLatLng([newLat, newLng])
          }
        })
      }
    })

    m.on('dragend', () => {
      surgeryIsDragging = false
      hasSurgeryVertexEdits.value = true

      // Refresh Geoman markers and redraw cleanly across all affected layers
      const affectedLayers = new Set([
        ...surgeryDragInitialItems.map(it => it.layer),
        ...surgerySharedNodes.map(it => it.layer)
      ])

      setTimeout(() => {
        affectedLayers.forEach(l => {
          l.redraw?.()
          if (l.pm && typeof l.pm._initMarkers === 'function') {
            l.pm._initMarkers()
            attachSurgeryVertexSelectionListeners(l)
          }
        })
        refreshSurgeryVertexMarkerStyles()
      }, 10)

      surgeryDragPivot = null
      surgeryDragStartPos = null
      surgeryDragInitialItems = []
      surgerySharedNodes = []
    })

    m.on('click', (e) => {
      if (surgeryIsDragging) return
      L.DomEvent.stopPropagation(e)

      const isShift = !!e.originalEvent?.shiftKey || surgeryMultiSelectActive.value
      if (isShift) {
        // Toggle selection (QGIS / Figma Shift-Click)
        toggleSurgeryVertexSelection(target, m)
      } else {
        // Single selection (QGIS / Figma Click)
        const isAlreadyOnlySelected = selectedSurgeryVertices.value.length === 1 &&
          (selectedSurgeryVertices.value[0].marker === m || selectedSurgeryVertices.value[0].marker?._leaflet_id === m._leaflet_id)

        clearSurgeryVertexSelection()

        if (!isAlreadyOnlySelected) {
          selectedSurgeryVertices.value.push({
            marker: m,
            layer: target,
            latlng: m.getLatLng()
          })
          if (m._icon) m._icon.classList.add('selected-vertex-marker')
        }
      }
    })
  })
}

const deleteSelectedSurgeryVertices = () => {
  if (!selectedSurgeryVertices.value.length || !surgeryLayerGroup) return
  const totalCount = selectedSurgeryVertices.value.length

  // Group selected markers by polygon layer
  const layerMap = new Map()
  selectedSurgeryVertices.value.forEach(item => {
    if (!layerMap.has(item.layer)) layerMap.set(item.layer, [])
    layerMap.get(item.layer).push(item.marker)
  })

  // Validate that each polygon retains at least 3 vertices
  for (const [layer, markers] of layerMap.entries()) {
    const sampleMarker = markers[0]
    const { ring } = getCoordsRingForMarker(layer, sampleMarker)
    if (ring && ring.length - markers.length < 3) {
      showToast(`⚠️ Poligon harus memiliki minimal 3 titik sudut. Tidak dapat menghapus ${markers.length} dari ${ring.length} titik.`)
      return
    }
  }

  // Perform clean deletion using descending index splicing (rock-solid, no Geoman middle-marker conflict)
  let totalDeleted = 0
  for (const [layer, markers] of layerMap.entries()) {
    const indicesToDelete = []

    markers.forEach(m => {
      const { index } = getCoordsRingForMarker(layer, m)
      if (index >= 0) {
        indicesToDelete.push(index)
      }
    })

    // Sort descending so splicing earlier indices doesn't affect later indices
    indicesToDelete.sort((a, b) => b - a)
    const uniqueIndices = [...new Set(indicesToDelete)]

    if (uniqueIndices.length > 0) {
      const sampleMarker = markers[0]
      const { ring } = getCoordsRingForMarker(layer, sampleMarker)

      if (ring) {
        uniqueIndices.forEach(idx => {
          if (idx >= 0 && idx < ring.length) {
            ring.splice(idx, 1)
            totalDeleted++
          }
        })

        // Redraw polygon with new coordinates
        layer.redraw?.()
        if (layer.pm && typeof layer.pm._initMarkers === 'function') {
          layer.pm._initMarkers()
        }
        attachSurgeryVertexSelectionListeners(layer)
      }
    }
  }

  clearSurgeryVertexSelection()
  hasSurgeryVertexEdits.value = true
  showToast(`🗑️ ${totalDeleted || totalCount} titik simpul berhasil dihapus. Tekan "Simpan Perubahan Titik" untuk menerapkan.`)
}

const applySurgeryVertexMode = () => {
  if (!surgeryMapInstance || !surgeryLayerGroup) return

  surgeryLayerGroup.eachLayer(layer => {
    const applyToLayer = (target) => {
      if (!target.pm) return
      if (!surgeryVertexModeActive.value) {
        target.pm.disable()
        return
      }

      // Unified QGIS/Figma vertex editing tool:
      // Dragging moves points freely without snapping back, right-click also deletes single point
      target.pm.enable({
        snappable: true,
        snapDistance: 20,
        snapSegment: true,
        snapVertex: true,
        snapMiddleMarkers: false,
        allowSelfIntersection: true,
        preventMarkerRemoval: false,
        removeVertexOn: 'contextmenu'
      })

      attachSurgeryVertexSelectionListeners(target)

      target.off('pm:edit', onSurgeryLayerEdit)
      target.off('pm:dragend', onSurgeryLayerEdit)
      target.off('pm:vertexremoved', onSurgeryVertexRemoved)

      target.on('pm:edit', () => {
        onSurgeryLayerEdit()
        setTimeout(() => attachSurgeryVertexSelectionListeners(target), 50)
      })
      target.on('pm:dragend', onSurgeryLayerEdit)
      target.on('pm:vertexadded', () => {
        onSurgeryLayerEdit()
        setTimeout(() => attachSurgeryVertexSelectionListeners(target), 50)
      })
      target.on('pm:vertexremoved', () => {
        onSurgeryVertexRemoved()
        setTimeout(() => attachSurgeryVertexSelectionListeners(target), 50)
      })
    }

    if (layer.eachLayer) {
      layer.eachLayer(sl => applyToLayer(sl))
    } else {
      applyToLayer(layer)
    }
  })
}

const toggleSurgeryVertexEdit = () => {
  if (!surgeryMapInstance || !surgeryLayerGroup) return
  surgeryVertexModeActive.value = !surgeryVertexModeActive.value
  if (!surgeryVertexModeActive.value) {
    clearSurgeryVertexSelection()
  }
  applySurgeryVertexMode()
  if (surgeryVertexModeActive.value) {
    showToast('✏️ Edit Simpul Aktif (Mode QGIS/Figma): Klik titik untuk memilih, Shift untuk banyak titik, atau tarik untuk menggeser.')
  }
}

const cancelSurgeryVertexEdits = () => {
  hasSurgeryVertexEdits.value = false
  clearSurgeryVertexSelection()
  loadSurgeryError(surgeryErrorIndex.value)
  showToast('Perubahan titik simpul dibatalkan.')
}

const saveSurgeryVertexEdits = async () => {
  if (!surgeryLayerGroup || !selectedTaskId.value) return
  surgeryIsProcessing.value = true
  try {
    const layers = []
    surgeryLayerGroup.eachLayer(l => {
      if (l.eachLayer) {
        l.eachLayer(sl => layers.push(sl))
      } else {
        layers.push(l)
      }
    })

    layers.forEach(sLayer => {
      const polyId = sLayer.feature?.id ?? sLayer.feature?.properties?.id
      if (polyId && sLayer.getLatLngs && featureGroup) {
        featureGroup.eachLayer(mLayer => {
          const mid = mLayer.feature?.id ?? mLayer.feature?.properties?.id
          if (mid === polyId && mLayer.setLatLngs) {
            mLayer.setLatLngs(sLayer.getLatLngs())
            mLayer.redraw?.()
          }
        })
      }
    })

    await saveAnnotations()
    showToast('✅ Koordinat simpul poligon berhasil diperbarui!')
    hasSurgeryVertexEdits.value = false
    surgeryVertexModeActive.value = false

    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck(false)
    refreshSurgeryState()
  } catch (err) {
    console.error('Failed to save vertex edits:', err)
    showToast('Gagal menyimpan perubahan titik.')
  } finally {
    surgeryIsProcessing.value = false
  }
}

const executeSurgeryClip = async (action) => {
  if (!selectedTaskId.value || surgeryInvolvedPolygons.value.length < 2) return
  surgeryIsProcessing.value = true
  const idA = surgeryInvolvedPolygons.value[0].id
  const idB = surgeryInvolvedPolygons.value[1].id

  try {
    const res = await api.resolveOverlap({
      task_grid_id: selectedTaskId.value,
      ann_id_a: idA,
      ann_id_b: idB,
      action: action
    })
    showToast(res.data?.message || 'Overlap berhasil dipotong!')
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck(false)
    refreshSurgeryState()
  } catch (err) {
    console.error('Surgery clip error:', err)
    alert(err.response?.data?.detail || 'Gagal memotong overlap.')
  } finally {
    surgeryIsProcessing.value = false
  }
}

const executeSurgeryMerge = async () => {
  if (!selectedTaskId.value || surgeryInvolvedPolygons.value.length < 2) return
  surgeryIsProcessing.value = true
  const ids = surgeryInvolvedPolygons.value.map(p => p.id)
  const targetClassId = surgeryInvolvedPolygons.value[0].geojson?.properties?.class_id || annotationsStore.classes[0]?.id

  try {
    const res = await api.mergePolygons(selectedTaskId.value, ids, targetClassId)
    showToast(res.data?.message || 'Poligon berhasil digabungkan!')
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck(false)
    refreshSurgeryState()
  } catch (err) {
    console.error('Surgery merge error:', err)
    alert(err.response?.data?.detail || 'Gagal menggabungkan poligon.')
  } finally {
    surgeryIsProcessing.value = false
  }
}

const executeSurgeryHeal = async () => {
  const err = surgeryCurrentError.value
  const targetId = err?.annotation_id || err?.annotation_ids?.[0]
  if (!targetId || !selectedTaskId.value) return
  surgeryIsProcessing.value = true

  try {
    await handleRepairSingleGeometry(targetId)
    showToast('Geometri poligon berhasil dirapikan!')
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck(false)
    refreshSurgeryState()
  } catch (healErr) {
    console.error('Surgery heal error:', healErr)
    alert('Gagal merapikan geometri.')
  } finally {
    surgeryIsProcessing.value = false
  }
}

const executeSurgeryDelete = async (polyId) => {
  if (!polyId || !selectedTaskId.value) return
  if (!confirm(`Hapus poligon #${polyId} dari database?`)) return
  surgeryIsProcessing.value = true

  try {
    await api.deleteAnnotation(polyId)
    showToast(`Poligon #${polyId} berhasil dihapus.`)
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck(false)
    refreshSurgeryState()
  } catch (err) {
    console.error('Surgery delete error:', err)
    alert('Gagal menghapus poligon.')
  } finally {
    surgeryIsProcessing.value = false
  }
}

const nextSurgeryError = () => {
  if (!topologyResult.value?.errors?.length) return
  surgeryErrorIndex.value = (surgeryErrorIndex.value + 1) % topologyResult.value.errors.length
  loadSurgeryError(surgeryErrorIndex.value)
}

const prevSurgeryError = () => {
  if (!topologyResult.value?.errors?.length) return
  surgeryErrorIndex.value = (surgeryErrorIndex.value - 1 + topologyResult.value.errors.length) % topologyResult.value.errors.length
  loadSurgeryError(surgeryErrorIndex.value)
}

const resetSurgeryZoom = () => {
  if (surgeryMapInstance && surgeryLayerGroup) {
    const bounds = surgeryLayerGroup.getBounds()
    if (bounds.isValid()) {
      surgeryMapInstance.fitBounds(bounds, { padding: [80, 80], maxZoom: 22 })
      surgeryCurrentZoom.value = surgeryMapInstance.getZoom()
    }
  }
}

const handleAutoHealRemaining = async () => {
  if (!selectedTaskId.value) return
  surgeryIsProcessing.value = true
  try {
    await handleAutoHeal()
    if (topologyResult.value?.errors?.length) {
      surgeryErrorIndex.value = 0
      loadSurgeryError(0)
    } else {
      closeTopologySurgeryModal()
    }
  } finally {
    surgeryIsProcessing.value = false
  }
}

const executeInspectorEdit = (targetIdParam = null) => {
  const targetId = targetIdParam || inspectorPolygons.value[0]?.id || inspectorPolygons.value[0]?.properties?.id
  if (!targetId || !featureGroup || !map) {
    setDigitizeMode('edit')
    return
  }
  let targetLayer = null
  featureGroup.eachLayer(l => {
    const lid = l.feature?.id ?? l.feature?.properties?.id
    if (lid === targetId) targetLayer = l
  })
  if (targetLayer && targetLayer.pm) {
    map.pm.disableGlobalEditMode()
    targetLayer.pm.enable({
      snappable: true,
      snapDistance: 20,
      snapSegment: true,
      snapVertex: true,
      snapMiddleMarkers: false,
      allowSelfIntersection: true
    })
    targetLayer.bringToFront()
    activeTool.value = 'edit'
    showToast(`✏️ Mode Edit Titik aktif untuk Poligon #${targetId}. Geser titik untuk memperbaiki, lalu klik Simpan / Selesai Edit.`)
  } else {
    setDigitizeMode('edit')
  }
}

const closeAndFinishVertexEdit = () => {
  if (!map) return
  if (featureGroup) {
    featureGroup.eachLayer(l => {
      if (l.pm && l.pm.enabled()) {
        l.pm.disable()
        if (l.getLatLngs) {
          try {
            const latlngs = l.getLatLngs()
            if (Array.isArray(latlngs) && latlngs[0] && Array.isArray(latlngs[0])) {
              const ring = latlngs[0]
              // If duplicate closing point exists, remove it so ring remains clean Leaflet polygon
              if (ring.length > 3) {
                const first = ring[0]
                const last = ring[ring.length - 1]
                if (Math.abs(first.lat - last.lat) < 1e-7 && Math.abs(first.lng - last.lng) < 1e-7) {
                  ring.pop()
                  l.setLatLngs([ring])
                }
              }
            }
          } catch (_) {}
        }
        l.redraw?.()
      }
    })
  }
  if (map.pm) {
    map.pm.disableGlobalEditMode()
  }
  activeTool.value = null
  syncFeaturesFromMap()
  pushHistory()
  showToast('✓ Edit titik simpul selesai dan poligon tertutup rapat.')
}

const isCleaningSlivers = ref(false)

const handleCleanSlivers = async () => {
  if (!selectedTaskId.value) return
  if (!confirm('Bersihkan dan serap semua sliver garis/pita tipis pada grid ini ke poligon tetangganya?')) return

  isCleaningSlivers.value = true
  try {
    const res = await api.cleanSlivers(selectedTaskId.value)
    showToast(res.data?.message || 'Sliver garis berhasil diserap!')
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck()
  } catch (err) {
    console.error('Clean slivers error:', err)
    alert(err.response?.data?.detail || 'Gagal membersihkan sliver.')
  } finally {
    isCleaningSlivers.value = false
  }
}

const handleAutoHeal = async () => {
  if (!selectedTaskId.value) return
  if (!confirm('Rapikan geometri grid ini? Sistem akan menggunakan konfigurasi perbaikan cepat standar.')) return

  isHealingTopology.value = true
  try {
    const res = await api.autoHealTopology(selectedTaskId.value)
    showToast(res.data?.message || 'Geometri poligon berhasil dirapikan!')
    await loadTaskData(selectedTaskId.value, true)
    await runTopologyCheck()
  } catch (err) {
    console.error('Auto heal error:', err)
    alert(err.response?.data?.detail || 'Gagal merapikan geometri.')
  } finally {
    isHealingTopology.value = false
  }
}

// ─── TOPOLOGICAL AUTO-CLIP & AUTO-HEAL ON EDIT ───────────
let isAutoClipping = false
let debouncedEditTimer = null

const cleanSliversFromGeometry = (geom) => {
  if (!geom) return null
  const MIN_AREA_SQM = 3.0 // 3 m2 threshold (discard micro sliver artifacts)

  if (geom.type === 'Polygon') {
    try {
      const p = turf.polygon(geom.coordinates)
      if (turf.area(p) < MIN_AREA_SQM) return null
      return geom
    } catch (_) {
      return null
    }
  }

  if (geom.type === 'MultiPolygon') {
    const validPolys = []
    for (const polyCoords of geom.coordinates) {
      try {
        const p = turf.polygon(polyCoords)
        if (turf.area(p) >= MIN_AREA_SQM) {
          validPolys.push(polyCoords)
        }
      } catch (_) {}
    }
    if (validPolys.length === 0) return null
    if (validPolys.length === 1) {
      return { type: 'Polygon', coordinates: validPolys[0] }
    }
    return { type: 'MultiPolygon', coordinates: validPolys }
  }
  return geom
}

const updateLayerGeometry = (layer, geom) => {
  if (!layer || !geom) return
  const cleanedGeom = cleanSliversFromGeometry(geom)
  if (!cleanedGeom) return
  const isMulti = cleanedGeom.type === 'MultiPolygon'
  const latlngs = L.GeoJSON.coordsToLatLngs(cleanedGeom.coordinates, isMulti ? 2 : 1)
  layer.setLatLngs(latlngs)
  if (!layer.feature) {
    layer.feature = layer.toGeoJSON()
  }
  layer.feature.geometry = JSON.parse(JSON.stringify(cleanedGeom))
  try {
    layer.feature.properties.area_sqm = turf.area(turf.feature(cleanedGeom))
  } catch (_) {}
  layer.redraw?.()
}

const applyAutoClipAndHealOnEdit = (editedLayer) => {
  if (!enableLiveAutoClip.value && !enableTopologicalEditing.value) {
    // When both live auto-clip and topological editing are disabled, sync geometry safely
    syncFeaturesFromMap()
    pushHistory()
    return
  }
  if (isAutoClipping || !editedLayer || !featureGroup) return
  isAutoClipping = true

  try {
    let newFeat = editedLayer.toGeoJSON()
    if (!newFeat || !newFeat.geometry) return

    try {
      newFeat = turf.cleanCoords(newFeat)
    } catch (_) {}

    // Ensure edited polygon coordinates are strictly closed
    if (newFeat.geometry && newFeat.geometry.type === 'Polygon' && newFeat.geometry.coordinates?.[0]?.length >= 3) {
      const ring = newFeat.geometry.coordinates[0]
      const first = ring[0]
      const last = ring[ring.length - 1]
      if (first[0] !== last[0] || first[1] !== last[1]) {
        ring.push([first[0], first[1]])
      }
    }

    const editedUiId = editedLayer._uiId || editedLayer.feature?._uiId
    const oldGeom = editedLayer._preEditGeom || features.value.find(f => (f._uiId || f.id) === editedUiId)?.geometry

    let oldPoly = null
    if (oldGeom) {
      try {
        oldPoly = turf.cleanCoords(turf.feature(oldGeom))
      } catch (_) {}
    }
    const newPoly = turf.cleanCoords(turf.feature(newFeat.geometry))

    let anyModified = false
    const layersToRemove = []

    const editedBounds = editedLayer.getBounds ? editedLayer.getBounds() : null

    // 1. AUTO-CLIP OVERLAPS:
    // When edited polygon expands over neighbor, clip that neighbor: neighbor = neighbor - newPoly
    featureGroup.eachLayer((neighborLayer) => {
      if (neighborLayer === editedLayer) return
      const neighborUiId = neighborLayer._uiId || neighborLayer.feature?._uiId
      if (neighborUiId && neighborUiId === editedUiId) return

      // Ultra-fast bounding box pre-check to eliminate 95% of distant polygons instantly
      if (neighborLayer.getBounds && editedBounds) {
        const nB = neighborLayer.getBounds()
        if (nB && !nB.intersects(editedBounds)) {
          return
        }
      }

      const nFeat = neighborLayer.toGeoJSON()
      if (!nFeat || !nFeat.geometry) return
      let nPoly = null
      try {
        nPoly = turf.cleanCoords(turf.feature(nFeat.geometry))
      } catch (_) {
        return
      }

      try {
        if (turf.booleanIntersects(nPoly, newPoly)) {
          const inter = turf.intersect(turf.featureCollection([nPoly, newPoly]))
          if (inter && turf.area(inter) > 0.05) {
            const clipped = turf.difference(turf.featureCollection([nPoly, newPoly]))
            if (clipped && clipped.geometry && turf.area(clipped) > 3.0) {
              updateLayerGeometry(neighborLayer, clipped.geometry)
              anyModified = true
            } else {
              layersToRemove.push(neighborLayer)
              anyModified = true
            }
          }
        }
      } catch (clipErr) {
        console.warn('Auto-clip error on neighbor:', clipErr)
      }
    })

    layersToRemove.forEach(l => featureGroup.removeLayer(l))

    // 2. AUTO-HEAL VOID / GAP (Anti-Bolong):
    // When edited polygon shrinks/moves away, vacated area is absorbed by adjacent neighbor
    if (oldPoly) {
      try {
        const vacated = turf.difference(turf.featureCollection([oldPoly, newPoly]))
        if (vacated && vacated.geometry && turf.area(vacated) > 3.0) {
          let bestNeighbor = null
          let maxShared = -1

          const vacatedBounds = editedBounds ? editedBounds.pad(0.08) : null

          featureGroup.eachLayer((neighborLayer) => {
            if (neighborLayer === editedLayer || layersToRemove.includes(neighborLayer)) return

            // Ultra-fast bounding box pre-check
            if (neighborLayer.getBounds && vacatedBounds) {
              const nB = neighborLayer.getBounds()
              if (nB && !nB.intersects(vacatedBounds)) {
                return
              }
            }

            const nFeat = neighborLayer.toGeoJSON()
            if (!nFeat || !nFeat.geometry) return
            let nPoly = null
            try {
              nPoly = turf.cleanCoords(turf.feature(nFeat.geometry))
            } catch (_) {
              return
            }

            try {
              if (turf.booleanIntersects(vacated, nPoly) || turf.booleanTouches(vacated, nPoly)) {
                const buffered = turf.buffer(vacated, 0.000005, { units: 'kilometers' })
                if (buffered && turf.booleanIntersects(buffered, nPoly)) {
                  const inter = turf.intersect(turf.featureCollection([buffered, nPoly]))
                  const score = inter ? turf.area(inter) : 0
                  if (score > maxShared) {
                    maxShared = score
                    bestNeighbor = neighborLayer
                  }
                }
              }
            } catch (_) {}
          })

          if (bestNeighbor) {
            const bFeat = bestNeighbor.toGeoJSON()
            const bPoly = turf.cleanCoords(turf.feature(bFeat.geometry))
            const healed = turf.union(turf.featureCollection([bPoly, vacated]))
            if (healed && healed.geometry) {
              updateLayerGeometry(bestNeighbor, healed.geometry)
              anyModified = true
            }
          }
        }
      } catch (healErr) {
        console.warn('Auto-heal void error:', healErr)
      }
    }

    // Set new baseline geometry
    editedLayer._preEditGeom = JSON.parse(JSON.stringify(newFeat.geometry))

    // Sync features and push undo snapshot
    syncFeaturesFromMap()
    pushHistory()

    if (anyModified) {
      showToast('Penyesuaian batas otomatis diterapkan (Bebas Tumpang Tindih)')
    }
  } catch (err) {
    console.error('applyAutoClipAndHealOnEdit error:', err)
  } finally {
    isAutoClipping = false
  }
}

// ─── INTERACTIVE POPUP & LAYER EVENTS ─────────────────────
const bindLayerEvents = (layer) => {
  layer.off('click')
  layer.on('click', (e) => {
    // 0. Mode Tambah Pin Catatan Evaluasi (Klik di atas poligon):
    if (isAddEvaluationPinMode.value) {
      L.DomEvent.stopPropagation(e)
      handleMapClickForEvaluationPin(e, layer)
      return
    }

    // 1. Mode Gabung Poligon:
    if (activeTool.value === 'merge') {
      L.DomEvent.stopPropagation(e)
      const idx = findFeatureIndexForLayer(layer)
      const feat = idx >= 0 ? features.value[idx] : (layer.feature || layer.toGeoJSON())
      if (feat) {
        if (!feat._uiId) feat._uiId = getFeatureUiId(feat)
        if (!layer._uiId) layer._uiId = feat._uiId

        const existingIdx = selectedForMerge.value.findIndex(m => {
          if (m === feat || m === layer.feature) return true
          if (m._uiId && m._uiId === feat._uiId) return true
          const mId = m.id || m.properties?.id
          const featId = feat.id || feat.properties?.id
          if (mId && featId && mId === featId) return true
          return false
        })

        if (existingIdx >= 0) {
          selectedForMerge.value.splice(existingIdx, 1)
        } else {
          selectedForMerge.value.push(feat)
        }
        refreshMapStyles()
      }
      return
    }

    // 2. Mode Hapus (Smart Delete / Serap Tetangga):
    if (activeTool.value === 'delete') {
      L.DomEvent.stopPropagation(e)
      const idx = findFeatureIndexForLayer(layer)
      const feat = idx >= 0 ? features.value[idx] : (layer.feature || layer.toGeoJSON())
      if (feat) {
        executeSmartDelete(feat, idx)
      }
      return
    }

    // 2b. Mode AI Magic Wand (klik di area poligon untuk segmentasi otomatis):
    if (activeTool.value === 'ai_wand') {
      L.DomEvent.stopPropagation(e)
      onMapClickForAiWand(e)
      return
    }

    // 3. Mode digitizing / pemotongan lain: biarkan Geoman menangani tanpa popup
    if (activeTool.value !== null) {
      return
    }

    // 4. Mode Pilih Poligon (Pointer / default select mode: activeTool === null):
    L.DomEvent.stopPropagation(e)
    const idx = findFeatureIndexForLayer(layer)
    if (idx < 0) return

    const feat = features.value[idx] || layer.feature
    const uId = layer._uiId || (feat && (feat._uiId || getFeatureUiId(feat)))

    // If Shift key is held while clicking a polygon on the map -> toggle it in multi-selection!
    if (e.originalEvent && e.originalEvent.shiftKey && uId) {
      toggleSelectPolygon(uId)
      rightTab.value = 'polygons'
      return
    }

    clickedFeatureIdx.value = idx
    rightTab.value = 'classes'
    refreshMapStyles()

    // Open Interactive Popup on Polygon
    openClassPickerPopup(layer, feat, idx, e.latlng)
  })

  // Layer-level edit and marker drag hooks for Topological Editing and fast closure
  let layerTopologicalNodes = []
  let layerDragStartPos = null

  layer.off('pm:markerdragstart')
  layer.on('pm:markerdragstart', (e) => {
    try {
      layer._preEditGeom = JSON.parse(JSON.stringify(layer.toGeoJSON().geometry))
    } catch (_) {}

    const m = e.marker || e.markerEvent?.target
    if (m && m.getLatLng) {
      layerDragStartPos = m.getLatLng()
      layerTopologicalNodes = findSharedTopologicalNodes(layer, layerDragStartPos, featureGroup)
    } else {
      layerTopologicalNodes = []
      layerDragStartPos = null
    }
  })

  layer.off('pm:markerdrag')
  layer.on('pm:markerdrag', (e) => {
    const m = e.marker || e.markerEvent?.target
    if (!m || !layerDragStartPos || !layerTopologicalNodes.length) return
    const currentPos = m.getLatLng()
    const dLat = currentPos.lat - layerDragStartPos.lat
    const dLng = currentPos.lng - layerDragStartPos.lng

    layerTopologicalNodes.forEach(item => {
      const newLat = item.startLat + dLat
      const newLng = item.startLng + dLng
      if (item.ring && item.index >= 0 && item.index < item.ring.length) {
        item.ring[item.index].lat = newLat
        item.ring[item.index].lng = newLng

        // If index 0 has duplicate closing point at end of ring, update it too
        if (item.index === 0 && item.ring.length > 3) {
          const last = item.ring[item.ring.length - 1]
          if (isCoincidentLatLng(item.ring[0], last, 1e-7)) {
            last.lat = newLat
            last.lng = newLng
          }
        }
        item.layer.setLatLngs?.(item.layer.getLatLngs())
        item.layer.redraw?.()
      }
      if (item.marker && item.marker !== m) {
        item.marker.setLatLng([newLat, newLng])
      }
    })
  })

  const handleVertexChangeFast = () => {
    // Clean up any accidental duplicate closing vertex on Leaflet polygon layer
    if (layer && layer.getLatLngs) {
      try {
        const latlngs = layer.getLatLngs()
        if (Array.isArray(latlngs) && latlngs[0] && Array.isArray(latlngs[0])) {
          const ring = latlngs[0]
          if (ring.length > 3) {
            const first = ring[0]
            const last = ring[ring.length - 1]
            if (Math.abs(first.lat - last.lat) < 1e-7 && Math.abs(first.lng - last.lng) < 1e-7) {
              ring.pop()
              layer.setLatLngs([ring])
            }
          }
        }
      } catch (_) {}
      layer.redraw?.()
    }
    // Debounce expensive auto-clip and history clone so UI remains 60fps
    if (debouncedEditTimer) clearTimeout(debouncedEditTimer)
    debouncedEditTimer = setTimeout(() => {
      applyAutoClipAndHealOnEdit(layer)
    }, 120)
  }

  layer.off('pm:markerdragend')
  layer.on('pm:markerdragend', () => {
    if (layerTopologicalNodes.length > 0) {
      layerTopologicalNodes.forEach(item => {
        item.layer.redraw?.()
        if (item.layer.pm && item.layer.pm.enabled() && typeof item.layer.pm._initMarkers === 'function') {
          item.layer.pm._initMarkers()
        }
      })
      syncFeaturesFromMap()
      pushHistory()
      layerTopologicalNodes = []
      layerDragStartPos = null
    }
    handleVertexChangeFast()
  })

  layer.off('pm:vertexadded')
  layer.on('pm:vertexadded', handleVertexChangeFast)

  layer.off('pm:vertexremoved')
  layer.on('pm:vertexremoved', handleVertexChangeFast)
}

const openClassPickerPopup = (layer, feat, idx, latlng) => {
  const currentClassId = feat.properties?.class_id !== undefined ? feat.properties.class_id : 0
  const currentClassName = feat.properties?.class_name || 'Belum Teridentifikasi'
  const currentColor = feat.properties?.color || '#9CA3AF'
  const areaHa = Math.round((feat.properties?.area_sqm || 10000) / 10000)

  // Build interactive HTML popup
  const popupContent = document.createElement('div')
  popupContent.className = 'p-1 text-slate-800 font-sans space-y-2 max-w-[240px]'

  popupContent.innerHTML = `
    <div class="flex items-center justify-between border-b border-slate-200 pb-1.5">
      <div class="flex items-center gap-1.5">
        <div class="w-3 h-3 rounded-xs border border-slate-300" style="background-color: ${currentColor};"></div>
        <span class="font-extrabold text-xs text-slate-900">Poligon #${idx + 1}</span>
      </div>
      <span class="text-[10px] text-slate-500 font-mono">~${areaHa} Ha</span>
    </div>

    <div class="text-[11px] text-slate-600">
      Status: <b class="text-slate-800">${currentClassName}</b>
    </div>

    <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
      Pilih / Ganti Kelas:
    </div>

    <div class="grid grid-cols-2 gap-1 max-h-36 overflow-y-auto pr-0.5" id="popup-class-grid">
    </div>
  `

  const classGrid = popupContent.querySelector('#popup-class-grid')
  annotationsStore.classes.forEach(cls => {
    const btn = document.createElement('button')
    const isSelected = cls.id === currentClassId
    btn.className = `p-1 rounded text-[10px] text-left flex items-center gap-1.5 border transition-all cursor-pointer ${
      isSelected
        ? 'bg-rose-600 text-white font-bold border-rose-600 shadow-xs'
        : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
    }`
    btn.innerHTML = `
      <div class="w-2.5 h-2.5 rounded-xs shrink-0 border border-slate-300" style="background-color: ${cls.color};"></div>
      <span class="truncate">${cls.name}</span>
    `
    btn.onclick = () => {
      reassignClassToClickedPolygon(cls)
      map.closePopup()
    }
    classGrid.appendChild(btn)
  })

  L.popup({
    className: 'custom-gis-popup',
    offset: [0, -10],
    closeButton: true
  })
    .setLatLng(latlng || layer.getBounds().getCenter())
    .setContent(popupContent)
    .openOn(map)
}

const reassignClassToClickedPolygon = async (cls) => {
  if (clickedFeatureIdx.value === null || !featureGroup) return
  
  let layerIdx = 0
  featureGroup.eachLayer((layer) => {
    if (layerIdx === clickedFeatureIdx.value) {
      layer.feature = layer.feature || { type: 'Feature', properties: {} }
      layer.feature.properties = {
        class_id: cls.id,
        class_name: cls.name,
        color: cls.color
      }
      styleLayer(layer, cls.color)
    }
    layerIdx++
  })
  
  syncFeaturesFromMap()
  pushHistory()
  showToast(`Kelas Poligon #${clickedFeatureIdx.value + 1} diubah → ${cls.name}`)

  // Fast direct save in background
  const targetFeat = features.value[clickedFeatureIdx.value]
  if (targetFeat && targetFeat.id) {
    try {
      await api.updateAnnotationClass(targetFeat.id, cls.id)
    } catch {}
  }
}

const handleSmartDeleteSelected = () => {
  if (clickedFeatureIdx.value === null) return
  const feat = features.value[clickedFeatureIdx.value]
  if (feat) {
    executeSmartDelete(feat, clickedFeatureIdx.value)
  }
}

const executeSmartDelete = async (targetFeat, targetIdx) => {
  if (!selectedTaskId.value) return
  if (features.value.length <= 1) {
    alert('⚠️ Poligon ini adalah satu-satunya poligon di dalam grid tile.\n\nTidak dapat dihapus karena akan membuat seluruh grid kosong bolong!\nJika ingin mengganti tutupan lahan, silakan gunakan menu Ubah Kelas atau Potong Poligon.')
    return
  }

  // Find neighbor candidates using Turf.js
  const otherFeats = features.value.filter((f, i) => i !== targetIdx)
  const targetPoly = targetFeat.type === 'Feature' ? targetFeat : turf.feature(targetFeat.geometry || targetFeat)

  let bestNeighbor = null
  let maxSharedScore = -1

  for (const other of otherFeats) {
    try {
      const otherPoly = other.type === 'Feature' ? other : turf.feature(other.geometry || other)
      
      let sharedScore = 0
      const isTouching = turf.booleanTouches(targetPoly, otherPoly)
      const isOverlap = turf.booleanOverlap(targetPoly, otherPoly)
      
      if (isTouching || isOverlap) {
        try {
          const inter = turf.intersect(turf.featureCollection([targetPoly, otherPoly]))
          if (inter) {
            sharedScore = (inter.geometry && inter.geometry.type.includes('Line'))
              ? turf.length(inter)
              : turf.area(inter)
          } else {
            sharedScore = 1.0
          }
        } catch (_) {
          sharedScore = 1.0
        }
      } else {
        // Test with tiny buffer (~0.5m) to catch vertices touching with snapping tolerance
        const buffered = turf.buffer(targetPoly, 0.000005, { units: 'kilometers' })
        if (turf.booleanIntersects(buffered, otherPoly)) {
          sharedScore = 0.1
        }
      }

      if (sharedScore > maxSharedScore) {
        maxSharedScore = sharedScore
        bestNeighbor = other
      }
    } catch (e) {
      console.warn('Neighbor check warning:', e)
    }
  }

  // Fallback: if no direct touching neighbor detected due to precision, pick closest neighbor
  if (!bestNeighbor && otherFeats.length > 0) {
    let minDist = Infinity
    for (const other of otherFeats) {
      try {
        const otherPoly = other.type === 'Feature' ? other : turf.feature(other.geometry || other)
        const d = turf.distance(turf.centroid(targetPoly), turf.centroid(otherPoly))
        if (d < minDist) {
          minDist = d
          bestNeighbor = other
        }
      } catch (_) {}
    }
  }

  const neighborClassName = bestNeighbor?.properties?.class_name || 'Poligon Tetangga'
  const targetClassName = targetFeat.properties?.class_name || 'Poligon'

  const confirmed = confirm(
    `Hapus poligon [${targetClassName}]?\n\n` +
    `Areanya akan otomatis disatukan ke tetangga [${neighborClassName}] agar tidak berlubang.\n\n` +
    `Lanjutkan?`
  )
  if (!confirmed) return

  showToast(`Menghapus poligon [${targetClassName}]...`)

  try {
    const targetId = targetFeat.id || targetFeat.properties?.id
    const neighborId = bestNeighbor?.id || bestNeighbor?.properties?.id
    let backendSuccess = false

    if (targetId && typeof targetId === 'number') {
      try {
        const res = await api.smartDeletePolygon(selectedTaskId.value, targetId, neighborId || null)
        showToast(`✨ ${res.data?.message || 'Poligon berhasil dihapus!'}`)
        backendSuccess = true
        if (res.data?.deleted_ids || res.data?.updated_features || res.data?.created_features) {
          applyDeltaUpdate(res.data.deleted_ids || [], res.data.created_features || [], res.data.updated_features || [])
        } else {
          await loadTaskData(selectedTaskId.value, true)
          pushHistory()
        }
      } catch (backendErr) {
        console.warn('Backend smart delete failed, falling back to client-side turf:', backendErr)
      }
    }

    if (!backendSuccess && bestNeighbor) {
      // Client-side Turf union fallback
      const otherPoly = bestNeighbor.type === 'Feature' ? bestNeighbor : turf.feature(bestNeighbor.geometry || bestNeighbor)
      const unioned = turf.union(turf.featureCollection([otherPoly, targetPoly]))
      if (!unioned) {
        throw new Error('Gagal menyatukan geometri poligon.')
      }

      unioned.properties = { ...bestNeighbor.properties }
      unioned._uiId = bestNeighbor._uiId || getFeatureUiId(bestNeighbor)

      // Replace bestNeighbor with unioned, and remove targetFeat
      const targetUiId = targetFeat._uiId || targetFeat.id || targetFeat.properties?.id
      const neighborUiId = bestNeighbor._uiId || bestNeighbor.id || bestNeighbor.properties?.id

      const newFeaturesList = features.value.filter(f => {
        const uId = f._uiId || f.id || f.properties?.id
        return uId !== targetUiId && uId !== neighborUiId
      })
      newFeaturesList.push(unioned)

      await annotationsStore.saveGridAnnotations(selectedTaskId.value, newFeaturesList)
      showToast(`✨ Poligon berhasil dihapus!`)
      await loadTaskData(selectedTaskId.value, true)
      pushHistory()
    }
  } catch (err) {
    console.error('Delete error:', err)
    alert(err.response?.data?.detail || err.message || 'Gagal menghapus poligon.')
  } finally {
    clickedFeatureIdx.value = null
  }
}

const selectFeatureFromList = (idx) => {
  clickedFeatureIdx.value = idx
  flyToFeature(idx)
}

const flyToFeature = (idx) => {
  clickedFeatureIdx.value = idx
  if (!featureGroup || !map) return
  
  let layerIdx = 0
  featureGroup.eachLayer((layer) => {
    if (layerIdx === idx) {
      if (layer.getBounds) {
        map.flyToBounds(layer.getBounds(), { maxZoom: 16, duration: 0.5, padding: [40, 40] })
      }
    }
    layerIdx++
  })
}

const refreshMapStyles = () => {
  if (!featureGroup) return
  let idx = 0
  featureGroup.eachLayer((layer) => {
    const feat = features.value[idx] || layer.feature
    const uId = layer._uiId || feat?._uiId || (feat && getFeatureUiId(feat))
    if (!layer._uiId && uId) layer._uiId = uId

    const isClicked = clickedFeatureIdx.value === idx
    const isMergedSelected = isFeatureSelectedForMerge(feat, layer)
    const isMultiSelected = uId && selectedPolyUiIds.value.has(uId)
    const isHovered = hoverFeatureIdx.value === idx
    const color = layer.feature?.properties?.color || feat?.properties?.color || '#9CA3AF'

    let weight = 2
    let strokeColor = color
    let fillColor = color
    let fillOpacity = polygonOpacity.value
    let strokeOpacity = 1
    let dashArray = null

    if (isMultiSelected) {
      // 🌟 Unmistakable Cyan Multi-Selection Highlight on Map
      weight = 4.5
      strokeColor = '#06b6d4' // Cyan-500
      fillColor = '#22d3ee' // Cyan-400
      fillOpacity = polygonOpacity.value === 0 ? 0 : Math.max(polygonOpacity.value, 0.35)
      strokeOpacity = 1
      dashArray = '6, 4'
      try { layer.bringToFront() } catch (_) {}
    } else if (isHovered) {
      // 🌟 Hover Highlight from Sidebar List (Hollow: hanya garis batas kuning)
      weight = 4
      strokeColor = '#facc15' // Amber/Yellow
      fillOpacity = polygonOpacity.value
      strokeOpacity = 1
      try { layer.bringToFront() } catch (_) {}
    } else if (isClicked) {
      weight = 3.5
      strokeColor = '#4f46e5' // Indigo highlight
      fillOpacity = polygonOpacity.value === 0 ? 0 : Math.max(polygonOpacity.value, 0.25)
      strokeOpacity = 1
      try { layer.bringToFront() } catch (_) {}
    } else if (isMergedSelected) {
      weight = 3.5
      strokeColor = '#10b981' // Emerald highlight for merge
      fillOpacity = polygonOpacity.value === 0 ? 0 : Math.max(polygonOpacity.value, 0.25)
      strokeOpacity = 1
      try { layer.bringToFront() } catch (_) {}
    }

    layer.setStyle({
      color: strokeColor,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      opacity: strokeOpacity,
      weight: weight,
      dashArray: dashArray
    })
    idx++
  })
}

const previousOpacity = ref(0.6)
const isPeekHidden = computed(() => polygonOpacity.value === 0)

const togglePeekVisibility = () => {
  if (polygonOpacity.value > 0) {
    previousOpacity.value = polygonOpacity.value
    polygonOpacity.value = 0
    showToast('Poligon disembunyikan (mode inspeksi citra)')
  } else {
    polygonOpacity.value = previousOpacity.value > 0 ? previousOpacity.value : 0.6
    showToast(`Poligon ditampilkan (${Math.round(polygonOpacity.value * 100)}%)`)
  }
  updateOpacity()
}

const setOpacityPreset = (val) => {
  polygonOpacity.value = val
  updateOpacity()
}

const setLayer = (layerId) => {
  currentLayer.value = layerId
  updateTileLayer()
}

const setYear = async (yr) => {
  currentYear.value = yr
  tasksStore.selectedYear = yr
  await tasksStore.fetchTasks()

  // 1. First priority: exact sibling match from preloaded taskSiblings
  let targetSibling = taskSiblings.value.find(s => s.year === yr)

  // 2. Fallback: search tasksStore.tasks matching baseCode AND chosen year
  if (!targetSibling && tasksStore.currentTask) {
    const currentCode = tasksStore.currentTask.grid_code
    const baseCode = currentCode.replace(/_\d{4}$/, '')
    const targetCode = `${baseCode}_${yr}`
    targetSibling = tasksStore.tasks.find(t => t.year === yr && (t.grid_code === targetCode || t.grid_code.startsWith(`${baseCode}_`)))
  }

  if (targetSibling) {
    selectedTaskId.value = targetSibling.id
    router.replace({ query: { taskId: targetSibling.id } })
    await loadTaskData(targetSibling.id)
    showToast(`Beralih ke task ${targetSibling.grid_code} (${yr})`)
    return
  }

  // Update imagery layer for the chosen year
  await updateTileLayer()
  showToast(`Citra Satelit beralih ke komposit tahun ${yr}`)
}

const styleLayer = (layer, colorHex) => {
  layer.setStyle({
    color: colorHex,
    fillColor: colorHex,
    fillOpacity: polygonOpacity.value,
    opacity: polygonOpacity.value === 0 ? 0.35 : 1,
    weight: 2
  })
}

const updateOpacity = () => {
  refreshMapStyles()
}

const onTaskChange = async () => {
  if (!selectedTaskId.value) return
  router.replace({ query: { taskId: selectedTaskId.value } })
  await loadTaskData(selectedTaskId.value)
}

const loadTaskData = async (taskId, preserveHistory = false) => {
  const task = await tasksStore.fetchTaskDetail(taskId)
  if (!task || !map) return

  if (task.year && currentYear.value !== task.year) {
    currentYear.value = task.year
    await updateTileLayer()
  }

  clickedFeatureIdx.value = null
  if (!showTopologySurgeryModal.value) {
    topologyResult.value = null
  }
  if (!preserveHistory) {
    activeTool.value = null
  }
  selectedForMerge.value = []

  // 1. Remove previous layers
  if (focusMaskLayer) map.removeLayer(focusMaskLayer)
  if (gridBoundingLayer) map.removeLayer(gridBoundingLayer)
  if (neighboringGridsLayer) map.removeLayer(neighboringGridsLayer)
  if (neighborPolygonsLayer) {
    map.removeLayer(neighborPolygonsLayer)
    neighborPolygonsLayer = null
  }

  // 2. Build Inverted Mask around Active Grid: Dims the outside world with adjustable light transparent overlay
  const worldOuterRing = [[-90, -180], [-90, 180], [90, 180], [90, -180], [-90, -180]]
  const activeGridHole = [
    [task.min_lat, task.min_lon],
    [task.min_lat, task.max_lon],
    [task.max_lat, task.max_lon],
    [task.max_lat, task.min_lon],
    [task.min_lat, task.min_lon]
  ]

  focusMaskLayer = L.polygon([worldOuterRing, activeGridHole], {
    color: '#334155',
    weight: 1,
    fillColor: '#020617',
    fillOpacity: outsideDimOpacity.value,
    interactive: false
  }).addTo(map)

  // 3. Draw Neighboring Task Grids (Transparent footprint & dashed border to clearly see neighboring satellite imagery)
  neighboringGridsLayer = L.featureGroup().addTo(map)
  tasksStore.tasks.forEach(t => {
    if (t.id !== task.id) {
      const rect = L.rectangle([[t.min_lat, t.min_lon], [t.max_lat, t.max_lon]], {
        color: '#64748b',
        weight: 1.5,
        dashArray: '5, 5',
        fillColor: '#0f172a',
        fillOpacity: 0.0, // 100% transparan agar citra di grid sebelah terlihat jernih dan natural
        interactive: true
      })
      rect.bindTooltip(`Grid Sebelah: <b>${t.grid_code}</b><br><span class="text-[10px] text-slate-300">Pilih di dropdown kiri untuk berpindah</span>`, { sticky: true })
      rect.addTo(neighboringGridsLayer)
    }
  })

  // 4. Draw Active Grid Bounding Box (Golden Amber outline, 100% transparent inside!)
  const bounds = [[task.min_lat, task.min_lon], [task.max_lat, task.max_lon]]
  gridBoundingLayer = L.rectangle(bounds, {
    color: '#f59e0b',
    weight: 3.5,
    dashArray: '6, 6',
    fillOpacity: 0.0,
    interactive: false
  }).addTo(map)

  // FIX PENTING: Hanya panggil fitBounds jika bukan preserveHistory (bukan reload setelah digitasi/split/merge)
  // agar posisi zoom mapper tidak meloncat keluar / zoom out
  if (!preserveHistory) {
    map.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 })
  }

  // 5. Load Existing Polygons (STRICT SINGLEPART GUARANTEE)
  featureGroup.clearLayers()
  const fetchedFeatures = await annotationsStore.fetchGridAnnotations(taskId)
  const strictFeatures = []
  fetchedFeatures.forEach(feat => {
    strictFeatures.push(...explodeGeoJsonFeature(feat))
  })
  features.value = strictFeatures

  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  if (strictFeatures.length > 0) {
    strictFeatures.forEach(feat => {
      feat._uiId = getFeatureUiId(feat)
      const geojsonLayer = L.geoJSON(feat, {
        style: () => {
          const cls = classesMap[feat.properties?.class_id]
          const color = cls?.color || '#9CA3AF'
          return { color, fillColor: color, fillOpacity: polygonOpacity.value, weight: 2 }
        }
      })

      geojsonLayer.eachLayer((l) => {
        l.feature = feat
        l._uiId = feat._uiId
        const cls = classesMap[feat.properties?.class_id]
        if (cls) l.feature.properties.color = cls.color
        else l.feature.properties.color = '#9CA3AF'
        bindLayerEvents(l)
        featureGroup.addLayer(l)
      })
    })
  }

  // Check for local offline draft in IndexedDB (Poin 1)
  try {
    const draft = await getTaskDraft(taskId)
    if (draft && draft.features && draft.features.length > 0) {
      localDraftStatus.value = {
        updatedAt: draft.updatedAt,
        polygonCount: draft.features.length
      }
      if (draft.features.length !== fetchedFeatures.length) {
        pendingDraftToRestore.value = draft
        showDraftRestorePrompt.value = true
      }
    } else {
      localDraftStatus.value = null
      showDraftRestorePrompt.value = false
    }
  } catch (err) {
    console.warn('Gagal membaca draf IndexedDB:', err)
  }

  // 5. Fetch sibling task information across other available years
  try {
    const siblingsRes = await api.getTaskSiblings(taskId)
    taskSiblings.value = siblingsRes.data || []
    showSmartCopyBanner.value = true
  } catch (err) {
    taskSiblings.value = []
  }

  // 6. Load Neighboring Polygons (if enabled for Edge-Matching)
  if (showNeighborPolygons.value) {
    loadNeighborPolygons(taskId)
  }

  // 6. Sync Year & Refresh Basemap Tile Layer
  if (task.year) {
    currentYear.value = task.year
  }
  updateTileLayer()

  // 7. Manage History Stack for Undo/Redo
  if (preserveHistory) {
    pushHistory()
  } else {
    history.value = [JSON.parse(JSON.stringify(features.value))]
    historyIndex.value = 0
  }

  // 8. Load Review Pins / Notes from Supervisi (QC)
  await tasksStore.fetchReviewPins(taskId)
  renderReviewPinsOnMap()
}

// ─────────────────────────────────────────────
// REVIEW PINS (Catatan Supervisi / QC Marker di Peta)
// ─────────────────────────────────────────────

const renderReviewPinsOnMap = () => {
  if (!reviewPinsLayerGroup || !map) return
  reviewPinsLayerGroup.clearLayers()

  if (!showReviewPins.value) return

  const pins = tasksStore.currentTaskReviewPins || []
  const isDigitizingActive = activeTool.value !== null
  const currentZoom = map.getZoom ? map.getZoom() : 16

  // Scale pin according to zoom: at scale ~300m (zoom <= 16), keep it a micro-target (13px)
  const pinSize = currentZoom >= 17 ? 16 : 13
  const halfSize = Math.floor(pinSize / 2)

  pins.forEach(pin => {
    const isResolved = pin.status === 'RESOLVED'

    // Extract category if available: [Category] Note body
    const match = (pin.note || '').match(/^\[(.*?)\]\s*(.*)$/)
    const categoryName = match ? match[1] : null
    const cleanNote = match ? match[2] : pin.note

    // Micro target pin styling:
    // When digitizing is active, pins switch to semi-transparent ghost mode and ignore pointer events
    const ghostClass = isDigitizingActive ? 'opacity-35 pointer-events-none' : 'hover:scale-125 cursor-pointer shadow-xs'

    const markerHtml = isResolved
      ? `<div class="relative flex items-center justify-center rounded-full bg-emerald-600 text-white border-[1.5px] border-white transition-all ${ghostClass}" style="width: ${pinSize}px; height: ${pinSize}px;" title="QC Selesai: ${cleanNote}">
           <div class="w-1 h-1 bg-white rounded-full"></div>
         </div>`
      : `<div class="relative flex items-center justify-center rounded-full bg-rose-600 text-white border-[1.5px] border-white transition-all ${ghostClass}" style="width: ${pinSize}px; height: ${pinSize}px;" title="QC: ${cleanNote}">
           <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
           <span class="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-amber-400 rounded-full border border-white"></span>
         </div>`

    const customIcon = L.divIcon({
      html: markerHtml,
      className: `annotator-review-pin-marker ${isDigitizingActive ? 'pointer-events-none' : ''}`,
      iconSize: [pinSize, pinSize],
      iconAnchor: [halfSize, halfSize],
      popupAnchor: [0, -halfSize - 6]
    })

    const marker = L.marker([pin.lat, pin.lon], {
      icon: customIcon,
      interactive: !isDigitizingActive // During digitizing/cutting, mouse clicks pass directly to map vertices
    })

    const statusBadge = isResolved
      ? `<span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300">✓ Sudah Selesai</span>`
      : `<span class="bg-rose-100 text-rose-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-rose-300">● Perlu Diperbaiki</span>`

    const categoryBadge = categoryName
      ? `<span class="bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-bold px-2 py-0.5 rounded-full">🏷️ ${categoryName}</span>`
      : ''

    const polygonContext = pin.annotation_id
      ? `<div class="text-[10px] text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md font-mono border border-indigo-200">Poligon Terkait: #${pin.annotation_id}</div>`
      : `<div class="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-sans border border-emerald-200">Pin Titik Bebas</div>`

    const toggleBtn = isResolved
      ? `<button onclick="window._mapperTogglePin(${pin.id})" class="flex-1 py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl border border-slate-300 transition-colors cursor-pointer flex items-center justify-center gap-1">
           <span>↺ Buka Kembali</span>
         </button>`
      : `<button onclick="window._mapperTogglePin(${pin.id})" class="flex-1 py-1.5 px-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors cursor-pointer flex items-center justify-center gap-1">
           <span>✓ Tandai Selesai</span>
         </button>`

    const deleteBtn = `<button onclick="window._mapperDeletePin(${pin.id})" class="py-1.5 px-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold rounded-xl border border-rose-200 transition-colors cursor-pointer flex items-center justify-center gap-1" title="Hapus Pin Ini">
        <span>🗑️</span>
      </button>`

    const popupContent = `
      <div class="p-2 space-y-2 min-w-[250px] max-w-[320px] font-sans text-slate-800">
        <div class="flex items-center justify-between gap-1 border-b border-slate-200 pb-1.5">
          <span class="text-xs font-bold text-slate-900 flex items-center gap-1">📍 Catatan Evaluasi</span>
          ${statusBadge}
        </div>
        <div class="flex items-center justify-between gap-1 flex-wrap">
          ${categoryBadge}
          ${polygonContext}
        </div>
        <div class="text-xs text-slate-900 bg-amber-50/80 p-2.5 rounded-xl border border-amber-200 font-medium leading-relaxed">
          "${cleanNote}"
        </div>
        <div class="text-[10px] text-slate-500 flex items-center justify-between">
          <span>Oleh: <b>${pin.reviewer_name || 'Petugas/Reviewer'}</b></span>
          <span class="font-mono">${new Date(pin.created_at).toLocaleDateString('id-ID')}</span>
        </div>
        <div class="pt-1.5 border-t border-slate-100 flex items-center gap-1.5">
          ${toggleBtn}
          ${deleteBtn}
        </div>
      </div>
    `

    marker.bindPopup(popupContent, { maxWidth: 340, className: 'custom-mapper-pin-popup' })
    reviewPinsLayerGroup.addLayer(marker)
  })
}

// Global hooks for pin interactions from leaflet popup
if (typeof window !== 'undefined') {
  window._mapperTogglePin = (pinId) => {
    const pin = (tasksStore.currentTaskReviewPins || []).find(p => p.id === pinId)
    if (pin) togglePinResolved(pin)
  }
  window._mapperDeletePin = (pinId) => {
    deleteEvaluationPin(pinId)
  }
}

const togglePinResolved = async (pin) => {
  const newStatus = pin.status === 'RESOLVED' ? 'PENDING' : 'RESOLVED'
  try {
    await tasksStore.updateReviewPin(selectedTaskId.value, pin.id, { status: newStatus })
    renderReviewPinsOnMap()
    showToast(newStatus === 'RESOLVED' ? '✓ Pin ditandai selesai!' : '↺ Pin dibuka kembali')
  } catch (err) {
    console.error('Failed to update review pin:', err)
  }
}

const toggleAddEvaluationPinMode = (forceState) => {
  if (!map) return
  if (!selectedTaskId.value) {
    showToast('Pilih tugas grid terlebih dahulu.')
    return
  }

  isAddEvaluationPinMode.value = forceState !== undefined ? forceState : !isAddEvaluationPinMode.value
  const mapElem = document.getElementById('map-container')

  if (isAddEvaluationPinMode.value) {
    // Cancel drawing or editing tools if any
    setDigitizeMode(null)
    if (mapElem) mapElem.style.cursor = 'crosshair'
    window.addEventListener('keydown', onEscKeyForEvaluationPin)
    showToast('Mode Tambah Catatan: Klik lokasi pada peta')
  } else {
    if (mapElem) mapElem.style.cursor = ''
    window.removeEventListener('keydown', onEscKeyForEvaluationPin)
  }
}

const onEscKeyForEvaluationPin = (e) => {
  if (e.key === 'Escape' && isAddEvaluationPinMode.value) {
    toggleAddEvaluationPinMode(false)
  }
}

const onMapClickForEvaluationPin = (e) => {
  if (!isAddEvaluationPinMode.value) return
  handleMapClickForEvaluationPin(e, null)
}

const handleMapClickForEvaluationPin = (e, layer = null) => {
  if (!isAddEvaluationPinMode.value) return
  const lat = Number(e.latlng.lat.toFixed(6))
  const lon = Number(e.latlng.lng.toFixed(6))

  let poly = null
  if (layer) {
    const idx = findFeatureIndexForLayer(layer)
    poly = idx >= 0 ? features.value[idx] : (layer.feature || layer.toGeoJSON())
  }

  evaluationPinModalData.value = {
    lat,
    lon,
    note: '',
    category: 'Batas Kurang Pas',
    annotation_id: poly ? (poly.id || poly.properties?.id || null) : null,
    class_name: poly?.properties?.class_name || ''
  }

  showEvaluationPinModal.value = true
  toggleAddEvaluationPinMode(false)
}

const saveNewEvaluationPin = async () => {
  const rawNote = evaluationPinModalData.value.note.trim()
  if (!rawNote || !selectedTaskId.value) return

  submittingEvaluationPin.value = true
  try {
    const cat = evaluationPinModalData.value.category
    const finalNote = cat && !rawNote.startsWith('[') ? `[${cat}] ${rawNote}` : rawNote

    await tasksStore.createReviewPin(selectedTaskId.value, {
      lat: evaluationPinModalData.value.lat,
      lon: evaluationPinModalData.value.lon,
      note: finalNote,
      annotation_id: evaluationPinModalData.value.annotation_id
    })

    showEvaluationPinModal.value = false
    renderReviewPinsOnMap()
    showToast('Catatan evaluasi berhasil ditambahkan.')
  } catch (err) {
    console.error('Failed to create review pin:', err)
    showToast('Gagal menyimpan catatan: ' + (err.response?.data?.detail || err.message))
  } finally {
    submittingEvaluationPin.value = false
  }
}

const deleteEvaluationPin = async (pinId) => {
  if (!confirm('Hapus pin catatan evaluasi ini?')) return
  try {
    await tasksStore.deleteReviewPin(selectedTaskId.value, pinId)
    renderReviewPinsOnMap()
    showToast('Catatan evaluasi berhasil dihapus.')
  } catch (err) {
    console.error('Failed to delete review pin:', err)
    showToast('Gagal menghapus catatan: ' + (err.response?.data?.detail || err.message))
  }
}

const focusOnReviewPin = (pin) => {
  if (!map) return
  if (!showReviewPins.value) {
    showReviewPins.value = true
    renderReviewPinsOnMap()
  }
  map.setView([pin.lat, pin.lon], Math.max(map.getZoom(), 15), { animate: true })
  setTimeout(() => {
    if (reviewPinsLayerGroup) {
      reviewPinsLayerGroup.eachLayer(layer => {
        const latlng = layer.getLatLng?.()
        if (latlng && Math.abs(latlng.lat - pin.lat) < 0.0001 && Math.abs(latlng.lng - pin.lon) < 0.0001) {
          layer.openPopup?.()
        }
      })
    }
  }, 250)
}

// Automatically sync review pins when digitizing tool or store data changes
watch(activeTool, () => {
  renderReviewPinsOnMap()
})

watch(() => tasksStore.currentTaskReviewPins, () => {
  renderReviewPinsOnMap()
}, { deep: true })

const bestCopyCandidate = computed(() => {
  if (features.value.length > 0) return null
  return taskSiblings.value.find(s => s.annotation_count > 0) || null
})

const candidateSourceTasks = computed(() => {
  // First priority: siblings from other years of this exact same grid that have annotations
  const siblingsWithData = taskSiblings.value.filter(s => s.annotation_count > 0)
  if (siblingsWithData.length > 0) return siblingsWithData
  if (taskSiblings.value.length > 0) return taskSiblings.value

  // Fallback: any other tasks with annotations in the project
  if (!tasksStore.currentTask) return []
  const currentId = tasksStore.currentTask.id
  return tasksStore.tasks.filter(t => t.id !== currentId && t.annotation_count > 0)
})

const quickCopyFromSibling = async (sibling) => {
  if (!selectedTaskId.value || !sibling) return
  copyingAnnotations.value = true
  try {
    const res = await api.copyAnnotations(selectedTaskId.value, sibling.id)
    showToast(res.data?.message || `Berhasil menyalin poligon dari tahun ${sibling.year}!`)
    showSmartCopyBanner.value = false
    await loadTaskData(selectedTaskId.value, true)
  } catch (err) {
    showToast(err.response?.data?.detail || 'Gagal menyalin anotasi')
  } finally {
    copyingAnnotations.value = false
  }
}

const openCopyModal = () => {
  if (candidateSourceTasks.value.length > 0) {
    selectedSourceTaskId.value = candidateSourceTasks.value[0].id
  }
  showCopyModal.value = true
}

const handleCopyAnnotations = async () => {
  if (!selectedTaskId.value || !selectedSourceTaskId.value) return
  copyingAnnotations.value = true
  try {
    const res = await api.copyAnnotations(selectedTaskId.value, selectedSourceTaskId.value)
    showToast(res.data?.message || 'Poligon berhasil disalin!')
    showCopyModal.value = false
    await loadTaskData(selectedTaskId.value, true)
  } catch (err) {
    showToast(err.response?.data?.detail || 'Gagal menyalin anotasi')
  } finally {
    copyingAnnotations.value = false
  }
}

// ─── TOPOLOGY VALIDATION ─────────────────
const runTopologyCheck = async (autoSave = true) => {
  if (!selectedTaskId.value) return
  topologyLoading.value = true

  try {
    if (autoSave && !showTopologySurgeryModal.value) {
      // Attempt auto-save first if editable and not inside surgery studio
      try {
        await saveAnnotations()
      } catch (saveErr) {
        console.warn('Could not auto-save before topology check:', saveErr)
      }

      // Reload features dari server agar ID layer di peta = ID di database
      try {
        await loadTaskData(selectedTaskId.value, true)
      } catch (reloadErr) {
        console.warn('Could not reload features after save:', reloadErr)
      }
    }

    const res = await api.validateTopology(selectedTaskId.value)
    topologyResult.value = res.data
    currentTopologyErrorIndex.value = 0
    activeTopologyError.value = res.data.errors?.[0] || null

    if (res.data.valid || !res.data.errors?.length) {
      showToast(`✅ Topologi valid! Coverage ${res.data.coverage_percent || 100}%`)
      if (showTopologySurgeryModal.value) {
        closeTopologySurgeryModal()
        showToast('🎉 Semua masalah topologi telah terselesaikan!')
      }
    } else if (res.data.errors?.length) {
      if (showTopologySurgeryModal.value) {
        refreshSurgeryState()
      } else {
        showToast(`⚠️ Ditemukan ${res.data.errors.length} masalah topologi. Klik "Buka Studio Perbaikan Topologi" untuk mulai perbaikan.`)
      }
    }
  } catch (err) {
    showToast('Gagal menjalankan validasi topologi')
    console.error('Topology validation error:', err)
  } finally {
    topologyLoading.value = false
  }
}

const calculatePolygonAreaSqm = (coords) => {
  if (!coords || coords.length < 3) return 0
  const radius = 6378137
  let area = 0
  for (let i = 0; i < coords.length; i++) {
    const p1 = coords[i]
    const p2 = coords[(i + 1) % coords.length]
    const lat1 = (p1[1] * Math.PI) / 180
    const lat2 = (p2[1] * Math.PI) / 180
    const lon1 = (p1[0] * Math.PI) / 180
    const lon2 = (p2[0] * Math.PI) / 180
    area += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2))
  }
  area = (Math.abs(area) * radius * radius) / 2.0
  return area
}

const gridAreaSqm = computed(() => {
  const t = tasksStore.currentTask
  if (!t) return 104857600
  const w = (t.max_lon - t.min_lon) * 111320 * Math.cos(((t.min_lat + t.max_lat) / 2 * Math.PI) / 180)
  const h = (t.max_lat - t.min_lat) * 110540
  return Math.abs(w * h) || 104857600
})

const totalDrawnAreaSqm = computed(() => {
  let sum = 0
  features.value.forEach(f => {
    const coords = f.geometry?.coordinates?.[0]
    if (coords) sum += calculatePolygonAreaSqm(coords)
  })
  return sum
})

const coveragePercent = computed(() => {
  if (!gridAreaSqm.value) return 0
  const pct = Math.round((totalDrawnAreaSqm.value / gridAreaSqm.value) * 100)
  return Math.min(pct, 100)
})

const syncFeaturesFromMap = () => {
  if (!featureGroup) return
  const newFeatures = []
  featureGroup.eachLayer((layer) => {
    const json = layer.toGeoJSON()
    if (!layer._uiId) {
      layer._uiId = layer.feature?._uiId || getFeatureUiId(layer.feature)
    }
    const currentProps = layer.feature?.properties || {}
    json.id = layer.feature?.id || currentProps.id || null
    json._uiId = layer._uiId
    json.properties = {
      id: json.id,
      class_id: currentProps.class_id !== undefined ? currentProps.class_id : 0,
      class_name: currentProps.class_name || 'Belum Teridentifikasi',
      color: currentProps.color || '#9CA3AF',
      area_sqm: currentProps.area_sqm || null
    }
    layer.feature = json

    // STRICT SINGLEPART: Explode any multi-part features
    const exploded = explodeGeoJsonFeature(json)
    newFeatures.push(...exploded)
  })
  features.value = newFeatures
}

const saveAnnotations = async () => {
  if (!selectedTaskId.value) return
  if (annotationsStore.saving) return
  syncFeaturesFromMap()

  if (features.value.length === 0) {
    const existingCount = tasksStore.currentTask?.annotation_count || 0
    if (existingCount > 0) {
      alert(`⚠️ Peringatan: Tidak ada poligon di kanvas peta, sementara grid memiliki ${existingCount} poligon tersimpan di server. Penyimpanan dibatalkan untuk mencegah hilangnya data secara tidak sengaja.`)
      return
    }
  }

  const ok = await annotationsStore.saveGridAnnotations(selectedTaskId.value, features.value)
  if (ok) {
    showToast('Semua poligon draf berhasil disimpan!')
    await tasksStore.fetchTaskDetail(selectedTaskId.value)
    if (selectedTaskId.value) {
      await clearTaskDraft(selectedTaskId.value)
      localDraftStatus.value = null
      showDraftRestorePrompt.value = false
    }
    // Reload features to ensure local Leaflet layers possess fresh DB IDs
    try {
      await loadTaskData(selectedTaskId.value, true)
    } catch (reloadErr) {
      console.warn('Could not reload features after save:', reloadErr)
    }
  }
}

const submitForReview = async () => {
  if (!selectedTaskId.value) return
  if (features.value.length === 0) {
    alert('Harap buat minimal 1 poligon tutupan lahan sebelum submit!')
    return
  }

  syncFeaturesFromMap()

  // Save first
  await saveAnnotations()

  // CRITICAL: Reload features so local featureGroup layers and features.value have fresh DB IDs
  try {
    await loadTaskData(selectedTaskId.value, true)
  } catch (reloadErr) {
    console.warn('Could not reload features after pre-submit save:', reloadErr)
  }

  // Run topology validation before submit
  topologyLoading.value = true
  try {
    const topoRes = await api.validateTopology(selectedTaskId.value)
    topologyResult.value = topoRes.data

    if (!topoRes.data.valid) {
      const errorSummary = topoRes.data.errors.map(e => `• [${e.type}] ${e.message}`).join('\n')
      const canAutoHeal = topoRes.data.errors.every(e => ['OVERLAP', 'SELF_INTERSECTION', 'INVALID_GEOM'].includes(e.type))

      if (canAutoHeal) {
        if (confirm(`⚠️ Validasi Topologi Mendeteksi ${topoRes.data.errors.length} Masalah Overlap/Geometri:\n\n${errorSummary}\n\nIngin jalankan Auto-Heal otomatis untuk merapikan poligon dan langsung submit ke QC?`)) {
          showToast('Menjalankan Auto-Heal topologi...')
          try {
            await api.autoHealTopology(selectedTaskId.value)
            await loadTaskData(selectedTaskId.value, true)
            const recheck = await api.validateTopology(selectedTaskId.value)
            topologyResult.value = recheck.data
            if (recheck.data.valid) {
              const ok = await tasksStore.updateStatus(selectedTaskId.value, 'SUBMITTED')
              if (ok) {
                showToast('🎉 Topologi berhasil dirapikan otomatis & tugas berhasil disubmit untuk review QC!')
              }
              topologyLoading.value = false
              return
            }
          } catch (healErr) {
            console.warn('Pre-submit auto-heal failed:', healErr)
          }
        }
      }

      alert(`⚠️ Validasi Topologi Gagal!\n\nMasalah yang ditemukan:\n${errorSummary}\n\nKlik 'Buka Studio Perbaikan Topologi' untuk merapikan poligon sebelum submit.`)
      topologyLoading.value = false
      return
    }
  } catch (err) {
    console.error('Topology pre-submit check failed:', err)
    if (!confirm('Validasi topologi gagal dijalankan. Tetap lanjut submit tanpa validasi?')) {
      topologyLoading.value = false
      return
    }
  }
  topologyLoading.value = false

  const ok = await tasksStore.updateStatus(selectedTaskId.value, 'SUBMITTED')
  if (ok) {
    showToast('Tugas berhasil disubmit untuk review QC!')
  }
}

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
/* Leaflet Geoman custom toolbar theme */
.leaflet-pm-toolbar .leaflet-buttons-control-button {
  background-color: #ffffff !important;
  color: #0f172a !important;
  border-color: #cbd5e1 !important;
  border-radius: 8px !important;
  margin-bottom: 4px !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08) !important;
}
.leaflet-pm-toolbar .leaflet-buttons-control-button:hover {
  background-color: #f1f5f9 !important;
  color: #e11d48 !important;
}
.leaflet-pm-actions-container {
  background-color: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
}
.leaflet-pm-action {
  color: #0f172a !important;
}

/* Custom GIS Popup Styling */
.custom-gis-popup .leaflet-popup-content-wrapper {
  background-color: #ffffff !important;
  border-radius: 14px !important;
  box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.2) !important;
  border: 1px solid #cbd5e1 !important;
  padding: 2px !important;
}
.custom-gis-popup .leaflet-popup-tip {
  background-color: #ffffff !important;
}

/* Ensure Leaflet bottom controls float above the docked status bar without colliding */
.leaflet-bottom {
  bottom: 30px !important;
}

/* Hide Leaflet default attribution text from overlapping status bar metrics */
.leaflet-control-attribution {
  display: none !important;
}

/* Leaflet Scale Bar (Professional GIS Styling) */
.leaflet-control-scale {
  margin-bottom: 8px !important;
  margin-left: 14px !important;
}
.leaflet-control-scale-line {
  border: 2px solid #0f172a !important;
  border-top: none !important;
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(8px) !important;
  color: #0f172a !important;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  padding: 3px 6px 2px !important;
  border-radius: 0 0 5px 5px !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15) !important;
  letter-spacing: 0.025em !important;
}

/* Sembunyikan bubble teks petunjuk bawaan Geoman saat menggambar (Click first marker to finish, dll) */
.leaflet-pm-tooltip,
.pm-tooltip {
  display: none !important;
}

/* Styling Khusus Mode Hapus Titik (Studio Perbaikan Topologi) */
#topology-surgery-map-canvas.delete-vertex-active .leaflet-marker-icon {
  cursor: crosshair !important;
  filter: hue-rotate(140deg) saturate(3) drop-shadow(0 0 6px rgba(239, 68, 68, 0.95)) !important;
  transition: transform 0.15s ease, filter 0.15s ease !important;
}
#topology-surgery-map-canvas.delete-vertex-active .leaflet-marker-icon:hover {
  transform: scale(1.45) !important;
  filter: hue-rotate(140deg) saturate(5) drop-shadow(0 0 10px #ef4444) !important;
}

/* Styling Khusus Titik Terpilih (Multi-Select Vertex via Shift+Click / Multi-Pilih) */
.selected-vertex-marker {
  background: #3B82F6 !important;
  border: 2.5px solid #FFFFFF !important;
  border-radius: 50% !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.7), 0 0 14px rgba(59, 130, 246, 0.95) !important;
  transform: scale(1.45) !important;
  z-index: 1000 !important;
  cursor: pointer !important;
  animation: surgeryVertexPulse 1.6s infinite ease-in-out !important;
}

@keyframes surgeryVertexPulse {
  0% {
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.7), 0 0 10px rgba(59, 130, 246, 0.8);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.35), 0 0 18px rgba(59, 130, 246, 1);
  }
  100% {
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.7), 0 0 10px rgba(59, 130, 246, 0.8);
  }
}
</style>

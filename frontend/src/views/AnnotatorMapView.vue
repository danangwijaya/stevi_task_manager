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
          <option v-for="t in tasksStore.tasks" :key="t.id" :value="t.id">
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

      <!-- Revision Notes (if any) -->
      <div
        v-if="tasksStore.currentTask?.reviewer_notes && tasksStore.currentTask?.status === 'REVISION_NEEDED'"
        class="m-3 p-3 bg-rose-50 border border-rose-200 rounded-xl text-[11px] text-rose-800 space-y-1 shadow-2xs"
      >
        <div class="font-bold flex items-center gap-1.5 text-rose-700">
          <AlertTriangle :size="14" />
          <span>Catatan Revisi Reviewer:</span>
        </div>
        <div class="text-[11px] text-rose-900/90 leading-tight italic">"{{ tasksStore.currentTask.reviewer_notes }}"</div>
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

          <button
            @click="saveAnnotations"
            :disabled="annotationsStore.saving"
            class="bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold px-3.5 py-1.5 rounded-xl border border-slate-300 transition-all flex items-center gap-1.5 shadow-xs cursor-pointer"
          >
            <RotateCw v-if="annotationsStore.saving" :size="13" class="animate-spin text-slate-500" />
            <Save v-else :size="13" class="text-slate-500" />
            <span class="hidden sm:inline">Simpan Draf</span>
          </button>

          <button
            v-if="tasksStore.currentTask && tasksStore.currentTask.status !== 'APPROVED'"
            @click="submitForReview"
            class="bg-gradient-to-r from-rose-600 to-red-500 hover:from-rose-500 hover:to-red-400 text-white text-xs font-bold px-4 py-1.5 rounded-xl shadow-md shadow-rose-500/20 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <Send :size="13" />
            <span>Submit Review QC</span>
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

      <!-- Topology Results Banner -->
      <div
        v-if="topologyResult && !topologyResult.valid"
        class="bg-rose-50 border-b border-rose-200 px-4 py-2 text-xs text-rose-900 z-10 shrink-0 shadow-xs"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <AlertTriangle :size="14" class="text-rose-600 shrink-0" />
            <span><b>Masalah Topologi ({{ topologyResult.errors.length }}):</b></span>
          </div>
          <button @click="topologyResult = null" class="text-rose-400 hover:text-rose-600 cursor-pointer">
            <X :size="14" />
          </button>
        </div>
        <ul class="mt-1 space-y-0.5 ml-5">
          <li v-for="(err, idx) in topologyResult.errors.slice(0, 5)" :key="idx" class="text-[11px] text-rose-800 list-disc">
            <span class="font-mono text-[10px] text-rose-500">[{{ err.type }}]</span> {{ err.message }}
          </li>
          <li v-if="topologyResult.errors.length > 5" class="text-[11px] text-rose-600 italic">
            ...dan {{ topologyResult.errors.length - 5 }} error lainnya
          </li>
        </ul>
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
          class="absolute top-4 left-4 z-20 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-slate-200 p-1.5 flex flex-col gap-1 transition-all duration-200"
          :class="isToolboxCollapsed ? 'w-auto' : 'w-44'"
        >
          <!-- Header Bar with Title & Collapse/Expand Button -->
          <div class="flex items-center justify-between px-1.5 py-1 border-b border-slate-100 mb-0.5">
            <button
              @click="isToolboxCollapsed = !isToolboxCollapsed"
              class="flex items-center gap-1.5 text-slate-700 hover:text-rose-600 transition-colors cursor-pointer w-full justify-between"
              :title="isToolboxCollapsed ? 'Klik untuk membuka panel tools' : 'Klik untuk menyembunyikan/menciutkan panel tools'"
            >
              <div class="flex items-center gap-1.5">
                <Wrench :size="13" class="text-rose-600 shrink-0" />
                <span v-if="!isToolboxCollapsed" class="text-[10px] font-black uppercase tracking-wider text-slate-700">Tools Digitasi</span>
                <span v-else class="text-[10px] font-bold text-slate-600">Tools</span>
              </div>
              <ChevronDown v-if="isToolboxCollapsed" :size="13" class="text-slate-400 shrink-0" />
              <ChevronUp v-else :size="13" class="text-slate-400 shrink-0" />
            </button>
          </div>

          <!-- Collapsed Summary: Mini Icon Button -->
          <div v-if="isToolboxCollapsed" class="flex flex-col gap-1 items-center py-0.5">
            <button
              @click="isToolboxCollapsed = false"
              class="p-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 text-[10px] font-bold flex items-center justify-center cursor-pointer transition-all border border-slate-200 hover:border-rose-300"
              title="Klik untuk membuka semua tools digitasi"
            >
              <Scissors v-if="activeTool === 'split_line'" :size="15" class="text-rose-600" />
              <Layers v-else-if="activeTool === 'split_poly'" :size="15" class="text-rose-600" />
              <LassoSelect v-else-if="activeTool === 'freehand_cut'" :size="15" class="text-rose-600" />
              <PenTool v-else-if="activeTool === 'draw_poly'" :size="15" class="text-rose-600" />
              <Spline v-else-if="activeTool === 'freehand_poly'" :size="15" class="text-rose-600" />
              <Combine v-else-if="activeTool === 'merge'" :size="15" class="text-indigo-600" />
              <Edit3 v-else-if="activeTool === 'edit'" :size="15" class="text-amber-500" />
              <Trash2 v-else-if="activeTool === 'delete'" :size="15" class="text-rose-600" />
              <MousePointer v-else :size="15" class="text-slate-700" />
            </button>
          </div>

          <!-- Expanded Content: Full Tools & Transparency Controls -->
          <template v-else>
            <!-- Tool: Select / Pointer -->
            <button
              @click="setDigitizeMode(null)"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === null ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Pilih / Ubah Kelas: Klik poligon untuk memilih dan mengganti jenis tutupan lahan"
            >
              <MousePointer :size="15" />
              <span class="text-[11px]">Pilih Poligon</span>
            </button>

            <!-- Tool: Split with Line (Blade) -->
            <button
              @click="setDigitizeMode('split_line')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'split_line' ? 'bg-rose-600 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Potong dengan Garis: Tarik garis melintasi poligon untuk membaginya menjadi 2 bagian"
            >
              <Scissors :size="15" />
              <span class="text-[11px]">Potong Garis</span>
            </button>

            <!-- Tool: Split with Polygon (Cookie Cutter) -->
            <button
              @click="setDigitizeMode('split_poly')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'split_poly' ? 'bg-rose-600 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Potong Area: Gambar poligon untuk membagi area dalam dan luar tanpa menghapus"
            >
              <Layers :size="15" />
              <span class="text-[11px]">Potong Area</span>
            </button>

            <!-- Tool: Freehand Cut (Lasso Cookie Cutter) -->
            <button
              @click="setDigitizeMode('freehand_cut')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'freehand_cut' ? 'bg-rose-600 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Potong Bebas: Tahan & lingkari area untuk memotong poligon secara instan tanpa klik berulang"
            >
              <LassoSelect :size="15" />
              <span class="text-[11px]">Potong Bebas</span>
            </button>

            <!-- Tool: Draw Standard Polygon -->
            <button
              @click="setDigitizeMode('draw_poly')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'draw_poly' ? 'bg-rose-600 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Gambar Poligon Biasa (Klik titik demi titik, Backspace untuk batalkan titik)"
            >
              <PenTool :size="15" />
              <span class="text-[11px]">Gambar Poligon</span>
            </button>

            <!-- Tool: Freehand / Stream Polygon Draw -->
            <button
              @click="setDigitizeMode('freehand_poly')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'freehand_poly' ? 'bg-rose-600 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Freehand Stream: Tahan & geser mouse untuk menggambar kurva meliuk (sungai/hutan) secara mengalir & mulus"
            >
              <Spline :size="15" />
              <span class="text-[11px]">Freehand Stream</span>
            </button>

            <!-- Tool: Merge Polygons -->
            <button
              @click="setDigitizeMode('merge')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'merge' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Gabung Poligon: Pilih 2 atau lebih poligon untuk disatukan"
            >
              <Combine :size="15" />
              <span class="text-[11px]">Gabung Poligon</span>
            </button>

            <!-- Tool: Edit Vertices -->
            <button
              @click="setDigitizeMode('edit')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'edit' ? 'bg-amber-500 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-100'"
              title="Edit Titik Sudut Poligon"
            >
              <Edit3 :size="15" />
              <span class="text-[11px]">Edit Titik</span>
            </button>

            <!-- Tool: Delete Polygon -->
            <button
              @click="setDigitizeMode('delete')"
              class="p-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer text-left"
              :class="activeTool === 'delete' ? 'bg-rose-100 text-rose-700 border border-rose-300' : 'text-slate-700 hover:bg-slate-100'"
              title="Hapus Poligon yang Diklik"
            >
              <Trash2 :size="15" />
              <span class="text-[11px]">Hapus Poligon</span>
            </button>

            <!-- Quick Undo & Redo in Toolbox -->
            <div class="grid grid-cols-2 gap-1 pt-0.5">
              <button
                @click="undo"
                :disabled="!canUndo"
                class="p-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 transition-all cursor-pointer border border-slate-200 bg-slate-50 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed"
                title="Undo (Ctrl+Z)"
              >
                <Undo2 :size="12" />
                <span>Undo</span>
              </button>
              <button
                @click="redo"
                :disabled="!canRedo"
                class="p-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 transition-all cursor-pointer border border-slate-200 bg-slate-50 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed"
                title="Redo (Ctrl+Y)"
              >
                <Redo2 :size="12" />
                <span>Redo</span>
              </button>
            </div>

            <div class="border-t border-slate-200 my-0.5"></div>

            <!-- Active Selected Class Indicator in Toolbar -->
            <div class="p-1.5 bg-slate-50 rounded-xl border border-slate-200 text-[10px] space-y-1">
              <div class="text-[9px] text-slate-400 font-bold uppercase">Kelas Aktif:</div>
              <div class="flex items-center gap-1.5">
                <div class="w-3 h-3 rounded-sm shrink-0 border border-slate-300" :style="{ backgroundColor: annotationsStore.selectedClass?.color || '#006400' }"></div>
                <span class="font-bold truncate text-slate-800 text-[10px]">{{ annotationsStore.selectedClass?.name || 'Hutan Lahan Kering' }}</span>
              </div>
            </div>

            <!-- Opacity & Transparency Control inside Toolbar -->
            <div class="p-1.5 bg-slate-50 rounded-xl border border-slate-200 text-[10px] space-y-1">
              <div class="flex items-center justify-between text-[9px] font-bold text-slate-500">
                <span class="uppercase">Transparansi:</span>
                <span class="font-mono text-rose-600 font-black">{{ Math.round(polygonOpacity * 100) }}%</span>
              </div>
              <div class="flex items-center gap-1.5">
                <button
                  @click="togglePeekVisibility"
                  class="p-0.5 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-200 cursor-pointer"
                  :title="isPeekHidden ? 'Tampilkan kembali poligon' : 'Intip citra satelit (sembunyikan poligon)'"
                >
                  <EyeOff v-if="isPeekHidden" :size="12" class="text-rose-600" />
                  <Eye v-else :size="12" class="text-slate-500" />
                </button>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  v-model="polygonOpacity"
                  @input="updateOpacity"
                  class="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-600"
                  title="Atur transparansi kenampakan hasil digitasi poligon"
                />
              </div>
              <!-- Presets -->
              <div class="grid grid-cols-3 gap-1 pt-0.5">
                <button
                  @click="setOpacityPreset(0)"
                  class="py-0.5 rounded text-[9px] font-bold border transition-all cursor-pointer text-center"
                  :class="polygonOpacity === 0 ? 'bg-rose-600 text-white border-rose-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                  title="Transparan 100% (hanya garis batas)"
                >
                  0%
                </button>
                <button
                  @click="setOpacityPreset(0.5)"
                  class="py-0.5 rounded text-[9px] font-bold border transition-all cursor-pointer text-center"
                  :class="polygonOpacity === 0.5 ? 'bg-rose-600 text-white border-rose-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                  title="Transparansi Sedang 50%"
                >
                  50%
                </button>
                <button
                  @click="setOpacityPreset(0.85)"
                  class="py-0.5 rounded text-[9px] font-bold border transition-all cursor-pointer text-center"
                  :class="polygonOpacity === 0.85 ? 'bg-rose-600 text-white border-rose-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
                  title="Solid 85%"
                >
                  85%
                </button>
              </div>
            </div>

            <!-- Kontrol Transparansi Grid Sebelah / Luar Grid -->
            <div class="p-1.5 bg-slate-50 rounded-xl border border-slate-200 text-[10px] space-y-1">
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
            <div class="p-2 bg-gradient-to-br from-indigo-50/70 to-slate-50 rounded-xl border border-indigo-100 text-[10px] space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5 font-bold text-indigo-900">
                  <component :is="showNeighborPolygons ? Eye : EyeOff" :size="12" class="text-indigo-600" />
                  <span>Poligon Grid Sebelah</span>
                </div>
                <button
                  @click="toggleNeighborPolygons"
                  type="button"
                  class="relative inline-flex h-4 w-7 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                  :class="showNeighborPolygons ? 'bg-indigo-600' : 'bg-slate-300'"
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
                <span v-if="isLoadingNeighbors" class="text-indigo-600 animate-pulse font-semibold">Memuat...</span>
                <span v-else-if="showNeighborPolygons" class="text-indigo-700 font-semibold bg-indigo-100/70 px-1 py-0.2 rounded text-[8.5px]">
                  {{ neighborFeaturesCount }} Poligon Terdeteksi
                </span>
                <span v-else class="text-slate-400">Non-Aktif</span>
              </div>

              <!-- Slider Transparansi Poligon Tetangga (jika aktif) -->
              <div v-if="showNeighborPolygons" class="space-y-1 pt-1 border-t border-indigo-100/80">
                <div class="flex items-center justify-between text-[9px] text-indigo-950">
                  <span class="text-slate-500">Transparansi Poligon:</span>
                  <span class="font-mono font-bold">{{ Math.round(neighborPolygonsOpacity * 100) }}%</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.8"
                  step="0.05"
                  v-model.number="neighborPolygonsOpacity"
                  @input="updateNeighborOpacity"
                  class="w-full h-1 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  title="Atur transparansi warna poligon grid sebelah"
                />
                <div class="text-[8px] text-slate-400 leading-tight">
                  * Garis putus-putus acuan sambungan (read-only)
                </div>
              </div>
            </div>

            <!-- Keyboard Quick Tips (Smooth GIS Experience) -->
            <div class="px-2 py-1.5 bg-slate-100/90 rounded-xl text-[9px] text-slate-500 leading-tight space-y-1 border border-slate-200/60">
              <div class="flex items-center justify-between">
                <span>Tahan <kbd class="px-1 py-0.2 bg-white rounded border border-slate-300 font-mono text-slate-700 font-bold">Spasi</kbd></span>
                <span class="text-slate-400">Intip Citra</span>
              </div>
              <div class="flex items-center justify-between">
                <span><kbd class="px-1 py-0.2 bg-white rounded border border-slate-300 font-mono text-slate-700 font-bold">⌫ Del</kbd></span>
                <span class="text-slate-400">Undo Titik</span>
              </div>
            </div>
          </template>
        </div>

        <!-- Merge Mode Floating Bar (shows when merge mode is active) -->
        <div v-if="activeTool === 'merge'" class="absolute top-4 left-44 z-20 bg-indigo-900 text-white rounded-2xl shadow-xl p-3 flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
          <div class="text-xs">
            <span class="font-bold">Mode Gabung:</span> Klik poligon di peta untuk memilih (Terpilih: <b>{{ selectedForMerge.length }}</b>)
          </div>
          <button
            @click="executeMerge"
            :disabled="selectedForMerge.length < 2 || mergeLoading"
            class="px-3 py-1 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Combine :size="13" />
            <span>{{ mergeLoading ? 'Menggabungkan...' : 'Satukan Poligon' }}</span>
          </button>
          <button @click="cancelMerge" class="text-slate-300 hover:text-white text-xs font-semibold cursor-pointer">
            Batal
          </button>
        </div>

        <!-- Floating Map Top-Right Controls: Imagery & Spectral Adjustment Panel -->
        <div class="absolute top-4 right-4 z-20 flex flex-col flex-nowrap items-end gap-2 pointer-events-auto">
          <!-- Trigger Button on Map -->
          <button
            @click="showImageryPanel = !showImageryPanel"
            class="flex items-center gap-2 px-3 py-2 bg-white/95 hover:bg-white text-slate-800 rounded-2xl shadow-lg border border-slate-200/90 backdrop-blur-md text-xs font-bold transition-all hover:scale-102 active:scale-98 cursor-pointer"
            :class="showImageryPanel ? 'ring-2 ring-rose-500 text-rose-600 bg-rose-50/90' : ''"
            title="Buka Pengaturan Citra, Komposit, Kontras & Gamma"
          >
            <SlidersHorizontal :size="14" class="text-rose-600" />
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

        <!-- Floating Live Map Info Pill (Zoom, Representative Scale, Coordinates) -->
        <div class="absolute bottom-3 left-48 z-10 hidden sm:flex items-center gap-2 pointer-events-none">
          <div class="bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-300/90 shadow-md text-[11px] font-mono font-bold text-slate-700 flex items-center gap-2 pointer-events-auto select-none">
            <span class="flex items-center gap-1 text-slate-500">
              <Compass :size="12" class="text-rose-600" />
              <span>Z{{ mapZoom }}</span>
            </span>
            <span class="text-slate-300">•</span>
            <span class="text-slate-900 font-black" title="Estimasi Skala Representatif Peta">Skala {{ mapScaleRatio }}</span>
            <template v-if="cursorCoords.lat">
              <span class="text-slate-300">•</span>
              <span class="text-[10px] text-slate-500" title="Koordinat Kursor (WGS84)">{{ cursorCoords.lat }}°, {{ cursorCoords.lng }}°</span>
            </template>
          </div>
        </div>
      </div>

      <!-- Toast Notification -->
      <div
        v-if="toastMessage"
        class="absolute bottom-6 left-1/2 -translate-x-1/2 bg-slate-900 text-white border border-slate-700 px-4 py-2 rounded-2xl shadow-2xl z-30 text-xs font-bold flex items-center gap-2 backdrop-blur-md animate-bounce"
      >
        <CheckCircle2 :size="14" class="text-emerald-400" />
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
          <b class="font-bold text-slate-800">{{ features[clickedFeatureIdx]?.properties?.class_name || 'Belum Terklasifikasi' }}</b>
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
            @click="deleteClickedPolygon"
            class="flex-1 py-1 px-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 transition-all cursor-pointer"
          >
            <Trash2 :size="12" />
            <span>Hapus Poligon</span>
          </button>
          <button
            @click="flyToFeature(clickedFeatureIdx)"
            class="py-1 px-2.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 transition-all cursor-pointer"
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

      <!-- Tab Content 2: List of Drawn Polygons -->
      <div v-show="rightTab === 'polygons'" class="flex-1 p-3 space-y-2 overflow-y-auto">
        <div v-if="features.length === 0" class="text-center py-12 text-slate-400 text-xs">
          Belum ada poligon yang digambar.<br>Gunakan tool Potong / Gambar di kiri atas peta!
        </div>

        <div
          v-for="(feat, idx) in features"
          :key="idx"
          @click="selectFeatureFromList(idx)"
          class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1 hover:border-slate-300 transition-all text-xs cursor-pointer"
          :class="clickedFeatureIdx === idx ? 'ring-2 ring-indigo-500 border-indigo-400 bg-indigo-50/40' : ''"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div
                class="w-3 h-3 rounded-sm border border-slate-300"
                :style="{ backgroundColor: feat.properties?.color || '#9CA3AF' }"
              ></div>
              <span class="font-bold text-slate-800">{{ feat.properties?.class_name || 'Belum Terklasifikasi' }}</span>
            </div>
            <span class="text-[10px] text-slate-400 font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">#{{ idx + 1 }}</span>
          </div>

          <div class="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
            <span class="font-mono">Luas: ~{{ Math.round((feat.properties?.area_sqm || 10000) / 10000) }} Ha</span>
            <span v-if="feat.properties?.class_id === 0" class="text-amber-600 font-bold">⚠️ Belum di-assign</span>
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
  RefreshCcw
} from 'lucide-vue-next'
import * as turf from '@turf/turf'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import { useAnnotationsStore } from '../stores/annotations'
import api from '../services/api'
import { imageMapLayer } from 'esri-leaflet'

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

// Active GIS Digitize Mode
const activeTool = ref(null) // null | 'split_line' | 'split_poly' | 'draw_poly' | 'merge' | 'edit' | 'delete'
const selectedForMerge = ref([]) // array of selected feature objects
const mergeLoading = ref(false)

let _featureUiCounter = 0
const getFeatureUiId = (feat) => {
  if (!feat) return 'f_' + (++_featureUiCounter)
  if (feat._uiId) return feat._uiId
  const id = feat.id || feat.properties?.id
  const uiId = id ? `f_id_${id}` : `f_tmp_${Date.now()}_${++_featureUiCounter}`
  feat._uiId = uiId
  return uiId
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
}

const undo = async () => {
  if (!canUndo.value) return
  historyIndex.value--
  const snapshot = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  restoreFeaturesToMap(snapshot)
  showToast('↩️ Undo: Perubahan dibatalkan')
  if (selectedTaskId.value) {
    try {
      await annotationsStore.saveGridAnnotations(selectedTaskId.value, snapshot)
    } catch {}
  }
}

const redo = async () => {
  if (!canRedo.value) return
  historyIndex.value++
  const snapshot = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  restoreFeaturesToMap(snapshot)
  showToast('↪️ Redo: Perubahan diterapkan kembali')
  if (selectedTaskId.value) {
    try {
      await annotationsStore.saveGridAnnotations(selectedTaskId.value, snapshot)
    } catch {}
  }
}

const restoreFeaturesToMap = (snapshotFeatures) => {
  if (!featureGroup || !map) return
  clickedFeatureIdx.value = null
  map.closePopup()

  featureGroup.clearLayers()
  features.value = snapshotFeatures

  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  snapshotFeatures.forEach(feat => {
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
      const cls = classesMap[feat.properties?.class_id]
      if (cls) l.feature.properties.color = cls.color
      else l.feature.properties.color = feat.properties?.color || '#9CA3AF'
      bindLayerEvents(l)
      featureGroup.addLayer(l)
    })
  })
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
    showToast('👁️ Tahan Spasi: Mengintip citra satelit asli (Lepas untuk kembali)')
    return
  }

  // 2. Single-Vertex Undo: Backspace / Delete during active polygon or line drawing
  if (e.key === 'Backspace' || e.key === 'Delete') {
    if (map && map.pm && map.pm.Draw) {
      const activeShape = map.pm.Draw.getActiveShape?.()
      if (activeShape && map.pm.Draw[activeShape]?._removeLastVertex) {
        e.preventDefault()
        map.pm.Draw[activeShape]._removeLastVertex()
        showToast('↩️ Titik terakhir dibatalkan (Backspace)')
        return
      }
    }
  }

  // 3. Escape key: cancel active draw mode or reset to pointer
  if (e.key === 'Escape') {
    if (activeTool.value) {
      setDigitizeMode(null)
      showToast('👆 Mode dinonaktifkan (Kembali ke Pilih Poligon)')
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
  } else if (cmdOrCtrl && e.key.toLowerCase() === 'y') {
    e.preventDefault()
    redo()
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
const features = ref([])
const outsideDimOpacity = ref(0.12) // Default lembut agar citra grid sebelah terlihat jernih
const showNeighborPolygons = ref(false) // Default OFF agar kanvas bersih, mapper bisa aktifkan saat perlu edge-matching
const neighborPolygonsOpacity = ref(0.4)
const neighborFeaturesCount = ref(0)
const isLoadingNeighbors = ref(false)

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
        layer.options.pmIgnore = true
        layer.options.snapIgnore = false
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
    maxNativeZoom: conf.maxNativeZoom,
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

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('keyup', handleKeyup)
  
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
    selectedTaskId.value = tasksStore.tasks[0].id
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

function onMapMouseMove(e) {
  if (e && e.latlng) {
    cursorCoords.value = {
      lat: e.latlng.lat.toFixed(5),
      lng: e.latlng.lng.toFixed(5)
    }
  }
}

const initMap = () => {
  if (map) return

  map = L.map('map-container', {
    center: [-0.947, 100.370],
    zoom: 13,
    maxZoom: 16, // Maksimal zoom in dibatasi di level 16 (skala ~300 meter)
    minZoom: 9,
    zoomControl: false
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
  map.on('mousemove', onMapMouseMove)
  updateMapScaleInfo()

  // Satellite Basemap
  updateTileLayer()

  // Feature Group for actively drawn/editable polygons
  featureGroup = L.featureGroup().addTo(map)

  map.pm.setGlobalOptions({
    snappable: true,
    snapDistance: 22,
    snapSegment: true,
    snapMiddleMarkers: true,
    allowSelfIntersection: false
  })

  // Freehand / Stream mode mouse bindings
  map.on('mousedown', onMapMouseDown)
  map.on('mousemove', onMapMouseMoveFreehand)
  map.on('mouseup', onMapMouseUp)
  window.addEventListener('mouseup', onMapMouseUp)

  // Hook creation events from Geoman
  map.on('pm:create', async (e) => {
    const layer = e.layer
    const layerGeoJSON = layer.toGeoJSON()

    // 1. If in split_line mode (LineString drawn)
    if (activeTool.value === 'split_line') {
      map.removeLayer(layer)
      await handleSplitByLine(layerGeoJSON.geometry)
      return
    }

    // 2. If in split_poly mode (Polygon drawn)
    if (activeTool.value === 'split_poly') {
      map.removeLayer(layer)
      await handleSplitByPolygon(layerGeoJSON.geometry)
      return
    }

    // 3. If in standard draw mode
    const currentClass = annotationsStore.selectedClass || annotationsStore.classes.find(c => c.id !== 0) || annotationsStore.classes[0]
    
    const uiId = 'f_draw_' + Date.now() + '_' + (++_featureUiCounter)
    layer._uiId = uiId
    layer.feature = {
      type: 'Feature',
      _uiId: uiId,
      geometry: layerGeoJSON.geometry,
      properties: {
        class_id: currentClass?.id || 1,
        class_name: currentClass?.name || 'Hutan Lahan Kering',
        color: currentClass?.color || '#006400'
      }
    }

    styleLayer(layer, currentClass?.color || '#006400')
    bindLayerEvents(layer)
    featureGroup.addLayer(layer)
    syncFeaturesFromMap()
    pushHistory()
    showToast(`Poligon [${currentClass?.name}] ditambahkan`)
  })

  map.on('pm:remove', () => {
    clickedFeatureIdx.value = null
    syncFeaturesFromMap()
    pushHistory()
  })

  map.on('pm:edit', () => {
    syncFeaturesFromMap()
    pushHistory()
  })

  map.on('pm:dragend', () => {
    syncFeaturesFromMap()
    pushHistory()
  })
}

// ── FREEHAND / STREAM CURVE DIGITIZING ───────────────────
let isDrawingFreehand = false
let freehandPoints = []
let freehandPolyline = null

const onMapMouseDown = (e) => {
  if (!['freehand_poly', 'freehand_cut'].includes(activeTool.value)) return
  if (e.originalEvent && e.originalEvent.button !== 0) return

  isDrawingFreehand = true
  if (map) map.dragging.disable()
  freehandPoints = [e.latlng]

  const currentClass = annotationsStore.selectedClass || annotationsStore.classes.find(c => c.id !== 0) || annotationsStore.classes[0]
  const strokeColor = activeTool.value === 'freehand_cut' ? '#E11D48' : (currentClass?.color || '#006400')

  if (freehandPolyline && map) {
    map.removeLayer(freehandPolyline)
  }

  freehandPolyline = L.polyline([e.latlng], {
    color: strokeColor,
    weight: activeTool.value === 'freehand_cut' ? 3.5 : 3,
    dashArray: '4, 4',
    opacity: 0.95
  }).addTo(map)
}

const onMapMouseMoveFreehand = (e) => {
  if (!isDrawingFreehand || (!['freehand_poly', 'freehand_cut'].includes(activeTool.value)) || !freehandPolyline || !map) return

  const lastPoint = freehandPoints[freehandPoints.length - 1]
  const p1 = map.latLngToLayerPoint(lastPoint)
  const p2 = map.latLngToLayerPoint(e.latlng)

  // Record point every 6 screen pixels for silky smooth natural curves
  if (p1.distanceTo(p2) >= 6) {
    freehandPoints.push(e.latlng)
    freehandPolyline.setLatLngs(freehandPoints)
  }
}

const onMapMouseUp = async () => {
  if (!isDrawingFreehand || (!['freehand_poly', 'freehand_cut'].includes(activeTool.value))) return
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

    // ── CASE 1: FREEHAND CUT (Lasso Cookie Cutter) ──
    if (activeTool.value === 'freehand_cut') {
      await handleSplitByPolygon(polyGeoJSON.geometry)
      return
    }

    // ── CASE 2: FREEHAND CREATE NEW POLYGON ──
    const currentClass = annotationsStore.selectedClass || annotationsStore.classes.find(c => c.id !== 0) || annotationsStore.classes[0]
    const layer = L.geoJSON(polyGeoJSON, {
      style: () => ({
        color: currentClass?.color || '#006400',
        fillColor: currentClass?.color || '#006400',
        fillOpacity: polygonOpacity.value,
        weight: 2
      })
    }).getLayers()[0]

    if (layer) {
      layer.feature = layer.feature || { type: 'Feature', properties: {} }
      layer.feature.properties = {
        class_id: currentClass?.id || 1,
        class_name: currentClass?.name || 'Hutan Lahan Kering',
        color: currentClass?.color || '#006400'
      }

      styleLayer(layer, currentClass?.color || '#006400')
      bindLayerEvents(layer)
      featureGroup.addLayer(layer)
      syncFeaturesFromMap()
      pushHistory()
      showToast(`✨ Poligon Freehand [${currentClass?.name}] berhasil dibuat!`)
    }
  } catch (err) {
    console.error('Failed to process freehand action:', err)
    showToast('⚠️ Gagal memproses freehand. Coba gambar kembali.')
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
  }

  // Always close any open popup and clear selection
  map.closePopup()

  // Disable any active Geoman modes
  map.pm.disableDraw()
  map.pm.disableGlobalEditMode()
  map.pm.disableGlobalRemovalMode()
  map.pm.disableGlobalDragMode()

  if (!force && activeTool.value === mode) {
    activeTool.value = null
    showToast('👆 Mode Pilih Poligon Aktif')
    return
  }

  activeTool.value = mode
  selectedForMerge.value = []

  switch (mode) {
    case null:
      showToast('👆 Mode Pilih Poligon: Klik poligon untuk ubah kelas / inspeksi')
      break

    case 'freehand_cut':
      showToast('✂️ Mode Potong Bebas (Lasso Cut): Tahan & lingkari area untuk memotong poligon secara instan')
      break

    case 'freehand_poly':
      showToast('〰️ Mode Freehand Stream: Klik & tahan mouse, lalu gerakkan untuk menggambar kurva mulus')
      break

    case 'split_line':
      showToast('✂️ Mode Potong Garis: Tarik garis melintasi poligon dari batas ke batas')
      map.pm.enableDraw('Line', {
        snappable: true,
        snapDistance: 22,
        snapSegment: true
      })
      break

    case 'split_poly':
      showToast('🔪 Mode Potong Area: Gambar poligon untuk membagi area tanpa menghapus')
      map.pm.enableDraw('Polygon', {
        snappable: true,
        snapDistance: 22,
        snapSegment: true
      })
      break

    case 'draw_poly':
      showToast('✏️ Mode Gambar Poligon Baru (Klik titik demi titik, Backspace untuk batalkan titik)')
      map.pm.enableDraw('Polygon', {
        snappable: true,
        snapDistance: 22,
        snapSegment: true
      })
      break

    case 'edit':
      showToast('✋ Mode Edit Titik: Klik dan geser titik sudut poligon')
      map.pm.enableGlobalEditMode()
      break

    case 'delete':
      showToast('🗑️ Mode Hapus: Klik poligon yang ingin dihapus')
      map.pm.enableGlobalRemovalMode()
      break

    case 'merge':
      showToast('🔗 Mode Gabung: Klik 2 atau lebih poligon pada peta lalu klik "Satukan Poligon"')
      break
  }
}

// Handle Line Split
const handleSplitByLine = async (lineGeom) => {
  if (!selectedTaskId.value) return
  const previousTool = activeTool.value
  showToast('Memproses pemotongan garis...')

  // Get active class for newly created slice
  const newClass = annotationsStore.selectedClass || annotationsStore.classes.find(c => c.id !== 0) || annotationsStore.classes[0]

  try {
    const res = await api.splitByLine(selectedTaskId.value, lineGeom, null, newClass?.id || 0)
    showToast(res.data?.message || 'Poligon berhasil dipotong!')
    await loadTaskData(selectedTaskId.value, true)
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal memotong poligon. Pastikan garis melintasi batas poligon.')
  } finally {
    if (previousTool) {
      setDigitizeMode(previousTool, true)
    }
  }
}

// Handle Polygon Cut / Split
const handleSplitByPolygon = async (cuttingGeom) => {
  if (!selectedTaskId.value) return
  const previousTool = activeTool.value
  showToast('Memproses pemisahan area poligon...')

  const newClass = annotationsStore.selectedClass || annotationsStore.classes.find(c => c.id !== 0) || annotationsStore.classes[0]

  try {
    const res = await api.splitByPolygon(selectedTaskId.value, cuttingGeom, null, newClass?.id || 0)
    showToast(res.data?.message || 'Poligon berhasil dipisah menjadi bagian mandiri!')
    await loadTaskData(selectedTaskId.value, true)
  } catch (err) {
    alert(err.response?.data?.detail || 'Gagal memotong area. Pastikan poligon pemotong beririsan dengan poligon target.')
  } finally {
    if (previousTool) {
      setDigitizeMode(previousTool, true)
    }
  }
}

// Handle Merge Polygons
const executeMerge = async () => {
  if (selectedForMerge.value.length < 2 || !selectedTaskId.value) return
  mergeLoading.value = true

  const targetClass = annotationsStore.selectedClass || annotationsStore.classes.find(c => c.id !== 0) || annotationsStore.classes[0]
  const targetClassId = targetClass?.id || 1
  const targetClassName = targetClass?.name || 'Hutan Lahan Kering'
  const targetColor = targetClass?.color || '#006400'

  const annotationIds = selectedForMerge.value.map(f => f.id || f.properties?.id).filter(Boolean)

  try {
    // If backend IDs exist for all selected polygons, use backend merge API
    if (annotationIds.length === selectedForMerge.value.length) {
      const res = await api.mergePolygons(selectedTaskId.value, annotationIds, targetClassId)
      showToast(res.data?.message || 'Poligon berhasil digabungkan!')
      await loadTaskData(selectedTaskId.value, true)
    } else {
      // Fallback: merge using Turf client-side union
      const validPolys = selectedForMerge.value.map(f => {
        let p = f.type === 'Feature' ? f : turf.feature(f.geometry || f)
        return p
      })
      const fc = turf.featureCollection(validPolys)
      const unioned = turf.union(fc)
      if (!unioned) {
        throw new Error('Gagal menyatukan poligon. Pastikan poligon saling bersentuhan atau bertampalan.')
      }

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
  activeTool.value = null
  refreshMapStyles()
}

// ─── INTERACTIVE POPUP & LAYER EVENTS ─────────────────────
const bindLayerEvents = (layer) => {
  layer.off('click')
  layer.on('click', (e) => {
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

    // 2. Mode digitizing / pemotongan lain: biarkan Geoman menangani tanpa popup
    if (activeTool.value !== null) {
      return
    }

    // 3. Mode Pilih Poligon (Pointer / default select mode: activeTool === null):
    L.DomEvent.stopPropagation(e)
    const idx = findFeatureIndexForLayer(layer)
    if (idx < 0) return

    const feat = features.value[idx] || layer.feature
    clickedFeatureIdx.value = idx
    rightTab.value = 'classes'
    refreshMapStyles()

    // Open Interactive Popup on Polygon
    openClassPickerPopup(layer, feat, idx, e.latlng)
  })
}

const openClassPickerPopup = (layer, feat, idx, latlng) => {
  const currentClassId = feat.properties?.class_id !== undefined ? feat.properties.class_id : 0
  const currentClassName = feat.properties?.class_name || 'Belum Terklasifikasi'
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

const deleteClickedPolygon = () => {
  if (clickedFeatureIdx.value === null || !featureGroup) return
  
  let layerIdx = 0
  let targetLayer = null
  featureGroup.eachLayer((layer) => {
    if (layerIdx === clickedFeatureIdx.value) {
      targetLayer = layer
    }
    layerIdx++
  })

  if (targetLayer) {
    featureGroup.removeLayer(targetLayer)
    clickedFeatureIdx.value = null
    syncFeaturesFromMap()
    pushHistory()
    showToast('Poligon dihapus')
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
    const isClicked = clickedFeatureIdx.value === idx
    const isMergedSelected = isFeatureSelectedForMerge(feat, layer)
    const color = layer.feature?.properties?.color || feat?.properties?.color || '#9CA3AF'

    let weight = 2
    let strokeColor = color
    let fillOpacity = polygonOpacity.value
    let strokeOpacity = polygonOpacity.value === 0 ? 0.35 : 1

    if (isClicked) {
      weight = 3.5
      strokeColor = '#4f46e5' // Indigo highlight
      fillOpacity = Math.max(polygonOpacity.value, 0.4)
      strokeOpacity = 1
    } else if (isMergedSelected) {
      weight = 3.5
      strokeColor = '#10b981' // Emerald highlight for merge
      fillOpacity = Math.max(polygonOpacity.value, 0.45)
      strokeOpacity = 1
    }

    layer.setStyle({
      color: strokeColor,
      fillColor: color,
      fillOpacity: fillOpacity,
      opacity: strokeOpacity,
      weight: weight
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
    showToast('👁️ Poligon disembunyikan (Hanya garis batas tipis) untuk memeriksa citra satelit')
  } else {
    polygonOpacity.value = previousOpacity.value > 0 ? previousOpacity.value : 0.6
    showToast(`👁️ Poligon ditampilkan kembali (${Math.round(polygonOpacity.value * 100)}%)`)
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
  topologyResult.value = null
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

  // 5. Load Existing Polygons
  featureGroup.clearLayers()
  const fetchedFeatures = await annotationsStore.fetchGridAnnotations(taskId)
  features.value = fetchedFeatures

  const classesMap = {}
  annotationsStore.classes.forEach(c => { classesMap[c.id] = c })

  if (fetchedFeatures.length > 0) {
    fetchedFeatures.forEach(feat => {
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
}

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
const runTopologyCheck = async () => {
  if (!selectedTaskId.value) return
  topologyLoading.value = true
  topologyResult.value = null

  // Save current state first
  await saveAnnotations()

  try {
    const res = await api.validateTopology(selectedTaskId.value)
    topologyResult.value = res.data
    if (res.data.valid) {
      showToast(`✅ Topologi valid! Coverage ${res.data.coverage_percent}%`)
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
      class_name: currentProps.class_name || 'Belum Terklasifikasi',
      color: currentProps.color || '#9CA3AF',
      area_sqm: currentProps.area_sqm || null
    }
    layer.feature = json
    newFeatures.push(json)
  })
  features.value = newFeatures
}

const saveAnnotations = async () => {
  if (!selectedTaskId.value) return
  syncFeaturesFromMap()

  const ok = await annotationsStore.saveGridAnnotations(selectedTaskId.value, features.value)
  if (ok) {
    showToast('Semua poligon draf berhasil disimpan!')
    await tasksStore.fetchTaskDetail(selectedTaskId.value)
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

  // Run topology validation before submit
  topologyLoading.value = true
  try {
    const topoRes = await api.validateTopology(selectedTaskId.value)
    topologyResult.value = topoRes.data

    if (!topoRes.data.valid) {
      const errorSummary = topoRes.data.errors.map(e => `• [${e.type}] ${e.message}`).join('\n')
      alert(`⚠️ Validasi Topologi Gagal!\n\nMasalah yang ditemukan:\n${errorSummary}\n\nPerbaiki masalah di atas sebelum submit untuk review QC.`)
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

/* Leaflet Scale Bar (Professional GIS Styling) */
.leaflet-control-scale {
  margin-bottom: 12px !important;
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
</style>

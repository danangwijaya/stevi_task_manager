<template>
  <div class="min-h-full bg-[#f0f2f5] font-sans text-[#2c3038]">

    <!-- Page Header -->
    <div class="bg-white border-b border-[#e4e7eb] px-6 lg:px-10 py-5">
      <div class="max-w-screen-xl mx-auto flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-[#d73f3f] flex items-center justify-center shadow-sm text-white">
            <Shield :size="20" />
          </div>
          <div>
            <h1 class="text-xl font-black text-[#1f242e] font-heading tracking-tight">Panel Admin</h1>
            <p class="text-xs text-[#707a8a]">Manajemen Proyek & Pengguna STEVI Task Manager</p>
          </div>
        </div>
        <div class="flex items-center gap-2 text-xs text-[#707a8a] bg-[#f0f2f5] px-3 py-1.5 rounded-lg border border-[#e4e7eb]">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Login sebagai <b class="text-[#1f242e]">{{ authStore.user?.full_name || 'Admin' }}</b></span>
        </div>
      </div>
    </div>

    <div class="max-w-screen-xl mx-auto px-4 lg:px-10 py-6 space-y-6">

      <!-- Tab Navigation -->
      <div class="flex flex-wrap gap-2 bg-white p-1.5 rounded-2xl border border-[#e4e7eb] shadow-xs w-fit">
        <button
          @click="activeTab = 'projects'"
          class="px-5 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2 cursor-pointer"
          :class="activeTab === 'projects'
            ? 'bg-[#d73f3f] text-white shadow-sm'
            : 'text-[#707a8a] hover:text-[#1f242e] hover:bg-[#f0f2f5]'"
        >
          <FolderKanban :size="16" />
          Manajemen Proyek
          <span class="text-[10px] bg-white/25 px-1.5 py-0.5 rounded font-mono">{{ adminStore.projects.length }}</span>
        </button>
        <button
          @click="activeTab = 'import'"
          class="px-5 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2 cursor-pointer"
          :class="activeTab === 'import'
            ? 'bg-[#d73f3f] text-white shadow-sm'
            : 'text-[#707a8a] hover:text-[#1f242e] hover:bg-[#f0f2f5]'"
        >
          <UploadCloud :size="16" />
          Import Grid Kustom (Shapefile / GeoJSON)
        </button>
        <button
          @click="activeTab = 'users'"
          class="px-5 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2 cursor-pointer"
          :class="activeTab === 'users'
            ? 'bg-[#d73f3f] text-white shadow-sm'
            : 'text-[#707a8a] hover:text-[#1f242e] hover:bg-[#f0f2f5]'"
        >
          <Users :size="16" />
          Manajemen Pengguna
          <span class="text-[10px] bg-white/25 px-1.5 py-0.5 rounded font-mono">{{ adminStore.users.length }}</span>
        </button>
      </div>

      <!-- ═══════════════════════════════════════ -->
      <!-- TAB 1: MANAJEMEN PROYEK                -->
      <!-- ═══════════════════════════════════════ -->
      <div v-if="activeTab === 'projects'" class="space-y-4">

        <!-- Toolbar -->
        <div class="flex items-center justify-between flex-wrap gap-3">
          <h2 class="text-base font-black text-[#1f242e] flex items-center gap-2">
            <Map :size="18" class="text-[#d73f3f]" />
            Daftar Proyek Tasking Grid
          </h2>
          <div class="flex items-center gap-2.5">
            <button
              @click="activeTab = 'import'"
              class="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs px-3.5 py-2 rounded-xl border border-slate-300 transition-all cursor-pointer shadow-2xs"
            >
              <UploadCloud :size="14" class="text-rose-600" />
              <span>Import Shapefile / GeoJSON</span>
            </button>
            <button
              @click="openProjectModal()"
              class="flex items-center gap-2 bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs px-4 py-2 rounded-xl transition-all shadow-sm cursor-pointer"
            >
              <Plus :size="14" />
              Tambah Proyek Baru
            </button>
          </div>
        </div>

        <!-- Loading skeleton -->
        <div v-if="adminStore.loadingProjects" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <div v-for="i in 3" :key="i" class="bg-white rounded-2xl border border-[#e4e7eb] p-5 animate-pulse space-y-3">
            <div class="h-4 bg-slate-200 rounded w-3/4"></div>
            <div class="h-3 bg-slate-100 rounded w-full"></div>
            <div class="h-3 bg-slate-100 rounded w-1/2"></div>
          </div>
        </div>

        <!-- Projects grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <div
            v-for="project in adminStore.projects"
            :key="project.id"
            class="bg-white rounded-2xl border border-[#e4e7eb] p-5 hover:border-[#cfd4dc] hover:shadow-md transition-all space-y-4"
          >
            <!-- Project header -->
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <div class="font-black text-sm text-[#1f242e] leading-tight">{{ project.name }}</div>
                <div class="text-[11px] text-[#707a8a] mt-0.5 line-clamp-2">{{ project.description || 'Tidak ada deskripsi' }}</div>
              </div>
              <div class="flex gap-1.5 shrink-0">
                <button
                  @click="openProjectModal(project)"
                  class="w-7 h-7 rounded-lg border border-[#e4e7eb] flex items-center justify-center text-[#707a8a] hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all cursor-pointer"
                  title="Edit proyek"
                >
                  <Pencil :size="12" />
                </button>
                <button
                  @click="confirmDeleteProject(project)"
                  class="w-7 h-7 rounded-lg border border-[#e4e7eb] flex items-center justify-center text-[#707a8a] hover:border-red-300 hover:text-red-600 hover:bg-red-50 transition-all cursor-pointer"
                  title="Hapus proyek"
                >
                  <Trash2 :size="12" />
                </button>
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-2 text-center">
              <div class="bg-[#f0f2f5] rounded-xl p-2">
                <div class="font-black text-base text-[#1f242e] font-mono">{{ project.total_tasks.toLocaleString() }}</div>
                <div class="text-[10px] text-[#707a8a] font-bold uppercase">Total Grid</div>
              </div>
              <div class="bg-emerald-50 border border-emerald-100 rounded-xl p-2">
                <div class="font-black text-base text-emerald-700 font-mono">{{ project.approved_tasks }}</div>
                <div class="text-[10px] text-emerald-600 font-bold uppercase">Approved</div>
              </div>
              <div class="bg-blue-50 border border-blue-100 rounded-xl p-2">
                <div class="font-black text-base text-blue-700 font-mono">{{ project.in_progress_tasks }}</div>
                <div class="text-[10px] text-blue-600 font-bold uppercase">On Progress</div>
              </div>
            </div>

            <!-- Progress bar -->
            <div>
              <div class="flex justify-between text-[10px] font-bold text-[#707a8a] mb-1">
                <span>Progress</span>
                <span class="font-mono text-emerald-600">
                  {{ project.total_tasks > 0 ? Math.round((project.approved_tasks / project.total_tasks) * 100) : 0 }}%
                </span>
              </div>
              <div class="w-full h-1.5 bg-[#e4e7eb] rounded-full overflow-hidden">
                <div
                  class="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  :style="{ width: project.total_tasks > 0 ? (project.approved_tasks / project.total_tasks * 100) + '%' : '0%' }"
                ></div>
              </div>
            </div>

            <!-- Center coordinates -->
            <div class="text-[11px] text-[#707a8a] font-mono border-t border-[#e4e7eb] pt-3">
              📍 {{ project.center_lat.toFixed(4) }}°, {{ project.center_lon.toFixed(4) }}°
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="!adminStore.loadingProjects && adminStore.projects.length === 0"
            class="col-span-3 bg-white rounded-2xl border border-dashed border-[#cfd4dc] p-12 text-center text-[#707a8a]">
            <FolderKanban :size="40" class="mx-auto mb-3 opacity-30 text-slate-400" />
            <p class="font-bold text-sm">Belum ada proyek tasking</p>
            <p class="text-xs mt-1">Klik "Tambah Proyek Baru" untuk membuat proyek pertama</p>
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════ -->
      <!-- TAB 2: IMPORT GRID KUSTOM               -->
      <!-- ═══════════════════════════════════════ -->
      <div v-if="activeTab === 'import'" class="space-y-6">
        
        <!-- Header -->
        <div class="bg-white rounded-3xl border border-[#e4e7eb] p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <div class="p-2 bg-rose-50 text-rose-600 rounded-xl">
                <UploadCloud :size="20" />
              </div>
              <h2 class="text-lg font-black text-[#1f242e]">Import Grid Kustom (Shapefile / GeoJSON)</h2>
            </div>
            <p class="text-xs text-[#707a8a] max-w-2xl leading-relaxed">
              Unggah file Shapefile (*.zip yang berisi .shp, .shx, .dbf, .prj) atau GeoJSON (*.geojson, *.json) Anda sendiri. Sistem akan otomatis melakukan reproyeksi WGS84, menghitung batas koordinat, dan mendistribusikannya ke antrean tasking.
            </p>
          </div>
        </div>

        <!-- Main Import Form Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          <!-- Drag & Drop Zone (7 cols) -->
          <div class="lg:col-span-7 bg-white rounded-3xl border border-[#e4e7eb] p-6 shadow-xs space-y-4">
            <h3 class="text-sm font-black text-[#1f242e] flex items-center gap-2">
              <FileArchive :size="16" class="text-rose-600" />
              <span>Pilih atau Tarik File Grid Anda</span>
            </h3>

            <!-- Drop Zone Container -->
            <div
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="onFileDrop"
              @click="$refs.fileInput.click()"
              class="border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-3 min-h-[240px]"
              :class="isDragging
                ? 'border-rose-500 bg-rose-50/70 scale-[0.99]'
                : importFile
                  ? 'border-emerald-400 bg-emerald-50/30'
                  : 'border-slate-300 hover:border-rose-400 bg-slate-50/60 hover:bg-slate-50'"
            >
              <input
                ref="fileInput"
                type="file"
                accept=".zip,.geojson,.json,.shp"
                @change="onFileSelect"
                class="hidden"
              />

              <div
                class="w-14 h-14 rounded-2xl flex items-center justify-center transition-all shadow-sm"
                :class="importFile ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-600'"
              >
                <CheckCircle2 v-if="importFile" :size="28" />
                <UploadCloud v-else :size="28" />
              </div>

              <div v-if="!importFile" class="space-y-1">
                <p class="font-extrabold text-sm text-slate-800">
                  Tarik & Jatuhkan file Shapefile (.zip) atau GeoJSON di sini
                </p>
                <p class="text-xs text-slate-500">
                  atau <span class="text-rose-600 font-bold underline">klik untuk memilih dari komputer Anda</span>
                </p>
                <div class="pt-2 flex items-center justify-center gap-2 text-[11px] text-slate-400 font-mono">
                  <span class="bg-white px-2 py-0.5 rounded border border-slate-200">.ZIP (Shapefile)</span>
                  <span class="bg-white px-2 py-0.5 rounded border border-slate-200">.GEOJSON</span>
                  <span class="bg-white px-2 py-0.5 rounded border border-slate-200">.JSON</span>
                </div>
              </div>

              <div v-else class="space-y-1 text-center">
                <div class="font-black text-sm text-emerald-950 font-mono flex items-center justify-center gap-2">
                  <span>{{ importFile.name }}</span>
                </div>
                <div class="text-xs text-slate-500">
                  Ukuran: {{ formatFileSize(importFile.size) }} • Siap diproses
                </div>
                <button
                  type="button"
                  @click.stop="importFile = null; importResult = null"
                  class="mt-2 text-xs text-rose-600 hover:underline font-bold cursor-pointer"
                >
                  Ganti File Lain
                </button>
              </div>
            </div>

            <!-- Notes & Instructions -->
            <div class="bg-amber-50/80 border border-amber-200/80 rounded-2xl p-3.5 text-xs text-amber-900 space-y-1">
              <div class="font-bold flex items-center gap-1.5 text-amber-800">
                <Info :size="14" />
                <span>Format Shapefile yang Didukung:</span>
              </div>
              <ul class="ml-5 list-disc space-y-0.5 text-[11px] text-amber-800">
                <li>Untuk <b>Shapefile</b>, pastikan dikompres dalam format <b>.zip</b> dan memuat minimal 4 file pendukung: <code>.shp</code>, <code>.shx</code>, <code>.dbf</code>, dan <code>.prj</code>.</li>
                <li>Jika koordinat dalam UTM / Proyeksi lain, sistem akan <b>otomatis mereproyeksikan</b> ke WGS84 (EPSG:4326).</li>
              </ul>
            </div>
          </div>

          <!-- Configuration & Target Project (5 cols) -->
          <div class="lg:col-span-5 bg-white rounded-3xl border border-[#e4e7eb] p-6 shadow-xs space-y-5">
            <h3 class="text-sm font-black text-[#1f242e] flex items-center gap-2">
              <FolderPlus :size="16" class="text-rose-600" />
              <span>Pengaturan Target Grid</span>
            </h3>

            <!-- Option 1: Destination Project Type -->
            <div class="space-y-2">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Tujuan Wilayah / Proyek:
              </label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  @click="importTargetType = 'new'"
                  class="p-2.5 rounded-xl border text-xs font-bold transition-all text-left cursor-pointer flex flex-col gap-0.5"
                  :class="importTargetType === 'new'
                    ? 'border-rose-500 bg-rose-50/70 text-rose-900 shadow-2xs'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
                >
                  <span>✨ Buat Proyek Baru</span>
                  <span class="text-[10px] font-normal text-slate-500">Otomatis dari nama file</span>
                </button>
                <button
                  type="button"
                  @click="importTargetType = 'existing'"
                  class="p-2.5 rounded-xl border text-xs font-bold transition-all text-left cursor-pointer flex flex-col gap-0.5"
                  :class="importTargetType === 'existing'
                    ? 'border-rose-500 bg-rose-50/70 text-rose-900 shadow-2xs'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
                >
                  <span>📁 Proyek Yang Ada</span>
                  <span class="text-[10px] font-normal text-slate-500">Gabungkan ke proyek</span>
                </button>
              </div>
            </div>

            <!-- New Project Inputs -->
            <div v-if="importTargetType === 'new'" class="space-y-3 p-3.5 bg-slate-50 rounded-2xl border border-slate-200">
              <div class="space-y-1">
                <label class="block text-[11px] font-bold text-slate-700">Nama Proyek Baru *</label>
                <input
                  v-model="importNewProjectName"
                  placeholder="Contoh: Grid Kustom Riau 2025"
                  class="w-full bg-white border border-slate-300 rounded-xl p-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500 font-sans"
                />
              </div>
              <div class="space-y-1">
                <label class="block text-[11px] font-bold text-slate-700">Deskripsi (Opsional)</label>
                <input
                  v-model="importNewProjectDesc"
                  placeholder="Deskripsi wilayah atau sumber shapefile..."
                  class="w-full bg-white border border-slate-300 rounded-xl p-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500 font-sans"
                />
              </div>
            </div>

            <!-- Existing Project Select -->
            <div v-else class="space-y-1 p-3.5 bg-slate-50 rounded-2xl border border-slate-200">
              <label class="block text-[11px] font-bold text-slate-700">Pilih Proyek / Wilayah Studi Tujuan *</label>
              <select
                v-model="importSelectedProjectId"
                class="w-full bg-white border border-slate-300 rounded-xl p-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500 font-sans"
              >
                <option :value="null" disabled>-- Pilih salah satu proyek --</option>
                <option v-for="proj in adminStore.projects" :key="proj.id" :value="proj.id">
                  {{ proj.name }} ({{ proj.total_tasks }} tasks)
                </option>
              </select>
            </div>

            <!-- Year Checkboxes -->
            <div class="space-y-2">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Tahun Komposit Sentinel-2:
              </label>
              <div class="flex items-center gap-3">
                <label v-for="yr in [2017, 2021, 2025]" :key="yr" class="flex items-center gap-1.5 text-xs font-bold text-slate-800 cursor-pointer">
                  <input
                    type="checkbox"
                    :value="yr"
                    v-model="importYears"
                    class="w-4 h-4 text-rose-600 rounded border-slate-300 focus:ring-rose-500 cursor-pointer"
                  />
                  <span>{{ yr }}</span>
                </label>
              </div>
              <p class="text-[10px] text-slate-400">Setiap poligon grid akan dibuatkan 1 tugas terpisah untuk setiap tahun yang dicentang.</p>
            </div>

            <!-- Custom Column ID (Optional) -->
            <div class="space-y-1">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Nama Kolom Kode Grid (Opsional):
              </label>
              <input
                v-model="importColumnName"
                placeholder="Otomatis (misal: grid_code, id, name, fid)"
                class="w-full bg-slate-50 border border-slate-300 rounded-xl p-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500 focus:bg-white font-mono"
              />
              <p class="text-[10px] text-slate-400">Kosongkan untuk mendeteksi kolom atribut secara otomatis.</p>
            </div>

            <!-- Process Button -->
            <div class="pt-2">
              <button
                @click="executeImport"
                :disabled="!importFile || importLoading || importYears.length === 0"
                class="w-full bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-extrabold text-sm py-3 rounded-2xl transition-all shadow-md shadow-rose-600/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <RotateCw v-if="importLoading" :size="16" class="animate-spin" />
                <UploadCloud v-else :size="16" />
                <span>{{ importLoading ? 'Memproses & Mengimpor Grid...' : 'Proses & Import Grid Sekarang' }}</span>
              </button>
            </div>

            <!-- Success Card -->
            <div v-if="importResult" class="p-4 bg-emerald-50 border border-emerald-300 rounded-2xl space-y-3 animate-in fade-in">
              <div class="flex items-center gap-2 text-emerald-900 font-extrabold text-xs">
                <CheckCircle2 :size="18" class="text-emerald-600 shrink-0" />
                <span>{{ importResult.message }}</span>
              </div>
              <div class="text-[11px] text-emerald-800 space-y-1 font-mono">
                <div>• Proyek: <b>{{ importResult.study_area_name }}</b></div>
                <div>• Jumlah Grid Asli: <b>{{ importResult.feature_count }} fitur</b></div>
                <div>• Total Tugas Dibuat: <b>{{ importResult.created_tasks_count }} tugas</b></div>
              </div>
              <router-link
                to="/tasking"
                class="inline-flex items-center gap-1.5 text-xs bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-3 py-1.5 rounded-xl transition-all shadow-xs cursor-pointer"
              >
                <ExternalLink :size="12" />
                <span>Buka di Tasking Manager</span>
              </router-link>
            </div>

          </div>

        </div>

      </div>

      <!-- ═══════════════════════════════════════ -->
      <!-- TAB 3: MANAJEMEN PENGGUNA (2026 MODERN) -->
      <!-- ═══════════════════════════════════════ -->
      <div v-if="activeTab === 'users'" class="space-y-6">

        <!-- 1. KPI Stats Summary Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Total Users -->
          <div class="bg-white rounded-3xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-all relative overflow-hidden group">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Akun</span>
              <div class="w-10 h-10 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-700 group-hover:scale-105 transition-transform">
                <Users :size="20" />
              </div>
            </div>
            <div class="mt-3">
              <div class="text-3xl font-black text-slate-900 font-heading tracking-tight">{{ totalUsersCount }}</div>
              <p class="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                <span class="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Semua pengguna terdaftar</span>
              </p>
            </div>
          </div>

          <!-- Admins -->
          <div class="bg-white rounded-3xl p-5 border border-purple-200/80 shadow-xs hover:shadow-md transition-all relative overflow-hidden group bg-gradient-to-br from-white to-purple-50/30">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-purple-700 uppercase tracking-wider">Administrator</span>
              <div class="w-10 h-10 rounded-2xl bg-purple-100 flex items-center justify-center text-purple-700 group-hover:scale-105 transition-transform">
                <ShieldCheck :size="20" />
              </div>
            </div>
            <div class="mt-3">
              <div class="text-3xl font-black text-purple-900 font-heading tracking-tight">{{ adminUsersCount }}</div>
              <p class="text-xs text-purple-600 mt-1">
                <span>Hak penuh & kelola pengguna</span>
              </p>
            </div>
          </div>

          <!-- Dosen / QC Reviewers -->
          <div class="bg-white rounded-3xl p-5 border border-indigo-200/80 shadow-xs hover:shadow-md transition-all relative overflow-hidden group bg-gradient-to-br from-white to-indigo-50/30">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-indigo-700 uppercase tracking-wider">Dosen / Reviewer</span>
              <div class="w-10 h-10 rounded-2xl bg-indigo-100 flex items-center justify-center text-indigo-700 group-hover:scale-105 transition-transform">
                <GraduationCap :size="20" />
              </div>
            </div>
            <div class="mt-3">
              <div class="text-3xl font-black text-indigo-900 font-heading tracking-tight">{{ dosenUsersCount }}</div>
              <p class="text-xs text-indigo-600 mt-1">
                <span>Hak validasi & evaluasi QC</span>
              </p>
            </div>
          </div>

          <!-- Active Annotators -->
          <div class="bg-white rounded-3xl p-5 border border-emerald-200/80 shadow-xs hover:shadow-md transition-all relative overflow-hidden group bg-gradient-to-br from-white to-emerald-50/30">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-700 uppercase tracking-wider">Mapper Aktif</span>
              <div class="w-10 h-10 rounded-2xl bg-emerald-100 flex items-center justify-center text-emerald-700 group-hover:scale-105 transition-transform">
                <PenTool :size="18" />
              </div>
            </div>
            <div class="mt-3">
              <div class="text-3xl font-black text-emerald-700 font-heading tracking-tight">{{ activeAnnotatorsCount }}</div>
              <p class="text-xs text-emerald-600 mt-1">
                <span>Kontributor aktif digitasi</span>
              </p>
            </div>
          </div>

          <!-- Inactive / Suspended Users -->
          <div class="bg-white rounded-3xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-all relative overflow-hidden group">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Nonaktif</span>
              <div class="w-10 h-10 rounded-2xl bg-rose-50 flex items-center justify-center text-rose-600 group-hover:scale-105 transition-transform">
                <UserX :size="20" />
              </div>
            </div>
            <div class="mt-3">
              <div class="text-3xl font-black text-slate-800 font-heading tracking-tight">{{ inactiveUsersCount }}</div>
              <p class="text-xs text-slate-500 mt-1">
                <span>Akses login ditangguhkan</span>
              </p>
            </div>
          </div>
        </div>

        <!-- 2. Smart Toolbar & Filter Control -->
        <div class="bg-white rounded-3xl border border-slate-200/90 p-4 lg:p-5 shadow-xs flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          <!-- Search & Filter Chips -->
          <div class="flex flex-wrap items-center gap-3 flex-1">
            <!-- Search Box -->
            <div class="relative w-full sm:w-72">
              <input
                v-model="userSearch"
                placeholder="Cari nama, username, email..."
                class="w-full pl-9 pr-8 py-2.5 text-xs border border-slate-200 rounded-2xl bg-slate-50/60 focus:bg-white focus:outline-none focus:border-rose-500 transition-all font-sans text-slate-800"
              />
              <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <button
                v-if="userSearch"
                @click="userSearch = ''"
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X :size="14" />
              </button>
            </div>

            <!-- Role Filter Chips -->
            <div class="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200/80 text-xs">
              <button
                @click="userRoleFilter = 'all'"
                class="px-3 py-1.5 rounded-xl font-bold transition-all cursor-pointer"
                :class="userRoleFilter === 'all' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-500 hover:text-slate-800'"
              >
                Semua Peran
              </button>
              <button
                @click="userRoleFilter = 'admin'"
                class="px-3 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1 cursor-pointer"
                :class="userRoleFilter === 'admin' ? 'bg-purple-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
              >
                <ShieldCheck :size="12" />
                <span>Admin</span>
              </button>
              <button
                @click="userRoleFilter = 'dosen'"
                class="px-3 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1 cursor-pointer"
                :class="userRoleFilter === 'dosen' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
              >
                <GraduationCap :size="13" />
                <span>Dosen</span>
              </button>
              <button
                @click="userRoleFilter = 'annotator'"
                class="px-3 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1 cursor-pointer"
                :class="userRoleFilter === 'annotator' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
              >
                <PenTool :size="11" />
                <span>Mapper</span>
              </button>
            </div>

            <!-- Status Filter Chips -->
            <div class="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200/80 text-xs">
              <button
                @click="userStatusFilter = 'all'"
                class="px-3 py-1.5 rounded-xl font-bold transition-all cursor-pointer"
                :class="userStatusFilter === 'all' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-500 hover:text-slate-800'"
              >
                Semua Status
              </button>
              <button
                @click="userStatusFilter = 'active'"
                class="px-3 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1 cursor-pointer"
                :class="userStatusFilter === 'active' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-white"></span>
                <span>Aktif</span>
              </button>
              <button
                @click="userStatusFilter = 'inactive'"
                class="px-3 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1 cursor-pointer"
                :class="userStatusFilter === 'inactive' ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-white"></span>
                <span>Nonaktif</span>
              </button>
            </div>
          </div>

          <!-- Actions & View Toggles -->
          <div class="flex items-center gap-2 self-end lg:self-center">
            <!-- View Mode Switcher -->
            <div class="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200/80 text-slate-500">
              <button
                @click="userViewMode = 'table'"
                class="p-2 rounded-xl transition-all cursor-pointer"
                :class="userViewMode === 'table' ? 'bg-white text-slate-900 shadow-2xs' : 'hover:text-slate-800'"
                title="Tampilan Tabel Detail"
              >
                <List :size="15" />
              </button>
              <button
                @click="userViewMode = 'grid'"
                class="p-2 rounded-xl transition-all cursor-pointer"
                :class="userViewMode === 'grid' ? 'bg-white text-slate-900 shadow-2xs' : 'hover:text-slate-800'"
                title="Tampilan Kartu Profil"
              >
                <LayoutGrid :size="15" />
              </button>
            </div>

            <!-- Refresh Button -->
            <button
              @click="refreshUsers"
              :disabled="adminStore.loadingUsers"
              class="p-2.5 rounded-2xl border border-slate-200 hover:bg-slate-50 text-slate-600 hover:text-slate-900 transition-all cursor-pointer"
              title="Perbarui Data Pengguna"
            >
              <RefreshCw :size="15" :class="adminStore.loadingUsers ? 'animate-spin text-rose-600' : ''" />
            </button>

            <!-- Add User Button -->
            <button
              @click="openUserModal()"
              class="flex items-center gap-2 bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-extrabold text-xs px-4 py-2.5 rounded-2xl transition-all shadow-md shadow-rose-600/20 whitespace-nowrap cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
            >
              <UserPlus :size="15" />
              <span>Tambah Pengguna</span>
            </button>
          </div>
        </div>

        <!-- 3A. Modern Table View -->
        <div v-if="userViewMode === 'table'" class="bg-white rounded-3xl border border-slate-200/90 overflow-hidden shadow-xs">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-slate-200 bg-slate-50/70 text-[11px] font-black text-slate-500 uppercase tracking-wider">
                  <th class="py-3.5 px-4 w-12 text-center">#</th>
                  <th class="py-3.5 px-4">Pengguna & Profil</th>
                  <th class="py-3.5 px-4">Email</th>
                  <th class="py-3.5 px-4">Peran (Role)</th>
                  <th class="py-3.5 px-4">Beban & Kontribusi</th>
                  <th class="py-3.5 px-4 text-center">Status</th>
                  <th class="py-3.5 px-4 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 text-xs">
                <!-- Loading state -->
                <tr v-if="adminStore.loadingUsers" v-for="i in 5" :key="i" class="animate-pulse">
                  <td class="p-4 text-center"><div class="h-3 w-4 bg-slate-200 rounded mx-auto"></div></td>
                  <td class="p-4">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 bg-slate-200 rounded-2xl"></div>
                      <div class="space-y-1.5 flex-1">
                        <div class="h-3.5 bg-slate-200 rounded w-32"></div>
                        <div class="h-2.5 bg-slate-100 rounded w-20"></div>
                      </div>
                    </div>
                  </td>
                  <td class="p-4"><div class="h-3 bg-slate-200 rounded w-28"></div></td>
                  <td class="p-4"><div class="h-6 bg-slate-200 rounded-full w-20"></div></td>
                  <td class="p-4"><div class="h-6 bg-slate-200 rounded-full w-24"></div></td>
                  <td class="p-4"><div class="h-6 bg-slate-200 rounded-full w-14 mx-auto"></div></td>
                  <td class="p-4 text-right"><div class="h-7 w-20 bg-slate-200 rounded-xl ml-auto"></div></td>
                </tr>

                <!-- Rows -->
                <tr
                  v-else-if="filteredUsers.length > 0"
                  v-for="(user, idx) in filteredUsers"
                  :key="user.id"
                  class="hover:bg-slate-50/80 transition-colors group"
                >
                  <!-- Index -->
                  <td class="py-3.5 px-4 text-center font-mono text-slate-400 font-bold text-[11px]">
                    {{ idx + 1 }}
                  </td>

                  <!-- User Profile Info -->
                  <td class="py-3.5 px-4">
                    <div class="flex items-center gap-3">
                      <!-- Avatar with status pulse -->
                      <div class="relative shrink-0">
                        <div
                          class="w-10 h-10 rounded-2xl flex items-center justify-center font-black text-sm text-white shadow-xs"
                          :class="getAvatarColor(user)"
                        >
                          {{ (user.full_name?.charAt(0) || user.username?.charAt(0) || 'U').toUpperCase() }}
                        </div>
                        <span
                          class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white"
                          :class="user.is_active ? 'bg-emerald-500' : 'bg-slate-400'"
                          :title="user.is_active ? 'Akun Aktif' : 'Akun Nonaktif'"
                        ></span>
                      </div>

                      <div class="min-w-0">
                        <div class="font-bold text-slate-900 text-sm truncate flex items-center gap-1.5">
                          <span>{{ user.full_name }}</span>
                          <span v-if="user.id === authStore.user?.id" class="text-[9px] bg-rose-100 text-rose-700 px-1.5 py-0.2 rounded-md font-bold uppercase">
                            Anda
                          </span>
                        </div>
                        <div class="text-[11px] text-slate-500 font-mono flex items-center gap-2 mt-0.5">
                          <span>@{{ user.username }}</span>
                          <span v-if="user.created_at" class="text-slate-300">•</span>
                          <span v-if="user.created_at" class="text-slate-400 text-[10px]">{{ formatDate(user.created_at) }}</span>
                        </div>
                        <div v-if="user.institution || user.department || user.phone || user.nim_nip" class="flex flex-wrap items-center gap-1.5 mt-1.5">
                          <span v-if="user.institution" class="inline-flex items-center gap-1 text-[10px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md">
                            <Building2 :size="10" class="text-slate-400" />
                            <span>{{ user.institution }}</span>
                            <span v-if="user.department" class="text-slate-400">• {{ user.department }}</span>
                          </span>
                          <span v-if="user.nim_nip" class="text-[10px] font-mono bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded-md font-bold">
                            ID: {{ user.nim_nip }}
                          </span>
                          <span v-if="user.phone" class="text-[10px] font-mono bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded-md font-medium inline-flex items-center gap-1">
                            <Phone :size="9" /> {{ user.phone }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </td>

                  <!-- Email with copy button -->
                  <td class="py-3.5 px-4">
                    <div class="flex items-center gap-1.5 group/email">
                      <span class="font-mono text-xs text-slate-600 select-all">{{ user.email }}</span>
                      <button
                        @click="copyToClipboard(user.email, `email_${user.id}`)"
                        class="opacity-0 group-hover/email:opacity-100 text-slate-400 hover:text-slate-700 transition-all p-1 rounded-md hover:bg-slate-200 cursor-pointer"
                        title="Salin email"
                      >
                        <CheckCheck v-if="copyFeedback[`email_${user.id}`]" :size="12" class="text-emerald-600" />
                        <Copy v-else :size="12" />
                      </button>
                    </div>
                  </td>

                  <!-- Role Badge -->
                  <td class="py-3.5 px-4">
                    <span
                      class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[10px] font-extrabold uppercase tracking-wider border shadow-2xs"
                      :class="user.role?.toLowerCase() === 'admin'
                        ? 'bg-purple-50 text-purple-800 border-purple-200'
                        : (user.role?.toLowerCase() === 'dosen'
                          ? 'bg-indigo-50 text-indigo-800 border-indigo-200'
                          : 'bg-emerald-50 text-emerald-800 border-emerald-200')"
                    >
                      <ShieldCheck v-if="user.role?.toLowerCase() === 'admin'" :size="12" class="text-purple-600" />
                      <GraduationCap v-else-if="user.role?.toLowerCase() === 'dosen'" :size="12" class="text-indigo-600" />
                      <PenTool v-else :size="11" class="text-emerald-600" />
                      <span>{{ user.role?.toLowerCase() === 'admin' ? 'Administrator' : (user.role?.toLowerCase() === 'dosen' ? 'Dosen (QC)' : 'Mapper') }}</span>
                    </span>
                  </td>

                  <!-- Contribution / Workload -->
                  <td class="py-3.5 px-4">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span
                        class="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-lg border"
                        :class="(user.assigned_tasks_count || 0) > 0 ? 'bg-blue-50 text-blue-800 border-blue-200' : 'bg-slate-50 text-slate-500 border-slate-200'"
                        title="Grid tugas yang sedang dipegang"
                      >
                        <Grid :size="11" />
                        <span>{{ user.assigned_tasks_count || 0 }} grid</span>
                      </span>
                      <span
                        class="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-lg border"
                        :class="(user.annotations_count || 0) > 0 ? 'bg-teal-50 text-teal-800 border-teal-200' : 'bg-slate-50 text-slate-500 border-slate-200'"
                        title="Total poligon data latih yang didigitasi"
                      >
                        <Shapes :size="11" />
                        <span>{{ user.annotations_count || 0 }} poligon</span>
                      </span>
                    </div>
                  </td>

                  <!-- Status Toggle Switch -->
                  <td class="py-3.5 px-4 text-center">
                    <button
                      @click="toggleActive(user)"
                      class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider transition-all border shadow-2xs cursor-pointer"
                      :class="user.is_active
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-300 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-300'
                        : 'bg-slate-100 text-slate-500 border-slate-300 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300'"
                      :title="user.is_active ? 'Klik untuk nonaktifkan akun' : 'Klik untuk aktifkan akun'"
                    >
                      <span class="w-1.5 h-1.5 rounded-full" :class="user.is_active ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                      <span>{{ user.is_active ? 'Aktif' : 'Nonaktif' }}</span>
                    </button>
                  </td>

                  <!-- Actions -->
                  <td class="py-3.5 px-4 text-right">
                    <div class="flex items-center justify-end gap-1">
                      <!-- Edit -->
                      <button
                        @click="openUserModal(user)"
                        class="p-1.5 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-blue-50 border border-transparent hover:border-blue-200 transition-all cursor-pointer"
                        title="Edit Data Profil"
                      >
                        <Pencil :size="14" />
                      </button>

                      <!-- Reset Password -->
                      <button
                        @click="openResetPasswordModal(user)"
                        class="p-1.5 rounded-xl text-slate-500 hover:text-amber-600 hover:bg-amber-50 border border-transparent hover:border-amber-200 transition-all cursor-pointer"
                        title="Reset Kata Sandi"
                      >
                        <Key :size="14" />
                      </button>

                      <!-- Delete -->
                      <button
                        v-if="user.id !== authStore.user?.id"
                        @click="confirmDeleteUser(user)"
                        class="p-1.5 rounded-xl text-slate-500 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-all cursor-pointer"
                        title="Hapus / Nonaktifkan Pengguna"
                      >
                        <Trash2 :size="14" />
                      </button>
                    </div>
                  </td>
                </tr>

                <!-- Empty State -->
                <tr v-else>
                  <td colspan="7" class="py-16 text-center text-slate-400">
                    <UserX :size="40" class="mx-auto mb-3 opacity-30 text-slate-400" />
                    <p class="font-extrabold text-sm text-slate-700">Tidak ada pengguna yang sesuai</p>
                    <p class="text-xs text-slate-500 mt-1">Coba sesuaikan kata kunci pencarian atau filter peran/status Anda.</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 3B. Modern Card Grid View -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Loading skeleton cards -->
          <template v-if="adminStore.loadingUsers">
            <div v-for="i in 6" :key="i" class="bg-white rounded-3xl p-5 border border-slate-200 animate-pulse space-y-4">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-2xl bg-slate-200"></div>
                <div class="space-y-2 flex-1">
                  <div class="h-3.5 bg-slate-200 rounded w-3/4"></div>
                  <div class="h-2.5 bg-slate-100 rounded w-1/2"></div>
                </div>
              </div>
              <div class="h-10 bg-slate-100 rounded-2xl"></div>
              <div class="h-8 bg-slate-100 rounded-2xl"></div>
            </div>
          </template>

          <!-- User Card -->
          <template v-else-if="filteredUsers.length > 0">
            <div
              v-for="user in filteredUsers"
              :key="user.id"
              class="bg-white rounded-3xl p-5 border border-slate-200/90 hover:border-slate-300 hover:shadow-md transition-all space-y-4 flex flex-col justify-between group"
            >
              <!-- Top Profile Info -->
              <div class="space-y-3">
                <div class="flex items-start justify-between gap-2">
                  <div class="flex items-center gap-3 min-w-0">
                    <div
                      class="w-12 h-12 rounded-2xl flex items-center justify-center font-black text-base text-white shadow-xs shrink-0"
                      :class="getAvatarColor(user)"
                    >
                      {{ (user.full_name?.charAt(0) || user.username?.charAt(0) || 'U').toUpperCase() }}
                    </div>
                    <div class="min-w-0">
                      <div class="font-bold text-slate-900 text-sm truncate flex items-center gap-1.5">
                        <span class="truncate">{{ user.full_name }}</span>
                        <span v-if="user.id === authStore.user?.id" class="text-[9px] bg-rose-100 text-rose-700 px-1 py-0.2 rounded font-bold">Anda</span>
                      </div>
                      <div class="text-xs text-slate-500 font-mono truncate">@{{ user.username }}</div>
                    </div>
                  </div>

                  <!-- Role Pill -->
                  <span
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[10px] font-extrabold uppercase tracking-wider border shrink-0"
                    :class="user.role?.toLowerCase() === 'admin'
                      ? 'bg-purple-50 text-purple-800 border-purple-200'
                      : (user.role?.toLowerCase() === 'dosen'
                        ? 'bg-indigo-50 text-indigo-800 border-indigo-200'
                        : 'bg-emerald-50 text-emerald-800 border-emerald-200')"
                  >
                    <ShieldCheck v-if="user.role?.toLowerCase() === 'admin'" :size="11" class="text-purple-600" />
                    <GraduationCap v-else-if="user.role?.toLowerCase() === 'dosen'" :size="11" class="text-indigo-600" />
                    <PenTool v-else :size="10" class="text-emerald-600" />
                    <span>{{ user.role?.toLowerCase() === 'admin' ? 'Admin' : (user.role?.toLowerCase() === 'dosen' ? 'Dosen' : 'Mapper') }}</span>
                  </span>
                </div>

                <!-- Email banner -->
                <div class="bg-slate-50 p-2.5 rounded-2xl border border-slate-200/70 flex items-center justify-between text-xs">
                  <span class="text-slate-600 font-mono text-[11px] truncate select-all">{{ user.email }}</span>
                  <button
                    @click="copyToClipboard(user.email, `email_card_${user.id}`)"
                    class="text-slate-400 hover:text-slate-700 p-1 rounded-md transition-colors cursor-pointer"
                    title="Salin email"
                  >
                    <CheckCheck v-if="copyFeedback[`email_card_${user.id}`]" :size="12" class="text-emerald-600" />
                    <Copy v-else :size="12" />
                  </button>
                </div>

                <!-- Administrative & Academic Info Strip (Optional) -->
                <div v-if="user.institution || user.department || user.phone || user.nim_nip" class="bg-slate-50/80 p-2.5 rounded-2xl border border-slate-200/60 space-y-1 text-[11px] text-slate-600">
                  <div v-if="user.institution" class="flex items-center gap-1.5 font-medium text-slate-800 truncate">
                    <Building2 :size="12" class="text-slate-400 shrink-0" />
                    <span class="truncate">{{ user.institution }}</span>
                  </div>
                  <div v-if="user.department" class="flex items-center gap-1.5 text-[10px] text-slate-500 truncate pl-4">
                    <span>{{ user.department }}</span>
                    <span v-if="user.nim_nip" class="font-mono text-blue-600">({{ user.nim_nip }})</span>
                  </div>
                  <div v-if="user.phone" class="flex items-center gap-1.5 text-[10px] font-mono text-emerald-700 pt-0.5">
                    <Phone :size="10" class="text-emerald-600" />
                    <span>{{ user.phone }}</span>
                  </div>
                </div>

                <!-- Workload Metrics Strip -->
                <div class="grid grid-cols-2 gap-2 text-center">
                  <div class="bg-blue-50/60 border border-blue-100 p-2 rounded-2xl">
                    <div class="font-mono font-black text-sm text-blue-800">{{ user.assigned_tasks_count || 0 }}</div>
                    <div class="text-[10px] font-bold text-blue-600 uppercase">Grid Tugas</div>
                  </div>
                  <div class="bg-teal-50/60 border border-teal-100 p-2 rounded-2xl">
                    <div class="font-mono font-black text-sm text-teal-800">{{ user.annotations_count || 0 }}</div>
                    <div class="text-[10px] font-bold text-teal-600 uppercase">Poligon Anotasi</div>
                  </div>
                </div>
              </div>

              <!-- Bottom Actions Bar -->
              <div class="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <!-- Status Switch -->
                <button
                  @click="toggleActive(user)"
                  class="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all border cursor-pointer"
                  :class="user.is_active
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                    : 'bg-slate-100 text-slate-500 border-slate-300'"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="user.is_active ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                  <span>{{ user.is_active ? 'Aktif' : 'Nonaktif' }}</span>
                </button>

                <!-- Action Button Group -->
                <div class="flex items-center gap-1">
                  <button
                    @click="openUserModal(user)"
                    class="p-2 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-blue-50 border border-slate-200 transition-all cursor-pointer"
                    title="Edit Profil"
                  >
                    <Pencil :size="13" />
                  </button>
                  <button
                    @click="openResetPasswordModal(user)"
                    class="p-2 rounded-xl text-slate-500 hover:text-amber-600 hover:bg-amber-50 border border-slate-200 transition-all cursor-pointer"
                    title="Reset Password"
                  >
                    <Key :size="13" />
                  </button>
                  <button
                    v-if="user.id !== authStore.user?.id"
                    @click="confirmDeleteUser(user)"
                    class="p-2 rounded-xl text-slate-500 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 transition-all cursor-pointer"
                    title="Hapus / Nonaktifkan"
                  >
                    <Trash2 :size="13" />
                  </button>
                </div>
              </div>
            </div>
          </template>

          <!-- Empty Grid View -->
          <div v-else class="col-span-full py-16 bg-white rounded-3xl border border-dashed border-slate-300 text-center text-slate-400">
            <UserX :size="40" class="mx-auto mb-3 opacity-30 text-slate-400" />
            <p class="font-extrabold text-sm text-slate-700">Tidak ada pengguna yang cocok</p>
            <p class="text-xs text-slate-500 mt-1">Coba sesuaikan kata kunci pencarian atau filter.</p>
          </div>
        </div>

      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- MODAL: Tambah / Edit PROYEK                             -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showProjectModal"
        class="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="closeProjectModal"
      >
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-lg border border-[#e4e7eb] overflow-hidden">
          <!-- Modal header -->
          <div class="px-6 py-5 border-b border-[#e4e7eb] flex items-center justify-between bg-[#f8f9fa]">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-xl bg-[#d73f3f] flex items-center justify-center text-white">
                <FolderPlus :size="16" />
              </div>
              <h3 class="font-black text-[#1f242e] text-sm">
                {{ editingProject ? 'Edit Proyek' : 'Tambah Proyek Baru' }}
              </h3>
            </div>
            <button @click="closeProjectModal" class="text-[#707a8a] hover:text-[#1f242e] transition-colors cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <!-- Form -->
          <div class="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Nama Proyek *</label>
              <input v-model="projectForm.name" type="text" placeholder="cth: Mapping Sumatera Barat 2026"
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors" />
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Deskripsi</label>
              <textarea v-model="projectForm.description" rows="2" placeholder="Deskripsi singkat proyek pemetaan..."
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors resize-none"></textarea>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Latitude Pusat *</label>
                <input v-model.number="projectForm.center_lat" type="number" step="0.001" placeholder="-0.750"
                  class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Longitude Pusat *</label>
                <input v-model.number="projectForm.center_lon" type="number" step="0.001" placeholder="100.500"
                  class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors" />
              </div>
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Default Zoom Level</label>
              <input v-model.number="projectForm.default_zoom" type="number" min="4" max="16" placeholder="8"
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors" />
            </div>

            <!-- Auto-generate grid (only for new project) -->
            <div v-if="!editingProject" class="rounded-2xl border border-[#e4e7eb] p-4 space-y-3 bg-[#f8f9fa]">
              <div class="flex items-center justify-between">
                <label class="text-xs font-bold text-[#1f242e] flex items-center gap-1.5">
                  <Grid :size="14" class="text-[#d73f3f]" />
                  Auto-Generate Grid (1024px)
                </label>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="projectForm.generateGrid" class="sr-only peer" />
                  <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#d73f3f]"></div>
                </label>
              </div>

              <div v-if="projectForm.generateGrid" class="space-y-3">
                <p class="text-[11px] text-[#707a8a]">Masukkan bounding box wilayah untuk auto-generate grid tiles 1024×1024px (~10.24km/tile)</p>
                <div class="grid grid-cols-2 gap-2">
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Min Longitude</label>
                    <input v-model.number="projectForm.min_lon" type="number" step="0.01" placeholder="98.60"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-none focus:border-[#d73f3f]" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Max Longitude</label>
                    <input v-model.number="projectForm.max_lon" type="number" step="0.01" placeholder="101.80"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-none focus:border-[#d73f3f]" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Min Latitude</label>
                    <input v-model.number="projectForm.min_lat" type="number" step="0.01" placeholder="-3.10"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-none focus:border-[#d73f3f]" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Max Latitude</label>
                    <input v-model.number="projectForm.max_lat" type="number" step="0.01" placeholder="0.40"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-none focus:border-[#d73f3f]" />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Prefix Kode Grid</label>
                    <input v-model="projectForm.grid_prefix" type="text" maxlength="3" placeholder="SB"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-none focus:border-[#d73f3f] uppercase" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Patch Size (px)</label>
                    <select v-model.number="projectForm.patch_size_px"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-none focus:border-[#d73f3f]">
                      <option :value="256">256px (~2.56km)</option>
                      <option :value="512">512px (~5.12km)</option>
                      <option :value="1024">1024px (~10.24km)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- Error -->
            <div v-if="modalError" class="text-xs text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-xl flex items-center gap-2">
              <AlertTriangle :size="14" />
              {{ modalError }}
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-[#e4e7eb] flex items-center justify-end gap-3 bg-[#f8f9fa]">
            <button @click="closeProjectModal" class="px-4 py-2 text-sm font-bold text-[#707a8a] hover:text-[#1f242e] transition-colors cursor-pointer">
              Batal
            </button>
            <button
              @click="saveProject"
              :disabled="savingProject"
              class="flex items-center gap-2 bg-[#d73f3f] hover:bg-[#c23434] disabled:opacity-50 text-white font-bold text-sm px-5 py-2 rounded-xl transition-all shadow-sm cursor-pointer"
            >
              <RotateCw v-if="savingProject" :size="14" class="animate-spin" />
              <Check v-else :size="14" />
              {{ savingProject ? 'Menyimpan...' : (editingProject ? 'Simpan Perubahan' : 'Buat Proyek') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- MODAL: Tambah / Edit PENGGUNA (2026 UI)                 -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showUserModal"
        class="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
        @click.self="closeUserModal"
      >
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-lg border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
          <!-- Modal header -->
          <div class="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-rose-500 to-red-600 flex items-center justify-center text-white shadow-xs">
                <UserCheck v-if="editingUser" :size="20" />
                <UserPlus v-else :size="20" />
              </div>
              <div>
                <h3 class="font-black text-slate-900 text-base">
                  {{ editingUser ? 'Edit Profil Pengguna' : 'Tambah Pengguna Baru' }}
                </h3>
                <p class="text-xs text-slate-500 font-medium">
                  {{ editingUser ? 'Perbarui informasi profil dan hak akses' : 'Daftarkan akun baru ke platform STEVI Task Manager' }}
                </p>
              </div>
            </div>
            <button @click="closeUserModal" class="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <!-- Form Body -->
          <div class="p-6 space-y-4 overflow-y-auto flex-1">
            <!-- Full Name -->
            <div class="space-y-1">
              <label class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
                <span>Nama Lengkap <span class="text-rose-600">*</span></span>
              </label>
              <input
                v-model="userForm.full_name"
                type="text"
                placeholder="Contoh: Ahmad Fauzi, S.T."
                class="w-full px-3.5 py-2.5 text-sm text-slate-900 border border-slate-200 rounded-2xl focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/10 transition-all font-sans bg-white"
              />
            </div>

            <!-- Username & Email Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  <span>Username <span class="text-rose-600">*</span></span>
                </label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-mono text-xs">@</span>
                  <input
                    v-model="userForm.username"
                    type="text"
                    placeholder="ahmad_fauzi"
                    :disabled="!!editingUser"
                    class="w-full pl-7 pr-3 py-2.5 text-sm text-slate-900 border border-slate-200 rounded-2xl focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/10 transition-all font-mono disabled:bg-slate-100 disabled:text-slate-500"
                  />
                </div>
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  <span>Email <span class="text-rose-600">*</span></span>
                </label>
                <input
                  v-model="userForm.email"
                  type="email"
                  placeholder="ahmad@geoai.ac.id"
                  class="w-full px-3.5 py-2.5 text-sm text-slate-900 border border-slate-200 rounded-2xl focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/10 transition-all font-sans bg-white"
                />
              </div>
            </div>

            <!-- Role Selection Cards (3 Roles) -->
            <div class="space-y-2">
              <label class="text-xs font-bold text-slate-700 uppercase tracking-wider">
                <span>Peran & Hak Akses (Role) <span class="text-rose-600">*</span></span>
              </label>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <!-- Card 1: Annotator -->
                <div
                  @click="userForm.role = 'annotator'"
                  class="p-3.5 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between space-y-2"
                  :class="userForm.role === 'annotator'
                    ? 'border-emerald-500 bg-emerald-50/40 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 bg-white'"
                >
                  <div class="flex items-center justify-between">
                    <div class="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                      <PenTool :size="16" />
                    </div>
                    <div
                      class="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                      :class="userForm.role === 'annotator' ? 'border-emerald-600 bg-emerald-600' : 'border-slate-300'"
                    >
                      <div v-if="userForm.role === 'annotator'" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                    </div>
                  </div>
                  <div>
                    <div class="font-extrabold text-xs text-slate-900">Mapper / Anotator</div>
                    <p class="text-[10px] text-slate-500 mt-0.5 leading-snug">
                      Mendigitasi tutupan lahan pada grid & submit untuk review.
                    </p>
                  </div>
                </div>

                <!-- Card 2: Dosen / Reviewer -->
                <div
                  @click="userForm.role = 'dosen'"
                  class="p-3.5 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between space-y-2"
                  :class="userForm.role === 'dosen'
                    ? 'border-indigo-500 bg-indigo-50/40 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 bg-white'"
                >
                  <div class="flex items-center justify-between">
                    <div class="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
                      <GraduationCap :size="16" />
                    </div>
                    <div
                      class="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                      :class="userForm.role === 'dosen' ? 'border-indigo-600 bg-indigo-600' : 'border-slate-300'"
                    >
                      <div v-if="userForm.role === 'dosen'" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                    </div>
                  </div>
                  <div>
                    <div class="font-extrabold text-xs text-slate-900">Dosen / Reviewer</div>
                    <p class="text-[10px] text-slate-500 mt-0.5 leading-snug">
                      Akses QC Review & evaluasi mutu tanpa akses kelola pengguna.
                    </p>
                  </div>
                </div>

                <!-- Card 3: Administrator -->
                <div
                  @click="userForm.role = 'admin'"
                  class="p-3.5 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between space-y-2"
                  :class="userForm.role === 'admin'
                    ? 'border-purple-500 bg-purple-50/40 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 bg-white'"
                >
                  <div class="flex items-center justify-between">
                    <div class="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                      <ShieldCheck :size="16" />
                    </div>
                    <div
                      class="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                      :class="userForm.role === 'admin' ? 'border-purple-600 bg-purple-600' : 'border-slate-300'"
                    >
                      <div v-if="userForm.role === 'admin'" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                    </div>
                  </div>
                  <div>
                    <div class="font-extrabold text-xs text-slate-900">Administrator</div>
                    <p class="text-[10px] text-slate-500 mt-0.5 leading-snug">
                      Akses penuh: kelola akun pengguna, proyek, dan sistem.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Password section -->
            <div class="space-y-2 p-4 bg-slate-50 rounded-2xl border border-slate-200/80">
              <div class="flex items-center justify-between">
                <label class="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  {{ editingUser ? 'Reset Password (Opsional)' : 'Kata Sandi Akun' }}
                  <span v-if="!editingUser" class="text-rose-600">*</span>
                </label>
                <!-- 1-Click Generator button -->
                <button
                  type="button"
                  @click="generateRandomPasswordForForm"
                  class="text-[11px] text-rose-600 hover:text-rose-700 font-bold flex items-center gap-1 cursor-pointer hover:underline"
                >
                  <Sparkles :size="12" />
                  <span>Generate Acak</span>
                </button>
              </div>

              <div class="relative">
                <input
                  v-model="userForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  :placeholder="editingUser ? 'Kosongkan jika tidak ingin mengubah password' : 'Minimal 6 karakter'"
                  class="w-full px-3.5 py-2.5 pr-20 text-sm text-slate-900 border border-slate-200 rounded-2xl focus:outline-none focus:border-rose-500 focus:bg-white transition-all font-mono bg-white"
                />
                <div class="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  <button
                    v-if="userForm.password"
                    type="button"
                    @click="copyToClipboard(userForm.password, 'form_password')"
                    class="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer"
                    title="Salin password"
                  >
                    <CheckCheck v-if="copyFeedback['form_password']" :size="14" class="text-emerald-600" />
                    <Copy v-else :size="14" />
                  </button>
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer"
                    :title="showPassword ? 'Sembunyikan' : 'Lihat'"
                  >
                    <EyeOff v-if="showPassword" :size="14" />
                    <Eye v-else :size="14" />
                  </button>
                </div>
              </div>
              <p v-if="copyFeedback['form_password']" class="text-[11px] text-emerald-600 font-bold flex items-center gap-1">
                <Check :size="12" /> Password berhasil disalin ke clipboard!
              </p>
            </div>

            <!-- Data Administrasi & Kontak (Opsional) -->
            <div class="space-y-3 p-4 bg-slate-50/80 rounded-2xl border border-slate-200/80">
              <div class="flex items-center justify-between border-b border-slate-200/70 pb-2">
                <div class="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <FileText :size="14" class="text-rose-600" />
                  <span>Data Administrasi & Kontak</span>
                </div>
                <span class="text-[10px] font-bold text-slate-400 uppercase bg-slate-200/60 px-2 py-0.5 rounded-full">Opsional</span>
              </div>

              <!-- Baris: No Telp/WA & NIM/NIP -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <Phone :size="12" class="text-slate-400" />
                    <span>No. WhatsApp / Telepon</span>
                  </label>
                  <input
                    v-model="userForm.phone"
                    type="text"
                    placeholder="Contoh: 081234567890"
                    class="w-full px-3 py-2 text-xs text-slate-900 border border-slate-200 rounded-xl focus:outline-none focus:border-rose-500 bg-white font-sans"
                  />
                </div>
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <FileText :size="12" class="text-slate-400" />
                    <span>NIM / NIP / ID Identitas</span>
                  </label>
                  <input
                    v-model="userForm.nim_nip"
                    type="text"
                    placeholder="Contoh: 211001234"
                    class="w-full px-3 py-2 text-xs text-slate-900 border border-slate-200 rounded-xl focus:outline-none focus:border-rose-500 bg-white font-mono"
                  />
                </div>
              </div>

              <!-- Baris: Universitas & Prodi -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <Building2 :size="12" class="text-slate-400" />
                    <span>Universitas / Lembaga</span>
                  </label>
                  <input
                    v-model="userForm.institution"
                    type="text"
                    placeholder="Contoh: Universitas Andalas / KLHK"
                    class="w-full px-3 py-2 text-xs text-slate-900 border border-slate-200 rounded-xl focus:outline-none focus:border-rose-500 bg-white font-sans"
                  />
                </div>
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <GraduationCap :size="12" class="text-slate-400" />
                    <span>Program Studi / Jurusan</span>
                  </label>
                  <input
                    v-model="userForm.department"
                    type="text"
                    placeholder="Contoh: S1 Geografi"
                    class="w-full px-3 py-2 text-xs text-slate-900 border border-slate-200 rounded-xl focus:outline-none focus:border-rose-500 bg-white font-sans"
                  />
                </div>
              </div>

              <!-- Baris: Alamat -->
              <div class="space-y-1">
                <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                  <MapPin :size="12" class="text-slate-400" />
                  <span>Alamat Lengkap / Domisili</span>
                </label>
                <textarea
                  v-model="userForm.address"
                  rows="2"
                  placeholder="Contoh: Jl. Sudirman No. 12, Padang, Sumatera Barat"
                  class="w-full px-3 py-2 text-xs text-slate-900 border border-slate-200 rounded-xl focus:outline-none focus:border-rose-500 bg-white resize-none font-sans"
                ></textarea>
              </div>
            </div>

            <!-- Active Status Toggle (only on edit) -->
            <div v-if="editingUser" class="flex items-center justify-between p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80">
              <div>
                <div class="font-bold text-xs text-slate-900">Status Akun Aktif</div>
                <div class="text-[11px] text-slate-500">Nonaktifkan untuk menolak login tanpa menghapus riwayat</div>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="userForm.is_active" class="sr-only peer" />
                <div class="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>

            <!-- Error Banner -->
            <div v-if="modalError" class="text-xs text-rose-700 bg-rose-50 border border-rose-200 p-3 rounded-2xl flex items-center gap-2">
              <AlertTriangle :size="16" class="shrink-0 text-rose-600" />
              <span>{{ modalError }}</span>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50">
            <button
              @click="closeUserModal"
              class="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-200/60 rounded-xl transition-colors cursor-pointer"
            >
              Batal
            </button>
            <button
              @click="saveUser"
              :disabled="savingUser"
              class="flex items-center gap-2 bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 disabled:opacity-50 text-white font-extrabold text-xs px-5 py-2.5 rounded-2xl transition-all shadow-md shadow-rose-600/20 cursor-pointer"
            >
              <RotateCw v-if="savingUser" :size="14" class="animate-spin" />
              <Check v-else :size="14" />
              <span>{{ savingUser ? 'Menyimpan...' : (editingUser ? 'Simpan Perubahan' : 'Buat Akun Sekarang') }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- MODAL: Dedicated Reset Password (1-Click Generator)     -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="resetPasswordModal.show"
        class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
        @click.self="closeResetPasswordModal"
      >
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md border border-slate-200 overflow-hidden space-y-4">
          <!-- Header -->
          <div class="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center shadow-xs">
                <Key :size="18" />
              </div>
              <div>
                <h3 class="font-black text-slate-900 text-base">Reset Kata Sandi</h3>
                <p class="text-xs text-slate-500 font-medium">Buat kata sandi baru untuk pengguna</p>
              </div>
            </div>
            <button @click="closeResetPasswordModal" class="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 space-y-4 pt-2">
            <!-- User summary badge -->
            <div class="p-3 bg-slate-50 rounded-2xl border border-slate-200 flex items-center gap-3">
              <div
                class="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white shadow-xs text-sm"
                :class="getAvatarColor(resetPasswordModal.user)"
              >
                {{ (resetPasswordModal.user?.full_name?.charAt(0) || 'U').toUpperCase() }}
              </div>
              <div class="min-w-0">
                <div class="font-bold text-slate-900 text-xs truncate">{{ resetPasswordModal.user?.full_name }}</div>
                <div class="text-[11px] text-slate-500 font-mono">@{{ resetPasswordModal.user?.username }}</div>
              </div>
            </div>

            <!-- Generator Button -->
            <button
              type="button"
              @click="generateRandomPasswordForResetModal"
              class="w-full py-2.5 px-3 rounded-2xl border border-dashed border-amber-300 bg-amber-50/60 hover:bg-amber-100/70 text-amber-900 text-xs font-extrabold flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <Sparkles :size="14" class="text-amber-600" />
              <span>Generate Kata Sandi Acak Otomatis</span>
            </button>

            <!-- Password Input Display -->
            <div class="space-y-1">
              <label class="text-[11px] font-bold text-slate-700 uppercase tracking-wider">Kata Sandi Baru:</label>
              <div class="relative">
                <input
                  v-model="resetPasswordModal.newPassword"
                  type="text"
                  placeholder="Ketik password atau klik generate di atas"
                  class="w-full px-3.5 py-2.5 pr-12 text-sm text-slate-900 border border-slate-200 rounded-2xl focus:outline-none focus:border-amber-500 font-mono bg-white"
                />
                <button
                  type="button"
                  @click="copyToClipboard(resetPasswordModal.newPassword, 'reset_modal')"
                  :disabled="!resetPasswordModal.newPassword"
                  class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-30 cursor-pointer"
                  title="Salin kata sandi"
                >
                  <CheckCheck v-if="copyFeedback['reset_modal']" :size="16" class="text-emerald-600" />
                  <Copy v-else :size="16" />
                </button>
              </div>
              <p v-if="copyFeedback['reset_modal']" class="text-[11px] text-emerald-600 font-bold flex items-center gap-1 mt-1">
                <Check :size="12" /> Berhasil disalin ke clipboard!
              </p>
            </div>

            <!-- Error -->
            <div v-if="resetPasswordModal.error" class="text-xs text-rose-700 bg-rose-50 border border-rose-200 p-3 rounded-xl flex items-center gap-2">
              <AlertTriangle :size="14" class="shrink-0 text-rose-600" />
              <span>{{ resetPasswordModal.error }}</span>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50">
            <button
              @click="closeResetPasswordModal"
              class="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-200/60 rounded-xl transition-colors cursor-pointer"
            >
              Batal
            </button>
            <button
              @click="executeResetPassword"
              :disabled="resetPasswordModal.loading || !resetPasswordModal.newPassword"
              class="flex items-center gap-2 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 disabled:opacity-50 text-white font-extrabold text-xs px-5 py-2.5 rounded-2xl transition-all shadow-md shadow-amber-600/20 cursor-pointer"
            >
              <RotateCw v-if="resetPasswordModal.loading" :size="14" class="animate-spin" />
              <Key v-else :size="14" />
              <span>{{ resetPasswordModal.loading ? 'Menyimpan...' : 'Simpan Password Baru' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- MODAL: Smart Konfirmasi Hapus / Nonaktifkan             -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showDeleteConfirm"
        class="fixed inset-0 z-[1001] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
        @click.self="showDeleteConfirm = false"
      >
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md border border-slate-200 p-6 space-y-5 text-center">
          <div
            class="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto"
            :class="pendingDelete.hasAnnotations ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-600'"
          >
            <ShieldAlert v-if="pendingDelete.hasAnnotations" :size="28" />
            <AlertTriangle v-else :size="28" />
          </div>
          <div>
            <h3 class="font-black text-slate-900 text-base">
              {{ pendingDelete.hasAnnotations ? 'Konfirmasi Penonaktifan Akun' : 'Konfirmasi Hapus Pengguna' }}
            </h3>
            <p class="text-xs text-slate-600 mt-2 leading-relaxed whitespace-pre-line">{{ deleteConfirmMessage }}</p>
          </div>

          <div class="flex gap-3 justify-center pt-2">
            <button
              @click="showDeleteConfirm = false"
              class="px-5 py-2.5 text-xs font-bold border border-slate-200 rounded-2xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-all cursor-pointer"
            >
              Batal
            </button>
            <button
              @click="executeDelete"
              :disabled="deleting"
              class="px-5 py-2.5 text-xs font-extrabold disabled:opacity-50 text-white rounded-2xl transition-all shadow-md flex items-center gap-2 cursor-pointer"
              :class="pendingDelete.hasAnnotations
                ? 'bg-amber-600 hover:bg-amber-700 shadow-amber-600/20'
                : 'bg-rose-600 hover:bg-rose-700 shadow-rose-600/20'"
            >
              <RotateCw v-if="deleting" :size="14" class="animate-spin" />
              <Trash2 v-else :size="14" />
              <span>{{ deleting ? 'Memproses...' : (pendingDelete.hasAnnotations ? 'Ya, Nonaktifkan Akun' : 'Ya, Hapus Akun') }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast notification -->
    <Teleport to="body">
      <div v-if="toast.show"
        class="fixed bottom-6 right-6 z-[1001] flex items-center gap-3 px-4 py-3 rounded-2xl shadow-xl text-white text-sm font-bold transition-all"
        :class="toast.type === 'success' ? 'bg-emerald-600' : 'bg-red-600'"
      >
        <CheckCircle2 v-if="toast.type === 'success'" :size="18" />
        <XCircle v-else :size="18" />
        {{ toast.message }}
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Shield,
  ShieldCheck,
  FolderKanban,
  FolderPlus,
  Map,
  Users,
  UserPlus,
  UserCheck,
  UserX,
  Search,
  Pencil,
  Trash2,
  Plus,
  X,
  Check,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Eye,
  EyeOff,
  RotateCw,
  Grid,
  UploadCloud,
  FileArchive,
  ExternalLink,
  Info,
  PenTool,
  Key,
  Lock,
  Copy,
  CheckCheck,
  RefreshCw,
  LayoutGrid,
  List,
  Sparkles,
  ShieldAlert,
  Shapes,
  GraduationCap,
  Phone,
  Building2,
  MapPin,
  FileText
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useAdminStore } from '../stores/admin'
import api from '../services/api'

const authStore = useAuthStore()
const adminStore = useAdminStore()

// ── Tab ──────────────────────────────────────────────────────────────────
const activeTab = ref('projects')

// ── User Management State (2026 Modern) ──────────────────────────────────
const userSearch = ref('')
const userRoleFilter = ref('all') // 'all' | 'admin' | 'dosen' | 'annotator'
const userStatusFilter = ref('all') // 'all' | 'active' | 'inactive'
const userViewMode = ref('table') // 'table' | 'grid'
const copyFeedback = ref({})

// KPI Computed
const totalUsersCount = computed(() => adminStore.users.length)
const adminUsersCount = computed(() => adminStore.users.filter(u => (u.role || '').toLowerCase() === 'admin').length)
const dosenUsersCount = computed(() => adminStore.users.filter(u => (u.role || '').toLowerCase() === 'dosen').length)
const activeAnnotatorsCount = computed(() => adminStore.users.filter(u => (u.role || '').toLowerCase() === 'annotator' && u.is_active).length)
const inactiveUsersCount = computed(() => adminStore.users.filter(u => !u.is_active).length)

const filteredUsers = computed(() => {
  let list = adminStore.users
  if (userRoleFilter.value !== 'all') {
    list = list.filter(u => (u.role || '').toLowerCase() === userRoleFilter.value)
  }
  if (userStatusFilter.value === 'active') {
    list = list.filter(u => u.is_active)
  } else if (userStatusFilter.value === 'inactive') {
    list = list.filter(u => !u.is_active)
  }
  if (userSearch.value.trim()) {
    const q = userSearch.value.toLowerCase().trim()
    list = list.filter(u =>
      u.full_name?.toLowerCase().includes(q) ||
      u.username?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q) ||
      u.institution?.toLowerCase().includes(q) ||
      u.department?.toLowerCase().includes(q) ||
      u.nim_nip?.toLowerCase().includes(q) ||
      u.phone?.toLowerCase().includes(q) ||
      u.address?.toLowerCase().includes(q)
    )
  }
  return list
})

// Avatar color helper
const avatarGradients = [
  'bg-gradient-to-br from-indigo-500 to-purple-600',
  'bg-gradient-to-br from-rose-500 to-pink-600',
  'bg-gradient-to-br from-teal-500 to-emerald-600',
  'bg-gradient-to-br from-amber-500 to-orange-600',
  'bg-gradient-to-br from-blue-500 to-cyan-600',
  'bg-gradient-to-br from-violet-500 to-fuchsia-600'
]

function getAvatarColor(user) {
  if (!user) return avatarGradients[0]
  const role = (user.role || '').toLowerCase()
  if (role === 'admin') {
    return 'bg-gradient-to-br from-purple-600 to-indigo-700'
  }
  if (role === 'dosen') {
    return 'bg-gradient-to-br from-indigo-500 to-blue-600'
  }
  const str = user.username || user.full_name || 'U'
  let hash = 0
  for (let i = 0; i < str.length; i++) hash += str.charCodeAt(i)
  return avatarGradients[hash % avatarGradients.length]
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return dateStr
  }
}

async function copyToClipboard(text, key) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copyFeedback.value[key] = true
    setTimeout(() => {
      copyFeedback.value[key] = false
    }, 2200)
  } catch (e) {
    console.error('Clipboard copy error:', e)
  }
}

function generateSecurePassword() {
  const chars = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*'
  let pass = 'GeoAI-'
  for (let i = 0; i < 8; i++) {
    pass += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return pass
}

async function refreshUsers() {
  try {
    await adminStore.fetchUsers()
    showToast('Data pengguna berhasil diperbarui')
  } catch (e) {
    showToast('Gagal memuat ulang pengguna', 'error')
  }
}

// ── Toast ─────────────────────────────────────────────────────────────────
const toast = ref({ show: false, message: '', type: 'success' })
function showToast(message, type = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3500)
}

// ── Project Modal ─────────────────────────────────────────────────────────
const showProjectModal = ref(false)
const editingProject = ref(null)
const savingProject = ref(false)
const modalError = ref('')
const projectForm = ref({
  name: '', description: '', center_lat: null, center_lon: null, default_zoom: 8,
  generateGrid: false,
  min_lon: null, min_lat: null, max_lon: null, max_lat: null,
  grid_prefix: 'P', patch_size_px: 1024
})

function openProjectModal(project = null) {
  editingProject.value = project
  modalError.value = ''
  if (project) {
    projectForm.value = {
      name: project.name,
      description: project.description || '',
      center_lat: project.center_lat,
      center_lon: project.center_lon,
      default_zoom: project.default_zoom,
      generateGrid: false,
      min_lon: null, min_lat: null, max_lon: null, max_lat: null,
      grid_prefix: 'P', patch_size_px: 1024
    }
  } else {
    projectForm.value = {
      name: '', description: '', center_lat: null, center_lon: null, default_zoom: 8,
      generateGrid: false,
      min_lon: null, min_lat: null, max_lon: null, max_lat: null,
      grid_prefix: 'P', patch_size_px: 1024
    }
  }
  showProjectModal.value = true
}

function closeProjectModal() {
  showProjectModal.value = false
  editingProject.value = null
  modalError.value = ''
}

async function saveProject() {
  if (!projectForm.value.name.trim()) { modalError.value = 'Nama proyek wajib diisi'; return }
  if (!projectForm.value.center_lat || !projectForm.value.center_lon) { modalError.value = 'Koordinat pusat wajib diisi'; return }

  savingProject.value = true
  modalError.value = ''
  try {
    if (editingProject.value) {
      await adminStore.updateProject(editingProject.value.id, {
        name: projectForm.value.name,
        description: projectForm.value.description,
        center_lat: projectForm.value.center_lat,
        center_lon: projectForm.value.center_lon,
        default_zoom: projectForm.value.default_zoom
      })
      showToast('Proyek berhasil diperbarui')
    } else {
      const payload = {
        name: projectForm.value.name,
        description: projectForm.value.description,
        center_lat: projectForm.value.center_lat,
        center_lon: projectForm.value.center_lon,
        default_zoom: projectForm.value.default_zoom,
        patch_size_px: projectForm.value.patch_size_px,
        grid_prefix: projectForm.value.grid_prefix
      }
      if (projectForm.value.generateGrid) {
        payload.min_lon = projectForm.value.min_lon
        payload.min_lat = projectForm.value.min_lat
        payload.max_lon = projectForm.value.max_lon
        payload.max_lat = projectForm.value.max_lat
      }
      await adminStore.createProject(payload)
      showToast('Proyek baru berhasil dibuat')
    }
    closeProjectModal()
  } catch (e) {
    modalError.value = e.response?.data?.detail || 'Gagal menyimpan proyek'
  } finally {
    savingProject.value = false
  }
}

// ── User Modal (2026 Modern) ──────────────────────────────────────────────
const showUserModal = ref(false)
const editingUser = ref(null)
const savingUser = ref(false)
const showPassword = ref(false)
const userForm = ref({
  full_name: '',
  username: '',
  email: '',
  role: 'annotator',
  password: '',
  is_active: true,
  phone: '',
  institution: '',
  department: '',
  nim_nip: '',
  address: ''
})

function generateRandomPasswordForForm() {
  const pass = generateSecurePassword()
  userForm.value.password = pass
  copyToClipboard(pass, 'form_password')
}

function openUserModal(user = null) {
  editingUser.value = user
  modalError.value = ''
  showPassword.value = false
  if (user) {
    userForm.value = {
      full_name: user.full_name,
      username: user.username,
      email: user.email,
      role: (user.role || 'annotator').toLowerCase(),
      password: '',
      is_active: user.is_active,
      phone: user.phone || '',
      institution: user.institution || '',
      department: user.department || '',
      nim_nip: user.nim_nip || '',
      address: user.address || ''
    }
  } else {
    userForm.value = {
      full_name: '',
      username: '',
      email: '',
      role: 'annotator',
      password: generateSecurePassword(),
      is_active: true,
      phone: '',
      institution: '',
      department: '',
      nim_nip: '',
      address: ''
    }
  }
  showUserModal.value = true
}

function closeUserModal() {
  showUserModal.value = false
  editingUser.value = null
  modalError.value = ''
}

async function saveUser() {
  if (!userForm.value.full_name.trim()) { modalError.value = 'Nama lengkap wajib diisi'; return }
  if (!editingUser.value && !userForm.value.username.trim()) { modalError.value = 'Username wajib diisi'; return }
  if (!userForm.value.email.trim()) { modalError.value = 'Email wajib diisi'; return }
  if (!editingUser.value && !userForm.value.password) { modalError.value = 'Password wajib diisi untuk akun baru'; return }

  savingUser.value = true
  modalError.value = ''
  try {
    if (editingUser.value) {
      const payload = {
        full_name: userForm.value.full_name.trim(),
        email: userForm.value.email.trim(),
        role: userForm.value.role.toLowerCase(),
        is_active: userForm.value.is_active,
        phone: userForm.value.phone ? userForm.value.phone.trim() : null,
        institution: userForm.value.institution ? userForm.value.institution.trim() : null,
        department: userForm.value.department ? userForm.value.department.trim() : null,
        nim_nip: userForm.value.nim_nip ? userForm.value.nim_nip.trim() : null,
        address: userForm.value.address ? userForm.value.address.trim() : null
      }
      if (userForm.value.password.trim()) payload.password = userForm.value.password.trim()
      await adminStore.updateUser(editingUser.value.id, payload)
      showToast('Data pengguna berhasil diperbarui')
    } else {
      await adminStore.createUser({
        full_name: userForm.value.full_name.trim(),
        username: userForm.value.username.trim().toLowerCase(),
        email: userForm.value.email.trim(),
        role: userForm.value.role.toLowerCase(),
        password: userForm.value.password,
        phone: userForm.value.phone ? userForm.value.phone.trim() : null,
        institution: userForm.value.institution ? userForm.value.institution.trim() : null,
        department: userForm.value.department ? userForm.value.department.trim() : null,
        nim_nip: userForm.value.nim_nip ? userForm.value.nim_nip.trim() : null,
        address: userForm.value.address ? userForm.value.address.trim() : null
      })
      showToast('Akun pengguna baru berhasil dibuat')
    }
    closeUserModal()
    await adminStore.fetchUsers()
  } catch (e) {
    modalError.value = e.response?.data?.detail || 'Gagal menyimpan data pengguna'
  } finally {
    savingUser.value = false
  }
}

async function toggleActive(user) {
  try {
    await adminStore.toggleUserActive(user.id, !user.is_active)
    showToast(`Akun @${user.username} ${!user.is_active ? 'diaktifkan' : 'dinonaktifkan'}`)
  } catch (e) {
    showToast(e.response?.data?.detail || 'Gagal mengubah status akun', 'error')
  }
}

// ── Reset Password Modal ──────────────────────────────────────────────────
const resetPasswordModal = ref({
  show: false,
  user: null,
  newPassword: '',
  loading: false,
  error: ''
})

function openResetPasswordModal(user) {
  const autoPass = generateSecurePassword()
  resetPasswordModal.value = {
    show: true,
    user,
    newPassword: autoPass,
    loading: false,
    error: ''
  }
}

function closeResetPasswordModal() {
  resetPasswordModal.value.show = false
  resetPasswordModal.value.user = null
  resetPasswordModal.value.newPassword = ''
  resetPasswordModal.value.error = ''
}

function generateRandomPasswordForResetModal() {
  const pass = generateSecurePassword()
  resetPasswordModal.value.newPassword = pass
  copyToClipboard(pass, 'reset_modal')
}

async function executeResetPassword() {
  if (!resetPasswordModal.value.newPassword.trim()) {
    resetPasswordModal.value.error = 'Password tidak boleh kosong'
    return
  }

  resetPasswordModal.value.loading = true
  resetPasswordModal.value.error = ''
  try {
    const user = resetPasswordModal.value.user
    const pass = resetPasswordModal.value.newPassword.trim()
    await adminStore.resetPassword(user.id, pass)
    await copyToClipboard(pass, 'reset_modal')
    showToast(`Password untuk @${user.username} berhasil di-reset dan disalin!`)
    closeResetPasswordModal()
  } catch (e) {
    resetPasswordModal.value.error = e.response?.data?.detail || 'Gagal mereset password'
  } finally {
    resetPasswordModal.value.loading = false
  }
}

// ── Delete / Deactivate Confirm ───────────────────────────────────────────
const showDeleteConfirm = ref(false)
const deleteConfirmMessage = ref('')
const deleting = ref(false)
const pendingDelete = ref({ type: null, item: null, hasAnnotations: false })

function confirmDeleteProject(project) {
  pendingDelete.value = { type: 'project', item: project, hasAnnotations: false }
  deleteConfirmMessage.value = `Proyek "${project.name}" dan ${project.total_tasks} grid tile di dalamnya akan dihapus permanen. Tindakan ini tidak dapat dibatalkan.`
  showDeleteConfirm.value = true
}

function confirmDeleteUser(user) {
  const hasAnnotations = (user.annotations_count || 0) > 0
  const hasTasks = (user.assigned_tasks_count || 0) > 0
  pendingDelete.value = { type: 'user', item: user, hasAnnotations }

  if (hasAnnotations) {
    deleteConfirmMessage.value = `Pengguna "${user.full_name}" (@${user.username}) memiliki ${user.annotations_count} poligon anotasi data latih.\n\nDemi menjaga integritas dataset Deep Learning agar tidak hilang, akun akan DINONAKTIFKAN (bukan dihapus permanen).`
  } else if (hasTasks) {
    deleteConfirmMessage.value = `Pengguna "${user.full_name}" (@${user.username}) memiliki ${user.assigned_tasks_count} grid tugas yang sedang dipegang.\n\nGrid tugas akan otomatis dilepas kembali ke status UNASSIGNED, dan akun akan dihapus permanen dari sistem.`
  } else {
    deleteConfirmMessage.value = `Akun pengguna "${user.full_name}" (@${user.username}) akan dihapus permanen dari sistem.`
  }
  showDeleteConfirm.value = true
}

async function executeDelete() {
  deleting.value = true
  try {
    const { type, item, hasAnnotations } = pendingDelete.value
    if (type === 'project') {
      await adminStore.deleteProject(item.id)
      showToast(`Proyek "${item.name}" berhasil dihapus`)
    } else {
      const res = await adminStore.deleteUser(item.id)
      if (res?.action === 'deactivated' || hasAnnotations) {
        showToast(`Akun @${item.username} dinonaktifkan (data anotasi tetap aman)`)
      } else {
        showToast(`Akun @${item.username} berhasil dihapus permanen`)
      }
      await adminStore.fetchUsers()
    }
    showDeleteConfirm.value = false
  } catch (e) {
    showToast(e.response?.data?.detail || 'Gagal memproses penghapusan data', 'error')
    showDeleteConfirm.value = false
  } finally {
    deleting.value = false
    pendingDelete.value = { type: null, item: null, hasAnnotations: false }
  }
}

// ── Import Custom Grid (Shapefile / GeoJSON) ──────────────────────────────
const importFile = ref(null)
const isDragging = ref(false)
const importTargetType = ref('new') // 'new' | 'existing'
const importSelectedProjectId = ref(null)
const importNewProjectName = ref('')
const importNewProjectDesc = ref('')
const importYears = ref([2017, 2021, 2025])
const importColumnName = ref('')
const importLoading = ref(false)
const importResult = ref(null)

const onFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) handleChosenFile(file)
}

const onFileDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) handleChosenFile(file)
}

const handleChosenFile = (file) => {
  importFile.value = file
  importResult.value = null
  if (!importNewProjectName.value) {
    const base = file.name.replace(/\.[^/.]+$/, '').replace(/[_.-]+/g, ' ')
    importNewProjectName.value = `Grid ${base}`
  }
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const executeImport = async () => {
  if (!importFile.value) {
    showToast('Harap pilih file Shapefile (.zip) atau GeoJSON terlebih dahulu', 'error')
    return
  }

  if (importTargetType.value === 'new' && !importNewProjectName.value.trim()) {
    showToast('Harap isi nama proyek baru', 'error')
    return
  }

  if (importTargetType.value === 'existing' && !importSelectedProjectId.value) {
    showToast('Harap pilih salah satu proyek tujuan', 'error')
    return
  }

  if (importYears.value.length === 0) {
    showToast('Pilih minimal 1 tahun Sentinel-2', 'error')
    return
  }

  importLoading.value = true
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    if (importTargetType.value === 'existing' && importSelectedProjectId.value) {
      formData.append('study_area_id', importSelectedProjectId.value)
    } else {
      formData.append('new_project_name', importNewProjectName.value)
      if (importNewProjectDesc.value) {
        formData.append('new_project_desc', importNewProjectDesc.value)
      }
    }
    formData.append('years_str', importYears.value.join(','))
    if (importColumnName.value.trim()) {
      formData.append('grid_id_col', importColumnName.value.trim())
    }

    const res = await api.importGrid(formData)
    importResult.value = res.data
    showToast(res.data?.message || 'Grid kustom berhasil diimpor!', 'success')
    await adminStore.fetchProjects()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Gagal mengimpor file grid geospasial.', 'error')
  } finally {
    importLoading.value = false
  }
}

// ── On mount ──────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([
    adminStore.fetchProjects(),
    adminStore.fetchUsers()
  ])
  if (adminStore.projects.length > 0 && !importSelectedProjectId.value) {
    importSelectedProjectId.value = adminStore.projects[0].id
  }
})
</script>

<style scoped>
/* Force dark text on ALL form inputs in admin modals — prevents white-on-white issue */
input,
textarea,
select {
  color: #1f242e !important;
  background-color: #ffffff;
}

input::placeholder,
textarea::placeholder {
  color: #9ca3af;
}

input:disabled,
textarea:disabled,
select:disabled {
  color: #707a8a !important;
  background-color: #f8f9fa;
}
</style>

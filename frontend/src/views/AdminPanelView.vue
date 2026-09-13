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
      <!-- TAB 3: MANAJEMEN PENGGUNA              -->
      <!-- ═══════════════════════════════════════ -->
      <div v-if="activeTab === 'users'" class="space-y-4">

        <!-- Toolbar + search -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <h2 class="text-base font-black text-[#1f242e] flex items-center gap-2">
            <Users :size="18" class="text-[#d73f3f]" />
            Daftar Pengguna Terdaftar
          </h2>
          <div class="flex items-center gap-2">
            <div class="relative">
              <input
                v-model="userSearch"
                placeholder="Cari nama atau username..."
                class="pl-8 pr-3 py-2 text-xs border border-[#e4e7eb] rounded-xl bg-white focus:outline-none focus:border-[#d73f3f] w-56 transition-all"
              />
              <Search :size="13" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#707a8a]" />
            </div>
            <button
              @click="openUserModal()"
              class="flex items-center gap-2 bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs px-4 py-2 rounded-xl transition-all shadow-sm whitespace-nowrap cursor-pointer"
            >
              <UserPlus :size="14" />
              Tambah Pengguna
            </button>
          </div>
        </div>

        <!-- Users table -->
        <div class="bg-white rounded-2xl border border-[#e4e7eb] overflow-hidden shadow-xs">
          <!-- Table header -->
          <div class="grid grid-cols-[auto_1fr_140px_110px_100px_90px] gap-4 px-5 py-3 border-b border-[#e4e7eb] bg-[#f8f9fa] text-[10px] font-black text-[#707a8a] uppercase tracking-wider">
            <div>#</div>
            <div>Nama / Username</div>
            <div>Email</div>
            <div>Role</div>
            <div>Status</div>
            <div class="text-right">Aksi</div>
          </div>

          <!-- Loading skeleton -->
          <div v-if="adminStore.loadingUsers">
            <div v-for="i in 6" :key="i" class="grid grid-cols-[auto_1fr_140px_110px_100px_90px] gap-4 px-5 py-3.5 border-b border-[#f0f2f5] animate-pulse">
              <div class="h-3 w-5 bg-slate-200 rounded"></div>
              <div class="space-y-1.5">
                <div class="h-3 w-3/4 bg-slate-200 rounded"></div>
                <div class="h-2.5 w-1/2 bg-slate-100 rounded"></div>
              </div>
              <div class="h-3 w-full bg-slate-100 rounded"></div>
              <div class="h-5 w-16 bg-slate-200 rounded-full"></div>
              <div class="h-5 w-14 bg-slate-200 rounded-full"></div>
              <div class="flex gap-1 justify-end">
                <div class="h-6 w-6 bg-slate-200 rounded-lg"></div>
                <div class="h-6 w-6 bg-slate-200 rounded-lg"></div>
              </div>
            </div>
          </div>

          <!-- User rows -->
          <template v-else>
            <div
              v-for="(user, idx) in filteredUsers"
              :key="user.id"
              class="grid grid-cols-[auto_1fr_140px_110px_100px_90px] gap-4 px-5 py-3.5 border-b border-[#f0f2f5] last:border-0 hover:bg-[#f8f9fa] transition-colors items-center"
            >
              <!-- Index -->
              <div class="text-xs font-mono text-[#707a8a] w-5 text-center">{{ idx + 1 }}</div>

              <!-- Name + Username -->
              <div class="min-w-0">
                <div class="font-bold text-sm text-[#1f242e] truncate">{{ user.full_name }}</div>
                <div class="text-[11px] text-[#707a8a] font-mono">@{{ user.username }}</div>
              </div>

              <!-- Email -->
              <div class="text-[11px] text-[#555d6b] truncate">{{ user.email }}</div>

              <!-- Role badge -->
              <div>
                <span
                  class="text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wide flex items-center gap-1 w-fit"
                  :class="user.role === 'admin'
                    ? 'bg-purple-100 text-purple-800 border-purple-300'
                    : 'bg-blue-50 text-blue-700 border-blue-200'"
                >
                  <ShieldCheck :size="10" v-if="user.role === 'admin'" />
                  <Pencil :size="10" v-else />
                  {{ user.role === 'admin' ? 'Admin' : 'Annotator' }}
                </span>
              </div>

              <!-- Active toggle -->
              <div>
                <button
                  @click="toggleActive(user)"
                  class="text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wide transition-all cursor-pointer"
                  :class="user.is_active
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-red-50 hover:text-red-700 hover:border-red-200'
                    : 'bg-red-50 text-red-700 border-red-200 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200'"
                  :title="user.is_active ? 'Klik untuk nonaktifkan' : 'Klik untuk aktifkan'"
                >
                  {{ user.is_active ? 'Aktif' : 'Nonaktif' }}
                </button>
              </div>

              <!-- Action buttons -->
              <div class="flex items-center gap-1.5 justify-end">
                <button
                  @click="openUserModal(user)"
                  class="w-7 h-7 rounded-lg border border-[#e4e7eb] flex items-center justify-center text-[#707a8a] hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all cursor-pointer"
                  title="Edit pengguna"
                >
                  <Pencil :size="12" />
                </button>
                <button
                  @click="confirmDeleteUser(user)"
                  class="w-7 h-7 rounded-lg border border-[#e4e7eb] flex items-center justify-center text-[#707a8a] hover:border-red-300 hover:text-red-600 hover:bg-red-50 transition-all cursor-pointer"
                  title="Hapus pengguna"
                >
                  <Trash2 :size="12" />
                </button>
              </div>
            </div>

            <!-- Empty state -->
            <div v-if="filteredUsers.length === 0" class="py-12 text-center text-[#707a8a]">
              <UserX :size="32" class="mx-auto mb-2 opacity-30 text-slate-400" />
              <p class="text-sm font-bold">Tidak ada pengguna ditemukan</p>
            </div>
          </template>
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
    <!-- MODAL: Tambah / Edit PENGGUNA                          -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showUserModal"
        class="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="closeUserModal"
      >
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md border border-[#e4e7eb] overflow-hidden">
          <!-- Modal header -->
          <div class="px-6 py-5 border-b border-[#e4e7eb] flex items-center justify-between bg-[#f8f9fa]">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-xl bg-[#d73f3f] flex items-center justify-center text-white">
                <UserCheck :size="16" />
              </div>
              <h3 class="font-black text-[#1f242e] text-sm">
                {{ editingUser ? 'Edit Pengguna' : 'Tambah Pengguna Baru' }}
              </h3>
            </div>
            <button @click="closeUserModal" class="text-[#707a8a] hover:text-[#1f242e] transition-colors cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <!-- Form -->
          <div class="p-6 space-y-4">
            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Nama Lengkap *</label>
              <input v-model="userForm.full_name" type="text" placeholder="cth: Ahmad Fauzi"
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors" />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Username *</label>
                <input v-model="userForm.username" type="text" placeholder="username_mapper"
                  :disabled="!!editingUser"
                  class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Role *</label>
                <select v-model="userForm.role"
                  class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors">
                  <option value="ANNOTATOR">Kontributor / Mapper (Annotator)</option>
                  <option value="admin">Administrator / Reviewer (Admin)</option>
                </select>
              </div>
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Email *</label>
              <input v-model="userForm.email" type="email" placeholder="nama@email.com"
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors" />
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">
                {{ editingUser ? 'Reset Password (kosongkan jika tidak diubah)' : 'Password *' }}
              </label>
              <div class="relative">
                <input
                  v-model="userForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  :placeholder="editingUser ? '••••••••' : 'Min 6 karakter'"
                  class="w-full px-3.5 py-2.5 pr-10 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-none focus:border-[#d73f3f] transition-colors"
                />
                <button type="button" @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-[#707a8a] hover:text-[#1f242e] cursor-pointer">
                  <EyeOff v-if="showPassword" :size="14" />
                  <Eye v-else :size="14" />
                </button>
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
            <button @click="closeUserModal" class="px-4 py-2 text-sm font-bold text-[#707a8a] hover:text-[#1f242e] transition-colors cursor-pointer">
              Batal
            </button>
            <button
              @click="saveUser"
              :disabled="savingUser"
              class="flex items-center gap-2 bg-[#d73f3f] hover:bg-[#c23434] disabled:opacity-50 text-white font-bold text-sm px-5 py-2 rounded-xl transition-all shadow-sm cursor-pointer"
            >
              <RotateCw v-if="savingUser" :size="14" class="animate-spin" />
              <Check v-else :size="14" />
              {{ savingUser ? 'Menyimpan...' : (editingUser ? 'Simpan Perubahan' : 'Buat Akun') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- MODAL: Konfirmasi Hapus                                 -->
    <!-- ═══════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showDeleteConfirm"
        class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="showDeleteConfirm = false"
      >
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-sm border border-[#e4e7eb] p-6 space-y-5 text-center">
          <div class="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mx-auto text-red-600">
            <AlertTriangle :size="28" />
          </div>
          <div>
            <h3 class="font-black text-[#1f242e] text-base">Konfirmasi Hapus</h3>
            <p class="text-sm text-[#707a8a] mt-1">{{ deleteConfirmMessage }}</p>
          </div>
          <div class="flex gap-3 justify-center">
            <button @click="showDeleteConfirm = false"
              class="px-5 py-2 text-sm font-bold border border-[#e4e7eb] rounded-xl text-[#707a8a] hover:text-[#1f242e] hover:bg-[#f0f2f5] transition-all cursor-pointer">
              Batal
            </button>
            <button @click="executeDelete"
              :disabled="deleting"
              class="px-5 py-2 text-sm font-bold bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-xl transition-all shadow-sm flex items-center gap-2 cursor-pointer">
              <RotateCw v-if="deleting" :size="14" class="animate-spin" />
              <Trash2 v-else :size="14" />
              {{ deleting ? 'Menghapus...' : 'Ya, Hapus' }}
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
  Info
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useAdminStore } from '../stores/admin'
import api from '../services/api'

const authStore = useAuthStore()
const adminStore = useAdminStore()

// ── Tab ──────────────────────────────────────────────────────────────────
const activeTab = ref('projects')

// ── User search ──────────────────────────────────────────────────────────
const userSearch = ref('')
const filteredUsers = computed(() => {
  if (!userSearch.value.trim()) return adminStore.users
  const q = userSearch.value.toLowerCase()
  return adminStore.users.filter(u =>
    u.full_name?.toLowerCase().includes(q) ||
    u.username?.toLowerCase().includes(q) ||
    u.email?.toLowerCase().includes(q)
  )
})

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

// ── User Modal ────────────────────────────────────────────────────────────
const showUserModal = ref(false)
const editingUser = ref(null)
const savingUser = ref(false)
const showPassword = ref(false)
const userForm = ref({ full_name: '', username: '', email: '', role: 'ANNOTATOR', password: '' })

function openUserModal(user = null) {
  editingUser.value = user
  modalError.value = ''
  showPassword.value = false
  if (user) {
    userForm.value = { full_name: user.full_name, username: user.username, email: user.email, role: user.role, password: '' }
  } else {
    userForm.value = { full_name: '', username: '', email: '', role: 'ANNOTATOR', password: '' }
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
        full_name: userForm.value.full_name,
        email: userForm.value.email,
        role: userForm.value.role,
      }
      if (userForm.value.password) payload.password = userForm.value.password
      await adminStore.updateUser(editingUser.value.id, payload)
      showToast('Data pengguna berhasil diperbarui')
    } else {
      await adminStore.createUser({
        full_name: userForm.value.full_name,
        username: userForm.value.username,
        email: userForm.value.email,
        role: userForm.value.role,
        password: userForm.value.password
      })
      showToast('Akun pengguna berhasil dibuat')
    }
    closeUserModal()
  } catch (e) {
    modalError.value = e.response?.data?.detail || 'Gagal menyimpan data pengguna'
  } finally {
    savingUser.value = false
  }
}

async function toggleActive(user) {
  try {
    await adminStore.toggleUserActive(user.id, !user.is_active)
    showToast(`Akun ${user.username} ${!user.is_active ? 'diaktifkan' : 'dinonaktifkan'}`)
  } catch (e) {
    showToast('Gagal mengubah status akun', 'error')
  }
}

// ── Delete Confirm ────────────────────────────────────────────────────────
const showDeleteConfirm = ref(false)
const deleteConfirmMessage = ref('')
const deleting = ref(false)
const pendingDelete = ref({ type: null, item: null })

function confirmDeleteProject(project) {
  pendingDelete.value = { type: 'project', item: project }
  deleteConfirmMessage.value = `Proyek "${project.name}" dan ${project.total_tasks} grid tile di dalamnya akan dihapus permanen. Tindakan ini tidak dapat dibatalkan.`
  showDeleteConfirm.value = true
}

function confirmDeleteUser(user) {
  pendingDelete.value = { type: 'user', item: user }
  deleteConfirmMessage.value = `Akun pengguna "${user.full_name}" (@${user.username}) akan dihapus permanen.`
  showDeleteConfirm.value = true
}

async function executeDelete() {
  deleting.value = true
  try {
    const { type, item } = pendingDelete.value
    if (type === 'project') {
      await adminStore.deleteProject(item.id)
      showToast(`Proyek "${item.name}" berhasil dihapus`)
    } else {
      await adminStore.deleteUser(item.id)
      showToast(`Akun ${item.username} berhasil dihapus`)
    }
    showDeleteConfirm.value = false
  } catch (e) {
    showToast(e.response?.data?.detail || 'Gagal menghapus data', 'error')
    showDeleteConfirm.value = false
  } finally {
    deleting.value = false
    pendingDelete.value = { type: null, item: null }
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

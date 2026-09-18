<template>
  <div class="h-[calc(100vh-57px)] w-full flex bg-[#f0f2f5] font-sans text-[#2c3038] overflow-hidden">
    
    <!-- ══════════════════════════════════════════════════════════ -->
    <!-- 1. MODERN ADMIN SIDEBAR NAVIGATION                         -->
    <!-- ══════════════════════════════════════════════════════════ -->
    <aside class="w-64 lg:w-72 bg-white border-r border-[#e4e7eb] flex flex-col h-full shrink-0 z-20 select-none shadow-xs">
      
      <!-- Sidebar Brand Header -->
      <div class="p-5 border-b border-[#e4e7eb] bg-slate-50/70 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-[#d73f3f] flex items-center justify-center text-white shadow-sm">
            <Shield :size="18" />
          </div>
          <div>
            <div class="font-black text-sm text-[#1f242e] font-heading tracking-tight leading-tight">Admin Dashboard</div>
            <div class="text-[11px] text-slate-500 font-medium">GEOSTEVIA Control Hub</div>
          </div>
        </div>
        <div class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-bold">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Online</span>
        </div>
      </div>

      <!-- Sidebar Menu Groups (Scrollable) -->
      <div class="flex-1 overflow-y-auto p-4 space-y-6">
        
        <!-- GROUP 1: UTAMA / RINGKASAN -->
        <div class="space-y-1">
          <div class="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-400 mb-1.5">
            Ringkasan & Akun
          </div>
          
          <button
            @click="activeTab = 'account_info'"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer"
            :class="activeTab === 'account_info'
              ? 'bg-[#d73f3f] text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'"
          >
            <div class="flex items-center gap-2.5">
              <BadgeCheck :size="16" :class="activeTab === 'account_info' ? 'text-white' : 'text-slate-500'" />
              <span>Informasi Akun</span>
            </div>
            <span v-if="activeTab === 'account_info'" class="w-1.5 h-1.5 rounded-full bg-white"></span>
          </button>

          <button
            @click="activeTab = 'stats'"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer"
            :class="activeTab === 'stats'
              ? 'bg-[#d73f3f] text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'"
          >
            <div class="flex items-center gap-2.5">
              <BarChart3 :size="16" :class="activeTab === 'stats' ? 'text-white' : 'text-slate-500'" />
              <span>Statistik Kontribusi</span>
            </div>
            <span class="text-[10px] px-1.5 py-0.2 rounded font-mono" :class="activeTab === 'stats' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'">Live</span>
          </button>
        </div>

        <!-- GROUP 2: MANAJEMEN PENGGUNA -->
        <div class="space-y-1">
          <div class="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-400 mb-1.5">
            Manajemen Pengguna
          </div>

          <button
            @click="activeTab = 'users_crud'"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer"
            :class="activeTab === 'users_crud'
              ? 'bg-[#d73f3f] text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'"
          >
            <div class="flex items-center gap-2.5">
              <Users :size="16" :class="activeTab === 'users_crud' ? 'text-white' : 'text-slate-500'" />
              <span>CRUD Pengguna</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold"
              :class="activeTab === 'users_crud' ? 'bg-white text-[#d73f3f]' : 'bg-slate-200 text-slate-700'">
              {{ adminStore.users.length }}
            </span>
          </button>

          <button
            @click="activeTab = 'user_profile'"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer"
            :class="activeTab === 'user_profile'
              ? 'bg-[#d73f3f] text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'"
          >
            <div class="flex items-center gap-2.5">
              <UserCog :size="16" :class="activeTab === 'user_profile' ? 'text-white' : 'text-slate-500'" />
              <span>Profil Pengguna</span>
            </div>
            <span v-if="activeTab === 'user_profile'" class="w-1.5 h-1.5 rounded-full bg-white"></span>
          </button>
        </div>

        <!-- GROUP 3: KAWASAN & SPASIAL -->
        <div class="space-y-1">
          <div class="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-400 mb-1.5">
            Kawasan & Spasial
          </div>

          <button
            @click="activeTab = 'projects'"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer"
            :class="activeTab === 'projects'
              ? 'bg-[#d73f3f] text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'"
          >
            <div class="flex items-center gap-2.5">
              <FolderKanban :size="16" :class="activeTab === 'projects' ? 'text-white' : 'text-slate-500'" />
              <span>Panel Admin / Proyek</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold"
              :class="activeTab === 'projects' ? 'bg-white text-[#d73f3f]' : 'bg-slate-200 text-slate-700'">
              {{ adminStore.projects.length }}
            </span>
          </button>

          <button
            @click="activeTab = 'import'"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer"
            :class="activeTab === 'import'
              ? 'bg-[#d73f3f] text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'"
          >
            <div class="flex items-center gap-2.5">
              <UploadCloud :size="16" :class="activeTab === 'import' ? 'text-white' : 'text-slate-500'" />
              <span>Import Grid Kustom</span>
            </div>
            <span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-extrabold" v-if="activeTab !== 'import'">SHP</span>
          </button>
        </div>

        <!-- GROUP 4: MODUL PEMETAAN TERPADU (SHORTCUTS) -->
        <div class="space-y-1">
          <div class="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-400 mb-1.5">
            Modul Pemetaan
          </div>

          <router-link
            to="/tasking"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 transition-all"
          >
            <div class="flex items-center gap-2.5">
              <Grid :size="16" class="text-blue-500" />
              <span>Tasking Map</span>
            </div>
            <ExternalLink :size="12" class="text-slate-400" />
          </router-link>

          <router-link
            to="/qc"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 transition-all"
          >
            <div class="flex items-center gap-2.5">
              <CheckSquare :size="16" class="text-amber-500" />
              <span>QC Review</span>
            </div>
            <ExternalLink :size="12" class="text-slate-400" />
          </router-link>

          <router-link
            to="/export"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 transition-all"
          >
            <div class="flex items-center gap-2.5">
              <Download :size="16" class="text-emerald-500" />
              <span>Ekspor Dataset</span>
            </div>
            <ExternalLink :size="12" class="text-slate-400" />
          </router-link>

          <router-link
            to="/projects"
            class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 transition-all"
          >
            <div class="flex items-center gap-2.5">
              <Compass :size="16" class="text-rose-500" />
              <span>Katalog Proyek</span>
            </div>
            <ExternalLink :size="12" class="text-slate-400" />
          </router-link>
        </div>

      </div>

      <!-- Sidebar Footer: Active Admin User & Quick Logout -->
      <div class="p-4 border-t border-[#e4e7eb] bg-slate-50/70 shrink-0 space-y-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="w-8 h-8 rounded-lg bg-purple-600 text-white flex items-center justify-center font-black text-xs shrink-0 shadow-2xs">
              {{ (authStore.user?.full_name || authStore.userName || 'A').charAt(0).toUpperCase() }}
            </div>
            <div class="min-w-0">
              <div class="text-xs font-black text-slate-800 truncate leading-tight">
                {{ authStore.user?.full_name || authStore.userName }}
              </div>
              <div class="text-[10px] text-purple-700 font-bold flex items-center gap-1">
                <span>Administrator</span>
              </div>
            </div>
          </div>

          <button
            @click="authStore.logout()"
            title="Keluar (Logout)"
            class="p-2 hover:bg-rose-50 hover:text-rose-600 text-slate-400 border border-slate-200/80 rounded-lg transition-colors cursor-pointer bg-white"
          >
            <LogOut :size="14" />
          </button>
        </div>
      </div>
    </aside>

    <!-- ══════════════════════════════════════════════════════════ -->
    <!-- 2. MAIN VIEWPORT AREA (Header + Content)                   -->
    <!-- ══════════════════════════════════════════════════════════ -->
    <main class="flex-1 flex flex-col h-full overflow-y-auto">
      
      <!-- Top Header Bar -->
      <header class="bg-white border-b border-[#e4e7eb] px-6 lg:px-10 py-4 shrink-0 flex items-center justify-between gap-4 sticky top-0 z-10 shadow-2xs">
        <div>
          <!-- Dynamic Breadcrumbs -->
          <div class="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <span>Admin Dashboard</span>
            <span>/</span>
            <span class="font-bold text-slate-800 capitalize">{{ currentTabTitle }}</span>
          </div>
          <h1 class="text-xl font-black text-[#1f242e] font-heading tracking-tight leading-tight mt-0.5">
            {{ currentTabHeading }}
          </h1>
        </div>

        <div class="flex items-center gap-2.5">
          <!-- Contextual Action Buttons -->
          <button
            v-if="activeTab === 'projects'"
            @click="openProjectModal()"
            class="flex items-center gap-2 bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs px-4 py-2 rounded-xl transition-all shadow-sm cursor-pointer"
          >
            <Plus :size="14" />
            <span>Tambah Proyek Baru</span>
          </button>

          <button
            v-if="activeTab === 'users_crud'"
            @click="openUserModal()"
            class="flex items-center gap-2 bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs px-4 py-2 rounded-xl transition-all shadow-sm cursor-pointer"
          >
            <UserPlus :size="14" />
            <span>Tambah Pengguna</span>
          </button>

          <button
            @click="refreshCurrentTab"
            class="p-2 border border-slate-200 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors cursor-pointer bg-white"
            title="Segarkan Data"
          >
            <RotateCw :size="14" :class="{ 'animate-spin': isRefreshing }" />
          </button>
        </div>
      </header>

      <!-- Main Body Container -->
      <div class="flex-1 p-6 lg:p-10 space-y-6">

        <!-- ────────────────────────────────────────────────── -->
        <!-- VIEW 1: INFORMASI AKUN                             -->
        <!-- ────────────────────────────────────────────────── -->
        <div v-if="activeTab === 'account_info'" class="space-y-6 max-w-5xl">
          
          <!-- Welcome Hero Banner -->
          <div class="bg-gradient-to-r from-slate-900 via-[#1f242e] to-slate-800 text-white rounded-3xl p-6 sm:p-8 shadow-sm relative overflow-hidden">
            <div class="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
              <div class="flex items-center gap-4">
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-500 to-indigo-600 flex items-center justify-center font-black text-2xl text-white shadow-md border-2 border-white/20">
                  {{ (authStore.user?.full_name || authStore.userName || 'A').charAt(0).toUpperCase() }}
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <h2 class="text-2xl font-black text-white font-heading">{{ authStore.user?.full_name || authStore.userName }}</h2>
                    <span class="px-2.5 py-0.5 rounded-full bg-purple-500/30 border border-purple-400/40 text-purple-200 font-bold text-[11px] uppercase tracking-wider">
                      Administrator
                    </span>
                  </div>
                  <p class="text-xs text-slate-300 mt-1">
                    Username: <span class="font-mono text-white font-bold">{{ authStore.user?.username }}</span> · Hak Akses Penuh Sistem GEOSTEVIA
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <button
                  @click="activeTab = 'user_profile'"
                  class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white font-bold text-xs rounded-xl border border-white/20 transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <Pencil :size="13" />
                  <span>Edit Profil</span>
                </button>
                <button
                  @click="activeTab = 'projects'"
                  class="px-4 py-2 bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs rounded-xl transition-all flex items-center gap-1.5 shadow-sm cursor-pointer"
                >
                  <FolderKanban :size="13" />
                  <span>Kelola Proyek</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Account Details Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            <!-- Card 1: Data Identitas Pengguna -->
            <div class="bg-white rounded-2xl border border-slate-200/80 p-5 space-y-4 shadow-xs">
              <div class="flex items-center gap-2 text-slate-900 font-extrabold text-sm border-b border-slate-100 pb-3">
                <BadgeCheck :size="16" class="text-blue-600" />
                <span>Identitas Akun</span>
              </div>
              <div class="space-y-2.5 text-xs">
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Nama Lengkap</div>
                  <div class="font-bold text-slate-800 text-sm mt-0.5">{{ currentAdminUser.full_name || authStore.userName }}</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Alamat Email</div>
                  <div class="font-bold text-slate-800 mt-0.5">{{ currentAdminUser.email || '-' }}</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Nomor Induk (NIM/NIP)</div>
                  <div class="font-mono font-bold text-slate-800 mt-0.5">{{ currentAdminUser.nim_nip || 'N/A' }}</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Nomor Telepon / WhatsApp</div>
                  <div class="font-bold text-slate-800 mt-0.5">{{ currentAdminUser.phone || '-' }}</div>
                </div>
              </div>
            </div>

            <!-- Card 2: Lembaga & Satuan Kerja -->
            <div class="bg-white rounded-2xl border border-slate-200/80 p-5 space-y-4 shadow-xs">
              <div class="flex items-center gap-2 text-slate-900 font-extrabold text-sm border-b border-slate-100 pb-3">
                <Building2 :size="16" class="text-purple-600" />
                <span>Institusi & Divisi</span>
              </div>
              <div class="space-y-2.5 text-xs">
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Institusi / Universitas</div>
                  <div class="font-bold text-slate-800 mt-0.5">{{ currentAdminUser.institution || 'GEOSTEVIA Core Platform' }}</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Departemen / Fakultas</div>
                  <div class="font-bold text-slate-800 mt-0.5">{{ currentAdminUser.department || 'Divisi Spasial & Pemetaan' }}</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Alamat Domisili / Kantor</div>
                  <div class="text-slate-700 mt-0.5 leading-relaxed">{{ currentAdminUser.address || 'Padang, Sumatera Barat' }}</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Status Akun</div>
                  <div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-extrabold text-[11px] mt-0.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    <span>Aktif & Terverifikasi</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Card 3: Sesi & Keamanan -->
            <div class="bg-white rounded-2xl border border-slate-200/80 p-5 space-y-4 shadow-xs">
              <div class="flex items-center gap-2 text-slate-900 font-extrabold text-sm border-b border-slate-100 pb-3">
                <ShieldCheck :size="16" class="text-emerald-600" />
                <span>Status Keamanan & Sesi</span>
              </div>
              <div class="space-y-2.5 text-xs">
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Tipe Autentikasi</div>
                  <div class="font-mono text-slate-800 font-bold mt-0.5">OAuth2 / Bearer JWT (HS256)</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Masa Berlaku Token</div>
                  <div class="text-slate-700 mt-0.5">7 Hari sejak login (Auto-renew)</div>
                </div>
                <div>
                  <div class="text-slate-400 text-[10px] font-bold uppercase">Hak Istimewa (Privilege)</div>
                  <div class="text-slate-700 mt-0.5">
                    Full CRUD Proyek, CRUD User, QC Approval, Ekspor Dataset
                  </div>
                </div>
                <div class="pt-2">
                  <button
                    @click="activeTab = 'user_profile'"
                    class="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-xl transition-colors text-xs flex items-center justify-center gap-1.5"
                  >
                    <Key :size="13" />
                    <span>Ubah Password Akun</span>
                  </button>
                </div>
              </div>
            </div>

          </div>

          <!-- Quick System Metrics Bar -->
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
            <h3 class="text-xs font-black uppercase tracking-wider text-slate-400 mb-4">Ringkasan Beban Kerja Sistem</h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div class="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div class="text-2xl font-black text-slate-900 font-mono">{{ adminStore.projects.length }}</div>
                <div class="text-[11px] font-bold text-slate-500 uppercase mt-0.5">Total Proyek</div>
              </div>
              <div class="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div class="text-2xl font-black text-blue-600 font-mono">{{ totalUsersCount }}</div>
                <div class="text-[11px] font-bold text-slate-500 uppercase mt-0.5">Pengguna Terdaftar</div>
              </div>
              <div class="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div class="text-2xl font-black text-purple-600 font-mono">{{ totalSystemGrids }}</div>
                <div class="text-[11px] font-bold text-slate-500 uppercase mt-0.5">Total Grid Patches</div>
              </div>
              <div class="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div class="text-2xl font-black text-emerald-600 font-mono">{{ totalSystemApproved }}</div>
                <div class="text-[11px] font-bold text-slate-500 uppercase mt-0.5">Grid Lulus QC</div>
              </div>
            </div>
          </div>

        </div>

        <!-- ────────────────────────────────────────────────── -->
        <!-- VIEW 2: STATISTIK KONTRIBUSI                       -->
        <!-- ────────────────────────────────────────────────── -->
        <div v-if="activeTab === 'stats'" class="space-y-6">
          
          <!-- KPI Stats Summary Cards -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
              <div class="flex items-center justify-between text-slate-500">
                <span class="text-xs font-bold uppercase tracking-wider">Total Akun</span>
                <Users :size="18" class="text-slate-600" />
              </div>
              <div class="text-3xl font-black text-slate-900 mt-2 font-heading">{{ totalUsersCount }}</div>
              <div class="text-[11px] text-slate-400 mt-1">{{ activeAnnotatorsCount }} Kontributor Aktif</div>
            </div>

            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
              <div class="flex items-center justify-between text-slate-500">
                <span class="text-xs font-bold uppercase tracking-wider">Total Proyek</span>
                <FolderKanban :size="18" class="text-rose-600" />
              </div>
              <div class="text-3xl font-black text-slate-900 mt-2 font-heading">{{ adminStore.projects.length }}</div>
              <div class="text-[11px] text-slate-400 mt-1">Wilayah Kajian Spasial</div>
            </div>

            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
              <div class="flex items-center justify-between text-slate-500">
                <span class="text-xs font-bold uppercase tracking-wider">Total Grid Patches</span>
                <Grid :size="18" class="text-blue-600" />
              </div>
              <div class="text-3xl font-black text-slate-900 mt-2 font-mono">{{ totalSystemGrids }}</div>
              <div class="text-[11px] text-slate-400 mt-1">Resolusi 1024×1024px</div>
            </div>

            <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
              <div class="flex items-center justify-between text-slate-500">
                <span class="text-xs font-bold uppercase tracking-wider">Grid Lulus QC</span>
                <CheckCircle2 :size="18" class="text-emerald-600" />
              </div>
              <div class="text-3xl font-black text-emerald-600 mt-2 font-mono">{{ totalSystemApproved }}</div>
              <div class="text-[11px] text-emerald-700 font-bold mt-1">Siap Ekspor Data Latih</div>
            </div>
          </div>

          <!-- Leaderboard Kontributor Mahasiswa -->
          <div class="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
            <div class="p-5 border-b border-slate-100 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <Trophy :size="18" class="text-amber-500" />
                <h3 class="font-extrabold text-sm text-slate-800 font-heading">Leaderboard Kontributor Mahasiswa</h3>
              </div>
              <span class="text-xs text-slate-400">Peringkat berdasarkan grid selesai dan poligon</span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] border-b border-slate-200">
                  <tr>
                    <th class="py-3 px-4 w-12 text-center">Rank</th>
                    <th class="py-3 px-4">Kontributor / Mahasiswa</th>
                    <th class="py-3 px-4">NIM / Akun</th>
                    <th class="py-3 px-4 text-center">Grid Disetujui</th>
                    <th class="py-3 px-4 text-center">Total Poligon</th>
                    <th class="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr
                    v-for="(student, idx) in leaderboardList"
                    :key="student.id || idx"
                    class="hover:bg-slate-50/80 transition-colors"
                  >
                    <td class="py-3 px-4 text-center font-black">
                      <span v-if="idx === 0" class="text-lg">🥇</span>
                      <span v-else-if="idx === 1" class="text-lg">🥈</span>
                      <span v-else-if="idx === 2" class="text-lg">🥉</span>
                      <span v-else class="text-slate-400 font-mono">{{ idx + 1 }}</span>
                    </td>
                    <td class="py-3 px-4">
                      <div class="font-bold text-slate-900">{{ student.name || student.full_name }}</div>
                      <div class="text-[10px] text-slate-400">{{ student.institution || 'Mahasiswa' }}</div>
                    </td>
                    <td class="py-3 px-4 font-mono text-slate-600">
                      {{ student.nim_nip || student.username }}
                    </td>
                    <td class="py-3 px-4 text-center font-bold text-emerald-600 font-mono">
                      {{ student.approved_tasks || 0 }} Grid
                    </td>
                    <td class="py-3 px-4 text-center font-black text-purple-700 font-mono">
                      {{ student.total_polygons || 0 }}
                    </td>
                    <td class="py-3 px-4 text-center">
                      <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Aktif
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>

        <!-- ────────────────────────────────────────────────── -->
        <!-- VIEW 3: CRUD PENGGUNA                              -->
        <!-- ────────────────────────────────────────────────── -->
        <div v-if="activeTab === 'users_crud'" class="space-y-6">
          
          <!-- KPI Row -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs">
              <div class="text-xs font-bold text-slate-500 uppercase">Total Pengguna</div>
              <div class="text-2xl font-black text-slate-900 mt-1 font-heading">{{ totalUsersCount }}</div>
            </div>
            <div class="bg-white rounded-2xl p-4 border border-purple-200/80 shadow-xs bg-purple-50/20">
              <div class="text-xs font-bold text-purple-700 uppercase">Administrator</div>
              <div class="text-2xl font-black text-purple-900 mt-1 font-heading">{{ adminUsersCount }}</div>
            </div>
            <div class="bg-white rounded-2xl p-4 border border-indigo-200/80 shadow-xs bg-indigo-50/20">
              <div class="text-xs font-bold text-indigo-700 uppercase">Supervisi / Dosen</div>
              <div class="text-2xl font-black text-indigo-900 mt-1 font-heading">{{ dosenUsersCount }}</div>
            </div>
            <div class="bg-white rounded-2xl p-4 border border-rose-200/80 shadow-xs bg-rose-50/20">
              <div class="text-xs font-bold text-rose-700 uppercase">Kontributor Mahasiswa</div>
              <div class="text-2xl font-black text-rose-900 mt-1 font-heading">{{ activeAnnotatorsCount }}</div>
            </div>
          </div>

          <!-- Search & Filter Bar -->
          <div class="bg-white rounded-2xl border border-[#e4e7eb] p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
            <div class="relative flex-1 w-full max-w-md">
              <Search :size="15" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                v-model="userSearch"
                type="text"
                placeholder="Cari nama, NIM, email, username..."
                class="w-full pl-9 pr-8 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-hidden focus:border-rose-500 focus:bg-white"
              />
              <button v-if="userSearch" @click="userSearch = ''" class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                <X :size="13" />
              </button>
            </div>

            <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
              <select
                v-model="userRoleFilter"
                class="bg-slate-50 border border-slate-200 text-xs font-bold text-slate-700 py-2 px-3 rounded-xl focus:outline-hidden"
              >
                <option value="all">Semua Peran</option>
                <option value="admin">Administrator</option>
                <option value="dosen">Supervisi / Dosen</option>
                <option value="annotator">Anotator / Mahasiswa</option>
              </select>

              <select
                v-model="userStatusFilter"
                class="bg-slate-50 border border-slate-200 text-xs font-bold text-slate-700 py-2 px-3 rounded-xl focus:outline-hidden"
              >
                <option value="all">Semua Status</option>
                <option value="active">Aktif</option>
                <option value="inactive">Nonaktif</option>
              </select>
            </div>
          </div>

          <!-- User Table -->
          <div class="bg-white rounded-2xl border border-[#e4e7eb] overflow-hidden shadow-xs">
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] border-b border-slate-200">
                  <tr>
                    <th class="py-3.5 px-4">Pengguna</th>
                    <th class="py-3.5 px-4">Kontak & Lembaga</th>
                    <th class="py-3.5 px-4">Role / Peran</th>
                    <th class="py-3.5 px-4 text-center">Status</th>
                    <th class="py-3.5 px-4 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr
                    v-for="user in filteredUsers"
                    :key="user.id"
                    class="hover:bg-slate-50/80 transition-colors"
                  >
                    <!-- Pengguna -->
                    <td class="py-3.5 px-4">
                      <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-white text-xs shrink-0" :class="getAvatarColor(user)">
                          {{ (user.full_name || user.username || 'U').charAt(0).toUpperCase() }}
                        </div>
                        <div class="min-w-0">
                          <div class="font-extrabold text-slate-900 leading-tight">{{ user.full_name }}</div>
                          <div class="text-[11px] text-slate-400 font-mono">@{{ user.username }}</div>
                        </div>
                      </div>
                    </td>

                    <!-- Kontak & Lembaga -->
                    <td class="py-3.5 px-4">
                      <div class="text-slate-800">{{ user.email || '-' }}</div>
                      <div class="text-[11px] text-slate-400">{{ user.institution || '-' }} <span v-if="user.nim_nip">· NIM: {{ user.nim_nip }}</span></div>
                    </td>

                    <!-- Role Badge -->
                    <td class="py-3.5 px-4">
                      <span v-if="user.role === 'admin'" class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-purple-50 text-purple-700 border border-purple-200">Admin</span>
                      <span v-else-if="user.role === 'dosen' || user.role === 'supervisi'" class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-50 text-indigo-700 border border-indigo-200">Supervisi</span>
                      <span v-else class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-slate-100 text-slate-700 border border-slate-200">Kontributor</span>
                    </td>

                    <!-- Status -->
                    <td class="py-3.5 px-4 text-center">
                      <button
                        @click="toggleActive(user)"
                        class="px-2.5 py-1 rounded-full text-[10px] font-extrabold transition-all cursor-pointer border"
                        :class="user.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-slate-100 text-slate-500 border-slate-300'"
                      >
                        {{ user.is_active ? 'Aktif' : 'Nonaktif' }}
                      </button>
                    </td>

                    <!-- Aksi -->
                    <td class="py-3.5 px-4 text-right">
                      <div class="flex items-center justify-end gap-1.5">
                        <button
                          @click="openUserModal(user)"
                          class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                          title="Edit User"
                        >
                          <Pencil :size="13" />
                        </button>
                        <button
                          @click="openResetPasswordModal(user)"
                          class="p-1.5 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer"
                          title="Reset Password"
                        >
                          <Key :size="13" />
                        </button>
                        <button
                          v-if="user.id !== authStore.user?.id"
                          @click="confirmDeleteUser(user)"
                          class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                          title="Hapus User"
                        >
                          <Trash2 :size="13" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>

        <!-- ────────────────────────────────────────────────── -->
        <!-- VIEW 4: PROFIL PENGGUNA (EDITOR DETAIL)            -->
        <!-- ────────────────────────────────────────────────── -->
        <div v-if="activeTab === 'user_profile'" class="space-y-6 max-w-4xl">
          
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-6 shadow-xs">
            <div class="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 class="font-extrabold text-base text-slate-900 font-heading">Perbarui Informasi Profil</h3>
                <p class="text-xs text-slate-500 mt-0.5">Kelola identitas, instansi, dan informasi kontak akun administrator Anda.</p>
              </div>
              <span class="px-3 py-1 rounded-full bg-purple-50 text-purple-700 text-xs font-bold border border-purple-200">
                Administrator
              </span>
            </div>

            <form @submit.prevent="saveMyProfile" class="space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-700 uppercase">Nama Lengkap *</label>
                  <input v-model="profileForm.full_name" type="text" class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
                </div>
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-700 uppercase">Alamat Email *</label>
                  <input v-model="profileForm.email" type="email" class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-700 uppercase">Nomor Induk (NIM / NIP)</label>
                  <input v-model="profileForm.nim_nip" type="text" class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
                </div>
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-700 uppercase">Nomor Telepon / WhatsApp</label>
                  <input v-model="profileForm.phone" type="text" class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-700 uppercase">Institusi / Universitas</label>
                  <input v-model="profileForm.institution" type="text" class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
                </div>
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-700 uppercase">Fakultas / Program Studi</label>
                  <input v-model="profileForm.department" type="text" class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
                </div>
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-700 uppercase">Alamat Kantor / Domisili</label>
                <textarea v-model="profileForm.address" rows="2" class="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden resize-none"></textarea>
              </div>

              <div class="pt-2 flex justify-end">
                <button
                  type="submit"
                  :disabled="savingProfile"
                  class="px-6 py-2.5 bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs rounded-xl shadow-sm transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  <RotateCw v-if="savingProfile" :size="14" class="animate-spin" />
                  <Save v-else :size="14" />
                  <span>{{ savingProfile ? 'Menyimpan...' : 'Simpan Perubahan Profil' }}</span>
                </button>
              </div>
            </form>
          </div>

          <!-- Password Change Card -->
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
            <div class="border-b border-slate-100 pb-3">
              <h3 class="font-extrabold text-sm text-slate-900 font-heading">Ubah Password Administrator</h3>
              <p class="text-xs text-slate-500 mt-0.5">Pastikan password baru memiliki panjang minimal 6 karakter.</p>
            </div>

            <form @submit.prevent="changeMyPassword" class="space-y-4 max-w-md">
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-700 uppercase">Password Baru</label>
                <input v-model="passwordForm.new_password" type="password" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-700 uppercase">Konfirmasi Password Baru</label>
                <input v-model="passwordForm.confirm_password" type="password" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl focus:border-rose-500 focus:outline-hidden" />
              </div>
              <button
                type="submit"
                :disabled="savingPassword || !passwordForm.new_password"
                class="px-5 py-2 bg-slate-900 hover:bg-black text-white font-bold text-xs rounded-xl transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Lock :size="13" />
                <span>{{ savingPassword ? 'Memperbarui...' : 'Perbarui Password' }}</span>
              </button>
            </form>
          </div>

        </div>

        <!-- ────────────────────────────────────────────────── -->
        <!-- VIEW 5: PANEL ADMIN (KELOLA PROYEK)               -->
        <!-- ────────────────────────────────────────────────── -->
        <div v-if="activeTab === 'projects'" class="space-y-4">
          
          <!-- Projects Grid -->
          <div v-if="adminStore.loadingProjects" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div v-for="i in 3" :key="i" class="bg-white rounded-2xl border border-[#e4e7eb] p-5 animate-pulse space-y-3">
              <div class="h-4 bg-slate-200 rounded w-3/4"></div>
              <div class="h-3 bg-slate-100 rounded w-full"></div>
              <div class="h-3 bg-slate-100 rounded w-1/2"></div>
            </div>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div
              v-for="project in adminStore.projects"
              :key="project.id"
              class="bg-white rounded-2xl border border-[#e4e7eb] p-5 hover:border-slate-300 hover:shadow-md transition-all space-y-4"
            >
              <!-- Project Header with Lucide priority/difficulty badges -->
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <div class="flex items-center gap-1.5 mb-1.5">
                    <span
                      v-if="project.priority === 'URGENT'"
                      class="border border-red-500 text-red-600 font-extrabold text-[9px] px-2 py-0.5 rounded tracking-wider uppercase flex items-center gap-1"
                    >
                      <Flame :size="10" />
                      <span>URGENT</span>
                    </span>
                    <span
                      v-else-if="project.priority === 'HIGH'"
                      class="border border-amber-500 text-amber-600 font-extrabold text-[9px] px-2 py-0.5 rounded tracking-wider uppercase flex items-center gap-1"
                    >
                      <Clock :size="10" />
                      <span>HIGH</span>
                    </span>
                    <span
                      v-else
                      class="border border-blue-400 text-blue-600 font-extrabold text-[9px] px-2 py-0.5 rounded tracking-wider uppercase flex items-center gap-1"
                    >
                      <Layers :size="10" />
                      <span>{{ project.priority || 'MEDIUM' }}</span>
                    </span>
                    <span class="text-[10px] text-slate-500 font-medium">· {{ project.difficulty || 'Moderate' }}</span>
                  </div>
                  <div class="font-black text-sm text-[#1f242e] leading-tight">{{ project.name }}</div>
                  <div class="text-[11px] text-[#707a8a] mt-0.5 line-clamp-2">{{ project.description || 'Tidak ada deskripsi' }}</div>
                </div>

                <div class="flex gap-1 shrink-0">
                  <button
                    @click="confirmResetProject(project)"
                    class="w-7 h-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-400 hover:border-amber-400 hover:text-amber-600 hover:bg-amber-50 transition-all cursor-pointer"
                    title="Reset seluruh pengerjaan proyek"
                  >
                    <RotateCcw :size="12" />
                  </button>
                  <button
                    @click="openProjectModal(project)"
                    class="w-7 h-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-400 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-all cursor-pointer"
                    title="Edit Proyek"
                  >
                    <Pencil :size="12" />
                  </button>
                  <button
                    @click="confirmDeleteProject(project)"
                    class="w-7 h-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-400 hover:border-red-400 hover:text-red-600 hover:bg-red-50 transition-all cursor-pointer"
                    title="Hapus Proyek"
                  >
                    <Trash2 :size="12" />
                  </button>
                </div>
              </div>

              <!-- Stats Metrics -->
              <div class="grid grid-cols-3 gap-2 text-center">
                <div class="bg-slate-50 rounded-xl p-2 border border-slate-100">
                  <div class="font-black text-base text-[#1f242e] font-mono">{{ project.total_tasks?.toLocaleString() || 0 }}</div>
                  <div class="text-[10px] text-[#707a8a] font-bold uppercase">Total Grid</div>
                </div>
                <div class="bg-emerald-50/70 border border-emerald-100 rounded-xl p-2">
                  <div class="font-black text-base text-emerald-700 font-mono">{{ project.approved_tasks || 0 }}</div>
                  <div class="text-[10px] text-emerald-600 font-bold uppercase">Approved</div>
                </div>
                <div class="bg-blue-50/70 border border-blue-100 rounded-xl p-2">
                  <div class="font-black text-base text-blue-700 font-mono">{{ project.in_progress_tasks || 0 }}</div>
                  <div class="text-[10px] text-blue-600 font-bold uppercase">On Progress</div>
                </div>
              </div>

              <!-- Action Link -->
              <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                <router-link :to="`/project/${project.id}`" class="font-bold text-[#d73f3f] hover:underline flex items-center gap-1">
                  <span>Buka Tasking Studio</span>
                  <ExternalLink :size="12" />
                </router-link>
                <span class="text-[10px] text-slate-400 font-mono">ID: #{{ 64060 + project.id }}</span>
              </div>
            </div>
          </div>

        </div>

        <!-- ────────────────────────────────────────────────── -->
        <!-- VIEW 6: IMPORT GRID KUSTOM                         -->
        <!-- ────────────────────────────────────────────────── -->
        <div v-if="activeTab === 'import'" class="space-y-4 max-w-4xl">
          
          <div class="bg-white rounded-2xl border border-[#e4e7eb] p-6 space-y-6 shadow-xs">
            <div>
              <h3 class="font-extrabold text-base text-slate-900 font-heading">Import Grid Geospasial Kustom</h3>
              <p class="text-xs text-slate-500 mt-0.5">Unggah Shapefile (.zip) atau file GeoJSON (.geojson / .json) untuk membuat petak grid tasking otomatis.</p>
            </div>

            <!-- Target Project Type -->
            <div class="space-y-2">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">Tujuan Proyek:</label>
              <div class="flex items-center gap-4 text-xs font-bold">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="radio" v-model="importTargetType" value="existing" class="text-rose-600" />
                  <span>Tambahkan ke Proyek yang Sudah Ada</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="radio" v-model="importTargetType" value="new" class="text-rose-600" />
                  <span>Buat Proyek Baru Otomatis</span>
                </label>
              </div>
            </div>

            <div v-if="importTargetType === 'existing'" class="space-y-1">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">Pilih Proyek:</label>
              <select v-model="importSelectedProjectId" class="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800">
                <option v-for="p in adminStore.projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>

            <div v-else class="space-y-3">
              <div class="space-y-1">
                <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">Nama Proyek Baru *</label>
                <input v-model="importNewProjectName" type="text" placeholder="cth: Kawasan Hutan Lindung Riau 2026" class="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800" />
              </div>
              <div class="space-y-1">
                <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">Deskripsi Proyek</label>
                <textarea v-model="importNewProjectDesc" rows="2" class="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-800 resize-none"></textarea>
              </div>
            </div>

            <!-- Upload File Box -->
            <div
              @dragover.prevent="isDragOver = true"
              @dragleave.prevent="isDragOver = false"
              @drop.prevent="handleDrop"
              class="border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer"
              :class="isDragOver ? 'border-rose-500 bg-rose-50/40' : 'border-slate-300 bg-slate-50/50 hover:bg-slate-50'"
              @click="$refs.fileInput.click()"
            >
              <input ref="fileInput" type="file" accept=".zip,.geojson,.json" class="hidden" @change="onFileSelected" />
              <div class="w-12 h-12 rounded-xl bg-rose-100 text-[#d73f3f] flex items-center justify-center mx-auto mb-2">
                <UploadCloud :size="24" />
              </div>
              <div class="text-sm font-bold text-slate-800">
                {{ importFile ? importFile.name : 'Klik atau seret file Shapefile (.zip) / GeoJSON ke sini' }}
              </div>
              <div class="text-xs text-slate-400 mt-1">Maksimum ukuran file: 25 MB</div>
            </div>

            <button
              @click="executeImport"
              :disabled="!importFile || importLoading"
              class="w-full py-3 bg-[#d73f3f] hover:bg-[#c23434] text-white font-extrabold text-sm rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <RotateCw v-if="importLoading" :size="16" class="animate-spin" />
              <UploadCloud v-else :size="16" />
              <span>{{ importLoading ? 'Memproses & Mengimpor Grid...' : 'Proses & Import Grid Sekarang' }}</span>
            </button>

            <!-- Success Card -->
            <div v-if="importResult" class="p-4 bg-emerald-50 border border-emerald-300 rounded-2xl space-y-2">
              <div class="flex items-center gap-2 text-emerald-900 font-extrabold text-xs">
                <CheckCircle2 :size="16" class="text-emerald-600" />
                <span>{{ importResult.message }}</span>
              </div>
              <div class="text-[11px] text-emerald-800 space-y-0.5 font-mono">
                <div>• Proyek: <b>{{ importResult.study_area_name }}</b></div>
                <div>• Total Tugas Dibuat: <b>{{ importResult.created_tasks_count }} grid</b></div>
              </div>
            </div>

          </div>

        </div>

      </div>
    </main>

    <!-- ══════════════════════════════════════════════════════════ -->
    <!-- 3. MODAL: Tambah / Edit PROYEK (LUCIDE ICONS, NO EMOJI)   -->
    <!-- ══════════════════════════════════════════════════════════ -->
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
          <div class="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Nama Proyek *</label>
              <input v-model="projectForm.name" type="text" placeholder="cth: Mapping Sumatera Barat 2026"
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-hidden focus:border-[#d73f3f] transition-colors" />
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Deskripsi</label>
              <textarea v-model="projectForm.description" rows="2" placeholder="Deskripsi singkat proyek pemetaan..."
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-hidden focus:border-[#d73f3f] transition-colors resize-none"></textarea>
            </div>

            <!-- Priority Selector (Clean Lucide Icons, NO WhatsApp Emoji) -->
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider flex items-center gap-1.5">
                <Flame :size="13" class="text-rose-500" />
                <span>Prioritas Proyek *</span>
              </label>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <button
                  type="button"
                  @click="projectForm.priority = 'URGENT'"
                  class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
                  :class="projectForm.priority === 'URGENT' ? 'bg-red-50 border-red-500 text-red-700 shadow-2xs ring-2 ring-red-500/20' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                >
                  <Flame :size="13" class="text-red-600" />
                  <span>Urgent</span>
                </button>
                <button
                  type="button"
                  @click="projectForm.priority = 'HIGH'"
                  class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
                  :class="projectForm.priority === 'HIGH' ? 'bg-amber-50 border-amber-500 text-amber-700 shadow-2xs ring-2 ring-amber-500/20' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                >
                  <Clock :size="13" class="text-amber-600" />
                  <span>High</span>
                </button>
                <button
                  type="button"
                  @click="projectForm.priority = 'MEDIUM'"
                  class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
                  :class="projectForm.priority === 'MEDIUM' ? 'bg-blue-50 border-blue-500 text-blue-700 shadow-2xs ring-2 ring-blue-500/20' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                >
                  <Layers :size="13" class="text-blue-600" />
                  <span>Medium</span>
                </button>
                <button
                  type="button"
                  @click="projectForm.priority = 'LOW'"
                  class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
                  :class="projectForm.priority === 'LOW' ? 'bg-slate-100 border-slate-400 text-slate-800 shadow-2xs ring-2 ring-slate-400/20' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                >
                  <Shield :size="13" class="text-slate-500" />
                  <span>Low</span>
                </button>
              </div>
            </div>

            <!-- Difficulty Selector (Clean Lucide Icons, NO WhatsApp Emoji) -->
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider flex items-center gap-1.5">
                <SlidersHorizontal :size="13" class="text-slate-400" />
                <span>Tingkat Kesulitan *</span>
              </label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  @click="projectForm.difficulty = 'Beginner'"
                  class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
                  :class="projectForm.difficulty === 'Beginner' ? 'bg-emerald-50 border-emerald-500 text-emerald-700 shadow-2xs ring-2 ring-emerald-500/20' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                >
                  <CheckCircle2 :size="13" class="text-emerald-600" />
                  <span>Beginner</span>
                </button>
                <button
                  type="button"
                  @click="projectForm.difficulty = 'Moderate'"
                  class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
                  :class="projectForm.difficulty === 'Moderate' ? 'bg-amber-50 border-amber-500 text-amber-700 shadow-2xs ring-2 ring-amber-500/20' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                >
                  <SlidersHorizontal :size="13" class="text-amber-600" />
                  <span>Moderate</span>
                </button>
                <button
                  type="button"
                  @click="projectForm.difficulty = 'Challenging'"
                  class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer"
                  :class="projectForm.difficulty === 'Challenging' ? 'bg-rose-50 border-rose-500 text-rose-700 shadow-2xs ring-2 ring-rose-500/20' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                >
                  <AlertTriangle :size="13" class="text-rose-600" />
                  <span>Challenging</span>
                </button>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Latitude Pusat *</label>
                <input v-model.number="projectForm.center_lat" type="number" step="0.001" placeholder="-0.750"
                  class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-hidden focus:border-[#d73f3f] transition-colors" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Longitude Pusat *</label>
                <input v-model.number="projectForm.center_lon" type="number" step="0.001" placeholder="100.500"
                  class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-hidden focus:border-[#d73f3f] transition-colors" />
              </div>
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase tracking-wider">Default Zoom Level</label>
              <input v-model.number="projectForm.default_zoom" type="number" min="4" max="16" placeholder="8"
                class="w-full px-3.5 py-2.5 text-sm text-[#1f242e] border border-[#e4e7eb] rounded-xl focus:outline-hidden focus:border-[#d73f3f] transition-colors" />
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
                  <div class="w-9 h-5 bg-slate-200 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#d73f3f]"></div>
                </label>
              </div>

              <div v-if="projectForm.generateGrid" class="space-y-3">
                <p class="text-[11px] text-[#707a8a]">Masukkan bounding box wilayah untuk auto-generate grid tiles 1024×1024px (~10.24km/tile)</p>
                <div class="grid grid-cols-2 gap-2">
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Min Longitude</label>
                    <input v-model.number="projectForm.min_lon" type="number" step="0.01" placeholder="98.60"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-hidden focus:border-[#d73f3f]" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Max Longitude</label>
                    <input v-model.number="projectForm.max_lon" type="number" step="0.01" placeholder="101.80"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-hidden focus:border-[#d73f3f]" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Min Latitude</label>
                    <input v-model.number="projectForm.min_lat" type="number" step="0.01" placeholder="-3.10"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-hidden focus:border-[#d73f3f]" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Max Latitude</label>
                    <input v-model.number="projectForm.max_lat" type="number" step="0.01" placeholder="0.40"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-hidden focus:border-[#d73f3f]" />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Prefix Kode Grid</label>
                    <input v-model="projectForm.grid_prefix" type="text" maxlength="3" placeholder="SB"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-hidden focus:border-[#d73f3f] uppercase" />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-bold text-[#707a8a]">Patch Size (px)</label>
                    <select v-model.number="projectForm.patch_size_px"
                      class="w-full px-2.5 py-1.5 text-xs text-[#1f242e] border border-[#e4e7eb] rounded-lg focus:outline-hidden focus:border-[#d73f3f]">
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

          <!-- Modal footer -->
          <div class="px-6 py-4 border-t border-[#e4e7eb] flex items-center justify-end gap-3 bg-[#f8f9fa]">
            <button @click="closeProjectModal" class="px-4 py-2 text-xs font-bold text-[#707a8a] hover:text-[#1f242e] transition-colors cursor-pointer">
              Batal
            </button>
            <button
              @click="saveProject"
              :disabled="savingProject"
              class="px-5 py-2 text-xs font-bold text-white bg-[#d73f3f] hover:bg-[#c23434] rounded-xl transition-all flex items-center gap-2 shadow-sm cursor-pointer disabled:opacity-50"
            >
              <RotateCw v-if="savingProject" :size="14" class="animate-spin" />
              <Check v-else :size="14" />
              <span>{{ savingProject ? 'Menyimpan...' : 'Simpan Perubahan' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ══════════════════════════════════════════════════════════ -->
    <!-- 4. MODAL: Tambah / Edit PENGGUNA                            -->
    <!-- ══════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showUserModal"
        class="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="closeUserModal"
      >
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md border border-[#e4e7eb] overflow-hidden">
          <div class="px-6 py-5 border-b border-[#e4e7eb] flex items-center justify-between bg-[#f8f9fa]">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-xl bg-purple-600 flex items-center justify-center text-white">
                <UserPlus :size="16" />
              </div>
              <h3 class="font-black text-[#1f242e] text-sm">
                {{ editingUser ? 'Edit Pengguna' : 'Tambah Pengguna Baru' }}
              </h3>
            </div>
            <button @click="closeUserModal" class="text-[#707a8a] hover:text-[#1f242e] transition-colors cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <div class="p-6 space-y-3.5 max-h-[75vh] overflow-y-auto">
            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase">Nama Lengkap *</label>
              <input v-model="userForm.full_name" type="text" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl" />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase">Username *</label>
                <input v-model="userForm.username" type="text" :disabled="!!editingUser" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl disabled:bg-slate-100" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase">Role / Peran *</label>
                <select v-model="userForm.role" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl">
                  <option value="annotator">Anotator / Mapper</option>
                  <option value="dosen">Supervisi / Dosen</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase">Alamat Email</label>
              <input v-model="userForm.email" type="email" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl" />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase">NIM / NIP</label>
                <input v-model="userForm.nim_nip" type="text" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-[#555d6b] uppercase">Telepon</label>
                <input v-model="userForm.phone" type="text" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl" />
              </div>
            </div>

            <div v-if="!editingUser" class="space-y-1">
              <label class="text-xs font-bold text-[#555d6b] uppercase">Password Awal *</label>
              <div class="flex gap-2">
                <input v-model="userForm.password" type="text" class="w-full px-3.5 py-2 text-sm border border-slate-200 rounded-xl font-mono text-purple-700 font-bold" />
                <button type="button" @click="generateRandomPasswordForForm" class="px-3 py-2 bg-slate-100 text-xs font-bold rounded-xl shrink-0">Acak</button>
              </div>
            </div>

            <div v-if="modalError" class="text-xs text-red-600 bg-red-50 p-2.5 rounded-xl flex items-center gap-2">
              <AlertTriangle :size="14" />
              <span>{{ modalError }}</span>
            </div>
          </div>

          <div class="px-6 py-4 border-t border-[#e4e7eb] flex items-center justify-end gap-3 bg-[#f8f9fa]">
            <button @click="closeUserModal" class="px-4 py-2 text-xs font-bold text-slate-500">Batal</button>
            <button @click="saveUser" :disabled="savingUser" class="px-5 py-2 text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-xl">
              {{ savingUser ? 'Menyimpan...' : 'Simpan Pengguna' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ══════════════════════════════════════════════════════════ -->
    <!-- 5. MODAL: Reset Password PENGGUNA                           -->
    <!-- ══════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showResetPasswordModal" class="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="closeResetPasswordModal">
        <div class="bg-white rounded-3xl shadow-2xl w-full max-w-sm border border-[#e4e7eb] p-6 space-y-4">
          <div class="flex items-center gap-2.5 text-amber-800 font-black text-sm">
            <Key :size="18" class="text-amber-600" />
            <span>Reset Password Pengguna</span>
          </div>
          <p class="text-xs text-slate-500">Reset password untuk <b>{{ targetUserForPassword?.full_name }}</b> (@{{ targetUserForPassword?.username }}).</p>
          <div class="space-y-1">
            <label class="text-[10px] font-bold text-slate-600 uppercase">Password Baru</label>
            <div class="flex gap-2">
              <input v-model="newPasswordValue" type="text" class="w-full px-3 py-2 text-xs border rounded-xl font-mono text-purple-700 font-bold" />
              <button @click="generateNewPassword" class="px-2.5 py-1 bg-slate-100 text-xs font-bold rounded-xl shrink-0">Acak</button>
            </div>
          </div>
          <div class="flex items-center justify-end gap-2 pt-2">
            <button @click="closeResetPasswordModal" class="px-3 py-1.5 text-xs font-bold text-slate-500">Batal</button>
            <button @click="executeResetPassword" :disabled="resettingPassword" class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-xl">
              {{ resettingPassword ? 'Mereset...' : 'Simpan Password Baru' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast Notification -->
    <Teleport to="body">
      <div v-if="toast.show" class="fixed bottom-6 right-6 z-[9999] flex items-center gap-2.5 px-4 py-3 rounded-2xl shadow-xl border text-xs font-bold text-white transition-all animate-in slide-in-from-bottom"
        :class="toast.type === 'error' ? 'bg-red-600 border-red-700' : 'bg-slate-900 border-slate-800'">
        <CheckCircle2 v-if="toast.type === 'success'" :size="16" class="text-emerald-400" />
        <AlertTriangle v-else :size="16" class="text-amber-400" />
        <span>{{ toast.message }}</span>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Shield,
  FolderKanban,
  UploadCloud,
  Users,
  Plus,
  RotateCcw,
  Pencil,
  Trash2,
  Grid,
  AlertTriangle,
  X,
  CheckCircle2,
  FolderPlus,
  Search,
  RotateCw,
  ExternalLink,
  Key,
  ShieldCheck,
  Check,
  Lock,
  UserPlus,
  Flame,
  Clock,
  Layers,
  Compass,
  BarChart3,
  BadgeCheck,
  UserCog,
  Download,
  CheckSquare,
  Building2,
  SlidersHorizontal,
  Save,
  LogOut,
  Trophy
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useAdminStore } from '../stores/admin'
import { useTasksStore } from '../stores/tasks'
import api from '../services/api'

const authStore = useAuthStore()
const adminStore = useAdminStore()
const tasksStore = useTasksStore()

// ── Active Sidebar Tab ───────────────────────────────────────────────────
// Options: 'account_info' | 'stats' | 'users_crud' | 'user_profile' | 'projects' | 'import'
const activeTab = ref('projects')
const isRefreshing = ref(false)

const currentTabTitle = computed(() => {
  switch (activeTab.value) {
    case 'account_info': return 'Informasi Akun'
    case 'stats': return 'Statistik Kontribusi'
    case 'users_crud': return 'CRUD Pengguna'
    case 'user_profile': return 'Profil Pengguna'
    case 'projects': return 'Panel Admin / Proyek'
    case 'import': return 'Import Grid Kustom'
    default: return 'Dashboard'
  }
})

const currentTabHeading = computed(() => {
  switch (activeTab.value) {
    case 'account_info': return 'Informasi & Identitas Akun Administrator'
    case 'stats': return 'Statistik Pemetaan & Kontributor'
    case 'users_crud': return 'Manajemen Akun Pengguna & Mahasiswa'
    case 'user_profile': return 'Pengaturan Profil & Keamanan Akun'
    case 'projects': return 'Manajemen Proyek Tasking Grid Spasial'
    case 'import': return 'Import Grid Shapefile / GeoJSON'
    default: return 'Admin Dashboard'
  }
})

const currentAdminUser = computed(() => {
  return adminStore.users.find(u => u.id === authStore.user?.id) || authStore.user || {}
})

const totalSystemGrids = computed(() => {
  return adminStore.projects.reduce((acc, p) => acc + (p.total_tasks || 0), 0)
})

const totalSystemApproved = computed(() => {
  return adminStore.projects.reduce((acc, p) => acc + (p.approved_tasks || 0), 0)
})

// ── Toast ─────────────────────────────────────────────────────────────────
const toast = ref({ show: false, message: '', type: 'success' })
function showToast(message, type = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3500)
}

const refreshCurrentTab = async () => {
  isRefreshing.value = true
  try {
    await Promise.allSettled([
      adminStore.fetchProjects(),
      adminStore.fetchUsers(),
      tasksStore.fetchStatsSummary()
    ])
    showToast('Data berhasil diperbarui')
  } catch (e) {
    showToast('Gagal memuat ulang data', 'error')
  } finally {
    isRefreshing.value = false
  }
}

// ── Profile Editor Form State ─────────────────────────────────────────────
const profileForm = ref({
  full_name: '',
  email: '',
  phone: '',
  institution: '',
  department: '',
  nim_nip: '',
  address: ''
})
const passwordForm = ref({
  new_password: '',
  confirm_password: ''
})
const savingProfile = ref(false)
const savingPassword = ref(false)

const initProfileForm = () => {
  const u = currentAdminUser.value
  profileForm.value = {
    full_name: u.full_name || authStore.userName || '',
    email: u.email || '',
    phone: u.phone || '',
    institution: u.institution || '',
    department: u.department || '',
    nim_nip: u.nim_nip || '',
    address: u.address || ''
  }
}

async function saveMyProfile() {
  if (!profileForm.value.full_name.trim()) {
    showToast('Nama lengkap wajib diisi', 'error')
    return
  }
  savingProfile.value = true
  try {
    const updated = await adminStore.updateUser(authStore.user.id, profileForm.value)
    if (authStore.user) {
      authStore.user.full_name = updated.full_name
      localStorage.setItem('geoai_user', JSON.stringify(authStore.user))
    }
    showToast('Profil administrator berhasil diperbarui')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Gagal menyimpan profil', 'error')
  } finally {
    savingProfile.value = false
  }
}

async function changeMyPassword() {
  if (!passwordForm.value.new_password || passwordForm.value.new_password.length < 6) {
    showToast('Password baru minimal 6 karakter', 'error')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    showToast('Konfirmasi password tidak cocok', 'error')
    return
  }
  savingPassword.value = true
  try {
    await adminStore.resetPassword(authStore.user.id, passwordForm.value.new_password)
    passwordForm.value.new_password = ''
    passwordForm.value.confirm_password = ''
    showToast('Password berhasil diubah')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Gagal mengubah password', 'error')
  } finally {
    savingPassword.value = false
  }
}

// ── Users CRUD State ──────────────────────────────────────────────────────
const userSearch = ref('')
const userRoleFilter = ref('all')
const userStatusFilter = ref('all')

const totalUsersCount = computed(() => adminStore.users.length)
const adminUsersCount = computed(() => adminStore.users.filter(u => (u.role || '').toLowerCase() === 'admin').length)
const dosenUsersCount = computed(() => adminStore.users.filter(u => ['dosen', 'supervisi'].includes((u.role || '').toLowerCase())).length)
const activeAnnotatorsCount = computed(() => adminStore.users.filter(u => (u.role || '').toLowerCase() === 'annotator' && u.is_active).length)

const filteredUsers = computed(() => {
  let list = adminStore.users
  if (userRoleFilter.value === 'dosen') {
    list = list.filter(u => ['dosen', 'supervisi'].includes((u.role || '').toLowerCase()))
  } else if (userRoleFilter.value !== 'all') {
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
      u.nim_nip?.toLowerCase().includes(q)
    )
  }
  return list
})

const leaderboardList = computed(() => {
  const statsList = tasksStore.stats?.student_contributions || []
  if (statsList.length > 0) return statsList
  // Fallback to annotators list
  return adminStore.users.filter(u => (u.role || '').toLowerCase() === 'annotator').slice(0, 10).map((u, i) => ({
    name: u.full_name,
    username: u.username,
    nim_nip: u.nim_nip,
    institution: u.institution,
    approved_tasks: Math.max(0, 10 - i),
    total_polygons: Math.max(0, (10 - i) * 15)
  }))
})

const avatarGradients = [
  'bg-gradient-to-br from-indigo-500 to-purple-600',
  'bg-gradient-to-br from-rose-500 to-pink-600',
  'bg-gradient-to-br from-teal-500 to-emerald-600',
  'bg-gradient-to-br from-amber-500 to-orange-600',
  'bg-gradient-to-br from-blue-500 to-cyan-600'
]
function getAvatarColor(user) {
  if (!user) return avatarGradients[0]
  const str = user.username || user.full_name || 'U'
  let hash = 0
  for (let i = 0; i < str.length; i++) hash += str.charCodeAt(i)
  return avatarGradients[hash % avatarGradients.length]
}

async function toggleActive(user) {
  try {
    await adminStore.toggleUserActive(user.id, !user.is_active)
    showToast(`Status ${user.full_name} berhasil diubah`)
  } catch (e) {
    showToast('Gagal mengubah status pengguna', 'error')
  }
}

// ── Project Modal (Clean Lucide Priority / Difficulty) ────────────────────
const showProjectModal = ref(false)
const editingProject = ref(null)
const savingProject = ref(false)
const modalError = ref('')
const projectForm = ref({
  name: '', description: '', center_lat: null, center_lon: null, default_zoom: 8,
  priority: 'MEDIUM', difficulty: 'Moderate',
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
      priority: project.priority || 'MEDIUM',
      difficulty: project.difficulty || 'Moderate',
      generateGrid: false,
      min_lon: null, min_lat: null, max_lon: null, max_lat: null,
      grid_prefix: 'P', patch_size_px: 1024
    }
  } else {
    projectForm.value = {
      name: '', description: '', center_lat: null, center_lon: null, default_zoom: 8,
      priority: 'MEDIUM', difficulty: 'Moderate',
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
        default_zoom: projectForm.value.default_zoom,
        priority: projectForm.value.priority,
        difficulty: projectForm.value.difficulty
      })
      showToast('Proyek berhasil diperbarui')
    } else {
      const payload = {
        name: projectForm.value.name,
        description: projectForm.value.description,
        center_lat: projectForm.value.center_lat,
        center_lon: projectForm.value.center_lon,
        default_zoom: projectForm.value.default_zoom,
        priority: projectForm.value.priority,
        difficulty: projectForm.value.difficulty,
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

async function confirmResetProject(project) {
  if (!confirm(`Reset seluruh grid pada proyek "${project.name}" kembali ke status Tersedia?`)) return
  try {
    await adminStore.resetProject(project.id)
    showToast('Seluruh grid proyek berhasil direset ke status Tersedia')
  } catch (e) {
    showToast('Gagal mereset proyek', 'error')
  }
}

async function confirmDeleteProject(project) {
  if (!confirm(`Hapus proyek "${project.name}" beserta seluruh grid di dalamnya secara permanen?`)) return
  try {
    await adminStore.deleteProject(project.id)
    showToast('Proyek berhasil dihapus')
  } catch (e) {
    showToast('Gagal menghapus proyek', 'error')
  }
}

// ── User Modal State ──────────────────────────────────────────────────────
const showUserModal = ref(false)
const editingUser = ref(null)
const savingUser = ref(false)
const userForm = ref({
  full_name: '', username: '', email: '', role: 'annotator',
  password: '', is_active: true, phone: '', institution: '',
  department: '', nim_nip: '', address: ''
})

function generateSecurePassword() {
  const chars = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$'
  let pass = 'GeoAI-'
  for (let i = 0; i < 6; i++) pass += chars.charAt(Math.floor(Math.random() * chars.length))
  return pass
}

function generateRandomPasswordForForm() {
  userForm.value.password = generateSecurePassword()
}

function openUserModal(user = null) {
  editingUser.value = user
  modalError.value = ''
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
      full_name: '', username: '', email: '', role: 'annotator',
      password: generateSecurePassword(), is_active: true, phone: '',
      institution: '', department: '', nim_nip: '', address: ''
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
  if (!userForm.value.full_name.trim() || !userForm.value.username.trim()) {
    modalError.value = 'Nama lengkap dan username wajib diisi'
    return
  }
  savingUser.value = true
  modalError.value = ''
  try {
    if (editingUser.value) {
      await adminStore.updateUser(editingUser.value.id, userForm.value)
      showToast('Data pengguna berhasil diperbarui')
    } else {
      await adminStore.createUser(userForm.value)
      showToast('Pengguna baru berhasil ditambahkan')
    }
    closeUserModal()
  } catch (e) {
    modalError.value = e.response?.data?.detail || 'Gagal menyimpan data pengguna'
  } finally {
    savingUser.value = false
  }
}

async function confirmDeleteUser(user) {
  if (!confirm(`Nonaktifkan/hapus akun pengguna "${user.full_name}" (@${user.username})?`)) return
  try {
    await adminStore.deleteUser(user.id)
    showToast(`Pengguna ${user.full_name} berhasil dinonaktifkan`)
  } catch (e) {
    showToast('Gagal menghapus pengguna', 'error')
  }
}

// ── Reset Password Modal ──────────────────────────────────────────────────
const showResetPasswordModal = ref(false)
const targetUserForPassword = ref(null)
const newPasswordValue = ref('')
const resettingPassword = ref(false)

function openResetPasswordModal(user) {
  targetUserForPassword.value = user
  newPasswordValue.value = generateSecurePassword()
  showResetPasswordModal.value = true
}

function closeResetPasswordModal() {
  showResetPasswordModal.value = false
  targetUserForPassword.value = null
}

function generateNewPassword() {
  newPasswordValue.value = generateSecurePassword()
}

async function executeResetPassword() {
  if (!newPasswordValue.value) return
  resettingPassword.value = true
  try {
    await adminStore.resetPassword(targetUserForPassword.value.id, newPasswordValue.value)
    showToast(`Password untuk ${targetUserForPassword.value.full_name} berhasil direset`)
    closeResetPasswordModal()
  } catch (e) {
    showToast('Gagal mereset password', 'error')
  } finally {
    resettingPassword.value = false
  }
}

// ── Import Grid State ─────────────────────────────────────────────────────
const importTargetType = ref('existing')
const importSelectedProjectId = ref(null)
const importNewProjectName = ref('')
const importNewProjectDesc = ref('')
const importFile = ref(null)
const isDragOver = ref(false)
const importLoading = ref(false)
const importResult = ref(null)

const onFileSelected = (e) => {
  const file = e.target.files[0]
  if (file) handleChosenFile(file)
}
const handleDrop = (e) => {
  isDragOver.value = false
  const file = e.dataTransfer?.files[0]
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
const executeImport = async () => {
  if (!importFile.value) {
    showToast('Pilih file Shapefile (.zip) atau GeoJSON terlebih dahulu', 'error')
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
      if (importNewProjectDesc.value) formData.append('new_project_desc', importNewProjectDesc.value)
    }
    formData.append('years_str', '2026,2017')
    const res = await api.importGrid(formData)
    importResult.value = res.data
    showToast(res.data?.message || 'Grid kustom berhasil diimpor!', 'success')
    await adminStore.fetchProjects()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Gagal mengimpor file grid geospasial', 'error')
  } finally {
    importLoading.value = false
  }
}

// ── Initial Mount ─────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.allSettled([
    adminStore.fetchProjects(),
    adminStore.fetchUsers(),
    tasksStore.fetchStatsSummary()
  ])
  initProfileForm()
  if (adminStore.projects.length > 0 && !importSelectedProjectId.value) {
    importSelectedProjectId.value = adminStore.projects[0].id
  }
})
</script>

<style scoped>
input, textarea, select {
  color: #1f242e !important;
  background-color: #ffffff;
}
input::placeholder, textarea::placeholder {
  color: #9ca3af;
}
input:disabled, textarea:disabled, select:disabled {
  color: #707a8a !important;
  background-color: #f8f9fa;
}
</style>

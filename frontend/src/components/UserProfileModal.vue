<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
    <div class="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200">
      
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-2xl flex items-center justify-center font-bold text-white shadow-sm" :class="authStore.isAdmin ? 'bg-amber-500' : 'bg-rose-600'">
            {{ authStore.user?.full_name?.charAt(0) || 'U' }}
          </div>
          <div>
            <h2 class="text-base font-extrabold text-slate-900 leading-tight">Manajemen Profil & Pengguna</h2>
            <p class="text-xs text-slate-500 font-medium">GEOSTEVIA • Geospatial Ecosystem Services Analytics</p>
          </div>
        </div>
        <button
          @click="closeModal"
          class="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-xl transition-colors cursor-pointer"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- Navigation Tabs inside Profile Modal -->
      <div class="px-6 border-b border-slate-200 bg-white flex items-center gap-6 text-xs font-bold uppercase tracking-wider">
        <button
          @click="activeTab = 'info'"
          class="py-3 border-b-2 transition-colors flex items-center gap-2 cursor-pointer"
          :class="activeTab === 'info' ? 'border-rose-600 text-rose-600' : 'border-transparent text-slate-500 hover:text-slate-900'"
        >
          <User :size="14" />
          <span>Informasi Akun</span>
        </button>
        <button
          @click="activeTab = 'stats'"
          class="py-3 border-b-2 transition-colors flex items-center gap-2 cursor-pointer"
          :class="activeTab === 'stats' ? 'border-rose-600 text-rose-600' : 'border-transparent text-slate-500 hover:text-slate-900'"
        >
          <PieChart :size="14" />
          <span>Statistik Kontribusi</span>
        </button>
        <button
          v-if="authStore.isAdmin"
          @click="activeTab = 'crud_users'; loadUsers()"
          class="py-3 border-b-2 transition-colors flex items-center gap-2 cursor-pointer"
          :class="activeTab === 'crud_users' ? 'border-rose-600 text-rose-600' : 'border-transparent text-slate-500 hover:text-slate-900'"
        >
          <Users :size="14" />
          <span>CRUD Pengguna (Admin)</span>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 overflow-y-auto space-y-6 text-xs text-slate-700 flex-1">
        
        <!-- Alert feedback -->
        <div v-if="feedbackMsg" class="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center justify-between text-xs">
          <span>{{ feedbackMsg }}</span>
          <button @click="feedbackMsg = ''" class="text-emerald-600 hover:text-emerald-900 cursor-pointer"><X :size="14" /></button>
        </div>

        <div v-if="errorMsg" class="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl flex items-center justify-between text-xs">
          <span>{{ errorMsg }}</span>
          <button @click="errorMsg = ''" class="text-rose-600 hover:text-rose-900 cursor-pointer"><X :size="14" /></button>
        </div>

        <!-- TAB 1: INFORMASI AKUN -->
        <div v-if="activeTab === 'info'" class="space-y-5">
          <div class="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-4 text-center sm:text-left">
              <div class="w-14 h-14 rounded-2xl flex items-center justify-center font-black text-xl text-white shadow-md" :class="authStore.isAdmin ? 'bg-amber-500' : (authStore.isDosen ? 'bg-indigo-600' : 'bg-rose-600')">
                {{ authStore.user?.full_name?.charAt(0) || 'U' }}
              </div>
              <div>
                <div class="text-sm font-extrabold text-slate-900">{{ authStore.user?.full_name }}</div>
                <div class="text-xs text-slate-500 font-mono">@{{ authStore.user?.username }} • {{ authStore.user?.email || 'user@stevi.id' }}</div>
                <div class="mt-1 flex items-center gap-2 justify-center sm:justify-start">
                  <span
                    class="px-2 py-0.5 rounded-full font-bold text-[10px] uppercase tracking-wider"
                    :class="authStore.isAdmin
                      ? 'bg-amber-100 text-amber-800 border border-amber-300'
                      : (authStore.isDosen
                        ? 'bg-indigo-100 text-indigo-800 border border-indigo-300'
                        : 'bg-rose-100 text-rose-700 border border-rose-300')"
                  >
                    {{ authStore.roleTitle }}
                  </span>
                  <span class="text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-bold text-[10px]">
                    ● Aktif
                  </span>
                </div>
              </div>
            </div>

            <button
              @click="authStore.logout(); closeModal()"
              class="px-4 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <LogOut :size="14" />
              <span>Keluar (Logout)</span>
            </button>
          </div>

          <!-- Form Edit Profil & Data Administrasi (Opsional) -->
          <div class="bg-slate-50/70 rounded-2xl border border-slate-200 p-5 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 class="font-extrabold text-slate-900 text-xs flex items-center gap-2">
                  <FileText :size="15" class="text-rose-600" />
                  <span>Data Administrasi & Profil Pengguna</span>
                </h3>
                <p class="text-[11px] text-slate-500 mt-0.5">Informasi pendukung dokumen, administrasi kegiatan, dan sertifikasi anotasi (opsional).</p>
              </div>
              <span class="text-[10px] font-bold text-slate-400 uppercase bg-slate-200/60 px-2 py-0.5 rounded-full">Opsional</span>
            </div>

            <form @submit.prevent="saveSelfProfile" class="space-y-3.5">
              <!-- Baris 1: Nama Lengkap & Email -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700">Nama Lengkap</label>
                  <input
                    v-model="selfProfileForm.full_name"
                    type="text"
                    required
                    placeholder="Nama Lengkap & Gelar"
                    class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
                  />
                </div>
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700">Email Akun</label>
                  <input
                    v-model="selfProfileForm.email"
                    type="email"
                    required
                    placeholder="nama@email.com"
                    class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
                  />
                </div>
              </div>

              <!-- Baris 2: No Telpon/WA & NIM/NIP -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <Phone :size="12" class="text-slate-400" />
                    <span>No. WhatsApp / Telepon</span>
                  </label>
                  <input
                    v-model="selfProfileForm.phone"
                    type="text"
                    placeholder="Contoh: 081234567890"
                    class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
                  />
                </div>
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <FileText :size="12" class="text-slate-400" />
                    <span>NIM / NIP / ID Identitas</span>
                  </label>
                  <input
                    v-model="selfProfileForm.nim_nip"
                    type="text"
                    placeholder="Contoh: 211001234 atau 198501..."
                    class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>
              </div>

              <!-- Baris 3: Universitas/Instansi & Program Studi/Jurusan -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <Building2 :size="12" class="text-slate-400" />
                    <span>Universitas / Lembaga / Instansi</span>
                  </label>
                  <input
                    v-model="selfProfileForm.institution"
                    type="text"
                    placeholder="Contoh: Universitas Andalas / KLHK"
                    class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
                  />
                </div>
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <GraduationCap :size="12" class="text-slate-400" />
                    <span>Program Studi / Jurusan / Unit</span>
                  </label>
                  <input
                    v-model="selfProfileForm.department"
                    type="text"
                    placeholder="Contoh: S1 Geografi / Kehutanan"
                    class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
                  />
                </div>
              </div>

              <!-- Baris 4: Alamat Domisili -->
              <div class="space-y-1">
                <label class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                  <MapPin :size="12" class="text-slate-400" />
                  <span>Alamat Lengkap / Domisili</span>
                </label>
                <textarea
                  v-model="selfProfileForm.address"
                  rows="2"
                  placeholder="Contoh: Jl. Sudirman No. 12, Padang, Sumatera Barat"
                  class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500 resize-none font-sans"
                ></textarea>
              </div>

              <!-- Baris 5: Ganti Password (Opsional) -->
              <div class="pt-2 border-t border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div class="w-full sm:w-1/2 space-y-1">
                  <label class="text-[11px] font-bold text-slate-700">Ganti Password (Opsional)</label>
                  <input
                    v-model="selfProfileForm.password"
                    type="password"
                    placeholder="Kosongkan jika tidak diganti"
                    class="w-full bg-white border border-slate-300 rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>

                <div class="w-full sm:w-auto flex justify-end pt-2 sm:pt-4">
                  <button
                    type="submit"
                    :disabled="savingProfile"
                    class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-extrabold text-xs transition-all shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    <Save :size="14" />
                    <span>{{ savingProfile ? 'Menyimpan...' : 'Simpan Profil' }}</span>
                  </button>
                </div>
              </div>
            </form>
          </div>

          <!-- Quick Page Navigation Shortcuts -->
          <div class="space-y-2 pt-2 border-t border-slate-200">
            <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Akses Langsung Halaman Sistem</div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <router-link
                v-if="authStore.isAdmin"
                to="/admin"
                @click="closeModal"
                class="p-2.5 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-xl text-left flex flex-col justify-between transition-colors shadow-2xs group"
              >
                <div class="flex items-center justify-between text-purple-700">
                  <Shield :size="16" />
                  <span class="text-[9px] font-mono font-bold bg-purple-200 px-1 py-0.2 rounded">Admin</span>
                </div>
                <div class="mt-2 font-bold text-slate-800 text-xs group-hover:text-purple-700">Panel Admin</div>
                <div class="text-[10px] text-slate-500">CRUD Proyek & User</div>
              </router-link>

              <router-link
                to="/export"
                @click="closeModal"
                class="p-2.5 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-xl text-left flex flex-col justify-between transition-colors shadow-2xs group"
              >
                <div class="flex items-center justify-between text-emerald-700">
                  <Box :size="16" />
                  <span class="text-[9px] font-mono font-bold bg-emerald-200 px-1 py-0.2 rounded">DATASET</span>
                </div>
                <div class="mt-2 font-bold text-slate-800 text-xs group-hover:text-emerald-700">Dataset Export</div>
                <div class="text-[10px] text-slate-500">Raster & Vektor Penutupan Lahan</div>
              </router-link>

              <router-link
                v-if="authStore.isReviewer"
                to="/qc"
                @click="closeModal"
                class="p-2.5 bg-orange-50 hover:bg-orange-100 border border-orange-200 rounded-xl text-left flex flex-col justify-between transition-colors shadow-2xs group"
              >
                <div class="flex items-center justify-between text-orange-700">
                  <ClipboardCheck :size="16" />
                  <span class="text-[9px] font-mono font-bold bg-orange-200 px-1 py-0.2 rounded">QC</span>
                </div>
                <div class="mt-2 font-bold text-slate-800 text-xs group-hover:text-orange-700">QC Review</div>
                <div class="text-[10px] text-slate-500">Validasi Anotasi Grid</div>
              </router-link>

              <router-link
                to="/tasking"
                @click="closeModal"
                class="p-2.5 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl text-left flex flex-col justify-between transition-colors shadow-2xs group"
              >
                <div class="flex items-center justify-between text-rose-700">
                  <Grid :size="16" />
                  <span class="text-[9px] font-mono font-bold bg-rose-200 px-1 py-0.2 rounded">Grid</span>
                </div>
                <div class="mt-2 font-bold text-slate-800 text-xs group-hover:text-rose-700">Tasking Map</div>
                <div class="text-[10px] text-slate-500">Pilih Grid Digitasi</div>
              </router-link>
            </div>
          </div>
        </div>

        <!-- TAB 2: STATISTIK KONTRIBUSI -->
        <div v-if="activeTab === 'stats'" class="space-y-5">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-2xl">
              <div class="text-[10px] font-bold text-slate-500 uppercase">Grid Dikerjakan</div>
              <div class="text-xl font-black text-slate-900 font-mono mt-0.5">8 Grid</div>
            </div>
            <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-2xl">
              <div class="text-[10px] font-bold text-emerald-700 uppercase">Grid Approved</div>
              <div class="text-xl font-black text-emerald-800 font-mono mt-0.5">6 Grid</div>
            </div>
            <div class="p-3 bg-orange-50 border border-orange-200 rounded-2xl">
              <div class="text-[10px] font-bold text-orange-700 uppercase">Review QC</div>
              <div class="text-xl font-black text-orange-800 font-mono mt-0.5">2 Grid</div>
            </div>
            <div class="p-3 bg-purple-50 border border-purple-200 rounded-2xl">
              <div class="text-[10px] font-bold text-purple-700 uppercase">Total Poligon</div>
              <div class="text-xl font-black text-purple-800 font-mono mt-0.5">142</div>
            </div>
          </div>
        </div>

        <!-- TAB 3: CRUD PENGGUNA (Admin / Dosen Only) -->
        <div v-if="activeTab === 'crud_users' && authStore.isAdmin" class="space-y-4">
          
          <!-- Banner link to Full Admin Panel -->
          <div class="p-3.5 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl flex items-center justify-between gap-3">
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                <Shield :size="16" />
              </div>
              <div>
                <div class="font-black text-xs text-purple-900">Suite Manajemen Pengguna 2026 Tersedia</div>
                <div class="text-[11px] text-purple-700">Akses statistik KPI, filter peran/status, password generator, dan tampilan kartu di Panel Admin.</div>
              </div>
            </div>
            <router-link
              to="/admin"
              @click="closeModal"
              class="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs transition-colors shrink-0 flex items-center gap-1 shadow-xs"
            >
              <span>Buka Panel Admin</span>
              <ExternalLink :size="12" />
            </router-link>
          </div>

          <div class="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <h3 class="font-extrabold text-slate-900 text-sm">Manajemen Pengguna (CRUD)</h3>
              <p class="text-slate-500 text-[11px]">Tambah, perbarui peran, reset password, dan kelola akses pengguna.</p>
            </div>

            <button
              @click="openAddUserModal"
              class="bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold text-xs px-3.5 py-2 rounded-xl transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
            >
              <UserPlus :size="14" />
              <span>Tambah User Baru</span>
            </button>
          </div>

          <!-- Table of Users -->
          <div class="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-2xs">
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs min-w-[650px]">
                <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th class="p-3 whitespace-nowrap">User</th>
                    <th class="p-3 whitespace-nowrap">Email</th>
                    <th class="p-3 whitespace-nowrap">Role</th>
                    <th class="p-3 whitespace-nowrap">Status</th>
                    <th class="p-3 pr-5 text-right whitespace-nowrap">Aksi</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-for="u in usersList" :key="u.id" class="hover:bg-slate-50/80 transition-colors">
                    <td class="p-3">
                      <div class="font-bold text-slate-900">{{ u.full_name }}</div>
                      <div class="text-[10px] text-slate-400 font-mono">@{{ u.username }}</div>
                    </td>
                    <td class="p-3 font-mono text-[11px] text-slate-600">
                      {{ u.email }}
                    </td>
                    <td class="p-3">
                      <span
                        class="px-2 py-0.5 rounded-full font-bold text-[10px] uppercase tracking-wider"
                        :class="u.role?.toLowerCase() === 'admin'
                          ? 'bg-amber-100 text-amber-800 border border-amber-300'
                          : (['dosen', 'supervisi'].includes(u.role?.toLowerCase())
                            ? 'bg-indigo-100 text-indigo-800 border border-indigo-300'
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-300')"
                      >
                        {{ u.role?.toLowerCase() === 'admin' ? 'Admin' : (['dosen', 'supervisi'].includes(u.role?.toLowerCase()) ? 'Supervisi' : 'Mapper') }}
                      </span>
                    </td>
                    <td class="p-3">
                      <span class="inline-flex items-center gap-1 font-bold text-[10px]" :class="u.is_active ? 'text-emerald-600' : 'text-slate-400'">
                        ● {{ u.is_active ? 'Aktif' : 'Non-aktif' }}
                      </span>
                    </td>
                    <td class="p-3 pr-5 text-right whitespace-nowrap space-x-1.5">
                      <button
                        @click="openEditUserModal(u)"
                        class="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                        title="Edit Data User"
                      >
                        <Pencil :size="13" />
                      </button>
                      <button
                        v-if="u.id !== authStore.user?.id"
                        @click="handleDeleteUser(u)"
                        class="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                        title="Hapus User"
                      >
                        <Trash2 :size="13" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>

      <!-- Modal Footer -->
      <div class="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
        <span class="text-[11px] text-slate-500">GEOSTEVIA (Geospatial Ecosystem Services Analytics)</span>
        <button
          @click="closeModal"
          class="bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs px-5 py-2 rounded-xl transition-colors cursor-pointer"
        >
          Tutup
        </button>
      </div>

    </div>

    <!-- SUB-MODAL: Add / Edit User Form -->
    <div v-if="showUserFormModal" class="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div class="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-md p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="font-extrabold text-slate-900 text-sm">
            {{ isEditing ? 'Edit Akun Pengguna' : 'Tambah Pengguna Baru' }}
          </h3>
          <button @click="showUserFormModal = false" class="text-slate-400 hover:text-slate-700 cursor-pointer">
            <X :size="18" />
          </button>
        </div>

        <form @submit.prevent="submitUserForm" class="space-y-3 text-xs">
          <div>
            <label class="block font-bold text-slate-700 mb-1">Nama Lengkap</label>
            <input
              v-model="userForm.full_name"
              type="text"
              required
              class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:border-rose-500 focus:bg-white"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Username</label>
            <input
              v-model="userForm.username"
              type="text"
              required
              :disabled="isEditing"
              class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:border-rose-500 focus:bg-white disabled:opacity-60"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Email</label>
            <input
              v-model="userForm.email"
              type="email"
              required
              class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:border-rose-500 focus:bg-white"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Peran (Role)</label>
            <select
              v-model="userForm.role"
              class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:border-rose-500 focus:bg-white font-medium"
            >
              <option value="annotator">Kontributor / Mapper (Annotator)</option>
              <option value="dosen">Supervisi (Verifikasi & QC)</option>
              <option value="admin">Administrator (Admin)</option>
            </select>
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">
              {{ isEditing ? 'Password Baru (Kosongkan jika tidak diubah)' : 'Password' }}
            </label>
            <input
              v-model="userForm.password"
              type="password"
              :required="!isEditing"
              placeholder="••••••••"
              class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:border-rose-500 focus:bg-white"
            />
          </div>

          <div v-if="isEditing" class="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="is_active_checkbox"
              v-model="userForm.is_active"
              class="rounded border-slate-300 text-rose-600 focus:ring-rose-500"
            />
            <label for="is_active_checkbox" class="font-bold text-slate-700">Akun Aktif</label>
          </div>

          <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              @click="showUserFormModal = false"
              class="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 font-bold cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              class="px-5 py-2 rounded-xl bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold transition-colors cursor-pointer"
            >
              Simpan
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import {
  X,
  User,
  PieChart,
  Users,
  LogOut,
  ShieldCheck,
  GraduationCap,
  Shield,
  UserPlus,
  Pencil,
  Trash2,
  Box,
  Grid,
  ClipboardCheck,
  ExternalLink,
  Phone,
  Building2,
  MapPin,
  Save,
  FileText
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const authStore = useAuthStore()
const activeTab = ref('info')
const usersList = ref([])
const feedbackMsg = ref('')
const errorMsg = ref('')

const savingProfile = ref(false)
const selfProfileForm = reactive({
  full_name: '',
  email: '',
  phone: '',
  institution: '',
  department: '',
  nim_nip: '',
  address: '',
  password: ''
})

const showUserFormModal = ref(false)
const isEditing = ref(false)
const editingUserId = ref(null)

const userForm = reactive({
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

const closeModal = () => {
  emit('close')
}

const loadSelfProfile = () => {
  const u = authStore.user || {}
  selfProfileForm.full_name = u.full_name || ''
  selfProfileForm.email = u.email || ''
  selfProfileForm.phone = u.phone || ''
  selfProfileForm.institution = u.institution || ''
  selfProfileForm.department = u.department || ''
  selfProfileForm.nim_nip = u.nim_nip || ''
  selfProfileForm.address = u.address || ''
  selfProfileForm.password = ''
}

const saveSelfProfile = async () => {
  savingProfile.value = true
  feedbackMsg.value = ''
  errorMsg.value = ''
  try {
    const payload = {
      full_name: selfProfileForm.full_name,
      email: selfProfileForm.email,
      phone: selfProfileForm.phone,
      institution: selfProfileForm.institution,
      department: selfProfileForm.department,
      nim_nip: selfProfileForm.nim_nip,
      address: selfProfileForm.address
    }
    if (selfProfileForm.password && selfProfileForm.password.trim()) {
      payload.password = selfProfileForm.password.trim()
    }
    await authStore.updateProfile(payload)
    feedbackMsg.value = 'Profil dan data administrasi Anda berhasil disimpan!'
    selfProfileForm.password = ''
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Gagal menyimpan profil.'
  } finally {
    savingProfile.value = false
  }
}

const loadUsers = async () => {
  if (authStore.isAdmin) {
    usersList.value = await authStore.fetchAllUsers()
  }
}

const openAddUserModal = () => {
  isEditing.value = false
  editingUserId.value = null
  userForm.full_name = ''
  userForm.username = ''
  userForm.email = ''
  userForm.role = 'annotator'
  userForm.password = ''
  userForm.is_active = true
  userForm.phone = ''
  userForm.institution = ''
  userForm.department = ''
  userForm.nim_nip = ''
  userForm.address = ''
  showUserFormModal.value = true
}

const openEditUserModal = (user) => {
  isEditing.value = true
  editingUserId.value = user.id
  userForm.full_name = user.full_name
  userForm.username = user.username
  userForm.email = user.email
  userForm.role = (user.role || 'annotator').toLowerCase()
  userForm.password = ''
  userForm.is_active = user.is_active
  userForm.phone = user.phone || ''
  userForm.institution = user.institution || ''
  userForm.department = user.department || ''
  userForm.nim_nip = user.nim_nip || ''
  userForm.address = user.address || ''
  showUserFormModal.value = true
}

const submitUserForm = async () => {
  feedbackMsg.value = ''
  errorMsg.value = ''
  try {
    if (isEditing.value) {
      const payload = {
        full_name: userForm.full_name,
        email: userForm.email,
        role: userForm.role,
        is_active: userForm.is_active,
        phone: userForm.phone,
        institution: userForm.institution,
        department: userForm.department,
        nim_nip: userForm.nim_nip,
        address: userForm.address
      }
      if (userForm.password) {
        payload.password = userForm.password
      }
      await authStore.updateUser(editingUserId.value, payload)
      feedbackMsg.value = `Akun ${userForm.username} berhasil diperbarui.`
    } else {
      await authStore.createUser({
        full_name: userForm.full_name,
        username: userForm.username,
        email: userForm.email,
        role: userForm.role,
        password: userForm.password,
        phone: userForm.phone,
        institution: userForm.institution,
        department: userForm.department,
        nim_nip: userForm.nim_nip,
        address: userForm.address
      })
      feedbackMsg.value = `Pengguna baru ${userForm.username} berhasil dibuat.`
    }
    showUserFormModal.value = false
    await loadUsers()
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Gagal memproses data pengguna.'
  }
}

const handleDeleteUser = async (user) => {
  if (confirm(`Yakin ingin menghapus pengguna "${user.full_name}" (@${user.username})?`)) {
    try {
      await authStore.deleteUser(user.id)
      feedbackMsg.value = `User ${user.username} berhasil dihapus.`
      await loadUsers()
    } catch (err) {
      errorMsg.value = err.response?.data?.detail || 'Gagal menghapus user.'
    }
  }
}

watch(() => props.isOpen, async (val) => {
  if (val) {
    try {
      const { data } = await api.getMe()
      authStore.user = { ...authStore.user, ...data }
      localStorage.setItem('geoai_user', JSON.stringify(authStore.user))
    } catch (e) {
      console.warn('Could not refresh me:', e)
    }
    loadSelfProfile()
    if (authStore.isAdmin && activeTab.value === 'crud_users') {
      loadUsers()
    }
  }
})

onMounted(async () => {
  loadSelfProfile()
  if (authStore.isAdmin) {
    loadUsers()
  }
})
</script>


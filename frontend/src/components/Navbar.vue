<template>
  <header class="bg-white border-b border-slate-200 text-slate-800 px-4 lg:px-8 py-2.5 flex items-center justify-between sticky top-0 z-50 shadow-xs">
    <!-- Brand / Logo (STEVI Task Manager) -->
    <div class="flex items-center gap-3">
      <router-link to="/" class="flex items-center gap-3 group" title="A geospatial analytical platform for ecosystem services assessment, visualization, and spatial decision support.">
        <img
          src="https://koboegis.app/klh-logo.png?v=2026|g"
          alt="GEOSTEVIA Logo"
          class="h-10 w-auto object-contain transition-transform group-hover:scale-105"
          @error="handleLogoError"
        />
        <div>
          <div class="font-black text-xl md:text-2xl tracking-tight leading-tight text-slate-900 font-heading">
            GEOSTEVIA
          </div>
          <div class="text-xs text-slate-500 font-medium leading-none mt-0.5">
            Geospatial Ecosystem Services Analytics
          </div>
        </div>
      </router-link>
    </div>

    <!-- Center Navigation Links (when authenticated) -->
    <nav v-if="authStore.isAuthenticated" class="hidden md:flex items-center gap-1.5 bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200 text-sm font-bold">
      <router-link
        to="/projects"
        class="px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 text-slate-600 hover:text-slate-900"
        active-class="bg-white text-slate-900 shadow-2xs"
      >
        <Compass :size="15" />
        <span>Projects</span>
      </router-link>

      <router-link
        to="/dashboard"
        class="px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 text-slate-600 hover:text-slate-900"
        active-class="bg-white text-slate-900 shadow-2xs"
      >
        <LayoutDashboard :size="15" />
        <span>Dashboard</span>
      </router-link>

      <router-link
        to="/tasking"
        class="px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 text-slate-600 hover:text-slate-900"
        active-class="bg-white text-slate-900 shadow-2xs"
      >
        <Grid :size="15" />
        <span>Tasking</span>
      </router-link>

      <router-link
        to="/map"
        class="px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 text-slate-600 hover:text-slate-900"
        active-class="bg-white text-slate-900 shadow-2xs"
      >
        <Shapes :size="15" />
        <span>Studio Digitasi</span>
      </router-link>

      <router-link
        v-if="authStore.isReviewer"
        to="/qc"
        class="px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 text-amber-800 hover:text-amber-900"
        active-class="bg-amber-100 text-amber-900 shadow-2xs"
      >
        <CheckSquare :size="15" class="text-amber-600" />
        <span>QC Review</span>
      </router-link>

      <router-link
        v-if="authStore.isAdmin"
        to="/admin"
        class="px-3.5 py-2 rounded-xl transition-all flex items-center gap-2 text-purple-800 hover:text-purple-900"
        active-class="bg-purple-100 text-purple-900 shadow-2xs"
      >
        <Shield :size="15" class="text-purple-600" />
        <span>Panel Admin</span>
      </router-link>
    </nav>

    <!-- User Profile Area -->
    <div class="flex items-center gap-2 sm:gap-3">
      <!-- Current User Profile Badge (Clickable to open User Profile Modal) -->
      <div v-if="authStore.isAuthenticated" class="flex items-center gap-2">
        <button
          @click="handleProfileClick"
          class="flex items-center gap-3 p-1.5 pr-3.5 rounded-2xl hover:bg-slate-100/80 border border-slate-200/80 bg-white transition-all text-left group cursor-pointer shadow-2xs"
          :title="authStore.isAdmin ? 'Buka Panel Admin Dashboard' : 'Buka Manajemen Profil Pengguna'"
        >
          <div
            class="w-9 h-9 rounded-xl flex items-center justify-center font-black text-sm shadow-xs border group-hover:scale-105 transition-transform"
            :class="authStore.isAdmin ? 'bg-amber-100 text-amber-800 border-amber-300' : (authStore.isDosen ? 'bg-indigo-100 text-indigo-800 border-indigo-300' : 'bg-rose-100 text-rose-700 border-rose-300')"
          >
            {{ authStore.user?.full_name?.charAt(0) || 'U' }}
          </div>
          <div>
            <div class="text-sm font-extrabold text-slate-800 leading-none truncate max-w-[150px] group-hover:text-rose-600 transition-colors">
              {{ authStore.userName }}
            </div>
            <div class="text-xs font-semibold mt-1 flex items-center gap-1.5">
              <span v-if="authStore.isAdmin" class="text-amber-700 font-bold">Administrator</span>
              <span v-else-if="authStore.isDosen" class="text-indigo-700 font-bold">Supervisi</span>
              <span v-else class="text-rose-600 font-bold">Kontributor</span>
              <Settings :size="12" class="text-slate-400 group-hover:text-slate-700" />
            </div>
          </div>
        </button>

        <button
          @click="authStore.logout()"
          title="Keluar (Logout)"
          class="p-2.5 hover:bg-rose-50 hover:text-rose-600 text-slate-400 border border-slate-200/70 rounded-xl transition-colors cursor-pointer bg-white"
        >
          <LogOut :size="16" />
        </button>
      </div>

      <!-- If Not Logged In -->
      <div v-else class="flex items-center gap-2">
        <router-link
          to="/projects"
          class="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 text-slate-700 hover:text-slate-900 hover:bg-slate-50 text-xs font-bold transition-all"
        >
          <Compass :size="14" />
          <span>Jelajahi Proyek</span>
        </router-link>
        <router-link
          to="/login"
          class="bg-rose-600 hover:bg-rose-700 text-white text-sm font-extrabold px-5 py-2.5 rounded-xl transition-all shadow-md shadow-rose-600/20 flex items-center gap-2 cursor-pointer"
        >
          <LogIn :size="16" />
          <span>Masuk</span>
        </router-link>
      </div>
    </div>

    <!-- User Profile Modal Component -->
    <UserProfileModal
      :isOpen="showProfileModal"
      @close="showProfileModal = false"
    />
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  Compass,
  Settings,
  LogOut,
  LogIn,
  LayoutDashboard,
  Grid,
  Shapes,
  CheckSquare,
  Shield
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import { useRouter } from 'vue-router'
import UserProfileModal from './UserProfileModal.vue'

const authStore = useAuthStore()
const tasksStore = useTasksStore()
const router = useRouter()
const showProfileModal = ref(false)

const handleProfileClick = () => {
  if (authStore.isAdmin) {
    router.push('/admin')
  } else {
    showProfileModal.value = true
  }
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    tasksStore.fetchTasks()
  }
})

const quickLogin = async (username, password) => {
  const success = await authStore.login(username, password)
  if (success) {
    window.location.reload()
  }
}

const handleLogoError = (e) => {
  e.target.style.display = 'none'
}
</script>



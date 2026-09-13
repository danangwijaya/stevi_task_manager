<template>
  <header class="bg-white border-b border-slate-200 text-slate-800 px-4 lg:px-8 py-2.5 flex items-center justify-between sticky top-0 z-50 shadow-xs">
    <!-- Brand / Logo (STEVI Task Manager) -->
    <div class="flex items-center gap-3">
      <router-link to="/" class="flex items-center gap-3 group">
        <img
          src="https://koboegis.app/klh-logo.png?v=2026|g"
          alt="STEVI Logo"
          class="h-10 w-auto object-contain transition-transform group-hover:scale-105"
          @error="handleLogoError"
        />
        <div>
          <div class="font-black text-xl md:text-2xl tracking-tight leading-tight text-slate-900 font-heading">
            STEVI Task Manager
          </div>
          <div class="text-xs text-slate-500 font-medium leading-none mt-0.5">
            Platform Kolaborasi Pembuatan Training Sample
          </div>
        </div>
      </router-link>
    </div>



    <!-- User Profile Area -->
    <div class="flex items-center gap-2 sm:gap-3">
      <!-- Current User Profile Badge (Clickable to open User Profile Modal) -->
      <div v-if="authStore.isAuthenticated" class="flex items-center gap-2">
        <button
          @click="showProfileModal = true"
          class="flex items-center gap-2.5 p-1.5 pr-3 rounded-2xl hover:bg-slate-100/80 border border-slate-200/80 bg-white transition-all text-left group cursor-pointer shadow-2xs"
          title="Buka Manajemen Profil Pengguna"
        >
          <div
            class="w-8 h-8 rounded-xl flex items-center justify-center font-black text-xs shadow-xs border group-hover:scale-105 transition-transform"
            :class="authStore.isAdmin ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-rose-100 text-rose-700 border-rose-300'"
          >
            {{ authStore.user?.full_name?.charAt(0) || 'U' }}
          </div>
          <div>
            <div class="text-xs font-bold text-slate-800 leading-none truncate max-w-[140px] group-hover:text-rose-600 transition-colors">
              {{ authStore.userName }}
            </div>
            <div class="text-[10px] font-semibold mt-0.5 flex items-center gap-1">
              <span v-if="authStore.isAdmin" class="text-amber-700 font-bold">Administrator</span>
              <span v-else class="text-rose-600 font-bold">Kontributor</span>
              <Settings :size="10" class="text-slate-400 group-hover:text-slate-700" />
            </div>
          </div>
        </button>

        <button
          @click="authStore.logout()"
          title="Keluar (Logout)"
          class="p-2 hover:bg-rose-50 hover:text-rose-600 text-slate-400 border border-slate-200/70 rounded-xl transition-colors cursor-pointer bg-white"
        >
          <LogOut :size="15" />
        </button>
      </div>

      <!-- If Not Logged In -->
      <div v-else class="flex items-center gap-2">
        <router-link
          to="/login"
          class="bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-md shadow-rose-600/20 flex items-center gap-1.5 cursor-pointer"
        >
          <LogIn :size="14" />
          <span>Masuk / Demo</span>
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
  Settings,
  LogOut,
  LogIn
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useTasksStore } from '../stores/tasks'
import { useRouter } from 'vue-router'
import UserProfileModal from './UserProfileModal.vue'

const authStore = useAuthStore()
const tasksStore = useTasksStore()
const router = useRouter()
const showProfileModal = ref(false)

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



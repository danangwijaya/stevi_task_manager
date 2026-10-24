<template>
  <div class="h-screen w-screen bg-slate-50 text-slate-800 flex flex-col flex-nowrap selection:bg-rose-500 selection:text-white font-sans antialiased overflow-hidden">
    <div v-if="newVersion" class="shrink-0 bg-amber-400 text-slate-900 text-sm px-4 py-2 flex items-center justify-center gap-3 flex-wrap">
      <span>Versi baru GEOSTEVIA tersedia. Simpan pekerjaan Anda, lalu muat ulang agar memakai perbaikan terbaru.</span>
      <button class="px-3 py-1 rounded-md bg-slate-900 text-white font-medium" @click="reloadNow">Muat ulang</button>
    </div>
    <Navbar v-if="$route.path !== '/login'" class="shrink-0" />
    <main class="flex-1 flex flex-col flex-nowrap min-h-0 overflow-y-auto relative">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import Navbar from './components/Navbar.vue'
import { startVersionCheck } from './services/versionCheck'

const authStore = useAuthStore()
const themeStore = useThemeStore()

// A tab left open keeps its old code: tell the user, and the router reloads the page on the next navigation
const newVersion = ref(false)
const reloadNow = () => window.location.reload()
let stopVersionCheck = () => {}

onBeforeUnmount(() => stopVersionCheck())

onMounted(async () => {
  stopVersionCheck = startVersionCheck(__APP_BUILD__, () => { newVersion.value = true })
  themeStore.loadTheme()
  if (authStore.token) {
    await authStore.fetchCurrentUser()
  }
})
</script>

<style>
/* Global light theme scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: #f1f5f9;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 9999px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>

<template>
  <div class="h-screen w-screen bg-slate-50 text-slate-800 flex flex-col flex-nowrap selection:bg-rose-500 selection:text-white font-sans antialiased overflow-hidden">
    <Navbar v-if="$route.path !== '/login'" class="shrink-0" />
    <main class="flex-1 flex flex-col flex-nowrap min-h-0 overflow-y-auto relative">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import Navbar from './components/Navbar.vue'

const authStore = useAuthStore()

onMounted(async () => {
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

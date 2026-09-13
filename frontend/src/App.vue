<template>
  <div class="min-h-screen bg-slate-50 text-slate-800 flex flex-col selection:bg-rose-500 selection:text-white font-sans antialiased">
    <Navbar v-if="$route.path !== '/login'" />
    <main class="flex-1">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth'
import Navbar from './components/Navbar.vue'

const authStore = useAuthStore()
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

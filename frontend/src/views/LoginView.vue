<template>
  <div class="min-h-screen bg-slate-100 flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans">
    <!-- Ambient subtle light gradients -->
    <div class="absolute -top-40 -left-40 w-96 h-96 bg-rose-200/30 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-amber-200/30 rounded-full blur-3xl pointer-events-none"></div>

    <div class="max-w-md w-full bg-white border border-slate-200 rounded-3xl p-8 shadow-xl relative z-10">
      
      <!-- Brand & Header -->
      <div class="text-center mb-6">
        <router-link to="/" class="inline-flex items-center justify-center mb-3 group">
          <img
            src="https://koboegis.app/klh-logo.png?v=2026|g"
            alt="STEVI Logo"
            class="h-16 w-auto object-contain group-hover:scale-105 transition-transform"
            @error="handleLogoError"
          />
        </router-link>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight font-heading">STEVI Task Manager</h1>
        <p class="text-xs text-slate-500 mt-1 leading-relaxed">
          Platform Kolaborasi Pembuatan Training Sample
        </p>
      </div>

      <!-- Error alert -->
      <div v-if="authStore.error" class="mb-5 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2 shadow-2xs">
        <AlertTriangle :size="16" class="text-rose-600 shrink-0" />
        <span>{{ authStore.error }}</span>
      </div>

      <!-- LOGIN FORM -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Username / Email</label>
          <input
            v-model="loginForm.username"
            type="text"
            required
            autocomplete="username"
            placeholder="Masukkan username atau email Anda"
            class="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-500 focus:bg-white focus:ring-1 focus:ring-rose-500 shadow-2xs"
          />
        </div>

        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">Password</label>
          </div>
          <input
            v-model="loginForm.password"
            type="password"
            required
            autocomplete="current-password"
            placeholder="••••••••"
            class="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-500 focus:bg-white focus:ring-1 focus:ring-rose-500 shadow-2xs"
          />
        </div>

        <button
          type="submit"
          :disabled="authStore.loading"
          class="w-full bg-[#d73f3f] hover:bg-[#c23434] text-white font-bold py-2.5 px-4 rounded-xl transition-all shadow-md shadow-rose-500/20 text-sm flex items-center justify-center gap-2 uppercase tracking-wider cursor-pointer disabled:opacity-50 mt-2"
        >
          <RotateCw v-if="authStore.loading" :size="16" class="animate-spin text-white" />
          <LogIn v-else :size="16" />
          <span>Masuk ke Akun</span>
        </button>
      </form>

      <!-- Information footer note -->
      <div class="mt-8 pt-5 border-t border-slate-100 text-center">
        <p class="text-xs text-slate-500 leading-relaxed">
          Belum memiliki akun kontributor / mapper? <br>
          <span class="text-slate-700 font-semibold">Silakan hubungi Administrator Proyek untuk pembuatan akun.</span>
        </p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlertTriangle,
  RotateCw,
  LogIn
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const loginForm = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  const success = await authStore.login(loginForm.username, loginForm.password)
  if (success) {
    router.push('/')
  }
}

const handleLogoError = (e) => {
  e.target.style.display = 'none'
}
</script>


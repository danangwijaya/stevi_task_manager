<template>
  <div class="flex-1 overflow-y-auto bg-slate-50/60 p-4 md:p-8">
    <div class="max-w-4xl mx-auto space-y-6">
      <!-- Breadcrumb & Header -->
      <div class="space-y-2">
        <div class="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <router-link to="/dashboard" class="hover:text-slate-800 transition-colors">Dashboard</router-link>
          <span>/</span>
          <span class="text-slate-400">Pengaturan</span>
          <span>/</span>
          <span class="text-rose-600 font-bold">Desain & Tampilan</span>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
              <i class="fa-solid fa-palette text-rose-600 text-xl"></i>
              <span>Pengaturan Desain & Tampilan UI</span>
            </h1>
            <p class="text-xs text-slate-500 mt-1">
              Sesuaikan preferensi visual platform GEOSTEVIA sesuai kenyamanan kerja dan kebutuhan perangkat Anda.
            </p>
          </div>

          <div class="flex items-center gap-2">
            <router-link
              to="/map"
              class="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-2"
            >
              <i class="fa-solid fa-map"></i>
              <span>Kembali ke Studio Digitasi</span>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Main Settings Card -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-xs p-6">
        <DesignSettingsPanel />
      </div>

      <!-- Info / Best Practices Box -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-2">
          <div class="flex items-center gap-2 text-xs font-bold text-slate-800">
            <i class="fa-solid fa-lightbulb text-amber-500"></i>
            <span>Tips Kenyamanan Digitasi (Ergonomi UI)</span>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed">
            Jika Anda bekerja dengan layar resolusi tinggi (FHD / 2K) atau laptop 13-14 inci, gunakan opsi <b>Kerapatan Ringkas (Compact GIS)</b> dan font <b>Plus Jakarta Sans</b> agar bidang pandang citra satelit dan poligon tetap maksimal.
          </p>
        </div>

        <div class="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-2">
          <div class="flex items-center gap-2 text-xs font-bold text-slate-800">
            <i class="fa-solid fa-shield-halved text-emerald-600"></i>
            <span>Penyimpanan Lokal & Privasi</span>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed">
            Seluruh preferensi visual tersimpan secara lokal di browser Anda (Local Storage) dan tidak akan mengubah tampilan annotator atau reviewer lainnya di proyek yang sama.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import DesignSettingsPanel from '../components/DesignSettingsPanel.vue'
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-xs animate-in fade-in duration-200"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[90vh] flex flex-col flex-nowrap overflow-hidden animate-in zoom-in-95 duration-150"
    >
      <!-- Modal Header -->
      <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 border border-rose-200 flex items-center justify-center">
            <i class="fa-solid fa-swatchbook text-sm"></i>
          </div>
          <div>
            <h2 class="text-sm font-bold text-slate-900 leading-tight">Pengaturan Desain & Tampilan UI</h2>
            <p class="text-[11px] text-slate-500">Sesuaikan tipografi, ukuran teks, kerapatan tata letak, dan mode GIS.</p>
          </div>
        </div>

        <button
          type="button"
          @click="$emit('close')"
          class="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200/70 rounded-lg transition-colors cursor-pointer"
          title="Tutup"
        >
          <i class="fa-solid fa-xmark text-sm"></i>
        </button>
      </div>

      <!-- Modal Body (Scrollable) -->
      <div class="p-5 overflow-y-auto flex-1">
        <DesignSettingsPanel />
      </div>

      <!-- Modal Footer -->
      <div class="px-5 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
        <router-link
          to="/settings/design"
          @click="$emit('close')"
          class="text-xs font-semibold text-slate-600 hover:text-rose-600 flex items-center gap-1.5 cursor-pointer"
        >
          <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          <span>Buka di Halaman Penuh (/settings/design)</span>
        </router-link>

        <button
          type="button"
          @click="$emit('close')"
          class="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer shadow-2xs"
        >
          Selesai
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import DesignSettingsPanel from './DesignSettingsPanel.vue'

defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])
</script>

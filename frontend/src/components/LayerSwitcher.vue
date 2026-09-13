<template>
  <div class="bg-white border border-slate-200 rounded-2xl p-3 shadow-sm flex flex-col gap-3 min-w-[260px]">
    <div class="flex items-center justify-between pb-2 border-b border-slate-100">
      <div class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
        <Satellite :size="14" class="text-slate-400" />
        <span>Layer Sentinel-2 (GEE)</span>
      </div>
      <!-- Year Badge -->
      <div class="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
        <button
          @click="$emit('update:year', 2017)"
          class="px-2 py-0.5 text-[10px] font-bold rounded-md transition-colors cursor-pointer"
          :class="selectedYear === 2017 ? 'bg-rose-600 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'"
        >
          2017
        </button>
        <button
          @click="$emit('update:year', 2021)"
          class="px-2 py-0.5 text-[10px] font-bold rounded-md transition-colors cursor-pointer"
          :class="selectedYear === 2021 ? 'bg-rose-600 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'"
        >
          2021
        </button>
        <button
          @click="$emit('update:year', 2025)"
          class="px-2 py-0.5 text-[10px] font-bold rounded-md transition-colors cursor-pointer"
          :class="selectedYear === 2025 ? 'bg-rose-600 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'"
        >
          2025
        </button>
      </div>
    </div>

    <!-- Layer Options -->
    <div class="flex flex-col gap-1.5">
      <button
        v-for="layer in layers"
        :key="layer.id"
        @click="$emit('update:layer', layer.id)"
        class="w-full text-left p-2.5 rounded-xl transition-all border flex items-center justify-between group cursor-pointer"
        :class="selectedLayer === layer.id
          ? 'bg-rose-50/90 border-rose-400 ring-1 ring-rose-400/40 shadow-xs'
          : 'bg-slate-50 border-slate-200 hover:bg-white hover:border-slate-300'"
      >
        <div class="flex items-center gap-2.5">
          <component :is="layer.icon" :size="15" :class="layer.colorClass" class="shrink-0" />
          <div>
            <div class="text-xs font-bold text-slate-800 group-hover:text-slate-900">{{ layer.name }}</div>
            <div class="text-[10px] text-slate-500">{{ layer.desc }}</div>
          </div>
        </div>
        <div
          class="w-2.5 h-2.5 rounded-full border shrink-0"
          :class="selectedLayer === layer.id ? 'bg-rose-500 border-rose-600' : 'border-slate-300 bg-white'"
        ></div>
      </button>
    </div>

    <!-- Polygon Opacity Slider -->
    <div class="border-t border-slate-100 pt-2 flex flex-col gap-1.5">
      <div class="flex justify-between text-[11px] text-slate-500 font-bold">
        <span>Transparansi Anotasi</span>
        <span class="font-mono text-rose-600">{{ Math.round(opacity * 100) }}%</span>
      </div>
      <input
        type="range"
        min="0.1"
        max="0.9"
        step="0.05"
        :value="opacity"
        @input="$emit('update:opacity', parseFloat($event.target.value))"
        class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-600"
      />
    </div>
  </div>
</template>

<script setup>
import {
  Satellite,
  Flame,
  Wheat,
  TrendingUp,
  Map
} from 'lucide-vue-next'

const props = defineProps({
  selectedLayer: {
    type: String,
    default: 'true_color'
  },
  selectedYear: {
    type: Number,
    default: 2025
  },
  opacity: {
    type: Number,
    default: 0.55
  }
})

defineEmits(['update:layer', 'update:year', 'update:opacity'])

const layers = [
  { id: 'true_color', name: 'True Color (RGB 4-3-2)', desc: 'Tampilan warna asli alami', icon: Satellite, colorClass: 'text-slate-600' },
  { id: 'false_color_nir', name: 'False Color NIR (8-4-3)', desc: 'Vegetasi tampak merah kontras', icon: Flame, colorClass: 'text-rose-600' },
  { id: 'swir', name: 'Agriculture SWIR (11-8-2)', desc: 'Sawah, sawit & tambang jelas', icon: Wheat, colorClass: 'text-amber-600' },
  { id: 'ndvi', name: 'NDVI Indeks Kerapatan', desc: 'Gradien hijau kerapatan kanopi', icon: TrendingUp, colorClass: 'text-emerald-600' },
  { id: 'osm', name: 'OpenStreetMap Base', desc: 'Peta jalan dan batas administrasi', icon: Map, colorClass: 'text-slate-500' }
]
</script>


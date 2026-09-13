<template>
  <div class="bg-white border border-slate-200 rounded-2xl p-3 shadow-sm flex flex-col gap-2 max-h-[calc(100vh-140px)] overflow-y-auto">
    <div class="flex items-center justify-between pb-2 border-b border-slate-100">
      <div class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
        <Palette :size="14" class="text-slate-400" />
        <span>12 Kelas Tutupan Lahan</span>
      </div>
      <span class="text-[10px] bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full font-mono font-bold">U-Net</span>
    </div>

    <div class="flex flex-col gap-1.5">
      <button
        v-for="cls in annotationsStore.classes"
        :key="cls.id"
        @click="selectClass(cls)"
        class="w-full text-left p-2 rounded-xl transition-all border flex items-center justify-between group cursor-pointer"
        :class="annotationsStore.selectedClass?.id === cls.id 
          ? 'bg-rose-50/90 border-rose-400 shadow-xs ring-1 ring-rose-400/50' 
          : 'bg-slate-50 border-slate-200 hover:bg-white hover:border-slate-300'"
      >
        <div class="flex items-center gap-2.5 min-w-0">
          <!-- Color indicator -->
          <div
            class="w-4 h-4 rounded-md shrink-0 shadow-2xs border border-slate-300"
            :style="{ backgroundColor: cls.color }"
          ></div>
          
          <!-- Class Name -->
          <div class="truncate">
            <div class="text-xs font-bold text-slate-800 group-hover:text-slate-900 leading-tight truncate">
              {{ cls.name }}
            </div>
            <div class="text-[10px] text-slate-500 truncate">{{ cls.description }}</div>
          </div>
        </div>

        <!-- Class ID badge & count -->
        <div class="flex items-center gap-1.5 shrink-0 pl-2">
          <span 
            v-if="classCounts[cls.id]"
            class="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-rose-100 text-rose-700 font-bold border border-rose-200"
            title="Jumlah poligon kelas ini pada grid aktif"
          >
            {{ classCounts[cls.id] }}
          </span>
          <span class="text-[10px] font-mono bg-white text-slate-400 px-1.5 py-0.5 rounded border border-slate-200">
            #{{ cls.id }}
          </span>
        </div>
      </button>
    </div>

    <div class="text-[10px] text-slate-500 border-t border-slate-100 pt-2 px-1 text-center font-medium flex items-center justify-center gap-1.5">
      <Lightbulb :size="12" class="text-amber-500" />
      <span>Klik kelas di atas sebelum menggambar poligon dengan Geoman</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Palette, Lightbulb } from 'lucide-vue-next'
import { useAnnotationsStore } from '../stores/annotations'


const annotationsStore = useAnnotationsStore()

const props = defineProps({
  features: {
    type: Array,
    default: () => []
  }
})

const classCounts = computed(() => {
  const counts = {}
  props.features.forEach(f => {
    const cid = f.properties?.class_id
    if (cid) {
      counts[cid] = (counts[cid] || 0) + 1
    }
  })
  return counts
})

const selectClass = (cls) => {
  annotationsStore.setSelectedClass(cls)
}
</script>

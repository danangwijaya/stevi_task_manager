<template>
  <div class="space-y-6 text-slate-800">
    <!-- Section 1: Font Family / Tipografi -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
            <i class="fa-solid fa-font text-rose-600"></i>
            <span>Tipografi & Font Antarmuka</span>
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">Pilih font utama untuk teks antarmuka, tombol, tabel, dan form input.</p>
        </div>
        <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
          {{ themeStore.activeFont.name }}
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div
          v-for="font in themeStore.fontOptions"
          :key="font.id"
          @click="selectFont(font.id)"
          class="relative p-3.5 rounded-lg border-2 transition-all cursor-pointer bg-white hover:border-slate-300 shadow-2xs select-none"
          :class="themeStore.fontFamily === font.id ? 'border-rose-600 ring-2 ring-rose-100 bg-rose-50/20' : 'border-slate-200'"
        >
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-extrabold text-slate-900">{{ font.name }}</span>
            <span
              class="text-[9px] font-bold px-1.5 py-0.5 rounded border"
              :class="themeStore.fontFamily === font.id ? 'bg-rose-100 text-rose-700 border-rose-200' : 'bg-slate-100 text-slate-600 border-slate-200'"
            >
              {{ font.badge }}
            </span>
          </div>

          <div class="text-[10px] text-slate-500 font-medium mb-2.5">
            {{ font.category }}
          </div>

          <!-- Specimen Preview -->
          <div
            class="p-2 rounded bg-slate-50 border border-slate-200/80 mb-2 text-xs leading-snug"
            :style="{ fontFamily: font.fontFamily, letterSpacing: font.tracking }"
          >
            <div class="font-bold text-slate-900">GEOSTEVIA Platform</div>
            <div class="text-[11px] text-slate-600 mt-0.5">Analisis Ekosistem Spasial (1:25.000)</div>
          </div>

          <p class="text-[11px] text-slate-600 leading-tight">
            {{ font.description }}
          </p>

          <div
            v-if="themeStore.fontFamily === font.id"
            class="absolute top-2 right-2 w-2 h-2 rounded-full bg-rose-600"
          ></div>
        </div>
      </div>
    </div>

    <!-- Section 2: UI Density & Base Scale -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-200">
      <!-- UI Density -->
      <div class="space-y-2.5">
        <div>
          <h4 class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
            <i class="fa-solid fa-table-cells-large text-slate-600"></i>
            <span>Kerapatan Tata Letak (Density)</span>
          </h4>
          <p class="text-[11px] text-slate-500 mt-0.5">Mengatur kerapatan padding tombol dan panel kerja.</p>
        </div>

        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="d in themeStore.densityOptions"
            :key="d.id"
            type="button"
            @click="selectDensity(d.id)"
            class="p-2.5 rounded-lg border text-left transition-all cursor-pointer flex flex-col justify-between"
            :class="themeStore.density === d.id ? 'border-rose-600 bg-rose-50/30 text-rose-900 font-bold shadow-2xs' : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'"
          >
            <span class="text-xs font-bold">{{ d.name }}</span>
            <span class="text-[10px] text-slate-500 font-normal mt-1 leading-tight">{{ d.description }}</span>
          </button>
        </div>
      </div>

      <!-- Base Font Scale -->
      <div class="space-y-2.5">
        <div>
          <h4 class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
            <i class="fa-solid fa-text-height text-slate-600"></i>
            <span>Skala Ukuran Teks (Font Scale)</span>
          </h4>
          <p class="text-[11px] text-slate-500 mt-0.5">Menyesuaikan ukuran teks dasar seluruh sistem.</p>
        </div>

        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="fs in themeStore.fontSizeOptions"
            :key="fs.id"
            type="button"
            @click="selectFontSize(fs.id)"
            class="p-2 rounded-lg border text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-1"
            :class="themeStore.fontSize === fs.id ? 'border-rose-600 bg-rose-50/30 text-rose-900 font-bold shadow-2xs' : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'"
          >
            <span class="text-xs font-bold">{{ fs.name }}</span>
            <span class="text-[10px] font-mono text-slate-500">{{ fs.size }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Section 3: Border Radius & GIS Workspace Options -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-200">
      <!-- Border Radius Style -->
      <div class="space-y-2.5">
        <div>
          <h4 class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
            <i class="fa-solid fa-vector-square text-slate-600"></i>
            <span>Gaya Sudut Elemen (Corner Radius)</span>
          </h4>
          <p class="text-[11px] text-slate-500 mt-0.5">Bentuk lengkungan sudut pada panel, tombol, dan kotak modal.</p>
        </div>

        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="rad in themeStore.radiusOptions"
            :key="rad.id"
            type="button"
            @click="selectRadius(rad.id)"
            class="p-2 rounded-lg border text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-1"
            :class="themeStore.borderRadius === rad.id ? 'border-rose-600 bg-rose-50/30 text-rose-900 font-bold shadow-2xs' : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'"
          >
            <span class="text-xs font-bold">{{ rad.name }}</span>
            <span class="text-[10px] text-slate-500 font-normal leading-tight">{{ rad.description }}</span>
          </button>
        </div>
      </div>

      <!-- GIS Workspace Preferences -->
      <div class="space-y-2.5">
        <div>
          <h4 class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
            <i class="fa-solid fa-map-location-dot text-slate-600"></i>
            <span>Preferensi Workspace Studio Digitasi</span>
          </h4>
          <p class="text-[11px] text-slate-500 mt-0.5">Pengaturan tampilan elemen pendukung di canvas peta.</p>
        </div>

        <div class="space-y-2">
          <label class="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-white cursor-pointer hover:bg-slate-50">
            <div class="pr-2">
              <div class="text-xs font-bold text-slate-800">Status Bar Bawah (Docked GIS)</div>
              <div class="text-[10px] text-slate-500">Tampilkan panel Zoom, Skala, Koordinat WGS84, dan Total Luas.</div>
            </div>
            <input
              type="checkbox"
              v-model="themeStore.showStatusBar"
              @change="themeStore.applyTheme()"
              class="w-4 h-4 rounded text-rose-600 focus:ring-rose-500 border-slate-300"
            />
          </label>

          <label class="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-white cursor-pointer hover:bg-slate-50">
            <div class="pr-2">
              <div class="text-xs font-bold text-slate-800">Badge Pintasan Keyboard [V, C, X, Del]</div>
              <div class="text-[10px] text-slate-500">Tampilkan indikator huruf shortcut pada bilah alat digitasi kiri.</div>
            </div>
            <input
              type="checkbox"
              v-model="themeStore.showShortcuts"
              @change="themeStore.applyTheme()"
              class="w-4 h-4 rounded text-rose-600 focus:ring-rose-500 border-slate-300"
            />
          </label>
        </div>
      </div>
    </div>

    <!-- Section 4: Live Preview Sandbox -->
    <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/70 space-y-2.5">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
          <i class="fa-solid fa-eye text-slate-500"></i>
          <span>Pratinjau Langsung (Live Preview)</span>
        </span>
        <span class="text-[10px] font-mono text-slate-500">Perubahan aktif seketika tanpa refresh</span>
      </div>

      <div class="p-3.5 bg-white rounded-lg border border-slate-200 shadow-2xs space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded bg-rose-600 text-white flex items-center justify-center font-black text-xs">
              G
            </div>
            <div>
              <div class="text-xs font-bold text-slate-900 leading-tight">GEOSTEVIA Task Manager</div>
              <div class="text-[10px] text-slate-500">SB_GRID_049_2022 • Hutan Lahan Kering Sekunder</div>
            </div>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            DISETUJUI (VALID)
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-bold shadow-2xs transition-colors">
            Simpan Poligon
          </button>
          <button class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-bold transition-colors">
            Gabung (Merge)
          </button>
          <div class="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-slate-100/90 border border-slate-200 text-xs font-mono text-slate-700">
            <i class="fa-solid fa-location-crosshairs text-slate-400 text-[10px]"></i>
            <span>-7.142857, 110.428571</span>
            <span class="text-slate-400">|</span>
            <span class="text-rose-600 font-bold">184.25 ha</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions Footer -->
    <div class="flex items-center justify-between pt-2 border-t border-slate-200">
      <button
        type="button"
        @click="resetToDefaults"
        class="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
      >
        <i class="fa-solid fa-rotate-left text-[11px]"></i>
        <span>Reset ke Pengaturan Standar</span>
      </button>

      <div class="text-[11px] text-slate-500 italic">
        Pengaturan tersimpan otomatis di perangkat ini
      </div>
    </div>
  </div>
</template>

<script setup>
import { useThemeStore } from '../stores/theme'

const themeStore = useThemeStore()

const selectFont = (fontId) => {
  themeStore.fontFamily = fontId
  themeStore.applyTheme()
}

const selectDensity = (densityId) => {
  themeStore.density = densityId
  themeStore.applyTheme()
}

const selectFontSize = (sizeId) => {
  themeStore.fontSize = sizeId
  themeStore.applyTheme()
}

const selectRadius = (radiusId) => {
  themeStore.borderRadius = radiusId
  themeStore.applyTheme()
}

const resetToDefaults = () => {
  themeStore.resetDefaults()
}
</script>

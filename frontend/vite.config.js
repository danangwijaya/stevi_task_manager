import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'

// One id per build: baked into the bundle and written to dist/version.json so open tabs can tell they are out of date
const BUILD_ID = new Date().toISOString().replace(/\D/g, '').slice(0, 14)

const emitVersionFile = {
  name: 'emit-version-file',
  generateBundle() {
    this.emitFile({ type: 'asset', fileName: 'version.json', source: JSON.stringify({ build: BUILD_ID }) })
  }
}

export default defineConfig({
  define: { __APP_BUILD__: JSON.stringify(BUILD_ID) },
  plugins: [
    emitVersionFile,
    vue({
      template: { transformAssetUrls }
    }),
    quasar()
  ],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})

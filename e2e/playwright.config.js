// Browser tests of the real map: the Vite dev server of ../frontend against a local backend on a throwaway SQLite database
// (the seed creates the admin account and sample grids). `npm test` starts both; servers that already run are reused.
// BACKEND_PYTHON overrides the interpreter that runs uvicorn (default: the backend virtualenv).
import { defineConfig } from '@playwright/test'

const DB = '/tmp/geostevia_e2e.db'
const PY = process.env.BACKEND_PYTHON || '../backend/venv/bin/python'

export default defineConfig({
  testDir: './tests',
  timeout: 180000,
  workers: 1,                               // the tests share one database
  reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:5173', headless: true, viewport: { width: 1440, height: 900 }, screenshot: 'only-on-failure' },
  webServer: [
    {
      command: `rm -f ${DB} && ${PY} -m uvicorn app.main:app --port 8000 --log-level warning`,
      cwd: '../backend',
      env: { DATABASE_URL: `sqlite:///${DB}`, SECRET_KEY: 'e2e-local-only', RASTER_BASE_DIR: '/tmp/geostevia_e2e_raster' },
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: true,
      timeout: 120000,
    },
    { command: 'npm run dev -- --port 5173 --strictPort', cwd: '../frontend', url: 'http://127.0.0.1:5173', reuseExistingServer: true, timeout: 120000 },
  ],
})

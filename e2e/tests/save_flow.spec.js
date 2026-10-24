// The bug of October 2026: a polygon made by a cut carried `_uiId` beside `properties`, the server dropped it, the client never
// learned the row ids and every autosave deleted and re-inserted the polygons of the previous save. This drives the real map:
// cut twice, let the autosave run twice (full-save path), and check that the second save already knows the pieces of the first cut.
import { test, expect, request as pwRequest } from '@playwright/test'

const API = 'http://127.0.0.1:8000/api/v1'
const GRID_ID = 1

const login = async () => {
  const api = await pwRequest.newContext()
  const res = await api.post(`${API}/auth/login`, { data: { username: 'admin', password: 'admin123' } })
  expect(res.ok()).toBeTruthy()
  const body = await res.json()
  const headers = { Authorization: `Bearer ${body.access_token}` }
  return { api, headers, token: body.access_token, user: body.user || { username: 'admin', role: 'admin' } }
}

test('polygons made by a cut keep their database ids across autosaves', async ({ page }) => {
  const { api, headers, token, user } = await login()
  await api.post(`${API}/tasks/${GRID_ID}/claim`, { headers })
  await api.post(`${API}/annotations/grid/${GRID_ID}/init-base`, { headers })       // one polygon covering the grid

  await page.addInitScript(([t, u]) => {
    localStorage.setItem('geoai_token', t)
    localStorage.setItem('geoai_user', JSON.stringify(u))
    localStorage.setItem('geostevia_delta_save', '0')            // the full-save path, the one that lost ids
  }, [token, user])

  const saves = []
  page.on('request', (req) => {
    if (req.method() === 'POST' && /\/annotations\/grid\/\d+$/.test(req.url())) saves.push(JSON.parse(req.postData()))
  })

  await page.goto(`/map?taskId=${GRID_ID}`)
  const map = page.locator('.leaflet-container').first()
  await expect(map).toBeVisible({ timeout: 60000 })
  await page.waitForSelector('path.leaflet-interactive', { timeout: 60000 })
  await page.screenshot({ path: 'test-results/01-map-loaded.png' })

  await page.locator('.leaflet-control-zoom-out').click()           // the polygon must leave room around it for a line that crosses both edges
  await page.waitForTimeout(800)
  await page.getByText('Snap Sudut: ON').click()                    // snapping would pull the line's ends onto the polygon's edges
  const box = await map.boundingBox()
  const cut = async (x) => {
    const tool = page.locator('button[title^="Potong dengan Garis"]')
    await tool.click()
    await expect(tool).toHaveClass(/bg-slate-800/)                  // the cutting tool is active
    const top = box.y + box.height * 0.14
    const bottom = box.y + box.height * 0.86
    await page.mouse.move(x, top, { steps: 6 })
    await page.mouse.click(x, top)
    await page.mouse.move(x, (top + bottom) / 2, { steps: 6 })
    await page.mouse.click(x, (top + bottom) / 2)
    await page.mouse.move(x, bottom, { steps: 6 })
    const answered = page.waitForResponse((r) => r.url().includes('/annotations/split-by-line'), { timeout: 30000 })
    await page.mouse.dblclick(x, bottom)                           // a double click on the last point finishes the line
    const res = await answered
    expect(res.ok(), `split-by-line answered ${res.status()}: ${(await res.text()).slice(0, 300)}`).toBeTruthy()
  }

  await cut(box.x + box.width * 0.45)
  await page.screenshot({ path: 'test-results/02-after-first-cut.png' })
  await expect.poll(() => saves.length, { timeout: 60000, message: 'first autosave' }).toBeGreaterThanOrEqual(1)

  await cut(box.x + box.width * 0.60)
  await expect.poll(() => saves.length, { timeout: 60000, message: 'second autosave' }).toBeGreaterThanOrEqual(2)

  const idless = (payload) => payload.features.filter((f) => f.id === null || f.id === undefined).length
  const [first, second] = saves.slice(-2)
  console.log('features without id: first autosave', idless(first), '/', first.features.length, '| second autosave', idless(second), '/', second.features.length)
  expect(idless(first)).toBe(first.features.length)                  // both pieces of the first cut are new in the first autosave
  // ... and the piece the second cut left alone is known in the second one. With the bug every polygon lacked an id again.
  expect(second.features.length - idless(second)).toBeGreaterThanOrEqual(1)

  const rows = await (await api.get(`${API}/annotations/grid/${GRID_ID}`, { headers })).json()
  const ids = (rows.features || rows).map((f) => f.id ?? f.properties?.id)
  expect(new Set(ids).size).toBe(ids.length)                          // no polygon twice
})

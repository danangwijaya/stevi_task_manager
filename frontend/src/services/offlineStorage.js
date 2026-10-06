/**
 * GeoStevia Offline & Local Draft Storage Service
 * Uses HTML5 IndexedDB to persist in-progress polygon annotations locally
 * preventing data loss on network drops, laptop crashes, or accidental reloads.
 */

const DB_NAME = 'geostevia_offline_db'
const DB_VERSION = 1
const STORE_NAME = 'task_drafts'

let dbPromise = null

function getDb() {
  if (dbPromise) return dbPromise

  dbPromise = new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      resolve(null)
      return
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = (event) => {
      const db = event.target.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'taskId' })
      }
    }

    request.onsuccess = (event) => {
      resolve(event.target.result)
    }

    request.onerror = (event) => {
      console.warn('Failed to open IndexedDB:', event.target.error)
      resolve(null)
    }
  })

  return dbPromise
}

export async function saveTaskDraft(taskId, features, meta = {}) {
  try {
    const db = await getDb()
    if (!db) return false

    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)

      const draftRecord = {
        taskId: Number(taskId),
        features: JSON.parse(JSON.stringify(features)),
        polygonCount: features.length,
        savedAt: Date.now(),
        meta: meta
      }

      const req = store.put(draftRecord)
      req.onsuccess = () => resolve(true)
      req.onerror = () => resolve(false)
    })
  } catch (err) {
    console.warn('Error saving offline draft:', err)
    return false
  }
}

export async function getTaskDraft(taskId) {
  try {
    const db = await getDb()
    if (!db) return null

    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const req = store.get(Number(taskId))

      req.onsuccess = (e) => {
        resolve(e.target.result || null)
      }
      req.onerror = () => resolve(null)
    })
  } catch (err) {
    console.warn('Error reading offline draft:', err)
    return null
  }
}

export async function clearTaskDraft(taskId) {
  try {
    const db = await getDb()
    if (!db) return false

    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const req = store.delete(Number(taskId))

      req.onsuccess = () => resolve(true)
      req.onerror = () => resolve(false)
    })
  } catch (err) {
    console.warn('Error clearing offline draft:', err)
    return false
  }
}

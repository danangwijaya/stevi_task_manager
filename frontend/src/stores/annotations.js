import { defineStore } from 'pinia'
import api from '../services/api'
import { useAuthStore } from './auth'
import { buildBaseline, computeDelta, applyResponse, rebase, numericId } from '../services/deltaSave'

// What the server is known to hold per grid (Map id -> { hash, version }). Kept outside Pinia state on purpose:
// it is bookkeeping for the next save, not something the UI renders, and it can hold thousands of entries.
const baselines = new Map()

// Delta save is on for admins and the pilot mappers below by default, and opt-in/out per browser with localStorage
// 'geostevia_delta_save' = '1' / '0'. Widening the rollout later means changing this one function.
const DELTA_PILOT_USER_IDS = [23, 28]   // Nurul Halimah, Tita Amalia Sudarma
const deltaSaveEnabled = () => {
  let flag = null
  try { flag = localStorage.getItem('geostevia_delta_save') } catch (_) {}
  if (flag === '1') return true
  if (flag === '0') return false
  const auth = useAuthStore()
  return auth.isAdmin || DELTA_PILOT_USER_IDS.includes(auth.user?.id)
}

export const useAnnotationsStore = defineStore('annotations', {
  state: () => ({
    classes: [],
    selectedClass: null,
    currentFeatures: [],
    loading: false,
    saving: false,
    dirty: false,
    lastSaveError: null,
    // Per grid: server clock at last sync, and newest annotation change seen at that load
    syncedAt: {},
    annotationsUpdatedAt: {}
  }),

  actions: {
    async fetchClasses() {
      try {
        const response = await api.getClasses()
        this.classes = response.data
        if (this.classes.length > 0 && !this.selectedClass) {
          this.selectedClass = this.classes[0]
        }
      } catch (err) {
        console.error('Failed to fetch classes:', err)
      }
    },

    setSelectedClass(cls) {
      this.selectedClass = cls
    },

    async fetchGridAnnotations(taskGridId) {
      this.loading = true
      try {
        const response = await api.getGridAnnotations(taskGridId)
        this.currentFeatures = response.data.features || []
        baselines.set(taskGridId, buildBaseline(this.currentFeatures))
        this.syncedAt[taskGridId] = response.data.server_time || null
        this.annotationsUpdatedAt[taskGridId] = response.data.annotations_updated_at || null
        this.dirty = false
        return this.currentFeatures
      } catch (err) {
        console.error('Failed to fetch annotations:', err)
        this.currentFeatures = []
        return []
      } finally {
        this.loading = false
      }
    },

    // Called by the map after the server changed rows on its own (smart delete neighbours)
    rebaseFeatures(taskGridId, features) {
      const base = baselines.get(taskGridId)
      if (base) rebase(base, features)
    },

    // Sends only what changed. Returns the same shape as the full save plus `conflicts`, `rejected`,
    // `extra_features`; returns null when a delta cannot be computed safely (the caller falls back to the full save).
    async saveGridChanges(taskGridId, features) {
      const base = baselines.get(taskGridId)
      const delta = computeDelta(features, base)
      if (delta.fallback) return null
      if (!delta.upserts.length && !delta.deletes.length) {
        return { ok: true, id_map: {}, count: 0, preserved_ids: [], dropped_duplicates: 0, conflicts: [], rejected: [], extra_features: [], nothing: true }
      }
      const response = await api.saveGridChanges(taskGridId, { upserts: delta.upserts, deletes: delta.deletes })
      const out = applyResponse(base, delta.sent, response.data)
      this.currentFeatures = features
      if (response.data?.server_time) this.syncedAt[taskGridId] = response.data.server_time
      this.dirty = false
      return {
        ok: true,
        id_map: out.idMap,
        count: delta.upserts.length,
        preserved_ids: [],
        dropped_duplicates: 0,
        conflicts: out.conflicts,
        rejected: out.rejected,
        extra_features: out.extraFeatures
      }
    },

    async saveGridAnnotations(taskGridId, features) {
      this.saving = true
      this.lastSaveError = null
      try {
        if (deltaSaveEnabled() && Array.isArray(features)) {
          const viaDelta = await this.saveGridChanges(taskGridId, features)
          if (viaDelta) return viaDelta
        }
        const response = await api.saveGridAnnotations(taskGridId, features, this.syncedAt[taskGridId] || null)
        const idMap = response.data?.id_map || null
        if (idMap && Array.isArray(features)) {
          features.forEach(f => {
            if (!f) return
            const uId = f._uiId || f.properties?._uiId
            if (uId && idMap[uId] !== undefined) {
              const dbId = idMap[uId]
              f.id = dbId
              if (f.properties) f.properties.id = dbId
            }
          })
        }
        if (Array.isArray(response.data?.saved_features) && response.data.saved_features.length > 0) {
          this.currentFeatures = response.data.saved_features
        } else {
          this.currentFeatures = features
        }
        // When the server kept rows this client never received (preserved_ids), do NOT move the sync point forward:
        // the next save would treat those rows as known and delete them. It stays until the grid is reloaded.
        if (response.data?.server_time && !(response.data.preserved_ids?.length)) {
          this.syncedAt[taskGridId] = response.data.server_time
        }
        this.dirty = false
        // Only trust the baseline when every polygon now has a database id; otherwise (e.g. the server dropped a
        // duplicate the screen still shows) the next save must be a full one, or that polygon would be inserted again.
        if (Array.isArray(features) && features.every(f => numericId(f) !== null) && !response.data?.dropped_duplicates) {
          baselines.set(taskGridId, buildBaseline(features))
        } else {
          baselines.delete(taskGridId)
        }
        return {
          ok: true,
          id_map: idMap,
          count: response.data?.count,
          preserved_ids: response.data?.preserved_ids || [],
          dropped_duplicates: response.data?.dropped_duplicates || 0
        }
      } catch (err) {
        console.error('Failed to save annotations:', err)
        this.lastSaveError = err.response?.data?.detail || err.message || 'Gagal menyimpan anotasi ke server.'
        return false
      } finally {
        this.saving = false
      }
    },

    async fetchAnnotationsOverview(params = {}) {
      try {
        const response = await api.getAnnotationsOverview(params)
        return response.data
      } catch (err) {
        console.error('Failed to fetch annotations overview:', err)
        return { summary: {}, by_grid: [], by_mapper: [], by_class: [] }
      }
    },

    async fetchAllAnnotationsFeatures(params = {}) {
      try {
        const response = await api.getAllAnnotationsFeatures(params)
        return response.data.features || []
      } catch (err) {
        console.error('Failed to fetch all annotations features:', err)
        return []
      }
    }
  }
})

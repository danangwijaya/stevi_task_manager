import { defineStore } from 'pinia'
import api from '../services/api'

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

    async saveGridAnnotations(taskGridId, features) {
      this.saving = true
      this.lastSaveError = null
      try {
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
        if (response.data?.server_time) this.syncedAt[taskGridId] = response.data.server_time
        this.dirty = false
        return {
          ok: true,
          id_map: idMap,
          count: response.data?.count,
          preserved_ids: response.data?.preserved_ids || []
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

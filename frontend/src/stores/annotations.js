import { defineStore } from 'pinia'
import api from '../services/api'

export const useAnnotationsStore = defineStore('annotations', {
  state: () => ({
    classes: [],
    selectedClass: null,
    currentFeatures: [],
    loading: false,
    saving: false,
    dirty: false
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
      try {
        await api.saveGridAnnotations(taskGridId, features)
        this.currentFeatures = features
        this.dirty = false
        return true
      } catch (err) {
        console.error('Failed to save annotations:', err)
        return false
      } finally {
        this.saving = false
      }
    }
  }
})

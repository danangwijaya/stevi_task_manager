import { defineStore } from 'pinia'
import api from '../services/api'
import { useAuthStore } from './auth'

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    projects: [],
    tasks: [],
    currentTask: null,
    stats: null,
    loading: false,
    loadingProjects: false,
    selectedYear: 2025,
    selectedArea: null,
    selectedStatus: null,
    filterMyTasks: false,
    currentTaskReviewPins: []
  }),

  getters: {
    myRevisionTasks(state) {
      const authStore = useAuthStore()
      if (!authStore.user) return []
      return state.tasks.filter(t => 
        t.status === 'REVISION_NEEDED' && 
        (authStore.isAdmin || t.assigned_user_id === authStore.user.id)
      )
    },
    totalRevisionCount(state) {
      const authStore = useAuthStore()
      if (!authStore.user) return 0
      return state.tasks.filter(t => 
        t.status === 'REVISION_NEEDED' && 
        (authStore.isAdmin || t.assigned_user_id === authStore.user.id)
      ).length
    }
  },

  actions: {
    async fetchProjects() {
      this.loadingProjects = true
      try {
        const response = await api.getProjects()
        this.projects = response.data
        return response.data
      } catch (err) {
        console.error('Failed to fetch projects:', err)
        return []
      } finally {
        this.loadingProjects = false
      }
    },

    async fetchTasks() {
      this.loading = true
      try {
        const params = {}
        if (this.selectedYear) params.year = this.selectedYear
        if (this.selectedArea) params.study_area_id = this.selectedArea
        if (this.selectedStatus) params.status = this.selectedStatus
        if (this.filterMyTasks) params.assigned_to_me = true

        const response = await api.getTasks(params)
        this.tasks = response.data
      } catch (err) {
        console.error('Failed to fetch tasks:', err)
      } finally {
        this.loading = false
      }
    },

    async fetchTaskDetail(taskId) {
      this.loading = true
      try {
        const response = await api.getTaskDetail(taskId)
        this.currentTask = response.data
        return response.data
      } catch (err) {
        console.error('Failed to fetch task detail:', err)
        return null
      } finally {
        this.loading = false
      }
    },

    async fetchStats() {
      try {
        const response = await api.getStatsSummary()
        this.stats = response.data
      } catch (err) {
        console.error('Failed to fetch stats:', err)
      }
    },

    async fetchStatsSummary() {
      return this.fetchStats()
    },

    async claimTask(taskId) {
      try {
        const response = await api.claimTask(taskId)
        await this.fetchTasks()
        if (this.currentTask && this.currentTask.id === taskId) {
          this.currentTask.status = response.data.status || 'IN_PROGRESS'
          this.currentTask.assigned_user_name = response.data.assigned_user_name
        }
        return true
      } catch (err) {
        console.error('Failed to claim task:', err)
        throw err
      }
    },

    async unclaimTask(taskId) {
      try {
        await api.unclaimTask(taskId)
        await this.fetchTasks()
        if (this.currentTask && this.currentTask.id === taskId) {
          this.currentTask.status = 'UNASSIGNED'
          this.currentTask.assigned_user_name = null
        }
        return true
      } catch (err) {
        console.error('Failed to unclaim task:', err)
        throw err
      }
    },

    async updateStatus(taskId, status, notes = null) {
      try {
        await api.updateTaskStatus(taskId, status, notes)
        await this.fetchTasks()
        if (this.currentTask && this.currentTask.id === taskId) {
          this.currentTask.status = status
          this.currentTask.reviewer_notes = notes
        }
        await this.fetchStats()
        return true
      } catch (err) {
        console.error('Failed to update task status:', err)
        return false
      }
    },

    async assignTask(taskId, userId) {
      try {
        await api.assignTask(taskId, userId)
        await this.fetchTasks()
        await this.fetchStats()
        return true
      } catch (err) {
        console.error('Failed to assign task:', err)
        return false
      }
    },

    async resetProjectProgress(projectId) {
      try {
        const response = await api.resetProjectProgress(projectId)
        await this.fetchProjects()
        await this.fetchTasks()
        await this.fetchStats()
        return response.data
      } catch (err) {
        console.error('Failed to reset project progress:', err)
        throw err
      }
    },

    async fetchReviewPins(taskId) {
      try {
        const response = await api.getTaskReviewPins(taskId)
        this.currentTaskReviewPins = response.data || []
        return this.currentTaskReviewPins
      } catch (err) {
        console.error('Failed to fetch review pins:', err)
        return []
      }
    },

    async createReviewPin(taskId, pinData) {
      try {
        const response = await api.createTaskReviewPin(taskId, pinData)
        this.currentTaskReviewPins.push(response.data)
        return response.data
      } catch (err) {
        console.error('Failed to create review pin:', err)
        throw err
      }
    },

    async updateReviewPin(taskId, pinId, updateData) {
      try {
        const response = await api.updateTaskReviewPin(taskId, pinId, updateData)
        const idx = this.currentTaskReviewPins.findIndex(p => p.id === pinId)
        if (idx !== -1) {
          this.currentTaskReviewPins[idx] = response.data
        }
        return response.data
      } catch (err) {
        console.error('Failed to update review pin:', err)
        throw err
      }
    },

    async deleteReviewPin(taskId, pinId) {
      try {
        await api.deleteTaskReviewPin(taskId, pinId)
        this.currentTaskReviewPins = this.currentTaskReviewPins.filter(p => p.id !== pinId)
        return true
      } catch (err) {
        console.error('Failed to delete review pin:', err)
        throw err
      }
    }
  }
})


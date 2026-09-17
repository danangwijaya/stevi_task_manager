import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
const getBaseApi = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return `http://${window.location.hostname}:8000`
  }
  return ''
}

const API = getBaseApi()

function authHeaders() {
  const token = localStorage.getItem('geoai_token')
  return { Authorization: `Bearer ${token}` }
}

export const useAdminStore = defineStore('admin', () => {
  // ── State ────────────────────────────────────────────────────────────────
  const users = ref([])
  const projects = ref([])
  const loadingUsers = ref(false)
  const loadingProjects = ref(false)
  const error = ref(null)

  // ── USER ACTIONS ─────────────────────────────────────────────────────────

  async function fetchUsers() {
    loadingUsers.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${API}/api/v1/auth/users`, {
        headers: authHeaders()
      })
      users.value = data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Gagal memuat data pengguna'
    } finally {
      loadingUsers.value = false
    }
  }

  async function createUser(payload) {
    const { data } = await axios.post(`${API}/api/v1/auth/users`, payload, {
      headers: authHeaders()
    })
    users.value.push(data)
    return data
  }

  async function updateUser(userId, payload) {
    const { data } = await axios.put(`${API}/api/v1/auth/users/${userId}`, payload, {
      headers: authHeaders()
    })
    const idx = users.value.findIndex(u => u.id === userId)
    if (idx !== -1) users.value[idx] = data
    return data
  }

  async function deleteUser(userId) {
    const { data } = await axios.delete(`${API}/api/v1/auth/users/${userId}`, {
      headers: authHeaders()
    })
    if (data?.action === 'deactivated') {
      const idx = users.value.findIndex(u => u.id === userId)
      if (idx !== -1) users.value[idx].is_active = false
    } else {
      users.value = users.value.filter(u => u.id !== userId)
    }
    return data
  }

  async function toggleUserActive(userId, isActive) {
    return updateUser(userId, { is_active: isActive })
  }

  async function resetPassword(userId, newPassword = null) {
    const payload = newPassword ? { password: newPassword } : {}
    const { data } = await axios.post(`${API}/api/v1/auth/users/${userId}/reset-password`, payload, {
      headers: authHeaders()
    })
    return data
  }

  // ── PROJECT ACTIONS ───────────────────────────────────────────────────────

  async function fetchProjects() {
    loadingProjects.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${API}/api/v1/tasks/projects`, {
        headers: authHeaders()
      })
      projects.value = data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Gagal memuat data proyek'
    } finally {
      loadingProjects.value = false
    }
  }

  async function createProject(payload) {
    const { data } = await axios.post(`${API}/api/v1/tasks/projects`, payload, {
      headers: authHeaders()
    })
    projects.value.push(data)
    return data
  }

  async function updateProject(projectId, payload) {
    const { data } = await axios.put(`${API}/api/v1/tasks/projects/${projectId}`, payload, {
      headers: authHeaders()
    })
    const idx = projects.value.findIndex(p => p.id === projectId)
    if (idx !== -1) projects.value[idx] = data
    return data
  }

  async function deleteProject(projectId) {
    await axios.delete(`${API}/api/v1/tasks/projects/${projectId}`, {
      headers: authHeaders()
    })
    projects.value = projects.value.filter(p => p.id !== projectId)
  }

  async function resetProject(projectId) {
    const { data } = await axios.post(`${API}/api/v1/tasks/projects/${projectId}/reset`, {}, {
      headers: authHeaders()
    })
    await fetchProjects()
    return data
  }

  return {
    users, projects, loadingUsers, loadingProjects, error,
    fetchUsers, createUser, updateUser, deleteUser, toggleUserActive, resetPassword,
    fetchProjects, createProject, updateProject, deleteProject, resetProject
  }
})

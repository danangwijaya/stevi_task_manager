import { defineStore } from 'pinia'
import api from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('geoai_token') || null,
    user: JSON.parse(localStorage.getItem('geoai_user') || 'null'),
    allUsers: [],
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => (state.user?.role || '').toLowerCase() === 'admin',
    isDosen: (state) => ['dosen', 'supervisi'].includes((state.user?.role || '').toLowerCase()),
    isSupervisi: (state) => ['dosen', 'supervisi'].includes((state.user?.role || '').toLowerCase()),
    isReviewer: (state) => ['admin', 'dosen', 'supervisi'].includes((state.user?.role || '').toLowerCase()),
    roleTitle: (state) => {
      const role = (state.user?.role || '').toLowerCase()
      if (role === 'admin') return 'Lead Administrator'
      if (role === 'dosen' || role === 'supervisi') return 'Supervisi'
      return 'Anotator / Mapper'
    },
    userName: (state) => state.user?.full_name || state.user?.username || 'User'
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const response = await api.login({ username, password })
        const { access_token, user_id, full_name, role } = response.data
        
        this.token = access_token
        this.user = { id: user_id, username, full_name, role }
        
        localStorage.setItem('geoai_token', access_token)
        localStorage.setItem('geoai_user', JSON.stringify(this.user))
        
        return true
      } catch (err) {
        console.error('Login error:', err)
        this.error = err.response?.data?.detail || err.message || 'Gagal login. Periksa username dan password.'
        return false
      } finally {
        this.loading = false
      }
    },

    async signup(userData) {
      this.loading = true
      this.error = null
      try {
        const response = await api.signup(userData)
        const { access_token, user_id, full_name, role, username } = response.data
        
        this.token = access_token
        this.user = { id: user_id, username, full_name, role }
        
        localStorage.setItem('geoai_token', access_token)
        localStorage.setItem('geoai_user', JSON.stringify(this.user))
        
        return true
      } catch (err) {
        console.error('Signup error:', err)
        this.error = err.response?.data?.detail || err.message || 'Gagal mendaftar. Silakan coba lagi.'
        return false
      } finally {
        this.loading = false
      }
    },

    async oauthLogin(provider, email = null, full_name = null) {
      this.loading = true
      this.error = null
      try {
        const response = await api.oauthLogin({ provider, email, full_name })
        const { access_token, user_id, full_name: name, role, username } = response.data
        
        this.token = access_token
        this.user = { id: user_id, username, full_name: name, role }
        
        localStorage.setItem('geoai_token', access_token)
        localStorage.setItem('geoai_user', JSON.stringify(this.user))
        
        return true
      } catch (err) {
        console.error('OAuth login error:', err)
        this.error = err.response?.data?.detail || err.message || `Gagal login via ${provider}.`
        return false
      } finally {
        this.loading = false
      }
    },

    async fetchAllUsers() {
      try {
        const response = await api.getUsers()
        this.allUsers = response.data
        return response.data
      } catch (err) {
        console.error('Failed to fetch users:', err)
        return []
      }
    },

    async createUser(userData) {
      try {
        await api.createUser(userData)
        await this.fetchAllUsers()
        return true
      } catch (err) {
        console.error('Failed to create user:', err)
        throw err
      }
    },

    async updateUser(userId, userData) {
      try {
        await api.updateUser(userId, userData)
        await this.fetchAllUsers()
        return true
      } catch (err) {
        console.error('Failed to update user:', err)
        throw err
      }
    },

    async deleteUser(userId) {
      try {
        await api.deleteUser(userId)
        await this.fetchAllUsers()
        return true
      } catch (err) {
        console.error('Failed to delete user:', err)
        throw err
      }
    },

    async updateProfile(profileData) {
      this.loading = true
      this.error = null
      try {
        const response = await api.updateMe(profileData)
        const updated = response.data
        this.user = {
          ...this.user,
          ...updated
        }
        localStorage.setItem('geoai_user', JSON.stringify(this.user))
        return updated
      } catch (err) {
        console.error('Failed to update profile:', err)
        this.error = err.response?.data?.detail || err.message || 'Gagal memperbarui profil'
        throw err
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('geoai_token')
      localStorage.removeItem('geoai_user')
      window.location.href = '/'
    }
  }
})

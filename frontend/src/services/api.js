import axios from 'axios'

// Dynamically determine backend URL
const getBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // In development, connect directly to FastAPI port 8000 to bypass proxy issues
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return `http://${window.location.hostname}:8000/api/v1`
  }
  return '/api/v1'
}

const api = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('geoai_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('geoai_token')
      localStorage.removeItem('geoai_user')
      const publicPaths = ['/', '/login']
      const currentPath = typeof window !== 'undefined' ? window.location.pathname : ''
      const isPublic = publicPaths.includes(currentPath) || currentPath.startsWith('/project')
      if (!isPublic && typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export { api }

export default {
  // Generic HTTP methods
  get: (url, config) => api.get(url, config),
  post: (url, data, config) => api.post(url, data, config),
  put: (url, data, config) => api.put(url, data, config),
  delete: (url, config) => api.delete(url, config),

  // ArcGIS Token
  getArcgisToken: () => api.get('/arcgis/token'),

  // Auth
  login: (credentials) => api.post('/auth/login', credentials),
  signup: (userData) => api.post('/auth/signup', userData),
  oauthLogin: (oauthData) => api.post('/auth/oauth', oauthData),
  getMe: () => api.get('/auth/me'),
  updateMe: (profileData) => api.put('/auth/me', profileData),
  getUsers: () => api.get('/auth/users'),
  createUser: (userData) => api.post('/auth/users', userData),
  updateUser: (userId, userData) => api.put(`/auth/users/${userId}`, userData),
  deleteUser: (userId) => api.delete(`/auth/users/${userId}`),
  resetPassword: (userId, data) => api.post(`/auth/users/${userId}/reset-password`, data),

  // Projects & Tasks
  getProjects: () => api.get('/tasks/projects'),
  createProject: (projectData) => api.post('/tasks/projects', projectData),
  updateProject: (projectId, projectData) => api.put(`/tasks/projects/${projectId}`, projectData),
  deleteProject: (projectId) => api.delete(`/tasks/projects/${projectId}`),
  resetProjectProgress: (projectId) => api.post(`/tasks/projects/${projectId}/reset`),
  getTasks: (params) => api.get('/tasks/', { params }),
  getTaskDetail: (taskId) => api.get(`/tasks/${taskId}`),
  getTaskSiblings: (taskId) => api.get(`/tasks/${taskId}/siblings`),
  createTask: (taskData) => api.post('/tasks/', taskData),
  assignTask: (taskId, userId) => api.post(`/tasks/${taskId}/assign`, { user_id: userId }),
  claimTask: (taskId) => api.post(`/tasks/${taskId}/claim`),
  unclaimTask: (taskId) => api.post(`/tasks/${taskId}/unclaim`),
  updateTaskStatus: (taskId, status, reviewerNotes = null) => 
    api.post(`/tasks/${taskId}/status`, { status, reviewer_notes: reviewerNotes }),
  getStatsSummary: () => api.get('/tasks/stats/summary'),

  // Annotations & Classes
  getClasses: () => api.get('/annotations/classes'),
  getAnnotationsOverview: (params) => api.get('/annotations/overview', { params }),
  getAllAnnotationsFeatures: (params) => api.get('/annotations/all-features', { params }),
  getGridAnnotations: (taskGridId) => api.get(`/annotations/grid/${taskGridId}`),
  getNeighborAnnotations: (taskGridId) => api.get(`/annotations/grid/${taskGridId}/neighbors-features`),
  saveGridAnnotations: (taskGridId, features) => api.post(`/annotations/grid/${taskGridId}`, {
    task_grid_id: taskGridId,
    features: features
  }),
  deleteAnnotation: (annId) => api.delete(`/annotations/${annId}`),
  initBasePolygon: (taskGridId) => api.post(`/annotations/grid/${taskGridId}/init-base`),
  validateTopology: (taskGridId) => api.post(`/annotations/grid/${taskGridId}/validate-topology`),
  copyAnnotations: (targetId, sourceId) => api.post(`/annotations/grid/${targetId}/copy-from/${sourceId}`),
  splitByPolygon: (taskGridId, cuttingGeom, targetAnnId = null, newClassId = 0) =>
    api.post('/annotations/split-by-polygon', {
      task_grid_id: taskGridId,
      cutting_geom: cuttingGeom,
      target_annotation_id: targetAnnId,
      new_class_id: newClassId
    }),
  splitByLine: (taskGridId, lineGeom, targetAnnId = null, newClassId = 0) =>
    api.post('/annotations/split-by-line', {
      task_grid_id: taskGridId,
      line_geom: lineGeom,
      target_annotation_id: targetAnnId,
      new_class_id: newClassId
    }),
  mergePolygons: (taskGridId, annotationIds, targetClassId) =>
    api.post('/annotations/merge', {
      task_grid_id: taskGridId,
      annotation_ids: annotationIds,
      target_class_id: targetClassId
    }),
  updateAnnotationClass: (annId, classId) =>
    api.put(`/annotations/${annId}/class`, { class_id: classId }),

  // GEE Satellite Layers
  getGEEStatus: () => api.get('/gee/status'),
  getGEETiles: (params) => api.get('/gee/tiles', { params }),

  // 1-Click Export & Vector Export
  triggerExport: (year = 2025, onlyApproved = false) => 
    api.post('/export/trigger', null, { params: { year, only_approved: onlyApproved } }),
  getDownloadUrl: (jobId) => `${getBaseUrl()}/export/download/${jobId}`,
  
  // Vector Training Samples Export (GeoJSON & Shapefile)
  getVectorExportSummary: (params = {}) => api.get('/export/vector/summary', { params }),
  getVectorGeoJsonDownloadUrl: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return `${getBaseUrl()}/export/vector/geojson${qs ? '?' + qs : ''}`
  },
  getVectorShapefileDownloadUrl: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return `${getBaseUrl()}/export/vector/shapefile${qs ? '?' + qs : ''}`
  },
  downloadVectorGeoJson: (params = {}) =>
    api.get('/export/vector/geojson', { params, responseType: 'blob' }),
  downloadVectorShapefile: (params = {}) =>
    api.get('/export/vector/shapefile', { params, responseType: 'blob' }),

  // Import Custom Grid (Shapefile / GeoJSON)
  importGrid: (formData) => api.post('/tasks/import-grid', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),

  // Dynamic Sentinel-2 COG Raster Layer (2025, 2022, 2018+)
  getRasterYears: () => api.get('/raster/years'),
  getGridRasterInfo: (gridCode) => api.get(`/raster/info/${gridCode}`),
  getGridRasterTileUrl: (year, gridCode, mode = 'rgb', gamma = 1.0) =>
    `${getBaseUrl()}/raster/tiles/${year}/${gridCode}/{z}/{x}/{y}.png?mode=${mode}&gamma=${gamma}`,
  getMosaicRasterTileUrl: (year, mode = 'rgb', gamma = 1.0) =>
    `${getBaseUrl()}/raster/tiles/${year}/{z}/{x}/{y}.png?mode=${mode}&gamma=${gamma}`
}

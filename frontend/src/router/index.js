import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '../views/LandingView.vue'
import ProjectDetailView from '../views/ProjectDetailView.vue'
import DashboardView from '../views/DashboardView.vue'
import TaskingManagerView from '../views/TaskingManagerView.vue'
import AnnotatorMapView from '../views/AnnotatorMapView.vue'
import AdminQCView from '../views/AdminQCView.vue'
import AdminPanelView from '../views/AdminPanelView.vue'
import ExportDatasetView from '../views/ExportDatasetView.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingView
  },
  {
    path: '/project/:id?',
    name: 'project-detail',
    component: ProjectDetailView
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tasking',
    name: 'tasking',
    component: TaskingManagerView,
    meta: { requiresAuth: true }
  },
  {
    path: '/map',
    name: 'map',
    component: AnnotatorMapView,
    meta: { requiresAuth: true }
  },
  {
    path: '/qc',
    name: 'qc',
    component: AdminQCView,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminPanelView,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/export',
    name: 'export',
    component: ExportDatasetView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('geoai_token')
  const userRaw = localStorage.getItem('geoai_user')

  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  if (to.meta.requiresAdmin) {
    try {
      const user = userRaw ? JSON.parse(userRaw) : null
      if (!user || user.role !== 'admin') {
        next('/')
        return
      }
    } catch {
      next('/')
      return
    }
  }

  if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router

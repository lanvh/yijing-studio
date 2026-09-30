import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true } },
    { path: '/models', name: 'models', component: () => import('../views/ModelsView.vue'), meta: { requiresAuth: true } },
    { path: '/models/create', name: 'model-create', component: () => import('../views/ModelFormView.vue'), meta: { requiresAuth: true } },
    { path: '/models/:id/edit', name: 'model-edit', component: () => import('../views/ModelFormView.vue'), meta: { requiresAuth: true } },
    { path: '/models/:id', name: 'model-detail', component: () => import('../views/ModelDetailView.vue'), meta: { requiresAuth: true } },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.initialized) await auth.restore()
  if (to.meta.requiresAuth && !auth.user) return { name: 'login' }
  if (to.name === 'login' && auth.user) return { name: 'dashboard' }
})

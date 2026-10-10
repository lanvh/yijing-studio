import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/mobile-publish/:id', name: 'mobile-publish', component: () => import('../views/MobilePublishView.vue') },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true } },
    { path: '/models', name: 'models', component: () => import('../views/ModelsView.vue'), meta: { requiresAuth: true } },
    { path: '/models/create', name: 'model-create', component: () => import('../views/ModelFormView.vue'), meta: { requiresAuth: true } },
    { path: '/models/:id/edit', name: 'model-edit', component: () => import('../views/ModelFormView.vue'), meta: { requiresAuth: true } },
    { path: '/models/:id', name: 'model-detail', component: () => import('../views/ModelDetailView.vue'), meta: { requiresAuth: true } },
    { path: '/products', name: 'products', component: () => import('../views/ProductsView.vue'), meta: { requiresAuth: true } },
    { path: '/products/create', name: 'product-create', component: () => import('../views/ProductFormView.vue'), meta: { requiresAuth: true } },
    { path: '/products/:id/edit', name: 'product-edit', component: () => import('../views/ProductFormView.vue'), meta: { requiresAuth: true } },
    { path: '/products/:id', name: 'product-detail', component: () => import('../views/ProductDetailView.vue'), meta: { requiresAuth: true } },
    { path: '/create-content', name: 'create-content', component: () => import('../views/CreateContentView.vue'), meta: { requiresAuth: true } },
    { path: '/tasks', name: 'tasks', component: () => import('../views/TasksView.vue'), meta: { requiresAuth: true } },
    { path: '/tasks/:id', name: 'task-detail', component: () => import('../views/TaskDetailView.vue'), meta: { requiresAuth: true } },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { requiresAuth: true } },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

router.beforeEach(async (to) => {
  if (to.name === 'mobile-publish') return
  const auth = useAuthStore()
  if (!auth.initialized) await auth.restore()
  if (to.meta.requiresAuth && !auth.user) return { name: 'login' }
  if (to.name === 'login' && auth.user) return { name: 'dashboard' }
})

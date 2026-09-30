import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElInputNumber, ElPagination, ElCheckbox, ElDialog } from 'element-plus'
import 'element-plus/dist/index.css'
import { router } from './router'
import App from './App.vue'
import './style.css'
import './models.css'
import './products.css'
import { api } from './api/client'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())
app.use(router)
for (const component of [ElAlert, ElButton, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElInputNumber, ElPagination, ElCheckbox, ElDialog]) {
  app.component(component.name!, component)
}
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401 && !error.config?.url?.startsWith('/auth')) {
    const auth = useAuthStore()
    auth.user = null
    auth.serviceError = '登录已失效，请重新登录。'
    void router.replace('/login')
  }
  return Promise.reject(error)
})
app.mount('#app')

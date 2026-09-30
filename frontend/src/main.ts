import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput } from 'element-plus'
import 'element-plus/dist/index.css'
import { router } from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
for (const component of [ElAlert, ElButton, ElForm, ElFormItem, ElInput]) {
  app.component(component.name!, component)
}
app.mount('#app')

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { errorMessage } from '../api/client'

defineProps<{ title: string }>()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const busy = ref(false)
const error = ref('')
async function logout() {
  busy.value = true
  error.value = ''
  try {
    await auth.logout()
    await router.replace('/login')
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <div class="workspace">
    <aside class="sidebar">
      <router-link
        class="brand"
        to="/dashboard"
      >
        <span class="brand-mark">s</span><span>AI SEED<br>STUDIO</span>
      </router-link>
      <p class="nav-label">
        工作空间
      </p>
      <nav aria-label="主导航">
        <router-link
          to="/dashboard"
          :class="{ 'nav-active': route.path === '/dashboard' }"
        >
          <span>◫</span> 工作台
        </router-link>
        <router-link
          to="/models"
          :class="{ 'nav-active': route.path.startsWith('/models') }"
        >
          <span>♧</span> AI 模特
        </router-link>
        <router-link
          to="/products"
          :class="{ 'nav-active': route.path.startsWith('/products') }"
        >
          <span>◇</span> 商品库
        </router-link>
        <router-link
          to="/create-content"
          :class="{ 'nav-active': route.path === '/create-content' }"
        >
          <span>✧</span> 创建内容
        </router-link>
        <router-link
          to="/tasks"
          :class="{ 'nav-active': route.path.startsWith('/tasks') }"
        >
          <span>▤</span> 生成记录
        </router-link>
        <router-link
          to="/settings"
          :class="{ 'nav-active': route.path === '/settings' }"
        >
          <span>⚙</span> 系统状态
        </router-link>
      </nav>
      <div class="sidebar-bottom">
        <span class="status-dot" /> 私人创作空间<p>从灵感开始，慢慢成形。</p>
      </div>
    </aside>
    <main class="workspace-main">
      <header class="workspace-header">
        <span>工作空间 <span class="breadcrumb">/</span> {{ title }}</span>
        <div class="account-tools">
          <span class="avatar">{{ auth.user?.display_name.slice(0, 1) }}</span>
          <span>{{ auth.user?.display_name }}</span>
          <el-button
            text
            :loading="busy"
            @click="logout"
          >
            退出登录
          </el-button>
        </div>
      </header>
      <nav
        class="mobile-nav"
        aria-label="移动导航"
      >
        <router-link to="/dashboard">
          工作台
        </router-link><router-link to="/models">
          AI 模特
        </router-link><router-link to="/products">
          商品库
        </router-link>
        <router-link to="/create-content">
          创建内容
        </router-link>
        <router-link to="/tasks">
          生成记录
        </router-link>
        <router-link to="/settings">
          系统状态
        </router-link>
      </nav>
      <div class="dashboard-content">
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          role="alert"
        />
        <slot />
      </div>
    </main>
  </div>
</template>

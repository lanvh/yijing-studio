<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { errorMessage } from '../api/client'

const auth = useAuthStore()
const router = useRouter()
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
      <a
        class="brand"
        href="/dashboard"
      ><span class="brand-mark">s</span> <span>AI SEED<br>STUDIO</span></a>
      <p class="nav-label">
        工作空间
      </p>
      <nav aria-label="主导航">
        <router-link
          class="nav-active"
          to="/dashboard"
        >
          <span>◫</span> 工作台 <span class="nav-dot">●</span>
        </router-link>
        <div class="nav-future">
          <span>♧</span> AI 模特 <small>即将开放</small>
        </div>
        <div class="nav-future">
          <span>◇</span> 商品库
        </div>
        <div class="nav-future">
          <span>✧</span> 创建内容
        </div>
        <div class="nav-future">
          <span>▤</span> 生成记录
        </div>
      </nav>
      <div class="sidebar-bottom">
        <span class="status-dot" /> 私人创作空间<p>从灵感开始，慢慢成形。</p>
      </div>
    </aside>
    <main class="workspace-main">
      <header class="workspace-header">
        <span>工作空间 <span class="breadcrumb">/</span> 工作台</span>
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
      <div class="dashboard-content">
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          role="alert"
        />
        <div class="dashboard-title">
          <div>
            <p class="eyebrow">
              YOUR CREATIVE WORKSPACE
            </p><h1>你好，{{ auth.user?.display_name }}。</h1><p class="muted">
              欢迎来到你的 AI 摄影棚。好作品，从这里开始。
            </p>
          </div><span class="version-pill">早期预览</span>
        </div>
        <section class="welcome-card">
          <div>
            <p class="eyebrow light">
              THE BEGINNING OF SOMETHING GOOD
            </p><h2>你的下一组作品，<br>从一个灵感开始。</h2><p>人物、商品、场景，将在这里相遇。</p><span class="coming-label">创作功能准备中</span>
          </div>
          <div
            class="welcome-art"
            aria-hidden="true"
          >
            <span>✧</span><div class="welcome-circle" /><div class="welcome-square" />
          </div>
        </section>
        <div class="section-title">
          <h2>创作，从这三步开始</h2><span class="muted">功能将逐步开放</span>
        </div>
        <section
          class="journey-grid"
          aria-label="创作流程预览"
        >
          <article><span class="step-number">01 / CHARACTER</span><span class="journey-icon">♧</span><h3>塑造你的 AI 模特</h3><p>为每一种风格，找到合适的表达。</p><span class="next-label">下一步开放</span></article>
          <article><span class="step-number">02 / PRODUCT</span><span class="journey-icon">◇</span><h3>放入你的好物</h3><p>收集商品图片，让细节成为主角。</p><span class="muted">准备中</span></article>
          <article><span class="step-number">03 / CREATE</span><span class="journey-icon">✧</span><h3>把想法变成作品</h3><p>搭配人物与场景，探索新的可能。</p><span class="muted">准备中</span></article>
        </section>
        <section class="recent-section">
          <div class="section-title">
            <h2>最近创作</h2><span class="muted">你的作品将出现在这里</span>
          </div><div class="empty-state">
            <span>▧</span><div><h3>故事，等待开场</h3><p>创作功能开放后，在这里查看和管理你的素材。</p></div>
          </div>
        </section>
        <footer class="dashboard-footer">
          <span>AI 辅助创作 · 人工审核与发布</span><span>{{ auth.user?.email }}</span>
        </footer>
      </div>
    </main>
  </div>
</template>

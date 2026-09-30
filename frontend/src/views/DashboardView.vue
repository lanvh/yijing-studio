<script setup lang="ts">
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
</script>
<template>
  <WorkspaceLayout title="工作台">
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
        </p><h2>你的下一组作品，<br>从一个灵感开始。</h2><p>人物、商品、场景，将在这里相遇。</p><router-link
          class="coming-label"
          to="/models/create"
        >
          新建 AI 模特 ↗
        </router-link>
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
      <article>
        <span class="step-number">01 / CHARACTER</span><span class="journey-icon">♧</span><h3>塑造你的 AI 模特</h3><p>为每一种风格，找到合适的表达。</p><router-link
          class="next-label"
          to="/models"
        >
          管理 AI 模特 →
        </router-link>
      </article>
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
  </WorkspaceLayout>
</template>

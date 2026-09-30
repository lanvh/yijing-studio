<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { modelsApi } from '../api/models'
import { productsApi } from '../api/products'
import { generationApi } from '../api/generation'
import { errorMessage } from '../api/client'
import { statusLabels, type TaskSummary } from '../types/generation'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
const counts = ref<number[] | null>(null), recent = ref<TaskSummary[]>([]), error = ref('')
async function load() {
  error.value = ''
  try {
    const [models,products,tasks] = await Promise.all([modelsApi.list('',0,1),productsApi.list('','',0,1),generationApi.list(0,5)])
    counts.value = [models.total, products.total, tasks.total]; recent.value = tasks.items
  } catch (cause) { error.value = errorMessage(cause) }
}
onMounted(load)
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
      </div><span class="version-pill">Mock 工作流</span>
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
      <h2>创作，从这三步开始</h2><span class="muted">素材 → 生成 → 整理与下载</span>
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
      <article>
        <span class="step-number">02 / PRODUCT</span><span class="journey-icon">◇</span><h3>放入你的好物</h3><p>收集商品图片，让细节成为主角。</p><router-link
          class="next-label"
          to="/products"
        >
          管理商品库 →
        </router-link>
      </article>
      <article>
        <span class="step-number">03 / CREATE</span><span class="journey-icon">✧</span><h3>把想法变成作品</h3><p>搭配人物与场景，探索新的可能。</p><router-link
          class="next-label"
          to="/create-content"
        >
          创建 Mock 内容 →
        </router-link>
      </article>
    </section>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
    />
    <el-button
      v-if="error"
      @click="load"
    >
      重新加载工作台
    </el-button>
    <section
      v-if="counts"
      class="stat-grid"
    >
      <router-link to="/models">
        AI 模特<strong>{{ counts[0] }}</strong>
      </router-link>
      <router-link to="/products">
        商品资料<strong>{{ counts[1] }}</strong>
      </router-link>
      <router-link to="/tasks">
        创作任务<strong>{{ counts[2] }}</strong>
      </router-link>
    </section>
    <section class="recent-section">
      <div class="section-title">
        <h2>最近创作</h2><router-link to="/tasks">
          查看全部 →
        </router-link>
      </div>
      <div
        v-if="recent.length"
        class="task-list"
      >
        <router-link
          v-for="task in recent"
          :key="task.id"
          class="task-row"
          :to="'/tasks/' + task.id"
        >
          <div class="task-symbol">
            ✧
          </div><div class="task-row-main">
            <h2>{{ task.product_name }}</h2><p>{{ task.model_name }} · Mock · {{ task.result_count }} 张结果</p>
          </div><span :class="['task-status',task.status]">{{ statusLabels[task.status] }}</span>
        </router-link>
      </div>
      <div
        v-else-if="counts"
        class="empty-state"
      >
        <span>▧</span><div><h3>故事，等待开场</h3><p>从创建内容开始，生成后在这里继续整理与下载。</p></div>
      </div>
    </section>
    <footer class="dashboard-footer">
      <span>AI 辅助创作 · 人工审核与发布</span><span>{{ auth.user?.email }}</span>
    </footer>
  </WorkspaceLayout>
</template>

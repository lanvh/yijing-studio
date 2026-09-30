<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import ModelPortrait from '../components/ModelPortrait.vue'
import { modelsApi } from '../api/models'
import { errorMessage } from '../api/client'
import { genderLabels, type AIModel } from '../types/models'

const items = ref<AIModel[]>([])
const query = ref('')
const currentQuery = ref('')
const page = ref(1)
const total = ref(0)
const busy = ref(false)
const removing = ref('')
const error = ref('')
let requestId = 0
async function load() {
  const id = ++requestId
  busy.value = true
  error.value = ''
  try {
    const result = await modelsApi.list(currentQuery.value, (page.value - 1) * 12)
    if (id !== requestId) return
    items.value = result.items
    total.value = result.total
    if (!items.value.length && page.value > 1) { page.value--; await load() }
  } catch (cause) {
    if (id === requestId) error.value = errorMessage(cause)
  } finally {
    if (id === requestId) busy.value = false
  }
}
function search() { currentQuery.value = query.value.trim(); page.value = 1; void load() }
async function remove(model: AIModel) {
  try {
    await ElMessageBox.confirm('将删除「' + model.name + '」的资料及全部参考图，此操作无法撤销。', '删除模特', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  removing.value = model.id
  error.value = ''
  try { await modelsApi.remove(model.id); await load() }
  catch (cause) { error.value = errorMessage(cause) }
  finally { removing.value = '' }
}
onMounted(load)
</script>
<template>
  <WorkspaceLayout title="AI 模特">
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          YOUR CHARACTER LIBRARY
        </p><h1>每一种风格，都有自己的主角。</h1><p class="muted">
          保存人物特征与参考图，为接下来的创作做好准备。
        </p>
      </div>
      <router-link to="/models/create">
        <el-button
          type="primary"
          size="large"
        >
          ＋ 新建模特
        </el-button>
      </router-link>
    </div>
    <section class="library-toolbar">
      <span><strong>{{ total }}</strong> 位 AI 模特</span>
      <form
        class="model-search"
        @submit.prevent="search"
      >
        <el-input
          v-model="query"
          placeholder="搜索模特名称"
          aria-label="搜索模特名称"
          clearable
          maxlength="100"
          @clear="search"
        /><el-button
          native-type="submit"
          :loading="busy"
        >
          搜索
        </el-button>
      </form>
    </section>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      role="alert"
      class="section-alert"
    />
    <div
      v-if="error"
      class="retry-row"
    >
      <el-button @click="load">
        重新加载
      </el-button>
    </div>
    <div
      v-if="busy"
      class="library-loading"
      role="status"
    >
      正在整理你的模特库…
    </div>
    <section
      v-else-if="items.length"
      class="models-grid"
      aria-label="模特列表"
    >
      <article
        v-for="model in items"
        :key="model.id"
        class="model-card"
      >
        <router-link
          :to="'/models/' + model.id"
          :aria-label="'查看 ' + model.name"
        >
          <ModelPortrait
            :name="model.name"
            :src="model.reference_images[0]?.image_url"
          />
        </router-link>
        <div class="model-card-body">
          <div class="model-card-title">
            <h2>{{ model.name }}</h2><span>{{ model.reference_images.length }} 张参考图</span>
          </div>
          <p>{{ genderLabels[model.gender] }} · {{ model.age_range }} 岁<span v-if="model.height"> · {{ model.height }} cm</span></p>
          <div class="model-tags">
            <span>{{ model.style || '风格待补充' }}</span><span v-if="model.body_type">{{ model.body_type }}</span>
          </div>
          <div class="model-card-actions">
            <router-link :to="'/models/' + model.id">
              查看资料 ↗
            </router-link><router-link :to="'/models/' + model.id + '/edit'">
              编辑
            </router-link><el-button
              text
              type="danger"
              :loading="removing === model.id"
              :disabled="!!removing"
              @click="remove(model)"
            >
              删除
            </el-button>
          </div>
        </div>
      </article>
    </section>
    <section
      v-else-if="!error"
      class="library-empty"
    >
      <div class="empty-portrait">
        ♧
      </div><h2>{{ currentQuery ? '没有找到这位模特' : '给你的创作，找一位主角。' }}</h2>
      <p>{{ currentQuery ? '试试其他名称，或清空搜索条件。' : '从人物特征开始，逐步建立你的 AI 模特库。' }}</p>
      <el-button
        v-if="currentQuery"
        @click="query = ''; search()"
      >
        清空搜索
      </el-button>
      <router-link
        v-else
        to="/models/create"
      >
        <el-button type="primary">
          创建第一位模特
        </el-button>
      </router-link>
    </section>
    <el-pagination
      v-if="total > 12"
      v-model:current-page="page"
      :page-size="12"
      :total="total"
      layout="prev, pager, next"
      class="model-pagination"
      @current-change="load"
    />
    <p class="library-footnote">
      当前保存人物配置与参考图。AI 图片生成功能将在后续开放。
    </p>
  </WorkspaceLayout>
</template>

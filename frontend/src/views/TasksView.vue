<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { generationApi } from '../api/generation'
import { errorMessage } from '../api/client'
import { statusLabels, taskTime, type TaskSummary } from '../types/generation'
const items = ref<TaskSummary[]>([]), total = ref(0), page = ref(1), status = ref('')
const busy = ref(false), error = ref(''), removing = ref('')
let sequence = 0, timer: ReturnType<typeof setTimeout> | undefined, disposed = false
async function load() {
  clearTimeout(timer)
  const id = ++sequence
  busy.value = true; error.value = ''
  try {
    const result = await generationApi.list((page.value-1)*12,12,status.value)
    if (disposed || id !== sequence) return
    items.value = result.items; total.value = result.total
    if (!items.value.length && page.value > 1) { page.value--; await load(); return }
    if (items.value.some(t => t.is_active)) timer = setTimeout(() => { if (!disposed) void load() },4000)
  } catch (cause) { if (id === sequence) error.value = errorMessage(cause) }
  finally { if (id === sequence) busy.value = false }
}
function filter() { page.value = 1; void load() }
async function remove(task: TaskSummary) {
  try { await ElMessageBox.confirm('将删除该任务的图片、文案和保存的素材副本，无法撤销。','删除任务',{confirmButtonText:'确认删除',cancelButtonText:'取消',type:'warning'}) }
  catch { return }
  removing.value = task.id
  try { await generationApi.remove(task.id); await load() }
  catch (cause) { error.value = errorMessage(cause) }
  finally { removing.value = '' }
}
onMounted(load)
onUnmounted(() => { disposed = true; sequence++; clearTimeout(timer) })
</script>
<template>
  <WorkspaceLayout title="生成记录">
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          YOUR CREATIVE ARCHIVE
        </p><h1>每一次灵感，都有迹可循。</h1><p class="muted">
          继续整理结果，或回到一组熟悉的搭配。
        </p>
      </div><router-link to="/create-content">
        <el-button
          type="primary"
          size="large"
        >
          ＋ 创建内容
        </el-button>
      </router-link>
    </div>
    <section class="library-toolbar">
      <span><strong>{{ total }}</strong> 个任务</span><div class="task-filter">
        <label for="task-status">任务状态</label><select
          id="task-status"
          v-model="status"
          @change="filter"
        >
          <option value="">
            全部状态
          </option><option
            v-for="(label,key) in statusLabels"
            :key="key"
            :value="key"
          >
            {{ label }}
          </option>
        </select><el-button
          :loading="busy"
          @click="load"
        >
          刷新
        </el-button>
      </div>
    </section>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      role="alert"
    />
    <p
      v-if="busy && !items.length"
      role="status"
    >
      正在读取任务…
    </p>
    <section
      v-if="items.length"
      class="task-list"
    >
      <article
        v-for="task in items"
        :key="task.id"
        class="task-row"
      >
        <div
          class="task-symbol"
          aria-hidden="true"
        >
          ✧
        </div>
        <div class="task-row-main">
          <router-link :to="'/tasks/' + task.id">
            <h2>{{ task.product_name }}</h2>
          </router-link><p>{{ task.model_name }} · {{ taskTime(task.created_at) }}</p><span class="muted">Mock · 已保存 {{ task.result_count }} / {{ task.requested_count }} 张</span>
        </div>
        <span :class="['task-status',task.status]">{{ statusLabels[task.status] }}</span>
        <div class="task-actions">
          <router-link :to="'/tasks/' + task.id">
            <el-button>查看结果</el-button>
          </router-link><el-button
            text
            type="danger"
            :disabled="task.is_active"
            :loading="removing === task.id"
            @click="remove(task)"
          >
            删除
          </el-button>
        </div>
      </article>
    </section>
    <section
      v-else-if="!busy && !error"
      class="empty-state"
    >
      <span>▧</span><div>
        <h2>这里还没有任务</h2><p>选好模特与商品，开始第一组 Mock 创作。</p><router-link to="/create-content">
          创建内容 →
        </router-link>
      </div>
    </section>
    <el-pagination
      v-if="total > 12"
      v-model:current-page="page"
      :page-size="12"
      :total="total"
      layout="prev, pager, next"
      @current-change="load"
    />
  </WorkspaceLayout>
</template>

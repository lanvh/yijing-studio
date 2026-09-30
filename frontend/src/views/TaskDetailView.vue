<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { generationApi } from '../api/generation'
import { errorMessage } from '../api/client'
import { statusLabels, taskTime, type GenerationTask, type GenerationResult, type ContentCopy } from '../types/generation'
const route = useRoute()
const task = ref<GenerationTask | null>(null), error = ref(''), notice = ref('')
const loading = ref(false), busy = ref(false), preview = ref<GenerationResult | null>(null)
const draft = reactive({ title:'', caption:'', hashtags:'', product_summary:'', styling_notes:'' })
const saved = ref('')
const dirty = computed(() => JSON.stringify(draft) !== saved.value && !!task.value?.copy)
const selected = computed(() => task.value?.results.filter(r => r.is_selected).length || 0)
let timer: ReturnType<typeof setTimeout> | undefined, disposed = false, sequence = 0
function applyCopy(copy: ContentCopy | null) {
  if (!copy) return
  Object.assign(draft,{title:copy.title, caption:copy.caption, hashtags:copy.hashtags.join('\n'), product_summary:copy.product_summary, styling_notes:copy.styling_notes})
  saved.value = JSON.stringify(draft)
}
async function load() {
  clearTimeout(timer)
  const current = ++sequence
  loading.value = true; error.value = ''
  try {
    const result = await generationApi.get(String(route.params.id))
    if (disposed || current !== sequence) return
    const retainDraft = dirty.value
    task.value = result
    if (!retainDraft) applyCopy(result.copy)
    if (result.is_active) timer = setTimeout(() => { if (!disposed) void load() },3000)
  } catch (cause) { if (current === sequence) error.value = errorMessage(cause) }
  finally { if (current === sequence) loading.value = false }
}
async function act(action: () => Promise<void>) {
  if (busy.value) return
  clearTimeout(timer)
  busy.value = true; error.value = ''; notice.value = ''
  try { await action() }
  catch (cause) {
    // ZIP errors use a blob transport, so decode the server's safe message.
    const blob = (cause as { response?: { data?: unknown } })?.response?.data
    if (blob instanceof Blob) {
      try { error.value = JSON.parse(await blob.text()).detail || '下载失败，请重试。' }
      catch { error.value = '下载失败，请重试。' }
    } else error.value = errorMessage(cause)
  } finally { busy.value = false }
}
async function retry() {
  await act(async () => {
    task.value = await generationApi.retry(String(route.params.id))
    if (!dirty.value) applyCopy(task.value.copy)
    await load()
  })
}
async function selectResult(result: GenerationResult, event: Event) {
  const input = event.target as HTMLInputElement
  await act(async () => { const updated = await generationApi.select(result.id,!result.is_selected); Object.assign(result,updated) })
  input.checked = result.is_selected
}
async function deleteResult(result: GenerationResult) {
  try { await ElMessageBox.confirm('该图片将从任务中移除，无法撤销。','删除图片',{confirmButtonText:'确认删除',cancelButtonText:'取消',type:'warning'}) }
  catch { return }
  await act(async () => { await generationApi.removeResult(result.id); await load() })
}
async function saveCopy() {
  await act(async () => {
    const copy = await generationApi.copy(String(route.params.id),{ ...draft, hashtags:draft.hashtags.split('\n').map(t => t.trim().replace(/^#+/, '')).filter(Boolean) })
    if (task.value) task.value.copy = copy
    applyCopy(copy); notice.value = '文案已保存。'
  })
}
async function regenerate() {
  try { await ElMessageBox.confirm('将用素材资料重新生成本地文案草稿，并覆盖已有文案。','重新生成文案',{confirmButtonText:'确认重新生成',cancelButtonText:'取消'}) }
  catch { return }
  await act(async () => {
    const copy = await generationApi.regenerateCopy(String(route.params.id))
    if (task.value) task.value.copy = copy
    applyCopy(copy); notice.value = '文案草稿已重新生成。'
  })
}
async function download() {
  await act(async () => {
    const blob = await generationApi.export(String(route.params.id))
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url; anchor.download = 'ai-seed-' + route.params.id + '.zip'
    document.body.append(anchor); anchor.click(); anchor.remove()
    setTimeout(() => URL.revokeObjectURL(url),10000)
    notice.value = '素材包已下载。发布前请人工核对图片和文案。'
  })
}
function closePreview(open: boolean) { if (!open) preview.value = null }
function beforeUnload(event: BeforeUnloadEvent) { if (dirty.value) { event.preventDefault(); event.returnValue = '' } }
window.addEventListener('beforeunload',beforeUnload)
onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  try { await ElMessageBox.confirm('文案修改尚未保存，离开后将丢失。','离开结果页',{confirmButtonText:'放弃修改并离开',cancelButtonText:'继续编辑'}); return true }
  catch { return false }
})
watch(() => route.params.id, () => { task.value = null; saved.value = ''; void load() },{immediate:true})
onUnmounted(() => { disposed = true; sequence++; clearTimeout(timer); window.removeEventListener('beforeunload',beforeUnload) })
</script>
<template>
  <WorkspaceLayout title="创作结果">
    <router-link
      class="back-link"
      to="/tasks"
    >
      ← 返回生成记录
    </router-link>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      role="alert"
    />
    <el-alert
      v-if="notice"
      :title="notice"
      type="success"
      :closable="false"
      role="status"
    />
    <p
      v-if="loading && !task"
      role="status"
    >
      正在读取创作结果…
    </p>
    <el-button
      v-if="error && !task"
      @click="load"
    >
      重新加载
    </el-button>
    <template v-if="task">
      <div class="page-heading">
        <div>
          <p class="eyebrow">
            FROM IDEA TO CONTENT
          </p><h1>{{ task.product_name }}</h1><p class="muted">
            {{ task.model_name }} · {{ taskTime(task.created_at) }} · 第 {{ task.attempt }} 次尝试
          </p>
        </div><span :class="['task-status',task.status]">{{ statusLabels[task.status] }}</span>
      </div>
      <div class="mock-notice">
        <strong>Mock 演示结果</strong><span>这些图片是本地生成的示意素材，不是真实 AI 换装。文件检查通过不代表人物、商品或美观度已验证。</span>
      </div>
      <section
        v-if="task.status !== 'SUCCEEDED'"
        class="task-progress"
      >
        <h2>{{ task.is_active ? '正在生成并保存图片…' : statusLabels[task.status] }}</h2>
        <p>{{ task.error_message || (task.is_active ? '页面会自动刷新，离开后也可从生成记录回来查看。' : '上次执行可能中断，可尝试继续生成。') }}</p>
        <p>已保存 {{ task.result_count }} / {{ task.requested_count }} 张。已有图片和编辑过的文案会保留。</p>
        <el-button
          v-if="task.can_retry"
          :loading="busy"
          type="primary"
          @click="retry"
        >
          重试并补齐图片
        </el-button>
        <p
          v-else-if="!task.is_active"
          class="muted"
        >
          最多尝试 3 次。可使用已有结果，或创建新任务。
        </p>
        <el-button
          :loading="loading"
          :disabled="busy"
          @click="load"
        >
          刷新状态
        </el-button>
      </section>
      <div class="section-title">
        <h2>挑选本次作品</h2><span class="muted">已选 {{ selected }} / {{ task.results.length }} 张 · 第一张选中图片作为封面</span>
      </div>
      <section
        v-if="task.results.length"
        class="result-grid"
      >
        <article
          v-for="(result,index) in task.results"
          :key="result.id"
          :class="['result-card',{selected:result.is_selected}]"
        >
          <button
            class="result-preview"
            :aria-label="'预览结果图片 ' + (index+1)"
            @click="preview = result"
          >
            <img
              :src="result.image_url"
              :alt="'Mock 示意图 ' + (index+1)"
            ><span>MOCK / {{ String(index+1).padStart(2,'0') }}</span>
          </button>
          <div class="result-card-body">
            <label class="result-select"><input
              type="checkbox"
              :checked="result.is_selected"
              :disabled="busy || task.is_active"
              :aria-label="'选择图片 ' + (index+1)"
              @change="selectResult(result, $event)"
            >加入素材包</label><p class="muted">
              {{ result.metadata.file_check.width }} × {{ result.metadata.file_check.height }} · 文件检查通过
            </p><div class="task-actions">
              <a
                :href="result.image_url"
                :download="'mock-' + (index+1) + '.jpg'"
              >下载图片</a><el-button
                text
                type="danger"
                :disabled="busy || task.is_active"
                @click="deleteResult(result)"
              >
                删除图片
              </el-button>
            </div>
          </div>
        </article>
      </section>
      <div
        v-else
        class="empty-state"
      >
        <span>▧</span><p>暂无图片。可重试生成，或创建新任务。</p>
      </div>
      <section
        v-if="task.copy"
        class="form-panel copy-panel"
      >
        <div class="section-title">
          <div>
            <p class="step-number">
              WORDS TO GO WITH YOUR IMAGES
            </p><h2>让文案也成为你的表达</h2>
          </div><span class="muted">{{ dirty ? '有未保存修改' : task.copy.source === 'user_edited' ? '已保存你的编辑' : '本地模板草稿' }}</span>
        </div>
        <p class="muted">
          草稿仅使用已填写的商品资料，不代表真实试穿或使用体验。发布前请核对。
        </p>
        <form @submit.prevent="saveCopy">
          <fieldset :disabled="busy || task.is_active">
            <label for="copy-title">标题</label><input
              id="copy-title"
              v-model="draft.title"
              maxlength="200"
              required
            >
            <label for="copy-caption">正文</label><textarea
              id="copy-caption"
              v-model="draft.caption"
              rows="6"
              maxlength="5000"
              required
            />
            <div class="form-grid">
              <div>
                <label for="copy-tags">话题标签（每行一个，最多 20 个）</label><textarea
                  id="copy-tags"
                  v-model="draft.hashtags"
                  rows="4"
                  maxlength="1220"
                />
              </div><div>
                <label for="copy-summary">商品摘要</label><textarea
                  id="copy-summary"
                  v-model="draft.product_summary"
                  rows="4"
                  maxlength="2000"
                />
              </div>
            </div>
            <label for="copy-styling">搭配建议</label><textarea
              id="copy-styling"
              v-model="draft.styling_notes"
              rows="3"
              maxlength="2000"
            />
            <div class="task-actions">
              <el-button
                type="primary"
                native-type="submit"
                :loading="busy"
                :disabled="task.is_active || !task.results.length"
              >
                保存文案
              </el-button><el-button
                :disabled="busy || task.is_active || !task.results.length"
                @click="regenerate"
              >
                重新生成草稿
              </el-button>
            </div>
          </fieldset>
        </form>
      </section>
      <section class="creation-submit">
        <div>
          <h2>把这组灵感带走</h2><p class="muted">
            {{ selected }} 张图片 · 标题、正文、话题 · 商品资料与文件清单
          </p><p
            v-if="dirty"
            class="save-hint"
          >
            请先保存文案修改，再下载素材包。
          </p>
        </div><el-button
          type="primary"
          size="large"
          :loading="busy"
          :disabled="!selected || dirty || task.is_active || !task.copy"
          @click="download"
        >
          下载 ZIP 素材包
        </el-button>
      </section>
      <p class="muted">
        素材需由你手动审核与发布。系统不会自动发布到任何平台。
      </p>
    </template>
    <el-dialog
      :model-value="!!preview"
      title="Mock 图片预览"
      width="min(760px, 94vw)"
      @update:model-value="closePreview"
    >
      <img
        v-if="preview"
        class="full-result"
        :src="preview.image_url"
        alt="Mock 结果大图"
      >
    </el-dialog>
  </WorkspaceLayout>
</template>

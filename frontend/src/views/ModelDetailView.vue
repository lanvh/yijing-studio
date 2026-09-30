<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import ModelPortrait from '../components/ModelPortrait.vue'
import { generationApi } from '../api/generation'
import { modelsApi } from '../api/models'
import { errorMessage } from '../api/client'
import { genderLabels, type AIModel, type ModelLimits, type ReferenceImage } from '../types/models'

const route = useRoute()
const router = useRouter()
const model = ref<AIModel | null>(null)
const limits = ref<ModelLimits | null>(null)
const busy = ref(false)
const error = ref('')
const uploading = ref(false)
const uploadProgress = ref(0)
const consent = ref(false)
const removing = ref('')
const deletingModel = ref(false)
const preview = ref<ReferenceImage | null>(null)
const notice = ref('')
const generating = ref(false)
const provider = ref<Awaited<ReturnType<typeof generationApi.provider>> | null>(null)
function setPreviewOpen(value: boolean) { if (!value) preview.value = null }
async function load() {
  busy.value = true
  error.value = ''
  model.value = null
  try {
    const [record, options, status] = await Promise.all([modelsApi.get(String(route.params.id)), modelsApi.limits(), generationApi.provider()])
    provider.value = status
    model.value = record
    limits.value = options
  } catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
async function generateReference() {
  if (!model.value || generating.value) return
  generating.value = true; error.value = ''; notice.value = ''
  try {
    const image = await modelsApi.generateReference(model.value.id,crypto.randomUUID())
    model.value.reference_images.push(image)
    notice.value = '生成的参考图已保存。'
  } catch (cause) { error.value = errorMessage(cause) }
  finally { generating.value = false }
}
async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !model.value || !limits.value || uploading.value) return
  error.value = ''
  notice.value = ''
  if (!consent.value) { error.value = '请先确认图片来源与使用权。'; return }
  if (!limits.value.allowed_image_types.includes(file.type) || !/\.(jpe?g|png|webp)$/i.test(file.name)) {
    error.value = '请选择 JPG、PNG 或 WebP 图片。'; return
  }
  if (file.size > limits.value.max_image_size_mb * 1024 * 1024) {
    error.value = '单张图片不能超过 ' + limits.value.max_image_size_mb + ' MB。'; return
  }
  uploading.value = true
  uploadProgress.value = 0
  try {
    const image = await modelsApi.upload(model.value.id, file, consent.value, value => { uploadProgress.value = value })
    model.value.reference_images.push(image)
    uploadProgress.value = 100
    notice.value = '参考图已保存。'
  } catch (cause) { error.value = errorMessage(cause) }
  finally { uploading.value = false }
}
async function removeImage(image: ReferenceImage) {
  try {
    await ElMessageBox.confirm('移除后将删除这张参考图文件。', '移除参考图', {
      confirmButtonText: '确认移除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  removing.value = image.id
  error.value = ''
  notice.value = ''
  try {
    await modelsApi.removeImage(image.image_url)
    if (model.value) model.value.reference_images = model.value.reference_images.filter(item => item.id !== image.id)
    notice.value = '参考图已移除。'
  } catch (cause) { error.value = errorMessage(cause) }
  finally { removing.value = '' }
}
async function removeModel() {
  if (!model.value) return
  try {
    await ElMessageBox.confirm('将删除「' + model.value.name + '」的资料及全部参考图，此操作无法撤销。', '删除模特', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  deletingModel.value = true
  try { await modelsApi.remove(model.value.id); await router.replace('/models') }
  catch (cause) { error.value = errorMessage(cause) }
  finally { deletingModel.value = false }
}
watch(() => route.params.id, load, { immediate: true })
</script>
<template>
  <WorkspaceLayout title="模特资料">
    <router-link
      class="back-link"
      to="/models"
    >
      ← 返回模特库
    </router-link>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      role="alert"
      class="section-alert"
    />
    <div
      v-if="busy"
      class="library-loading"
      role="status"
    >
      正在读取人物资料…
    </div>
    <div
      v-else-if="!model"
      class="library-empty"
    >
      <h2>暂时无法显示模特</h2><p>请重试，或返回模特库查看已有资料。</p><el-button @click="load">
        重新加载
      </el-button>
    </div>
    <template v-else>
      <div class="page-heading">
        <div>
          <p class="eyebrow">
            CHARACTER PROFILE
          </p><h1>{{ model.name }}</h1><p class="muted">
            AI 虚拟成人形象 · 仅自己可见
          </p>
        </div>
        <div class="heading-actions">
          <router-link :to="'/models/' + model.id + '/edit'">
            <el-button :disabled="uploading || !!removing || deletingModel">
              编辑资料
            </el-button>
          </router-link><el-button
            type="danger"
            plain
            :loading="deletingModel"
            :disabled="uploading || !!removing"
            @click="removeModel"
          >
            删除模特
          </el-button>
        </div>
      </div>
      <section class="model-summary">
        <ModelPortrait
          :name="model.name"
          :src="model.reference_images[0]?.image_url"
        />
        <div class="summary-body">
          <span class="eyebrow">THE CHARACTER AT A GLANCE</span><h2>人物档案</h2>
          <dl class="profile-facts">
            <div><dt>性别</dt><dd>{{ genderLabels[model.gender] }}</dd></div><div><dt>年龄段</dt><dd>{{ model.age_range }} 岁</dd></div>
            <div><dt>身高</dt><dd>{{ model.height ? model.height + ' cm' : '未填写' }}</dd></div><div><dt>体型</dt><dd>{{ model.body_type || '未填写' }}</dd></div>
            <div><dt>肤色</dt><dd>{{ model.skin_tone || '未填写' }}</dd></div><div><dt>发色</dt><dd>{{ model.hair_color || '未填写' }}</dd></div>
            <div><dt>发型</dt><dd>{{ model.hair_style || '未填写' }}</dd></div><div><dt>风格</dt><dd>{{ model.style || '未填写' }}</dd></div>
          </dl>
          <p class="profile-description">
            {{ model.description || '还没有人物描述。可以在编辑资料中补充。' }}
          </p>
        </div>
      </section>
      <section class="reference-section">
        <div class="section-title">
          <h2>参考图片 <span class="reference-count">{{ model.reference_images.length }} / {{ limits?.max_model_images }}</span></h2><span class="muted">第一张图片作为模特封面</span>
        </div>
        <p class="reference-intro">
          建议搭配正面、侧面与全身图，让人物特征更清晰。可以上传已有虚拟人物图片，也可按人物档案生成新的参考图。
        </p>
        <div class="creation-submit">
          <div>
            <strong>{{ provider?.mock ? '生成 Mock 参考图' : '生成 AI 虚拟模特参考图' }}</strong>
            <p>{{ provider?.mock ? '按档案生成本地示意图，验证人物素材流程。' : '生成原创虚拟成人形象；使用已配置的图片服务，可能产生费用。' }}</p>
          </div>
          <el-button
            type="primary"
            :loading="generating"
            :disabled="!provider?.available || uploading || !!removing || model.reference_images.length >= (limits?.max_model_images || 8)"
            @click="generateReference"
          >
            生成参考图
          </el-button>
        </div>
        <router-link :to="{ path: '/create-content', query: { model: model.id } }">
          使用这个模特创建内容 →
        </router-link>
        <div class="upload-panel">
          <div>
            <h3>添加人物参考图</h3><p>JPG / PNG / WebP · 每张不超过 {{ limits?.max_image_size_mb }} MB · 保存为清晰的 JPEG 图片</p>
            <el-checkbox
              v-model="consent"
              :disabled="uploading"
            >
              我确认这是有使用权的 AI 虚拟成人形象，非真人照片。
            </el-checkbox>
          </div>
          <label
            class="upload-button"
            :class="{ 'is-disabled': !consent || uploading || !!removing || model.reference_images.length >= (limits?.max_model_images || 0) }"
          >
            {{ uploading ? '上传中 ' + uploadProgress + '%' : '＋ 上传参考图' }}
            <input
              type="file"
              aria-label="上传参考图"
              accept=".jpg,.jpeg,.png,.webp"
              :disabled="!consent || uploading || !!removing || model.reference_images.length >= (limits?.max_model_images || 0)"
              @change="upload"
            >
          </label>
        </div>
        <p
          v-if="model.reference_images.length >= (limits?.max_model_images || 8)"
          class="upload-limit-note"
        >
          已达到参考图上限，可移除旧图后再上传。
        </p>
        <p
          v-if="notice"
          class="success-notice"
          role="status"
        >
          {{ notice }}
        </p>
        <div
          v-if="model.reference_images.length"
          class="reference-grid"
        >
          <article
            v-for="(image, index) in model.reference_images"
            :key="image.id"
            class="reference-card"
          >
            <button
              class="reference-preview-button"
              :aria-label="'预览参考图 ' + (index + 1)"
              @click="preview = image"
            >
              <img
                :src="image.image_url"
                :alt="model.name + ' 参考图 ' + (index + 1)"
                loading="lazy"
              ><span
                v-if="index === 0"
                class="cover-badge"
              >封面</span>
            </button>
            <div class="reference-caption">
              <span>{{ image.metadata.width }} × {{ image.metadata.height }}</span><el-button
                text
                type="danger"
                :loading="removing === image.id"
                :disabled="uploading || !!removing"
                @click="removeImage(image)"
              >
                移除
              </el-button>
            </div>
          </article>
        </div>
        <div
          v-else
          class="reference-empty"
        >
          <span>▧</span><h3>为这个角色，留下第一张参考图。</h3><p>确认图片来源后，就可以开始上传。</p>
        </div>
      </section>
    </template>
    <el-dialog
      :model-value="!!preview"
      title="参考图预览"
      width="min(860px, 92vw)"
      @update:model-value="setPreviewOpen"
    >
      <img
        v-if="preview"
        :src="preview.image_url"
        alt="参考图放大预览"
        class="full-reference"
      >
    </el-dialog>
  </WorkspaceLayout>
</template>

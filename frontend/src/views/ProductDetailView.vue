<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import ProductCover from '../components/ProductCover.vue'
import { generationApi } from '../api/generation'
import { productsApi } from '../api/products'
import { errorMessage } from '../api/client'
import { categoryLabels, type Product, type ProductLimits, type ProductImage } from '../types/products'

const route = useRoute()
const router = useRouter()
const product = ref<Product | null>(null)
const limits = ref<ProductLimits | null>(null)
const busy = ref(false)
const error = ref('')
const uploading = ref(false)
const uploadProgress = ref(0)
const consent = ref(false)
const removing = ref('')
const deletingProduct = ref(false)
const preview = ref<ProductImage | null>(null)
const notice = ref('')
const analyzing = ref(false)
const provider = ref<Awaited<ReturnType<typeof generationApi.provider>> | null>(null)
function setPreviewOpen(value: boolean) { if (!value) preview.value = null }
async function load() {
  busy.value = true
  error.value = ''
  product.value = null
  try {
    const [record, options, status] = await Promise.all([productsApi.get(String(route.params.id)), productsApi.limits(), generationApi.provider()])
    provider.value = status
    product.value = record
    limits.value = options
  } catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !product.value || !limits.value || uploading.value || analyzing.value) return
  error.value = ''
  notice.value = ''
  if (!consent.value) { error.value = '请先确认图片来源与使用权。'; return }
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || !/\.(jpe?g|png|webp)$/i.test(file.name)) {
    error.value = '请选择 JPG、PNG 或 WebP 图片。'; return
  }
  if (file.size > limits.value.max_image_size_mb * 1024 * 1024) {
    error.value = '单张图片不能超过 ' + limits.value.max_image_size_mb + ' MB。'; return
  }
  uploading.value = true
  uploadProgress.value = 0
  try {
    const updated = await productsApi.upload(product.value.id, file, consent.value, value => { uploadProgress.value = value })
    product.value = updated
    uploadProgress.value = 100
    notice.value = '商品图片已保存。'
  } catch (cause) { error.value = errorMessage(cause) }
  finally { uploading.value = false }
}
async function removeImage(image: ProductImage) {
  try {
    await ElMessageBox.confirm('移除后将同时删除这张图片的原文件与预览图。', '移除商品图片', {
      confirmButtonText: '确认移除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  removing.value = image.id
  error.value = ''
  notice.value = ''
  try {
    product.value = await productsApi.removeImage(image.image_url)
    notice.value = '商品图片已移除。'
  } catch (cause) { error.value = errorMessage(cause) }
  finally { removing.value = '' }
}
async function removeProduct() {
  if (!product.value) return
  try {
    await ElMessageBox.confirm('将删除「' + product.value.name + '」的资料及全部商品图片，此操作无法撤销。', '删除商品', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  deletingProduct.value = true
  try { await productsApi.remove(product.value.id); await router.replace('/products') }
  catch (cause) { error.value = errorMessage(cause) }
  finally { deletingProduct.value = false }
}
async function analyze() {
  if (!product.value || analyzing.value) return
  analyzing.value = true
  error.value = ''
  try { product.value = await productsApi.analyze(product.value.id); notice.value = '特征已重新整理。' }
  catch (cause) { error.value = errorMessage(cause) }
  finally { analyzing.value = false }
}
function originalUrl(image: ProductImage) {
  return product.value?.original_images.find(item => item.id === image.metadata.original_image_id)?.image_url
}
watch(() => route.params.id, load, { immediate: true })
</script>
<template>
  <WorkspaceLayout title="商品资料">
    <router-link
      class="back-link"
      to="/products"
    >
      ← 返回商品库
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
      正在读取商品资料…
    </div>
    <div
      v-else-if="!product"
      class="library-empty"
    >
      <h2>暂时无法显示商品</h2><p>请重试，或返回商品库查看已有资料。</p><el-button @click="load">
        重新加载
      </el-button>
    </div>
    <template v-else>
      <div class="page-heading">
        <div>
          <p class="eyebrow">
            PRODUCT PROFILE
          </p><h1>{{ product.name }}</h1><p class="muted">
            商品资料与图片 · 仅自己可见
          </p>
        </div>
        <div class="heading-actions">
          <router-link :to="'/products/' + product.id + '/edit'">
            <el-button :disabled="uploading || analyzing || !!removing || deletingProduct">
              编辑资料
            </el-button>
          </router-link><el-button
            type="danger"
            plain
            :loading="deletingProduct"
            :disabled="uploading || analyzing || !!removing"
            @click="removeProduct"
          >
            删除商品
          </el-button>
        </div>
      </div>
      <section class="model-summary">
        <ProductCover
          :name="product.name"
          :src="product.processed_images[0]?.image_url"
        />
        <div class="summary-body">
          <span class="eyebrow">THE PRODUCT AT A GLANCE</span><h2>商品档案</h2>
          <dl class="profile-facts">
            <div><dt>类别</dt><dd>{{ categoryLabels[product.category] }}</dd></div>
            <div><dt>品牌</dt><dd>{{ product.brand || '未填写' }}</dd></div>
            <div><dt>颜色</dt><dd>{{ product.color || '未填写' }}</dd></div>
            <div><dt>商品图片</dt><dd>{{ product.processed_images.length }} 张</dd></div>
          </dl>
          <p class="profile-description">
            {{ product.description || '还没有商品描述。可以在编辑资料中补充。' }}
          </p>
        </div>
      </section>
      <section class="product-features">
        <div class="section-title">
          <h2>商品特征</h2><el-button
            :loading="analyzing"
            :disabled="uploading || !!removing || deletingProduct"
            @click="analyze"
          >
            重新整理特征
          </el-button>
        </div>
        <p>以下特征来自你填写的资料。编辑商品可补充或纠正。</p>
        <dl class="profile-facts">
          <div><dt>材质</dt><dd>{{ product.product_features.confirmed.material || '未填写' }}</dd></div>
          <div><dt>图案</dt><dd>{{ product.product_features.confirmed.pattern || '未填写' }}</dd></div>
          <div><dt>Logo</dt><dd>{{ product.product_features.confirmed.logo_description || '未填写' }}</dd></div>
          <div><dt>形状与结构</dt><dd>{{ product.product_features.confirmed.shape || '未填写' }}</dd></div>
        </dl>
        <ul v-if="product.product_features.confirmed.critical_features.length">
          <li
            v-for="feature in product.product_features.confirmed.critical_features"
            :key="feature"
          >
            {{ feature }}
          </li>
        </ul>
        <template v-if="product.product_features.image_observations.length">
          <h3>图片色板</h3><p>色板由整张图片统计，包含背景，不代表商品主色。</p>
          <div
            v-for="(observation, index) in product.product_features.image_observations"
            :key="observation.image_id"
            class="product-palette"
          >
            <span class="product-swatch">图片 {{ index + 1 }}</span><span
              v-for="color in observation.palette"
              :key="color"
              class="product-swatch"
            ><i :style="{ backgroundColor: color }" />{{ color }}</span>
          </div>
        </template>
        <p v-else>
          添加图片后，将展示图片色板。
        </p>
      </section>
      <section
        v-if="product.product_features.ai_analysis"
        class="form-panel"
      >
        <h2>AI 图片分析 · 待确认</h2>
        <p v-if="product.product_features.ai_analysis.status === 'failed'">
          {{ product.product_features.ai_analysis.message }}，可点击重新整理特征重试。
        </p>
        <template v-if="product.product_features.ai_analysis.findings">
          <p>以下仅为图片观察建议，不会自动改写商品事实。请核对后在编辑资料中填写确认信息。</p>
          <dl class="profile-facts">
            <div><dt>可见颜色</dt><dd>{{ product.product_features.ai_analysis.findings.colors.join('、') || '未知' }}</dd></div>
            <div><dt>图案</dt><dd>{{ product.product_features.ai_analysis.findings.pattern || '未知' }}</dd></div>
            <div><dt>Logo 位置</dt><dd>{{ product.product_features.ai_analysis.findings.logo_description || '未知' }}</dd></div>
            <div><dt>结构</dt><dd>{{ product.product_features.ai_analysis.findings.shape || '未知' }}</dd></div>
            <div><dt>表面外观（非材质结论）</dt><dd>{{ product.product_features.ai_analysis.findings.material_appearance || '未知' }}</dd></div>
          </dl>
          <p>{{ product.product_features.ai_analysis.findings.critical_features.join('；') }}</p>
          <p class="muted">
            {{ product.product_features.ai_analysis.findings.uncertainties.join('；') }}
          </p>
        </template>
      </section>
      <router-link :to="{ path: '/create-content', query: { product: product.id } }">
        使用这个商品创建内容 →
      </router-link>
      <section class="reference-section">
        <div class="section-title">
          <h2>商品图片 <span class="reference-count">{{ product.processed_images.length }} / {{ limits?.max_product_images }}</span></h2><span class="muted">第一张图片作为商品封面</span>
        </div>
        <p class="reference-intro">
          添加正面、侧面与局部细节图片。原文件保留供下载，预览图会修正方向并清理元数据。
        </p>
        <p
          v-if="provider?.copy_mode === 'openai'"
          class="mock-notice"
        >
          已启用 AI 商品分析。上传后将把最多前 4 张商品预览图发送至已配置服务，产生相应分析费用。
        </p>
        <div class="upload-panel">
          <div>
            <h3>添加商品图片</h3><p>JPG / PNG / WebP · 每张不超过 {{ limits?.max_image_size_mb }} MB · 保留原图并生成 JPEG 预览</p>
            <el-checkbox
              v-model="consent"
              :disabled="uploading"
            >
              我确认拥有商品图片的使用权，或已获授权。
            </el-checkbox>
          </div>
          <label
            class="upload-button"
            :class="{ 'is-disabled': !consent || uploading || analyzing || !!removing || product.processed_images.length >= (limits?.max_product_images || 0) }"
          >
            {{ uploading ? '上传中 ' + uploadProgress + '%' : '＋ 上传商品图片' }}
            <input
              type="file"
              aria-label="上传商品图片"
              accept=".jpg,.jpeg,.png,.webp"
              :disabled="!consent || uploading || analyzing || !!removing || product.processed_images.length >= (limits?.max_product_images || 0)"
              @change="upload"
            >
          </label>
        </div>
        <p
          v-if="product.processed_images.length >= (limits?.max_product_images || 8)"
          class="upload-limit-note"
        >
          已达到商品图片上限，可移除旧图后再上传。
        </p>
        <p
          v-if="notice"
          class="success-notice"
          role="status"
        >
          {{ notice }}
        </p>
        <div
          v-if="product.processed_images.length"
          class="reference-grid product-images"
        >
          <article
            v-for="(image, index) in product.processed_images"
            :key="image.id"
            class="reference-card"
          >
            <button
              class="reference-preview-button"
              :aria-label="'预览商品图片 ' + (index + 1)"
              @click="preview = image"
            >
              <img
                :src="image.image_url"
                :alt="product.name + ' 商品图片 ' + (index + 1)"
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
                :disabled="uploading || analyzing || !!removing"
                @click="removeImage(image)"
              >
                移除
              </el-button>
            </div>
            <a
              v-if="originalUrl(image)"
              :href="originalUrl(image)"
              class="original-link"
              download
            >下载原图</a>
          </article>
        </div>
        <div
          v-else
          class="reference-empty"
        >
          <span>▧</span><h3>添加第一张图片，让商品细节更清晰。</h3><p>确认图片来源后，就可以开始上传。</p>
        </div>
      </section>
    </template>
    <el-dialog
      :model-value="!!preview"
      title="商品图片预览"
      width="min(860px, 92vw)"
      @update:model-value="setPreviewOpen"
    >
      <img
        v-if="preview"
        :src="preview.image_url"
        alt="商品图片放大预览"
        class="full-reference"
      >
    </el-dialog>
  </WorkspaceLayout>
</template>

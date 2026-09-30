<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import ModelPortrait from '../components/ModelPortrait.vue'
import ProductCover from '../components/ProductCover.vue'
import { modelsApi } from '../api/models'
import { productsApi } from '../api/products'
import { generationApi } from '../api/generation'
import { errorMessage } from '../api/client'
import type { AIModel } from '../types/models'
import type { Product } from '../types/products'
import type { GenerationOptions } from '../types/generation'

const router = useRouter()
const route = useRoute()
const models = ref<AIModel[]>([]), products = ref<Product[]>([])
const options = ref<GenerationOptions | null>(null)
const form = reactive({ model_id: '', product_id: '', scene: 'studio', style: 'casual', pose: 'front_standing', requested_count: 4 })
const modelQuery = ref(''), productQuery = ref('')
const selectedModel = ref<AIModel | null>(null), selectedProduct = ref<Product | null>(null)
const busy = ref(false), loading = ref(true), searching = ref(false), error = ref('')
const provider = ref<Awaited<ReturnType<typeof generationApi.provider>> | null>(null)
const requestKey = ref(crypto.randomUUID())
const ready = computed(() => !!selectedModel.value?.reference_images.length && !!selectedProduct.value?.processed_images.length)
watch(form, () => { requestKey.value = crypto.randomUUID() })
watch(() => form.model_id, id => { selectedModel.value = models.value.find(m => m.id === id) || null })
watch(() => form.product_id, id => { selectedProduct.value = products.value.find(p => p.id === id) || null })
async function search() {
  searching.value = true
  error.value = ''
  try {
    const [m,p] = await Promise.all([modelsApi.list(modelQuery.value,0,100), productsApi.list(productQuery.value,'',0,100)])
    models.value = m.items; products.value = p.items
    if (selectedModel.value && !models.value.some(m => m.id === form.model_id)) models.value.unshift(selectedModel.value)
    if (selectedProduct.value && !products.value.some(p => p.id === form.product_id)) products.value.unshift(selectedProduct.value)
  } catch (cause) { error.value = errorMessage(cause) }
  finally { searching.value = false }
}
async function initialize() {
  loading.value = true
  try { const [presets, status] = await Promise.all([generationApi.options(), generationApi.provider()]); options.value = presets; provider.value = status; await search()
    if (typeof route.query.model === 'string') {
      const record = await modelsApi.get(route.query.model)
      if (!models.value.some(m => m.id === record.id)) models.value.unshift(record)
      form.model_id = record.id
    }
    if (typeof route.query.product === 'string') {
      const record = await productsApi.get(route.query.product)
      if (!products.value.some(p => p.id === record.id)) products.value.unshift(record)
      form.product_id = record.id
    } }
  catch (cause) { error.value = errorMessage(cause) }
  finally { loading.value = false }
}
async function submit() {
  if (!ready.value || busy.value || !provider.value?.available) return
  busy.value = true; error.value = ''
  try {
    const task = await generationApi.create({ ...form, request_key: requestKey.value })
    await router.push('/tasks/' + task.id)
  } catch (cause) { error.value = errorMessage(cause) + ' 如提交中断，可先查看生成记录；保持参数不变再次提交不会重复创建。' }
  finally { busy.value = false }
}
onMounted(initialize)
</script>
<template>
  <WorkspaceLayout title="创建内容">
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          MAKE SOMETHING YOURS
        </p><h1>把人物、好物与灵感放在一起。</h1><p class="muted">
          选好素材与场景，生成一组可整理、可下载的演示作品。
        </p>
      </div><router-link to="/tasks">
        查看生成记录 →
      </router-link>
    </div>
    <div class="mock-notice">
      <strong>{{ provider?.mock ? 'Mock 演示模式' : 'AI 图片生成' }}</strong><span>{{ provider?.mock ? '使用本地示意图走通流程，不进行真实换装，不调用付费图片服务。' : '参考图片会发送至已配置的服务生成内容，按服务商规则计费。请核对素材与生成数量。' }}</span>
    </div>
    <el-alert
      v-if="provider && !provider.available"
      :title="provider.message"
      type="warning"
      :closable="false"
    />
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      role="alert"
    />
    <p
      v-if="loading"
      role="status"
    >
      正在读取素材…
    </p>
    <el-button
      v-if="!loading && !options"
      @click="initialize"
    >
      重新加载
    </el-button>
    <form
      v-if="options"
      class="creation-form"
      @submit.prevent="submit"
    >
      <fieldset :disabled="busy || loading">
        <section class="form-panel">
          <p class="step-number">
            01 / MATERIALS
          </p><h2>选择本次创作素材</h2>
          <div class="form-grid">
            <div>
              <label for="model-search">搜索模特名称</label><input
                id="model-search"
                v-model="modelQuery"
                maxlength="100"
                placeholder="输入名称筛选，可留空"
              >
            </div>
            <div>
              <label for="product-search">搜索商品名称</label><input
                id="product-search"
                v-model="productQuery"
                maxlength="100"
                placeholder="输入名称筛选，可留空"
              >
            </div>
          </div>
          <el-button
            :loading="searching"
            :disabled="busy"
            @click="search"
          >
            筛选素材
          </el-button>
          <p class="muted">
            每类显示前 100 项，可按名称筛选查找；每次生成最多使用各自前 8 张参考图。
          </p>
          <div class="form-grid">
            <div>
              <label for="model-choice">AI 模特</label><select
                id="model-choice"
                v-model="form.model_id"
                required
              >
                <option
                  value=""
                  disabled
                >
                  请选择模特
                </option><option
                  v-for="model in models"
                  :key="model.id"
                  :value="model.id"
                >
                  {{ model.name }} · {{ model.reference_images.length }} 张参考图
                </option>
              </select>
              <div
                v-if="selectedModel"
                class="selected-material"
              >
                <ModelPortrait
                  :src="selectedModel.reference_images[0]?.image_url"
                  :name="selectedModel.name"
                /><div>
                  <strong>{{ selectedModel.name }}</strong><p>{{ selectedModel.reference_images.length }} 张参考图</p><router-link :to="'/models/' + selectedModel.id">
                    查看 / 补充参考图 →
                  </router-link>
                </div>
              </div>
              <router-link
                v-else
                to="/models/create"
              >
                还没有模特？新建一个 →
              </router-link>
            </div>
            <div>
              <label for="product-choice">商品</label><select
                id="product-choice"
                v-model="form.product_id"
                required
              >
                <option
                  value=""
                  disabled
                >
                  请选择商品
                </option><option
                  v-for="product in products"
                  :key="product.id"
                  :value="product.id"
                >
                  {{ product.name }} · {{ product.processed_images.length }} 张图片
                </option>
              </select>
              <div
                v-if="selectedProduct"
                class="selected-material"
              >
                <ProductCover
                  :src="selectedProduct.processed_images[0]?.image_url"
                  :name="selectedProduct.name"
                /><div>
                  <strong>{{ selectedProduct.name }}</strong><p>{{ selectedProduct.color || '颜色待补充' }}</p><router-link :to="'/products/' + selectedProduct.id">
                    查看 / 补充商品图片 →
                  </router-link>
                </div>
              </div>
              <router-link
                v-else
                to="/products/create"
              >
                还没有商品？加入商品库 →
              </router-link>
            </div>
          </div>
        </section>
        <section class="form-panel">
          <p class="step-number">
            02 / DIRECTION
          </p><h2>给这组作品一个方向</h2>
          <div class="form-grid">
            <div>
              <label for="scene-choice">场景</label><select
                id="scene-choice"
                v-model="form.scene"
              >
                <option
                  v-for="(label,key) in options.scenes"
                  :key="key"
                  :value="key"
                >
                  {{ label }}
                </option>
              </select>
            </div>
            <div>
              <label for="style-choice">风格</label><select
                id="style-choice"
                v-model="form.style"
              >
                <option
                  v-for="(label,key) in options.styles"
                  :key="key"
                  :value="key"
                >
                  {{ label }}
                </option>
              </select>
            </div>
            <div>
              <label for="pose-choice">姿势</label><select
                id="pose-choice"
                v-model="form.pose"
              >
                <option
                  v-for="(label,key) in options.poses"
                  :key="key"
                  :value="key"
                >
                  {{ label }}
                </option>
              </select>
            </div>
            <div>
              <label for="count-choice">生成张数</label><select
                id="count-choice"
                v-model="form.requested_count"
              >
                <option
                  v-for="count in options.counts"
                  :key="count"
                  :value="count"
                >
                  {{ count }} 张
                </option>
              </select>
            </div>
          </div>
        </section>
        <section class="creation-submit">
          <div>
            <strong>{{ form.requested_count }} 张{{ provider?.mock ? ' Mock 示意图' : ' AI 图片' }} + 文案草稿</strong><p class="muted">
              {{ ready ? '资料已就绪。生成后可选择图片、编辑文案并下载 ZIP。' : '模特和商品都需要至少一张图片。' }}
            </p>
          </div><el-button
            type="primary"
            size="large"
            native-type="submit"
            :loading="busy"
            :disabled="!ready || loading || !provider?.available"
          >
            {{ provider?.mock ? '生成 Mock 内容' : '生成 AI 内容' }}
          </el-button>
        </section>
      </fieldset>
    </form>
    <p
      v-if="busy"
      role="status"
    >
      正在生成并保存结果。任务会保留在生成记录中，请稍候…
    </p>
  </WorkspaceLayout>
</template>

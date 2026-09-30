<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { productsApi } from '../api/products'
import { errorMessage } from '../api/client'
import { categoryLabels, type ProductProfile } from '../types/products'
const route = useRoute()
const router = useRouter()
const productId = computed(() => typeof route.params.id === 'string' ? route.params.id : '')
const editing = computed(() => !!productId.value)
const defaults = (): ProductProfile => ({
  name: '', brand: '', category: 'top', color: '', description: '',
  feature_notes: { material: '', pattern: '', logo_description: '', shape: '', critical_features: [] },
})
const form = reactive<ProductProfile>(defaults())
const criticalText = ref('')
const formRef = ref<FormInstance>()
const busy = ref(false)
const loading = ref(false)
const loadFailed = ref(false)
const error = ref('')
const rules: FormRules = {
  name: [{ required: true, whitespace: true, message: '请输入商品名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择商品类别', trigger: 'change' }],
}
async function load() {
  Object.assign(form, defaults())
  criticalText.value = ''
  error.value = ''
  loadFailed.value = false
  if (!productId.value) return
  loading.value = true
  try {
    const product = await productsApi.get(productId.value)
    for (const key of ['name', 'brand', 'category', 'color', 'description'] as const) Object.assign(form, { [key]: product[key] })
    form.feature_notes = { ...product.product_features.confirmed }
    criticalText.value = form.feature_notes.critical_features.join('\n')
  } catch (cause) { error.value = errorMessage(cause); loadFailed.value = true }
  finally { loading.value = false }
}
async function save() {
  if (busy.value || !(await formRef.value?.validate().catch(() => false))) return
  error.value = ''
  const critical = criticalText.value.split('\n').map(value => value.trim()).filter(Boolean)
  if (critical.length > 20 || critical.some(value => value.length > 200)) {
    error.value = '关键细节最多 20 条，每条不超过 200 字。'; return
  }
  busy.value = true
  try {
    const payload = { ...form, name: form.name.trim(), feature_notes: { ...form.feature_notes, critical_features: critical } }
    const product = editing.value ? await productsApi.update(productId.value, payload) : await productsApi.create(payload)
    await router.replace('/products/' + product.id)
  } catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
watch(productId, load, { immediate: true })
</script>
<template>
  <WorkspaceLayout :title="editing ? '编辑商品' : '新建商品'">
    <router-link
      class="back-link"
      :to="editing ? '/products/' + productId : '/products'"
    >
      ← 返回{{ editing ? '商品详情' : '商品库' }}
    </router-link>
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          PRODUCT PROFILE
        </p><h1>{{ editing ? '把好物的细节，记录完整。' : '从一件值得分享的好物开始。' }}</h1><p class="muted">
          先保存商品资料，再添加清晰的商品图片。
        </p>
      </div>
    </div>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      role="alert"
      class="section-alert"
    />
    <div
      v-if="loading"
      class="library-loading"
      role="status"
    >
      正在读取商品资料…
    </div>
    <el-button
      v-else-if="loadFailed"
      @click="load"
    >
      重新加载
    </el-button>
    <div
      v-else
      class="profile-form-layout"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="profile-form"
        :disabled="busy"
        @submit.prevent="save"
      >
        <section class="form-panel">
          <span class="eyebrow">01 / THE PRODUCT</span><h2>基本信息</h2>
          <el-form-item
            label="商品名称"
            prop="name"
          >
            <el-input
              v-model="form.name"
              maxlength="100"
              show-word-limit
              placeholder="例如：白色低帮运动鞋"
            />
          </el-form-item>
          <div class="form-grid">
            <el-form-item
              label="商品类别"
              prop="category"
            >
              <el-select v-model="form.category">
                <el-option
                  v-for="(label, value) in categoryLabels"
                  :key="value"
                  :label="label"
                  :value="value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="品牌">
              <el-input
                v-model="form.brand"
                maxlength="100"
                placeholder="选填，不确定可以留空"
              />
            </el-form-item>
            <el-form-item label="商品颜色">
              <el-input
                v-model="form.color"
                maxlength="100"
                placeholder="例如：米白色、银色"
              />
            </el-form-item>
          </div>
          <el-form-item label="商品描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              maxlength="2000"
              show-word-limit
              placeholder="记录款式、用途或其他已知信息。"
            />
          </el-form-item>
        </section>
        <section class="form-panel">
          <span class="eyebrow">02 / DETAILS TO KEEP</span><h2>已知商品特征</h2>
          <p class="reference-intro">
            填写你已确认的信息；不确定的特征可以留空。
          </p>
          <div class="form-grid">
            <el-form-item label="材质">
              <el-input
                v-model="form.feature_notes.material"
                maxlength="300"
                placeholder="例如：棉、不锈钢"
              />
            </el-form-item>
            <el-form-item label="图案">
              <el-input
                v-model="form.feature_notes.pattern"
                maxlength="300"
                placeholder="例如：纯色、条纹"
              />
            </el-form-item>
            <el-form-item label="Logo 描述">
              <el-input
                v-model="form.feature_notes.logo_description"
                maxlength="300"
                placeholder="例如：侧面小号刺绣标志"
              />
            </el-form-item>
            <el-form-item label="形状与结构">
              <el-input
                v-model="form.feature_notes.shape"
                maxlength="300"
                placeholder="例如：圆形表盘、双提手"
              />
            </el-form-item>
          </div>
          <el-form-item label="关键细节（每行一条）">
            <el-input
              v-model="criticalText"
              type="textarea"
              :rows="3"
              maxlength="4020"
              placeholder="例如：三条缝线&#10;银色金属扣"
            />
          </el-form-item>
        </section>
        <div class="form-save-row">
          <router-link :to="editing ? '/products/' + productId : '/products'">
            <el-button :disabled="busy">
              取消
            </el-button>
          </router-link><el-button
            type="primary"
            native-type="submit"
            :loading="busy"
          >
            {{ editing ? '保存修改' : '创建商品' }}
          </el-button>
        </div>
      </el-form>
      <aside class="profile-tip">
        <span class="tip-symbol">◇</span><p class="eyebrow">
          EVERY DETAIL MATTERS
        </p><h2>让好物，<br>有一份清晰的档案。</h2><p>类别、颜色和关键细节，帮助你在之后的创作中保持商品特征。</p><div class="tip-divider" /><h3>接下来，添加商品图片</h3><p>优先选择清晰的正面图，补充侧面与局部细节。上传时会保留原图，并准备方便浏览的预览图。</p>
      </aside>
    </div>
  </WorkspaceLayout>
</template>

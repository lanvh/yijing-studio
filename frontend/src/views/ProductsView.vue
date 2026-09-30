<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import ProductCover from '../components/ProductCover.vue'
import { productsApi } from '../api/products'
import { errorMessage } from '../api/client'
import { categoryLabels, type Category, type Product } from '../types/products'

const items = ref<Product[]>([])
const query = ref('')
const category = ref<Category | ''>('')
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
    const result = await productsApi.list(currentQuery.value, category.value, (page.value - 1) * 12)
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
async function remove(product: Product) {
  try {
    await ElMessageBox.confirm('将删除「' + product.name + '」的资料及全部商品图，此操作无法撤销。', '删除商品', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  removing.value = product.id
  error.value = ''
  try { await productsApi.remove(product.id); await load() }
  catch (cause) { error.value = errorMessage(cause) }
  finally { removing.value = '' }
}
onMounted(load)
</script>
<template>
  <WorkspaceLayout title="商品库">
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          YOUR PRODUCT LIBRARY
        </p><h1>把值得分享的好物，收进这里。</h1><p class="muted">
          记录商品信息、图片与细节，为下一次创作积累素材。
        </p>
      </div>
      <router-link to="/products/create">
        <el-button
          type="primary"
          size="large"
        >
          ＋ 新建商品
        </el-button>
      </router-link>
    </div>
    <section class="library-toolbar">
      <span><strong>{{ total }}</strong> 件 商品</span>
      <form
        class="model-search product-search"
        @submit.prevent="search"
      >
        <el-input
          v-model="query"
          placeholder="搜索名称或品牌"
          aria-label="搜索名称或品牌"
          clearable
          maxlength="100"
          @clear="search"
        /><el-select
          v-model="category"
          aria-label="筛选商品类别"
          @change="search"
        >
          <el-option
            label="全部类别"
            value=""
          /><el-option
            v-for="(label, value) in categoryLabels"
            :key="value"
            :label="label"
            :value="value"
          />
        </el-select><el-button
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
      正在读取你的商品库…
    </div>
    <section
      v-else-if="items.length"
      class="models-grid"
      aria-label="商品列表"
    >
      <article
        v-for="product in items"
        :key="product.id"
        class="model-card"
      >
        <router-link
          :to="'/products/' + product.id"
          :aria-label="'查看 ' + product.name"
        >
          <ProductCover
            :name="product.name"
            :src="product.processed_images[0]?.image_url"
          />
        </router-link>
        <div class="model-card-body">
          <div class="model-card-title">
            <h2>{{ product.name }}</h2><span>{{ product.processed_images.length }} 张商品图</span>
          </div>
          <p>{{ product.brand || '品牌未填写' }}</p>
          <div class="model-tags">
            <span>{{ categoryLabels[product.category] }}</span><span v-if="product.color">{{ product.color }}</span>
          </div>
          <div class="model-card-actions">
            <router-link :to="'/products/' + product.id">
              查看资料 ↗
            </router-link><router-link :to="'/products/' + product.id + '/edit'">
              编辑
            </router-link><el-button
              text
              type="danger"
              :loading="removing === product.id"
              :disabled="!!removing"
              @click="remove(product)"
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
      </div><h2>{{ (currentQuery || category) ? '没有找到匹配商品' : '第一件好物，从这里开始。' }}</h2>
      <p>{{ (currentQuery || category) ? '试试其他名称，或清空搜索条件。' : '保存商品资料，再上传正面与细节图片。' }}</p>
      <el-button
        v-if="currentQuery || category"
        @click="query = ''; category = ''; search()"
      >
        清空搜索
      </el-button>
      <router-link
        v-else
        to="/products/create"
      >
        <el-button type="primary">
          创建第一件商品
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
      商品资料和图片仅自己可见。
    </p>
  </WorkspaceLayout>
</template>

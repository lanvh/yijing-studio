<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { productsApi } from '../api/products'
import { errorMessage } from '../api/client'
const route = useRoute(), router = useRouter()
const id = computed(() => typeof route.params.id === 'string' ? route.params.id : '')
const editing = computed(() => !!id.value)
const form = reactive({ name: '' })
const busy = ref(false), loading = ref(false), error = ref(''), failed = ref(false)
async function load() {
  error.value = ''; failed.value = false; form.name = ''
  if (!id.value) return
  loading.value = true
  try { form.name = (await productsApi.get(id.value)).name }
  catch (cause) { error.value = errorMessage(cause); failed.value = true }
  finally { loading.value = false }
}
async function save() {
  if (busy.value || !form.name.trim()) return
  busy.value = true; error.value = ''
  try {
    const payload = { name: form.name.trim() }
    const product = editing.value ? await productsApi.update(id.value, payload) : await productsApi.create(payload)
    await router.replace('/products/' + product.id)
  } catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
watch(id, load, { immediate: true })
</script>
<template>
  <WorkspaceLayout :title="editing ? '编辑衣服' : '添加衣服'">
    <router-link
      class="back-link"
      :to="editing ? '/products/' + id : '/products'"
    >
      ← 返回商品库
    </router-link>
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          PRODUCT PROFILE
        </p><h1>记住名字，其余交给图片。</h1><p class="muted">
          保存后上传衣服图片，自动观察颜色、图案与版型。
        </p>
      </div>
    </div>
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
      正在读取商品资料…
    </p><el-button
      v-else-if="failed"
      @click="load"
    >
      重新加载
    </el-button>
    <div
      v-else
      class="profile-form-layout"
    >
      <form
        class="profile-form"
        @submit.prevent="save"
      >
        <fieldset :disabled="busy">
          <section class="form-panel">
            <h2>衣服名称</h2><label for="product-name">衣服名称</label><input
              id="product-name"
              v-model="form.name"
              required
              maxlength="100"
              placeholder="例如：酒红色拉链针织开衫"
            >
          </section><div class="form-save-row">
            <el-button
              type="primary"
              native-type="submit"
              :loading="busy"
            >
              {{ editing ? '保存修改' : '创建商品' }}
            </el-button>
          </div>
        </fieldset>
      </form>
      <aside class="profile-tip">
        <h2>让衣服的细节，留在参考图里。</h2><p>上传清晰的正面、背面和局部图，保留颜色、领口、图案、拉链与 Logo。图片生成直接参考原有外观。</p><p>AI 观察是图片描述，材质成分和性能仍以商品真实资料为准。</p>
      </aside>
    </div>
  </WorkspaceLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { modelsApi } from '../api/models'
import { errorMessage } from '../api/client'
import type { ModelProfile } from '../types/models'
const route = useRoute(), router = useRouter()
const id = computed(() => typeof route.params.id === 'string' ? route.params.id : '')
const editing = computed(() => !!id.value)
const form = reactive<{ name: string; gender: ModelProfile['gender'] }>({ name: '', gender: 'female' })
const busy = ref(false), loading = ref(false), error = ref(''), failed = ref(false)
async function load() {
  error.value = ''; failed.value = false; form.name = ''; form.gender = 'female'
  if (!id.value) return
  loading.value = true
  try { const model = await modelsApi.get(id.value); form.name = model.name; form.gender = model.gender }
  catch (cause) { error.value = errorMessage(cause); failed.value = true }
  finally { loading.value = false }
}
async function save() {
  if (busy.value || !form.name.trim()) return
  busy.value = true; error.value = ''
  try {
    const payload = { name: form.name.trim(), gender: form.gender }
    const model = editing.value ? await modelsApi.update(id.value, payload) : await modelsApi.create(payload)
    await router.replace('/models/' + model.id)
  } catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
watch(id, load, { immediate: true })
</script>
<template>
  <WorkspaceLayout :title="editing ? '编辑模特' : '新建模特'">
    <router-link
      class="back-link"
      :to="editing ? '/models/' + id : '/models'"
    >
      ← 返回模特库
    </router-link>
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          CHARACTER PROFILE
        </p><h1>给你的模特取个名字。</h1><p class="muted">
          保存后上传参考图，脸部、发型与身材以图片为准。
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
      正在读取人物资料…
    </p>
    <el-button
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
            <h2>基本信息</h2>
            <label for="model-name">模特名称</label><input
              id="model-name"
              v-model="form.name"
              required
              maxlength="100"
              placeholder="例如：小林"
            >
            <label for="model-gender">性别</label><select
              id="model-gender"
              v-model="form.gender"
            >
              <option value="female">
                女性
              </option><option value="male">
                男性
              </option><option value="androgynous">
                中性
              </option>
            </select>
          </section>
          <div class="form-save-row">
            <el-button
              type="primary"
              native-type="submit"
              :loading="busy"
            >
              {{ editing ? '保存修改' : '创建模特' }}
            </el-button>
          </div>
        </fieldset>
      </form>
      <aside class="profile-tip">
        <h2>一组参考图，就是人物档案。</h2><p>准备清晰的正面人像、侧面和全身图。生成时直接参考这些图片，保持脸部、发型和身材一致。</p><p>仅使用有使用权的成年 AI 虚拟形象。</p>
      </aside>
    </div>
  </WorkspaceLayout>
</template>

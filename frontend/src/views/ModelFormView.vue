<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { modelsApi } from '../api/models'
import { errorMessage } from '../api/client'
import type { ModelProfile } from '../types/models'

const route = useRoute()
const router = useRouter()
const modelId = computed(() => typeof route.params.id === 'string' ? route.params.id : '')
const editing = computed(() => !!modelId.value)
const defaults = (): ModelProfile => ({ name: '', gender: 'female', age_range: '25-34', height: null, body_type: '', skin_tone: '', hair_style: '', hair_color: '', style: 'casual', description: '' })
const form = reactive<ModelProfile>(defaults())
const formRef = ref<FormInstance>()
const busy = ref(false)
const loading = ref(false)
const loadFailed = ref(false)
const error = ref('')
const rules: FormRules = {
  name: [{ required: true, whitespace: true, message: '请输入模特名称', trigger: 'blur' }, { max: 100, message: '名称不能超过 100 字', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age_range: [{ required: true, message: '请选择成年年龄段', trigger: 'change' }],
}
async function load() {
  Object.assign(form, defaults())
  error.value = ''
  loadFailed.value = false
  if (!modelId.value) return
  loading.value = true
  try {
    const model = await modelsApi.get(modelId.value)
    for (const key of Object.keys(defaults()) as (keyof ModelProfile)[]) Object.assign(form, { [key]: model[key] })
  } catch (cause) { error.value = errorMessage(cause); loadFailed.value = true }
  finally { loading.value = false }
}
async function save() {
  if (busy.value || !(await formRef.value?.validate().catch(() => false))) return
  busy.value = true
  error.value = ''
  try {
    const payload = { ...form, name: form.name.trim(), height: form.height ?? null }
    const model = editing.value ? await modelsApi.update(modelId.value, payload) : await modelsApi.create(payload)
    await router.replace('/models/' + model.id)
  } catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
watch(modelId, load, { immediate: true })
</script>
<template>
  <WorkspaceLayout :title="editing ? '编辑模特' : '新建模特'">
    <router-link
      class="back-link"
      :to="editing ? '/models/' + modelId : '/models'"
    >
      ← {{ editing ? '返回模特资料' : '返回模特库' }}
    </router-link>
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          CHARACTER PROFILE
        </p><h1>{{ editing ? '让人物特征，更完整。' : '从一个鲜明的角色开始。' }}</h1><p class="muted">
          {{ editing ? '修改资料后保存，已有参考图会继续保留。' : '先描述你的虚拟模特，保存后再添加参考图片。' }}
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
      正在读取人物资料…
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
          <span class="eyebrow">01 / IDENTITY</span><h2>基本信息</h2>
          <el-form-item
            label="模特名称"
            prop="name"
          >
            <el-input
              v-model="form.name"
              maxlength="100"
              show-word-limit
              placeholder="例如：Female Casual"
            />
          </el-form-item>
          <div class="form-grid">
            <el-form-item
              label="性别"
              prop="gender"
            >
              <el-select v-model="form.gender">
                <el-option
                  label="女性"
                  value="female"
                /><el-option
                  label="男性"
                  value="male"
                /><el-option
                  label="中性"
                  value="androgynous"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              label="年龄段"
              prop="age_range"
            >
              <el-select v-model="form.age_range">
                <el-option
                  v-for="age in ['18-24', '25-34', '35-44', '45-54', '55+']"
                  :key="age"
                  :label="age + ' 岁'"
                  :value="age"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              label="身高（cm）"
              prop="height"
            >
              <el-input-number
                v-model="form.height"
                :min="100"
                :max="250"
                :precision="0"
                controls-position="right"
                placeholder="选填"
              />
            </el-form-item>
            <el-form-item
              label="体型"
              prop="body_type"
            >
              <el-input
                v-model="form.body_type"
                maxlength="60"
                placeholder="例如：匀称、运动型"
              />
            </el-form-item>
          </div>
        </section>
        <section class="form-panel">
          <span class="eyebrow">02 / APPEARANCE</span><h2>外观与风格</h2>
          <div class="form-grid">
            <el-form-item
              label="肤色"
              prop="skin_tone"
            >
              <el-input
                v-model="form.skin_tone"
                maxlength="60"
                placeholder="例如：自然小麦色"
              />
            </el-form-item>
            <el-form-item
              label="发色"
              prop="hair_color"
            >
              <el-input
                v-model="form.hair_color"
                maxlength="60"
                placeholder="例如：黑色"
              />
            </el-form-item>
            <el-form-item
              label="发型"
              prop="hair_style"
            >
              <el-input
                v-model="form.hair_style"
                maxlength="80"
                placeholder="例如：齐肩短发"
              />
            </el-form-item>
            <el-form-item
              label="人物风格"
              prop="style"
            >
              <el-input
                v-model="form.style"
                maxlength="80"
                placeholder="例如：casual、streetwear"
              />
            </el-form-item>
          </div>
          <el-form-item
            label="人物描述"
            prop="description"
          >
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              maxlength="2000"
              show-word-limit
              placeholder="补充人物气质、穿搭偏好或需要保持的特征。"
            />
          </el-form-item>
        </section>
        <div class="form-save-row">
          <router-link :to="editing ? '/models/' + modelId : '/models'">
            <el-button :disabled="busy">
              取消
            </el-button>
          </router-link><el-button
            type="primary"
            native-type="submit"
            :loading="busy"
          >
            {{ editing ? '保存修改' : '创建模特' }}
          </el-button>
        </div>
      </el-form>
      <aside class="profile-tip">
        <span class="tip-symbol">♧</span><p class="eyebrow">
          A DISTINCT CHARACTER
        </p><h2>一致的人物，<br>从清晰的特征开始。</h2><p>写下关键外观与风格，让每一次创作都有参考。</p><div class="tip-divider" /><h3>接下来，添加参考图</h3><p>建议准备正面、侧面和全身图，优先选择清晰、光线自然的图片。</p><p class="tip-note">
          当前仅支持成人 AI 虚拟形象，不支持真人照片。此步骤保存配置，不会生成图片。
        </p>
      </aside>
    </div>
  </WorkspaceLayout>
</template>

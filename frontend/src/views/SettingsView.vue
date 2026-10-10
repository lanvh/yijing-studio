<script setup lang="ts">
import { onMounted, ref } from 'vue'
import WorkspaceLayout from '../layouts/WorkspaceLayout.vue'
import { generationApi } from '../api/generation'
import { errorMessage } from '../api/client'
const status = ref<Awaited<ReturnType<typeof generationApi.provider>> | null>(null)
const error = ref(''), busy = ref(false)
async function load() {
  busy.value = true; error.value = ''
  try { status.value = await generationApi.provider() }
  catch (cause) { error.value = errorMessage(cause) }
  finally { busy.value = false }
}
onMounted(load)
</script>
<template>
  <WorkspaceLayout title="系统状态">
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          YOUR STUDIO SETTINGS
        </p><h1>安心创作，清楚每一步。</h1><p class="muted">
          查看当前运行模式与素材处理方式。
        </p>
      </div>
    </div>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
    />
    <section class="form-panel">
      <h2>图片服务</h2><p v-if="status">
        <strong>{{ status.mock ? 'Mock 本地演示' : status.provider === 'seedream' ? 'Seedream 图片服务' : status.provider === 'openai' ? 'OpenAI 图片服务' : status.provider }}</strong> · {{ status.available ? (status.mock ? '服务可用' : '配置就绪') : '服务不可用' }}
      </p><p>{{ status?.message }}</p>
      <p v-if="status?.mock">
        当前图片生成使用本地示意图，无图片 API 费用。
      </p>
      <p v-else>
        真实图片生成按服务商规则计费。这里的状态仅代表配置检查，实际访问权限、余额和可用性以生成请求为准。
      </p>
      <p v-if="status">
        文案与商品分析：{{ ['openai', 'ark'].includes(status.copy_mode) ? 'AI 服务' : '本地模板与资料整理' }} · {{ status.copy_available ? '配置就绪' : '缺少有效配置' }}
      </p>
      <p>API Key 仅在服务端环境变量中配置。页面不会显示或保存密钥。</p><el-button
        :loading="busy"
        @click="load"
      >
        刷新服务状态
      </el-button>
    </section>
    <section class="form-panel">
      <h2>素材与文案</h2><p>上传的模特和商品图片、任务结果仅供当前账户访问。任务保留创作时的资料副本，删除任务会移除对应副本与结果。</p><p>文案根据配置使用本地模板或 AI 服务，可继续编辑；AI 商品分析是待确认建议。系统仅检查图片文件是否可读取，尚不评估人物一致性、商品还原或美观度。</p><p>发布需由你手动操作。请使用有权使用的素材，并在发布前检查内容。</p>
    </section>
  </WorkspaceLayout>
</template>

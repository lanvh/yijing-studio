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
        <strong>{{ status.mock ? 'Mock 本地演示' : '当前配置未开放' }}</strong> · {{ status.available ? '服务可用' : '服务不可用' }}
      </p><p>本轮只开放 Mock：生成本地示意图、保存任务、整理文案和下载素材包。无需 API Key，不调用付费服务。</p><el-button
        :loading="busy"
        @click="load"
      >
        刷新服务状态
      </el-button>
    </section>
    <section class="form-panel">
      <h2>素材与文案</h2><p>上传的模特和商品图片、任务结果仅供当前账户访问。任务保留创作时的资料副本，删除任务会移除对应副本与结果。</p><p>文案来自本地模板和你填写的商品信息，可继续编辑。系统仅检查图片文件是否可读取，尚不评估人物一致性、商品还原或美观度。</p><p>发布需由你手动操作。请使用有权使用的素材，并在发布前检查内容。</p>
    </section>
  </WorkspaceLayout>
</template>

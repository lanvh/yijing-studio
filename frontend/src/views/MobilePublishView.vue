<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { mobileTransferApi, type MobileContent } from '../api/mobileTransfer'
import { errorMessage } from '../api/client'
const route = useRoute()
const token = location.hash.slice(1)
const content = ref<MobileContent | null>(null), error = ref(''), notice = ref(''), loading = ref(true)
const pictures = ref<{id:string;name:string;url:string;failed:boolean}[]>([])
const preview = ref(''), text = ref<HTMLTextAreaElement | null>(null)
const fullCopy = computed(() => content.value ? [content.value.title,content.value.caption,content.value.hashtags.map(t => '#'+t.replace(/^#+/,'')).join(' ')].join('\n\n') : '')
let disposed = false
async function load() {
  loading.value = true; error.value = ''; notice.value = ''; preview.value = ''
  try {
    const data = await mobileTransferApi.content(String(route.params.id), token)
    if (disposed) return
    content.value = data
    pictures.value.forEach(p => URL.revokeObjectURL(p.url)); pictures.value = []
    pictures.value = data.images.map(p => ({...p,url:'',failed:false}))
    await Promise.all(pictures.value.map(async p => {
      try { const blob = await mobileTransferApi.image(String(route.params.id),p.id,token); if (!disposed) p.url = URL.createObjectURL(blob) }
      catch { p.failed = true }
    }))
  } catch (cause) { error.value = errorMessage(cause) }
  finally { loading.value = false }
}
async function copy() {
  try {
    if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(fullCopy.value)
    else {
      text.value?.focus(); text.value?.select(); text.value?.setSelectionRange(0,fullCopy.value.length)
      if (!document.execCommand('copy')) throw new Error()
    }
    notice.value = '已复制标题、正文和话题。打开得物后粘贴即可。'
  } catch { text.value?.focus(); text.value?.select(); notice.value = '文案已选中，请长按并选择“复制”。' }
}
onMounted(load)
onUnmounted(() => { disposed = true; pictures.value.forEach(p => URL.revokeObjectURL(p.url)) })
</script>
<template>
  <main class="mobile-publish">
    <p class="eyebrow">
      AI SEED STUDIO
    </p><h1>把这组穿搭带到得物</h1>
    <p class="muted">
      先保存图片，再复制文案，最后到得物编辑并发布。
    </p>
    <p
      v-if="loading"
      role="status"
    >
      正在准备图片…
    </p>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
    />
    <el-button
      v-if="error"
      @click="load"
    >
      重新加载
    </el-button>
    <template v-if="content">
      <section class="form-panel">
        <h2>1. 保存图片</h2><p>点开图片后长按，选择“存储到照片”（不同 iOS 版本名称可能不同）。保存到相册后可在得物选择。</p>
        <div class="mobile-image-grid">
          <button
            v-for="picture in pictures"
            :key="picture.id"
            class="mobile-image-button"
            :aria-label="'打开'+picture.name"
            :disabled="!picture.url"
            @click="preview = picture.url"
          >
            <img
              v-if="picture.url"
              :src="picture.url"
              :alt="picture.name"
            ><span v-else>{{ picture.failed ? '图片加载失败，请重新加载' : '图片加载中…' }}</span>
          </button>
        </div><p v-if="!pictures.length">
          图片已取消选择或删除，请在电脑上重新生成取图二维码。
        </p>
      </section>
      <section class="form-panel">
        <h2>2. 复制完整文案</h2><textarea
          ref="text"
          :value="fullCopy"
          aria-label="完整发布文案"
          readonly
          rows="10"
        />
        <el-button
          type="primary"
          @click="copy"
        >
          一键复制完整文案
        </el-button><p
          v-if="notice"
          role="status"
        >
          {{ notice }}
        </p>
      </section>
      <section class="form-panel">
        <h2>3. 在得物编辑并发布</h2><p>打开得物 App 创建图文，选择刚保存的照片，粘贴文案。检查图片、文案和 AI 标识后再发布。</p><p class="muted">
          无需绑定得物账号；此页面不会自动发送内容。取图链接一小时有效，电脑需保持运行并与手机连接同一 Wi-Fi。
        </p>
      </section>
    </template>
    <el-dialog
      :model-value="!!preview"
      title="长按图片，存储到照片"
      width="96vw"
      @update:model-value="preview = ''"
    >
      <img
        v-if="preview"
        class="full-result"
        :src="preview"
        alt="可保存的原图"
      >
    </el-dialog>
  </main>
</template>
<style scoped>
.mobile-publish { max-width: 680px; margin: 0 auto; padding: 28px 18px; }
.mobile-publish h1 { font-size: 27px; }
.mobile-publish p { line-height: 1.8; }
.mobile-publish .form-panel { padding: 20px; }
.mobile-image-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; }
.mobile-image-button { padding: 0; border: 0; border-radius: 8px; background: #eef2e9; overflow: hidden; aspect-ratio: 3/4; cursor: pointer; }
.mobile-image-button img { width: 100%; height: 100%; object-fit: cover; display: block; }
.mobile-publish textarea { box-sizing: border-box; width: 100%; padding: 12px; border: 1px solid #d8ddd4; border-radius: 8px; font: inherit; line-height: 1.7; margin-bottom: 16px; }
</style>

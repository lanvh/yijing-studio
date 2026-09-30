<script setup lang="ts">
import { ref, watch } from 'vue'
const props = defineProps<{ name: string; src?: string }>()
const broken = ref(false)
watch(() => props.src, () => { broken.value = false })
</script>
<template>
  <div class="model-portrait">
    <img
      v-if="src && !broken"
      :src="src"
      :alt="name + '的参考图'"
      loading="lazy"
      @error="broken = true"
    >
    <div
      v-else
      class="portrait-placeholder"
      aria-label="尚无可用参考图"
    >
      <div class="portrait-head" /><div class="portrait-body" /><span>{{ broken ? '参考图暂时不可用' : '等待你的参考图' }}</span>
    </div>
  </div>
</template>

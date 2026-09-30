<script setup lang="ts">
import { ref, watch } from 'vue'
const props = defineProps<{ src?: string; name: string }>()
const failed = ref(false)
watch(() => props.src, () => { failed.value = false })
</script>
<template>
  <div class="product-cover">
    <img
      v-if="src && !failed"
      :src="src"
      :alt="name"
      loading="lazy"
      @error="failed = true"
    >
    <div
      v-else
      class="product-placeholder"
    >
      <svg
        viewBox="0 0 100 100"
        width="90"
        height="90"
        aria-hidden="true"
      >
        <path
          d="M20 35 50 20 80 35 80 70 50 87 20 70Z M20 35 50 51 80 35 M50 51V87 M35 27 65 43V58"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        />
      </svg>
      <span>{{ failed ? '图片暂时无法显示' : '等待你的第一张商品图' }}</span>
    </div>
  </div>
</template>

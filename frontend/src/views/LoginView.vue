<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { errorMessage } from '../api/client'

const auth = useAuthStore()
const router = useRouter()
const formRef = ref<FormInstance>()
const form = reactive({ email: '', password: '' })
const busy = ref(false)
const error = ref('')
const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  if (busy.value || !(await formRef.value?.validate().catch(() => false))) return
  busy.value = true
  error.value = ''
  try {
    await auth.login(form.email.trim(), form.password)
    form.password = ''
    await router.replace('/dashboard')
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="login-shell">
    <section
      class="studio-story"
      aria-label="衣镜 Studio介绍"
    >
      <a
        class="brand brand-light"
        href="/"
      ><span class="brand-mark">衣</span> 衣镜 Studio</a>
      <div class="story-copy">
        <span class="eyebrow light">YOUR NEXT CREATIVE SPACE</span>
        <h1>让灵感，<br>成为下一张好图。</h1>
        <p>从一个商品，到一组表达。<br>为你的创作，留一间 AI 摄影棚。</p>
      </div>
      <div
        class="studio-art"
        aria-hidden="true"
      >
        <div class="art-orbit" />
        <div class="art-frame frame-back">
          <span>THE STUDIO / 01</span>
        </div>
        <div class="art-frame frame-front">
          <div class="sculpture" /><span>LESS SETUP. MORE IDEAS.</span>
        </div>
        <span class="art-label">A SPACE FOR WHAT'S NEXT ↗</span>
      </div>
      <div class="story-footer">
        <span>衣镜 Studio</span><span>CREATE WITH INTENTION.</span>
      </div>
    </section>

    <section class="login-panel">
      <span class="edition">创作者工作空间 <span class="status-dot" /></span>
      <div class="login-content">
        <span class="eyebrow">WELCOME TO YOUR STUDIO</span>
        <h2>欢迎回到摄影棚</h2>
        <p class="muted intro">
          登录账号，进入你的创作空间。
        </p>
        <el-alert
          v-if="error || auth.serviceError"
          :title="error || auth.serviceError"
          type="error"
          :closable="false"
          show-icon
          role="alert"
          class="login-error"
        />
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="submit"
        >
          <el-form-item
            label="邮箱地址"
            prop="email"
          >
            <el-input
              v-model="form.email"
              type="email"
              autocomplete="username"
              placeholder="you@example.com"
              size="large"
              :disabled="busy"
              maxlength="254"
            />
          </el-form-item>
          <el-form-item
            label="密码"
            prop="password"
          >
            <el-input
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="输入你的密码"
              show-password
              size="large"
              :disabled="busy"
              maxlength="128"
            />
          </el-form-item>
          <el-button
            class="login-button"
            type="primary"
            size="large"
            native-type="submit"
            :loading="busy"
          >
            {{ busy ? '正在进入…' : '进入摄影棚' }} <span
              v-if="!busy"
              class="button-arrow"
            >↗</span>
          </el-button>
        </el-form>
        <p class="account-note">
          暂未开放注册。请使用管理员为你创建的账号。
        </p>
      </div>
      <footer class="login-footer">
        <span>灵感有出处，创作有边界。</span><span>衣镜 Studio © 2026</span>
      </footer>
    </section>
  </main>
</template>

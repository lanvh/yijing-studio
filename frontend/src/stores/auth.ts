import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, errorMessage } from '../api/client'
import type { User } from '../types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const initialized = ref(false)
  const serviceError = ref('')

  async function restore() {
    try {
      user.value = (await api.get<User>('/auth/me')).data
      serviceError.value = ''
    } catch (error) {
      user.value = null
      serviceError.value = axios.isAxiosError(error) && error.response?.status === 401
        ? '' : errorMessage(error)
    } finally {
      initialized.value = true
    }
  }

  async function login(email: string, password: string) {
    user.value = (await api.post<User>('/auth/login', { email, password })).data
    serviceError.value = ''
    initialized.value = true
  }

  async function logout() {
    await api.post('/auth/logout')
    user.value = null
  }

  return { user, initialized, serviceError, restore, login, logout }
})

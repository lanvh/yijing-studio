import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  withCredentials: true,
  headers: { 'X-Requested-With': 'AISeedStudio' },
})

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') return '请求超时，请稍后重试。'
    const detail: unknown = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (error.response?.status === 422) return '请检查填写内容、文件格式与必填项。'
    if (!error.response || error.response.status >= 500) return '暂时无法连接服务，请稍后重试。'
  }
  return '操作未完成，请重试。'
}

import { api } from './client'
import type { ContentCopy, GenerationTask, TaskSummary, TaskCreate, GenerationOptions, GenerationResult } from '../types/generation'
const base = '/generation'
export const generationApi = {
  stats: async () => (await api.get<{ models: number; products: number; tasks: number; weekly_tasks: number; succeeded_tasks: number }>(base + '/stats')).data,
  options: async () => (await api.get<GenerationOptions>(base + '/options')).data,
  list: async (offset = 0, limit = 12, status = '') => (await api.get<{ items: TaskSummary[]; total: number }>(base + '/tasks', { params: { offset, limit, status: status || undefined } })).data,
  create: async (payload: TaskCreate) => (await api.post<GenerationTask>(base + '/tasks', payload, { timeout: 1500000 })).data,
  get: async (id: string) => (await api.get<GenerationTask>(base + '/tasks/' + id)).data,
  retry: async (id: string) => (await api.post<GenerationTask>(base + '/tasks/' + id + '/retry', {}, { timeout: 1500000 })).data,
  remove: async (id: string) => { await api.delete(base + '/tasks/' + id) },
  select: async (id: string, selected: boolean) => (await api.patch<GenerationResult>(base + '/results/' + id, { is_selected: selected })).data,
  removeResult: async (id: string) => { await api.delete(base + '/results/' + id) },
  copy: async (id: string, copy: Omit<ContentCopy, 'source'>) => (await api.patch<ContentCopy>(base + '/tasks/' + id + '/copy', copy)).data,
  regenerateCopy: async (id: string) => (await api.post<ContentCopy>(base + '/tasks/' + id + '/copy', {}, { timeout: 150000 })).data,
  export: async (id: string) => (await api.post<Blob>(base + '/tasks/' + id + '/export', {}, { responseType: 'blob', timeout: 60000 })).data,
  provider: async () => (await api.get<{ available: boolean; mock: boolean; message: string; copy_mode: string; copy_available: boolean; configuration_only: boolean }>('/providers')).data,
}

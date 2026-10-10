import { api } from './client'
import type { AIModel, ModelProfile, ModelPage, ModelLimits, ReferenceImage } from '../types/models'

export const modelsApi = {
  generateReference: async (id: string, key: string) => (await api.post<ReferenceImage>('/models/' + id + '/generate-reference', { request_key: key }, { timeout: 700000 })).data,
  list: async (q = '', offset = 0, limit = 12) =>
    (await api.get<ModelPage>('/models', { params: { q, offset, limit } })).data,
  limits: async () => (await api.get<ModelLimits>('/models/options')).data,
  get: async (id: string) => (await api.get<AIModel>('/models/' + id)).data,
  create: async (profile: Partial<ModelProfile>) => (await api.post<AIModel>('/models', profile)).data,
  update: async (id: string, profile: Partial<ModelProfile>) =>
    (await api.patch<AIModel>('/models/' + id, profile)).data,
  remove: async (id: string) => { await api.delete('/models/' + id) },
  removeImage: async (imageUrl: string) => { await api.delete(imageUrl.replace('/api/v1', '')) },
  upload: async (id: string, file: File, rightsConfirmed: boolean, progress: (value: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    form.append('rights_confirmed', String(rightsConfirmed))
    return (await api.post<ReferenceImage>('/models/' + id + '/images', form, {
      timeout: 60000,
      onUploadProgress: event => progress(Math.min(99, Math.round((event.progress || 0) * 100))),
    })).data
  },
}

import { api } from './client'
import type { Product, ProductProfile, ProductPage, ProductLimits, Category } from '../types/products'
export const productsApi = {
  list: async (q = '', category: Category | '' = '', offset = 0, limit = 12) =>
    (await api.get<ProductPage>('/products', { params: { q, category: category || undefined, offset, limit } })).data,
  limits: async () => (await api.get<ProductLimits>('/products/options')).data,
  get: async (id: string) => (await api.get<Product>('/products/' + id)).data,
  create: async (profile: ProductProfile) => (await api.post<Product>('/products', profile)).data,
  update: async (id: string, profile: ProductProfile) =>
    (await api.patch<Product>('/products/' + id, profile)).data,
  remove: async (id: string) => { await api.delete('/products/' + id) },
  analyze: async (id: string) => (await api.post<Product>('/products/' + id + '/analyze')).data,
  removeImage: async (imageUrl: string) => (await api.delete<Product>(imageUrl.replace('/api/v1', ''))).data,
  upload: async (id: string, file: File, rightsConfirmed: boolean, progress: (value: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    form.append('rights_confirmed', String(rightsConfirmed))
    return (await api.post<Product>('/products/' + id + '/images', form, {
      timeout: 60000,
      onUploadProgress: event => progress(Math.min(99, Math.round((event.progress || 0) * 100))),
    })).data
  },
}

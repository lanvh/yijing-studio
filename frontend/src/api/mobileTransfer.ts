import { api } from './client'
export interface MobileLink { url: string; expires_at: number; qr_image: string }
export interface MobileContent { title: string; caption: string; hashtags: string[]; expires_at: number; images: {id: string; name: string}[] }
export const mobileTransferApi = {
  create: async (id: string) => (await api.post<MobileLink>('/generation/tasks/'+id+'/mobile-transfer')).data,
  revoke: async (id: string) => { await api.delete('/generation/tasks/'+id+'/mobile-transfer') },
  content: async (id: string, token: string) => (await api.get<MobileContent>('/mobile-publish/'+id, {headers:{'X-Mobile-Token':token}})).data,
  image: async (id: string, image: string, token: string) => (await api.get<Blob>('/mobile-publish/'+id+'/images/'+image,{headers:{'X-Mobile-Token':token},responseType:'blob'})).data,
}

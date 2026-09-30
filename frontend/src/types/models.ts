export interface ModelProfile {
  name: string
  gender: 'female' | 'male' | 'androgynous'
  age_range: '18-24' | '25-34' | '35-44' | '45-54' | '55+'
  height: number | null
  body_type: string
  skin_tone: string
  hair_style: string
  hair_color: string
  style: string
  description: string
}
export interface ReferenceImage {
  id: string
  image_url: string
  image_type: string
  metadata: { width: number; height: number; size_bytes: number; moderation_status: string }
  created_at: string
}
export interface AIModel extends ModelProfile {
  id: string
  reference_images: ReferenceImage[]
  created_at: string
  updated_at: string
}
export interface ModelPage {
  items: AIModel[]
  total: number
  limit: number
  offset: number
}
export interface ModelLimits {
  max_image_size_mb: number
  max_image_pixels: number
  max_model_images: number
  allowed_image_types: string[]
}
export const genderLabels = { female: '女性', male: '男性', androgynous: '中性' }

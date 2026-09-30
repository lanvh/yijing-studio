export const categoryLabels = {
  top: '上衣', bottom: '下装', dress: '连衣裙', shoes: '鞋履', bag: '包袋',
  necklace: '项链', bracelet: '手链', ring: '戒指', watch: '手表', hat: '帽子', other: '其他',
}
export type Category = keyof typeof categoryLabels
export interface FeatureNotes {
  material: string
  pattern: string
  logo_description: string
  shape: string
  critical_features: string[]
}
export interface ProductProfile {
  name: string
  brand: string
  category: Category
  color: string
  description: string
  feature_notes: FeatureNotes
}
export interface ProductImage {
  id: string
  image_url: string
  image_type: 'original' | 'processed'
  metadata: { width?: number; height?: number; original_image_id?: string; size_bytes: number }
}
export interface Product extends Omit<ProductProfile, 'feature_notes'> {
  id: string
  original_images: ProductImage[]
  processed_images: ProductImage[]
  product_features: {
    ai_analysis?: { status: string; message?: string; findings?: { category: string; colors: string[]; pattern: string; logo_description: string; shape: string; material_appearance: string; critical_features: string[]; uncertainties: string[] } }
    confirmed: FeatureNotes
    analyzed_at: string
    image_observations: { image_id: string; width: number; height: number; palette: string[] }[]
  }
}
export interface ProductPage { items: Product[]; total: number; limit: number; offset: number }
export interface ProductLimits { max_image_size_mb: number; max_product_images: number }

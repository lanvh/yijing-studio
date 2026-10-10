export interface ContentCopy {
  title: string; caption: string; hashtags: string[]; product_summary: string; styling_notes: string; source: string
}
export interface GenerationResult {
  id: string; image_url: string; is_selected: boolean
  quality_score: number | null
  metadata: { mock: boolean; file_check: { passed: boolean; width: number; height: number } }
}
export interface TaskSummary {
  id: string; request_key: string; model_id: string | null; product_id: string | null
  model_name: string; product_name: string; scene: string; style: string; pose: string; custom_direction: string
  requested_count: number; result_count: number; status: string; is_mock: boolean
  error_message: string; attempt: number; is_active: boolean; can_retry: boolean; created_at: string
}
export interface GenerationTask extends TaskSummary { results: GenerationResult[]; copy: ContentCopy | null }
export interface TaskCreate { model_id: string; product_id: string; request_key: string; scene: string; style: string; pose: string; requested_count: number; custom_direction?: string }
export interface GenerationOptions { scenes: Record<string,string>; styles: Record<string,string>; poses: Record<string,string>; counts: number[] }
export const statusLabels: Record<string,string> = { PENDING: '待执行', PROCESSING: '生成中', SUCCEEDED: '已完成', PARTIAL: '部分完成', FAILED: '生成失败' }
export function taskTime(value: string) { return new Date(value).toLocaleString('zh-CN', { hour12: false }) }

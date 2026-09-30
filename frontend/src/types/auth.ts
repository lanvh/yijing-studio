export interface User {
  id: string
  email: string
  display_name: string
  role: 'admin' | 'user'
  enabled: boolean
  created_at: string
}

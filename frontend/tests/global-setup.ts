import { request, type FullConfig } from '@playwright/test'

// Browser suites upload/generate fixtures. Never run them against billable services.
export default async function setup(config: FullConfig) {
  const context = await request.newContext({
    baseURL: config.projects[0]?.use.baseURL,
    extraHTTPHeaders: { 'X-Requested-With': 'AISeedStudio' },
  })
  try {
    const login = await context.post('/api/v1/auth/login', {
      data: { email: process.env.ADMIN_EMAIL, password: process.env.ADMIN_PASSWORD },
    })
    if (!login.ok()) throw new Error('Browser test login failed; check local test credentials.')
    const response = await context.get('/api/v1/providers')
    if (!response.ok()) throw new Error('Cannot check browser test service configuration.')
    const state = await response.json()
    if (!state.mock || !['local', 'mock'].includes(state.copy_mode)) {
      throw new Error('Browser tests require IMAGE_PROVIDER=mock and local copy. Paid services will not be exercised.')
    }
  } finally {
    await context.post('/api/v1/auth/logout').catch(() => {})
    await context.dispose()
  }
}

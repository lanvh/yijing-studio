import { expect, test } from '@playwright/test'

const email = process.env.ADMIN_EMAIL
const password = process.env.ADMIN_PASSWORD
if (!email || !password) throw new Error('Set ADMIN_EMAIL and ADMIN_PASSWORD in root .env.')

test('protected route, login, refresh, logout, back navigation', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/login$/)
  await page.screenshot({ path: '../storage/qa/login-desktop.png', fullPage: true })
  await page.getByLabel('邮箱地址').fill(email!)
  await page.getByLabel('密码', { exact: true }).fill(password!)
  await page.getByRole('button', { name: '进入摄影棚' }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByText(email!, { exact: true })).toBeVisible()
  await page.screenshot({ path: '../storage/qa/dashboard-desktop.png', fullPage: true })
  expect(await page.evaluate(() => localStorage.length)).toBe(0)
  await page.reload()
  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByRole('button', { name: '退出登录' })).toBeVisible()
  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page).toHaveURL(/\/login$/)
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/login$/)
  expect(errors).toEqual([])
})

test('invalid credentials and form validation', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: '进入摄影棚' }).click()
  await expect(page.getByText('请输入邮箱', { exact: true })).toBeVisible()
  await page.getByLabel('邮箱地址').fill(email!)
  await page.getByLabel('密码', { exact: true }).fill('wrong-password')
  await page.getByRole('button', { name: '进入摄影棚' }).click()
  await expect(page.getByRole('alert').filter({ hasText: '邮箱或密码错误' })).toBeVisible()
  await expect(page).toHaveURL(/\/login$/)
})

test('mobile viewport has no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: '欢迎回到摄影棚' })).toBeVisible()
  await page.screenshot({ path: '../storage/qa/login-mobile.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByLabel('邮箱地址').fill(email!)
  await page.getByLabel('密码', { exact: true }).fill(password!)
  await page.getByRole('button', { name: '进入摄影棚' }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  await page.screenshot({ path: '../storage/qa/dashboard-mobile.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page).toHaveURL(/\/login$/)
})

test('service outage shows actionable error', async ({ page }) => {
  await page.route('**/api/v1/auth/me', route => route.fulfill({
    status: 503, contentType: 'application/json',
    body: JSON.stringify({ detail: '数据库暂时不可用，请稍后重试。' }),
  }))
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('alert')).toContainText('数据库暂时不可用')
})

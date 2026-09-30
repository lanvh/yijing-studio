import { expect, test, type Page } from '@playwright/test'
import path from 'node:path'
import { readFileSync } from 'node:fs'

const email = process.env.ADMIN_EMAIL
const password = process.env.ADMIN_PASSWORD
if (!email || !password) throw new Error('Set ADMIN_EMAIL and ADMIN_PASSWORD in root .env.')
const headers = { 'X-Requested-With': 'AISeedStudio' }
const fixture = path.resolve('tests/fixtures/product.png')
let created: string[] = []

test.beforeEach(async ({ page }) => {
  created = []
  expect((await page.request.post('/api/v1/auth/login', { data: { email, password }, headers })).ok()).toBeTruthy()
})
test.afterEach(async ({ page }) => {
  for (const id of created) await page.request.delete('/api/v1/products/' + id, { headers })
  await page.request.post('/api/v1/auth/logout', { headers })
})
async function createProduct(page: Page, name: string, category = '鞋履') {
  await page.goto('/products/create')
  await page.getByLabel('商品名称', { exact: true }).fill(name)
  await page.getByRole('combobox', { name: /商品类别/ }).press('ArrowDown')
  await page.getByRole('option', { name: category, exact: true }).click()
  await page.getByLabel('商品颜色', { exact: true }).fill('米白色')
  await page.getByLabel('品牌', { exact: true }).fill('QA Brand')
  const waiting = page.waitForResponse(response => response.url().endsWith('/api/v1/products') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '创建商品', exact: true }).click()
  const response = await waiting
  expect(response.status()).toBe(201)
  const product = await response.json()
  created.push(product.id)
  await expect(page).toHaveURL(new RegExp('/products/' + product.id + '$'))
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  return product.id as string
}
async function addImage(page: Page) {
  await page.getByText('我确认拥有商品图片的使用权，或已获授权。', { exact: true }).click()
  const waiting = page.waitForResponse(response => response.url().endsWith('/images') && response.request().method() === 'POST')
  await page.getByLabel('上传商品图片', { exact: true }).setInputFiles(fixture)
  const response = await waiting
  expect(response.status()).toBe(201)
  await expect(page.getByText('商品图片已保存。', { exact: true })).toBeVisible()
  return response.json()
}

test('product CRUD, original download, feature refresh, filtering and responsive detail', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const name = '白色运动鞋 · QA ' + Date.now()
  const id = await createProduct(page, name)
  await page.getByRole('button', { name: '编辑资料' }).click()
  await page.getByLabel('材质', { exact: true }).fill('织物')
  await page.getByLabel('形状与结构', { exact: true }).fill('低帮系带')
  await page.getByLabel('关键细节（每行一条）', { exact: true }).fill('白色鞋底\n三组鞋带孔')
  await page.screenshot({ path: '../storage/qa/phase3-form-desktop.png', fullPage: true })
  await page.getByRole('button', { name: '保存修改', exact: true }).click()
  await expect(page).toHaveURL(new RegExp('/products/' + id + '$'))
  await expect(page.getByText('织物', { exact: true })).toBeVisible()
  await expect(page.getByLabel('上传商品图片', { exact: true })).toBeDisabled()
  const result = await addImage(page)
  const original = result.original_images[0]
  await expect((await page.request.get(original.image_url)).body()).resolves.toEqual(readFileSync(fixture))
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('link', { name: '下载原图' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe(original.id + '.png')
  await page.getByRole('button', { name: '重新整理特征' }).click()
  await expect(page.getByText('特征已重新整理。', { exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('button', { name: '预览商品图片 1' })).toBeVisible()
  await expect(page.getByText('白色鞋底', { exact: true })).toBeVisible()
  await page.screenshot({ path: '../storage/qa/phase3-detail-desktop.png', fullPage: true })
  await page.getByRole('button', { name: '预览商品图片 1' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: '../storage/qa/phase3-detail-mobile.png', fullPage: true, animations: 'disabled' })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole('link', { name: '返回商品库' }).click()
  await page.getByRole('textbox', { name: '搜索名称或品牌' }).fill(name)
  await page.getByRole('button', { name: '搜索', exact: true }).click()
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  await page.getByRole('combobox', { name: '筛选商品类别' }).press('ArrowDown')
  await page.getByRole('option', { name: '鞋履', exact: true }).click()
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  await page.setViewportSize({ width: 1440, height: 1000 })
  await expect(page.locator('.product-cover img')).toBeVisible()
  await expect.poll(() => page.locator('.product-cover img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true)
  await page.screenshot({ path: '../storage/qa/phase3-library-desktop.png', fullPage: true, animations: 'disabled' })
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await page.getByRole('button', { name: '取消', exact: true }).click()
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await page.getByRole('button', { name: '确认删除', exact: true }).click()
  await expect(page.getByRole('heading', { name: '没有找到匹配商品' })).toBeVisible()
  expect((await page.request.get(original.image_url)).status()).toBe(404)
  expect(errors).toEqual([])
})

test('product upload rejection, pair removal and mobile form', async ({ page }) => {
  const id = await createProduct(page, '包袋 · QA ' + Date.now(), '包袋')
  await page.getByRole('button', { name: '编辑资料' }).click()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: '../storage/qa/phase3-form-mobile.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole('button', { name: '保存修改', exact: true }).click()
  await expect(page).toHaveURL(new RegExp('/products/' + id + '$'))
  const result = await addImage(page)
  await page.getByLabel('上传商品图片', { exact: true }).setInputFiles({ name: 'bad.png', mimeType: 'image/png', buffer: Buffer.from('bad') })
  await expect(page.getByRole('alert')).toContainText('无法读取完整图片')
  await page.getByRole('button', { name: '移除', exact: true }).click()
  await page.getByRole('button', { name: '确认移除', exact: true }).click()
  await expect(page.getByText('商品图片已移除。', { exact: true })).toBeVisible()
  expect((await page.request.get(result.original_images[0].image_url)).status()).toBe(404)
  await page.reload()
  await expect(page.getByRole('button', { name: '预览商品图片 1' })).toHaveCount(0)
  await expect(page.getByText('添加图片后，将展示图片色板。', { exact: true })).toBeVisible()
})

test('remaining acceptance categories create and persist', async ({ page }) => {
  for (const category of ['上衣', '手表', '项链']) {
    const id = await createProduct(page, category + ' · QA ' + Date.now(), category)
    await page.reload()
    await expect(page.getByText(category, { exact: true })).toBeVisible()
    expect((await page.request.get('/api/v1/products/' + id)).ok()).toBeTruthy()
  }
})

test('product required fields, empty search and retry', async ({ page }) => {
  await page.goto('/products/create')
  await page.getByRole('button', { name: '创建商品', exact: true }).click()
  await expect(page.getByText('请输入商品名称', { exact: true })).toBeVisible()
  await page.route('**/api/v1/products?*', route => route.fulfill({
    status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '数据库暂时不可用，请稍后重试。' }),
  }))
  await page.goto('/products')
  await expect(page.getByRole('alert')).toContainText('数据库暂时不可用')
  await page.unroute('**/api/v1/products?*')
  await page.getByRole('button', { name: '重新加载', exact: true }).click()
  await expect(page.getByRole('alert')).toHaveCount(0)
  await page.getByRole('textbox', { name: '搜索名称或品牌' }).fill('no-match-' + Date.now())
  await page.getByRole('button', { name: '搜索', exact: true }).click()
  await expect(page.getByRole('heading', { name: '没有找到匹配商品' })).toBeVisible()
})

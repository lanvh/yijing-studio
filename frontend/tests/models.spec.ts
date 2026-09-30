import { expect, test, type Page } from '@playwright/test'
import path from 'node:path'

const email = process.env.ADMIN_EMAIL
const password = process.env.ADMIN_PASSWORD
if (!email || !password) throw new Error('Set ADMIN_EMAIL and ADMIN_PASSWORD in root .env.')
const headers = { 'X-Requested-With': 'AISeedStudio' }
const fixture = path.resolve('tests/fixtures/reference.png')
let created: string[] = []

test.beforeEach(async ({ page }) => {
  created = []
  const response = await page.request.post('/api/v1/auth/login', {
    data: { email, password }, headers,
  })
  expect(response.ok()).toBeTruthy()
})

test.afterEach(async ({ page }) => {
  for (const id of created) await page.request.delete('/api/v1/models/' + id, { headers })
  await page.request.post('/api/v1/auth/logout', { headers })
})

async function createModel(page: Page, name: string) {
  await page.goto('/models/create')
  await page.getByLabel('模特名称', { exact: true }).fill(name)
  await page.getByLabel('体型', { exact: true }).fill('匀称')
  await page.getByLabel('发型', { exact: true }).fill('齐肩短发')
  await page.getByLabel('人物描述', { exact: true }).fill('测试用成年虚拟角色。')
  const responsePromise = page.waitForResponse(response =>
    response.url().endsWith('/api/v1/models') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '创建模特', exact: true }).click()
  const response = await responsePromise
  expect(response.status()).toBe(201)
  const model = await response.json()
  created.push(model.id)
  await expect(page).toHaveURL(new RegExp('/models/' + model.id + '$'))
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  return model.id as string
}

test('create, edit, upload, persistence, search and model deletion', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const name = 'Female Casual · QA ' + Date.now()
  const id = await createModel(page, name)
  await page.getByRole('button', { name: '编辑资料' }).click()
  await page.getByLabel('人物风格', { exact: true }).fill('minimal')
  await page.getByLabel('发色', { exact: true }).fill('黑色')
  await page.getByRole('button', { name: '保存修改', exact: true }).click()
  await expect(page).toHaveURL(new RegExp('/models/' + id + '$'))
  await expect(page.getByText('minimal', { exact: true })).toBeVisible()
  await expect(page.getByLabel('上传参考图', { exact: true })).toBeDisabled()
  await page.getByText('我确认这是有使用权的 AI 虚拟成人形象，非真人照片。', { exact: true }).click()
  await expect(page.getByRole('checkbox')).toBeChecked()
  const uploadResponse = page.waitForResponse(response =>
    response.url().endsWith('/images') && response.request().method() === 'POST')
  await page.getByLabel('上传参考图', { exact: true }).setInputFiles(fixture)
  const imageResult = await uploadResponse
  expect(imageResult.status()).toBe(201)
  const image = await imageResult.json()
  await expect(page.getByText('参考图已保存。', { exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('button', { name: '预览参考图 1' })).toBeVisible()
  await page.screenshot({ path: '../storage/qa/phase2-detail-desktop.png', fullPage: true })
  await page.getByRole('button', { name: '预览参考图 1' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: '../storage/qa/phase2-detail-mobile.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole('link', { name: '返回模特库' }).click()
  await page.getByRole('textbox', { name: '搜索模特名称' }).fill(name)
  await page.getByRole('button', { name: '搜索', exact: true }).click()
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.screenshot({ path: '../storage/qa/phase2-library-desktop.png', fullPage: true })
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await page.getByRole('button', { name: '取消', exact: true }).click()
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await page.getByRole('button', { name: '确认删除', exact: true }).click()
  await expect(page.getByRole('heading', { name: '没有找到这位模特' })).toBeVisible()
  expect((await page.request.get(image.image_url)).status()).toBe(404)
  expect(errors).toEqual([])
})

test('male profile, invalid upload, image removal and mobile form', async ({ page }) => {
  const id = await createModel(page, 'Male Streetwear · QA ' + Date.now())
  await page.getByRole('button', { name: '编辑资料' }).click()
  await page.getByRole('combobox', { name: /性别/ }).press('ArrowDown')
  await page.getByRole('option', { name: '男性', exact: true }).click()
  await page.getByLabel('人物风格', { exact: true }).fill('streetwear')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: '../storage/qa/phase2-form-mobile.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole('button', { name: '保存修改', exact: true }).click()
  await expect(page).toHaveURL(new RegExp('/models/' + id + '$'))
  await page.getByText('我确认这是有使用权的 AI 虚拟成人形象，非真人照片。', { exact: true }).click()
  await expect(page.getByRole('checkbox')).toBeChecked()
  await page.getByLabel('上传参考图', { exact: true }).setInputFiles({
    name: 'bad.png', mimeType: 'image/png', buffer: Buffer.from('not a picture'),
  })
  await expect(page.getByRole('alert')).toContainText('无法读取完整图片')
  await page.getByLabel('上传参考图', { exact: true }).setInputFiles(fixture)
  await expect(page.getByText('参考图已保存。', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '移除', exact: true }).click()
  await page.getByRole('button', { name: '确认移除', exact: true }).click()
  await expect(page.getByText('参考图已移除。', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '预览参考图 1' })).toHaveCount(0)
  await page.reload()
  await expect(page.getByText('男性', { exact: true })).toBeVisible()
})

test('model form validation and list retry', async ({ page }) => {
  await page.goto('/models/create')
  await page.getByRole('button', { name: '创建模特', exact: true }).click()
  await expect(page.getByText('请输入模特名称', { exact: true })).toBeVisible()
  await page.route('**/api/v1/models?*', route => route.fulfill({
    status: 503, contentType: 'application/json', body: JSON.stringify({ detail: '数据库暂时不可用，请稍后重试。' }),
  }))
  await page.goto('/models')
  await expect(page.getByRole('alert')).toContainText('数据库暂时不可用')
  await page.unroute('**/api/v1/models?*')
  await page.getByRole('button', { name: '重新加载', exact: true }).click()
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('expired session redirects from model library to login', async ({ page }) => {
  await page.goto('/dashboard')
  await expect(page.getByRole('heading', { name: /你好/ })).toBeVisible()
  await page.request.post('/api/v1/auth/logout', { headers })
  await page.getByRole('navigation', { name: '主导航', exact: true }).getByRole('link', { name: 'AI 模特' }).click()
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('alert')).toContainText('登录已失效')
})


test('generate fictional model reference, persist and use in creation', async ({page}) => {
  const errors: string[] = []
  page.on('pageerror', e => errors.push(e.message))
  const id = await createModel(page, 'Generated Model · QA ' + Date.now())
  await expect(page.getByText('生成 Mock 参考图', {exact:true})).toBeVisible()
  await page.getByRole('button', {name:'生成参考图',exact:true}).click()
  await expect(page.getByText('生成的参考图已保存。',{exact:true})).toBeVisible()
  await expect(page.getByRole('button',{name:'预览参考图 1'})).toBeVisible()
  await page.reload()
  await expect(page.getByRole('button',{name:'预览参考图 1'})).toBeVisible()
  await page.getByRole('button',{name:'预览参考图 1'}).scrollIntoViewIfNeeded()
  await page.waitForFunction(() => [...document.querySelectorAll('.reference-preview-button img, .model-summary img')].every(image => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth > 0))
  await page.screenshot({path:'../storage/qa/mvp-generated-model.png',fullPage:true})
  await page.getByRole('link',{name:'使用这个模特创建内容 →'}).click()
  await expect(page.getByLabel('AI 模特',{exact:true})).toHaveValue(id)
  await page.setViewportSize({width:390,height:844})
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  expect(errors).toEqual([])
})

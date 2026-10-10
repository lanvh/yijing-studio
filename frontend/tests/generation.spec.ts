import { expect, test, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const email = process.env.ADMIN_EMAIL, password = process.env.ADMIN_PASSWORD
if (!email || !password) throw new Error('Set local admin credentials in root .env.')
const headers = { 'X-Requested-With': 'AISeedStudio' }
let modelId = '', productId = ''
let taskIds: string[] = []
test.beforeEach(async ({ page }) => {
  taskIds = []
  expect((await page.request.post('/api/v1/auth/login',{data:{email,password},headers})).ok()).toBeTruthy()
  const model = await page.request.post('/api/v1/models',{headers,data:{name:'Workflow Model '+Date.now(),gender:'female',age_range:'25-34'}})
  expect(model.status()).toBe(201); modelId = (await model.json()).id
  const product = await page.request.post('/api/v1/products',{headers,data:{name:'Workflow Shoes '+Date.now(),category:'shoes',color:'白色'}})
  expect(product.status()).toBe(201); productId = (await product.json()).id
  for (const [kind,id,fixture] of [['models',modelId,'reference.png'],['products',productId,'product.png']]) {
    expect((await page.request.post('/api/v1/'+kind+'/'+id+'/images',{headers,multipart:{
      rights_confirmed:'true',file:{name:fixture!,mimeType:'image/png',buffer:readFileSync(path.resolve('tests/fixtures/'+fixture))},
    }})).status()).toBe(201)
  }
})
test.afterEach(async ({ page }) => {
  for (const id of taskIds) await page.request.delete('/api/v1/generation/tasks/'+id,{headers})
  await page.request.delete('/api/v1/models/'+modelId,{headers})
  await page.request.delete('/api/v1/products/'+productId,{headers})
  await page.request.post('/api/v1/auth/logout',{headers})
})
async function choose(page: Page) {
  await page.goto('/create-content')
  await page.getByLabel('AI 模特',{exact:true}).selectOption(modelId)
  await page.getByRole('combobox',{name:'衣服',exact:true}).click()
  const productOption = page.getByRole('option').filter({hasText:'Workflow Shoes'}).last()
  await expect(productOption.locator('img')).toBeVisible()
  await expect.poll(() => productOption.locator('img').evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true)
  await productOption.click()
  await page.getByLabel('场景',{exact:true}).selectOption('cafe')
  await page.getByLabel('风格',{exact:true}).selectOption('minimal')
}
async function generate(page: Page) {
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/generation/tasks') && r.request().method()==='POST')
  await page.getByRole('button',{name:'生成 Mock 内容',exact:true}).click()
  const response = await responsePromise
  expect(response.status()).toBe(201)
  const task = await response.json()
  taskIds.push(task.id)
  await expect(page).toHaveURL(new RegExp('/tasks/'+task.id+'$'))
  await expect(page.locator('.result-card')).toHaveCount(4)
  return task.id as string
}
test('Mock full workflow, editable copy, selected export, persistence, responsive views and deletion',async ({page}) => {
  const errors: string[] = []
  page.on('pageerror',e => errors.push(e.message))
  await choose(page)
  await page.getByLabel('场景',{exact:true}).selectOption('bookstore')
  await page.getByLabel('风格',{exact:true}).selectOption('american_vintage')
  await page.getByLabel('姿势',{exact:true}).selectOption('hands_pockets')
  await page.getByLabel('自定义方向（选填）',{exact:true}).fill('暖色傍晚书店，美式复古穿搭，双手插兜自然站立')
  await page.screenshot({path:'../storage/qa/workflow-create-desktop.png',fullPage:true})
  const id = await generate(page)
  const detail = await (await page.request.get('/api/v1/generation/tasks/'+id)).json()
  expect(detail.custom_direction).toContain('暖色傍晚书店')
  await expect(page.getByText('自定义方向：暖色傍晚书店，美式复古穿搭，双手插兜自然站立',{exact:true})).toBeVisible()
  await page.waitForFunction(() => [...document.querySelectorAll('.result-preview img')].every(img => (img as HTMLImageElement).complete && (img as HTMLImageElement).naturalWidth>0))
  await page.screenshot({path:'../storage/qa/workflow-results-desktop.png',fullPage:true})
  await page.getByRole('checkbox',{name:'选择图片 4',exact:true}).uncheck()
  await expect(page.getByRole('checkbox',{name:'选择图片 4',exact:true})).not.toBeChecked()
  await page.getByLabel('标题',{exact:true}).fill('我的咖啡馆搭配草稿')
  await expect(page.getByRole('button',{name:'下载 ZIP 素材包'})).toBeDisabled()
  await page.getByRole('button',{name:'保存文案',exact:true}).click()
  await expect(page.getByText('文案已保存。',{exact:true})).toBeVisible()
  await page.reload()
  await expect(page.getByLabel('标题',{exact:true})).toHaveValue('我的咖啡馆搭配草稿')
  await expect(page.getByRole('checkbox',{name:'选择图片 4',exact:true})).not.toBeChecked()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button',{name:'下载 ZIP 素材包'}).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('ai-seed-'+id+'.zip')
  const stream = await download.createReadStream()
  const chunks: Buffer[] = []
  for await (const chunk of stream!) chunks.push(Buffer.from(chunk))
  const zip = Buffer.concat(chunks)
  expect(zip.subarray(0,2).toString()).toBe('PK')
  for (const name of ['01_cover.jpg','03_image.jpg','title.txt','caption.txt','hashtags.txt','product.json','manifest.json']) expect(zip.includes(Buffer.from(name))).toBeTruthy()
  expect(zip.includes(Buffer.from('04_image.jpg'))).toBeFalsy()
  await page.getByRole('button',{name:'预览结果图片 1'}).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.setViewportSize({width:390,height:844})
  await page.screenshot({path:'../storage/qa/workflow-results-mobile.png',fullPage:true})
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.goto('/create-content')
  await expect(page.getByLabel('AI 模特',{exact:true})).toBeEnabled()
  await page.screenshot({path:'../storage/qa/workflow-create-mobile.png',fullPage:true})
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.goto('/tasks')
  const row = page.locator('.task-row').filter({has:page.locator('a[href="/tasks/'+id+'"]')})
  await expect(row).toBeVisible()
  await page.screenshot({path:'../storage/qa/workflow-tasks-mobile.png',fullPage:true})
  await row.getByRole('button',{name:'删除',exact:true}).click()
  await page.getByRole('button',{name:'确认删除',exact:true}).click()
  await expect(row).toHaveCount(0)
  taskIds = []
  expect(errors).toEqual([])
})
test('submission outage retry, copy guard, deletion and empty selection',async ({page}) => {
  await choose(page)
  await page.route('**/api/v1/generation/tasks',r => r.request().method()==='POST' ? r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'演示服务暂时不可用'})}) : r.continue())
  await page.getByRole('button',{name:'生成 Mock 内容',exact:true}).click()
  await expect(page.getByRole('alert')).toContainText('演示服务暂时不可用')
  await page.unroute('**/api/v1/generation/tasks')
  const id = await generate(page)
  await page.getByLabel('标题',{exact:true}).fill('未保存的文字')
  await page.getByRole('link',{name:'← 返回生成记录'}).click()
  await expect(page.getByRole('dialog')).toContainText('文案修改尚未保存')
  await page.getByRole('button',{name:'继续编辑',exact:true}).click()
  await expect(page).toHaveURL(new RegExp('/tasks/'+id+'$'))
  await page.getByRole('button',{name:'保存文案',exact:true}).click()
  await expect(page.getByText('文案已保存。',{exact:true})).toBeVisible()
  for (let n=1;n<=4;n++) {
    await expect(page.getByRole('checkbox',{name:'选择图片 '+n,exact:true})).toBeEnabled()
    await page.getByRole('checkbox',{name:'选择图片 '+n,exact:true}).uncheck()
    await expect(page.getByRole('checkbox',{name:'选择图片 '+n,exact:true})).not.toBeChecked()
  }
  await expect(page.getByRole('button',{name:'下载 ZIP 素材包'})).toBeDisabled()
  await page.getByRole('button',{name:'删除图片',exact:true}).first().click()
  await page.getByRole('button',{name:'确认删除',exact:true}).click()
  await expect(page.locator('.result-card')).toHaveCount(3)
})
test('missing image blocks creation and settings report Mock mode',async ({page}) => {
  const model = await (await page.request.get('/api/v1/models/'+modelId)).json()
  await page.request.delete(model.reference_images[0].image_url,{headers})
  await choose(page)
  await expect(page.getByRole('button',{name:'生成 Mock 内容',exact:true})).toBeDisabled()
  await expect(page.getByText('模特和商品都需要至少一张图片。',{exact:true})).toBeVisible()
  await page.goto('/settings')
  await expect(page.getByText('Mock 本地演示',{exact:true})).toBeVisible()
  await expect(page.getByText('· 服务可用',{exact:false})).toBeVisible()
})

test('selection and ZIP failure recover without losing saved state', async ({page}) => {
  await choose(page)
  const id = await generate(page)
  await page.route('**/api/v1/generation/results/*', route =>
    route.request().method() === 'PATCH'
      ? route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'图片选择保存失败'})})
      : route.continue())
  await page.getByRole('checkbox',{name:'选择图片 1',exact:true}).click()
  await expect(page.getByRole('alert')).toContainText('图片选择保存失败')
  await expect(page.getByRole('checkbox',{name:'选择图片 1',exact:true})).toBeChecked()
  expect((await (await page.request.get('/api/v1/generation/tasks/'+id)).json()).results[0].is_selected).toBe(true)
  await page.unroute('**/api/v1/generation/results/*')
  await page.route('**/api/v1/generation/tasks/*/export',route => route.fulfill({
    status:503,contentType:'application/json',body:JSON.stringify({detail:'素材存储暂时不可用'}),
  }))
  await page.getByRole('button',{name:'下载 ZIP 素材包'}).click()
  await expect(page.getByRole('alert')).toContainText('素材存储暂时不可用')
  await expect(page.getByRole('button',{name:'下载 ZIP 素材包'})).toBeEnabled()
  await page.unroute('**/api/v1/generation/tasks/*/export')
  const waiting = page.waitForEvent('download')
  await page.getByRole('button',{name:'下载 ZIP 素材包'}).click()
  expect((await waiting).suggestedFilename()).toBe('ai-seed-'+id+'.zip')
})

test('partial task displays retry and retains edited copy', async ({page}) => {
  await choose(page)
  const id = await generate(page)
  const response = await page.request.get('/api/v1/generation/tasks/'+id)
  const completed = await response.json()
  // Backend failure injection is tested in pytest; this isolates the browser retry state.
  await page.route('**/api/v1/generation/tasks/'+id, route => route.fulfill({
    status:200,contentType:'application/json',
    body:JSON.stringify({...completed,status:'PARTIAL',can_retry:true,result_count:2,results:completed.results.slice(0,2),error_message:'模拟部分生成失败'}),
  }))
  await page.reload()
  await expect(page.getByRole('button',{name:'重试并补齐图片'})).toBeVisible()
  await expect(page.locator('.result-card')).toHaveCount(2)
  await page.getByLabel('标题',{exact:true}).fill('重试时保留的未保存文案')
  await page.route('**/api/v1/generation/tasks/'+id+'/retry',route => route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify(completed),
  }))
  await page.unroute('**/api/v1/generation/tasks/'+id)
  await page.getByRole('button',{name:'重试并补齐图片'}).click()
  await expect(page.locator('.result-card')).toHaveCount(4)
  await expect(page.getByLabel('标题',{exact:true})).toHaveValue('重试时保留的未保存文案')
  await expect(page.getByRole('button',{name:'下载 ZIP 素材包'})).toBeDisabled()
  await page.getByRole('button',{name:'保存文案',exact:true}).click()
  await expect(page.getByText('文案已保存。',{exact:true})).toBeVisible()
})


test('real mode labels and missing credentials block generation without paid calls',async ({page}) => {
  await page.route('**/api/v1/providers',route => route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify({
      provider:'seedream',mock:false,available:false,requires_api_key:true,operations:[],
      message:'未配置图片 API Key；请在服务端 .env 配置后重启。',
      copy_mode:'local',copy_available:true,configuration_only:true,
    }),
  }))
  await choose(page)
  await expect(page.getByRole('button',{name:'生成 AI 内容',exact:true})).toBeDisabled()
  await expect(page.getByText('AI 图片生成',{exact:true})).toBeVisible()
  await expect(page.getByText('未配置图片 API Key；请在服务端 .env 配置后重启。',{exact:true})).toBeVisible()
  await page.goto('/settings')
  await expect(page.getByText('Seedream 图片服务',{exact:true})).toBeVisible()
  await page.screenshot({path:'../storage/qa/mvp-configuration-missing.png',fullPage:true})
})

test('AI provenance and copy status render independently of current provider',async ({page}) => {
  await choose(page)
  const id = await generate(page)
  const task = await (await page.request.get('/api/v1/generation/tasks/'+id)).json()
  await page.route('**/api/v1/generation/tasks/'+id,route => route.fulfill({
    status:200,contentType:'application/json',
    body:JSON.stringify({...task,is_mock:false,copy:{...task.copy,source:'openai'}}),
  }))
  await page.reload()
  await expect(page.getByText('AI 生成结果',{exact:true})).toBeVisible()
  await expect(page.getByText('AI 文案草稿',{exact:true})).toBeVisible()
  await expect(page.getByText('Mock 演示结果',{exact:true})).toHaveCount(0)
})


test('clothing picker shows thumbnails and supports search on mobile', async ({page}) => {
  const product = await (await page.request.get('/api/v1/products/'+productId)).json()
  await page.goto('/create-content')
  const picker = page.getByRole('combobox',{name:'衣服',exact:true})
  await picker.click()
  await picker.fill(product.name)
  const option = page.getByRole('option').filter({hasText:product.name})
  await expect(option).toHaveCount(1)
  await expect.poll(() => option.locator('img').evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true)
  await page.screenshot({path:'../storage/qa/clothing-picker-desktop.png',fullPage:true})
  await page.keyboard.press('Escape')
  await page.setViewportSize({width:390,height:844})
  await picker.click()
  await picker.fill(product.name)
  await expect(option.locator('img')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({path:'../storage/qa/clothing-picker-mobile.png',fullPage:true})
  await option.click()
  await expect(page.locator('.selected-material').filter({hasText:product.name}).locator('img')).toBeVisible()
})


test('phone QR transfers selected images and saved copy without account login', async ({page,browser}) => {
  await choose(page)
  const id = await generate(page)
  await page.getByRole('checkbox',{name:'选择图片 4',exact:true}).uncheck()
  await page.getByLabel('标题',{exact:true}).fill('扫码穿搭分享')
  await expect(page.getByRole('button',{name:'手机发布助手',exact:true})).toBeDisabled()
  await page.getByRole('button',{name:'保存文案',exact:true}).click()
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/mobile-transfer') && r.request().method()==='POST')
  await page.getByRole('button',{name:'手机发布助手',exact:true}).click()
  const response = await responsePromise
  expect(response.status()).toBe(200)
  const transfer = await response.json()
  await expect(page.getByRole('img',{name:'手机取图二维码'})).toBeVisible()
  const phoneContext = await browser.newContext({viewport:{width:390,height:844}})
  const phone = await phoneContext.newPage()
  try {
    const url = new URL(transfer.url)
    await phone.goto('http://localhost:5173'+url.pathname+url.hash)
    await expect(phone.getByRole('heading',{name:'把这组穿搭带到得物'})).toBeVisible()
    await expect(phone.locator('.mobile-image-button img')).toHaveCount(3)
    await expect(phone.getByLabel('完整发布文案')).toHaveValue(/扫码穿搭分享/)
    await expect.poll(() => phone.locator('.mobile-image-button img').first().evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true)
    await phone.getByRole('button',{name:'一键复制完整文案'}).click()
    await expect(phone.getByRole('status')).toContainText(/已复制|已选中/)
    await phone.screenshot({path:'../storage/qa/mobile-publish-iphone.png',fullPage:true})
    expect(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await phone.getByRole('button',{name:'打开穿搭图片 1',exact:true}).click()
    await expect(phone.getByRole('dialog')).toBeVisible()
    await page.getByRole('button',{name:'停止本次取图'}).click()
    await phone.reload()
    await expect(phone.getByRole('alert')).toContainText('取图链接已失效')
    expect((await phone.request.get('/api/v1/generation/tasks/'+id)).status()).toBe(401)
  } finally { await phoneContext.close() }
})

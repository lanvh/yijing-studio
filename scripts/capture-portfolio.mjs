import { chromium } from '../frontend/node_modules/@playwright/test/index.mjs'
import { readFileSync } from 'node:fs'
const presets = {scenes:{studio:'摄影棚',bookstore:'书店'},styles:{casual:'休闲',american_vintage:'美式复古'},poses:{front_standing:'正面站姿'},counts:[1,2,4,6]}
const model = {id:'demo-model',name:'小林 · 演示模特',gender:'female',reference_images:[{image_url:'/api/v1/demo/model.png'}]}
const product = {id:'demo-product',name:'白色运动鞋 · 演示素材',processed_images:[{image_url:'/api/v1/demo/product.png'}]}
const browser = await chromium.launch({channel:'msedge',headless:true})
async function surface(authenticated, viewport) {
 const page = await browser.newPage({viewport})
 await page.route('**/api/v1/**',async route => {
  const path = new URL(route.request().url()).pathname
  if (path.endsWith('.png') || path.includes('/images/')) {
   const fixture = path.includes('model') ? 'reference.png' : 'product.png'
   return route.fulfill({status:200,contentType:'image/png',body:readFileSync(new URL('../frontend/tests/fixtures/'+fixture,import.meta.url))})
  }
  let data = {}
  if(path.endsWith('/auth/me')) {
   if(!authenticated) return route.fulfill({status:401,contentType:'application/json',body:'{"detail":"演示未登录"}'})
   data={id:'demo',email:'demo@example.com',display_name:'演示创作者',role:'user'}
  } else if(path.endsWith('/generation/options')) data=presets
  else if(path.endsWith('/providers')) data={provider:'mock',available:true,mock:true,copy_mode:'local',copy_available:true,message:'演示模式'}
  else if(path.endsWith('/models')) data={items:[model],total:1}
  else if(path.endsWith('/products')) data={items:[product],total:1}
  else if(path.includes('/mobile-publish/')) data={title:'日常搭配灵感 ✨',caption:'【Mock 流程演示，非真实试穿】\n\n这是用于展示界面与操作流程的示例文案。\n\n保存图片、复制文案，再到得物编辑发布。',hashtags:['穿搭灵感','日常搭配','AI创作展示'],expires_at:1999999999,images:[{id:'demo-image',name:'穿搭图片 1'}]}
  else return route.fulfill({status:404,contentType:'application/json',body:'{"detail":"仅展示 Mock 内容"}'})
  return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)})
 })
 return page
}
try {
 const login=await surface(false,{width:1440,height:1000})
 await login.goto('http://localhost:5173/login');await login.getByRole('button',{name:/进入摄影棚/}).waitFor({state:'visible'})
 await login.screenshot({path:'docs/images/login.png',fullPage:true});await login.close()
 const create=await surface(true,{width:1440,height:1000})
 await create.goto('http://localhost:5173/create-content')
 await create.getByLabel('AI 模特',{exact:true}).selectOption(model.id)
 await create.getByRole('combobox',{name:'衣服',exact:true}).click()
 await create.getByRole('option').filter({hasText:product.name}).click()
 await create.getByLabel('场景',{exact:true}).selectOption('bookstore')
 await create.getByLabel('风格',{exact:true}).selectOption('american_vintage')
 await create.getByLabel('自定义方向（选填）',{exact:true}).fill('傍晚书店、自然光线、美式复古氛围，保留参考人物和衣服外观。')
 await create.locator('.selected-material img').last().waitFor()
 await create.screenshot({path:'docs/images/create-content.png',fullPage:true});await create.close()
 const phone=await surface(false,{width:390,height:844})
 await phone.goto('http://localhost:5173/mobile-publish/demo#mock-portfolio-token')
 await phone.locator('.mobile-image-button img').waitFor()
 await phone.screenshot({path:'docs/images/mobile-publish.png',fullPage:true});await phone.close()
 console.log('Captured portfolio screenshots using intercepted Mock data only.')
} finally {await browser.close()}

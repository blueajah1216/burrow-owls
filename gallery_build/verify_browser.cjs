/* Use a disposable local database with GALLERY_HOSTS=127.0.0.1,thegreatgallery.art
 * and GALLERY_CANONICAL_HOST=127.0.0.1. Never run account writes on a live site. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
const preview='http://127.0.0.1:5058',base=preview;
const artifacts='/private/tmp/gallery-qa';fs.mkdirSync(artifacts,{recursive:true});
const paintings=JSON.parse(fs.readFileSync('data/fineart/gallery.json'));
const photos=JSON.parse(fs.readFileSync('data/photo/gallery.json'));
const painting=paintings.paintings.find(p=>!p.n),photo=photos.photos.find(p=>!p.n);
const user='qa_'+Date.now(),password='Local-gallery-qa-123';
const errors=[];
async function routing(context){await context.route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin!==base)return route.abort();
 try {const response=await route.fetch({maxRedirects:0,url:preview+url.pathname+url.search,headers:route.request().headers()});
 const headers=response.headers(); if(headers.location?.startsWith('http')){const target=new URL(headers.location);headers.location=base+target.pathname+target.search;} await route.fulfill({response,headers});} catch(e) {if (!/disposed|closed|cancelled/.test(e.message)) throw e;}
});}
async function signup(page,name){
 await page.goto(base+'/signup');await page.getByLabel('Your name').fill('A Gallery Lover');await page.getByLabel('Username').fill(name);
 await page.locator('input[name=password]').fill(password);await page.getByLabel('Password again',{exact:true}).fill(password);
 await page.locator('.gg-auth-card button[type=submit]').click();await page.waitForURL(base+'/my-gallery');await page.waitForLoadState('networkidle');await page.waitForFunction(()=>window.Gallery);
}
async function login(page){await page.goto(base+'/login');await page.getByLabel('Username').fill(user);await page.locator('input[name=password]').fill(password);await page.locator('.gg-auth-card button').click();await page.waitForURL(base+'/my-gallery');}
async function checkWidth(page){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overflow '+page.url()+' at '+page.viewportSize().width);}
async function save(page,path,selector){await page.goto(base+path);await page.evaluate(()=>Gallery.ready);const button=page.locator(selector).first();await button.click();await page.waitForFunction(s=>document.querySelector(s)?.getAttribute('aria-pressed')==='true',selector);}
(async()=>{const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});try{
 const context=await browser.newContext({viewport:{width:1440,height:1050}});await routing(context);const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 for(const [path,name] of [['/','paintings'],['/photography/','photography'],['/music','music']]){
  await page.goto(base+path);await page.locator('.gg-account-links .gg-create').waitFor();assert(await page.locator('.gg-invitation').isVisible());await checkWidth(page);await page.screenshot({path:`${artifacts}/${name}-desktop.png`});
 }
 for(const [path,kind] of [['/','painting'],['/photography/','photo']]) {
  await page.goto(base+path);const first=page.locator('.heart').first();await first.waitFor();const id=await first.getAttribute('data-gallery-id');assert(id);
  await first.click();await page.waitForFunction(([k,id])=>Gallery.has(k,id),[kind,id]);await page.locator(`.heart[data-gallery-id="${id}"]`).click();await page.waitForFunction(([k,id])=>!Gallery.has(k,id),[kind,id]);
 }
 await page.goto(base+'/signup');await checkWidth(page);await page.screenshot({path:artifacts+'/signup-desktop.png',fullPage:true});
 await save(page,'/p/'+painting.id,'#fav');await save(page,'/photography/p/'+photo.id,'#fav');await save(page,'/music/history/pieces/bach-1','[data-gallery-id="bach-1"]');
 await signup(page,user);await page.locator('.gg-item').nth(2).waitFor();assert.equal(await page.locator('.gg-item').count(),3);await checkWidth(page);await page.screenshot({path:artifacts+'/my-gallery-desktop.png',fullPage:true});
 await page.reload();await page.locator('.gg-item').nth(2).waitFor();assert.equal(await page.locator('.gg-item').count(),3);
 await page.locator('.gg-tabs a').filter({hasText:'Music'}).click();assert.equal(await page.locator('.gg-item').count(),1);await page.getByRole('searchbox').fill('Bach');await page.getByRole('button',{name:'Find',exact:true}).click();assert.equal(await page.locator('.gg-item').count(),1);
 // API failure must leave the saved state intact and offer a retry.
 await page.goto(base+'/music/history/pieces/bach-1');await page.route('**/api/gallery',route=>route.fulfill({status:503,body:'unavailable'}));
 await page.locator('[data-gallery-id="bach-1"]').click();await page.getByRole('button',{name:'Try again'}).waitFor();assert.equal(await page.locator('[data-gallery-id="bach-1"]').getAttribute('aria-pressed'),'true');await page.unroute('**/api/gallery');await page.getByRole('button',{name:'Try again'}).click();await page.waitForFunction(()=>!Gallery.has('music','bach-1'));
 // A second device must agree and must not resurrect removed favorites from its cache.
 const device=await browser.newContext({});await routing(device);const remote=await device.newPage();remote.on('pageerror',e=>errors.push(e.message));await login(remote);assert.equal(await remote.locator('.gg-item').count(),2);
 await page.goto(base+'/music/practice');await page.waitForFunction(()=>window.choirState);await page.locator('#practice-save').click();await page.waitForFunction(()=>Gallery.has('music','practice:hava-nagila'));
 await remote.reload();await remote.locator('[data-saved-kind="music"]').waitFor();assert.equal(await remote.locator('.gg-item').count(),3);
 await remote.locator('[data-saved-kind="photo"] .gg-save').click();await remote.waitForFunction(()=>document.querySelectorAll('.gg-item').length===2);
 await page.goto(base+'/my-gallery');assert.equal(await page.locator('.gg-item').count(),2);
 // Browser-local photos predating accounts offer explicit import.
 const legacy=await browser.newContext({});await routing(legacy);const old=await legacy.newPage();await old.goto(base+'/login');await old.evaluate(id=>localStorage.setItem('ph_favs',JSON.stringify([id])),photo.id);await login(old);await old.locator('[data-gallery-import]:visible').waitFor();await old.getByRole('button',{name:'Add them to my gallery'}).click();await old.locator('[data-saved-kind="photo"]').waitFor();assert.equal(await old.locator('.gg-item').count(),3);
 await page.setViewportSize({width:390,height:844});await page.goto(base+'/my-gallery');await checkWidth(page);await page.screenshot({path:artifacts+'/my-gallery-mobile.png',fullPage:true});
 await page.goto(base+'/account');await checkWidth(page);await page.screenshot({path:artifacts+'/account-mobile.png',fullPage:true});await page.getByRole('button',{name:'Log out',exact:true}).click();await page.waitForURL(base+'/');assert.equal(await page.evaluate(()=>localStorage.getItem('ph_favs')),null);
 for(const [path,name] of [['/','paintings'],['/photography/','photography'],['/music','music'],['/music/concerts','concerts'],['/music/history','history'],['/music/practice','practice'],['/signup','signup']]){await page.goto(base+path);await checkWidth(page);await page.screenshot({path:`${artifacts}/${name}-mobile.png`});}
 const touch=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await routing(touch);const touchPage=await touch.newPage();for(const path of ['/','/photography/']){await touchPage.goto(base+path);await touchPage.locator('.heart').first().waitFor();assert.equal(await touchPage.locator('.heart').first().evaluate(n=>getComputedStyle(n).opacity),'1');}await touch.close();
 for(const width of [320,768]) {await page.setViewportSize({width,height:900});for(const path of ['/','/photography/','/music','/signup']) {await page.goto(base+path);await checkWidth(page);}}
 await page.setViewportSize({width:390,height:844});
 await signup(page,user+'_other');assert.equal(await page.locator('.gg-item').count(),0);assert(await page.locator('.gg-discover').isVisible());
 // Actual no-JS form save, using the same session in a new context.
 const nojs=await browser.newContext({javaScriptEnabled:false,storageState:await context.storageState()});await routing(nojs);const fallback=await nojs.newPage();await fallback.goto(base+'/music/history/pieces/bach-1');await fallback.locator('[data-gallery-id="bach-1"]').click();await fallback.goto(base+'/my-gallery');assert.equal(await fallback.locator('.gg-item').count(),1);
 assert.deepEqual(errors,[]);console.log('Passed: guest saves in all three sections; signup/import; mixed gallery/filter/search; persistence; error/retry; practice saves; second-device sync; legacy photo import; logout/account isolation; mobile widths; no-JS save.');console.log('Screenshots: '+artifacts);
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});

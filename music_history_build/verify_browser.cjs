/* Run while Flask serves 127.0.0.1:5058. Screenshots stay outside the repo. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require('playwright');
const preview = process.env.MUSIC_HISTORY_TEST_URL || 'http://127.0.0.1:5058';
const base = 'https://thegreatgallery.art';
const artifacts = '/private/tmp/music-history-qa';
fs.mkdirSync(artifacts, {recursive:true});

// Exercise the production host middleware against local code without live traffic.
async function routePreview(context) {
  await context.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== base) return route.abort();
    const response = await route.fetch({
      url:`${preview}${url.pathname}${url.search}`,
      headers:{...request.headers(),host:'thegreatgallery.art'},
    });
    return route.fulfill({response});
  });
}

(async () => {
  const browser = await chromium.launch({
    executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,
  });
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1050}});
    await routePreview(page.context());
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const visible = () => page.locator('[data-item]:visible').count();
    const noOverflow = async () => assert(await page.evaluate(() =>
      document.documentElement.scrollWidth <= innerWidth), `Overflow on ${page.url()}`);
    await page.goto(`${base}/music/history`);
    assert.equal(await visible(), 100);
    await page.screenshot({path:`${artifacts}/desktop-hero.png`});
    await page.locator('#timeline').evaluate(el => window.scrollTo({top:el.offsetTop-20,behavior:'instant'}));
    await page.screenshot({path:`${artifacts}/desktop-timeline.png`});
    await page.locator('#history-search').fill('beethoven');
    assert.equal(await visible(), 7);
    assert(new URL(page.url()).searchParams.get('q') === 'beethoven');
    await page.locator('#era-filter').selectOption('romantic');
    assert.equal(await visible(), 4);
    await page.locator('.view-tabs a', {hasText:'50 composers'}).click();
    assert.equal(await visible(), 0); // Beethoven's stylistic chapter is Classical.
    assert(await page.locator('#empty-state').isVisible());
    await page.locator('#clear-filters').click();
    assert.equal(await visible(), 50);
    await page.locator('#history-search').fill('dvorak');
    assert.equal(await visible(), 1);
    await page.locator('.composer-item:visible h3 a').click();
    assert.match(await page.locator('h1').innerText(), /Dvořák/);
    assert.equal(await page.locator('.work-item').count(), 2);
    await page.screenshot({path:`${artifacts}/desktop-composer.png`,fullPage:true});
    await page.goto(`${base}/music/history/pieces/stravinsky-2`);
    assert.match(await page.locator('h1').innerText(), /Rite of Spring/);
    assert(await page.locator('a[href^="https://www.youtube.com/results?"]').count());
    await noOverflow();
    await page.screenshot({path:`${artifacts}/desktop-piece.png`,fullPage:true});
    for (const width of [390, 768]) {
      await page.setViewportSize({width,height:844});
      await page.goto(`${base}/music/history`);
      await noOverflow();
      await page.screenshot({path:`${artifacts}/${width}-hero.png`});
      await page.locator('#timeline').evaluate(el => window.scrollTo({top:el.offsetTop-20,behavior:'instant'}));
      await page.screenshot({path:`${artifacts}/${width}-timeline.png`});
      await page.locator('#history-search').fill('chopin');
      assert.equal(await visible(), 3);
      await page.locator('.work-item:visible h3 a').first().click();
      await noOverflow();
      await page.screenshot({path:`${artifacts}/${width}-piece.png`,fullPage:true});
      await page.goto(`${base}/music/history/composers/clara-schumann`);
      await noOverflow();
      await page.screenshot({path:`${artifacts}/${width}-composer.png`,fullPage:true});
    }
    await page.setViewportSize({width:390,height:844});
    await page.goto(`${base}/music`);
    await page.waitForFunction(() => window.choirState);
    await page.locator('#play:not(:disabled)').waitFor();
    assert.equal(await page.locator('.song-option').count(), 92);
    await page.locator('#play').click();
    await page.waitForFunction(() => window.choirState().position > .1);
    await page.locator('#play').click();
    await noOverflow();
    await page.screenshot({path:`${artifacts}/mobile-discovery.png`,fullPage:true});
    await page.locator('.music-history-invitation').click();
    assert.match(page.url(), /\/music\/history$/);
    const nojs = await browser.newContext({javaScriptEnabled:false,reducedMotion:'reduce',viewport:{width:390,height:844}});
    await routePreview(nojs);
    const fallback = await nojs.newPage();
    await fallback.goto(`${base}/music/history`);
    await fallback.locator('#history-search').fill('dvorak');
    await fallback.locator('.filter-submit').click();
    assert.equal(await fallback.locator('[data-item]:visible').count(), 2);
    assert.equal(errors.length, 0, errors.join('\n'));
    console.log('Passed: 100 works, 50 composers, search, eras, view changes, biography links, piece pages, mobile, tablet, no-JS form, and discovery.');
    console.log(`Screenshots: ${artifacts}`);
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode = 1;});

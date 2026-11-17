/* Local QA: real Umami tracker, intercepted collection requests (no live stats).
 * Run while Flask serves 127.0.0.1:5057. Requires installed Playwright/Chrome.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require('playwright');
const origin = 'https://thegreatgallery.art';
const artifacts = '/private/tmp/gallery-analytics-qa';
fs.mkdirSync(artifacts, {recursive:true});

(async () => {
  const browser = await chromium.launch({
    executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true,
  });
  try {
    const context = await browser.newContext({viewport:{width:1440, height:1000}});
    const events = [];
    const errors = [];
    const blocked = [];
    await context.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.hostname === 'thegreatgallery.art') {
        const response = await route.fetch({
          url:`http://127.0.0.1:5057${url.pathname}${url.search}`,
          headers:{...request.headers(), host:'thegreatgallery.art'},
        });
        return route.fulfill({response});
      }
      if (url.hostname === 'cloud.umami.is' && url.pathname === '/script.js') return route.continue();
      if (['cloud.umami.is', 'gateway.umami.is'].includes(url.hostname)) {
        events.push(request.postDataJSON());
        return route.fulfill({status:200, contentType:'application/json', body:'{}'});
      }
      blocked.push(request.url());
      return route.abort(); // Fonts/images do not affect telemetry verification.
    });
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    await page.clock.install();
    await page.goto(`${origin}/music/practice?search=PRIVATE-SEARCH#PRIVATE-FRAGMENT`);
    await page.waitForFunction(() => window.umami && window.choirState);
    await page.waitForFunction(() => document.querySelector('#play:not(:disabled)'));
    await page.waitForTimeout(1000);
    assert.equal(await page.locator('#gallery-analytics').getAttribute('data-website-id'),
      '396a7fd0-b7ee-462b-992d-41f2b601cd8a');
    assert(events.some(e => e.payload?.url === '/music/practice' && !e.payload?.name),
      `Initial music pageview: ${JSON.stringify(events)}, blocked: ${JSON.stringify(blocked)}`);
    assert(!JSON.stringify(events).includes('PRIVATE-'), 'Query/fragment redaction');

    const cleaned = await page.evaluate(() => window.galleryAnalyticsBeforeSend('event', {
      url:'/music?secret=PRIVATE', referrer:'https://thegreatgallery.art/login?next=PRIVATE',
    }));
    assert.equal(cleaned.url, '/music');
    assert.equal(cleaned.referrer, '/');
    assert.equal(await page.evaluate(() => window.galleryAnalyticsBeforeSend('event', {
      url:'/account?secret=PRIVATE',
    })), false);

    // Start with a clean visibility boundary and measure a complete minute.
    await page.evaluate(() => {
      Object.defineProperty(document, 'visibilityState', {configurable:true, value:'hidden'});
      document.dispatchEvent(new Event('visibilitychange'));
      Object.defineProperty(document, 'visibilityState', {configurable:true, value:'visible'});
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await page.waitForTimeout(200);
    let start = events.length;
    await page.clock.runFor(61000);
    await page.evaluate(() => {
      Object.defineProperty(document, 'visibilityState', {configurable:true, value:'hidden'});
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await page.waitForTimeout(200);
    const batches = events.slice(start).filter(e => e.payload?.name === 'engagement');
    const seconds = batches.reduce((total, e) => total + e.payload.data.seconds, 0);
    assert(seconds >= 60 && seconds <= 63 && batches.every(e => e.payload.data.section === 'music'),
      `A visible minute on a single page is recorded: ${JSON.stringify(batches)}`);
    start = events.length;
    await page.clock.runFor(180000);
    await page.waitForTimeout(200);
    assert.equal(events.slice(start).filter(e => e.payload?.name === 'engagement').length, 0,
      'Hidden tabs add no engagement');
    await page.evaluate(() => {
      Object.defineProperty(document, 'visibilityState', {configurable:true, value:'visible'});
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await page.clock.resume();
    start = events.length;
    await page.evaluate(async () => {
      Object.defineProperty(navigator, 'doNotTrack', {configurable:true, value:'1'});
      await window.umami.track('privacy-check');
      Object.defineProperty(navigator, 'doNotTrack', {configurable:true, value:null});
      localStorage.setItem('umami.disabled', '1');
      await window.umami.track('privacy-check');
      localStorage.removeItem('umami.disabled');
    });
    await page.waitForTimeout(200);
    assert.equal(events.length, start, 'DNT and local opt-out suppress collection');
    await page.screenshot({path:`${artifacts}/music.png`, fullPage:true});
    await page.locator('#play').click();
    await page.waitForFunction(() => window.choirState().playing);
    await page.locator('#play').click();

    for (const path of ['/', '/photography/', '/games']) {
      await page.goto(origin + path);
      await page.waitForFunction(() => window.umami);
      assert.equal(await page.locator('#gallery-analytics').count(), 1);
    }
    await page.setViewportSize({width:390, height:844});
    await page.goto(`${origin}/photography/`);
    await page.screenshot({path:`${artifacts}/photography-mobile.png`, fullPage:true});
    for (const path of ['/login', '/signup', '/account', '/lovers']) {
      await page.goto(origin + path);
      assert.equal(await page.locator('#gallery-analytics').count(), 0, `Excluded ${path}`);
    }
    // Verify host scoping through a direct local response, without the gallery route override.
    const response = await context.request.get('http://127.0.0.1:5057/fineart/music/practice');
    assert(!(await response.text()).includes('cloud.umami.is/script.js'));
    assert(!JSON.stringify(events).includes('PRIVATE-'), 'Queries never leak through later referrers');
    // The music room remains usable when an analytics blocker rejects the tracker.
    await page.route('https://cloud.umami.is/script.js', route => route.abort());
    await page.goto(`${origin}/music/practice`);
    await page.waitForFunction(() => window.choirState && !document.querySelector('#play').disabled);
    await page.locator('#play').click();
    await page.waitForFunction(() => window.choirState().playing);
    await page.locator('#play').click();
    assert.equal(errors.length, 0, errors.join('\n'));
    console.log(`Passed: ${events.length} intercepted events; pageviews, privacy, engagement, hidden tabs, opt-outs, blocked tracker, playback, host scope. Screenshots: ${artifacts}`);
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });

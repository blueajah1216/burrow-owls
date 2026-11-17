/* Run with node choir_build/verify_browser.cjs while Flask serves port 5057.
 * Uses the workspace's existing Playwright and installed headless Chrome.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require('playwright');
const base = process.env.CHOIR_TEST_URL || 'http://127.0.0.1:5057/fineart/music';
const artifacts = process.env.CHOIR_TEST_ARTIFACTS || '/private/tmp/gallery-choir-qa';
fs.mkdirSync(artifacts, {recursive:true});
(async () => {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440, height:1100}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base);
    await page.waitForFunction(() => window.choirState);
    const state = () => page.evaluate(() => window.choirState());
    assert.equal((await state()).song, 'hava-nagila');
    assert.equal(await page.locator('.song-option').count(), 92);
    await page.locator('[data-collection="Jewish songs"]').click();
    assert.equal(await page.locator('.song-option:visible').count(), 18);
    await page.screenshot({path:`${artifacts}/jewish-songbook.png`, fullPage:true});
    await page.locator('#song-search').fill('הבה נגילה');
    assert.equal(await page.locator('.song-option:visible').count(), 1);
    await page.locator('#song-search').fill('Ladino');
    assert.equal(await page.locator('.song-option:visible').count(), 1);
    await page.locator('.song-option:visible').click();
    assert.equal((await state()).song, 'durme-durme');
    await page.locator('[data-collection="Folk songs around the world"]').click();
    assert.equal(await page.locator('.song-option:visible').count(), 22);
    await page.locator('#song-search').fill('Jasmine Flower');
    assert.equal(await page.locator('.song-option:visible').count(), 1);
    await page.locator('.song-option:visible').click();
    assert.equal((await state()).song, 'mo-li-hua');
    await page.locator('#song-search').fill('Korea');
    assert.equal(await page.locator('.song-option:visible').count(), 1);
    await page.locator('.song-option:visible').click();
    assert.equal((await state()).song, 'arirang');
    await page.locator('#song-search').fill('');
    await page.screenshot({path:`${artifacts}/world-songbook.png`, fullPage:true});
    await page.locator('#category').selectOption('all');
    await page.locator('[data-song="hava-nagila"]').click();
    await page.screenshot({path:`${artifacts}/desktop.png`, fullPage:true});
    await page.locator('#play').click();
    await page.waitForTimeout(1600);
    let active = await state();
    assert.equal(active.playing, true);
    assert.equal(active.audioState, 'running');
    assert(active.position > .7);
    assert(await page.locator('.note-playing').count() > 0);
    assert(Number(await page.locator('.playhead').getAttribute('x')) > 0);
    await page.screenshot({path:`${artifacts}/playing.png`});
    await page.locator('[data-solo="1"]').click();
    assert.deepEqual((await state()).enabled, [false,true,false,false]);
    await page.locator('#backing').click();
    assert.deepEqual((await state()).enabled, [true,false,true,true]);
    await page.locator('#all-voices').click();
    await page.locator('#speed').evaluate(el => { el.value='50'; el.dispatchEvent(new Event('input',{bubbles:true})); });
    await page.waitForTimeout(200);
    assert.equal((await state()).speed, .5);
    assert.equal((await state()).playing, true);
    await page.locator('#play').click();
    const stopped = (await state()).position;
    await page.waitForTimeout(300);
    assert.equal((await state()).position, stopped);
    await page.locator('#seek').evaluate(el => { el.value='500'; el.dispatchEvent(new Event('input',{bubbles:true})); });
    active = await state();
    assert(Math.abs(active.position / active.duration - .5) < .001);
    await page.locator('#restart').click();
    assert.equal((await state()).position, 0);
    await page.locator('#song-search').fill('twinkle');
    assert.equal(await page.locator('.song-option:visible').count(), 1);
    await page.locator('.song-option:visible').click();
    assert.equal((await state()).song, 'twinkle-twinkle-little-star');
    await page.locator('#song-search').fill('');
    await page.locator('#category').selectOption({label:'Anthems'});
    assert.equal(await page.locator('.song-option:visible').count(), 4);
    for (const id of ['o-canada', 'the-star-spangled-banner']) {
      await page.locator(`[data-song="${id}"]`).click();
      assert.equal((await state()).song, id);
      await page.locator('#play').click();
      await page.waitForTimeout(500);
      assert.equal((await state()).playing, true);
      assert((await state()).position > 0);
      await page.locator('#play').click();
      await page.screenshot({path:`${artifacts}/${id}.png`, fullPage:true});
    }
    await page.locator('#category').selectOption('all');
    const midi = await page.locator('#download-midi').evaluate(async el => {
      const bytes = new Uint8Array(await (await fetch(el.href)).arrayBuffer());
      return {header:String.fromCharCode(...bytes.slice(0,4)), length:bytes.length};
    });
    assert.equal(midi.header, 'MThd'); assert(midi.length > 100);
    // Render every arrangement and compare the final score event with audio.
    const scores = await page.evaluate(async () => {
      const songs = await (await fetch(window.CHOIR_LIBRARY_URL)).json();
      const results = [];
      const container = document.createElement('div'); container.id='qa-score'; document.body.appendChild(container);
      for (const song of songs) {
        const tune = ABCJS.renderAbc(container, song.abc, {staffwidth:850, add_classes:true})[0];
        const seq = tune.setUpAudio({qpm:song.tempo,chordsOff:true});
        const tracks = seq.tracks.map(t => t.filter(n => n.cmd==='note'));
        const time = tune.setTiming();
        const audioEnd = seq.totalDuration * 240 / seq.tempo;
        const visualEnd = time[time.length-1].milliseconds / 1000;
        results.push({id:song.id, tracks:tracks.length, warnings:tune.warnings || [], delta:Math.abs(audioEnd-visualEnd), notes:tracks.map(t=>t.length)});
      }
      container.remove(); return results;
    });
    for (const score of scores) {
      assert.equal(score.tracks, 4, score.id);
      assert(score.notes.every(n=>n>0), score.id);
      assert.equal(score.warnings.length, 0, JSON.stringify(score));
      assert(score.delta < .03, JSON.stringify(score));
    }
    await page.locator('[data-song="silent-night"]').click();
    await page.locator('#loop').check();
    await page.locator('#seek').evaluate(el => { el.value='999'; el.dispatchEvent(new Event('input',{bubbles:true})); });
    await page.locator('#play').click();
    await page.waitForTimeout(800);
    assert.equal((await state()).playing, true);
    assert((await state()).position < 1);
    await page.locator('[data-song="hava-nagila"]').click();
    assert.equal((await state()).playing, false);
    assert.equal((await state()).position, 0);
    await page.setViewportSize({width:390, height:844});
    await page.screenshot({path:`${artifacts}/mobile.png`, fullPage:true});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile page overflows');
    assert(await page.locator('#score-scroll').evaluate(el => el.scrollWidth > el.clientWidth), 'Small-screen score must scroll, not shrink illegibly');
    await page.locator('#seek').evaluate(el => { el.value='200'; el.dispatchEvent(new Event('input',{bubbles:true})); });
    await page.locator('#play').click();
    await page.waitForTimeout(500);
    assert(await page.locator('#score-scroll').evaluate(el => {
      const cursor = el.querySelector('.playhead').getBoundingClientRect();
      const pane = el.getBoundingClientRect();
      return cursor.right >= pane.left && cursor.left <= pane.right;
    }), 'Phone score keeps the moving cursor in view');
    await page.locator('#play').click();
    await page.evaluate(() => { window.print = () => {}; });
    await page.locator('#print').click();
    await page.emulateMedia({media:'print'});
    assert(await page.locator('#print-score svg').count() > 1, 'Print score paginates by staff system');
    assert(await page.locator('#print-score svg').evaluateAll(items => items.some(el => el.getBoundingClientRect().height > 100)), 'Print staff systems must be visible');
    await page.screenshot({path:`${artifacts}/print.png`, fullPage:true});
    assert.deepEqual(errors, []);
    console.log(`PASS: ${scores.length} scores, Jewish/world collections, Hebrew/alias/origin search, audio/notation timing, playback, tempo, seek, looping, part controls, MIDI, print and desktop/mobile screenshots. Artifacts: ${artifacts}`);
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode=1;});

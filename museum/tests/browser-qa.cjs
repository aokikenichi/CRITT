/* Re-runnable Chromium acceptance checks. Run from the repository root while
 * a local HTTP preview server serves localhost:8000. Fixture images exist only in
 * intercepted test responses; the shipping catalog remains originals: []. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/Users/aoki/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const output = path.resolve(__dirname, '../qa-results');
fs.mkdirSync(output, { recursive: true });
const results = [], errors = [];
const base = process.env.MUSEUM_QA_ORIGIN || 'http://127.0.0.1:8000';
const executablePath = process.env.CHROMIUM_PATH || '/Users/aoki/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const catalog = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../artworks.json'), 'utf8'));
async function check(name, fn) {
  try { await fn(); results.push({ name, result: 'PASS' }); console.log('PASS', name); }
  catch (error) { results.push({ name, result: 'FAIL', detail: error.message }); console.log('FAIL', name, error.message); }
}
function watch(page) {
  page.on('pageerror', error => errors.push({ type: 'pageerror', message: error.message }));
  page.on('console', message => { if (message.type() === 'error') errors.push({ type: 'console', message: message.text() }); });
  page.on('response', response => { if (response.status() >= 400) errors.push({ type: 'http', status: response.status(), url: response.url() }); });
}
async function openWork(page, id, prefix = '/CRITT/museum/') {
  await page.goto(base + prefix + 'work.html?id=' + id);
  await page.locator('#mode-controls:not([hidden])').waitFor();
  return page.frames().find(frame => frame.url().includes('/works/' + id + '/'));
}
async function state(frame, id) {
  return frame.evaluate(id => id === '009' ? window.__critt09.state() : window.CRITT_WORK10.getState(), id);
}
async function holdKey(page, key, milliseconds = 350) {
  await page.keyboard.down(key); await page.waitForTimeout(milliseconds); await page.keyboard.up(key);
}
(async () => {
  let browser;
  try {
    browser = await chromium.launch({ headless: true, executablePath });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage(); watch(page);
    for (const prefix of ['/museum/', '/CRITT/museum/']) {
      await check(prefix + ' catalog and missing states', async () => {
        await page.goto(base + prefix);
        await page.locator('.work-card').last().waitFor();
        assert.equal(await page.locator('.work-card').count(), 10);
        assert.equal(await page.locator('.work-card.is-missing button[disabled]').count(), 8);
        assert.equal(await page.locator('.work-card.is-available').count(), 2);
        for (let number = 1; number <= 8; number++) {
          await page.goto(base + prefix + 'work.html?id=' + String(number).padStart(3, '0'));
          await page.locator('#missing-work:not([hidden])').waitFor();
          assert.match(await page.locator('#missing-work').innerText(), /未収録|収録準備中/);
          assert.equal(await page.locator('#artwork-frame').getAttribute('src'), null);
          assert.equal(await page.locator('#originals-button').isDisabled(), true);
        }
      });
      for (const query of ['id=999', 'id=9', 'id=009&id=010', '']) {
        await check(prefix + ' rejects ' + (query || 'missing ID'), async () => {
          await page.goto(base + prefix + 'work.html?' + query);
          await page.waitForURL(base + prefix + 'index.html');
        });
      }
    }
    for (const id of ['009', '010']) {
      await check(id + ' rendering and shared controls', async () => {
        const frame = await openWork(page, id);
        await frame.locator('#stage').waitFor();
        assert.equal(await page.locator('#originals-button').isDisabled(), true);
        const pixels = await frame.locator('#stage').evaluate(canvas => {
          const values = canvas.getContext('2d').getImageData(canvas.width / 2, canvas.height / 2, 10, 10).data;
          return Array.from(values).some((v, index) => index % 4 !== 3 && v > 0);
        });
        assert.equal(pixels, true);
        if (id === '009') await frame.waitForFunction(() => Object.values(window.__critt09.assets()).every(Boolean));
        await page.locator('[data-mode="auto"]').click();
        assert.equal((await state(frame, id)).mode, 'auto');
        await page.locator('[data-mode="pause"]').click();
        assert.equal(id === '009' ? (await state(frame, id)).paused : (await state(frame, id)).autoPaused, true);
        await page.locator('[data-mode="manual"]').click();
        const before = await state(frame, id); await holdKey(page, 'w'); const after = await state(frame, id);
        assert(Math.hypot(after.x - before.x, after.z - before.z) > .01);
        await page.locator('#about-button').click();
        await page.keyboard.press('Escape');
        assert.equal(await page.evaluate(() => document.activeElement.id), 'about-button');
        await page.locator('#help-button').click(); await page.keyboard.press('Escape');
        await page.locator('#hide-ui').click();
        assert.equal(await page.locator('#show-ui').isVisible(), true);
        await page.keyboard.press('Escape'); assert.equal(await page.locator('#shell-header').isVisible(), true);
        await page.screenshot({ path: path.join(output, 'desktop-' + id + '.png') });
      });
    }
    await check('009 scenes, gravity, density, reference provenance', async () => {
      const frame = await openWork(page, '009');
      for (let zone = 0; zone < 3; zone++) { await frame.locator('[data-stop="' + zone + '"]').click(); assert.equal((await state(frame, '009')).zone, zone); }
      await frame.locator('[data-g="0"]').click(); assert.equal((await state(frame, '009')).targetGravity, 0);
      await frame.locator('#density').click(); assert.equal((await state(frame, '009')).dense, false);
      await frame.locator('#openOriginals').click();
      assert.match(await frame.locator('#originals').innerText(), /未承認/);
      await page.keyboard.press('Escape'); assert.equal(await frame.locator('#originals').getAttribute('aria-hidden'), 'true');
    });
    await check('010 boundary crossing, local contribution and reset', async () => {
      const frame = await openWork(page, '010');
      await page.locator('[data-mode="manual"]').click();
      await holdKey(page, 'w', 2200); assert((await state(frame, '010')).crossCount > 0);
      await frame.locator('#leave').click(); await frame.locator('#phrase').fill('QA確認用・境界'); await frame.locator('#send').click();
      assert.equal((await state(frame, '010')).phrases, 1);
      await frame.locator('#reset').click(); assert.equal((await state(frame, '010')).crossCount, 0); assert.equal((await state(frame, '010')).phrases, 0);
      await frame.locator('#leave').click(); await page.keyboard.press('Escape');
      assert.equal(await frame.evaluate(() => document.activeElement.id), 'leave');
    });
    await check('approved originals test fixture: zoom, navigation, Esc', async () => {
      const fixture = structuredClone(catalog);
      fixture.items.find(item => item.id === '009').originals = [
        { src: 'qa-fixture-a.svg', alt: 'Test image A', title: 'TEST ONLY A', description: 'Fixture; not adopted artwork', provenance: 'Test response only', approval_status: 'approved' },
        { src: 'qa-fixture-b.svg', alt: 'Test image B', title: 'TEST ONLY B', approval_status: 'approved' },
        { src: 'unapproved.svg', approval_status: 'candidate' }
      ];
      await page.route('**/artworks.json', route => route.fulfill({ json: fixture }));
      await page.route('**/qa-fixture-*.svg', route => route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000"><rect width="1600" height="1000" fill="#225544"/></svg>' }));
      await openWork(page, '009'); await page.locator('#originals-button').click();
      await page.locator('.original-viewer-image:not([hidden])').waitFor();
      assert.equal(await page.locator('.original-viewer-counter').innerText(), '1 / 2');
      const before = await page.locator('.original-viewer-zoom').innerText();
      await page.getByRole('button', { name: '原画を拡大', exact: true }).click();
      assert.notEqual(await page.locator('.original-viewer-zoom').innerText(), before);
      await page.getByRole('button', { name: '次の原画', exact: true }).click();
      assert.equal(await page.locator('.original-viewer-counter').innerText(), '2 / 2');
      await page.keyboard.press('ArrowLeft'); assert.equal(await page.locator('.original-viewer-counter').innerText(), '1 / 2');
      await page.getByRole('button', { name: '画面に合わせる', exact: true }).click();
      await page.keyboard.press('Escape'); assert.equal(await page.evaluate(() => document.activeElement.id), 'originals-button');
      await page.unroute('**/artworks.json'); await page.unroute('**/qa-fixture-*.svg');
    });
    const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
    const phone = await mobile.newPage(); watch(phone);
    for (const id of ['009', '010']) {
      await check(id + ' mobile, touch movement and reduced motion', async () => {
        const frame = await openWork(phone, id);
        assert.equal(await phone.locator('#reduced-motion-note').isVisible(), true);
        assert.equal(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
        assert.equal((await state(frame, id)).mode, 'manual');
        const control = frame.locator('[data-key="w"]'); await control.scrollIntoViewIfNeeded();
        const box = await control.boundingBox(); assert(box);
        const before = await state(frame, id);
        const cdp = await mobile.newCDPSession(phone);
        await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: box.x + box.width / 2, y: box.y + box.height / 2 }] });
        await phone.waitForTimeout(350);
        await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
        const after = await state(frame, id);
        assert(Math.hypot(after.x - before.x, after.z - before.z) > .01);
        await cdp.detach();
        await phone.screenshot({ path: path.join(output, 'mobile-' + id + '.png'), fullPage: true });
      });
    }
    await mobile.close(); await context.close();
  } catch (error) { results.push({ name: 'browser execution', result: 'BLOCKED', detail: error.message }); }
  finally {
    if (browser) await browser.close();
    const report = { generated_at: new Date().toISOString(), base, executablePath, results, errors, note: 'Only PASS entries were actually verified. Fixture originals are test-only intercepted responses.' };
    fs.writeFileSync(path.join(output, 'browser-qa.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ passed: results.filter(x => x.result === 'PASS').length, failed: results.filter(x => x.result === 'FAIL').length, blocked: results.filter(x => x.result === 'BLOCKED').length, errors: errors.length }));
    if (results.some(x => x.result !== 'PASS') || errors.length) process.exitCode = 1;
  }
})();

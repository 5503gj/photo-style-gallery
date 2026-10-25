const assert = require('node:assert/strict');
const path = require('node:path');
const net = require('node:net');
const fs = require('node:fs/promises');
const os = require('node:os');
const {spawn} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const socket = net.createServer();
  await new Promise(resolve => socket.listen(0, '127.0.0.1', resolve));
  const port = socket.address().port;
  await new Promise(resolve => socket.close(resolve));
  const server = spawn(process.env.PYTHON || 'python', ['-u', 'app.py'], {
    cwd:path.resolve(__dirname, '..'), stdio:'ignore',
    env:{...process.env, PORT:String(port), PHOTO_HOST:'127.0.0.1', GRADIO_ANALYTICS_ENABLED:'False'},
  });
  let browser;
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'form-ui-'));
  try {
    let ready = false;
    for (let i=0; i<240; i++) {
      try { if ((await fetch(`http://127.0.0.1:${port}/config`)).ok) {ready=true;break;} } catch {}
      await new Promise(resolve => setTimeout(resolve, 250));
    }
    assert.ok(ready, 'Gradio must start');
    browser = await chromium.launch({headless:true, ...(process.env.CHROMIUM_PATH ? {executablePath:process.env.CHROMIUM_PATH}: {})});
    const page = await browser.newPage({viewport:{width:1580,height:1000}});
    const errors=[];page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${port}/`, {waitUntil:'domcontentloaded'});
    await page.locator('#sample-button').click();
    await page.waitForFunction(() => document.querySelectorAll('#compare-stage img').length===2);
    await page.locator('#director-button').click();
    await page.waitForFunction(() => document.querySelectorAll('.director-trace li').length===4);
    assert.equal(await page.locator('#trial-gallery .gallery-item').count(), 3);
    assert.ok(await page.locator('.palette-swatch').count()>0);
    await page.locator('#trial-gallery .gallery-item').nth(1).click();
    await page.waitForFunction(() => document.querySelector('#result-report').textContent.includes('铅笔素描'));
    const range=page.locator('#comparison-position input[type=range]');
    await range.focus();await range.press('End');
    await page.waitForFunction(() => {
      const image=document.querySelector('#compare-stage img.fixed');
      const percentages=image && getComputedStyle(image).clipPath.match(/([\d.]+)%/g);
      return percentages && parseFloat(percentages.at(-1))>75;
    });
    const [download] = await Promise.all([
      page.waitForEvent('download'), page.locator('#kit-download a[download]').click(),
    ]);
    assert.match(download.suggestedFilename(), /\.zip$/);
    await download.saveAs(path.join(directory, 'kit.zip'));
    assert.ok((await fs.stat(path.join(directory,'kit.zip'))).size>100);
    for (const width of [1580,768,390]) {
      await page.setViewportSize({width,height:900});
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth>innerWidth), false);
      const visible=await page.locator('#trial-gallery').evaluate(element => {
        const parent=element.getBoundingClientRect();
        return [...element.querySelectorAll('.caption-label')].every(node => {
          const box=node.getBoundingClientRect();return box.bottom<=parent.bottom+2 && box.right<=parent.right+2;
        });
      });
      assert.ok(visible, 'trial captions must remain inside gallery');
      assert.ok(await page.locator('#kit-download .filename').evaluate(node => node.getBoundingClientRect().width)>70);
    }
    await page.emulateMedia({reducedMotion:'reduce'});
    assert.equal(await page.locator('.director-trace li').first().evaluate(node => getComputedStyle(node).animationName),'none');
    await page.locator('#source-upload button[aria-label]').first().click();
    await page.waitForFunction(() => document.querySelectorAll('#trial-gallery .gallery-item').length===0);
    assert.equal(await page.locator('#kit-download a[download]').count(),0);
    assert.deepEqual(errors,[]);
    console.log('Browser passed: sample, real director, variant selection, keyboard comparison, ZIP download, clear, responsive and reduced motion.');
  } finally {
    if(browser) await browser.close();server.kill();await fs.rm(directory,{recursive:true,force:true});
  }
})().catch(error => {console.error(error);process.exitCode=1;});



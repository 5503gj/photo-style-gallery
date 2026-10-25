const {open,assert}=require('./online-harness.cjs'),fs=require('node:fs/promises'),path=require('node:path');
(async()=>{const {page,errors,requests,url,close}=await open();try{
 await page.goto(url);await page.locator('#sample').click();await page.waitForFunction(()=>document.querySelector('#report').textContent.includes('原图已就绪'),null,{timeout:120000});
 const source=await page.locator('#before').getAttribute('src');await page.locator('#direct').click();await page.waitForFunction(()=>document.querySelectorAll('#variants button').length===3,null,{timeout:60000});
 assert.equal(await page.locator('#before').getAttribute('src'),source);assert.notEqual(await page.locator('#after').getAttribute('src'),source);
 await page.locator('#variants button').nth(1).click();assert.match(await page.locator('#report').innerText(),/铅笔素描/);
 await page.locator('#position').focus();await page.locator('#position').press('End');assert.match(await page.locator('#after').getAttribute('style'),/100%/);
 await page.locator('#position').press('Home');assert.match(await page.locator('#after').getAttribute('style'),/0%/);
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#zip').click()]);
 const zipped=await fs.readFile(await download.path());assert.equal(zipped.subarray(0,2).toString(),'PK');assert.ok(zipped.length>1000);
 await page.locator('details').first().locator('summary').click();await page.locator('#style').selectOption('复古胶片');await page.locator('#apply').click();await page.waitForFunction(()=>document.querySelector('#report').textContent.includes('处理完成'));
 for(const width of [1440,768,390]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await page.locator('#tools li').first().evaluate(n=>getComputedStyle(n).animationName),'none');
 await page.locator('#clear').click();assert.equal(await page.locator('#zip').isVisible(),false);assert.equal(await page.locator('#before').getAttribute('src'),null);
 await page.locator('#upload').setInputFiles({name:'fake.png',mimeType:'image/png',buffer:Buffer.from('not an image')});await page.waitForFunction(()=>document.querySelector('#report').textContent.includes('图片无效'));assert.equal(await page.locator('#before').isVisible(),false);
 assert.equal(requests.filter(r=>r.method!=='GET').length,0);assert.ok(requests.every(r=>r.url.startsWith(url)||r.url.endsWith('favicon.ico')));assert.deepEqual(errors,[]);
 console.log('Online FORM passed: actual Python/OpenCV in worker, source/variants, keyboard comparison, ZIP, manual filter, clear, invalid image, subpath, mobile, no external dependencies or uploads.');
}finally{await close();}})().catch(error=>{console.error(error);process.exitCode=1;});

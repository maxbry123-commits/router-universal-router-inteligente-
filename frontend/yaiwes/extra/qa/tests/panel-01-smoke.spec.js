const { test, expect } = require('@playwright/test');
const path = require('path');
const { pathToFileURL } = require('url');
const target = pathToFileURL(path.resolve(__dirname,'../../Ui Yaiwes interface beta/04-panels/PANEL-01-CHAT/index.html')).href;
test('PANEL-01 boots and composer works', async ({page})=>{
 const errors=[]; page.on('console',m=>{if(m.type()==='error')errors.push(m.text())}); page.on('pageerror',e=>errors.push(e.message));
 await page.goto(target);
 await expect(page.locator('#composer')).toBeVisible();
 await expect(page.locator('#sendBtn')).toBeVisible();
 await page.locator('#composer').fill('QA YAIWES');
 await page.locator('#composer').press('Enter');
 await expect(page.locator('.message.user')).toContainText('QA YAIWES');
 expect(errors).toEqual([]);
});

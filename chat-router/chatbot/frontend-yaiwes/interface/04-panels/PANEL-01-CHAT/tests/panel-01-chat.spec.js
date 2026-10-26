const { test, expect } = require('@playwright/test');
const path = require('path');
const { pathToFileURL } = require('url');

const pageUrl = pathToFileURL(path.resolve(__dirname, '..', 'index.html')).href;

test.beforeEach(async ({ page }) => {
  await page.goto(pageUrl);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
});

test('AC01/03/04/07/08/11/12 core interactions', async ({ page }) => {
  await expect(page.locator('#composer')).toBeVisible();
  await page.locator('#newChat').click();
  await expect(page.locator('.chat-item.active')).toContainText('Nuevo chat');

  await page.locator('#modeTrigger').click();
  await page.locator('[data-mode="Fast"]').click();
  await expect(page.locator('#modeLabel')).toHaveText('Fast');

  await page.locator('#composer').fill('Prueba funcional');
  await page.locator('#sendBtn').click();
  await expect(page.locator('.message.user')).toContainText('Prueba funcional');
  await expect(page.locator('.message.system.blocked')).toContainText('bridge backend no está conectado');

  await page.locator('#moreTrigger').click();
  page.once('dialog', d => d.accept('Chat QA'));
  await page.locator('#renameBtn').click();
  await expect(page.locator('.chat-item.active')).toContainText('Chat QA');

  await page.reload();
  await expect(page.locator('#modeLabel')).toHaveText('Fast');
  await expect(page.locator('.chat-item.active')).toContainText('Chat QA');
});

test('AC05/06 tool sheet and toggle state', async ({ page }) => {
  await page.locator('#addTrigger').click();
  await expect(page.locator('#toolsDialog')).toBeVisible();
  const web = page.locator('[data-tool="web"]');
  await expect(web).toHaveAttribute('aria-pressed','false');
  await web.click();
  await expect(web).toHaveAttribute('aria-pressed','true');
});

test('AC14 keyboard send and mode navigation', async ({ page }) => {
  await page.locator('#composer').fill('Enter envía');
  await page.locator('#composer').press('Enter');
  await expect(page.locator('.message.user')).toContainText('Enter envía');
  await page.locator('#modeTrigger').click();
  await page.keyboard.press('ArrowDown');
  await expect(page.locator('#modelMenu button:focus')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('#modelMenu')).toBeHidden();
});

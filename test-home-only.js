const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:9001';
const SCREENSHOT_DIR = path.join(__dirname, 'test-screenshots');

async function run() {
  if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  try {
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(15000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'home-after-15s.png'), fullPage: true });
    const text = await page.evaluate(() => document.body.innerText);
    fs.writeFileSync(path.join(SCREENSHOT_DIR, 'home-text.txt'), text);
    console.log('Home page text snippet:', text.slice(0, 500));
  } finally {
    await browser.close();
  }
}

run().catch((e) => { console.error(e); process.exit(1); });

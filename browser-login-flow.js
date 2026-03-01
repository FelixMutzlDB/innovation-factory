/**
 * Navigate to recognition page, screenshot initial state,
 * wait 60s (check every 10s) for user to complete SSO login.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const OUTPUT_DIR = path.join(__dirname, 'browser-login-flow-output');

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log('Launching browser (headed - please complete SSO login when prompted)...');
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized'],
  });
  const context = await browser.newContext({
    viewport: null,
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  console.log('Navigating to', TARGET_URL, '...');
  await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(3000);

  // Initial screenshot
  const initialPath = path.join(OUTPUT_DIR, '01-initial.png');
  await page.screenshot({ path: initialPath, fullPage: true });
  console.log('Screenshot 1 (initial):', initialPath);

  const bodyText = () => page.evaluate(() => document.body.innerText);
  const isAppPage = (text) =>
    text.includes('Visual Product Recognition Hub') ||
    text.includes('Recent Recognition Jobs') ||
    (text.includes('innovation-factory') && text.includes('Overview'));

  // Wait up to 60 seconds, check every 10 seconds
  for (let i = 1; i <= 6; i++) {
    console.log(`Waiting ${i * 10}s / 60s...`);
    await page.waitForTimeout(10000);

    const text = await bodyText();
    const checkPath = path.join(OUTPUT_DIR, `02-check-${i * 10}s.png`);
    await page.screenshot({ path: checkPath, fullPage: true });
    console.log(`Screenshot ${i + 1} (${i * 10}s):`, checkPath);

    if (isAppPage(text)) {
      const finalPath = path.join(OUTPUT_DIR, '03-app-page-detected.png');
      await page.screenshot({ path: finalPath, fullPage: true });
      console.log('App page detected! Final screenshot:', finalPath);
      console.log('\nUser has logged in. App page visible.');
      await page.waitForTimeout(5000); // Keep page open a bit longer
      await browser.close();
      return { state: 'app-page', finalScreenshot: finalPath };
    }
  }

  console.log('60 seconds elapsed. Page may still be on login. Final screenshot taken.');
  const finalPath = path.join(OUTPUT_DIR, '03-after-60s.png');
  await page.screenshot({ path: finalPath, fullPage: true });
  console.log('Final screenshot:', finalPath);
  await browser.close();
  return { state: 'login-or-unknown', finalScreenshot: finalPath };
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});

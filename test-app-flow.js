/**
 * Manual test script for app flow at http://localhost:9001
 * Captures screenshots and console logs for each page
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:9001';
const SCREENSHOT_DIR = path.join(__dirname, 'test-screenshots');

async function run() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  const consoleLogs = [];
  const consoleErrors = [];
  page.on('console', (msg) => {
    const text = msg.text();
    const type = msg.type();
    if (type === 'error') {
      consoleErrors.push(text);
    }
    consoleLogs.push(`[${type}] ${text}`);
  });

  const results = [];

  try {
    // Step 1: Home page
    console.log('Step 1: Navigating to home page...');
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-home.png'), fullPage: true });
    const homeContent = await page.content();
    const homeHasProjectCards = homeContent.includes('project') || homeContent.includes('card') || homeContent.includes('hb-product');
    results.push({
      page: 'Home',
      url: BASE_URL,
      screenshot: '01-home.png',
      hasProjectCards: homeHasProjectCards,
      consoleErrors: [...consoleErrors],
    });
    console.log('  Screenshot: 01-home.png');

    // Step 2: HB Product Center - wait 30 seconds
    console.log('Step 2: Navigating to hb-product-center (waiting 30s)...');
    consoleErrors.length = 0;
    await page.goto(`${BASE_URL}/projects/hb-product-center`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(30000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02-hb-product-center.png'), fullPage: true });
    const kpiContent = await page.content();
    const hasSkeletons = kpiContent.includes('animate-pulse') || kpiContent.includes('skeleton');
    const hasNumbers = /\d{1,}[.,]?\d*/.test(kpiContent);
    results.push({
      page: 'HB Product Center',
      url: `${BASE_URL}/projects/hb-product-center`,
      screenshot: '02-hb-product-center.png',
      hasSkeletons,
      hasActualNumbers: hasNumbers,
      consoleErrors: [...consoleErrors],
    });
    console.log('  Screenshot: 02-hb-product-center.png');

    // Step 3: Recognition - wait 15 seconds
    console.log('Step 3: Navigating to recognition (waiting 15s)...');
    consoleErrors.length = 0;
    await page.goto(`${BASE_URL}/projects/hb-product-center/recognition`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(15000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03-recognition.png'), fullPage: true });
    const recContent = await page.content();
    const recHasSkeletons = recContent.includes('animate-pulse') || recContent.includes('skeleton');
    results.push({
      page: 'Recognition',
      url: `${BASE_URL}/projects/hb-product-center/recognition`,
      screenshot: '03-recognition.png',
      hasSkeletons: recHasSkeletons,
      consoleErrors: [...consoleErrors],
    });
    console.log('  Screenshot: 03-recognition.png');

    // Step 4: Quality - wait 15 seconds
    console.log('Step 4: Navigating to quality (waiting 15s)...');
    consoleErrors.length = 0;
    await page.goto(`${BASE_URL}/projects/hb-product-center/quality`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(15000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04-quality.png'), fullPage: true });
    const qualContent = await page.content();
    const qualHasSkeletons = qualContent.includes('animate-pulse') || qualContent.includes('skeleton');
    results.push({
      page: 'Quality',
      url: `${BASE_URL}/projects/hb-product-center/quality`,
      screenshot: '04-quality.png',
      hasSkeletons: qualHasSkeletons,
      consoleErrors: [...consoleErrors],
    });
    console.log('  Screenshot: 04-quality.png');

  } catch (err) {
    console.error('Test failed:', err.message);
    throw err;
  } finally {
    await browser.close();
  }

  // Write results
  fs.writeFileSync(
    path.join(SCREENSHOT_DIR, 'results.json'),
    JSON.stringify(results, null, 2)
  );
  fs.writeFileSync(
    path.join(SCREENSHOT_DIR, 'console.log'),
    consoleLogs.join('\n')
  );

  console.log('\n=== RESULTS ===');
  console.log(JSON.stringify(results, null, 2));
  console.log('\nScreenshots saved to:', SCREENSHOT_DIR);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});

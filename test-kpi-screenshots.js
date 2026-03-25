/**
 * Test KPI cards and project cards - check for real data vs skeletons
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

  const report = { hbProductCenter: {}, home: {} };

  try {
    // 1. HB Product Center - wait 30 seconds
    console.log('Navigating to hb-product-center...');
    await page.goto(`${BASE_URL}/projects/hb-product-center`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log('Waiting 30 seconds for full load...');
    await page.waitForTimeout(30000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'hb-product-center-after-30s.png'), fullPage: true });
    const kpiContent = await page.content();
    const kpiText = await page.evaluate(() => document.body.innerText);

    // Check for skeleton indicators
    const hasSkeletonClass = kpiContent.includes('animate-pulse') || kpiContent.includes('Skeleton');
    const hasSkeletonAria = kpiContent.includes('aria-busy="true"');

    // Check for expected KPI numbers
    const has50 = /\b50\b/.test(kpiText);
    const has40 = /\b40\b/.test(kpiText);
    const has80 = /80\.?\d*/.test(kpiText) || /\b80\b/.test(kpiText);
    const hasNumbers = /\d{2,}/.test(kpiText);

    report.hbProductCenter = {
      screenshot: 'hb-product-center-after-30s.png',
      hasSkeletonClass,
      hasSkeletonAria,
      has50,
      has40,
      has80,
      hasNumbers,
      kpiSnippet: kpiText.slice(0, 800),
    };
    console.log('HB Product Center:', JSON.stringify(report.hbProductCenter, null, 2));

    // 2. Home page - wait 15 seconds
    console.log('\nNavigating to home...');
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log('Waiting 15 seconds...');
    await page.waitForTimeout(15000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'home-after-15s.png'), fullPage: true });
    const homeContent = await page.content();
    const homeText = await page.evaluate(() => document.body.innerText);

    const homeHasSkeleton = homeContent.includes('animate-pulse') || homeContent.includes('Skeleton');
    const hasProjectNames = /hb-product|HB Product|mol.asm|MOL ASM/i.test(homeText);
    const hasRealCards = homeText.includes('Project') || homeText.includes('project');

    report.home = {
      screenshot: 'home-after-15s.png',
      hasSkeleton: homeHasSkeleton,
      hasProjectNames,
      hasRealCards,
      homeSnippet: homeText.slice(0, 800),
    };
    console.log('Home:', JSON.stringify(report.home, null, 2));

  } catch (err) {
    console.error('Test failed:', err.message);
    report.error = err.message;
  } finally {
    await browser.close();
  }

  fs.writeFileSync(path.join(SCREENSHOT_DIR, 'kpi-report.json'), JSON.stringify(report, null, 2));
  console.log('\n=== REPORT ===');
  console.log(JSON.stringify(report, null, 2));
  console.log('\nScreenshots:', SCREENSHOT_DIR);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});

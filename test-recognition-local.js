/**
 * Test recognition page locally (no auth required)
 * 1. Recognition jobs table loading
 * 2. Image upload area
 * 3. Console errors and failed network requests
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'http://localhost:9001/projects/hb-product-center/recognition';
const JOBS_API_PATTERN = /recognition\/jobs|hb-product-center.*jobs/;
const OUTPUT_DIR = path.join(__dirname, 'test-recognition-output');

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log('Launching browser (headless)...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  const consoleErrors = [];
  const failedRequests = [];
  const apiCalls = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('requestfailed', (req) => {
    failedRequests.push({ url: req.url(), error: req.failure()?.errorText });
  });
  page.on('response', (res) => {
    const url = res.url();
    if (JOBS_API_PATTERN.test(url) || url.includes('recognition')) {
      apiCalls.push({ url, status: res.status() });
    }
  });

  const report = { timestamp: new Date().toISOString(), url: TARGET_URL, screenshots: [], jobsTableLoaded: null, jobsTableError: null, uploadAreaRenders: null, dropZoneText: null, consoleErrors: [], failedRequests: [], apiCalls: [] };

  try {
    console.log('Navigating to', TARGET_URL, '...');
    await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);

    const bodyText = await page.evaluate(() => document.body.innerText);

    // Check jobs table
    const hasJobsError = bodyText.includes('Failed to load recognition jobs');
    report.jobsTableLoaded = !hasJobsError && (bodyText.includes('Recent Recognition Jobs') || bodyText.includes('Job ID') || bodyText.includes('Status'));
    report.jobsTableError = hasJobsError ? 'Failed to load recognition jobs' : null;

    // Check upload area
    const dropZoneText = 'Drop product image here or click to browse';
    report.uploadAreaRenders = bodyText.includes(dropZoneText);
    report.dropZoneText = dropZoneText;

    await page.screenshot({ path: path.join(OUTPUT_DIR, 'local-recognition-page.png'), fullPage: true });
    report.screenshots.push('local-recognition-page.png');

    const dropZone = page.locator('text=Drop product image here or click to browse');
    if (await dropZone.isVisible().catch(() => false)) {
      await dropZone.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: path.join(OUTPUT_DIR, 'local-after-dropzone-click.png'), fullPage: true });
      report.screenshots.push('local-after-dropzone-click.png');
    }

    report.consoleErrors = [...consoleErrors];
    report.failedRequests = [...failedRequests];
    report.apiCalls = apiCalls;
    fs.writeFileSync(path.join(OUTPUT_DIR, 'local-report.json'), JSON.stringify(report, null, 2));
    return report;
  } finally {
    await browser.close();
  }
}

run()
  .then((r) => {
    console.log('\n=== LOCAL TEST REPORT ===');
    console.log('Jobs table loaded:', r.jobsTableLoaded);
    console.log('Jobs table error:', r.jobsTableError || 'none');
    console.log('Upload area renders:', r.uploadAreaRenders);
    console.log('Console errors:', r.consoleErrors.length, r.consoleErrors);
    console.log('Failed requests:', r.failedRequests.length, r.failedRequests);
    console.log('API calls (recognition):', r.apiCalls);
    console.log('Screenshots:', r.screenshots);
  })
  .catch((e) => { console.error(e); process.exit(1); });

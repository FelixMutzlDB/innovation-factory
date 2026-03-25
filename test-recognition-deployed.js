/**
 * Test deployed Databricks app - recognition page
 * 1. Recognition jobs table loading
 * 2. Image upload area (drop zone)
 * 3. Console errors and failed network requests
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const JOBS_API_PATTERN = /recognition\/jobs/;
const OUTPUT_DIR = path.join(__dirname, 'test-recognition-output');
const HEADED = process.env.HEADED === '1';

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log('Launching browser...', HEADED ? '(headed - you can log in)' : '(headless)');
  const browser = await chromium.launch({
    headless: !HEADED,
    args: HEADED ? ['--start-maximized'] : [],
  });
  const context = await browser.newContext({
    viewport: HEADED ? null : { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  const consoleErrors = [];
  const failedRequests = [];
  const apiRequests = { jobs: [], failed: [] };

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  page.on('requestfailed', (req) => {
    const info = { url: req.url(), error: req.failure()?.errorText };
    failedRequests.push(info);
    if (JOBS_API_PATTERN.test(req.url())) {
      apiRequests.failed.push(info);
    }
  });

  page.on('request', (req) => {
    if (JOBS_API_PATTERN.test(req.url())) {
      apiRequests.jobs.push({ url: req.url(), method: req.method() });
    }
  });

  const report = {
    timestamp: new Date().toISOString(),
    url: TARGET_URL,
    screenshots: [],
    jobsTableLoaded: null,
    jobsTableError: null,
    uploadAreaRenders: null,
    dropZoneText: null,
    dropZoneClickScreenshot: null,
    consoleErrors: [],
    failedRequests: [],
    jobsApiRequests: [],
    jobsApiFailed: [],
  };

  try {
    console.log('Navigating to', TARGET_URL, '...');
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(3000);

    // Check if we're on login page
    const loginVisible = await page.locator('text=Continue with SSO').isVisible().catch(() => false);
    if (loginVisible) {
      console.log('Login page detected. Clicking "Continue with SSO"...');
      await page.screenshot({ path: path.join(OUTPUT_DIR, '01-login-page.png'), fullPage: true });
      report.screenshots.push('01-login-page.png');

      await page.click('text=Continue with SSO');
      console.log('Waiting 90 seconds for SSO authentication (complete login in browser if headed)...');
      await page.waitForTimeout(90000);
    }

    // Wait for page to settle
    await page.waitForTimeout(5000);

    const bodyText = await page.evaluate(() => document.body.innerText);

    // Determine if we're on recognition page or still on login
    const isRecognitionPage = bodyText.includes('Visual Product Recognition Hub') || bodyText.includes('Recent Recognition Jobs');
    const isLoginPage = bodyText.includes('Log in') && bodyText.includes('Continue with SSO');

    if (isLoginPage && !isRecognitionPage) {
      await page.screenshot({ path: path.join(OUTPUT_DIR, '02-still-login.png'), fullPage: true });
      report.screenshots.push('02-still-login.png');
      report.jobsTableLoaded = false;
      report.jobsTableError = 'Still on login page - authentication required';
      report.uploadAreaRenders = false;
    } else if (isRecognitionPage) {
      // Screenshot of full page
      await page.screenshot({ path: path.join(OUTPUT_DIR, '02-recognition-page.png'), fullPage: true });
      report.screenshots.push('02-recognition-page.png');

      // Check jobs table
      const hasJobsError = bodyText.includes('Failed to load recognition jobs');
      const hasJobsTable = bodyText.includes('Recent Recognition Jobs') || bodyText.includes('recognition');
      report.jobsTableLoaded = hasJobsTable && !hasJobsError;
      report.jobsTableError = hasJobsError ? 'Failed to load recognition jobs' : null;

      // Check upload area
      const dropZoneText = 'Drop product image here or click to browse';
      const hasDropZone = bodyText.includes(dropZoneText);
      report.uploadAreaRenders = hasDropZone;
      report.dropZoneText = hasDropZone ? dropZoneText : `Expected "${dropZoneText}" but page contains: ${bodyText.slice(0, 500)}`;

      // Click drop zone
      const dropZone = page.locator('text=Drop product image here or click to browse');
      if (await dropZone.isVisible().catch(() => false)) {
        await dropZone.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: path.join(OUTPUT_DIR, '03-after-dropzone-click.png'), fullPage: true });
        report.dropZoneClickScreenshot = '03-after-dropzone-click.png';
        report.screenshots.push('03-after-dropzone-click.png');
      }
    } else {
      await page.screenshot({ path: path.join(OUTPUT_DIR, '02-unknown-state.png'), fullPage: true });
      report.screenshots.push('02-unknown-state.png');
      report.jobsTableLoaded = false;
      report.uploadAreaRenders = false;
    }

    report.consoleErrors = [...consoleErrors];
    report.failedRequests = [...failedRequests];
    report.jobsApiRequests = apiRequests.jobs;
    report.jobsApiFailed = apiRequests.failed;

    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    return report;
  } finally {
    await browser.close();
  }
}

run()
  .then((r) => {
    console.log('\n=== REPORT ===');
    console.log('Jobs table loaded:', r.jobsTableLoaded);
    console.log('Jobs table error:', r.jobsTableError || 'none');
    console.log('Upload area renders:', r.uploadAreaRenders);
    console.log('Console errors:', r.consoleErrors.length, r.consoleErrors.length ? r.consoleErrors : '');
    console.log('Failed requests:', r.failedRequests.length);
    console.log('Jobs API requests:', r.jobsApiRequests.length);
    console.log('Jobs API failed:', r.jobsApiFailed.length, r.jobsApiFailed);
    console.log('Screenshots:', r.screenshots);
    console.log('Full report: test-recognition-output/report.json');
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

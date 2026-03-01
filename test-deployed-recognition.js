/**
 * Test deployed Databricks app - recognition page
 * Run with: HEADED=1 node test-deployed-recognition.js
 * If login required: log in during the 2-minute wait when browser opens
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const OUTPUT_DIR = path.join(__dirname, 'test-recognition-output');
const HEADED = process.env.HEADED === '1';

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log('Launching browser...', HEADED ? '(headed - log in if prompted)' : '(headless)');
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
  const allRequests = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('requestfailed', (req) => {
    failedRequests.push({ url: req.url(), error: req.failure()?.errorText });
  });
  page.on('response', (res) => {
    const url = res.url();
    const status = res.status();
    if (url.includes('recognition') || url.includes('/api/')) {
      allRequests.push({ url, status });
    }
  });

  const report = {
    timestamp: new Date().toISOString(),
    url: TARGET_URL,
    screenshots: [],
    jobsTableLoaded: null,
    jobsTableShowsError: null,
    uploadAreaComplete: null,
    uploadAreaChecks: {},
    consoleErrors: [],
    failedRequests: [],
    apiRequests: [],
  };

  try {
    console.log('Navigating to', TARGET_URL, '...');
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(3000);

    // Check for login page
    let isLoginPage = await page.locator('text=Continue with SSO').isVisible().catch(() => false);
    if (isLoginPage) {
      console.log('Login page - clicking "Continue with SSO"...');
      await page.click('text=Continue with SSO');
      await page.waitForTimeout(3000);
    }

    // Incremental waits - up to 2 min for user to complete SSO if headed
    let attempts = 0;
    const maxAttempts = 24; // 24 * 5s = 2 min
    while (attempts < maxAttempts) {
      await page.waitForTimeout(5000);
      attempts++;
      const bodyText = await page.evaluate(() => document.body.innerText);
      const onRecognitionPage = bodyText.includes('Visual Product Recognition Hub') || bodyText.includes('Recent Recognition Jobs');
      const onOktaPage = bodyText.includes('Sign In') && bodyText.includes('Email address') && !bodyText.includes('Visual Product Recognition');
      const stillOnDatabricksLogin = bodyText.includes('Continue with SSO');

      if (onRecognitionPage) {
        console.log('Reached recognition page after', attempts * 5, 'seconds');
        break;
      }
      if (onOktaPage) {
        console.log('On Okta page - waiting (user may have session)...');
      } else if (stillOnDatabricksLogin) {
        console.log('Still on Databricks login...');
      }
      if (attempts >= maxAttempts) {
        console.log('Timeout - did not reach recognition page');
      }
    }

    await page.waitForTimeout(3000);
    const bodyText = await page.evaluate(() => document.body.innerText);
    const isRecognitionPage = bodyText.includes('Visual Product Recognition Hub') || bodyText.includes('Recent Recognition Jobs');

    if (isRecognitionPage) {
      // Screenshot 1: Full page
      const shot1 = path.join(OUTPUT_DIR, 'deployed-recognition-full.png');
      await page.screenshot({ path: shot1, fullPage: true });
      report.screenshots.push('deployed-recognition-full.png');

      // Check jobs table
      report.jobsTableShowsError = bodyText.includes('Failed to load recognition jobs');
      const hasTableHeaders = bodyText.includes('Job ID') || bodyText.includes('Status') || bodyText.includes('Type');
      const hasDataRows = /\d+/.test(bodyText) && (bodyText.includes('single') || bodyText.includes('batch') || bodyText.includes('completed') || bodyText.includes('pending'));
      report.jobsTableLoaded = !report.jobsTableShowsError && (hasTableHeaders || hasDataRows);

      // Check upload area
      report.uploadAreaChecks = {
        dropZoneText: bodyText.includes('Drop product image here or click to browse'),
        supportsText: bodyText.includes('Supports JPG, PNG, WebP up to 10MB'),
        singleBatchToggle: bodyText.includes('Single') && bodyText.includes('Batch'),
        submitButton: bodyText.includes('Submit Recognition Job'),
      };
      report.uploadAreaComplete = Object.values(report.uploadAreaChecks).every(Boolean);

      // Screenshot 2: Upload area (scroll to it if needed)
      const uploadCard = page.locator('text=Upload Image').first();
      if (await uploadCard.isVisible().catch(() => false)) {
        await uploadCard.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
      }
      const shot2 = path.join(OUTPUT_DIR, 'deployed-upload-area.png');
      await page.screenshot({ path: shot2 });
      report.screenshots.push('deployed-upload-area.png');
    } else {
      const shotUnknown = path.join(OUTPUT_DIR, 'deployed-unknown-state.png');
      await page.screenshot({ path: shotUnknown, fullPage: true });
      report.screenshots.push('deployed-unknown-state.png');
      report.jobsTableLoaded = false;
      report.uploadAreaComplete = false;
    }

    report.consoleErrors = [...consoleErrors];
    report.failedRequests = [...failedRequests];
    report.apiRequests = allRequests.filter((r) => r.url.includes('recognition') || r.url.includes('/api/'));

    fs.writeFileSync(path.join(OUTPUT_DIR, 'deployed-report.json'), JSON.stringify(report, null, 2));
    return report;
  } finally {
    await browser.close();
  }
}

run()
  .then((r) => {
    console.log('\n=== DEPLOYED APP TEST REPORT ===');
    console.log('Jobs table loaded:', r.jobsTableLoaded);
    console.log('Jobs table shows error:', r.jobsTableShowsError);
    console.log('Upload area complete:', r.uploadAreaComplete);
    console.log('Upload area checks:', JSON.stringify(r.uploadAreaChecks, null, 2));
    console.log('Console errors:', r.consoleErrors.length);
    console.log('Failed requests:', r.failedRequests.length);
    console.log('API requests (recognition/api):', r.apiRequests.length);
    console.log('Screenshots:', r.screenshots);
    console.log('Full report: test-recognition-output/deployed-report.json');
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

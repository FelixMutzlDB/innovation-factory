/**
 * Full E2E test of visual recognition on deployed Databricks app:
 * 1. Navigate to recognition page
 * 2. Handle auth if needed (use saved session or wait for user)
 * 3. Screenshot initial UI
 * 4. Upload test image, click Find Similar
 * 5. Screenshot results
 *
 * Run: HEADED=1 node test-deployed-visual-recognition-full.js  (if login needed)
 * Run: node test-deployed-visual-recognition-full.js           (with saved session)
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL =
  'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const TEST_IMAGE =
  '/Users/sascha.saumer/.cursor/projects/Users-sascha-saumer-GIT-innovation-factory/assets/test_black_tshirt-52a79a5a-a944-4474-a159-9ce0c4e657c8.png';
const OUTPUT_DIR = path.join(__dirname, 'deployed-visual-recognition-test');
const USER_DATA_DIR = path.join(__dirname, '.playwright-auth-state');
const HEADED = process.env.HEADED === '1';

function isLoginPage(text) {
  return (
    (text.includes('Log in') && text.includes('Continue with SSO')) ||
    (text.includes('Sign In') && (text.includes('Username') || text.includes('Email'))) ||
    text.includes('Verify with Security Key') ||
    text.includes('Databricks')
  );
}

function isRecognitionPage(text) {
  return (
    text.includes('Visual Product Recognition') &&
    (text.includes('Find Similar') || text.includes('Upload Image'))
  );
}

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const launchOpts = {
    headless: !HEADED,
    args: HEADED ? ['--start-maximized'] : [],
  };

  console.log('Using persistent auth context:', USER_DATA_DIR);
  console.log('Mode:', HEADED ? 'HEADED (visible - log in if prompted)' : 'HEADLESS');

  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    ...launchOpts,
    viewport: HEADED ? null : { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });

  const page = context.pages()[0] || (await context.newPage());

  const report = {
    timestamp: new Date().toISOString(),
    url: TARGET_URL,
    screenshots: [],
    auth: { needed: null, completed: null },
    uiCheck: { hasUploadCard: null, hasFindSimilar: null, noJobsTable: null },
    upload: { success: null, error: null },
    search: { success: null, resultsCount: null, error: null },
  };

  const consoleErrors = [];
  const failedRequests = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('requestfailed', (req) => {
    failedRequests.push({ url: req.url(), error: req.failure()?.errorText });
  });

  try {
    // 1. Navigate
    console.log('Navigating to', TARGET_URL, '...');
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(4000);

    let bodyText = await page.evaluate(() => document.body.innerText);

    // 2. Handle login
    if (isLoginPage(bodyText) && !isRecognitionPage(bodyText)) {
      report.auth.needed = true;
      console.log('Login page detected.');
      const ssoBtn = page.locator('text=Continue with SSO');
      if (await ssoBtn.isVisible().catch(() => false)) {
        console.log('Clicking "Continue with SSO"...');
        await ssoBtn.click();
        await page.waitForTimeout(3000);
      }

      // Wait up to 2 min for user to complete SSO (if headed)
      let attempts = 0;
      while (attempts < 24) {
        await page.waitForTimeout(5000);
        attempts++;
        bodyText = await page.evaluate(() => document.body.innerText);
        if (isRecognitionPage(bodyText)) {
          report.auth.completed = true;
          console.log('Reached recognition page after', attempts * 5, 's');
          break;
        }
        if (attempts >= 24) {
          const shot = path.join(OUTPUT_DIR, '01-login-timeout.png');
          await page.screenshot({ path: shot, fullPage: true });
          report.screenshots.push('01-login-timeout.png');
          console.log('Timeout waiting for login.');
          report.auth.completed = false;
          fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
          await context.close();
          return report;
        }
      }
    } else {
      report.auth.needed = false;
      report.auth.completed = true;
    }

    if (!isRecognitionPage(bodyText)) {
      const shot = path.join(OUTPUT_DIR, '01-unknown-page.png');
      await page.screenshot({ path: shot, fullPage: true });
      report.screenshots.push('01-unknown-page.png');
      report.uiCheck.hasUploadCard = false;
      report.uiCheck.hasFindSimilar = false;
      report.uiCheck.noJobsTable = null;
      fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
      await context.close();
      return report;
    }

    // 3. Screenshot initial UI
    const shot1 = path.join(OUTPUT_DIR, '01-initial-ui.png');
    await page.screenshot({ path: shot1, fullPage: true });
    report.screenshots.push('01-initial-ui.png');
    report.uiCheck.hasUploadCard = bodyText.includes('Upload Image') && bodyText.includes('Drag and drop');
    report.uiCheck.hasFindSimilar = bodyText.includes('Find Similar');
    report.uiCheck.noJobsTable = !bodyText.includes('Recent Recognition Jobs');
    console.log('UI check:', report.uiCheck);
    console.log('Screenshot 1 (initial UI):', shot1);

    // 4. Upload test image
    const fileInput = page.locator('input[type="file"]');
    if (!(await fileInput.count())) {
      report.upload.success = false;
      report.upload.error = 'No file input found';
      console.log('ERROR: No file input found');
    } else {
      try {
        await fileInput.setInputFiles(TEST_IMAGE);
        report.upload.success = true;
        console.log('Uploaded test image:', path.basename(TEST_IMAGE));
        await page.waitForTimeout(1500); // Let preview render
      } catch (e) {
        report.upload.success = false;
        report.upload.error = String(e.message);
        console.log('Upload error:', e.message);
      }
    }

    if (report.upload.success) {
      // 5. Click Find Similar
      const findBtn = page.locator('button:has-text("Find Similar")');
      if (await findBtn.isVisible().catch(() => false)) {
        await findBtn.click();
        console.log('Clicked "Find Similar"');
        await page.waitForTimeout(2000);

        // Wait for results (up to 30s)
        for (let i = 0; i < 15; i++) {
          bodyText = await page.evaluate(() => document.body.innerText);
          const hasResults = bodyText.includes('Similar Images') || bodyText.includes('result');
          const hasError = bodyText.includes('Search failed') || bodyText.includes('Please try again');
          if (hasResults || hasError) {
            report.search.success = !hasError;
            report.search.resultsCount = hasResults
              ? (bodyText.match(/(\d+)\s*result/g) || [])[0]?.match(/\d+/)?.[0] || '?'
              : null;
            break;
          }
          await page.waitForTimeout(2000);
        }

        // 6. Screenshot results
        const shot2 = path.join(OUTPUT_DIR, '02-results.png');
        await page.screenshot({ path: shot2, fullPage: true });
        report.screenshots.push('02-results.png');
        console.log('Screenshot 2 (results):', shot2);

        bodyText = await page.evaluate(() => document.body.innerText);
        if (bodyText.includes('No similar images found')) {
          report.search.resultsCount = 0;
        }
      } else {
        report.search.success = false;
        report.search.error = 'Find Similar button not found';
      }
    }

    report.consoleErrors = consoleErrors;
    report.failedRequests = failedRequests;
  } finally {
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    await context.close();
  }
  return report;
}

run()
  .then((r) => {
    console.log('\n=== DEPLOYED VISUAL RECOGNITION TEST REPORT ===');
    console.log('Auth needed:', r.auth.needed);
    console.log('Auth completed:', r.auth.completed);
    console.log('UI - Upload card:', r.uiCheck.hasUploadCard);
    console.log('UI - Find Similar:', r.uiCheck.hasFindSimilar);
    console.log('UI - No jobs table:', r.uiCheck.noJobsTable);
    console.log('Upload success:', r.upload.success);
    console.log('Search success:', r.search.success);
    console.log('Results count:', r.search.resultsCount);
    console.log('Errors:', r.upload.error || r.search.error || 'none');
    console.log('Screenshots:', r.screenshots);
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

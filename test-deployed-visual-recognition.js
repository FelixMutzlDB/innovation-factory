/**
 * Full end-to-end test of Visual Recognition on deployed Databricks app.
 * 1. Navigate to deployed URL
 * 2. Handle login (uses persistent auth if available, else needs HEADED=1 for manual login)
 * 3. Screenshot initial UI
 * 4. Upload test image
 * 5. Click Find Similar, wait for results
 * 6. Screenshot results
 *
 * Run: node test-deployed-visual-recognition.js
 * If login required: HEADED=1 node test-deployed-visual-recognition.js (browser opens, log in when prompted)
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL =
  'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const TEST_IMAGE =
  '/Users/sascha.saumer/.cursor/projects/Users-sascha-saumer-GIT-innovation-factory/assets/test_black_tshirt-52a79a5a-a944-4474-a159-9ce0c4e657c8.png';
const OUTPUT_DIR = path.join(__dirname, 'deployed-visual-recognition-output');
const USER_DATA_DIR = path.join(__dirname, '.playwright-auth-state');
const HEADED = process.env.HEADED === '1';

function isAppPage(text) {
  return (
    text.includes('Visual Product Recognition') &&
    text.includes('Upload Image') &&
    (text.includes('Find Similar') || text.includes('Drop product image'))
  );
}

function isLoginPage(text) {
  return (
    (text.includes('Log in') && text.includes('Continue with SSO')) ||
    text.includes('Sign in to Databricks') ||
    (text.includes('Sign In') && text.includes('Email') && !text.includes('Visual Product Recognition'))
  );
}

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const report = {
    timestamp: new Date().toISOString(),
    url: TARGET_URL,
    testImage: TEST_IMAGE,
    screenshots: [],
    authenticated: false,
    uiVerified: false,
    uploadSucceeded: false,
    searchSucceeded: false,
    resultsCount: null,
    errors: [],
    consoleErrors: [],
    apiCalls: [],
  };

  console.log('Launching browser...', HEADED ? '(headed - log in if prompted)' : '(headless, persistent context)');
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: !HEADED,
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });

  const page = context.pages()[0] || (await context.newPage());

  page.on('console', (msg) => {
    if (msg.type() === 'error') report.consoleErrors.push(msg.text());
  });
  page.on('response', (res) => {
    const url = res.url();
    if (url.includes('similar') || url.includes('find') || url.includes('/api/hb-product-center')) {
      report.apiCalls.push({ url: url.slice(0, 120), status: res.status() });
    }
  });

  try {
    console.log('Navigating to', TARGET_URL, '...');
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(4000);

    let bodyText = await page.evaluate(() => document.body.innerText);

    if (isLoginPage(bodyText)) {
      report.authenticated = false;
      const loginShot = path.join(OUTPUT_DIR, '00-login-page.png');
      await page.screenshot({ path: loginShot, fullPage: true });
      report.screenshots.push('00-login-page.png');
      console.log('Login page detected. Screenshot saved.');
      if (!HEADED) {
        report.errors.push('Login required. Run with HEADED=1 to log in manually: HEADED=1 node test-deployed-visual-recognition.js');
        fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
        await context.close();
        return report;
      }
      console.log('Waiting up to 2 minutes for you to complete SSO login...');
      for (let i = 0; i < 24; i++) {
        await page.waitForTimeout(5000);
        bodyText = await page.evaluate(() => document.body.innerText);
        if (isAppPage(bodyText)) {
          report.authenticated = true;
          console.log('Logged in successfully after', (i + 1) * 5, 'seconds');
          break;
        }
      }
      if (!report.authenticated) {
        report.errors.push('Timeout waiting for login. Page may still be on SSO.');
        const afterWait = path.join(OUTPUT_DIR, '00-after-login-wait.png');
        await page.screenshot({ path: afterWait, fullPage: true });
        report.screenshots.push('00-after-login-wait.png');
      }
    } else {
      report.authenticated = true;
    }

    if (!report.authenticated) {
      fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
      await context.close();
      return report;
    }

    bodyText = await page.evaluate(() => document.body.innerText);
    report.uiVerified =
      bodyText.includes('Visual Product Recognition') &&
      bodyText.includes('Upload Image') &&
      bodyText.includes('Find Similar') &&
      !bodyText.includes('Recent Recognition Jobs') &&
      !bodyText.includes('Submit Recognition Job');

    // Screenshot 1: Initial UI
    const shot1 = path.join(OUTPUT_DIR, '01-initial-ui.png');
    await page.screenshot({ path: shot1, fullPage: true });
    report.screenshots.push('01-initial-ui.png');
    console.log('Screenshot 1 (initial UI):', shot1);

    // Upload test image
    if (!fs.existsSync(TEST_IMAGE)) {
      report.errors.push('Test image not found: ' + TEST_IMAGE);
    } else {
      const fileInput = page.locator('input[type="file"][accept*="image"]');
      await fileInput.setInputFiles(TEST_IMAGE).catch((e) => {
        report.errors.push('File upload failed: ' + e.message);
      });
      await page.waitForTimeout(1500);
      report.uploadSucceeded = (await page.evaluate(() => document.body.innerText)).includes('Remove');
    }

    if (report.uploadSucceeded) {
      const shot2 = path.join(OUTPUT_DIR, '02-after-upload.png');
      await page.screenshot({ path: shot2, fullPage: true });
      report.screenshots.push('02-after-upload.png');
      console.log('Screenshot 2 (after upload):', shot2);

      // Click Find Similar
      const findBtn = page.getByRole('button', { name: /Find Similar/i });
      await findBtn.click().catch((e) => report.errors.push('Find Similar click failed: ' + e.message));
      await page.waitForTimeout(2000);

      // Wait for results (Similar Images card or "No similar images found")
      for (let i = 0; i < 10; i++) {
        await page.waitForTimeout(2000);
        bodyText = await page.evaluate(() => document.body.innerText);
        if (bodyText.includes('Similar Images') || bodyText.includes('No similar images found')) {
          report.searchSucceeded = true;
          const match = bodyText.match(/(\d+)\s*result/);
          report.resultsCount = match ? parseInt(match[1], 10) : (bodyText.includes('No similar') ? 0 : null);
          break;
        }
        if (bodyText.includes('Search failed') || bodyText.includes('error') && bodyText.includes('failed')) {
          report.errors.push('Search returned error state');
          break;
        }
      }

      const shot3 = path.join(OUTPUT_DIR, '03-results.png');
      await page.screenshot({ path: shot3, fullPage: true });
      report.screenshots.push('03-results.png');
      console.log('Screenshot 3 (results):', shot3);
    }

    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    return report;
  } catch (e) {
    report.errors.push('Exception: ' + e.message);
    try {
      const errShot = path.join(OUTPUT_DIR, '99-error-state.png');
      await page.screenshot({ path: errShot, fullPage: true });
      report.screenshots.push('99-error-state.png');
    } catch (_) {}
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    throw e;
  } finally {
    await context.close();
  }
}

run()
  .then((r) => {
    console.log('\n=== DEPLOYED VISUAL RECOGNITION TEST REPORT ===');
    console.log('Authenticated:', r.authenticated);
    console.log('UI verified (new design):', r.uiVerified);
    console.log('Upload succeeded:', r.uploadSucceeded);
    console.log('Search succeeded:', r.searchSucceeded);
    console.log('Results count:', r.resultsCount);
    console.log('Errors:', r.errors.length ? r.errors : 'none');
    console.log('Console errors:', r.consoleErrors.length);
    console.log('API calls (find similar):', r.apiCalls.length);
    console.log('Screenshots:', r.screenshots);
    console.log('Full report: deployed-visual-recognition-output/report.json');
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

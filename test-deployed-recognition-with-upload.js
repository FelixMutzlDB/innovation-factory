/**
 * Test deployed Databricks app - Visual Recognition with full flow:
 * 1. Navigate to recognition page
 * 2. Handle auth if login page
 * 3. Screenshot initial UI
 * 4. Upload test image
 * 5. Click Find Similar, wait for results
 * 6. Screenshot results
 *
 * Run: HEADED=1 node test-deployed-recognition-with-upload.js
 * (HEADED=1 allows manual login if session expired)
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const TEST_IMAGE = '/Users/sascha.saumer/.cursor/projects/Users-sascha-saumer-GIT-innovation-factory/assets/test_black_tshirt-52a79a5a-a944-4474-a159-9ce0c4e657c8.png';
const OUTPUT_DIR = path.join(__dirname, 'test-recognition-output');
const USER_DATA_DIR = path.join(__dirname, '.playwright-auth-state');
const HEADED = process.env.HEADED === '1';

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const report = {
    timestamp: new Date().toISOString(),
    url: TARGET_URL,
    testImage: TEST_IMAGE,
    screenshots: [],
    authState: null,
    uiVerification: {},
    uploadSuccess: null,
    findSimilarClicked: null,
    resultsCount: null,
    resultsError: null,
    consoleErrors: [],
    failedRequests: [],
    apiCalls: [],
  };

  console.log('Launching browser...', HEADED ? '(headed - log in if prompted)' : '(headless, using saved auth)');
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: !HEADED,
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });

  const pages = context.pages();
  const page = pages.length > 0 ? pages[0] : await context.newPage();

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
    if (url.includes('find-similar') || url.includes('similar') || url.includes('/api/')) {
      apiCalls.push({ url, status: res.status() });
    }
  });

  const getBodyText = () => page.evaluate(() => document.body.innerText);
  const isLoginPage = (text) =>
    (text.includes('Log in') && text.includes('Continue with SSO')) ||
    (text.includes('Sign In') && text.includes('Email')) ||
    text.includes('Verify with Security Key');

  const isRecognitionPage = (text) =>
    text.includes('Visual Product Recognition') &&
    (text.includes('Find Similar') || text.includes('Upload Image'));

  try {
    // 1. Navigate
    console.log('Navigating to', TARGET_URL, '...');
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(3000);

    let bodyText = await getBodyText();
    if (isLoginPage(bodyText)) {
      report.authState = 'login_required';
      await page.screenshot({ path: path.join(OUTPUT_DIR, '01-login-page.png'), fullPage: true });
      report.screenshots.push('01-login-page.png');
      console.log('Login page detected. Session may have expired.');
      if (!HEADED) {
        console.log('Run with HEADED=1 to log in manually, then re-run this script.');
      } else {
        console.log('Please complete SSO login. Waiting 90 seconds...');
        for (let i = 0; i < 18; i++) {
          await page.waitForTimeout(5000);
          bodyText = await getBodyText();
          if (isRecognitionPage(bodyText)) {
            console.log('Logged in. Proceeding...');
            report.authState = 'logged_in_after_wait';
            break;
          }
          if (i === 17) {
            console.log('Timeout - did not reach recognition page.');
            report.authState = 'login_timeout';
            await context.close();
            fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
            return report;
          }
        }
      }
      if (report.authState === 'login_required') {
        await context.close();
        fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
        return report;
      }
    } else if (isRecognitionPage(bodyText)) {
      report.authState = 'already_authenticated';
    } else {
      report.authState = 'unknown';
    }

    // 2. Screenshot initial UI
    await page.screenshot({ path: path.join(OUTPUT_DIR, '02-recognition-ui.png'), fullPage: true });
    report.screenshots.push('02-recognition-ui.png');
    report.uiVerification = {
      hasHeader: bodyText.includes('Visual Product Recognition'),
      hasUploadCard: bodyText.includes('Upload Image') && bodyText.includes('Drag and drop'),
      hasFindSimilar: bodyText.includes('Find Similar'),
      noJobsTable: !bodyText.includes('Recent Recognition Jobs'),
    };
    console.log('UI verification:', report.uiVerification);

    // 3. Upload test image
    if (!fs.existsSync(TEST_IMAGE)) {
      report.uploadSuccess = false;
      report.resultsError = `Test image not found: ${TEST_IMAGE}`;
      console.error('Test image not found:', TEST_IMAGE);
    } else {
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(TEST_IMAGE);
      await page.waitForTimeout(1500);
      report.uploadSuccess = true;
      console.log('Uploaded test image');

      bodyText = await getBodyText();
      if (bodyText.includes('Remove') || bodyText.includes(TEST_IMAGE.split('/').pop())) {
        report.uploadSuccess = true;
      }

      await page.screenshot({ path: path.join(OUTPUT_DIR, '03-after-upload.png'), fullPage: true });
      report.screenshots.push('03-after-upload.png');

      // 4. Click Find Similar
      const findSimilarBtn = page.locator('button:has-text("Find Similar")');
      if (await findSimilarBtn.isVisible().catch(() => false)) {
        await findSimilarBtn.click();
        report.findSimilarClicked = true;
        console.log('Clicked Find Similar...');

        // 5. Wait for results (up to 30s)
        try {
          await page.waitForSelector('text=Similar Images', { timeout: 15000 });
          console.log('Results container appeared');
        } catch (e) {
          console.log('Waiting for results container...');
        }
        await page.waitForTimeout(5000);

        bodyText = await getBodyText();
        if (bodyText.includes('Similar Images')) {
          const match = bodyText.match(/(\d+)\s*result/);
          report.resultsCount = match ? parseInt(match[1], 10) : null;
          report.resultsError = bodyText.includes('No similar images found')
            ? 'No results'
            : bodyText.includes('Search failed')
              ? 'Search failed'
              : null;
        } else {
          report.resultsError = bodyText.includes('Search failed')
            ? 'Search failed'
            : 'Results did not appear';
        }

        // 6. Screenshot results
        await page.screenshot({ path: path.join(OUTPUT_DIR, '04-results.png'), fullPage: true });
        report.screenshots.push('04-results.png');
        console.log('Screenshot: 04-results.png');
      } else {
        report.findSimilarClicked = false;
        report.resultsError = 'Find Similar button not visible';
      }
    }

    report.consoleErrors = [...consoleErrors];
    report.failedRequests = [...failedRequests];
    report.apiCalls = apiCalls;
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    return report;
  } catch (err) {
    report.resultsError = err.message || String(err);
    report.consoleErrors = [...consoleErrors];
    report.failedRequests = [...failedRequests];
    report.apiCalls = apiCalls;
    await page.screenshot({ path: path.join(OUTPUT_DIR, '99-error.png'), fullPage: true }).catch(() => {});
    report.screenshots.push('99-error.png');
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    throw err;
  } finally {
    await context.close();
  }
}

run()
  .then((r) => {
    console.log('\n=== DEPLOYED RECOGNITION TEST REPORT ===');
    console.log('Auth state:', r.authState);
    console.log('UI verification:', JSON.stringify(r.uiVerification, null, 2));
    console.log('Upload success:', r.uploadSuccess);
    console.log('Find Similar clicked:', r.findSimilarClicked);
    console.log('Results count:', r.resultsCount);
    console.log('Results error:', r.resultsError);
    console.log('Console errors:', r.consoleErrors.length);
    console.log('Failed requests:', r.failedRequests.length);
    console.log('API calls:', r.apiCalls.length);
    console.log('Screenshots:', r.screenshots);
    console.log('Full report: test-recognition-output/report.json');
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

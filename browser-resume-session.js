/**
 * Resume browser session - assume user has logged in.
 * 1. List tabs (we use single page)
 * 2. Snapshot current page
 * 3. Navigate to recognition, wait 3s, screenshot
 * 4. Navigate to authenticity, wait 3s, screenshot
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const RECOGNITION_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const AUTHENTICITY_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/authenticity';
const OUTPUT_DIR = path.join(__dirname, 'browser-resume-output');
const USER_DATA_DIR = path.join(__dirname, '.playwright-auth-state');

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  console.log('Launching browser with persistent context (may have saved session)...');
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false,
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  });

  const pages = context.pages();
  const page = pages.length > 0 ? pages[0] : await context.newPage();

  console.log('Tabs/pages:', pages.length);

  // 1. Navigate to recognition first (in case we start blank)
  console.log('Navigating to recognition page...');
  await page.goto(RECOGNITION_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(3000);

  const getBodyText = () => page.evaluate(() => document.body.innerText);
  const isLoginPage = (text) =>
    text.includes('Log in') && text.includes('Continue with SSO') ||
    text.includes('Sign In') && text.includes('Username') ||
    text.includes('Verify with Security Key') ||
    text.includes('Waiting for the Kolide Agent');

  let text = await getBodyText();
  if (isLoginPage(text)) {
    console.log('Still on login page - session may have expired. Taking screenshot.');
    await page.screenshot({ path: path.join(OUTPUT_DIR, '00-login-page.png'), fullPage: true });
    await context.close();
    console.log('Screenshot: 00-login-page.png');
    process.exit(0);
    return;
  }

  // 2. Snapshot of recognition page
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01-recognition.png'), fullPage: true });
  console.log('Screenshot 1 (recognition): 01-recognition.png');

  text = await getBodyText();
  const recognitionReport = {
    hasJobsTable: text.includes('Recent Recognition Jobs') || text.includes('Job ID'),
    hasJobsError: text.includes('Failed to load recognition jobs'),
    hasUploadArea: text.includes('Drop product image here or click to browse'),
    hasImagePreview: text.includes('Remove') || text.includes('preview'), // after file select
  };

  await page.waitForTimeout(3000);

  // 3. Navigate to authenticity
  console.log('Navigating to authenticity page...');
  await page.goto(AUTHENTICITY_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(3000);

  await page.screenshot({ path: path.join(OUTPUT_DIR, '02-authenticity.png'), fullPage: true });
  console.log('Screenshot 2 (authenticity): 02-authenticity.png');

  text = await getBodyText();
  const authenticityReport = {
    hasVerificationData: text.includes('Verification') || text.includes('Authenticity') || text.includes('Verified') || text.includes('Result'),
    hasError: text.includes('Failed to load') || text.includes('Error'),
  };

  const report = {
    recognition: recognitionReport,
    authenticity: authenticityReport,
    screenshots: ['01-recognition.png', '02-authenticity.png'],
  };
  fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
  console.log('\nReport:', JSON.stringify(report, null, 2));
  await context.close();
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});

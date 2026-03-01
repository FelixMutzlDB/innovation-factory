/**
 * Open browser, navigate to recognition.
 * WAIT for user to complete login (checks every 5s for up to 2 min).
 * Once app page detected: screenshot recognition, navigate to authenticity, screenshot.
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

  console.log('Launching browser (headed). Please complete SSO login when the page opens.');
  console.log('Waiting up to 2 minutes for app page...\n');
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false,
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  });

  const page = context.pages()[0] || await context.newPage();
  await page.goto(RECOGNITION_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });

  const getBodyText = () => page.evaluate(() => document.body.innerText).catch(() => '');
  const isLoginPage = (text) =>
    (text.includes('Log in') && text.includes('Continue with SSO')) ||
    text.includes('Sign In') && text.includes('Username') ||
    text.includes('Verify with Security Key') ||
    text.includes('Waiting for the Kolide Agent');

  for (let i = 0; i < 24; i++) {
    await page.waitForTimeout(5000);
    const text = await getBodyText();
    if (!isLoginPage(text) && (text.includes('Visual Product Recognition Hub') || text.includes('innovation-factory'))) {
      console.log(`App page detected after ~${(i + 1) * 5}s`);
      break;
    }
    if (i === 23) {
      console.log('Timeout: app page not detected. Taking screenshot of current state.');
      await page.screenshot({ path: path.join(OUTPUT_DIR, '00-timeout.png'), fullPage: true });
      await context.close();
      process.exit(0);
      return;
    }
  }

  // Ensure we're on recognition
  await page.goto(RECOGNITION_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  await page.screenshot({ path: path.join(OUTPUT_DIR, '01-recognition.png'), fullPage: true });
  let text = await getBodyText();
  const recognitionReport = {
    hasJobsTable: text.includes('Recent Recognition Jobs') || text.includes('Job ID'),
    hasJobsError: text.includes('Failed to load recognition jobs'),
    hasJobsData: /\b\d+\b/.test(text) && text.includes('Status'),
    hasUploadArea: text.includes('Drop product image here or click to browse'),
    hasImagePreview: text.includes('Remove') || text.includes('preview'),
  };
  console.log('Recognition:', recognitionReport);

  await page.goto(AUTHENTICITY_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  await page.screenshot({ path: path.join(OUTPUT_DIR, '02-authenticity.png'), fullPage: true });
  text = await getBodyText();
  const authenticityReport = {
    hasVerificationData: text.includes('Verification') || text.includes('Authenticity') || text.includes('Verified') || text.includes('Result') || text.includes('Scan'),
    hasError: text.includes('Failed to load') || text.includes('Error loading'),
  };
  console.log('Authenticity:', authenticityReport);

  fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify({ recognition: recognitionReport, authenticity: authenticityReport }, null, 2));
  console.log('\nScreenshots saved. Closing in 5s...');
  await page.waitForTimeout(5000);
  await context.close();
}

run().catch((e) => { console.error(e); process.exit(1); });

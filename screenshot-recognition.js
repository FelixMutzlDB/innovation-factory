/**
 * Navigate to recognition page and take screenshot for verification
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'http://localhost:9001/projects/hb-product-center/recognition';
const OUTPUT_DIR = path.join(__dirname, 'debug-recognition-output');

async function run() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1280, height: 900 },
  });

  await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(3000);

  const bodyText = await page.evaluate(() => document.body.innerText);
  const screenshotPath = path.join(OUTPUT_DIR, 'recognition-verification.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });

  await browser.close();

  return { bodyText, screenshotPath };
}

run()
  .then(({ bodyText, screenshotPath }) => {
    console.log('Screenshot saved to:', screenshotPath);
    console.log('\n=== PAGE TEXT (for verification) ===\n');
    console.log(bodyText);
    
    const checks = {
      hasHeader: bodyText.includes('Visual Product Recognition'),
      hasUploadCard: bodyText.includes('Upload Image') && bodyText.includes('Drag and drop or click to upload'),
      hasDragDrop: bodyText.includes('Drop product image here') || bodyText.includes('drag'),
      hasFindSimilar: bodyText.includes('Find Similar'),
      noSubmitJob: !bodyText.includes('Submit Recognition Job'),
      noRecentJobs: !bodyText.includes('Recent Recognition Jobs'),
      noAIIdentification: !bodyText.includes('AI Product Identification'),
    };
    console.log('\n=== VERIFICATION CHECKS ===');
    Object.entries(checks).forEach(([k, v]) => console.log(`${k}: ${v ? '✓' : '✗'}`));
  })
  .catch((e) => { console.error(e); process.exit(1); });

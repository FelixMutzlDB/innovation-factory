/**
 * Debug script for recognition page at Databricks Apps URL
 * Captures: screenshot, console errors, network failures, image upload elements
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/recognition';
const OUTPUT_DIR = path.join(__dirname, 'debug-recognition-output');

async function run() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  const consoleLogs = [];
  const consoleErrors = [];
  const failedRequests = [];

  page.on('console', (msg) => {
    const text = msg.text();
    const type = msg.type();
    if (type === 'error') {
      consoleErrors.push(text);
    }
    consoleLogs.push(`[${type}] ${text}`);
  });

  page.on('requestfailed', (request) => {
    failedRequests.push({
      url: request.url(),
      failure: request.failure()?.errorText || 'Unknown',
      method: request.method(),
    });
  });

  const report = {
    url: TARGET_URL,
    timestamp: new Date().toISOString(),
    screenshot: null,
    pageLayout: null,
    consoleErrors: [],
    consoleLogsCount: 0,
    failedRequests: [],
    imageUploadElements: [],
    errorMessagesOnPage: [],
    clickAttemptResult: null,
  };

  try {
    // 1. Navigate
    console.log('Navigating to', TARGET_URL, '...');
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });

    // Wait for page to settle
    await page.waitForTimeout(5000);

    // 2. Screenshot
    const screenshotPath = path.join(OUTPUT_DIR, 'recognition-screenshot.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    report.screenshot = screenshotPath;
    console.log('Screenshot saved:', screenshotPath);

    // 3. Get page content and structure
    const html = await page.content();
    const bodyText = await page.evaluate(() => document.body.innerText);
    report.pageLayout = bodyText.slice(0, 2000);

    // 4. Find image upload elements
    const uploadSelectors = [
      'input[type="file"][accept*="image"]',
      'input[type="file"]',
      '[data-testid*="upload"]',
      '[data-testid*="dropzone"]',
      '[data-testid*="image"]',
      'button:has-text("upload")',
      'button:has-text("Upload")',
      'button:has-text("image")',
      'button:has-text("Image")',
      'a:has-text("upload")',
      'a:has-text("Upload")',
      '[role="button"]:has-text("upload")',
      '[role="button"]:has-text("Upload")',
      '.dropzone',
      '[class*="dropzone"]',
      '[class*="upload"]',
    ];

    for (const selector of uploadSelectors) {
      try {
        const els = await page.$$(selector);
        for (const el of els) {
          const info = await el.evaluate((e) => ({
            tag: e.tagName,
            type: e.type || null,
            accept: e.accept || null,
            name: e.name || null,
            id: e.id || null,
            className: e.className || null,
            placeholder: e.placeholder || null,
            ariaLabel: e.getAttribute('aria-label') || null,
            text: e.textContent?.slice(0, 100) || null,
            visible: e.offsetParent !== null && e.offsetWidth > 0 && e.offsetHeight > 0,
          })).catch(() => null);
          if (info) {
            report.imageUploadElements.push({ selector, ...info });
          }
        }
      } catch (_) {}
    }

    // 5. Look for error messages on page
    const errorSelectors = [
      '[role="alert"]',
      '[class*="error"]',
      '[class*="Error"]',
      '.error-message',
      '[data-error]',
      '.toast',
      '[aria-live="assertive"]',
    ];
    for (const selector of errorSelectors) {
      try {
        const els = await page.$$(selector);
        for (const el of els) {
          const text = await el.evaluate((e) => e.textContent?.trim()).catch(() => null);
          if (text && text.length > 0) {
            report.errorMessagesOnPage.push({ selector, text });
          }
        }
      } catch (_) {}
    }

    // 6. Try to click first upload element
    const uploadInput = await page.$('input[type="file"]');
    const uploadButton = await page.$('button:has-text("Upload"), button:has-text("upload"), [data-testid*="upload"]');
    const dropzone = await page.$('.dropzone, [class*="dropzone"]');

    if (uploadInput || uploadButton || dropzone) {
      const target = uploadInput || uploadButton || dropzone;
      try {
        await target.click();
        report.clickAttemptResult = { success: true, element: target === uploadInput ? 'input' : target === uploadButton ? 'button' : 'dropzone' };
        await page.waitForTimeout(3000);
        await page.screenshot({ path: path.join(OUTPUT_DIR, 'after-click.png'), fullPage: true });
      } catch (e) {
        report.clickAttemptResult = { success: false, error: e.message };
      }
    } else {
      report.clickAttemptResult = { success: false, error: 'No upload element found' };
    }

    // 7. Collect report data
    report.consoleErrors = [...consoleErrors];
    report.consoleLogsCount = consoleLogs.length;
    report.failedRequests = [...failedRequests];

    // 8. Write report
    const reportPath = path.join(OUTPUT_DIR, 'recognition-debug-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2, (key, val) => (val instanceof Error ? val.message : val)));
    console.log('Report saved:', reportPath);

    // 9. Write console logs
    fs.writeFileSync(path.join(OUTPUT_DIR, 'console-logs.txt'), consoleLogs.join('\n'));
    console.log('Console logs saved');

    return report;
  } finally {
    await browser.close();
  }
}

run()
  .then((r) => {
    console.log('\n=== SUMMARY ===');
    console.log('Console errors:', r.consoleErrors.length);
    console.log('Failed requests:', r.failedRequests.length);
    console.log('Image upload elements found:', r.imageUploadElements.length);
    console.log('Error messages on page:', r.errorMessagesOnPage.length);
    console.log('Click attempt:', JSON.stringify(r.clickAttemptResult, null, 2));
    if (r.consoleErrors.length) console.log('\nConsole errors:', r.consoleErrors);
    if (r.failedRequests.length) console.log('\nFailed requests:', r.failedRequests);
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

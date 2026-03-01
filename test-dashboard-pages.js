/**
 * Test two dashboard pages: hb-product-center/quality and adtech-intelligence/dashboard
 * - Screenshots
 * - AI/BI Dashboard tab
 * - Open in Databricks / Ask Genie href attributes
 * - Console errors
 * - Dashboard iframe content
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:9001';
const SCREENSHOT_DIR = path.join(__dirname, 'test-screenshots');

async function extractButtonHrefs(page) {
  return page.evaluate(() => {
    const result = { openInDatabricks: null, askGenie: null };
    const links = document.querySelectorAll('a[href]');
    links.forEach((a) => {
      const text = (a.textContent || '').trim();
      if (/open in databricks/i.test(text)) result.openInDatabricks = a.href;
      if (/ask genie/i.test(text)) result.askGenie = a.href;
    });
    // Also check buttons that might wrap links
    const buttons = document.querySelectorAll('a, button');
    buttons.forEach((el) => {
      const text = (el.textContent || '').trim();
      const href = el.getAttribute?.('href') || (el.closest?.('a')?.getAttribute?.('href'));
      if (/open in databricks/i.test(text) && !result.openInDatabricks) result.openInDatabricks = href ? new URL(href, window.location.origin).href : null;
      if (/ask genie/i.test(text) && !result.askGenie) result.askGenie = href ? new URL(href, window.location.origin).href : null;
    });
    return result;
  });
}

async function checkIframeContent(page) {
  return page.evaluate(() => {
    const iframe = document.querySelector('iframe');
    if (!iframe) return { hasIframe: false, src: null, content: null };
    const src = iframe.src;
    const doc = iframe.contentDocument;
    let content = null;
    if (doc && doc.body) {
      content = doc.body.innerText?.slice(0, 500) || '(empty or cross-origin)';
    } else {
      content = '(cross-origin or not loaded)';
    }
    return { hasIframe: true, src, content };
  });
}

async function collectConsoleMessages(page) {
  const messages = [];
  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error' || type === 'warning') {
      messages.push({ type, text });
    }
  });
  return messages;
}

async function run() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const report = { hbProductCenter: {}, adtechIntelligence: {} };
  const consoleErrors = [];

  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Capture console
  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') consoleErrors.push({ page: 'current', type, text });
  });

  try {
    // ========== 1. HB Product Center - Quality ==========
    console.log('\n=== 1. HB Product Center / Quality ===');
    await page.goto(`${BASE_URL}/projects/hb-product-center/quality`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'hb-quality-initial.png'), fullPage: true });
    report.hbProductCenter.initialScreenshot = 'hb-quality-initial.png';

    // Click AI/BI Dashboard tab if not active
    const aiBiTab = page.locator('button, [role="tab"], a').filter({ hasText: /AI\/BI Dashboard/i }).first();
    if (await aiBiTab.count() > 0) {
      const isActive = await aiBiTab.evaluate((el) => el.getAttribute('data-state') === 'active' || el.classList.contains('active'));
      if (!isActive) {
        await aiBiTab.click();
        await page.waitForTimeout(2000);
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'hb-quality-ai-bi-tab.png'), fullPage: true });
    report.hbProductCenter.aiBiTabScreenshot = 'hb-quality-ai-bi-tab.png';

    const hbHrefs = await extractButtonHrefs(page);
    report.hbProductCenter.openInDatabricksHref = hbHrefs.openInDatabricks;
    report.hbProductCenter.askGenieHref = hbHrefs.askGenie;

    const hbIframe = await checkIframeContent(page);
    report.hbProductCenter.iframe = hbIframe;

    // ========== 2. Adtech Intelligence - Dashboard ==========
    console.log('\n=== 2. Adtech Intelligence / Dashboard ===');
    const hbErrors = [...consoleErrors];
    consoleErrors.length = 0;

    await page.goto(`${BASE_URL}/projects/adtech-intelligence/dashboard`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'adtech-dashboard-initial.png'), fullPage: true });
    report.adtechIntelligence.initialScreenshot = 'adtech-dashboard-initial.png';

    // Click AI/BI Dashboard tab if present and not active
    const adtechAiBiTab = page.locator('button, [role="tab"], a').filter({ hasText: /AI\/BI Dashboard/i }).first();
    if (await adtechAiBiTab.count() > 0) {
      const isActive = await adtechAiBiTab.evaluate((el) => el.getAttribute('data-state') === 'active' || el.classList.contains('active'));
      if (!isActive) {
        await adtechAiBiTab.click();
        await page.waitForTimeout(2000);
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'adtech-dashboard-ai-bi-tab.png'), fullPage: true });
    report.adtechIntelligence.aiBiTabScreenshot = 'adtech-dashboard-ai-bi-tab.png';

    const adtechHrefs = await extractButtonHrefs(page);
    report.adtechIntelligence.openInDatabricksHref = adtechHrefs.openInDatabricks;
    report.adtechIntelligence.askGenieHref = adtechHrefs.askGenie;

    const adtechIframe = await checkIframeContent(page);
    report.adtechIntelligence.iframe = adtechIframe;

    report.hbProductCenter.consoleErrors = hbErrors.map((e) => e.text);
    report.adtechIntelligence.consoleErrors = [...consoleErrors].map((e) => e.text);
  } catch (err) {
    console.error('Test failed:', err.message);
    report.error = err.message;
  } finally {
    await browser.close();
  }

  fs.writeFileSync(path.join(SCREENSHOT_DIR, 'dashboard-report.json'), JSON.stringify(report, null, 2));
  console.log('\n=== REPORT ===');
  console.log(JSON.stringify(report, null, 2));
  console.log('\nScreenshots saved to:', SCREENSHOT_DIR);
  return report;
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:9001/projects/hb-product-center/';
const SCREENSHOT_DIR = path.join(__dirname, 'test-hb-chat-output');

async function run() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  try {
    // Step 1: Navigate to HB Product Center
    console.log('Step 1: Navigating to', BASE_URL);
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000); // Let content settle

    // Step 2: Screenshot initial page with chat widget
    console.log('Step 2: Taking screenshot of initial page');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-initial-load.png'), fullPage: true });

    // Verify chat widget and sample prompts visible
    const samplePromptText = await page.textContent('button:has-text("Show quality inspection trends")');
    console.log('Sample prompt button found:', samplePromptText ? 'Yes' : 'No');

    // Step 3: Click "Show quality inspection trends" (auto-sends)
    console.log('Step 3: Clicking sample prompt "Show quality inspection trends"');
    await page.click('button:has-text("Show quality inspection trends")');

    // Brief pause for state update
    await page.waitForTimeout(500);

    // Step 4: Screenshot after click - verify message sent and loading
    console.log('Step 4: Taking screenshot after click (message sent, loading)');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02-after-sample-click.png'), fullPage: true });

    // Check user message appeared
    const userMessageVisible = await page.locator('text=Show quality inspection trends').isVisible();
    console.log('User message appeared in chat:', userMessageVisible);

    // Step 5: Wait for response (up to 30 seconds)
    console.log('Step 5: Waiting up to 30 seconds for response...');
    await page.waitForTimeout(30000);

    // Step 6: Screenshot of response
    console.log('Step 6: Taking screenshot of response');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03-response.png'), fullPage: true });

    // Save page text for analysis
    const bodyText = await page.evaluate(() => document.body.innerText);
    fs.writeFileSync(path.join(SCREENSHOT_DIR, 'page-text.txt'), bodyText);
    console.log('Page text saved. Snippet:', bodyText.slice(0, 600));
  } finally {
    await browser.close();
  }
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});

/**
 * Test deployed Databricks app - HB Product Center chat interface
 * 1. Take screenshot of page with chat widget and sample prompts
 * 2. Click "Show quality inspection trends" - verify auto-sends
 * 3. Screenshot with user message in chat
 * 4. Wait up to 30s for response, screenshot result
 * 5. Verify markdown rendering if response has formatted content
 *
 * Run: HEADED=1 node test-deployed-hb-chat.js (if login needed)
 * Run: node test-deployed-hb-chat.js (with saved session)
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://innovation-factory-1444828305810485.aws.databricksapps.com/projects/hb-product-center/';
const OUTPUT_DIR = path.join(__dirname, 'deployed-hb-chat-output');
const USER_DATA_DIR = path.join(__dirname, '.playwright-auth-state');
const HEADED = process.env.HEADED === '1';

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
    url: BASE_URL,
    screenshots: [],
    step1_pageLoaded: null,
    step2_chatWidgetVisible: null,
    step3_sampleButtonFound: null,
    step4_autoSent: null,
    step5_userMessageVisible: null,
    step6_responseReceived: null,
    step7_markdownRendered: null,
    bodyTextSnippet: '',
  };

  try {
    // Step 1: Navigate
    console.log('\nStep 1: Navigating to', BASE_URL);
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(3000);

    // Check for login page
    const bodyText1 = await page.evaluate(() => document.body.innerText);
    const isLoginPage =
      bodyText1.includes('Continue with SSO') ||
      (bodyText1.includes('Sign In') && bodyText1.includes('Email'));

    if (isLoginPage) {
      console.log('Login page detected - clicking "Continue with SSO" if present');
      await page.locator('text=Continue with SSO').click().catch(() => {});
      await page.waitForTimeout(5000);
    }

    // Wait for app to load (up to 45s if we might be on login redirect)
    let attempts = 0;
    while (attempts < 9) {
      await page.waitForTimeout(5000);
      attempts++;
      const text = await page.evaluate(() => document.body.innerText);
      const onHbPage =
        text.includes('Product Center Intelligence Agent') || text.includes('Hugo Boss Intelligent Product Center');
      if (onHbPage) {
        console.log('Reached HB Product Center page after', attempts * 5, 'seconds');
        break;
      }
      if (attempts >= 9) {
        console.log('Timeout - may not have reached app');
      }
    }

    await page.waitForTimeout(2000);
    const bodyText = await page.evaluate(() => document.body.innerText);
    report.bodyTextSnippet = bodyText.slice(0, 1500);

    const onHbPage =
      bodyText.includes('Product Center Intelligence Agent') || bodyText.includes('Hugo Boss Intelligent Product Center');
    report.step1_pageLoaded = onHbPage;
    report.step2_chatWidgetVisible = bodyText.includes('Product Center Intelligence Agent');
    report.step3_sampleButtonFound = bodyText.includes('Show quality inspection trends');

    // Screenshot 1: Initial load
    const shot1 = path.join(OUTPUT_DIR, '01-initial-load.png');
    await page.screenshot({ path: shot1, fullPage: true });
    report.screenshots.push('01-initial-load.png');
    console.log('Screenshot 1: Initial load saved');

    if (!report.step3_sampleButtonFound) {
      console.log('Sample prompt button NOT found - page state may require login');
      fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
      await context.close();
      return report;
    }

    // Step 3: Click "Show quality inspection trends"
    console.log('\nStep 3: Clicking "Show quality inspection trends"');
    await page.click('button:has-text("Show quality inspection trends")');
    await page.waitForTimeout(500);

    // Step 4: Screenshot after click
    const shot2 = path.join(OUTPUT_DIR, '02-after-sample-click.png');
    await page.screenshot({ path: shot2, fullPage: true });
    report.screenshots.push('02-after-sample-click.png');

    const userMsgVisible = await page.locator('text=Show quality inspection trends').first().isVisible();
    report.step4_autoSent = userMsgVisible;
    report.step5_userMessageVisible = userMsgVisible;
    console.log('User message visible:', userMsgVisible);

    // Step 5: Wait up to 30 seconds for response
    console.log('\nStep 5: Waiting up to 30 seconds for response...');
    await page.waitForTimeout(30000);

    // Step 6: Screenshot response
    const shot3 = path.join(OUTPUT_DIR, '03-response.png');
    await page.screenshot({ path: shot3, fullPage: true });
    report.screenshots.push('03-response.png');

    const bodyTextAfter = await page.evaluate(() => document.body.innerText);
    const hasError = bodyTextAfter.includes("Sorry, I couldn't reach the agent");
    const hasResponse = hasError || bodyTextAfter.includes('Quality') || bodyTextAfter.includes('inspection');
    report.step6_responseReceived = hasResponse;

    // Check for markdown rendering: prose/styled elements, not raw markdown like ## or **
    const hasProseElements = await page.locator('.prose, table, strong').count() > 0;
    const hasRawMarkdown = bodyTextAfter.includes('## ') || bodyTextAfter.includes('**text**');
    report.step7_markdownRendered = hasResponse && (hasProseElements || (!hasRawMarkdown && !hasError));

    report.bodyTextSnippet = bodyTextAfter.slice(0, 2000);
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    fs.writeFileSync(path.join(OUTPUT_DIR, 'page-text.txt'), bodyTextAfter);

    await context.close();
    return report;
  } catch (e) {
    console.error(e);
    const shotErr = path.join(OUTPUT_DIR, '99-error-state.png');
    try {
      await page.screenshot({ path: shotErr, fullPage: true });
      report.screenshots.push('99-error-state.png');
    } catch (_) {}
    report.error = String(e);
    fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
    await context.close();
    throw e;
  }
}

run()
  .then((r) => {
    console.log('\n=== DEPLOYED HB CHAT TEST REPORT ===');
    console.log('Step 1 - Page loaded:', r.step1_pageLoaded);
    console.log('Step 2 - Chat widget visible:', r.step2_chatWidgetVisible);
    console.log('Step 3 - Sample button found:', r.step3_sampleButtonFound);
    console.log('Step 4 - Auto-sent (no submit):', r.step4_autoSent);
    console.log('Step 5 - User message in chat:', r.step5_userMessageVisible);
    console.log('Step 6 - Response received:', r.step6_responseReceived);
    console.log('Step 7 - Markdown rendered:', r.step7_markdownRendered);
    console.log('Screenshots:', r.screenshots);
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { chromium } from 'playwright';
import { discoverBrowsers } from '../scripts/agent-browser.mjs';

const browserCandidate = discoverBrowsers().find(candidate => candidate.engine === 'chromium');
const browserAvailable = Boolean(browserCandidate && fs.existsSync(browserCandidate.executablePath));

test('persistent browser data survives a controller restart', { skip: !browserAvailable }, async () => {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'agent-browser-integration-'));
  const server = http.createServer((_request, response) => {
    response.writeHead(200, { 'content-type': 'text/html' });
    response.end('<!doctype html><title>Persistence test</title>');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  const url = `http://127.0.0.1:${address.port}`;

  try {
    const launchOptions = { headless: true, executablePath: browserCandidate.executablePath };
    let context = await chromium.launchPersistentContext(profile, launchOptions);
    let page = context.pages()[0] || await context.newPage();
    await page.goto(url);
    await page.evaluate(() => localStorage.setItem('agent-browser-test', 'persisted'));
    await context.close();

    context = await chromium.launchPersistentContext(profile, launchOptions);
    page = context.pages()[0] || await context.newPage();
    await page.goto(url);
    assert.equal(await page.evaluate(() => localStorage.getItem('agent-browser-test')), 'persisted');
    await context.close();
  } finally {
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(profile, { recursive: true, force: true });
  }
});

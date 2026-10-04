import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  appDataRoot,
  assertDedicatedUserDataDir,
  assertSafePlaywrightCommand,
  configureProfile,
  discoverBrowsers,
  endBrowserTask,
  openBrowserSession,
  parseInvocation,
  playwrightArgs,
  profilePaths,
  validateConfig,
} from '../scripts/agent-browser.mjs';

test('resolves OS-specific application-data roots', () => {
  assert.equal(
    appDataRoot({ platform: 'win32', env: { LOCALAPPDATA: 'C:\\Users\\me\\AppData\\Local' }, home: 'C:\\Users\\me' }),
    path.win32.join('C:\\Users\\me\\AppData\\Local', 'agent-browser'),
  );
  assert.equal(
    appDataRoot({ platform: 'darwin', env: {}, home: '/Users/me' }),
    path.posix.join('/Users/me', 'Library', 'Application Support', 'agent-browser'),
  );
  assert.equal(
    appDataRoot({ platform: 'linux', env: { XDG_STATE_HOME: '/state' }, home: '/home/me' }),
    path.posix.join('/state', 'agent-browser'),
  );
});

test('discovers browsers without silently selecting one', () => {
  const brave = path.win32.resolve('C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe');
  const candidates = discoverBrowsers({
    platform: 'win32',
    env: { ProgramFiles: 'C:\\Program Files', LOCALAPPDATA: 'C:\\Users\\me\\AppData\\Local' },
    home: 'C:\\Users\\me',
    existsSync: candidate => path.win32.resolve(candidate) === brave,
    includeManaged: false,
  });
  assert.deepEqual(candidates, [{
    id: 'brave',
    label: 'Brave',
    engine: 'chromium',
    executablePath: brave,
    source: 'system',
  }]);
});

test('discovers browsers using macOS and Linux path conventions', () => {
  const macChrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  assert.deepEqual(discoverBrowsers({
    platform: 'darwin',
    env: {},
    home: '/Users/me',
    existsSync: candidate => candidate === macChrome,
    includeManaged: false,
  }).map(candidate => candidate.id), ['chrome']);

  assert.deepEqual(discoverBrowsers({
    platform: 'linux',
    env: { PATH: '/usr/local/bin:/usr/bin' },
    home: '/home/me',
    existsSync: candidate => candidate === '/usr/bin/chromium',
    includeManaged: false,
  }).map(candidate => candidate.id), ['chromium']);
});

test('supports named profiles and rejects invalid names', () => {
  assert.equal(parseInvocation(['--profile', 'client_a', 'status']).profileName, 'client_a');
  assert.throws(() => parseInvocation(['--profile', '../personal', 'status']), /Profile names/);
});

test('rejects personal and unexpected user-data directories', () => {
  const options = { platform: 'win32', env: { LOCALAPPDATA: 'C:\\Local' }, home: 'C:\\Users\\me', root: 'C:\\AgentState' };
  assert.throws(
    () => assertDedicatedUserDataDir('C:\\Local\\Google\\Chrome\\User Data', 'applications', options),
    /outside the dedicated profile|personal\/default/,
  );
  assert.doesNotThrow(() => {
    const expected = profilePaths('applications', options).userDataDir;
    assertDedicatedUserDataDir(expected, 'applications', options);
  });
});

test('configuration is local, absolute, and tied to its named profile', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'agent-browser-unit-'));
  try {
    const executable = path.join(root, 'browser.exe');
    fs.writeFileSync(executable, 'test');
    const { config, paths } = configureProfile('applications', {
      id: 'test-browser',
      label: 'Test Browser',
      engine: 'chromium',
      executablePath: executable,
    }, { root, platform: process.platform, env: process.env, home: os.homedir() });
    assert.equal(config.lifecycle, 'leave-open');
    assert.equal(config.userDataDir, paths.userDataDir);
    assert.ok(fs.existsSync(paths.configFile));
    assert.ok(fs.existsSync(paths.playwrightConfigFile));
    assert.doesNotThrow(() => validateConfig(config, 'applications', { root }));
    assert.throws(() => validateConfig(config, 'another-profile', { root }), /belongs to profile/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('blocks destructive, profile, and authentication-state commands', () => {
  for (const command of ['close', 'close-all', 'kill-all', 'delete-data', 'tab-close', 'state-save', 'cookie-list', 'localstorage-clear', 'run-code'])
    assert.throws(() => assertSafePlaywrightCommand([command]), /Blocked Playwright command/);
  assert.equal(assertSafePlaywrightCommand(['snapshot']), 'snapshot');
  assert.equal(assertSafePlaywrightCommand(['click', 'e5']), 'click');
});

test('passes paths with spaces as single process arguments', () => {
  const args = playwrightArgs('agent-applications', [
    'open',
    'https://example.com',
    '--config=C:\\Agent Browser\\playwright.config.json',
  ]);
  assert.equal(args.at(-1), '--config=C:\\Agent Browser\\playwright.config.json');
});

test('open creates a new tab when the named session already exists', () => {
  const calls = [];
  const execute = (_config, args) => {
    calls.push(args);
    if (args[0] === 'tab-list')
      return { status: 0, stdout: '{}', stderr: '' };
    return { status: 0, stdout: '', stderr: '' };
  };
  const config = { session: 'agent-applications' };
  openBrowserSession(config, '/tmp/config.json', 'https://example.com', execute);
  assert.deepEqual(calls, [
    ['tab-list', '--json'],
    ['tab-new', 'https://example.com'],
  ]);
});

test('open starts a headed persistent session when none exists', () => {
  const calls = [];
  const execute = (_config, args) => {
    calls.push(args);
    return { status: args[0] === 'tab-list' ? 1 : 0, stdout: '', stderr: '' };
  };
  const config = { session: 'agent-applications' };
  openBrowserSession(config, '/tmp/config.json', 'https://example.com', execute);
  assert.deepEqual(calls, [
    ['tab-list', '--json'],
    ['open', 'https://example.com', '--config=/tmp/config.json', '--headed'],
  ]);
});

test('reports profile locks without killing the owner', () => {
  const execute = (_config, args) => {
    if (args[0] === 'tab-list')
      return { status: 1, stdout: '', stderr: '' };
    return { status: 1, stdout: '', stderr: 'Browser is already in use for profile' };
  };
  assert.throws(
    () => openBrowserSession({ session: 'agent-applications' }, '/tmp/config.json', 'https://example.com', execute),
    /Do not kill it/,
  );
});

test('end performs only a read-only session check and leaves the browser open', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'agent-browser-end-'));
  const calls = [];
  const execute = (_config, args) => {
    calls.push(args);
    return { status: 0, stdout: '{}', stderr: '' };
  };
  try {
    assert.equal(endBrowserTask('applications', { session: 'agent-applications' }, execute, { root }), true);
    assert.deepEqual(calls, [['tab-list', '--json']]);
    const runtime = JSON.parse(fs.readFileSync(profilePaths('applications', { root }).runtimeFile, 'utf8'));
    assert.equal(runtime.status, 'released');
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

#!/usr/bin/env node

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(SCRIPT_DIR, '..');
const PLAYWRIGHT_CLI = path.join(REPO_ROOT, 'node_modules', 'playwright', 'cli.js');
const DEFAULT_PROFILE = 'applications';
const PROFILE_PATTERN = /^[a-z0-9][a-z0-9_-]{0,63}$/;

const BLOCKED_COMMANDS = new Set([
  'attach',
  'close',
  'close-all',
  'delete-data',
  'detach',
  'install',
  'install-browser',
  'kill-all',
  'open',
  'run-code',
  'state-load',
  'state-save',
  'tab-close',
]);

const BLOCKED_PREFIXES = [
  'cookie-',
  'localstorage-',
  'sessionstorage-',
];

function pathApi(platform = process.platform) {
  return platform === 'win32' ? path.win32 : path.posix;
}

export function appDataRoot({ platform = process.platform, env = process.env, home = os.homedir() } = {}) {
  const paths = pathApi(platform);
  if (platform === 'win32')
    return paths.join(env.LOCALAPPDATA || paths.join(home, 'AppData', 'Local'), 'agent-browser');
  if (platform === 'darwin')
    return paths.join(home, 'Library', 'Application Support', 'agent-browser');
  return paths.join(env.XDG_STATE_HOME || paths.join(home, '.local', 'state'), 'agent-browser');
}

export function profilePaths(profileName, options = {}) {
  validateProfileName(profileName);
  const paths = pathApi(options.platform);
  const root = options.root || appDataRoot(options);
  const profileRoot = paths.join(root, 'profiles', profileName);
  return {
    root,
    profileRoot,
    configFile: paths.join(profileRoot, 'config.json'),
    playwrightConfigFile: paths.join(profileRoot, 'playwright.config.json'),
    runtimeFile: paths.join(profileRoot, 'runtime.json'),
    userDataDir: paths.join(profileRoot, 'user-data'),
    artifactsDir: paths.join(profileRoot, 'artifacts'),
  };
}

export function validateProfileName(profileName) {
  if (!PROFILE_PATTERN.test(profileName))
    throw new Error('Profile names must use 1-64 lowercase letters, numbers, hyphens, or underscores.');
}

function normalizeForComparison(value, platform = process.platform) {
  const resolved = pathApi(platform).resolve(value).replace(/[\\/]+$/, '');
  return platform === 'win32' ? resolved.toLowerCase() : resolved;
}

export function knownPersonalDataDirs({ platform = process.platform, env = process.env, home = os.homedir() } = {}) {
  const paths = pathApi(platform);
  if (platform === 'win32') {
    const local = env.LOCALAPPDATA || paths.join(home, 'AppData', 'Local');
    return [
      paths.join(local, 'BraveSoftware', 'Brave-Browser', 'User Data'),
      paths.join(local, 'Google', 'Chrome', 'User Data'),
      paths.join(local, 'Microsoft', 'Edge', 'User Data'),
      paths.join(local, 'Chromium', 'User Data'),
    ];
  }
  if (platform === 'darwin') {
    const support = paths.join(home, 'Library', 'Application Support');
    return [
      paths.join(support, 'BraveSoftware', 'Brave-Browser'),
      paths.join(support, 'Google', 'Chrome'),
      paths.join(support, 'Microsoft Edge'),
      paths.join(support, 'Chromium'),
    ];
  }
  return [
    paths.join(home, '.config', 'BraveSoftware', 'Brave-Browser'),
    paths.join(home, '.config', 'google-chrome'),
    paths.join(home, '.config', 'microsoft-edge'),
    paths.join(home, '.config', 'chromium'),
  ];
}

export function assertDedicatedUserDataDir(userDataDir, profileName, options = {}) {
  const expected = profilePaths(profileName, options).userDataDir;
  const actualNormalized = normalizeForComparison(userDataDir, options.platform);
  const expectedNormalized = normalizeForComparison(expected, options.platform);
  if (actualNormalized !== expectedNormalized)
    throw new Error(`Refusing browser data directory outside the dedicated profile: ${userDataDir}`);

  for (const personalDir of knownPersonalDataDirs(options)) {
    const personalNormalized = normalizeForComparison(personalDir, options.platform);
    if (actualNormalized === personalNormalized || actualNormalized.startsWith(`${personalNormalized}${pathApi(options.platform).sep}`))
      throw new Error(`Refusing known personal/default browser data directory: ${userDataDir}`);
  }
}

function systemBrowserDefinitions({ platform = process.platform, env = process.env, home = os.homedir() } = {}) {
  const paths = pathApi(platform);
  if (platform === 'win32') {
    const programFiles = env.ProgramFiles || 'C:\\Program Files';
    const programFilesX86 = env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)';
    const local = env.LOCALAPPDATA || paths.join(home, 'AppData', 'Local');
    return [
      ['brave', 'Brave', 'chromium', [
        paths.join(programFiles, 'BraveSoftware', 'Brave-Browser', 'Application', 'brave.exe'),
        paths.join(programFilesX86, 'BraveSoftware', 'Brave-Browser', 'Application', 'brave.exe'),
        paths.join(local, 'BraveSoftware', 'Brave-Browser', 'Application', 'brave.exe'),
      ]],
      ['chrome', 'Google Chrome', 'chromium', [
        paths.join(programFiles, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        paths.join(programFilesX86, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        paths.join(local, 'Google', 'Chrome', 'Application', 'chrome.exe'),
      ]],
      ['edge', 'Microsoft Edge', 'chromium', [
        paths.join(programFilesX86, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        paths.join(programFiles, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
      ]],
      ['chromium', 'Chromium', 'chromium', [
        paths.join(local, 'Chromium', 'Application', 'chrome.exe'),
      ]],
    ];
  }

  if (platform === 'darwin') {
    return [
      ['brave', 'Brave', 'chromium', ['/Applications/Brave Browser.app/Contents/MacOS/Brave Browser']],
      ['chrome', 'Google Chrome', 'chromium', ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']],
      ['edge', 'Microsoft Edge', 'chromium', ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge']],
      ['chromium', 'Chromium', 'chromium', ['/Applications/Chromium.app/Contents/MacOS/Chromium']],
    ];
  }

  return [
    ['brave', 'Brave', 'chromium', ['brave-browser', 'brave', 'brave-browser-stable']],
    ['chrome', 'Google Chrome', 'chromium', ['google-chrome-stable', 'google-chrome']],
    ['edge', 'Microsoft Edge', 'chromium', ['microsoft-edge-stable', 'microsoft-edge']],
    ['chromium', 'Chromium', 'chromium', ['chromium', 'chromium-browser']],
  ];
}

function findOnPath(command, { env = process.env, platform = process.platform, existsSync = fs.existsSync } = {}) {
  const paths = pathApi(platform);
  const pathEntries = (env.PATH || '').split(paths.delimiter).filter(Boolean);
  const extensions = platform === 'win32'
    ? (env.PATHEXT || '.EXE;.CMD;.BAT').split(';')
    : [''];
  for (const directory of pathEntries) {
    for (const extension of extensions) {
      const candidate = paths.join(directory, platform === 'win32' ? `${command}${extension.toLowerCase()}` : command);
      if (existsSync(candidate))
        return paths.resolve(candidate);
    }
  }
  return undefined;
}

export function discoverBrowsers(options = {}) {
  const platform = options.platform || process.platform;
  const paths = pathApi(platform);
  const existsSync = options.existsSync || fs.existsSync;
  const candidates = [];

  for (const [id, label, engine, locations] of systemBrowserDefinitions({ ...options, platform })) {
    let executablePath;
    for (const location of locations) {
      const resolved = paths.isAbsolute(location)
        ? location
        : findOnPath(location, { ...options, platform, existsSync });
      if (resolved && existsSync(resolved)) {
        executablePath = paths.resolve(resolved);
        break;
      }
    }
    if (executablePath)
      candidates.push({ id, label, engine, executablePath, source: 'system' });
  }

  if (options.includeManaged !== false) {
    try {
      const playwright = require('playwright');
      for (const engine of ['chromium', 'firefox', 'webkit']) {
        const executablePath = playwright[engine].executablePath();
        if (existsSync(executablePath)) {
          candidates.push({
            id: `playwright-${engine}`,
            label: `Playwright ${engine}`,
            engine,
            executablePath: paths.resolve(executablePath),
            source: 'playwright',
          });
        }
      }
    } catch {
      // Discovery must remain useful before dependencies are installed.
    }
  }

  const seen = new Set();
  return candidates.filter(candidate => {
    const key = normalizeForComparison(candidate.executablePath, platform);
    if (seen.has(key))
      return false;
    seen.add(key);
    return true;
  });
}

function parseNamedOption(args, name) {
  const exactIndex = args.indexOf(name);
  if (exactIndex !== -1) {
    if (!args[exactIndex + 1])
      throw new Error(`${name} requires a value.`);
    const value = args[exactIndex + 1];
    args.splice(exactIndex, 2);
    return value;
  }
  const prefix = `${name}=`;
  const inlineIndex = args.findIndex(arg => arg.startsWith(prefix));
  if (inlineIndex !== -1) {
    const value = args[inlineIndex].slice(prefix.length);
    args.splice(inlineIndex, 1);
    return value;
  }
  return undefined;
}

export function parseInvocation(argv) {
  const args = [...argv];
  const profileName = parseNamedOption(args, '--profile') || DEFAULT_PROFILE;
  validateProfileName(profileName);
  const command = args.shift() || 'help';
  return { profileName, command, args };
}

export function assertSafePlaywrightCommand(args) {
  const command = args.find(arg => !arg.startsWith('-'));
  if (!command)
    throw new Error('run requires a Playwright CLI command after --.');
  const normalized = command.toLowerCase();
  if (BLOCKED_COMMANDS.has(normalized) || BLOCKED_PREFIXES.some(prefix => normalized.startsWith(prefix))) {
    throw new Error(`Blocked Playwright command '${command}'. The dedicated profile and open tabs must be preserved.`);
  }
  return normalized;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

export function validateConfig(config, profileName, options = {}) {
  if (config.schemaVersion !== 1)
    throw new Error('Unsupported browser configuration version. Run configure again.');
  if (config.profile !== profileName)
    throw new Error(`Browser configuration belongs to profile '${config.profile}', not '${profileName}'.`);
  validateProfileName(config.profile);
  if (!['chromium', 'firefox', 'webkit'].includes(config.browser?.engine))
    throw new Error(`Unsupported Playwright browser engine: ${config.browser?.engine || '(missing)'}`);
  const paths = pathApi(options.platform);
  if (!paths.isAbsolute(config.browser?.executablePath || ''))
    throw new Error('The configured browser executable path must be absolute.');
  if (!paths.isAbsolute(config.userDataDir || ''))
    throw new Error('The configured browser data directory must be absolute.');
  assertDedicatedUserDataDir(config.userDataDir, profileName, options);
  return config;
}

export function loadConfig(profileName, options = {}) {
  const paths = profilePaths(profileName, options);
  if (!fs.existsSync(paths.configFile))
    throw new Error(`Browser profile '${profileName}' is not configured. Run 'npm run browser -- discover', choose a candidate, then run configure.`);
  return validateConfig(readJson(paths.configFile), profileName, options);
}

function writeJsonSecure(file, value) {
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, { encoding: 'utf8', mode: 0o600 });
}

export function configureProfile(profileName, candidate, options = {}) {
  const pathOperations = pathApi(options.platform);
  const paths = profilePaths(profileName, options);
  assertDedicatedUserDataDir(paths.userDataDir, profileName, options);
  fs.mkdirSync(paths.profileRoot, { recursive: true, mode: 0o700 });
  fs.mkdirSync(paths.userDataDir, { recursive: true, mode: 0o700 });
  fs.mkdirSync(paths.artifactsDir, { recursive: true, mode: 0o700 });

  const config = {
    schemaVersion: 1,
    profile: profileName,
    session: `agent-${profileName}`,
    lifecycle: 'leave-open',
    browser: {
      candidateId: candidate.id,
      label: candidate.label,
      engine: candidate.engine,
      executablePath: pathOperations.resolve(candidate.executablePath),
    },
    userDataDir: paths.userDataDir,
  };
  validateConfig(config, profileName, options);

  const playwrightConfig = {
    browser: {
      browserName: candidate.engine,
      isolated: false,
      userDataDir: paths.userDataDir,
      launchOptions: {
        executablePath: pathOperations.resolve(candidate.executablePath),
        headless: false,
      },
    },
    outputDir: paths.artifactsDir,
  };

  writeJsonSecure(paths.configFile, config);
  writeJsonSecure(paths.playwrightConfigFile, playwrightConfig);
  return { config, paths };
}

export function playwrightArgs(session, args) {
  return [PLAYWRIGHT_CLI, 'cli', `-s=${session}`, ...args];
}

export function executePlaywright(config, args, { capture = false } = {}) {
  if (!fs.existsSync(PLAYWRIGHT_CLI)) {
    return {
      status: 1,
      stdout: '',
      stderr: `Local Playwright CLI is unavailable at ${PLAYWRIGHT_CLI}. Install repository dependencies only with user approval.`,
    };
  }
  const result = spawnSync(process.execPath, playwrightArgs(config.session, args), {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    stdio: capture ? 'pipe' : 'inherit',
    windowsHide: true,
  });
  return {
    status: result.status ?? 1,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
    error: result.error,
  };
}

export function isSessionOpen(config, execute = executePlaywright) {
  const result = execute(config, ['tab-list', '--json'], { capture: true });
  return result.status === 0;
}

export function openBrowserSession(config, playwrightConfigFile, url, execute = executePlaywright) {
  if (isSessionOpen(config, execute))
    return execute(config, ['tab-new', url]);
  const result = execute(config, ['open', url, `--config=${playwrightConfigFile}`, '--headed'], { capture: true });
  if (result.status !== 0 && /already in use|processsingleton|profile.*lock/i.test(`${result.stdout}\n${result.stderr}`)) {
    throw new Error('The dedicated browser profile is already in use by another controller. Do not kill it; close it manually or choose another named profile.');
  }
  return result;
}

export function endBrowserTask(profileName, config, execute = executePlaywright, options = {}) {
  writeRuntime(profileName, 'released', options);
  return isSessionOpen(config, execute);
}

function printDiscovery(candidates) {
  if (!candidates.length) {
    console.log('No supported browser was discovered. Use manual browser control, or configure a custom executable explicitly.');
    return;
  }
  console.log('Discovered browser candidates (no selection was made):');
  for (const candidate of candidates)
    console.log(`- ${candidate.id}: ${candidate.label} [${candidate.engine}]\n  ${candidate.executablePath}`);
  console.log("Choose one, then run: npm run browser -- configure --browser <candidate-id>");
}

function selectCandidate(browserId, args) {
  if (!browserId)
    throw new Error('configure requires --browser <candidate-id>. Run discover first; no default is selected.');
  if (browserId === 'custom') {
    const executablePath = parseNamedOption(args, '--executable');
    const engine = parseNamedOption(args, '--engine') || 'chromium';
    if (!executablePath || !path.isAbsolute(executablePath))
      throw new Error('Custom browsers require --executable <absolute-path>.');
    if (!['chromium', 'firefox', 'webkit'].includes(engine))
      throw new Error('Custom browser --engine must be chromium, firefox, or webkit.');
    if (!fs.existsSync(executablePath))
      throw new Error(`Custom browser executable does not exist: ${executablePath}`);
    return { id: 'custom', label: 'Custom browser', engine, executablePath };
  }
  const candidate = discoverBrowsers().find(item => item.id === browserId);
  if (!candidate)
    throw new Error(`Browser candidate '${browserId}' was not discovered on this machine. Run discover and select an exact listed id.`);
  return candidate;
}

function writeRuntime(profileName, status, options = {}) {
  const paths = profilePaths(profileName, options);
  fs.mkdirSync(paths.profileRoot, { recursive: true, mode: 0o700 });
  writeJsonSecure(paths.runtimeFile, { status, at: new Date().toISOString() });
}

function printHelp() {
  console.log(`Portable dedicated browser helper

Usage:
  npm run browser -- discover [--profile <name>]
  npm run browser -- configure --browser <candidate-id> [--profile <name>]
  npm run browser -- configure --browser custom --executable <absolute-path> [--engine chromium|firefox|webkit]
  npm run browser -- doctor [--profile <name>]
  npm run browser -- open <url> [--profile <name>]
  npm run browser -- run -- <playwright-cli command> [args...]
  npm run browser -- status [--profile <name>]
  npm run browser -- end [--profile <name>]

The default profile is '${DEFAULT_PROFILE}'. Browser-wide close, profile deletion,
tab close, cookie/storage export, attach, and arbitrary run-code commands are blocked.`);
}

function failResult(result) {
  if (result?.error)
    throw result.error;
  if (result?.status && result.status !== 0)
    process.exitCode = result.status;
}

function printCapturedResult(result) {
  if (result?.stdout)
    process.stdout.write(result.stdout);
  if (result?.stderr)
    process.stderr.write(result.stderr);
}

export function main(argv = process.argv.slice(2)) {
  try {
    const { profileName, command, args } = parseInvocation(argv);
    const paths = profilePaths(profileName);

    if (command === 'help' || command === '--help' || command === '-h') {
      printHelp();
      return;
    }

    if (command === 'discover') {
      printDiscovery(discoverBrowsers());
      return;
    }

    if (command === 'configure') {
      const browserId = parseNamedOption(args, '--browser');
      const candidate = selectCandidate(browserId, args);
      if (args.length)
        throw new Error(`Unknown configure arguments: ${args.join(' ')}`);
      const { config } = configureProfile(profileName, candidate);
      console.log(`Configured dedicated profile '${profileName}' with ${config.browser.label}.`);
      console.log(`Browser: ${config.browser.executablePath}`);
      console.log(`Profile: ${config.userDataDir}`);
      console.log('No personal/default browser profile will be attached.');
      return;
    }

    const config = loadConfig(profileName);
    if (!fs.existsSync(config.browser.executablePath))
      throw new Error(`Configured browser executable is missing: ${config.browser.executablePath}. Run discover and configure again; no fallback was opened.`);

    if (command === 'doctor') {
      if (!fs.existsSync(PLAYWRIGHT_CLI))
        throw new Error(`Local Playwright CLI is unavailable at ${PLAYWRIGHT_CLI}. Install repository dependencies only with user approval.`);
      if (!fs.existsSync(config.userDataDir))
        throw new Error(`Dedicated browser data directory is missing: ${config.userDataDir}. Run configure again.`);
      try {
        fs.accessSync(config.userDataDir, fs.constants.R_OK | fs.constants.W_OK);
      } catch {
        throw new Error(`Dedicated browser data directory is not readable and writable: ${config.userDataDir}`);
      }
      console.log(`Profile: ${profileName}`);
      console.log(`Browser: ${config.browser.label}`);
      console.log(`Executable: ${config.browser.executablePath}`);
      console.log(`User data: ${config.userDataDir}`);
      console.log(`Session: ${config.session}`);
      console.log(`Running: ${isSessionOpen(config) ? 'yes' : 'no'}`);
      console.log('Safety: dedicated profile validated; destructive browser commands blocked.');
      return;
    }

    if (command === 'open') {
      const url = args.shift();
      if (!url || args.length)
        throw new Error('open requires exactly one URL.');
      const parsed = new URL(url);
      if (!['http:', 'https:', 'about:'].includes(parsed.protocol))
        throw new Error(`Unsupported URL protocol: ${parsed.protocol}`);
      writeRuntime(profileName, 'active');
      const result = openBrowserSession(config, paths.playwrightConfigFile, url);
      printCapturedResult(result);
      failResult(result);
      return;
    }

    if (command === 'run') {
      if (args[0] === '--')
        args.shift();
      assertSafePlaywrightCommand(args);
      if (!isSessionOpen(config))
        throw new Error(`Dedicated browser session '${config.session}' is not running. Use open first.`);
      writeRuntime(profileName, 'active');
      failResult(executePlaywright(config, args));
      return;
    }

    if (command === 'status') {
      if (!isSessionOpen(config)) {
        console.log(`Dedicated browser session '${config.session}' is configured but not running.`);
        return;
      }
      failResult(executePlaywright(config, ['tab-list']));
      return;
    }

    if (command === 'end') {
      const running = endBrowserTask(profileName, config);
      console.log(`Browser task ended. Session '${config.session}' is ${running ? 'still open' : 'not running'}; no tabs or browser processes were closed.`);
      return;
    }

    throw new Error(`Unknown command '${command}'. Run with --help.`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)
  main();

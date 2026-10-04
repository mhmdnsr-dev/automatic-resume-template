---
name: browser-session
description: >-
  Opens and controls authenticated websites through the repository's dedicated,
  persistent browser profile without touching the user's personal browser.
  Use for every task that requires an interactive browser, login state, page
  navigation, form entry, browser automation, or user takeover for authentication.
---

# Dedicated browser session

Use the repository helper for every browser task. It provides a headed,
persistent profile that is separate from the user's everyday browser windows.

## Start

1. Run `npm run browser -- doctor` (`npm.cmd` on Windows when PowerShell blocks
   `npm.ps1`).
2. If the profile is not configured, run `npm run browser -- discover`, show the
   exact candidates, and ask the user to choose one. Never choose or switch
   browsers silently.
3. After the user chooses, run
   `npm run browser -- configure --browser <candidate-id>`.
4. Open the task URL with `npm run browser -- open "<url>"`. An existing session
   receives a new tab; existing tabs are not navigated or closed.

Use `--profile <name>` on every helper call when the user requests a profile
other than the default `applications` profile.

## Control

Send Playwright CLI operations through the helper:

```bash
npm run browser -- run -- snapshot
npm run browser -- run -- click e5
npm run browser -- run -- fill e8 "text"
npm run browser -- run -- tab-new "https://example.com"
npm run browser -- status
```

Do not bypass the helper with a global Playwright command, an editor-integrated
browser, CDP attachment, a system-default browser launch, or OS process control.

## Authentication handoff

If login, reauthentication, 2FA, CAPTCHA, or a password prompt appears:

1. Stop browser interactions immediately.
2. Tell the user the visible dedicated browser is waiting for them.
3. Never read, request, type, log, export, or inspect credentials or cookies.
4. Resume only after the user confirms authentication is complete, then take a
   fresh snapshot.

## End and failures

- End with `npm run browser -- end`. This leaves the browser and every tab open.
- Never close tabs, close the browser, delete profile data, kill browser
  processes, or attach to the personal/default browser profile.
- A locked profile means another controller owns it. Report the conflict; never
  kill or force-unlock it. Use another named profile only with user direction.
- If the configured browser is unavailable, report it and run discovery again;
  never fall back to another browser silently.
- If the helper cannot automate the selected browser, provide a manual click
  path and paste-ready content. Use an integrated or personal browser only when
  the user explicitly requests that exception for the current task.


# Browser handoff for website apply loops

Run this once at the start of an Upwork, Mostaql, or employment-site apply
session.

## Browser contract

Follow [`../browser-session/SKILL.md`](../browser-session/SKILL.md). All browsing
must use the explicitly configured, dedicated persistent profile through the
repository helper:

```bash
npm run browser -- doctor
npm run browser -- open "<platform-url>"
npm run browser -- run -- snapshot
```

Use `npm.cmd` instead of `npm` on Windows when PowerShell blocks `npm.ps1`.

Never use an editor-integrated browser, attach to the user's personal/default
browser profile, launch the system-default browser, or switch browser products
unless the user explicitly requests that exception for the current task.

## Apply-loop behavior

- Browser state and existing website profiles are not candidate-fact sources.
  Personalized content comes only from the current
  `resume.tex` under
  [`../candidate-source.md`](../candidate-source.md).
- Inspect the URL and visible page after navigation or redirects.
- If login, reauthentication, 2FA, CAPTCHA, or a password prompt appears, stop
  interactions and let the user take over the visible dedicated window. Resume
  only after confirmation and a fresh snapshot.
- Never read, type, request, log, inspect, or export credentials or cookies.
- Keep every existing apply/submission approval gate.
- Finish with `npm run browser -- end`; leave the browser and all tabs open.

If the configured browser cannot be controlled, provide the click path and
paste-ready content for manual completion. Do not silently fall back.

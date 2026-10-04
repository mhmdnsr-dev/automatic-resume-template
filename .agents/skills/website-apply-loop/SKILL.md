---
name: website-apply-loop
description: >-
  Shared browser and writing rules for freelance-apply-loop and job-apply-loop:
  use the dedicated persistent browser profile, hand authentication to the user,
  and apply proposal writing-voice rules.
---

# Website apply loop (shared)

Shared setup for [freelance-apply-loop](../freelance-apply-loop/SKILL.md) and [job-apply-loop](../job-apply-loop/SKILL.md).

## Candidate source — read first

Read [`../candidate-source.md`](../candidate-source.md), then read `resume.tex` fresh before generating or submitting any candidate/profile content. The `.tex` is the only source of Example Candidate’s facts.

## Before a platform loop

1. Follow [browser.md](browser.md) and the canonical [`browser-session`](../browser-session/SKILL.md). Use only the explicitly configured dedicated persistent profile through the repository helper.
2. Run the main skill (`freelance-apply-loop` or `job-apply-loop`).
3. Write proposals/cover letters using [writing-voice.md](writing-voice.md) plus the platform’s guide when applicable.

## Hard rules (shared)

- Never apply without explicit OK for that job/project.
- Candidate facts must come only from the current `resume.tex`; ask for required fields absent from it.
- Never use an integrated browser, system-default browser, or personal/default browser profile unless the user explicitly requests that exception for the current task.
- On login, reauthentication, 2FA, or CAPTCHA, pause for user takeover in the visible dedicated window and resume only after confirmation.
- End through the helper without closing the dedicated browser or any tabs.

## Files

- [browser.md](browser.md) — apply-loop handoff rules for the dedicated browser
- [../browser-session/SKILL.md](../browser-session/SKILL.md) — universal browser contract and helper commands
- [writing-voice.md](writing-voice.md) — proposal voice rules
- [../candidate-source.md](../candidate-source.md) — sole source rule

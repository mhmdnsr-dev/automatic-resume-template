---
name: freelance-apply-loop
description: >-
  Gated freelance apply loop for Upwork and Mostaql (مستقل): pick platform,
  find fit job/project, ask Apply now?, on OK submit tailored proposal, on No
  skip, repeat until stop. Use for Upwork, Mostaql, مستقل, proposals, Find work,
  or Arabic freelance bidding.
---

# Freelance Apply Loop — Upwork & Mostaql

Portable Agent Skill. Human-gated loop: **pick platform → find fit → ask → apply or next → until stop**.

## When to start

User says any of: freelance apply loop, Upwork apply, Mostaql apply, مستقل, Find work, تصفح المشاريع, proposals, continue applying on Upwork/Mostaql.

## Source of truth — read first

Read [`../candidate-source.md`](../candidate-source.md), then read `resume.tex` fresh before every proposal or form action.

## Step 0 — Pick platform

| Signal                                               | Platform                     | Sub-guide            |
| ---------------------------------------------------- | ---------------------------- | -------------------- |
| Upwork, Find work, Connects, hourly/fixed client job | **Upwork**                   | [upwork/](upwork/)   |
| Mostaql, مستقل, مشروع, نص العرض, تصفح المشاريع       | **Mostaql**                  | [mostaql/](mostaql/) |
| Ambiguous                                            | Ask once: Upwork or Mostaql? |

User may lock one platform for the session (“Upwork only” / “Mostaql only”).

## Browser start

Follow [`../browser-session/SKILL.md`](../browser-session/SKILL.md) and
[`../website-apply-loop/browser.md`](../website-apply-loop/browser.md). Use the
configured dedicated persistent profile through the repository helper.

**Upwork:**

```bash
npm run browser -- open "https://www.upwork.com/nx/find-work/"
```

**Mostaql:**

```bash
npm run browser -- open "https://mostaql.com/projects"
```

If authentication is required, pause for user takeover in the visible dedicated
window. Never attach to or close the user's personal browser. If helper control
is unavailable, provide manual steps rather than silently switching browsers.

## Shared hard rules

- **Never apply without explicit OK** for that job/project.
- **Upwork OK words:** `OK`, `Apply`, `yes`, `go`
- **Mostaql OK words:** `OK`, `Apply`, `yes`, `قدم`, `موافق`
- **Never invent** experience, tools, years, metrics, or clients.
- Ask for rate, budget, availability, or language level when required and absent from the `.tex`.
- On **No** / `skip` / `next` / `التالي`: do not apply; find next fit.
- On **stop** / `enough` / `توقف` / `pause`: summarize and exit.
- Connects / balance / membership / captcha / login blocks submit → report blocker; do not fake-submit.
- Session log: Applied / Skipped / Blocked.

## Loop (repeat until stop)

```
- [ ] Open browser → platform feed
- [ ] Find next Must/Strong fit (platform fit-criteria.md)
- [ ] Present Job/Project Card
- [ ] Ask: Apply now?
- [ ] OK → platform Apply Pipeline → next fit
- [ ] No → skipped → next fit
- [ ] stop → summary
```

## Step A — Find next fit

Follow the active platform guide:

- Upwork: [upwork/fit-criteria.md](upwork/fit-criteria.md) — Find work / Best Matches
- Mostaql: [mostaql/fit-criteria.md](mostaql/fit-criteria.md) — مشاريع برمجة / frontend keywords

Skip weak mismatches silently until Must/Strong (or Stretch with risk called out).

## Step B — Mandatory gate

Present a **Job Card** (Upwork) or **Project Card** (Mostaql), then ask exactly:

**Apply now?**

Wait. Do not open Apply / قدم عرضك until the user answers.

## Step C — Apply Pipeline (only after OK)

**Upwork:** open job → Apply now → form options per [upwork/proposal-guide.md](upwork/proposal-guide.md) → submit → confirm sent.

**Mostaql:** open project → قدم عرضك → bid + **Arabic** نص العرض per [mostaql/proposal-guide.md](mostaql/proposal-guide.md) → submit → confirm under عروضي.

Optional: run [jd-fit-resume](../jd-fit-resume/SKILL.md) if the user wants a tailored CV for a specific freelance brief (unusual; default is proposal-only). Generate PDF by default or DOCX only when explicitly requested.

## Session summary

```markdown
## Freelance session — [Upwork | Mostaql]

- **Applied:** N — [titles]
- **Skipped:** N — [titles]
- **Blocked:** N — [reason]
- **Next:** …
```

## Resources

- [upwork/fit-criteria.md](upwork/fit-criteria.md) · [upwork/proposal-guide.md](upwork/proposal-guide.md)
- [mostaql/fit-criteria.md](mostaql/fit-criteria.md) · [mostaql/proposal-guide.md](mostaql/proposal-guide.md)
- [../browser-session/SKILL.md](../browser-session/SKILL.md)
- [../website-apply-loop/browser.md](../website-apply-loop/browser.md) · [../website-apply-loop/writing-voice.md](../website-apply-loop/writing-voice.md)
- [../candidate-source.md](../candidate-source.md)

## Legacy entry points

[upwork-apply-loop](../upwork-apply-loop/SKILL.md) and [mostaql-apply-loop](../mostaql-apply-loop/SKILL.md) redirect here.

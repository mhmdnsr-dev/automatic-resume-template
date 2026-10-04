---
name: job-apply-loop
description: >-
  Runs a CV-only, human-gated job search and application loop across LinkedIn,
  referrals, Indeed Egypt, Wuzzuf, Bayt, GulfTalent, Naukrigulf, JobHunt, and
  reputable Egypt/MENA recruitment sites. Fits accessible profiles, hands
  authentication to the user, asks Apply now? before every submission, and
  after one successful application asks whether to stay on the same site or
  move to another. Use for jobs on those sources, Egypt or Arab-world job
  searches, employee referrals, profile fitting, and repeated applications.
---

# Job Apply Loop — Egypt and MENA

Portable Agent Skill (Codex, Claude Code, OpenCode, Cursor, and AGENTS.md-compatible agents).

Human-gated loop: **open site → user authentication handoff when needed → fit profile/search → show Job Card → ask → apply → choose site**.

## Source of truth — read first

Read [`../candidate-source.md`](../candidate-source.md), then read `resume.tex` fresh. The `.tex` is the **only** source for Example Candidate’s personal and professional facts. Never reuse facts merely because they appear on an existing site or in chat history.

If a required field is absent from the CV (salary, notice period, availability, work authorization, relocation, language level, demographics, etc.), ask the user; never guess.

## Sources and sites

Follow [sites.md](sites.md). Start with:

1. Referrals (always-on sourcing channel; outreach requires separate approval)
2. LinkedIn Jobs
3. Wuzzuf
4. Indeed Egypt
5. Workable
6. Bayt
7. GulfTalent
8. Naukrigulf
9. JobHunt (discovery/aggregator only; never use auto-apply)
10. Akhtaboot
11. Tanqeeb (discovery/aggregator; redirected destination becomes the active site)
12. Forasna only when a matching professional frontend role exists

## Browser start

Follow [`../browser-session/SKILL.md`](../browser-session/SKILL.md) and
[`../website-apply-loop/browser.md`](../website-apply-loop/browser.md). Use the
configured dedicated persistent profile through the repository helper:

```bash
npm run browser -- open "https://wuzzuf.net/explore"
npm run browser -- open "https://eg.indeed.com/?r=us"
npm run browser -- open "https://www.linkedin.com/jobs/"
```

## Login-page rotation rule

Immediately after opening a site—and again after every redirect—inspect the visible page and URL.

If a **login / sign-in / create-account page appears**, then:

1. Stop browser interactions immediately.
2. Ask the user to authenticate in the visible dedicated browser; never enter,
   inspect, or export credentials or cookies.
3. Resume only after the user confirms completion, then take a fresh snapshot.
4. If the user declines or authentication cannot be completed, log
   `Blocked — Login required` and move to the next site without closing tabs.

A company ATS reached through a job-board redirect counts as a new site. Apply the same login-page rule there.

Only revisit a login-blocked site if the user later confirms authentication is
complete and asks to retry.

## Mode A — Fit an accessible profile

When the user asks to fit/update a profile:

1. Open the profile area. If login appears, apply the rotation rule.
2. Read [profile-guide.md](profile-guide.md) and the `.tex` again.
3. Compare every visible field with CV truth; update only CV-supported fields.
4. Preserve required unknown fields and ask the user if they must change.
5. Never copy unsupported claims from another site.
6. Save, then re-open/snapshot the profile and confirm the visible result.
7. Continue to the next requested site.

## Mode B — Apply loop

### Step A — Find a fit

1. Open the next non-blocked site.
2. Search using [fit-criteria.md](fit-criteria.md).
3. Skip weak, stale, duplicate, or misleading roles silently.
4. Read the full JD: title, company, location/remote policy, employment type, seniority/years, stack, responsibilities, date, application route, and salary if shown.
5. If the posting truncates with **… more** / **Show more** / similar, **click it** and re-read before scoring. Never score from a truncated snippet alone when expansion is available.
6. Score Must / Strong / Stretch / Skip against the current `.tex`.

### Step B — Mandatory gate

Present:

```markdown
### Job N — [title] at [company]

- **Site:** …
- **Fit:** Must | Strong | Stretch — …
- **Location / mode:** …
- **Employment:** …
- **CV matches:** …
- **Risk / missing requirements:** …
- **Application route:** Easy Apply | site form | company ATS
- **URL:** …
```

Ask exactly:

**Apply now?**

Wait. Do not start or submit an application before explicit `OK` / `Apply` / `yes` / `قدم` / `موافق` for that job.

### Step C — Apply after OK

1. Re-read the `.tex` and [application-guide.md](application-guide.md). Ensure the JD is fully expanded (click **… more** if still truncated).
2. Run **[jd-fit-resume](../jd-fit-resume/SKILL.md)** for this job (URL + full JD text) → local folder with tailored PDF and `cover-letter.txt`. PDF is the application default; generate DOCX only when the user or destination explicitly requires it.
3. Open the application route. If it redirects to login, use the login-page rotation rule and mark the job Blocked.
4. Fill CV-supported fields only. Ask once for any required unknown field.
5. Upload the tailored PDF from the job folder. Use the tailored DOCX only when the form requires Word or the user explicitly requests it; use a master output only if the user explicitly says so.
6. Use the folder `cover-letter.txt` when the form asks for one, or when it materially helps; voice: [writing-voice.md](../website-apply-loop/writing-voice.md).
7. Stop on captcha, payment, legal consent ambiguity, or destructive/unexpected action and report it.
8. Review the final form, submit, and verify a success confirmation/application record.
9. Log Applied.

### Step D — Required site-choice gate

After **one successful submission on a site**, ask exactly:

**Do we continue with the same site or move to another?**

Wait for the answer:

| User answer                  | Action                                |
| ---------------------------- | ------------------------------------- |
| same / continue / نفس الموقع | Find the next fit on the current site |
| another / move / موقع آخر    | Rotate to the next non-blocked site   |
| stop / enough / توقف         | End and summarize                     |

Do not make a second submission on that site before this answer.

## Hard rules

- CV-only candidate facts; `.tex` always wins.
- Never apply without the per-job **Apply now?** approval.
- Never contact a person for a referral without showing the recipient, channel,
  and draft first and receiving explicit approval for that outreach.
- Never enable JobHunt Smart Apply, auto-apply, or any equivalent bulk submission
  feature; use JobHunt only to discover roles, then follow the normal job gate.
- After one successful application, always ask the site-choice question.
- Login pages require user takeover; unresolved authentication blocks that site.
- Never mass-apply, spam identical letters, evade anti-bot controls, or misrepresent experience.
- Keep a session log: Profile Updated / Applied / Skipped / Blocked (including Login required).

## Session summary

```markdown
## Job-application session

- **Profiles updated:** N — …
- **Applied:** N — [role — company — site]
- **Skipped:** N — …
- **Blocked:** N — [site/job — reason]
- **Next site:** …
```

## Resources

- [sites.md](sites.md)
- [fit-criteria.md](fit-criteria.md)
- [profile-guide.md](profile-guide.md)
- [application-guide.md](application-guide.md)
- [../candidate-source.md](../candidate-source.md)
- [../browser-session/SKILL.md](../browser-session/SKILL.md)
- [../website-apply-loop/browser.md](../website-apply-loop/browser.md)
- [../website-apply-loop/writing-voice.md](../website-apply-loop/writing-voice.md)
- [../jd-fit-resume/SKILL.md](../jd-fit-resume/SKILL.md)

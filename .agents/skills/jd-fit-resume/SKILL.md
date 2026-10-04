---
name: jd-fit-resume
description: >-
  Builds a local JD-tailored CV package from a job URL or pasted description:
  jd.txt, cover-letter.txt, resume.tex, and a PDF by default;
  can also produce DOCX when explicitly requested in yyyy-mm-dd_company-role/.
  No application submit. Use when the user pastes
  a JD link, asks to tailor a CV for a role, or job-apply-loop reaches Apply OK.
---

# JD fit resume — local package only

Portable Agent Skill. **Package factory only** — no job-board submit.

## When to start

User says any of: tailor CV for this JD, jd-fit-resume, paste job link, create job folder, fit resume to this posting.

Also invoked by [job-apply-loop](../job-apply-loop/SKILL.md) Step C after **Apply now?** approval.

## Source of truth — read first

Read [`../candidate-source.md`](../candidate-source.md), then read `resume.tex` fresh. Never invent facts.

## Output (local only, gitignored)

```
./yyyy-mm-dd_company-role/
  jd.txt
  cover-letter.txt
  resume.tex   # tailored copy of master
  resume.pdf   # compiled from copy
  resume.docx  # optional; only when requested
```

**Folder naming:** `yyyy-mm-dd_company-role` — lowercase, dashes, date = today unless user specifies.

## Pipeline

1. **Resolve JD**
   - URL provided → try [`scrape_page.py`](../../../scrape_page.py) for public pages:
     ```powershell
     python scrape_page.py "https://..." -o yyyy-mm-dd_company-role/jd.txt
     ```
   - Login wall / empty scrape → ask user to paste JD text into `jd.txt` (include URL at top).
   - Pasted text only → write `jd.txt` with any URL the user gave.
2. **Derive folder name** from company + role in the JD.
3. **Create folder** under the current workspace root.
4. **Copy master** → `yyyy-mm-dd_company-role/resume.tex` (never edit master).
5. **Moderate tailor** the copy — [tailoring.md](tailoring.md).
6. **Write** `cover-letter.txt` — [cover-letter.md](cover-letter.md); voice: [../website-apply-loop/writing-voice.md](../website-apply-loop/writing-voice.md).
7. **Compile PDF by default:** `python compile_cv.py yyyy-mm-dd_company-role`. If the user or destination requests Word, use `python compile_cv.py yyyy-mm-dd_company-role --format docx`. Run both commands only when both formats are requested.
8. **Verify** every requested output is single page; if spill, tighten `\sectiongap` only in that copy and regenerate.
9. **Return** folder path + short change note (summary, skills reordered, bullets tuned).

## Hard rules

- Never overwrite the master `.tex`.
- Never commit or push job folders.
- Never exceed one page in any requested tailored CV output.
- Never invent experience, tools, years, or metrics.
- Ask for salary, availability, notice period, or authorization only if the user is applying and the form requires it — not for package-only runs.

## Resources

- [tailoring.md](tailoring.md) — Moderate CV edit rules
- [cover-letter.md](cover-letter.md) — cover letter structure
- [../candidate-source.md](../candidate-source.md)
- [`WORKFLOW.md`](../../../WORKFLOW.md) — human-readable overview

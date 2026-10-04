# JD-Tailored CV Workflow

## Structural vs local-only

**Tracked (on remote):** `resume.tex`, `compile_cv.py`, `helpers/compile_cv_docx.py`, `requirements.txt`, `scrape_page.py`, `WORKFLOW.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/skills/`, `.gitignore` (plus thin vendor adapters or slash launchers under `.cursor/`, `.claude/`, `.gemini/`, and `.opencode/` if present).

**Local only (gitignored — do not commit or push):** dated job folders `yyyy-mm-dd_company-role/`, root generated outputs such as `resume.pdf` and `resume.docx`, LaTeX auxiliaries, scrape/playwright temps.

## Master (immutable)

- **Source of truth:** `resume.tex` (this folder root)
- **All skills:** Read [`.agents/skills/candidate-source.md`](.agents/skills/candidate-source.md) and the current master `.tex`; existing profiles and chat memory are not candidate-fact sources.
- **Master outputs:** `resume.pdf` and `resume.docx` are generated locally from the master `.tex`; commit them only if you intentionally want to publish your resume.
- Do **not** overwrite the master when tailoring for a job.
- Always **copy** the master into the job folder, then edit only the copy.

## Per-job folder (local only)

```
<repository-root>/yyyy-mm-dd_company-role/
  resume.tex   # tailored copy
  resume.pdf   # compiled from that .tex
  resume.docx  # optional; generated only when requested
  jd.txt                      # pasted job description (+ LinkedIn URL)
  cover-letter.txt            # tailored cover letter for this JD
```

**Folder naming:** `yyyy-mm-dd_company-role`  
- Lowercase, dash-separated  
- Date = application / task date (default: today)  
- Example: `2026-07-19_insense-frontend-developer`

Job packages remain on this machine only (see `.gitignore`). Never `git add` them.

## Tailoring depth: Moderate

See [`.agents/skills/jd-fit-resume/tailoring.md`](.agents/skills/jd-fit-resume/tailoring.md) for agent rules. Summary:

1. Rewrite **Professional Summary** toward the JD (factual).
2. Reorder **Technical Skills** for ATS keywords already true in the master.
3. Retune **2–4 Experience bullets** toward JD language; keep metrics.
4. Light **Projects** tweaks if relevant.
5. Update PDF metadata (`\hypersetup`); the DOCX backend derives Word metadata from the same tailored source.
6. Write **`cover-letter.txt`** — [cover-letter.md](.agents/skills/jd-fit-resume/cover-letter.md).
7. Stay on **one page** (CV).

## Scrape JD from a public URL

Use [`scrape_page.py`](scrape_page.py) + `playwright-cli` for **public pages that do not require login**:

```powershell
python scrape_page.py "https://example.com/job/..." -o yyyy-mm-dd_company-role/jd.txt
python scrape_page.py "https://..." --stdout
```

- Requires `playwright-cli` on PATH (`npm install -g @playwright/cli@latest`)
- Writes `URL` / `Title` / body text suitable for `jd.txt`
- If the page is empty or looks like a login wall, the script exits with an error — **paste the JD into `jd.txt` manually**

Authenticated / paywalled pages (many LinkedIn views) are **out of scope** for v1.

## Hard rules

- Never exceed one page in the requested CV output.
- Never invent experience, tools, or metrics
- Never edit the master unless explicitly asked to update the standard
- Never commit or push dated job packages (local only)

## Checklist (each JD)

1. Derive folder name: `yyyy-mm-dd_company-role`
2. Create the folder under the current repository root
3. Copy master → job folder `resume.tex`
4. Save JD as `jd.txt` (include LinkedIn URL when available)
   - Prefer: `python scrape_page.py "<url>" -o yyyy-mm-dd_company-role/jd.txt`
   - Fallback: paste manually if scrape fails (auth / empty)
5. Apply Moderate edits to the `.tex` copy
6. Write `cover-letter.txt` for this JD
7. Compile PDF by default (needs MiKTeX or TeX Live):
   ```
   python compile_cv.py yyyy-mm-dd_company-role
   ```
   `compile_cv.py` calls the `pdflatex` executable directly. It uses `pdflatex` from `PATH` on Windows or Linux and can also find a standard per-user MiKTeX installation on Windows.
   When the user or destination explicitly requires Word, install `requirements.txt` and compile DOCX instead:
   ```
   python compile_cv.py yyyy-mm-dd_company-role --format docx
   ```
   To deliver both, run both commands; each output must come from the same tailored `.tex`.
8. Confirm every requested CV output is single page; if spill, tighten `\sectiongap` only in that copy and regenerate.
9. Return folder path + short change note (requested CV output(s) + cover letter).

---

## Upwork apply loop (repeated)

**Canonical (any agent):** [`.agents/skills/upwork-apply-loop/SKILL.md`](.agents/skills/upwork-apply-loop/SKILL.md)  
Project rules: [`AGENTS.md`](AGENTS.md) · Fit: [`fit-criteria.md`](.agents/skills/upwork-apply-loop/fit-criteria.md) · Proposals: [`proposal-guide.md`](.agents/skills/upwork-apply-loop/proposal-guide.md)
**Shared:** [browser-session](.agents/skills/browser-session/) — explicitly configured dedicated persistent profile, user authentication handoff, leave browser open · [website-apply-loop](.agents/skills/website-apply-loop/) · [writing-voice.md](.agents/skills/website-apply-loop/writing-voice.md)

Works with Codex, Claude Code, OpenCode, Gemini CLI, Cursor, etc. Vendor folders and command files (`.cursor/skills`, `.claude/skills`, `.gemini/commands`, `.opencode/commands`) are thin pointers/launchers only — edit the canonical skill under `.agents/skills/`.

### Goal

Find fit Upwork jobs one at a time, ask before applying, apply with a tailored proposal when approved, otherwise skip — until you say stop.

### Human gate (required)

```
Find fit job → show Job Card → ask "Apply now?"
  ├─ OK / Apply / yes  → fill proposal + form options → submit → next fit
  ├─ No / skip / next  → do not apply → next fit
  └─ stop / enough     → session summary → exit
```

**Never apply without an explicit OK for that job.**

### Agent checklist (each candidate)

1. Open Upwork **Find work** (logged-in browser / automation if available)
2. Select next Must/Strong fit (skip weak mismatches per fit-criteria)
3. Present Job Card (title, fit, budget, skills, client signals, risk, URL)
4. Ask: **Apply now?**
5. Wait for reply
6. On **OK**: Apply pipeline — rate/options from JD plus user-confirmed values (ask when absent from the CV), proposal from current `.tex` facts only, honest screening answers, submit if Connects allow
7. On **No**: log skipped → next candidate
8. On **stop**: report Applied / Skipped / Blocked counts and titles

### Hard rules (Upwork)

- Same truthfulness rules as CV tailoring — no invented stack or metrics
- If Connects = 0 or paywall blocks submit: stop and ask (do not fake-send)
- Use only strengths demonstrated in the current `.tex`; do not import assessment/profile labels
- Session log stays in chat unless you ask to save a local note

### How to start (any agent)

Say e.g. **“Start Upwork apply loop”** or **“Find Upwork jobs and ask before apply”**.

Agent-specific shortcuts:

| Agent | Shortcut |
|-------|----------|
| Codex | `$freelance-apply-loop Upwork` |
| Claude Code | `/freelance-apply-loop Upwork` or `/upwork-apply-loop` |
| OpenCode | `/apply-upwork` |
| Gemini CLI | `/apply-upwork` |

---

## Mostaql apply loop (مستقل — repeated)

**Canonical (any agent):** [`.agents/skills/mostaql-apply-loop/SKILL.md`](.agents/skills/mostaql-apply-loop/SKILL.md)  
Fit: [`fit-criteria.md`](.agents/skills/mostaql-apply-loop/fit-criteria.md) · Proposals: [`proposal-guide.md`](.agents/skills/mostaql-apply-loop/proposal-guide.md)
**Shared:** [browser-session](.agents/skills/browser-session/) — explicitly configured dedicated persistent profile, user authentication handoff, leave browser open · [website-apply-loop](.agents/skills/website-apply-loop/) · writing-voice

Same gate pattern as Upwork; proposals default to **Arabic**.

```
Find fit project → Project Card → ask "Apply now?"
  ├─ OK / قدم / موافق → نص العرض + bid options → submit → next
  ├─ No / التالي       → skip → next
  └─ stop / توقف       → session summary → exit
```

**Never submit without explicit OK.** Prefer **مشاريع برمجة** / frontend keywords. Candidate facts and positioning come only from the current `.tex`.

### How to start

Say e.g. **“Start Mostaql apply loop”** or **“ابدأ حلقة تقديم عروض مستقل”**.

Agent-specific shortcuts:

| Agent | Shortcut |
|-------|----------|
| Codex | `$freelance-apply-loop Mostaql` |
| Claude Code | `/freelance-apply-loop Mostaql` or `/mostaql-apply-loop` |
| OpenCode | `/apply-mostaql` |
| Gemini CLI | `/apply-mostaql` |

---

## Employment-site apply loop (LinkedIn / Indeed Egypt / Wuzzuf / MENA)

**Canonical:** [`.agents/skills/job-apply-loop/SKILL.md`](.agents/skills/job-apply-loop/SKILL.md)  
Sites: [`sites.md`](.agents/skills/job-apply-loop/sites.md) · Fit: [`fit-criteria.md`](.agents/skills/job-apply-loop/fit-criteria.md) · Profiles: [`profile-guide.md`](.agents/skills/job-apply-loop/profile-guide.md)

```
Open site through the configured dedicated persistent browser helper
  ├─ login page → pause for user takeover → unresolved: Blocked → next site
  └─ accessible → fit profile / find fit job
                    └─ expand “… more” if truncated → Job Card → ask "Apply now?"
                         ├─ OK / Apply → WORKFLOW tailored package (folder + jd.txt + .tex + cover-letter + PDF default)
                         │                → use DOCX only if explicitly required → submit once → ask same site or another?
                         ├─ No / skip → next fit
                         └─ stop → summary
```

Candidate facts come only from the current `resume.tex`. Ask for required fields absent from it; never copy stale profile claims. On **Apply**, always build a local JD-tailored CV package (this checklist) before upload — never overwrite the master.

Agent-specific shortcuts:

| Agent | JD package | Employment apply loop |
|-------|------------|-----------------------|
| Codex | `$jd-fit-resume` | `$job-apply-loop` |
| Claude Code | `/jd-fit-resume` | `/job-apply-loop` |
| OpenCode | `/tailor-cv` | `/apply-jobs` |
| Gemini CLI | `/tailor-cv` | `/apply-jobs` |

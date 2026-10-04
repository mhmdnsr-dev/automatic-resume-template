# Automatic Resume Template

An agent-friendly resume workspace for tailoring a canonical LaTeX resume to job descriptions, then generating PDF or DOCX outputs from the same source.

The repository includes:

- `resume.tex`: sample one-page resume source with placeholder candidate data.
- `compile_cv.py`: PDF/DOCX build entry point.
- `.agents/skills/`: portable agent workflows for JD tailoring, job applications, freelance proposals, and browser handoff.
- `WORKFLOW.md`: human-readable checklist for per-job tailoring.
- Vendor adapters for Codex, Claude, Cursor, Gemini CLI, and OpenCode.

This public template intentionally avoids real candidate data, generated personal resumes, application history, browser state, credentials, and dated job packages.

## Quick Start

Install dependencies once:

```bash
npm install
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Compile the sample resume:

```bash
.venv/bin/python compile_cv.py
.venv/bin/python compile_cv.py --format docx
```

On Windows, use:

```powershell
npm install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe compile_cv.py
```

PDF output requires MiKTeX or TeX Live. DOCX output uses `python-docx`.

## Customize

1. Replace the placeholder details in `resume.tex`.
2. Update `.agents/skills/candidate-source.md` if your fact-source rules differ.
3. Keep one canonical resume source in the repository root.
4. Generate outputs from the selected `.tex`; do not maintain a separate Word-only source.

The default source name is `resume.tex`. You can also pass a specific file or a job package directory:

```bash
python compile_cv.py path/to/custom-resume.tex
python compile_cv.py 2026-10-04_example-company-frontend
python compile_cv.py 2026-10-04_example-company-frontend --format docx
```

## Per-Job Packages

Tailored job packages are local-only and ignored by Git:

```text
yyyy-mm-dd_company-role/
  resume.tex          # tailored copy of the root resume
  resume.pdf          # generated PDF
  resume.docx         # optional generated Word output
  jd.txt              # pasted job description
  cover-letter.txt    # tailored cover letter
```

Suggested tailoring depth:

1. Rewrite the professional summary toward the JD.
2. Reorder technical skills for ATS keywords.
3. Retune a few experience bullets without inventing facts.
4. Adjust project emphasis if relevant.
5. Update PDF metadata.
6. Keep the resume to one page.

## Agent Workflows

Canonical skill instructions live under `.agents/skills/`. Agent-specific folders are pointers or launchers only.

| Agent | Start a workflow |
| --- | --- |
| Codex | `/skills`, `$jd-fit-resume`, `$job-apply-loop`, `$freelance-apply-loop` |
| Claude Code | `/jd-fit-resume`, `/job-apply-loop`, `/freelance-apply-loop` |
| OpenCode | Native `.agents/skills` discovery, plus `/tailor-cv`, `/apply-jobs`, `/apply-upwork`, `/apply-mostaql` |
| Gemini CLI | `GEMINI.md` context, plus `/tailor-cv`, `/apply-jobs`, `/apply-upwork`, `/apply-mostaql` |
| Cursor / other agents | Read `AGENTS.md`, then load the relevant `.agents/skills/*/SKILL.md` |

Hard rules baked into the workflows:

- Candidate facts come only from the current `resume.tex`.
- Missing application fields must be asked, not guessed.
- Job packages are copied into dated folders; the root resume is not overwritten during tailoring.
- No job, Upwork, Mostaql, or employment-site application is submitted without explicit approval for that item.
- Browser automation uses a dedicated persistent browser profile, never your personal/default browser profile.

## Browser Helper

Interactive and authenticated browser work uses the repository helper:

```bash
npm run browser -- discover
npm run browser -- configure --browser <candidate-id>
npm run browser -- open "https://www.linkedin.com/jobs/"
npm run browser -- end
```

The `end` command leaves the dedicated browser and tabs open. Login, 2FA, CAPTCHA, and password prompts are handed to the user.

## Public Safety Notes

Before publishing your own fork:

- Replace all placeholder resume facts with your own deliberate public-safe data.
- Keep generated PDFs/DOCX files out of public commits unless you intend to publish them.
- Keep dated job packages ignored.
- Never commit browser state, cookies, credentials, scraped private pages, or application logs.
- If your private repo ever contained sensitive files, publish a clean-history repository instead of flipping visibility.

## Tests

Run the browser helper tests:

```bash
npm test
```

Run the Python tests:

```bash
python -m unittest discover tests
```

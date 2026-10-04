# Agent instructions (any coding agent)

This repo is agent-agnostic. **Canonical** skills and rules live here — not under a single vendor folder.

| Path | Role |
|------|------|
| [`AGENTS.md`](AGENTS.md) | Project rules for Codex, OpenCode, Cursor, Copilot, etc. |
| [`CLAUDE.md`](CLAUDE.md) | Thin pointer for Claude Code → same rules |
| [`GEMINI.md`](GEMINI.md) | Thin pointer for Gemini CLI → same rules |
| [`.agents/skills/`](.agents/skills/) | Portable Agent Skills (`SKILL.md` standard) |
| [`WORKFLOW.md`](WORKFLOW.md) | Human + agent CV and application-loop checklists |

Vendor adapters (optional mirrors that point at `.agents/skills/`):

- `.cursor/skills/` — Cursor
- `.claude/skills/` — Claude Code
- `.gemini/commands/` — Gemini CLI slash launchers
- `.opencode/commands/` — OpenCode slash launchers

OpenCode reads `.agents/skills/` directly. Codex reads the same canonical
skills through its skill discovery (`/skills` or `$skill-name`). Gemini and
OpenCode command files are launchers only; they must not contain the workflow
truth.

**Edit skills only under `.agents/skills/`.** Keep adapters as pointers.

## Agent invocation

| Agent | Preferred invocation |
|-------|----------------------|
| Codex | `/skills`, `$jd-fit-resume`, `$job-apply-loop`, `$freelance-apply-loop` |
| Claude Code | `/jd-fit-resume`, `/job-apply-loop`, `/freelance-apply-loop` |
| OpenCode | Native `.agents/skills` discovery, plus `/tailor-cv`, `/apply-jobs`, `/apply-upwork`, `/apply-mostaql` |
| Gemini CLI | `GEMINI.md` context, plus `/tailor-cv`, `/apply-jobs`, `/apply-upwork`, `/apply-mostaql` |
| Cursor / other agents | Read `AGENTS.md`, then load the canonical skill under `.agents/skills/` |

## Main skills (3)

### 1. job-apply-loop

Path: [`.agents/skills/job-apply-loop/SKILL.md`](.agents/skills/job-apply-loop/SKILL.md)

Employment sites (LinkedIn, Indeed Egypt, Wuzzuf, MENA): skip login walls; ask **Apply now?** per job; on OK run **jd-fit-resume** then submit; after one success ask same site or rotate.

### 2. freelance-apply-loop

Path: [`.agents/skills/freelance-apply-loop/SKILL.md`](.agents/skills/freelance-apply-loop/SKILL.md)

Upwork + Mostaql (مستقل): pick platform → find fit → ask **Apply now?** → tailored proposal → next until **stop**. Platform subs: [`upwork/`](.agents/skills/freelance-apply-loop/upwork/), [`mostaql/`](.agents/skills/freelance-apply-loop/mostaql/).

Legacy triggers `upwork-apply-loop` / `mostaql-apply-loop` redirect here.

### 3. jd-fit-resume

Path: [`.agents/skills/jd-fit-resume/SKILL.md`](.agents/skills/jd-fit-resume/SKILL.md)

Paste JD URL or text → local package (`jd.txt`, `cover-letter.txt`, tailored `.tex` + `.pdf`; `.docx` only when requested). **No submit.** Also used by job-apply-loop on Apply OK.

## Shared (not main entry points)

| Skill | Role |
|-------|------|
| [`candidate-source.md`](.agents/skills/candidate-source.md) | Sole CV fact source — all mains read first |
| [`browser-session/`](.agents/skills/browser-session/) | Dedicated persistent browser contract for every interactive browser task |
| [`website-apply-loop/`](.agents/skills/website-apply-loop/) | Apply-loop browser handoff and writing voice — job & freelance loops |

## Project rules (all agents)

1. **Master CV:** Read [`.agents/skills/candidate-source.md`](.agents/skills/candidate-source.md), then read `resume.tex` fresh for every skill task. Never use chat memory or existing profiles as evidence; ask for required fields absent from the CV.
2. **JD packages:** Follow [`jd-fit-resume`](.agents/skills/jd-fit-resume/SKILL.md). Copy master into dated folders; never overwrite master. Job packages are local-only (gitignored).
3. **CV compilation:** Use `python compile_cv.py [source]` for PDF (default) or add `--format docx` for Word. Both outputs must be generated from the selected `.tex`; never maintain a separate candidate-fact source for DOCX.
4. **Freelance applies:** Follow `freelance-apply-loop`. **Never submit without explicit OK** (`OK` / `Apply` / `yes` / `go` / `قدم` / `موافق`). Mostaql proposals default to **Arabic**.
5. **Connects / balance / paywall:** If blocked, report and ask — do not fake-submit.
6. **Browser:** For every interactive browser task, follow [`browser-session`](.agents/skills/browser-session/SKILL.md). Use only the explicitly configured dedicated persistent profile through `npm run browser -- ...`; never silently open an integrated, system-default, or personal-profile browser. End by leaving the dedicated browser and tabs open.
7. **Employment sites:** Follow `job-apply-loop`. Login page → pause for user takeover; unresolved login → block that site and rotate without closing tabs. Never submit without per-job OK. After one successful submission, ask: **Do we continue with the same site or move to another?**

# Gemini CLI

Follow the portable project instructions in [`AGENTS.md`](AGENTS.md).

Canonical skills live in [`.agents/skills/`](.agents/skills/). Treat each
`SKILL.md` as the workflow runbook for that task, and do not maintain a second
copy of the instructions in Gemini-specific files.

## Main workflows

| Request | Canonical skill |
|---------|-----------------|
| Tailor a CV for a JD or job URL | [jd-fit-resume](.agents/skills/jd-fit-resume/SKILL.md) |
| Apply to employment sites | [job-apply-loop](.agents/skills/job-apply-loop/SKILL.md) |
| Apply on Upwork or Mostaql | [freelance-apply-loop](.agents/skills/freelance-apply-loop/SKILL.md) |

Gemini project commands in [`.gemini/commands/`](.gemini/commands/) are only
launchers for those canonical skills:

- `/tailor-cv`
- `/apply-jobs`
- `/apply-upwork`
- `/apply-mostaql`

For every workflow, read [`.agents/skills/candidate-source.md`](.agents/skills/candidate-source.md)
and the current `resume.tex`. Never submit an application or
freelance proposal without the explicit per-item approval required by the
canonical skill.

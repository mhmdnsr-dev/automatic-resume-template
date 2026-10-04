# Claude Code

Follow the portable project instructions in [`AGENTS.md`](AGENTS.md).

Canonical skills: [`.agents/skills/`](.agents/skills/) (Agent Skills standard).
Claude project skills under [`.claude/skills/`](.claude/skills/) are pointer
adapters only. Edit the canonical skills under `.agents/skills/`.

**Main skills:**

| Trigger | Skill |
|---------|--------|
| LinkedIn / Indeed / Wuzzuf / employment apply | [job-apply-loop](.agents/skills/job-apply-loop/SKILL.md) |
| Upwork / Mostaql / freelance / proposals | [freelance-apply-loop](.agents/skills/freelance-apply-loop/SKILL.md) |
| JD link, tailor CV, job folder | [jd-fit-resume](.agents/skills/jd-fit-resume/SKILL.md) |

Legacy: `upwork-apply-loop` and `mostaql-apply-loop` redirect to **freelance-apply-loop**.

For CV / JD packages, follow [jd-fit-resume](.agents/skills/jd-fit-resume/SKILL.md) and [`WORKFLOW.md`](WORKFLOW.md).

For every interactive browser task, follow [browser-session](.agents/skills/browser-session/SKILL.md). Job and freelance loops also follow [website-apply-loop](.agents/skills/website-apply-loop/SKILL.md) for authentication handoff and proposal voice.

For every skill, read [candidate-source.md](.agents/skills/candidate-source.md) and the current `resume.tex`.

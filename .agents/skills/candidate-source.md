# Candidate source of truth

Every skill in this repository must read `resume.tex` **fresh at the start of the task** before producing, changing, or submitting any content about Example Candidate.

## Sole-source rule

`resume.tex` is the **only source of personal and professional facts**:

- identity and contact details
- location
- headline / professional positioning
- experience, employers, dates, titles, responsibilities, and metrics
- education
- projects and links
- skills, tools, technologies, and workflows

Do not use remembered chat facts, an existing website profile, previous proposals, skill examples, or cached summaries as evidence. They may be stale. Rephrase and reorder CV facts for the target, but never add a claim that cannot be traced to the current `.tex`.

## Unknown fields

If a form asks for information absent from the CV—such as salary expectation, notice period, availability, work authorization, relocation preference, language proficiency, demographic data, or a legal declaration—**ask the user**. Do not infer it.

## Application-answer preferences

These are user-approved form-handling preferences, not CV facts:

- **Current salary:** Treat as confidential. Leave blank when optional; enter `0` when the field is mandatory and accepts free text or numbers.
- **Expected salary:** Do not invent an amount without the employer's salary range. Leave blank when optional; enter `0` when mandatory and accepts free text or numbers.
- **Notice period:** Use `30 days` (one month).

If a mandatory salary field rejects `0`, asks for a currency/range declaration, or requires selecting a non-zero option, stop and ask the user.

Platform mechanics are not candidate facts: URLs, button names, proposal limits, and browser behavior may come from the live site. Treat existing profile values as data to review, not a source to copy into another profile.

## Conflict rule

When a skill guide/example conflicts with the current `.tex`, the `.tex` wins. Update the generated content from the `.tex`; do not preserve the stale claim.

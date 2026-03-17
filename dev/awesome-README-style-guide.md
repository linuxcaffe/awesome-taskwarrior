# awesome-taskwarrior README Style Guide

A guide for writing and revising README files for extensions in the
awesome-taskwarrior ecosystem. The goal is a README that communicates
clearly to a Taskwarrior user who has never heard of this extension:
what it does, why they'd want it, and how to get started — without
making them wade through internals.

---

## Guiding principles

- **Features, advantages, benefits** — in that order, without using
  those words as headings. Features go in TL;DR. Advantages go in
  "Why this exists". Benefits go in "What this means for you".
- Plain English first. Jargon only where unavoidable, defined when
  first used.
- If it belongs in DEVELOPERS.md, it doesn't belong here.
- Show, don't tell. Real commands beat abstract descriptions.
- Honest project status. Don't oversell stability.

---

## Section order and requirements

### 1. Top links  *(required)*
Two bare lines, before the title. No heading.
```
- Project: https://github.com/linuxcaffe/<repo>
- Issues:  https://github.com/linuxcaffe/<repo>/issues
```

### 2. Title and subtitle  *(required)*
```markdown
# extension-name

One sentence. Plain English. What it does, not how it works.
```
The subtitle should be comprehensible to someone who doesn't know
Taskwarrior internals. Avoid hook terminology here.

---

### 3. TL;DR  *(required)*
Bullet list. 4–8 items. Each bullet is a **feature** — a concrete
capability the extension adds. Lead with the most compelling item.
Use backtick code formatting for any commands, tags, or field names.
End with the Taskwarrior version requirement if it constrains usage.

> **Purpose:** Features. Answers: *"What does it do?"*

---

### 4. Why this exists  *(required)*
2–4 short paragraphs. Describe the problem in Taskwarrior that
motivated this extension. Be specific — name the limitation, the
friction, the gap. This section should make the reader nod.

Avoid vague phrases like "makes things easier". Name the actual pain.

> **Purpose:** Advantages. Answers: *"Why does this beat the
> built-in approach, or doing nothing?"*

---

### 5. What this means for you  *(required)*
1–3 sentences. Plain language. No code. This is the payoff — the
user's life after installing this extension. Written from the user's
perspective, not the developer's.

Examples of the right register:
- *"You can keep throwing any kind of task into your list without
  losing focus on what actually matters right now."*
- *"Your task list shrinks to what's actionable at this moment,
  without hiding anything important."*
- *"Set it once. Every recurring task just appears when it's due,
  without you tracking it."*

Avoid feature language here. No backticks. No "this hook". Just the
human outcome.

> **Purpose:** Benefits. Answers: *"How will my day actually
> be different?"*

---

### 6. Core concepts  *(include if the extension introduces new terms)*
Named terms in bold, each followed by a 1–3 sentence explanation.
Define only terms the user will encounter in Usage or Configuration.
Keep it short — this is a glossary, not a tutorial.

If there are no new terms (the extension is self-evident from Usage),
omit this section.

---

### 7. Installation  *(required)*
Three options, in this order. Use consistent heading style:

```markdown
### Option 1 — Install script
### Option 2 — Via [awesome-taskwarrior](https://github.com/linuxcaffe/awesome-taskwarrior)
### Option 3 — Manual
```

**Option 1** curls the `.install` file and runs it. Use this form:

```bash
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/<name>/main/<name>.install | bash
```

One line saying what it installs where. The pipe-to-bash form is
preferred for brevity; show the two-step form (save then run) only if
the script requires user review or has interactive prompts.

**Option 2** is the `tw -I <name>` one-liner. Nothing else needed.

**Option 3** is the manual steps, with inline comments in the code
block. End with the `~/.taskrc` include line and a verification
command if one exists, and task diag, if applicable.

---

### 8. Configuration  *(include if the extension has user-facing config)*
Show the config file with real defaults. Annotate non-obvious values
inline. Keep explanations short — one line per setting is usually
enough. Point to supplemental docs for advanced config.

---

### 9. Usage  *(required)*
Use `task <command>` throughout — not `tw <command>` — except where
the command genuinely requires the `tw` wrapper (e.g. `tw -I`,
`tw checkup`). Concrete commands with inline `# comments`. Group
related commands under bold sub-headings if needed. Use real-world
examples, not toy ones. Show companion scripts or aliases here.

---

### 10. Example workflow  *(include where helpful)*
A brief end-to-end scenario showing the extension solving a real
problem. Use numbered steps. Use `task <command>` except for actual
`tw` commands. Show both the commands and the result (✓/✗ lists,
before/after output, etc.). Place after Usage, not before Installation.

Omit this section if the Usage section already tells the complete
story.

---

### 11. Project status  *(required)*
One of two forms:

- Active and stable: one sentence.
- Early/experimental: use the ⚠️ prefix and list what may change.

Be honest. Don't claim stability that isn't there.

---

### 12. Further reading  *(include if supplemental docs exist)*
Short bulleted list of links with one-line descriptions. Typical targets:
- `DEVELOPERS.md` — architecture, internals, hook API
- `CHANGES.txt` — version history
- External specs or RFCs this implements

---

### 13. Metadata  *(required)*
```markdown
## Metadata

- License: MIT
- Language: Python (or Bash, etc.)
- Requires: Taskwarrior 2.6.2, Python 3.6+
- Platforms: Linux
- Version: x.y.z
```

---

## What belongs in DEVELOPERS.md, not here

Move these out of the README:

- Architecture diagrams and file-role tables
- Hook lifecycle explanations (on-add / on-modify / on-exit flow)
- Internal data structures (spool file, JSON format, etc.)
- Full field reference tables
- Validation rule lists
- Debug mode details beyond a one-liner

A one-line mention with a link is fine. Full explanation goes to DEVELOPERS.md.

---

## Tone and voice

- Second person ("you"), active voice.
- Short sentences. One idea per sentence.
- No "simply", "easily", "just" — if it were simple, they wouldn't
  need a README.
- Jargon that's unavoidable: define it in Core Concepts, then use
  freely.
- Emoji: ⚠️ for warnings, ✓/✗ in workflow examples only. Not
  decorative.

---

## Quick section checklist

| Section | Required? | Notes |
|---|---|---|
| Top links | ✓ | Before title, no heading |
| Title + subtitle | ✓ | Plain English subtitle |
| TL;DR | ✓ | Features, 4–8 bullets |
| Why this exists | ✓ | The problem |
| What this means for you | ✓ | The human payoff |
| Core concepts | if needed | New terms only |
| Installation | ✓ | 3 options |
| Configuration | if needed | With real defaults |
| Usage | ✓ | Real examples + comments |
| Example workflow | if helpful | After usage |
| Project status | ✓ | Honest |
| Further reading | if needed | Links with descriptions |
| Metadata | ✓ | License, language, requires, version |

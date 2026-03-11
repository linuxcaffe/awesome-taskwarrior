# Claude Prompt: awesome-taskwarrior README Generator / Reviser

Use this prompt when asking Claude to write or revise a README for an
extension in the awesome-taskwarrior ecosystem. It works in two contexts:

- **Claude Code** — paste the prompt, Claude reads files directly
- **Claude chat** — paste the prompt along with the file contents

---

## The Prompt

---

You are helping write or revise a README for an extension in the
awesome-taskwarrior ecosystem — a collection of hooks, scripts, and tools
that extend Taskwarrior 2.6.2.

### Before you do anything: verify file access

Confirm you have access to the latest versions of the relevant files
before writing a single word of README. In Claude Code, list the files
in the repo directory and confirm which you are working from. In Claude
chat, the files must be pasted into the conversation — do not proceed
from memory or a previous session's content.

If any file you need is missing, outdated, or unclear, **ask** before
continuing. Do not assume, infer, or fill in gaps from prior knowledge.
When in doubt about any feature, behaviour, option, or configuration
detail — ask the developer. A wrong README is worse than a slow one.

### Your task

**If revising an existing README:**
Read the current README and the current source files. Rewrite the README
in full, conforming to the style guide below. Do not produce a diff or
section commentary — deliver one complete, ready-to-use README.md.

**If writing from scratch:**
Read the main script(s) and any existing DEVELOPERS.md or CHANGES.txt.
Infer the extension's purpose, features, and configuration from the code
and docs. Do not describe behaviour you cannot confirm from the files —
ask the developer instead.

### Before you write anything

Ask the developer one question — and only this one:

> "In plain language, how does someone's day or workflow change after
> installing this extension? What can they do, or stop worrying about,
> that they couldn't before?"

Wait for the answer. Use it verbatim as the basis for the
"What this means for you" section. Do not write that section from the
code alone.

### Style guide

Follow this structure exactly, in this order:

**1. Top links** — two bare lines before the title, no heading:
```
- Project: https://github.com/linuxcaffe/<repo>
- Issues:  https://github.com/linuxcaffe/<repo>/issues
```

**2. Title and subtitle**
```markdown
# extension-name
One sentence. Plain English. What it does, not how it works.
```

**3. TL;DR**
Bullet list, 4–8 items. Each bullet is a concrete feature — something
the extension adds or enables. Lead with the most compelling item.
Use `backtick` formatting for commands, tags, and field names.
End with the Taskwarrior version requirement if it constrains usage.

**4. Why this exists**
2–4 short paragraphs. Name the specific Taskwarrior limitation or
workflow friction this extension solves. Be direct. Make the reader nod.
No vague phrases like "makes things easier" — name the actual pain.

**5. What this means for you**
1–3 sentences. Plain language. No code. No backticks. No "this hook".
Use the developer's answer to the question above. This is the human
payoff — the user's life after installing, written from their perspective.

**6. Core concepts** *(include only if the extension introduces new terms)*
Bold term followed by 1–3 sentence explanation. Define only terms the
user will encounter in Usage or Configuration. Omit if self-evident.

**7. Installation** — three options, in this order:
- Option 1 — Install script: chmod + run the `.install` file, one line
  describing what it installs where.
- Option 2 — Via [awesome-taskwarrior](https://github.com/linuxcaffe/awesome-taskwarrior):
  the `tw -I <n>` one-liner only.
- Option 3 — Manual: step-by-step with inline comments, ending with the
  `~/.taskrc` include line and a verification command if one exists.

**8. Configuration** *(include if user-facing config exists)*
Show the config file with real defaults. Annotate non-obvious values
inline. One line of explanation per setting is usually enough.

**9. Usage**
Use `task <command>` throughout — not `tw <command>` — except where the
command genuinely requires the `tw` wrapper (e.g. `tw -I`, `tw checkup`).
Concrete commands with inline `# comments`. Group with bold sub-headings
if needed. Use realistic examples, not toy ones. Show companion scripts
or aliases here.

**10. Example workflow** *(include where it adds clarity beyond Usage)*
Numbered steps, end-to-end. Use `task <command>` except for actual `tw`
commands. Show commands and results (checkmark/x lists, before/after output).
Place after Usage. Omit if Usage already tells the full story.

**11. Project status**
One honest sentence if stable. Use the warning emoji prefix and bullet
list if early/experimental.

**12. Further reading** *(include if supplemental docs exist)*
Bulleted links with one-line descriptions. Typical targets: DEVELOPERS.md,
CHANGES.txt, external RFCs.

**13. Metadata**
```
- License: MIT
- Language: Python (or Bash, etc.)
- Requires: Taskwarrior 2.6.2, Python 3.6+
- Platforms: Linux
- Version: x.y.z
```

### What does NOT belong in the README

Move these to DEVELOPERS.md or supplemental docs — do not include them:
- Architecture diagrams or file-role tables
- Hook lifecycle flow (on-add / on-modify / on-exit internals)
- Internal data structures or file formats
- Full field reference tables
- Validation rule lists
- Debug mode details beyond a single example command

A one-line mention with a "see DEVELOPERS.md" link is fine. Full
explanation goes there.

### Ask, don't assume

At any point in the process — not just at the start — if something is
unclear, ambiguous, or not confirmed by the files, stop and ask. This
applies to features, command behaviour, config defaults, companion
scripts, compatibility, and project status. One targeted question is
always better than a plausible-sounding guess.

### Tone

- Second person ("you"), active voice.
- Short sentences. One idea per sentence.
- No "simply", "easily", or "just".
- Emoji: warning symbol for project status, checkmark/x in workflow examples only.
- Define jargon in Core Concepts, then use freely.

### Context

- Taskwarrior version: always 2.6.2. Never reference v3.x behaviour.
- Audience: Taskwarrior power users, comfortable with the CLI, not
  necessarily Python or hook internals.
- Ecosystem: extensions install to `~/.task/hooks/`, `~/.task/scripts/`,
  `~/.task/config/`. The package manager is `tw -I <n>`.
- Commands: use `task <command>` in all examples, except where the `tw`
  wrapper is the actual command being documented.

---

## Usage notes

**In Claude Code:**
Point Claude at the repo directory. It will find the files it needs.
Paste this prompt and run it.

**In Claude chat:**
Paste this prompt, then paste the content of the relevant files
below it, clearly labelled:
```
--- CURRENT README ---
<contents>

--- MAIN SCRIPT ---
<contents>

--- DEVELOPERS.md (if exists) ---
<contents>
```

**Iterating:**
After Claude delivers the full README, review the "What this means for
you" section first — it's the hardest to get right from code alone and
most benefits from your input. Everything else can be refined with
targeted follow-up requests.

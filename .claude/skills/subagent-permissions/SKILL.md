---
name: subagent-permissions
description: Fix the "sub-agents can't write to project" sandbox issue by configuring .claude/settings.json with explicit Edit/Write/Bash allow rules + additionalDirectories for the project root. Symptoms — Agent tasks return "Write tool denied", "permission denied for path", "sandbox is rooted at <other dir>", or sub-agents that author content scripts but no .md files appear on disk. Triggers when the user asks to "unlock sub-agents", "fix permissions", "agents can't write", "Write denied", or after any sub-agent fails with a sandbox error.
---

# Unlock sub-agent write access for this project

When the parent Claude Code session is launched from a directory
OUTSIDE the project tree (e.g. cwd is `C:\Users\dimos\Downloads` but
the project is in `C:\Users\dimos\Documents\orthodox-site`), sub-agents
inherit a more restrictive sandbox than the parent. They get read
access but their Write/Edit/Bash calls into the project tree are
silently denied.

The fix is a project-level `.claude/settings.json` with explicit allow
rules.

## Symptoms

Any of these in a sub-agent's report:

- `Write tool denied`
- `EACCES`, `permission denied`, `sandbox is rooted at ...`
- Agent says "I authored 15 files" but `ls` shows 0
- Agent suggests running a script externally to bypass the sandbox

## The fix

Create or merge into `.claude/settings.json` at the project root:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Read",
      "Edit(C:/Users/dimos/Documents/orthodox-site/**)",
      "Write(C:/Users/dimos/Documents/orthodox-site/**)",
      "Bash(python *)",
      "Bash(python3 *)",
      "Bash(npm *)",
      "Bash(npx *)",
      "Bash(node *)",
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git push*)",
      "Bash(git pull*)",
      "Bash(ls *)",
      "Bash(mkdir *)",
      "Bash(cd *)"
    ],
    "additionalDirectories": [
      "C:/Users/dimos/Documents/orthodox-site"
    ]
  }
}
```

Use **forward slashes** in the paths. Windows handles them; JSON
escaping of backslashes is brittle. The project root MUST appear in
both `Edit(...)`/`Write(...)` rules AND `additionalDirectories` —
neither alone suffices.

## Verify

After committing the file, spawn a tiny test sub-agent:

> "Use the Write tool to create
> `C:\Users\dimos\Documents\orthodox-site\scripts\_perm_test.py` with
> the content `print('ok')`. Report only success/failure."

If it reports success, delete `_perm_test.py` and proceed with the
real work. If it still fails, the project-level settings file may not
be loading because:
- The session was launched before the file existed → restart Claude
  Code from inside the project directory.
- The path uses backslashes that JSON didn't escape correctly → use
  forward slashes.

## Don't

- Don't put this into `~/.claude/settings.json` (global). Project-level
  is correct because the rules are repo-specific.
- Don't add `"defaultMode": "acceptEdits"` — that's too permissive
  globally; explicit allow rules are safer.
- Don't try to bypass via `dangerouslyDisableSandbox: true` per-call.
  The settings approach is durable across sessions and clean.

## Why this is committed to the repo

`.claude/settings.json` is project-level config and is gitignored by
default in some setups, but for this repo we **commit it** so:
- Anyone collaborating gets the same sub-agent unlock automatically.
- The rules are reviewable in PR diffs (security audit).
- No "magic local file" that has to be recreated each time.

If concerned about leaking dev paths, you can replace the absolute
`C:/Users/dimos/...` with `${PROJECT_ROOT}/**` once that template is
supported (currently it isn't — Claude Code resolves paths literally).

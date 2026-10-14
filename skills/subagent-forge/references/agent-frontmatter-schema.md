# Subagent frontmatter schema

A subagent is a Markdown file with a YAML frontmatter block. The frontmatter
configures *how* the agent runs; the body is the agent's system prompt.

```markdown
---
name: scout
description: Fast codebase recon that returns compressed context for handoff to other agents
tools: read, grep, find, ls, bash
model: claude-haiku-4-5
---

You are a scout. Quickly investigate a codebase and return structured
findings that another agent can use without re-reading everything.
```

Everything below describes the format used by the pi subagent runner
(shipped as `examples/extensions/subagent/` upstream) and by Claude Code's
`.claude/agents/` directory. The two agree on the core fields; differences
are called out per field.

## Where agents live

| Scope | Directory | Loaded when |
|-------|-----------|-------------|
| User | `~/.pi/agent/agents/*.md` | Always available |
| Project (pi) | `<repo>/.pi/agents/*.md` | Only when the caller passes `agentScope: "project"` or `"both"`, and the project is trusted |
| Project (Claude Code) | `<repo>/.claude/agents/*.md` | Claude Code-compatible agents; checked when running under that agent |

Discovery details that matter when you place a file:

- The pi runner walks **up** from the current working directory to the
  repository root and uses the **nearest** `.pi/agents/` directory it finds.
  Put project agents at the repo root unless you deliberately want a
  nested, closer directory to win for a subtree.
- Only files ending in `.md` are read, and symlinks are followed.
- A malformed file is skipped silently rather than crashing discovery, so a
  broken agent simply never appears in the available list. Always run
  `scripts/validate_agents.py` after writing one.
- When scope is `"both"`, a **project agent overrides a user agent with the
  same `name`**. That is the intended way to specialize a personal agent for
  one repository.

## Fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `name` | Yes | string | The identifier the dispatching model passes to the subagent tool. Keep it lowercase-hyphenated (`test-writer`, not `TestWriter`). Must be unique within a scope; duplicates resolve by source precedence. |
| `description` | Yes | string | Shown in the agent list the parent model selects from. This is the *only* thing that decides whether the agent is picked for a task — write it like a routing description, stating what the agent does and what kinds of tasks belong to it. |
| `tools` | No | string or array | Tool allowlist. Both spellings are valid and handled: `tools: read, grep, find, ls` and `tools: [read, grep, find, ls]`. Omit it to give the agent the full default tool set. Empty/invalid values yield no tools. |
| `model` | No | string | Model id to run the agent on (e.g. `claude-sonnet-4-5`, `claude-haiku-4-5`). **Omit to inherit** the dispatching session's active model and thinking level — usually the safest default. |

A file missing `name` or `description` (or with a non-string value for
either) is skipped. `tools` and `model` are optional.

### `tools` values

Use the exact tool names the host exposes. Common ones:

| Tool | Read-only? | Typical use |
|------|-----------|-------------|
| `read` | Yes | Read file contents |
| `grep` | Yes | Search file contents |
| `find` | Yes | Find files by name/pattern |
| `ls` | Yes | List directories |
| `bash` | No | Run shell commands — read-only *or* mutating |
| `edit` | No | Modify existing files |
| `write` | No | Create/overwrite files |

Note that `bash` is not intrinsically read-only: a reviewer agent that
declares `bash` can still run destructive commands. Scope it by instruction
(`"Bash is for read-only commands only"`) and prefer agents that omit
`bash` entirely when recon can be done with `read`/`grep`/`find`/`ls`.

### `model` guidance

- **Omit** for behavioral specialists whose quality matters and whose cost
  should track the parent session (planners, reviewers).
- Set a fast, cheap model for high-volume, mechanical recon (scouts).
- Do not hardcode a model that the target project's provider does not have.
  If unsure, omit it; the agent will inherit and still work.

## YAML safety

The same trap that bites `SKILL.md` bites agent files: an **unquoted**
description containing `: ` (colon+space), `#`, or a leading quote is
invalid YAML. The parser error looks like:

```
Error in user YAML: mapping values are not allowed in this context
```

Because most good descriptions contain a colon somewhere, always either
single-quote the value (escaping inner `'` as `''`) or use a `>-` block
scalar:

```yaml
description: >-
  Reviews code for quality and security. Use for pull-request review,
  pre-merge audits, and "is this safe to ship" questions.
```

`scripts/new_agent.py` quotes the description for you; the validator
catches this class of error if you hand-edit.

## Minimal vs full example

Minimal — inherits model and all default tools:

```markdown
---
name: docs-writer
description: Writes and updates project documentation from source and existing docs. Use for README, API reference, and guide updates.
---

You are a documentation specialist. ...
```

Full — pinned model and a read-only tool set:

```markdown
---
name: reviewer
description: Code review specialist for quality and security analysis. Use after changes land, before merge, or when asked "is this safe".
tools: [read, grep, find, ls, bash]
model: claude-sonnet-4-5
---

You are a senior code reviewer. ...
```

## Related: workflow prompts

The pi subagent runner can also load orchestration prompts from
`~/.pi/agent/prompts/*.md` (or a project prompts directory). Those are a
separate artifact from agent files — see
`references/workflow-prompts.md` for the format and when to add one.

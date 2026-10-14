---
name: subagent-forge
description: 'Designs, scaffolds, and validates working project-scoped subagents (pi .pi/agents and Claude Code .claude/agents) for the current repository. Use this whenever the user wants to create a subagent, add or edit an agent definition, set up scout/planner/reviewer/worker-style agents, delegate work to isolated context windows, or organize multi-agent workflows for a project, even if they do not say ''skill'' or ''subagent'' explicitly.'
---

# subagent-forge

Turn "I want an agent that does X for this repo" into a working, validated
subagent definition (`.pi/agents/*.md`, optionally mirrored to
`.claude/agents/*.md`) that the subagent tool can actually discover, select,
and run.

A subagent is a Markdown file with YAML frontmatter. The frontmatter
(`name`, `description`, optional `tools`/`model`) configures it; the body is
its system prompt. The full field reference lives in
`references/agent-frontmatter-schema.md`.

## When to use this skill

Use it when the user:

- Asks to create, add, or edit a subagent / agent for the project
- Wants scout, planner, reviewer, worker, tester, auditor, or similar
  specialized agents
- Wants to delegate work to isolated context windows or parallelize agents
- Wants to organize a multi-agent workflow or an `/implement`-style command
- Mentions `.pi/agents`, `.claude/agents`, "project agents", or `subagent`

Do **not** use it for a one-off request to "act like a reviewer" in the
current conversation — that is not a reusable agent artifact.

## Core loop

1. Capture intent and scope.
2. Analyze the current project.
3. Choose the roster.
4. Scaffold each agent.
5. Write the system prompt and output contract.
6. Pick tools and model.
7. Validate.
8. Optionally add workflow prompts.
9. Report and show how to invoke.

Work through the steps in order. Stop and ask the user if intent or scope is
genuinely ambiguous; otherwise pick sensible defaults and say what you
assumed.

---

## Step 1 — Capture intent and scope

Establish, from the request or by asking:

1. **Which task(s)** should the agent(s) handle that the parent session
   cannot do inline? (isolated context, parallelism, read-only safety, or a
   specialized output contract)
2. **Which scope**: project (`.pi/agents/`, and/or `.claude/agents/`) or
   user-level (`~/.pi/agent/agents/`). Default to project for repo-specific
   agents; user-level only for genuinely repo-agnostic ones.
3. **Read-only or mutating**: must it change files, or only inspect?

If the conversation already contains a workflow the user wants captured,
extract the agent roles and boundaries from it and confirm before writing
files, rather than re-interviewing from scratch.

## Step 2 — Analyze the current project

Read `references/project-analysis.md` and follow it. The short version:
detect the stack, the real test/lint/build commands, the layout (especially
monorepos), and any existing agents, then write a one-line rationale per
planned agent. Check for an existing roster first:

```bash
ls .pi/agents .claude/agents 2>/dev/null
python3 scripts/list_agents.py --project .
```

Never create a duplicate name; edit the existing agent or pick a distinct
role.

## Step 3 — Choose the roster

Read `references/agent-patterns.md` and select only the archetypes the
project actually needs. For each agent, be able to state its trigger, what
it reads, whether it writes, its output contract, and its model tier. If you
cannot, do not create it.

Default lean roster for an unfamiliar repo:

- `scout` — read-only recon
- `reviewer` — read-only review
- `worker` — full-capability implementation

Add `planner`, `test-writer`, `docs-writer`, or an `auditor` only when the
project's workflow calls for them. Fewer sharp agents beat many vague ones.

## Step 4 — Scaffold each agent

Preferred: use the bundled scaffold script, which validates the name and
quotes the description for YAML safety.

```bash
# Project agents (pi), inheriting the parent model, read-only tools:
python3 scripts/new_agent.py \
  --name scout \
  --description "Fast codebase recon that returns compressed context for handoff. Use to locate relevant code before planning or implementing." \
  --tools "read, grep, find, ls, bash" \
  --targets pi

# Mirror to Claude Code as well:
python3 scripts/new_agent.py --name reviewer \
  --description "..." --tools "read, grep, find, ls, bash" \
  --targets pi,claude

# Write a fully custom prompt body from a file:
python3 scripts/new_agent.py --name worker --description "..." \
  --body-file <path-to-prompt-file>
```

Useful flags: `--dir <project-root>`, `--targets pi,claude,user`,
`--model <id>` (omit to inherit), `--force` (overwrite; off by default).

Alternatively, copy a ready-made starter from `assets/templates/` and edit
it: `assets/templates/agent-template.md` (generic),
`assets/templates/scout.md`, `assets/templates/planner.md`,
`assets/templates/reviewer.md`, `assets/templates/worker.md`,
`assets/templates/test-writer.md`. These are complete, valid agent files.

If you hand-write a file instead of using the script, the frontmatter must
start on the **first line** of the file and the description must be quoted
if it contains `: `, `#`, or quotes — see
`references/agent-frontmatter-schema.md`.

## Step 5 — Write the system prompt and output contract

Replace the scaffolded body. A good body:

- States the agent's job and its constraints in imperative language.
- Tells the agent its output goes to an agent that has **not** seen the
  files it explored (for recon/scout agents).
- Defines a short output contract of three to five fixed `##` sections the
  parent can consume without re-reading everything.
- Requires `path:line` references where the caller will act on them.
- References the project's **real** commands (from Step 2), never invented
  ones.
- Uses repo-relative paths only — no machine-specific absolute paths.

Pattern-match against the archetypes in `references/agent-patterns.md`.

## Step 6 — Pick tools and model

Apply least privilege (`references/agent-patterns.md#tool-scoping`):

- Read-only roles (`scout`, `planner`, `reviewer`, `auditor`): read tools
  only; add `bash` solely for read-only commands and say so in the prompt.
- Mutating roles (`worker`, `test-writer`, `docs-writer`): add `write`,
  `edit`, and `bash` as needed.
- **Omit `tools` entirely** when the agent needs the full default set.

For `model`, **omit it by default** so the agent inherits the dispatching
session's model and thinking level. Only pin a model when a specific tier is
required and the project's provider serves that exact id. A wrong model id
breaks the agent; inherit always works.

## Step 7 — Validate

Run the validator against the directory you wrote to:

```bash
python3 scripts/validate_agents.py .pi/agents
python3 scripts/validate_agents.py .pi/agents .claude/agents
python3 scripts/validate_agents.py --project . --user   # discover everything
```

It checks frontmatter parses as YAML, `name`/`description` exist, names are
valid and unique, `tools`/`model` are well-formed, the body is non-empty,
and read-only roles do not carry mutating tools. Fix every error before
continuing. Then walk `references/validation-checklist.md` for the judgment
calls a linter cannot make.

## Step 8 — Optionally add workflow prompts

If the roster is used as a fixed sequence repeatedly, add a prompt so it
runs as one command. Read `references/workflow-prompts.md`, then start from
`assets/templates/workflow-prompt.tmpl`. Do not create a prompt for a
composition the user would run once — chaining inline is fine.

## Step 9 — Report and show how to invoke

Summarize what was created: one line per agent (name, scope, tools, model,
trigger), plus the files written. Then show how to invoke:

```
Use scout to find all authentication code
Run 2 scouts in parallel: one for models, one for providers
Chain: scout -> planner -> worker to add caching
```

Note for the caller: in this environment, pass `confirmProjectAgents: false`
when invoking **project-local** agents in a trusted repository, to skip the
repeated confirmation prompt. Never do this for an untrusted project, and
never attempt to bypass a trust prompt.

---

## Prerequisites

The file-based subagent runner (pi's `examples/extensions/subagent`, or an
equivalent extension) must be installed and enabled; otherwise the
`.pi/agents` files are inert. `.claude/agents/*.md` is the Claude Code
convention. If the subagent tool is unavailable, tell the user rather than
claiming the agents will run.

## Scripts

- `scripts/new_agent.py` — scaffold one agent file with valid frontmatter;
  refuses overwrite unless `--force`.
- `scripts/validate_agents.py` — lint agent files; non-zero exit on errors.
- `scripts/list_agents.py` — list discovered user/project agents and
  precedence; use before creating to avoid duplicates.

## Assets

Ready-made agent templates (editable, valid as-is):
`assets/templates/agent-template.md` (generic),
`assets/templates/scout.md`, `assets/templates/planner.md`,
`assets/templates/reviewer.md`, `assets/templates/worker.md`,
`assets/templates/test-writer.md`. Workflow prompt starter:
`assets/templates/workflow-prompt.tmpl`. Copy one and edit it, or generate
with `scripts/new_agent.py`.

## Reference files

- `references/agent-frontmatter-schema.md` — every frontmatter field, agent
  locations, precedence, and YAML-safety rules. Read before hand-editing.
- `references/project-analysis.md` — read-only checklist to infer the
  project's stack, commands, and layout. Read at Step 2.
- `references/agent-patterns.md` — archetypes, tool scoping, model tiering,
  output contracts, orchestration modes, anti-patterns. Read at Step 3.
- `references/workflow-prompts.md` — orchestration prompt format and
  `{previous}` chaining. Read at Step 8.
- `references/validation-checklist.md` — manual review checklist to run
  after the validator. Read at Step 7.

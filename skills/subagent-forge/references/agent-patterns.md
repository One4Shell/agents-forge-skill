# Subagent patterns

Reusable archetypes and the rules that keep a roster useful. Start from an
archetype and adapt the prompt; do not invent a novel role unless the
project genuinely needs one.

## Contents

- [Archetypes](#archetypes)
- [Tool scoping](#tool-scoping)
- [Model tiering](#model-tiering)
- [Output contracts](#output-contracts)
- [Orchestration modes](#orchestration-modes)
- [Naming](#naming)
- [Anti-patterns](#anti-patterns)

## Archetypes

### scout — fast codebase recon

- **Purpose:** investigate a codebase and return compressed findings the
  parent (or a downstream agent) can use *without re-reading everything*.
- **Tools:** `read, grep, find, ls` (add `bash` only if recon needs `git`
  history or command output).
- **Model:** a cheap/fast tier, or omit.
- **Contract:** list of files with exact line ranges, the key code, how the
  pieces connect, and "start here" guidance. State up front that the reader
  has not seen the files.
- **Best for:** parallel fan-out over an unfamiliar area; feeding a planner.

### planner — implementation plans

- **Purpose:** turn context + requirements into a concrete, ordered plan.
- **Tools:** read-only (`read, grep, find, ls`). A planner must not write.
- **Model:** inherit or a strong tier.
- **Contract:** Goal, numbered Plan (each step small and actionable), Files
  to Modify, New Files, Risks. The plan should be executable verbatim.
- **Best for:** before a nondeterministic change; producing a reviewable
  artifact with no side effects.

### reviewer — quality and security analysis

- **Purpose:** review changes for bugs, security, and maintainability.
- **Tools:** `read, grep, find, ls`, and `bash` for **read-only** git
  commands (`git diff`, `git log`, `git show`) only. Say so explicitly in
  the prompt.
- **Model:** inherit or a strong tier — review quality tracks reasoning.
- **Contract:** Files Reviewed, Critical (must fix), Warnings (should fix),
  Suggestions (consider), Summary. Require file:line references.
- **Best for:** pre-merge review, post-implementation verification.

### worker — general-purpose implementer

- **Purpose:** execute a delegated task end-to-end in an isolated context.
- **Tools:** omit `tools` to grant the full default set (it needs to edit
  and run commands).
- **Model:** inherit or a strong tier.
- **Contract:** Completed, Files Changed (paths + what changed), Notes. If
  handing off, include exact paths and touched symbols.
- **Best for:** offloading a well-specified change so the main session's
  context stays clean.

### test-writer — tests for existing code

- **Purpose:** add or improve tests for a described module/behavior.
- **Tools:** `read, grep, find, ls, write, edit, bash` (it runs the suite).
- **Model:** inherit.
- **Contract:** test files added/changed, cases covered, command to run
  them, and any failures that remain (do not hide red tests).
- **Best for:** raising coverage on a specific module; mirroring an
  existing test's style. Point it at the project's real test command.

### docs-writer — documentation

- **Purpose:** write/update README, API reference, guides from source.
- **Tools:** `read, grep, find, ls, write, edit` (add `bash` only if it
  must run generators).
- **Model:** inherit.
- **Contract:** files changed, what was documented, and any source-code
  claims it could not verify.
- **Best for:** keeping docs in sync; drafting from scratch.

### refactor / migration specialist — mechanical multi-file change

- **Purpose:** apply a well-defined transformation across many files
  (rename an API, migrate to a new library).
- **Tools:** full set.
- **Model:** inherit.
- **Contract:** the transformation applied, files changed, verification
  command run, and anything it could not transform safely (list them rather
  than forcing it).
- **Best for:** repetitive, pattern-driven changes where consistency matters.

### auditor — dependency, security, or config review

- **Purpose:** read-only audit of dependencies, secrets, CI, or config.
- **Tools:** `read, grep, find, ls, bash` (read-only commands).
- **Model:** inherit or strong.
- **Contract:** Findings by severity with exact locations, evidence, and a
  recommended action. No edits.
- **Best for:** periodic checks; "is anything dangerous in here" questions.

## Tool scoping

Apply least privilege. The parent's trust in an agent's output is partly a
function of how little it *can* do.

| Role | Default tool set |
|------|------------------|
| scout, planner | `read, grep, find, ls` |
| reviewer, auditor | `read, grep, find, ls, bash` (read-only usage stated in the prompt) |
| docs-writer, test-writer | read tools + `write, edit` (+ `bash` if it runs commands) |
| worker, migration | omit `tools` — full default |

Prefer omitting a mutating tool over adding an instruction not to use it;
instructions are best-effort, allowlists are structural.

## Model tiering

| Tier | When | How |
|------|------|-----|
| Inherit | Default. Quality should track the parent session. | Omit `model`. |
| Cheap/fast | High-volume, mechanical recon (scouts). | Set a small model id; omit if unsure. |
| Strong | Planning and review, where reasoning dominates. | Set a strong model id; omit if unsure. |

Never hardcode a model the project's provider cannot serve. When in doubt,
omit `model` — inherit-always works, a wrong model id breaks the agent.

## Output contracts

The parent model consumes the agent's final message. Unstructured prose
forces re-reading; a fixed contract makes handoff cheap. Give every agent
a small set of `##` headings it must fill, and tell it its output goes to an
agent that has **not** seen the files it explored. Keep contracts short —
three to five sections — and require exact `path:line` references where the
reader will act on them.

## Orchestration modes

The subagent tool supports three modes; design agents so they compose.

- **Single** `{ agent, task }` — one agent, one task.
- **Parallel** `{ tasks: [...] }` — independent tasks at once (concurrent).
- **Chain** `{ chain: [...] }` — sequential; each step's output replaces the
  `{previous}` placeholder in the next step's task.

Typical compositions:

- scout → planner → worker (understand, plan, implement)
- worker → reviewer → worker (implement, review, fix)
- N parallel scouts → one planner (map several areas at once)

Agents that follow the contracts above compose without extra glue. See
`references/workflow-prompts.md` to package a composition as a reusable
`/command`.

## Naming

- Lowercase-hyphenated, descriptive of the *role*, not the person:
  `test-writer`, `security-auditor`, `migration-runner`.
- Keep names unique within a scope. To specialize a personal agent for one
  repo, reuse the same name in `.pi/agents/` — the project file overrides
  the user file.

## Anti-patterns

- **Kitchen-sink roster.** Eight overlapping agents make routing worse and
  cost more than three sharp ones. Each agent must have a distinct trigger.
- **Duplicate roles.** Two agents that answer the same requests will be
  chosen inconsistently. Merge them or differentiate the trigger.
- **Mutating "reviewers".** A reviewer with `write`/`edit` and no
  instruction boundary will eventually "fix" things it was asked to judge.
- **Vague descriptions.** `"Helps with code"` never gets selected. Name the
  concrete tasks and inputs.
- **Hardcoded machine paths.** `/home/me/project/...` in a prompt breaks on
  every other machine. Use repo-relative paths.
- **Guessing commands.** Reference the project's real task runner
  (`pnpm test`, `make check`), discovered during project analysis — not an
  invented one.
- **No output contract.** The parent gets an essay and pays to re-read it.

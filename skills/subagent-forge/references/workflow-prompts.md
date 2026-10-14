# Workflow prompts

Agent files define *who* does the work. A workflow prompt defines *a
sequence* of them behind a single `/command`. Add one only when a
multi-agent composition is used repeatedly — otherwise the parent model can
just chain agents directly.

## Format

Workflow prompts are ordinary Markdown files with optional frontmatter:

```markdown
---
description: scout -> planner -> implement
---

Use a chain of subagents to implement: {request}

1. Run the `scout` agent to find everything relevant to {request}. Ask it
   for compressed findings with file paths and line ranges.
2. Pass those findings to the `planner` agent and ask for a concrete plan.
3. Pass the plan to a `worker` agent and implement it exactly.

Report the final result and a short summary of what changed.
```

The user's arguments are appended after the prompt body, so `{request}`
(and any placeholder you choose) is a documentation aid; the runner appends
the raw text.

## Locations

- User: `~/.pi/agent/prompts/*.md`
- Project: the project's prompts directory (see the host's settings), so a
  repo can ship its own standard workflows.

The filename becomes the command: `scout-and-plan.md` → `/scout-and-plan`.

## Chain placeholders

In chain mode the subagent tool substitutes `{previous}` with the prior
step's output. Use it to forward context explicitly:

```
chain: [
  { agent: "scout",   task: "Find the code relevant to: <request>" },
  { agent: "planner", task: "Using these findings:\n{previous}\n\nWrite a plan." },
  { agent: "worker",  task: "Implement this plan verbatim:\n{previous}" }
]
```

## Useful compositions

| Prompt | Flow | When |
|--------|------|------|
| `/scout-and-plan` | scout → planner | Understand and plan before committing to changes |
| `/implement` | scout → planner → worker | Nondeterministic change needing context + a plan |
| `/implement-and-review` | worker → reviewer → worker | Implement, then verify and fix |

## Guidelines

- Keep the prompt to the sequencing and the handoff contract; put role
  detail in the agent files, not the prompt.
- State the placeholder and what each step receives, so the parent passes
  context correctly.
- Prefer parallel scouts when the areas are independent, chain when each
  step depends on the previous output.
- Do not create a prompt for a composition you would use once — it is
  cheap to chain inline for a one-off.

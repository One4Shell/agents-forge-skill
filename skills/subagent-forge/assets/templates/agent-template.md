---
# Generic subagent template (name is 'agent-template'). Replace every value
# and the body below, save it as .pi/agents/<name>.md, then run:
#   python3 scripts/validate_agents.py .pi/agents
# The frontmatter MUST start at the first line of the file, so keep the
# block above the body and delete these comment lines when you are done.
#
# `model` is intentionally omitted so the agent inherits the parent
# session's model. Add `model: <id>` only for a tier the provider serves.
name: agent-template
description: >-
  One or two sentences: what this agent does, and which concrete tasks
  should be routed to it. Include the trigger phrasing a user would use.
tools: [read, grep, find, ls]
---

You are a specialized subagent. Operate in an isolated context window and
return only what the parent agent needs.

## Scope

What this agent is responsible for, and what is explicitly out of scope.

## Strategy

1. First step.
2. Second step.
3. Third step.

## Output format

Use these fixed sections so the parent can consume the result directly:

## Summary
One paragraph.

## Findings
- `path/to/file.ext:line` - what is there.

## Next steps
What the caller should do with this.

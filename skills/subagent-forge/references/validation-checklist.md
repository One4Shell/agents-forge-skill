# Validation checklist

Run `python3 scripts/validate_agents.py <dir>` first for the mechanical
checks, then walk this list by hand. The validator cannot judge whether an
agent is *worth having* — that part is on you.

## Description (the routing field)

- [ ] States what the agent does **and** which tasks should route to it
- [ ] Uses realistic trigger language a user might type, not just formal
      terminology
- [ ] Is narrow enough not to steal tasks from sibling agents
- [ ] Is not a duplicate of an existing agent's description (check with
      `scripts/list_agents.py`)
- [ ] Is valid YAML — quoted or a `>-` block if it contains `: `, `#`, or a
      leading quote

## System prompt (the body)

- [ ] Imperative and specific — states the agent's job, constraints, and
      output contract, not a general essay
- [ ] Tells the agent that its output is consumed by an agent that has not
      seen the files it explored (for scouts/recon agents)
- [ ] Gives file:line reference expectations where the reader will act on
      them
- [ ] References the project's **real** commands (test/lint/build) found
      during analysis, not invented ones
- [ ] Uses repo-relative paths only — no machine-specific absolute paths
- [ ] Tells a read-only agent to keep `bash` strictly read-only, if it has
      `bash` at all

## Configuration

- [ ] `name` is lowercase-hyphenated and unique within its scope
- [ ] `tools` is least-privilege for the role (see `references/agent-patterns.md`)
- [ ] Mutating agents are the only ones with `write`/`edit`
- [ ] `model` is either omitted (inherit) or a model the project's provider
      actually serves
- [ ] Project agents live in the right directory (`.pi/agents/` and/or
      `.claude/agents/`, at the intended level of the repo)

## Contract and composition

- [ ] Output contract has three to five fixed `##` sections
- [ ] The agent composes with the others in the roster (scout → planner →
      worker, worker → reviewer → worker) without extra glue
- [ ] Workflow prompts (if any) name the agents that exist and explain the
      handoff

## Testing

- [ ] Invoke the agent once with a realistic task via the subagent tool and
      confirm it is selected and returns the expected contract
- [ ] For a read-only agent, confirm it did not modify the working tree
- [ ] For agents meant to run in parallel, confirm two run concurrently
      without conflicting
- [ ] For project agents, confirm the invocation is allowed by the trust
      settings and (for trusted projects) `confirmProjectAgents: false`
      suppresses the repeat prompt

## Before finishing

- [ ] `scripts/validate_agents.py` passes with no errors
- [ ] No leftover placeholders (`TODO`, `<...>`) in the agent files
- [ ] The roster has a stated rationale (one line per agent) that you can
      show the user

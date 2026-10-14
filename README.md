# subagent-forge

Installs the **subagent-forge** agent skill into any project: `SKILL.md`,
the `references/` docs, `scripts/` helpers, and any bundled `assets/`.

Designs, scaffolds, and validates working project-scoped subagents (pi `.pi/agents` and Claude Code `.claude/agents`) for the current repository. It analyzes the project, picks a lean agent roster, writes valid agent Markdown, and lints it before you rely on it.

## What it does

Given a project, the skill walks an agent through:

1. Capturing intent and scope (project vs user-level, read-only vs mutating)
2. Analyzing the repo's stack, real test/lint/build commands, and existing agents
3. Choosing a roster from proven archetypes (scout, planner, reviewer, worker, test-writer, auditor)
4. Scaffolding each agent with a valid frontmatter block and a system prompt
5. Scoping tools to least privilege and choosing a model tier
6. Validating every agent file before finishing

Example requests it handles:

- "Create a reviewer subagent for this repo"
- "Add a scout + planner workflow to `.pi/agents`"
- "Set up project agents for our monorepo"
- "Turn this review checklist into a reusable agent"

### Bundled helpers

```bash
python3 scripts/new_agent.py --name scout --description "..." --tools "read, grep, find, ls"
python3 scripts/validate_agents.py .pi/agents
python3 scripts/list_agents.py --project .
```

Ready-made agent templates live in `assets/templates/`. See `SKILL.md`
for the full workflow and `references/` for the schema and patterns.

> **Prerequisite:** the file-based subagent runner (pi's
> `examples/extensions/subagent` extension or equivalent) must be installed
> and enabled, otherwise the generated `.pi/agents` files are inert.

## Install (recommended)

This repo follows the [Agent Skills specification](https://agentskills.io),
so it installs with a single command via [`npx skills`](https://github.com/vercel-labs/skills)
— no cloning, no config:

```bash
npx skills add https://github.com/One4Shell/subagent-forge-skill --skill subagent-forge
```

`npx skills` auto-detects which coding agents you have installed and copies
(or symlinks) the skill into the right directory for each — `.agents/skills/`
for OpenCode/Codex/Cursor/Amp, `.claude/skills/` for Claude Code, and so on.
Add `-a <agent>` to target a specific one, or `-g` to install globally
instead of per-project.

## Install (no npm required)

If you'd rather not depend on the `skills` CLI, use the plain shell
installer bundled in this repo instead:

```bash
curl -fsSL https://raw.githubusercontent.com/One4Shell/subagent-forge-skill/main/install.sh | bash
```

To pass options through the pipe, use `bash -s --`:

```bash
curl -fsSL https://raw.githubusercontent.com/One4Shell/subagent-forge-skill/main/install.sh | bash -s -- --claude
```

Or clone and run it locally (no network access needed at install time):

```bash
git clone https://github.com/One4Shell/subagent-forge-skill.git
cd subagent-forge
./install.sh --dir /path/to/your/project
```

### `install.sh` options

```
--dir <path>     Project root to install into (default: current directory)
--path <path>    Custom install path, relative to --dir
                  (default: .agents/skills/subagent-forge)
--claude         Shorthand for --path .claude/skills/subagent-forge
--force          Overwrite existing files (default: skip files that already exist)
-h, --help       Show help
```

Env vars (only used in the `curl | bash` case, i.e. no local checkout):

```
SUBAGENT_FORGE_REPO     GitHub "owner/repo" to fetch from (default: baked into install.sh)
SUBAGENT_FORGE_BRANCH   Branch/ref to fetch (default: main)
```

Either method never overwrites existing files unless `--force` is passed, so
it's safe to re-run.

## What gets installed

```
skills/subagent-forge/            # repo layout — also discoverable as .agents/skills/subagent-forge
├── SKILL.md                      # entry point the agent reads
├── scripts/                      # executable helpers, if any
├── references/                   # docs loaded into context as needed
└── assets/                       # files used in output, if any
```

## After installing

Point your agent at a project containing the skill and describe what you
need — it will pick up `SKILL.md` and follow its instructions from there.

## License

MIT

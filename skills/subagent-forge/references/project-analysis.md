# Analyzing the current project

Before creating a single agent, find out what the project actually is. An
agent roster that ignores the stack produces generic scouts and reviewers
that add cost without adding signal. Spend two minutes here; it pays for
itself in the quality of every agent you write.

Work read-only. Do not modify project files during analysis.

## 1. Detect the stack

Look for manifest and config files, then read the ones that exist:

| Signal | What it tells you |
|--------|-------------------|
| `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb` | Node/JS/TS project, package manager, scripts (test/lint/build/typecheck) |
| `tsconfig.json` | TypeScript, path aliases, strictness |
| `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile`, `uv.lock` | Python project and tooling (pytest, ruff, mypy, uv/poetry) |
| `go.mod` | Go modules and Go version |
| `Cargo.toml` | Rust crates and workspace layout |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | JVM (Maven/Gradle) |
| `Gemfile`, `composer.json` | Ruby / PHP |
| `Makefile`, `justfile`, `Taskfile.yml` | Canonical build/test/lint entry points |
| `Dockerfile`, `docker-compose.yml` | Containerized build/run workflow |
| `*.tf`, `serverless.yml`, `cdk.json` | Infrastructure-as-code |

Read the `scripts` block of `package.json`, or the equivalent task runner
targets. Those names (`npm test`, `pnpm lint`, `make check`) are what your
agents should reference instead of guessing commands.

## 2. Detect the test and quality setup

- Test directories and framework: `tests/`, `__tests__/`, `*_test.go`,
  `#[test]`, `pytest.ini`, `jest.config.*`, `vitest.config.*`.
- Linters/formatters: `.eslintrc*`, `ruff.toml`, `.prettierrc`, `golangci*`.
- Type checking: `tsc --noEmit`, `mypy`, `pyright`.
- CI: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `circleci`.

CI configs are the highest-signal source for "how does this project
officially check itself", because they list the exact commands that must
pass. An agent that runs those commands is immediately useful.

## 3. Detect layout and conventions

- Monorepo? `workspaces` in `package.json`, `pnpm-workspace.yaml`,
  `Cargo.toml` workspace, `apps/` + `packages/`, Nx/Turborepo config.
  In a monorepo, decide whether agents operate at the root or per package,
  and say which in each agent's prompt.
- Where does application code live (`src/`, `lib/`, `internal/`, `app/`)?
- Where do docs live (`docs/`, `README.md`, ADRs)?
- Existing conventions: `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`,
  `.editorconfig`, commit conventions.

Read the project's own `AGENTS.md`/`CLAUDE.md` if present — it may already
declare house rules your agents must follow.

## 4. Detect existing agents

Check for an existing roster before adding to it:

```bash
ls -la .pi/agents .claude/agents 2>/dev/null
python3 scripts/list_agents.py --project .   # after installing this skill
```

Do not duplicate an agent that already exists under the same name — either
edit it or pick a distinct name/role. Note existing conventions (naming,
output format, tool scoping) so new agents fit in.

## 5. Turn findings into a roster rationale

Write a short rationale before scaffolding anything. For each agent you
intend to create, answer:

1. **What trigger/task** will the parent model route to this agent, and why
   can't the parent just do it inline? (Isolated context, parallelism,
   read-only safety, or a specialized output contract.)
2. **What does it need to read** (files, commands, CI config)?
3. **Will it write**, or is it strictly read-only?
4. **What output contract** will the parent consume? (Fixed headings.)
5. **Which model tier** and why (inherit, cheap, or strong)?

If you cannot answer all five crisply, the agent is not ready to scaffold.
Prefer three sharp agents over eight vague ones — every agent adds a
routing decision for the parent and maintenance for the team.

## Quick recon command block

A read-only sweep you can adapt (adjust for the project's languages):

```bash
# Manifests and task runners
ls package.json pyproject.toml go.mod Cargo.toml Makefile justfile 2>/dev/null
# CI and quality config
find . -maxdepth 3 \( -path ./.git -o -path ./node_modules \) -prune -o \
  \( -name '*.yml' -path '*workflows*' -o -name '.eslintrc*' \
     -o -name 'ruff.toml' -o -name 'pytest.ini' -o -name 'vitest.config.*' \) -print
# Existing agents and house rules
ls .pi/agents .claude/agents AGENTS.md CLAUDE.md CONTRIBUTING.md 2>/dev/null
```

Then read the two or three highest-signal files in full (CI workflow, task
runner, main manifest) rather than skimming everything.

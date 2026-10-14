#!/usr/bin/env python3
"""new_agent.py - scaffold a subagent Markdown file with valid frontmatter.

Writes a subagent definition (YAML frontmatter + system-prompt body) into
one or more agent directories, refusing to overwrite an existing file
unless --force is passed. The description is single-quoted so it stays
valid YAML even when it contains ': ', '#' or quotes.

Usage:
    python3 new_agent.py --name test-writer --description "Writes tests ..." \
        [--tools "read, grep, find, ls, write, edit, bash"] \
        [--model claude-sonnet-4-5] \
        [--targets pi,claude] [--dir <project-root>] \
        [--body-file path/to/prompt.md] [--force]

Targets:
    pi      -> <dir>/.pi/agents/<name>.md      (default)
    claude  -> <dir>/.claude/agents/<name>.md
    user    -> ~/.pi/agent/agents/<name>.md

Exits non-zero on invalid input or on a refused overwrite.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

STARTER_BODY = """You are a {name} subagent. {description}

## Scope

TODO: what this agent is responsible for, and what is explicitly out of scope.

## Strategy

1. TODO: first step.
2. TODO: second step.
3. TODO: third step.

## Output format

TODO: three to five fixed '##' sections the parent agent can consume,
with exact `path:line` references where useful.
"""


def yaml_single_quote(value: str) -> str:
    """Return `value` wrapped in single quotes, YAML-safe."""
    return "'" + value.replace("'", "''") + "'"


def resolve_target_dir(target: str, project_root: Path) -> Path:
    if target == "pi":
        return project_root / ".pi" / "agents"
    if target == "claude":
        return project_root / ".claude" / "agents"
    if target == "user":
        return Path(os.environ.get("PI_AGENT_DIR", Path.home() / ".pi" / "agent")) / "agents"
    raise ValueError(f"unknown target '{target}' (expected pi, claude or user)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="agent name, lowercase-hyphenated")
    ap.add_argument("--description", required=True, help="routing description shown to the parent model")
    ap.add_argument("--tools", default=None, help="comma-separated tool allowlist (omit to inherit all tools)")
    ap.add_argument("--model", default=None, help="model id (omit to inherit the parent session's model)")
    ap.add_argument("--targets", default="pi", help="comma-separated: pi,claude,user (default: pi)")
    ap.add_argument("--dir", default=".", help="project root for pi/claude targets (default: cwd)")
    ap.add_argument("--body-file", default=None, help="file containing the system prompt body")
    ap.add_argument("--force", action="store_true", help="overwrite existing agent files")
    args = ap.parse_args()

    if not NAME_RE.match(args.name):
        print(
            f"Error: name '{args.name}' is not lowercase-hyphenated "
            "(expected a pattern like 'test-writer')",
            file=sys.stderr,
        )
        return 1

    project_root = Path(args.dir).expanduser().resolve()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    if not targets:
        print("Error: --targets must name at least one of pi, claude, user", file=sys.stderr)
        return 1

    tools = None
    if args.tools:
        tools = [t.strip() for t in args.tools.split(",") if t.strip()]
        if not tools:
            print("Error: --tools was given but parsed to an empty list", file=sys.stderr)
            return 1

    if args.body_file:
        body_path = Path(args.body_file).expanduser()
        if not body_path.is_file():
            print(f"Error: --body-file '{body_path}' does not exist", file=sys.stderr)
            return 1
        body = body_path.read_text(encoding="utf-8").rstrip() + "\n"
    else:
        body = STARTER_BODY.format(name=args.name, description=args.description)

    fm_lines = ["---", f"name: {args.name}", f"description: {yaml_single_quote(args.description)}"]
    if tools:
        fm_lines.append("tools: [" + ", ".join(tools) + "]")
    if args.model:
        fm_lines.append(f"model: {args.model}")
    fm_lines.append("---")
    content = "\n".join(fm_lines) + "\n\n" + body

    written: list[Path] = []
    skipped: list[Path] = []
    for target in targets:
        try:
            target_dir = resolve_target_dir(target, project_root)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        out = target_dir / f"{args.name}.md"
        if out.exists() and not args.force:
            skipped.append(out)
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        written.append(out)

    for p in written:
        print(f"wrote: {p}")
    for p in skipped:
        print(f"skip (exists, use --force): {p}")

    if not written:
        print("Nothing written.", file=sys.stderr)
        return 1

    print("\nNext steps:")
    print(f"  1. Edit the system prompt in: {written[0]}")
    print(f"  2. Validate: python3 scripts/validate_agents.py {written[0].parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

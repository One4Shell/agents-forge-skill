#!/usr/bin/env python3
"""validate_agents.py - lint subagent Markdown files.

Checks frontmatter parses, required fields are present, names are valid and
unique, tools/models are well-formed, the body is non-empty, and read-only
roles are not granted mutating tools. Exits non-zero on errors.

Usage:
    python3 validate_agents.py [path ...] [--project <dir>] [--user]

With no paths and no flags, validates agents under ~/.pi/agent/agents and
the nearest .pi/agents / .claude/agents directories starting at the current
working directory.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # PyYAML optional; naive fallback below
    yaml = None

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)

KNOWN_TOOLS = {"read", "grep", "find", "ls", "bash", "edit", "write", "glob", "webfetch", "websearch", "task"}
MUTATING_TOOLS = {"write", "edit"}
READONLY_ROLE_HINTS = (
    "scout", "review", "planner", "plan", "audit", "auditor", "recon",
    "analy", "inspect", "explore",
)

FIELD_ERROR = "\0"


class FrontmatterError(ValueError):
    pass


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    raw_fm, body = m.group(1), m.group(2)
    if yaml is not None:
        try:
            loaded = yaml.safe_load(raw_fm)
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            loc = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
            raise FrontmatterError(f"frontmatter is not valid YAML{loc}: {exc}") from exc
        if loaded is None:
            return {}, body
        if not isinstance(loaded, dict):
            raise FrontmatterError(f"frontmatter must be a mapping (got {type(loaded).__name__})")
        return loaded, body
    fields: dict[str, object] = {}
    for line in raw_fm.splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields, body


def parse_tools(value) -> tuple[list[str], str | None]:
    """Return (tools, error). Accepts a list, a CSV string, or a bracketed CSV string."""
    if value is None:
        return [], None
    if isinstance(value, list):
        raw = [str(v) for v in value]
    elif isinstance(value, str):
        s = value.strip()
        if s.startswith("[") and s.endswith("]"):
            s = s[1:-1]
        raw = s.split(",")
    else:
        return [], f"tools must be a list or comma-separated string (got {type(value).__name__})"
    tools = [t.strip() for t in raw if t.strip()]
    return tools, None


def mirror_key(path: Path) -> str:
    """Collapse the .pi/.claude host segment so mirror pairs compare equal."""
    s = path.resolve().as_posix()
    return s.replace("/.pi/agents/", "/.host/agents/").replace("/.claude/agents/", "/.host/agents/")


def discover_dirs(project_root: Path, include_user: bool) -> list[Path]:
    dirs: list[Path] = []
    if include_user:
        dirs.append(Path(os.environ.get("PI_AGENT_DIR", Path.home() / ".pi" / "agent")) / "agents")
    current = project_root.resolve()
    while True:
        for sub in (Path(".pi") / "agents", Path(".claude") / "agents"):
            candidate = current / sub
            if candidate.is_dir():
                dirs.append(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent
    # de-duplicate, preserve order
    seen: set[Path] = set()
    out: list[Path] = []
    for d in dirs:
        rd = d.resolve()
        if rd not in seen:
            seen.add(rd)
            out.append(d)
    return out


def collect_files(paths: list[str], project_root: Path, include_user: bool) -> list[Path]:
    if paths:
        files: list[Path] = []
        for p in paths:
            path = Path(p).expanduser()
            if path.is_dir():
                files.extend(sorted(path.glob("*.md")))
            elif path.is_file():
                files.append(path)
            else:
                print(f"Warning: '{p}' is not a file or directory", file=sys.stderr)
        return files
    files = []
    for d in discover_dirs(project_root, include_user):
        files.extend(sorted(d.glob("*.md")))
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="agent files or directories to validate")
    ap.add_argument("--project", default=".", help="project root used for discovery (default: cwd)")
    ap.add_argument("--user", action="store_true", help="also include ~/.pi/agent/agents in discovery")
    args = ap.parse_args()

    files = collect_files(args.paths, Path(args.project), args.user)
    if not files:
        print("No agent files found to validate.")
        return 0

    errors: list[str] = []
    warnings: list[str] = []
    seen_in_dir: dict[tuple[Path, str], Path] = {}
    seen_anywhere: dict[str, Path] = {}

    for f in files:
        rel = f
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{rel}: cannot read ({exc})")
            continue

        try:
            fm, body = parse_frontmatter(text)
        except FrontmatterError as exc:
            errors.append(f"{rel}: {exc}")
            errors.append(f"{rel}: hint: quote the description or use a '>-' block scalar if it contains ': ', '#' or quotes")
            continue

        if fm is None:
            errors.append(f"{rel}: missing '---' YAML frontmatter block")
            continue

        name = fm.get("name")
        description = fm.get("description")
        model = fm.get("model")

        if not isinstance(name, str) or not name.strip():
            errors.append(f"{rel}: missing or non-string 'name'")
            name = None
        elif not NAME_RE.match(name):
            warnings.append(f"{rel}: name '{name}' is not lowercase-hyphenated")

        if not isinstance(description, str) or not description.strip():
            errors.append(f"{rel}: missing or non-string 'description'")
            description = ""
        else:
            low = description.lower()
            if "use" not in low and "when" not in low:
                warnings.append(f"{rel}: description does not state when to route to this agent (no 'use'/'when')")

        if model is not None and not isinstance(model, str):
            errors.append(f"{rel}: 'model' must be a string (got {type(model).__name__})")

        tools, terr = parse_tools(fm.get("tools"))
        if terr:
            errors.append(f"{rel}: {terr}")
        for t in tools:
            if t not in KNOWN_TOOLS:
                warnings.append(f"{rel}: unrecognized tool '{t}' (known: {', '.join(sorted(KNOWN_TOOLS))})")

        role_text = f"{(name or '').lower()} {description.lower()}"
        if any(h in role_text for h in READONLY_ROLE_HINTS):
            offending = sorted(set(tools) & MUTATING_TOOLS)
            if offending:
                warnings.append(
                    f"{rel}: role looks read-only but declares mutating tool(s): {', '.join(offending)}"
                )

        if not body.strip():
            errors.append(f"{rel}: system-prompt body is empty")
        elif len(body.strip()) < 40:
            warnings.append(f"{rel}: body is very short ({len(body.strip())} chars) — is it a real system prompt?")

        if name:
            dir_key = (f.parent.resolve(), name)
            if dir_key in seen_in_dir:
                errors.append(
                    f"{rel}: two files in the same directory declare name '{name}' "
                    f"(also in {seen_in_dir[dir_key]})"
                )
            else:
                seen_in_dir[dir_key] = rel
            if name in seen_anywhere:
                if mirror_key(f) != mirror_key(seen_anywhere[name]):
                    warnings.append(
                        f"{rel}: name '{name}' is also declared in {seen_anywhere[name]} "
                        "- rename one unless they are intentional mirrors"
                    )
            else:
                seen_anywhere[name] = rel
            if f.stem != name:
                warnings.append(f"{rel}: filename '{f.stem}.md' does not match name '{name}'")

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    if not errors and not warnings:
        print(f"OK - {len(files)} agent file(s) validated, no issues found.")
    elif not errors:
        print(f"\nNo blocking errors across {len(files)} agent file(s), but review the warnings above.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

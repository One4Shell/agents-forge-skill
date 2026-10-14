#!/usr/bin/env python3
"""list_agents.py - list discovered subagents and their precedence.

Shows user-level and project-level agents, which source wins on a name
collision, and each agent's tools and model. Read-only; safe to run any
time to sanity-check a roster.

Usage:
    python3 list_agents.py [--project <dir>] [--no-user] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    raw_fm = m.group(1)
    if yaml is not None:
        try:
            loaded = yaml.safe_load(raw_fm)
            return loaded if isinstance(loaded, dict) else {}
        except yaml.YAMLError:
            return {}
    fields: dict[str, object] = {}
    for line in raw_fm.splitlines():
        if ":" in line and not line.strip().startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def parse_tools(value) -> str:
    if value is None:
        return "(all)"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    s = str(value).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return ", ".join(parts) if parts else "(none)"


def load_dir(directory: Path, source: str, host: str) -> list[dict]:
    agents: list[dict] = []
    if not directory.is_dir():
        return agents
    for f in sorted(directory.glob("*.md")):
        try:
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        except OSError:
            continue
        name = fm.get("name")
        if not isinstance(name, str) or not name:
            continue
        agents.append(
            {
                "name": name,
                "source": source,
                "host": host,
                "tools": parse_tools(fm.get("tools")),
                "model": fm.get("model") or "(inherit)",
                "description": str(fm.get("description", "")).strip(),
                "path": str(f),
            }
        )
    return agents


def find_project_dirs(root: Path) -> list[Path]:
    dirs: list[Path] = []
    current = root.resolve()
    while True:
        for sub in (Path(".pi") / "agents", Path(".claude") / "agents"):
            candidate = current / sub
            if candidate.is_dir():
                dirs.append(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return dirs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".", help="project root for discovery (default: cwd)")
    ap.add_argument("--no-user", action="store_true", help="exclude ~/.pi/agent/agents")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    entries: list[dict] = []
    if not args.no_user:
        user_dir = Path(os.environ.get("PI_AGENT_DIR", Path.home() / ".pi" / "agent")) / "agents"
        entries.extend(load_dir(user_dir, "user", "pi"))

    # `.pi` and `.claude` are parallel host conventions (pi vs Claude Code),
    # so they never override each other. Within one host, the nearest project
    # directory wins over a farther one and over the user directory.
    project_dirs = list(reversed(find_project_dirs(Path(args.project))))
    for d in project_dirs:
        host = "claude" if d.parent.name == ".claude" else "pi"
        entries.extend(load_dir(d, "project", host))

    resolved: dict[tuple[str, str], dict] = {}
    for e in entries:
        key = (e["host"], e["name"])
        if key in resolved:
            e["overridden"] = resolved[key]["path"]
        resolved[key] = e
    final = list(resolved.values())

    if args.json:
        print(json.dumps(final, indent=2, ensure_ascii=False))
        return 0

    if not final:
        print("No agents found.")
        return 0

    name_w = max(len(a["name"]) for a in final) + 2
    print(f"{'NAME':<{name_w}}{'HOST':<8}{'SOURCE':<10}{'MODEL':<20}TOOLS")
    print("-" * (name_w + 46))
    for a in sorted(final, key=lambda x: (x["name"], x["host"])):
        print(f"{a['name']:<{name_w}}{a['host']:<8}{a['source']:<10}{a['model']:<20}{a['tools']}")
        if a.get("overridden"):
            print(f"{'':<{name_w}}  (overrides same-host agent at {a['overridden']})")

    print(f"\n{len(final)} agent(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

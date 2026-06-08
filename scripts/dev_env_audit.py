#!/usr/bin/env python3
"""Audit local developer tooling and project hygiene without external dependencies."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path


DEFAULT_TOOLS = [
    "bash",
    "zsh",
    "git",
    "python3",
    "node",
    "npm",
    "npx",
    "docker",
    "code",
    "rg",
    "jq",
    "curl",
    "ssh",
]


@dataclass
class ToolResult:
    name: str
    found: bool
    path: str | None = None
    version: str | None = None


def run_version(command: str) -> str | None:
    candidates = ([command, "--version"], [command, "-V"], [command, "version"])
    for candidate in candidates:
        try:
            result = subprocess.run(candidate, check=False, capture_output=True, text=True, timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode != 0:
            continue
        output = (result.stdout or result.stderr).strip().splitlines()
        if output:
            return output[0][:160]
    return None


def audit_tools(tools: list[str]) -> list[ToolResult]:
    results: list[ToolResult] = []
    for tool in tools:
        path = shutil.which(tool)
        results.append(ToolResult(name=tool, found=path is not None, path=path, version=run_version(tool) if path else None))
    return results


def discover_projects(roots: list[Path]) -> list[dict[str, str | int | bool]]:
    projects: list[dict[str, str | int | bool]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for git_dir in sorted(root.glob("*/.git")):
            repo = git_dir.parent
            dirty_count = 0
            branch = "unknown"
            valid = True
            try:
                repo_check = subprocess.run(
                    ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if repo_check.returncode != 0:
                    projects.append({"path": str(repo), "branch": "invalid-git-metadata", "dirty_files": 0, "valid": False})
                    continue
                branch = subprocess.run(
                    ["git", "-C", str(repo), "branch", "--show-current"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                ).stdout.strip() or "detached-or-unknown"
                status = subprocess.run(
                    ["git", "-C", str(repo), "status", "--porcelain"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                ).stdout.splitlines()
                dirty_count = len(status)
            except subprocess.TimeoutExpired:
                branch = "git-timeout"
                valid = False
            projects.append({"path": str(repo), "branch": branch, "dirty_files": dirty_count, "valid": valid})
    return projects


def print_table(results: list[ToolResult]) -> None:
    print("Developer Environment Audit")
    print(f"Generated: {subprocess.run(['date', '--iso-8601=seconds'], check=False, capture_output=True, text=True).stdout.strip()}")
    print()
    print("## Tools")
    for result in results:
        status = "OK" if result.found else "MISSING"
        version = f" | {result.version}" if result.version else ""
        path = result.path or "-"
        print(f"[{status}] {result.name:<10} {path}{version}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--tool", action="append", dest="tools", help="Tool to check. Can be repeated.")
    parser.add_argument(
        "--project-root",
        action="append",
        type=Path,
        default=[],
        help="Project root to scan one level deep for Git repositories.",
    )
    args = parser.parse_args()

    tools = args.tools if args.tools else DEFAULT_TOOLS
    roots = [path.expanduser() for path in args.project_root] or [Path.home() / "CodingProjects", Path.home() / "Projects"]
    tool_results = audit_tools(tools)
    projects = discover_projects(roots)

    if args.json:
        print(json.dumps({"tools": [asdict(result) for result in tool_results], "projects": projects}, indent=2))
        return

    print_table(tool_results)
    print()
    print("## Project Snapshot")
    if not projects:
        print("No Git repositories found in configured roots.")
    for project in projects:
        if not project.get("valid", True):
            state = "INVALID"
        else:
            state = "DIRTY" if project["dirty_files"] else "CLEAN"
        print(f"[{state}] {project['path']} | branch={project['branch']} | dirty_files={project['dirty_files']}")

    missing = [result.name for result in tool_results if not result.found]
    print()
    print("## Summary")
    print(f"Tools checked: {len(tool_results)}")
    print(f"Missing tools: {', '.join(missing) if missing else 'none'}")
    print(f"Git repositories found: {len(projects)}")


if __name__ == "__main__":
    os.environ.setdefault("LC_ALL", "C")
    main()

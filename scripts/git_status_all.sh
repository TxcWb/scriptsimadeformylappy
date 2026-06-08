#!/usr/bin/env bash
set -euo pipefail

roots=("$@")
if [[ ${#roots[@]} -eq 0 ]]; then
  roots=("$HOME/CodingProjects" "$HOME/Projects")
fi

printf 'Git Status Scan\n'
printf 'Generated: %s\n' "$(date --iso-8601=seconds)"

for root in "${roots[@]}"; do
  [[ -d "$root" ]] || continue
  printf '\n## %s\n' "$root"

  while IFS= read -r git_dir; do
    repo="$(dirname "$git_dir")"
    if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      printf '[INVALID] %s | .git metadata is not usable\n' "$repo"
      continue
    fi

    branch="$(git -C "$repo" branch --show-current 2>/dev/null || true)"
    [[ -n "$branch" ]] || branch="detached-or-unknown"

    porcelain="$(git -C "$repo" status --porcelain 2>/dev/null || true)"
    if [[ -n "$porcelain" ]]; then
      changed_count="$(printf '%s\n' "$porcelain" | wc -l)"
      printf '[DIRTY] %s | branch=%s | changes=%s\n' "$repo" "$branch" "$changed_count"
    else
      printf '[CLEAN] %s | branch=%s\n' "$repo" "$branch"
    fi
  done < <(find "$root" -type d -name .git -prune 2>/dev/null | sort)
done

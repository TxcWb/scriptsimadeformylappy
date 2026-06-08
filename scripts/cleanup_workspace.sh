#!/usr/bin/env bash
set -euo pipefail

mode="dry-run"
if [[ "${1:-}" == "--apply" ]]; then
  mode="apply"
elif [[ "${1:-}" == "--dry-run" || -z "${1:-}" ]]; then
  mode="dry-run"
else
  printf 'Usage: %s [--dry-run|--apply]\n' "$(basename "$0")" >&2
  exit 2
fi

candidates=(
  "$HOME/.cache/thumbnails"
  "$HOME/.cache/mozilla"
  "$HOME/.npm/_cacache"
)

printf 'Workspace Cleanup (%s)\n' "$mode"
printf 'Generated: %s\n' "$(date --iso-8601=seconds)"

for path in "${candidates[@]}"; do
  if [[ ! -e "$path" ]]; then
    printf '[SKIP] Missing: %s\n' "$path"
    continue
  fi

  size="$(du -sh "$path" 2>/dev/null | awk '{print $1}')"
  if [[ "$mode" == "dry-run" ]]; then
    printf '[DRY-RUN] Would remove %s (%s)\n' "$path" "$size"
  else
    printf '[REMOVE] %s (%s)\n' "$path" "$size"
    rm -rf --one-file-system "$path"
  fi
done


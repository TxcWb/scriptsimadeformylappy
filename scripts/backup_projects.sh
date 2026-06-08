#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/backups"
mkdir -p "$BACKUP_DIR"

usage() {
  printf 'Usage: %s [source_dir ...]\n' "$(basename "$0")"
  printf 'Example: %s "$HOME/CodingProjects" "$HOME/Projects"\n' "$(basename "$0")"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

sources=("$@")
if [[ ${#sources[@]} -eq 0 ]]; then
  sources=("$HOME/CodingProjects" "$HOME/Projects")
fi

timestamp="$(date +%Y%m%d_%H%M%S)"

for source in "${sources[@]}"; do
  if [[ ! -d "$source" ]]; then
    printf '[SKIP] Not a directory: %s\n' "$source"
    continue
  fi

  name="$(basename "$source")"
  archive="$BACKUP_DIR/${name}_$timestamp.tar.gz"
  printf '[BACKUP] %s -> %s\n' "$source" "$archive"
  tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='.next' \
    --exclude='target' \
    -czf "$archive" -C "$(dirname "$source")" "$name"
done

printf 'Backup complete. Directory: %s\n' "$BACKUP_DIR"


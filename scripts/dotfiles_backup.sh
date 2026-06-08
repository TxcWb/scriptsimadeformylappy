#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/backups"
mkdir -p "$BACKUP_DIR"

usage() {
  printf 'Usage: %s [--dry-run|--apply] [path ...]\n' "$(basename "$0")"
  printf 'Creates a timestamped archive of selected dotfiles and writes a SHA-256 manifest.\n'
}

mode="dry-run"
if [[ "${1:-}" == "--apply" ]]; then
  mode="apply"
  shift
elif [[ "${1:-}" == "--dry-run" ]]; then
  shift
elif [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

items=("$@")
if [[ ${#items[@]} -eq 0 ]]; then
  items=(
    "$HOME/.zshrc"
    "$HOME/.bashrc"
    "$HOME/.gitconfig"
    "$HOME/.ssh/config"
    "$HOME/.config/Code/User/settings.json"
    "$HOME/.config/Code/User/keybindings.json"
  )
fi

timestamp="$(date +%Y%m%d_%H%M%S)"
staging_dir="$BACKUP_DIR/dotfiles_$timestamp"
archive="$BACKUP_DIR/dotfiles_$timestamp.tar.gz"
manifest="$BACKUP_DIR/dotfiles_$timestamp.sha256"

printf 'Dotfiles Backup (%s)\n' "$mode"
printf 'Generated: %s\n' "$(date --iso-8601=seconds)"

included=()
for item in "${items[@]}"; do
  expanded="${item/#\~/$HOME}"
  if [[ -e "$expanded" ]]; then
    included+=("$expanded")
    printf '[INCLUDE] %s\n' "$expanded"
  else
    printf '[SKIP] Missing: %s\n' "$expanded"
  fi
done

if [[ ${#included[@]} -eq 0 ]]; then
  printf 'No files found to back up.\n'
  exit 0
fi

if [[ "$mode" == "dry-run" ]]; then
  printf 'Would create: %s\n' "$archive"
  printf 'Would create: %s\n' "$manifest"
  exit 0
fi

mkdir -p "$staging_dir"
for source in "${included[@]}"; do
  relative="${source#$HOME/}"
  destination="$staging_dir/$relative"
  mkdir -p "$(dirname "$destination")"
  cp -a "$source" "$destination"
done

(
  cd "$staging_dir"
  find . -type f -print0 | sort -z | xargs -0 sha256sum > "$manifest"
)

tar -czf "$archive" -C "$BACKUP_DIR" "$(basename "$staging_dir")"
rm -rf -- "$staging_dir"

printf 'Archive written: %s\n' "$archive"
printf 'Manifest written: %s\n' "$manifest"

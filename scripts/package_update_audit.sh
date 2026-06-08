#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s [--summary|--full]\n' "$(basename "$0")"
  printf 'Audits available package updates without installing anything.\n'
}

mode="summary"
case "${1:-}" in
  ""|--summary) mode="summary" ;;
  --full) mode="full" ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

section() {
  printf '\n## %s\n' "$1"
}

count_lines() {
  sed '/^[[:space:]]*$/d' | wc -l
}

printf 'Package Update Audit\n'
printf 'Generated: %s\n' "$(date --iso-8601=seconds)"
printf 'Mode: %s\n' "$mode"

section "Native Package Manager"
if command -v apt >/dev/null 2>&1; then
  printf 'Detected: apt\n'
  updates="$(apt list --upgradable 2>/dev/null | sed '1d' || true)"
  printf 'Upgradable packages: %s\n' "$(printf '%s\n' "$updates" | count_lines)"
  [[ "$mode" == "full" && -n "$updates" ]] && printf '%s\n' "$updates"
elif command -v dnf >/dev/null 2>&1; then
  printf 'Detected: dnf\n'
  if dnf check-update >/tmp/package_update_audit_dnf.txt 2>/dev/null; then
    updates=""
  else
    updates="$(grep -E '^[A-Za-z0-9_.+-]+[[:space:]]' /tmp/package_update_audit_dnf.txt || true)"
  fi
  printf 'Upgradable packages: %s\n' "$(printf '%s\n' "$updates" | count_lines)"
  [[ "$mode" == "full" && -n "$updates" ]] && printf '%s\n' "$updates"
elif command -v pacman >/dev/null 2>&1; then
  printf 'Detected: pacman\n'
  if command -v checkupdates >/dev/null 2>&1; then
    updates="$(checkupdates 2>/dev/null || true)"
    printf 'Upgradable packages: %s\n' "$(printf '%s\n' "$updates" | count_lines)"
    [[ "$mode" == "full" && -n "$updates" ]] && printf '%s\n' "$updates"
  else
    printf 'Install pacman-contrib for non-invasive update counts via checkupdates\n'
  fi
else
  printf 'No supported native package manager detected\n'
fi

section "Flatpak"
if command -v flatpak >/dev/null 2>&1; then
  flatpak remote-ls --updates 2>/dev/null || printf 'No Flatpak updates or remote unavailable\n'
else
  printf 'flatpak not installed\n'
fi

section "Snap"
if command -v snap >/dev/null 2>&1; then
  snap refresh --list 2>/dev/null || printf 'No Snap updates or snapd unavailable\n'
else
  printf 'snap not installed\n'
fi

section "Firmware"
if command -v fwupdmgr >/dev/null 2>&1; then
  fwupdmgr get-updates 2>/dev/null || printf 'No firmware update data available\n'
else
  printf 'fwupdmgr not installed\n'
fi

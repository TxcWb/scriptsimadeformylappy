#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORT_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
report_file="$REPORT_DIR/system_report_$timestamp.txt"

section() {
  printf '\n## %s\n' "$1"
}

{
  printf 'System Report\n'
  printf 'Generated: %s\n' "$(date --iso-8601=seconds)"
  printf 'Host: %s\n' "$(hostname 2>/dev/null || uname -n)"
  printf 'User: %s\n' "$USER"

  section "OS"
  if [[ -r /etc/os-release ]]; then
    grep -E '^(PRETTY_NAME|NAME|VERSION)=' /etc/os-release | sed 's/"//g'
  else
    uname -a
  fi

  section "Kernel"
  uname -a

  section "Uptime"
  uptime

  section "CPU"
  if command -v lscpu >/dev/null 2>&1; then
    lscpu | grep -E '^(Model name|CPU\\(s\\)|Thread|Core|Socket)'
  else
    printf 'lscpu not available\n'
  fi

  section "Memory"
  free -h

  section "Disk"
  df -h --output=source,fstype,size,used,avail,pcent,target | sed 1q
  df -h --output=source,fstype,size,used,avail,pcent,target | grep -E '^/dev|^Filesystem' || true

  section "Largest Home Directories"
  du -h --max-depth=1 "$HOME" 2>/dev/null | sort -hr | head -20

  section "Failed systemd User Units"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user --failed --no-pager 2>/dev/null || printf 'No user systemd status available\n'
  else
    printf 'systemctl not available\n'
  fi

  section "Top Processes By Memory"
  ps -eo pid,ppid,comm,%mem,%cpu --sort=-%mem | head -15
} > "$report_file"

printf 'System report written: %s\n' "$report_file"

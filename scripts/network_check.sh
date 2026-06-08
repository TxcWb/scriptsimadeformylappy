#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 0 ]]; then
  endpoints=("$@")
else
  endpoints=("github.com" "google.com" "cloudflare.com")
fi

section() {
  printf '\n## %s\n' "$1"
}

printf 'Network Check\n'
printf 'Generated: %s\n' "$(date --iso-8601=seconds)"

section "Interfaces"
if command -v ip >/dev/null 2>&1; then
  ip -brief address 2>/dev/null || printf 'Interface details unavailable in this environment\n'
else
  printf 'ip command not available\n'
fi

section "Default Route"
if command -v ip >/dev/null 2>&1; then
  ip route 2>/dev/null | grep '^default' || printf 'No default route available in this environment\n'
fi

section "DNS Resolution"
for endpoint in "${endpoints[@]}"; do
  if getent hosts "$endpoint" >/dev/null; then
    printf '[OK] %s resolves\n' "$endpoint"
  else
    printf '[FAIL] %s does not resolve\n' "$endpoint"
  fi
done

section "Ping"
for endpoint in "${endpoints[@]}"; do
  if ping -c 2 -W 2 "$endpoint" >/dev/null 2>&1; then
    printf '[OK] %s reachable\n' "$endpoint"
  else
    printf '[WARN] %s not reachable by ping\n' "$endpoint"
  fi
done

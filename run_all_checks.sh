#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
log_file="$LOG_DIR/all_checks_$timestamp.log"

run_step() {
  local name="$1"
  shift
  {
    printf '\n===== %s =====\n' "$name"
    "$@"
  } 2>&1 | tee -a "$log_file"
}

run_step "System report" "$ROOT_DIR/scripts/system_report.sh"
run_step "Laptop health check" "$ROOT_DIR/scripts/laptop_health_check.sh"
run_step "Network check" "$ROOT_DIR/scripts/network_check.sh"
run_step "Developer environment audit" python3 "$ROOT_DIR/scripts/dev_env_audit.py"
run_step "Package update audit" "$ROOT_DIR/scripts/package_update_audit.sh" --summary
run_step "Git status scan" "$ROOT_DIR/scripts/git_status_all.sh" "$HOME/CodingProjects" "$HOME/Projects"

printf '\nCombined log: %s\n' "$log_file"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORT_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
report_file="$REPORT_DIR/laptop_health_$timestamp.txt"

section() {
  printf '\n## %s\n' "$1"
}

human_status() {
  local label="$1"
  local value="$2"
  printf '%-28s %s\n' "$label:" "$value"
}

battery_from_sysfs() {
  local found_battery="false"
  if compgen -G "/sys/class/power_supply/BAT*" >/dev/null; then
    for battery in /sys/class/power_supply/BAT*; do
      [[ -d "$battery" ]] || continue
      found_battery="true"
      human_status "Battery" "$(basename "$battery")"
      [[ -r "$battery/status" ]] && human_status "Status" "$(cat "$battery/status")"
      [[ -r "$battery/capacity" ]] && human_status "Charge" "$(cat "$battery/capacity")%"
      if [[ -r "$battery/energy_full" && -r "$battery/energy_full_design" ]]; then
        full="$(cat "$battery/energy_full")"
        design="$(cat "$battery/energy_full_design")"
        if [[ "$design" -gt 0 ]]; then
          awk -v full="$full" -v design="$design" 'BEGIN { printf "%-28s %.1f%%\n", "Estimated health:", (full / design) * 100 }'
        fi
      elif [[ -r "$battery/charge_full" && -r "$battery/charge_full_design" ]]; then
        full="$(cat "$battery/charge_full")"
        design="$(cat "$battery/charge_full_design")"
        if [[ "$design" -gt 0 ]]; then
          awk -v full="$full" -v design="$design" 'BEGIN { printf "%-28s %.1f%%\n", "Estimated health:", (full / design) * 100 }'
        fi
      fi
    done
  fi

  [[ "$found_battery" == "true" ]]
}

{
  printf 'Laptop Health Check\n'
  printf 'Generated: %s\n' "$(date --iso-8601=seconds)"
  printf 'Host: %s\n' "$(hostname 2>/dev/null || uname -n)"

  section "Battery"
  if command -v upower >/dev/null 2>&1; then
    battery_path="$(upower -e 2>/dev/null | grep -m1 'BAT' || true)"
    if [[ -n "$battery_path" ]]; then
      upower -i "$battery_path" | grep -E 'state:|percentage:|capacity:|energy-full:|energy-full-design:|time to empty:|time to full:' || true
    else
      battery_from_sysfs || printf 'No battery telemetry available\n'
    fi
  else
    battery_from_sysfs || printf 'Battery telemetry unavailable\n'
  fi

  section "Thermals"
  if command -v sensors >/dev/null 2>&1; then
    sensors
  else
    found_sensor="false"
    for zone in /sys/class/thermal/thermal_zone*; do
      [[ -r "$zone/temp" ]] || continue
      found_sensor="true"
      label="$(cat "$zone/type" 2>/dev/null || basename "$zone")"
      temp_milli="$(cat "$zone/temp")"
      awk -v label="$label" -v temp="$temp_milli" 'BEGIN { printf "%-28s %.1f C\n", label ":", temp / 1000 }'
    done
    [[ "$found_sensor" == "true" ]] || printf 'Thermal sensors unavailable\n'
  fi

  section "Disk Pressure"
  df -h --output=source,fstype,size,used,avail,pcent,target | sed 1q
  df -h --output=source,fstype,size,used,avail,pcent,target | grep -E '^/dev|^Filesystem' || true

  section "Block Devices"
  if command -v lsblk >/dev/null 2>&1; then
    lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL
  else
    printf 'lsblk not available\n'
  fi

  section "Recent Boot Errors"
  if command -v journalctl >/dev/null 2>&1; then
    journalctl -p warning..alert -b --no-pager -n 40 2>/dev/null || printf 'Journal access unavailable\n'
  else
    printf 'journalctl not available\n'
  fi
} > "$report_file"

printf 'Laptop health report written: %s\n' "$report_file"

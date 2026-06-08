#Compilation of Scripts that I Made for My Laptop!

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/system_report.sh` | Creates a timestamped system health report in `reports/`. |
| `scripts/laptop_health_check.sh` | Captures battery, thermal, disk, block-device, and recent boot warning data. |
| `scripts/network_check.sh` | Checks DNS, gateway reachability, and selected endpoints. |
| `scripts/package_update_audit.sh` | Summarizes available package, Flatpak, Snap, and firmware updates without installing anything. |
| `scripts/dev_env_audit.py` | Audits developer tools and produces a project Git hygiene snapshot. Supports JSON output. |
| `scripts/git_status_all.sh` | Scans project directories and summarizes Git repo status. |
| `scripts/backup_projects.sh` | Archives selected project folders into `backups/`. |
| `scripts/dotfiles_backup.sh` | Backs up selected shell, Git, SSH, and editor configuration with a checksum manifest. Defaults to dry-run. |
| `scripts/organize_downloads.py` | Sorts files from `Downloads` into type-based folders, renames them consistently, and can remove exact duplicates. Defaults to dry-run. |
| `scripts/screenshot_manager.py` | Renames screenshots with timestamps, files them by year/month, and can compress old screenshots. Defaults to dry-run. |
| `scripts/clipboard_history.py` | Saves clipboard text, searches local history, and imports/exports history through a shared sync folder. |
| `scripts/cleanup_workspace.sh` | Finds cache/temp candidates and optionally removes only approved paths. Defaults to dry-run. |
| `run_all_checks.sh` | Runs the report/check scripts together and writes a combined log. |

## Quick Start

```bash
cd ~/Projects/automation-engineering-toolkit
chmod +x scripts/*.sh run_all_checks.sh
./run_all_checks.sh
```

## Safe Operations

Scripts that move or remove files default to preview mode:

```bash
python3 scripts/organize_downloads.py --dry-run
python3 scripts/organize_downloads.py --delete-duplicates --apply

python3 scripts/screenshot_manager.py --dry-run
python3 scripts/screenshot_manager.py --archive-old --older-than-days 90 --apply

./scripts/cleanup_workspace.sh --dry-run
./scripts/cleanup_workspace.sh --apply

./scripts/dotfiles_backup.sh --dry-run
./scripts/dotfiles_backup.sh --apply
```

## Audit Examples

```bash
./scripts/laptop_health_check.sh
./scripts/package_update_audit.sh --summary
./scripts/package_update_audit.sh --full
python3 scripts/dev_env_audit.py
python3 scripts/dev_env_audit.py --json
```

## Productivity Automation

Downloads organizer:

```bash
python3 scripts/organize_downloads.py --downloads ~/Downloads --dry-run
python3 scripts/organize_downloads.py --downloads ~/Downloads --delete-duplicates --apply
```

Files are moved into folders such as `PDFs`, `Images`, `Videos`, `ZIPs`, and `Code`. Names are normalized as `YYYYMMDD_slug.ext`; use `--keep-names` to preserve original names.

Screenshot manager:

```bash
python3 scripts/screenshot_manager.py --source ~/Pictures --output ~/Pictures/Screenshots --dry-run
python3 scripts/screenshot_manager.py --source ~/Pictures --output ~/Pictures/Screenshots --archive-old --older-than-days 90 --apply
```

Screenshots are renamed as `screenshot_YYYYMMDD_HHMMSS.ext` and moved into `YEAR/MM-Month/`. Old screenshots can be compressed into `_archives/`; add `--delete-originals` only when you want originals removed after archiving.

Clipboard history:

```bash
python3 scripts/clipboard_history.py add
python3 scripts/clipboard_history.py watch
python3 scripts/clipboard_history.py search "invoice"
python3 scripts/clipboard_history.py sync-export --sync-dir ~/Dropbox/clipboard-sync
python3 scripts/clipboard_history.py sync-import --sync-dir ~/Dropbox/clipboard-sync
```

On Linux, clipboard capture needs one of `wl-paste`, `xclip`, or `xsel` available. Sync is file-based, so any shared folder provider can move the JSONL history across devices.


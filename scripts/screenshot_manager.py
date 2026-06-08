#!/usr/bin/env python3
"""Rename, file, and archive screenshots with dry-run by default."""

from __future__ import annotations

import argparse
import tarfile
from datetime import datetime, timedelta
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".heic"}
SCREENSHOT_MARKERS = ("screenshot", "screen shot", "screen_shot")


def is_screenshot(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and any(
        marker in path.stem.lower() for marker in SCREENSHOT_MARKERS
    )


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination

    counter = 1
    while True:
        candidate = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def destination_for(path: Path, output_dir: Path) -> Path:
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    month_dir = output_dir / modified.strftime("%Y") / modified.strftime("%m-%B")
    filename = f"screenshot_{modified.strftime('%Y%m%d_%H%M%S')}{path.suffix.lower()}"
    return unique_destination(month_dir / filename)


def organize_screenshots(source_dir: Path, output_dir: Path, apply: bool) -> int:
    count = 0
    for item in sorted(source_dir.iterdir()):
        if not is_screenshot(item):
            continue

        destination = destination_for(item, output_dir)
        relative_destination = destination.relative_to(output_dir)
        if apply:
            destination.parent.mkdir(parents=True, exist_ok=True)
            item.rename(destination)
            print(f"[MOVE] {item.name} -> {relative_destination}")
        else:
            print(f"[DRY-RUN] {item.name} -> {relative_destination}")
        count += 1
    return count


def archive_old_screenshots(output_dir: Path, older_than_days: int, apply: bool, delete_originals: bool) -> int:
    cutoff = datetime.now() - timedelta(days=older_than_days)
    candidates = [
        path
        for path in sorted(output_dir.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in IMAGE_SUFFIXES
        and datetime.fromtimestamp(path.stat().st_mtime) < cutoff
    ]
    if not candidates:
        return 0

    archive_dir = output_dir / "_archives"
    archive_name = f"screenshots_before_{cutoff.strftime('%Y%m%d')}.tar.gz"
    archive_path = archive_dir / archive_name

    if apply:
        archive_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "w:gz") as archive:
            for path in candidates:
                archive.add(path, arcname=path.relative_to(output_dir))
        if delete_originals:
            for path in candidates:
                path.unlink()
        print(f"[ARCHIVE] {len(candidates)} file(s) -> {archive_path}")
    else:
        print(f"[DRY-RUN] Would archive {len(candidates)} file(s) -> {archive_path}")
        if delete_originals:
            print("[DRY-RUN] Would delete originals after archive is written")
    return len(candidates)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home() / "Pictures", help="Directory to scan")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "Pictures" / "Screenshots",
        help="Managed screenshot library directory",
    )
    parser.add_argument("--apply", action="store_true", help="Rename, move, and archive files")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions. This is the default.")
    parser.add_argument("--archive-old", action="store_true", help="Compress old managed screenshots")
    parser.add_argument("--older-than-days", type=int, default=90, help="Age threshold for compression")
    parser.add_argument(
        "--delete-originals",
        action="store_true",
        help="Delete old screenshots after they are added to the archive. Requires --apply.",
    )
    args = parser.parse_args()

    source_dir = args.source.expanduser()
    output_dir = args.output.expanduser()
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")

    moved = organize_screenshots(source_dir, output_dir, apply=args.apply)
    archived = archive_old_screenshots(output_dir, args.older_than_days, args.apply, args.delete_originals) if args.archive_old else 0
    mode = "applied" if args.apply else "previewed"
    print(f"{mode.capitalize()} {moved} move(s), {archived} archive candidate(s).")


if __name__ == "__main__":
    main()

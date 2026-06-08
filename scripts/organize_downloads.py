#!/usr/bin/env python3
"""Organize Downloads into type-based folders with dry-run by default."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path


CATEGORIES = {
    "PDFs": {".pdf"},
    "Documents": {".doc", ".docx", ".odt", ".txt", ".rtf", ".md"},
    "Spreadsheets": {".csv", ".xls", ".xlsx", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".heic", ".avif"},
    "Videos": {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a", ".ogg"},
    "ZIPs": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Installers": {".exe", ".msi", ".deb", ".rpm", ".appimage", ".dmg", ".pkg"},
    "Code": {".c", ".cpp", ".h", ".java", ".js", ".ts", ".tsx", ".py", ".sql", ".html", ".css", ".json", ".yaml", ".yml"},
}


def category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, suffixes in CATEGORIES.items():
        if suffix in suffixes:
            return category
    return "Other"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_stem(path: Path) -> str:
    text = unicodedata.normalize("NFKD", path.stem)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text or "file"


def organized_name(path: Path) -> str:
    stamp = path.stat().st_mtime
    date_prefix = datetime.fromtimestamp(stamp).strftime("%Y%m%d")
    return f"{date_prefix}_{normalized_stem(path)}{path.suffix.lower()}"


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def existing_hashes(downloads: Path) -> dict[str, Path]:
    hashes: dict[str, Path] = {}
    for item in sorted(downloads.rglob("*")):
        if not item.is_file() or item.name.startswith("."):
            continue
        if item.parent == downloads:
            continue
        hashes.setdefault(sha256_file(item), item)
    return hashes


def organize(downloads: Path, apply: bool, rename: bool, delete_duplicates: bool) -> tuple[int, int]:
    if not downloads.is_dir():
        raise SystemExit(f"Downloads directory not found: {downloads}")

    seen = existing_hashes(downloads)
    moved = 0
    duplicates = 0
    for item in sorted(downloads.iterdir()):
        if item.is_dir() or item.name.startswith("."):
            continue

        digest = sha256_file(item)
        if digest in seen:
            duplicates += 1
            existing = seen[digest]
            if apply and delete_duplicates:
                item.unlink()
                print(f"[DELETE] duplicate {item.name} matches {existing.relative_to(downloads)}")
            else:
                action = "Would delete" if delete_duplicates else "Duplicate"
                print(f"[DRY-RUN] {action}: {item.name} matches {existing.relative_to(downloads)}")
            continue

        category = category_for(item)
        destination_dir = downloads / category
        destination_name = organized_name(item) if rename else item.name
        destination = unique_destination(destination_dir / destination_name)

        if apply:
            destination_dir.mkdir(exist_ok=True)
            shutil.move(str(item), str(destination))
            print(f"[MOVE] {item.name} -> {category}/{destination.name}")
        else:
            print(f"[DRY-RUN] {item.name} -> {category}/{destination.name}")
        moved += 1
        seen[digest] = destination

    return moved, duplicates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--downloads",
        type=Path,
        default=Path.home() / "Downloads",
        help="Downloads directory to organize",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move files and delete duplicates when --delete-duplicates is set.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview moves. This is the default.",
    )
    parser.add_argument(
        "--keep-names",
        action="store_true",
        help="Keep original file names instead of renaming to YYYYMMDD_slug.ext.",
    )
    parser.add_argument(
        "--delete-duplicates",
        action="store_true",
        help="Delete exact duplicate files from the Downloads root. Previewed unless --apply is also set.",
    )
    args = parser.parse_args()

    count, duplicates = organize(
        args.downloads.expanduser(),
        apply=args.apply,
        rename=not args.keep_names,
        delete_duplicates=args.delete_duplicates,
    )
    mode = "applied" if args.apply else "previewed"
    print(f"{mode.capitalize()} {count} move(s), found {duplicates} duplicate(s).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Capture, search, and sync clipboard history without external Python packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STORE = Path.home() / ".local" / "share" / "automation-toolkit" / "clipboard_history.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_entries(store: Path) -> list[dict[str, str]]:
    if not store.exists():
        return []
    entries = []
    with store.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def append_entry(store: Path, text: str, source: str) -> bool:
    text = text.rstrip("\n")
    if not text:
        return False

    digest = text_hash(text)
    entries = read_entries(store)
    if entries and entries[-1].get("hash") == digest:
        return False

    store.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": now_iso(), "source": source, "hash": digest, "text": text}
    with store.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


def clipboard_command() -> list[str]:
    candidates = (
        ["wl-paste", "--no-newline"],
        ["xclip", "-selection", "clipboard", "-out"],
        ["xsel", "--clipboard", "--output"],
        ["pbpaste"],
        ["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard"],
    )
    for command in candidates:
        if shutil.which(command[0]):
            return command
    raise SystemExit("No clipboard reader found. Install wl-clipboard, xclip, xsel, or use macOS/PowerShell.")


def read_clipboard() -> str:
    command = clipboard_command()
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        return ""
    return result.stdout


def command_add(args: argparse.Namespace) -> None:
    text = args.text if args.text is not None else read_clipboard()
    added = append_entry(args.store.expanduser(), text, source="manual" if args.text is not None else "clipboard")
    print("[ADD] saved" if added else "[SKIP] empty or unchanged")


def command_watch(args: argparse.Namespace) -> None:
    store = args.store.expanduser()
    print(f"Watching clipboard. Store: {store}")
    while True:
        try:
            if append_entry(store, read_clipboard(), source="clipboard"):
                print(f"[ADD] {now_iso()}")
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Stopped.")
            return


def command_search(args: argparse.Namespace) -> None:
    needle = args.query.lower()
    matches = [entry for entry in read_entries(args.store.expanduser()) if needle in entry.get("text", "").lower()]
    for entry in matches[-args.limit :]:
        preview = entry["text"].replace("\n", " ")[:160]
        print(f"{entry['timestamp']} {entry['hash'][:12]} {preview}")
    print(f"Found {len(matches)} match(es).")


def command_list(args: argparse.Namespace) -> None:
    entries = read_entries(args.store.expanduser())
    for entry in entries[-args.limit :]:
        preview = entry["text"].replace("\n", " ")[:160]
        print(f"{entry['timestamp']} {entry['hash'][:12]} {preview}")
    print(f"Showing {min(len(entries), args.limit)} of {len(entries)} entry(s).")


def command_export(args: argparse.Namespace) -> None:
    store = args.store.expanduser()
    sync_dir = args.sync_dir.expanduser()
    sync_dir.mkdir(parents=True, exist_ok=True)
    destination = sync_dir / store.name
    shutil.copy2(store, destination) if store.exists() else destination.write_text("", encoding="utf-8")
    print(f"[EXPORT] {destination}")


def command_import(args: argparse.Namespace) -> None:
    store = args.store.expanduser()
    source = args.sync_dir.expanduser() / store.name
    if not source.exists():
        raise SystemExit(f"Sync file not found: {source}")

    merged = {(entry["timestamp"], entry["hash"]): entry for entry in read_entries(store)}
    for entry in read_entries(source):
        merged.setdefault((entry["timestamp"], entry["hash"]), entry)

    store.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(merged.values(), key=lambda entry: entry["timestamp"])
    with store.open("w", encoding="utf-8") as handle:
        for entry in ordered:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[IMPORT] merged {len(ordered)} unique entry(s) into {store}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE, help="Clipboard history JSONL file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Save current clipboard text or supplied text")
    add_parser.add_argument("text", nargs="?", help="Text to save instead of reading the clipboard")
    add_parser.set_defaults(func=command_add)

    watch_parser = subparsers.add_parser("watch", help="Continuously save clipboard changes")
    watch_parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds")
    watch_parser.set_defaults(func=command_watch)

    search_parser = subparsers.add_parser("search", help="Search saved clipboard text")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.set_defaults(func=command_search)

    list_parser = subparsers.add_parser("list", help="List recent clipboard entries")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.set_defaults(func=command_list)

    export_parser = subparsers.add_parser("sync-export", help="Copy history to a shared sync directory")
    export_parser.add_argument("--sync-dir", type=Path, required=True)
    export_parser.set_defaults(func=command_export)

    import_parser = subparsers.add_parser("sync-import", help="Merge history from a shared sync directory")
    import_parser.add_argument("--sync-dir", type=Path, required=True)
    import_parser.set_defaults(func=command_import)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

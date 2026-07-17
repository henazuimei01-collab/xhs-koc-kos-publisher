#!/usr/bin/env python3
"""Validate local tasks and emit the smallest browser/AI handoff payload."""

import argparse
import json
from datetime import datetime
from pathlib import Path


def validate(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    for key in ("task_id", "account", "account_id", "account_type", "scheduled_at", "title", "body", "images"):
        if not data.get(key):
            errors.append(f"missing {key}")
    try:
        scheduled = datetime.fromisoformat(data.get("scheduled_at", ""))
        if scheduled.tzinfo is None or scheduled <= datetime.now(scheduled.tzinfo):
            errors.append("scheduled_at is not in the future")
    except ValueError:
        errors.append("invalid scheduled_at")

    aliases = {"KOC": "KOC", "KOC商单": "KOC", "KOS": "KOS", "KOS直发": "KOS"}
    route = aliases.get(data.get("account_type"))
    order_id = str(data.get("order_id") or "").strip()
    if route == "KOC" and not order_id:
        errors.append("KOC missing order_id")
    elif route == "KOS" and order_id:
        errors.append("KOS contains order_id")
    elif route not in {"KOC", "KOS"}:
        errors.append("unknown account_type")
    if data.get("auto_publish") is not True:
        errors.append("auto_publish is not true")

    images = []
    for item in data.get("images", []):
        image = path.parent / item
        if image.is_file():
            images.append(str(image.resolve()))
        else:
            errors.append(f"missing image {item}")
    compact = {
        "task_id": data.get("task_id"), "account": data.get("account"),
        "account_id": data.get("account_id"), "route": route,
        "order_id": data.get("order_id"), "scheduled_at": data.get("scheduled_at"),
        "title": data.get("title"), "body": data.get("body"),
        "tags": data.get("tags", []), "images": images,
    }
    return errors, compact


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("publish-tasks"))
    parser.add_argument("--task-id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    paths = sorted(args.root.glob("*/task.json"))
    if args.task_id:
        paths = [path for path in paths if path.parent.name == args.task_id]

    ready, rejected = [], []
    for path in paths:
        errors, compact = validate(path)
        if errors:
            rejected.append({"task_id": compact["task_id"], "errors": errors})
        else:
            ready.append(compact)
    queue = {"ready": ready, "rejected": rejected}
    encoded = json.dumps(queue, ensure_ascii=False, separators=(",", ":"))
    result = {
        "queue": queue,
        "metrics": {
            "scanned_tasks": len(paths), "ready_tasks": len(ready),
            "rejected_tasks": len(rejected), "ai_payload_bytes": len(encoded.encode("utf-8")),
            "estimated_input_tokens": max(1, round(len(encoded) / 3)),
            "note": "Estimate for compact handoff only; not Codex billing usage.",
        },
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

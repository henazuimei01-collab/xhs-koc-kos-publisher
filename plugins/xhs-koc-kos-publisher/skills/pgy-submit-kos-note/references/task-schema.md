# Local batch template

Staff fill one XLSX row per note with: `账号名`, `账号ID`, `类型`, `蒲公英订单号`, `定时发布时间`, `标题`, `正文`, `图片文件夹`, and optional `备注`.

- Use `KOC` for ordinary-person commercial accounts and require one unique 蒲公英 order ID per row.
- Use `KOS` for employee direct publishing and leave the order ID empty.
- Allow every row to use a different account and scheduled time.
- Point `图片文件夹` to that note's local image directory. Sort uploads by filename.

Convert the XLSX with:

```bash
python3 scripts/prepare_task.py batch.xlsx --output publish-tasks --confirm-publish
```

The command references original local image paths without copying them, generates stable hidden task IDs, and rejects an existing ID to prevent duplicate submission.

# Internal manifest

The workbench creates one hidden directory per note. Staff never name or manage it:

```text
TASK-001/
├── task.json
└── images/
    ├── 01.jpeg
    ├── 02.jpeg
    └── 03.jpeg
```

Required `task.json` fields:

```json
{
  "task_id": "TASK-001",
  "account": "不吃香菜",
  "account_type": "KOC",
  "order_id": "2075508324325801984",
  "content_type": "图文笔记",
  "scheduled_at": "2026-07-31T18:30:00+08:00",
  "auto_publish": true,
  "title": "标题",
  "body": "正文",
  "tags": ["#标签1", "#标签2"],
  "images": ["images/01.jpeg", "images/02.jpeg"]
}
```

Use ISO 8601 time with an explicit timezone. `auto_publish` authorizes platform submission and scheduled publication for this task only.

Before browser automation, call `scripts/preflight_queue.py`; its compact output is the only task payload the model needs.

For `KOS`, omit `order_id`. For `KOC`, require it as the unique commercial-order key. Read order code and brand from the matched order page at runtime; do not ask staff to enter them.

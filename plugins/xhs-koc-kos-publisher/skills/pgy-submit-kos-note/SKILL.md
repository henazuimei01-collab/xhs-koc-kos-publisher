---
name: pgy-submit-kos-note
description: Publish batches of locally stored 小红书 notes from the simple KOC/KOS XLSX template. Use when staff need multi-account uploads with different scheduled times: KOC must match a unique 蒲公英 order, while KOS must publish directly and never bind an order.
---

# 小红书 KOC 商单 / KOS 直发

Automate a task explicitly enabled for automatic publication while preventing account-type, account, and order cross-routing.

## Route first

Read `类型` from the local task before any publishing action.

- `KOC`: require the unique 蒲公英 order ID and use only the commercial-order route.
- `KOS`: require the order ID to be empty and open the creator publishing page directly. Never open or bind 蒲公英.
- Missing, conflicting, or unknown account type: set `预检失败` and stop.

## Required input

Accept the local batch XLSX or an internal task manifest. Require these fields before browser actions:

- Source XLSX and each note's local image folder.
- Exact 小红书 account name.
- `类型` (`KOC` or `KOS`).
- 蒲公英 order ID only for `KOC`.
- Scheduled time with timezone.
- Explicit batch confirmation before conversion; generated manifests set `auto_publish=true`.

Read [task-schema.md](references/task-schema.md) for the manifest format.

## Workflow

1. Read all populated XLSX rows. Treat local content as final copy; do not require a content-review field.
2. Show one compact batch confirmation containing account groups, KOC/KOS counts, note count, and scheduled times.
3. After confirmation, run `scripts/prepare_task.py INPUT --output publish-tasks --confirm-publish`. It references the original local images without copying or downloading them and creates one manifest per row.
4. Run `scripts/preflight_queue.py` locally and give the browser only its single compact ready-task payload. Do not use model context to scan historical rows, validate ordinary fields, or rediscover local image paths.
5. Stop if validation fails, scheduled time is not in the future, or auto-publish is absent.
6. Use the Chrome control skill because the workflow depends on an authenticated Chrome profile mapped to the account.
7. Branch exactly once: for `KOC`, open the exact 蒲公英 order and verify account/order/code/brand/status, then click `提交笔记`; for `KOS`, open the creator publishing page directly and verify no commercial-order badge or binding is present.
8. Verify the creator account matches `account`; never ignore a mismatch.
9. Upload images in manifest order. Fill title and body, including tags.
10. For `KOC`, record and verify the matched order page's `内容合作` order code and brand. For `KOS`, verify all commercial-order elements are absent.
11. Enable `定时发布`, set `scheduled_at`, and read the value back from the page.
12. Before submission, re-check account, unique order ID, the order code and brand read from that order page, image count, title, scheduled time, and `auto_publish`.
13. Submit the note for review when the row has `auto_publish=true`; this is the per-task authorization for automatic submission and scheduled publication.
14. Write status, timestamp, rejection reason, and note URL to the local task manifest. Never create a second submission.

Read [browser-workflow.md](references/browser-workflow.md) before browser execution.

## Hard stops

- Account mismatch between 蒲公英 and creator platform.
- The chosen route differs from the task type.
- Order ID, account, brand, order code, or content type mismatch on the matched order page.
- A non-empty 蒲公英订单号 on a `KOS` task, or a missing order ID on a `KOC` task.
- Missing/duplicate images or incomplete copy.
- `auto_publish` is false.
- Scheduled time is missing, past, or outside platform limits.
- CAPTCHA, login expiry, unknown modal, upload failure, or page-layout uncertainty.
- Existing submitted note for the same task.

Never bypass login, CAPTCHA, platform controls, or risk warnings. Preserve screenshots/logs for submission and status changes.

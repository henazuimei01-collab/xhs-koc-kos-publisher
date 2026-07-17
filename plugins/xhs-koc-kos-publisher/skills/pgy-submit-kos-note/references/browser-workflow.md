# Browser execution checks

## Before upload

- Use the exact order URL containing `order_id`.
- Verify visible 蒲公英 account, order code, order ID, brand, content type, and `待提交笔记` state.
- After redirect, verify the creator-platform account again.

## Before scheduling

- Verify uploaded image count equals the manifest.
- Verify the `内容合作` block shows the manifest order code and brand.
- Enable `定时发布`, enter the manifest time, and read the displayed time back.
- Stop if the platform changes or rejects the requested time.

## Before submission

Run one final comparison against `task.json`. Save a screenshot. Submit only once.

## Monitoring

Record `submitted_at`, platform status, brand-review status, rejection reason, scheduled time, and final note URL when available. Notify the operator on rejection, schedule change, login expiry, or successful publication.


#!/usr/bin/env python3
"""Convert the simple KOC/KOS batch XLSX into local task manifests."""

import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
REQUIRED_HEADERS = {"账号名", "账号ID", "类型", "蒲公英订单号", "定时发布时间", "标题", "正文", "图片文件夹"}


def col_number(reference):
    letters = re.match(r"[A-Z]+", reference).group(0)
    value = 0
    for char in letters:
        value = value * 26 + ord(char) - 64
    return value


def read_sheet(path):
    with zipfile.ZipFile(path) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in item.iterfind(".//m:t", NS)))
        root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in root.findall(".//m:row", NS):
            values = {}
            for cell in row.findall("m:c", NS):
                column = col_number(cell.attrib["r"])
                kind = cell.attrib.get("t")
                raw = cell.findtext("m:v", default="", namespaces=NS)
                if kind == "s" and raw:
                    value = shared[int(raw)]
                elif kind == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iterfind(".//m:t", NS))
                else:
                    value = raw
                values[column] = value
            rows.append((int(row.attrib["r"]), values))
    return rows


def excel_datetime(value, tz):
    text = str(value).strip()
    if not text:
        raise ValueError("定时发布时间为空")
    try:
        number = float(text)
        dt = datetime(1899, 12, 30, tzinfo=tz) + timedelta(days=number)
    except ValueError:
        dt = datetime.fromisoformat(text.replace("/", "-"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
    return dt


def normalize_type(value):
    aliases = {"KOC": "KOC", "KOC商单": "KOC", "KOS": "KOS", "KOS直发": "KOS"}
    return aliases.get(str(value).strip())


def task_id(row_number, account_id, scheduled_at, title):
    raw = f"{row_number}|{account_id}|{scheduled_at}|{title}".encode("utf-8")
    return f"XHS-{hashlib.sha256(raw).hexdigest()[:12].upper()}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--row", type=int, action="append", help="Only prepare these Excel row numbers")
    parser.add_argument("--timezone", default="+08:00")
    parser.add_argument("--confirm-publish", action="store_true", help="User confirmed upload and scheduled submission")
    args = parser.parse_args()

    if not args.confirm_publish:
        raise ValueError("提交前必须使用 --confirm-publish 确认本批次")
    sign = -1 if args.timezone.startswith("-") else 1
    hours, minutes = map(int, args.timezone.lstrip("+-").split(":"))
    tz = timezone(sign * timedelta(hours=hours, minutes=minutes))

    rows = read_sheet(args.input)
    header_row = None
    headers = None
    for row_number, values in rows:
        candidate = {str(value).strip(): column for column, value in values.items() if str(value).strip()}
        if REQUIRED_HEADERS.issubset(candidate):
            header_row, headers = row_number, candidate
            break
    if not headers:
        raise ValueError("未找到批量发布模板表头")

    prepared, rejected = [], []
    selected = set(args.row or [])
    for row_number, values in rows:
        if row_number <= header_row or (selected and row_number not in selected):
            continue
        record = {name: str(values.get(column, "")).strip() for name, column in headers.items()}
        if not any(record.get(name) for name in REQUIRED_HEADERS):
            continue
        errors = []
        route = normalize_type(record.get("类型"))
        if not route:
            errors.append("类型必须是 KOC 或 KOS")
        account, account_id = record.get("账号名", ""), record.get("账号ID", "")
        title, body = record.get("标题", ""), record.get("正文", "")
        order_id = record.get("蒲公英订单号", "")
        if not account:
            errors.append("账号名为空")
        if not account_id:
            errors.append("账号ID为空")
        if not title or not body:
            errors.append("标题或正文为空")
        if route == "KOC" and not order_id:
            errors.append("KOC缺少蒲公英订单号")
        if route == "KOS" and order_id:
            errors.append("KOS不能填写蒲公英订单号")
        try:
            scheduled = excel_datetime(record.get("定时发布时间", ""), tz)
            if scheduled <= datetime.now(tz):
                errors.append("定时发布时间不是未来时间")
        except ValueError as exc:
            scheduled = None
            errors.append(str(exc))

        source_dir = Path(record.get("图片文件夹", "")).expanduser()
        images = []
        if source_dir.is_dir():
            images = sorted((p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS), key=lambda p: p.name.lower())
        if not images:
            errors.append("图片文件夹不存在或没有支持的图片")
        if errors:
            rejected.append({"row": row_number, "errors": errors})
            continue

        identifier = task_id(row_number, account_id, scheduled.isoformat(), title)
        destination = args.output / identifier
        if destination.exists():
            rejected.append({"row": row_number, "errors": [f"任务已存在，禁止重复生成：{identifier}"]})
            continue
        destination.mkdir(parents=True)
        image_paths = [str(source.resolve()) for source in images]
        manifest = {
            "task_id": identifier,
            "source_row": row_number,
            "account": account,
            "account_id": account_id,
            "account_type": route,
            "order_id": order_id or None,
            "scheduled_at": scheduled.isoformat(),
            "auto_publish": True,
            "title": title,
            "body": body,
            "tags": re.findall(r"#[^#\s]+", body),
            "images": image_paths,
            "source": str(args.input.resolve()),
            "status": "ready",
        }
        (destination / "task.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        prepared.append({"row": row_number, "task_id": identifier, "images": len(image_paths)})

    print(json.dumps({"prepared": prepared, "rejected": rejected}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

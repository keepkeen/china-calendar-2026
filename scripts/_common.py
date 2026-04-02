
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DIST_DIR = ROOT / "dist"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def daterange(start: str, end: str):
    cur = dt.date.fromisoformat(start)
    end_date = dt.date.fromisoformat(end)
    while cur <= end_date:
        yield cur
        cur += dt.timedelta(days=1)

def ics_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def uid_for(key: str) -> str:
    return hashlib.sha1(key.encode("utf-8")).hexdigest() + "@china-calendar"

def build_event(date_obj: dt.date, summary: str, description: str, categories: str) -> str:
    ds = date_obj.strftime("%Y%m%d")
    de = (date_obj + dt.timedelta(days=1)).strftime("%Y%m%d")
    stamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return "\r\n".join([
        "BEGIN:VEVENT",
        f"UID:{uid_for(f'{summary}-{ds}-{categories}')}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{ds}",
        f"DTEND;VALUE=DATE:{de}",
        f"SUMMARY:{ics_escape(summary)}",
        f"DESCRIPTION:{ics_escape(description)}",
        "STATUS:CONFIRMED",
        "TRANSP:TRANSPARENT",
        f"CATEGORIES:{ics_escape(categories)}",
        "END:VEVENT",
    ])

def build_calendar(name: str, desc: str, events: list[str]) -> str:
    return "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OpenAI//China Calendar Generator//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(name)}",
        f"X-WR-CALDESC:{ics_escape(desc)}",
        "X-WR-TIMEZONE:Asia/Shanghai",
        "X-PUBLISHED-TTL:PT12H",
        *events,
        "END:VCALENDAR",
        "",
    ])

def expand_holidays(data: dict) -> dict[dt.date, str]:
    result = {}
    for item in data["holiday_ranges"]:
        for d in daterange(item["start"], item["end"]):
            result[d] = item["name"]
    return result

def weekend_map(year: int, makeup_dates: set[dt.date]) -> dict[dt.date, str]:
    cur = dt.date(year, 1, 1)
    out = {}
    while cur.year == year:
        if cur.weekday() >= 5 and cur not in makeup_dates:
            out[cur] = "双休（周六）" if cur.weekday() == 5 else "双休（周日）"
        cur += dt.timedelta(days=1)
    return out

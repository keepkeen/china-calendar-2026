
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from _common import (
    DATA_DIR,
    DIST_DIR,
    build_calendar,
    build_event,
    expand_holidays,
    load_json,
    weekend_map,
)

INDEX_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Segoe UI", sans-serif; margin: 40px auto; max-width: 860px; line-height: 1.65; padding: 0 16px; color: #1f2328; }}
    .card {{ border: 1px solid #d0d7de; border-radius: 14px; padding: 18px; margin: 16px 0; }}
    a {{ text-decoration: none; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>部署到 GitHub Pages 后，下面四个文件可以直接作为 Apple Calendar / iOS Calendar 的订阅地址。</p>
  <div class="card"><h2>综合版</h2><p><a href="./china-calendar-{year}.ics">china-calendar-{year}.ics</a></p></div>
  <div class="card"><h2>拆分版</h2>
    <p><a href="./holidays-{year}.ics">holidays-{year}.ics</a></p>
    <p><a href="./weekends-{year}.ics">weekends-{year}.ics</a></p>
    <p><a href="./traditional-festivals-{year}.ics">traditional-festivals-{year}.ics</a></p>
  </div>
</body>
</html>
"""

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    args = parser.parse_args()

    holiday_data = load_json(DATA_DIR / f"holidays_{args.year}.json")
    trad_data = load_json(DATA_DIR / f"traditional_festivals_{args.year}.json")

    holiday_dates = expand_holidays(holiday_data)
    makeup_dates = {dt.date.fromisoformat(x["date"]): x["name"] for x in holiday_data["makeup_workdays"]}
    weekend_dates = weekend_map(args.year, set(makeup_dates))

    holiday_events = []
    for d, name in sorted(holiday_dates.items()):
        holiday_events.append((d, build_event(
            d,
            f"{name}（放假）",
            f"{d.isoformat()} {name} 放假安排。",
            "Holiday"
        )))
    for d, name in sorted(makeup_dates.items()):
        holiday_events.append((d, build_event(
            d,
            name,
            f"{d.isoformat()} 调休补班。",
            "Workday Override"
        )))

    weekend_events = [
        (d, build_event(d, summary, f"{d.isoformat()} 为双休日。", "Weekend"))
        for d, summary in sorted(weekend_dates.items())
    ]

    festival_events = []
    for item in sorted(trad_data["traditional_festivals"], key=lambda x: x["date"]):
        d = dt.date.fromisoformat(item["date"])
        festival_events.append((d, build_event(
            d,
            item["name"],
            f"{d.isoformat()} {item['name']}（{item['basis']}）。",
            "Traditional Festival"
        )))

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_DIR / f"holidays-{args.year}.ics").write_text(build_calendar(
        f"{args.year} 中国节假日与调休",
        f"{args.year} 中国法定节假日放假与调休补班日历",
        [e for _, e in sorted(holiday_events)]
    ), encoding="utf-8")

    (DIST_DIR / f"weekends-{args.year}.ics").write_text(build_calendar(
        f"{args.year} 中国双休日",
        f"{args.year} 中国双休周末日历（已排除调休补班）",
        [e for _, e in sorted(weekend_events)]
    ), encoding="utf-8")

    (DIST_DIR / f"traditional-festivals-{args.year}.ics").write_text(build_calendar(
        f"{args.year} 中国传统节日",
        f"{args.year} 中国传统节日日历",
        [e for _, e in sorted(festival_events)]
    ), encoding="utf-8")

    all_events = [e for _, e in sorted(holiday_events + weekend_events + festival_events)]
    (DIST_DIR / f"china-calendar-{args.year}.ics").write_text(build_calendar(
        f"{args.year} 中国节假日·双休·传统节日",
        f"{args.year} 中国法定节假日、调休补班、双休与传统节日综合日历",
        all_events
    ), encoding="utf-8")

    (DIST_DIR / "index.html").write_text(INDEX_TEMPLATE.format(
        title=f"{args.year} 中国节假日 / 双休 / 传统节日订阅",
        year=args.year
    ), encoding="utf-8")
    (DIST_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"[OK] generated calendars for {args.year}")

if __name__ == "__main__":
    main()

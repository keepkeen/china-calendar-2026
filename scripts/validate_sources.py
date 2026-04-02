
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from _common import DATA_DIR, load_json

REQUIRED_HOLIDAYS = {"元旦", "春节", "清明节", "劳动节", "端午节", "中秋节", "国庆节"}
REQUIRED_TRADITIONAL_FESTIVALS = {"春节", "端午节", "中秋节", "清明节", "冬至", "除夕"}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    args = parser.parse_args()

    holiday_path = DATA_DIR / f"holidays_{args.year}.json"
    if not holiday_path.exists():
        raise SystemExit(f"missing file: {holiday_path}")

    data = load_json(holiday_path)
    names = {item["name"] for item in data.get("holiday_ranges", [])}
    missing = REQUIRED_HOLIDAYS - names
    if missing:
        raise SystemExit(f"holiday_ranges 缺少项目: {sorted(missing)}")
    if len(data.get("holiday_ranges", [])) != 7:
        raise SystemExit(f"holiday_ranges 数量异常: {len(data.get('holiday_ranges', []))}")

    makeup_dates = {item["date"] for item in data.get("makeup_workdays", [])}
    if len(makeup_dates) != 6:
        raise SystemExit(f"调休补班日期数量异常: {len(makeup_dates)}")
    for value in makeup_dates:
        dt.date.fromisoformat(value)

    trad_path = DATA_DIR / f"traditional_festivals_{args.year}.json"
    if not trad_path.exists():
        print(f"[WARN] missing curated traditional festival file: {trad_path}")
    else:
        trad = load_json(trad_path)
        festivals = trad.get("traditional_festivals", [])
        if not festivals:
            raise SystemExit("traditional_festivals 为空")
        names = {item["name"] for item in festivals}
        missing = REQUIRED_TRADITIONAL_FESTIVALS - names
        if missing:
            raise SystemExit(f"traditional_festivals 缺少项目: {sorted(missing)}")
        for item in festivals:
            dt.date.fromisoformat(item["date"])

    print(f"[OK] validation passed for {args.year}")

if __name__ == "__main__":
    main()

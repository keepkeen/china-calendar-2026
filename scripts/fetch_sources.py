
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import requests

from _common import DATA_DIR, save_json

GOV_NOTICE_URL = "https://www.gov.cn/zhengce/zhengceku/202511/content_7047091.htm"
HKO_CSV_URL_TEMPLATE = "https://data.weather.gov.hk/weatherAPI/hko_data/calendar/nongli_calendar_{year}.csv"

HOLIDAY_HEADINGS = {
    "一、元旦：": "元旦",
    "二、春节：": "春节",
    "三、清明节：": "清明节",
    "四、劳动节：": "劳动节",
    "五、端午节：": "端午节",
    "六、中秋节：": "中秋节",
    "七、国庆节：": "国庆节",
}

LUNAR_FESTIVAL_RULES = [
    {"name": "腊八节", "lunar_month": "十二月", "lunar_date": "初八"},
    {"name": "北方小年", "lunar_month": "十二月", "lunar_date": "廿三"},
    {"name": "除夕", "lunar_month": "十二月", "lunar_date": "廿九"},
    {"name": "春节", "lunar_month": "正月", "lunar_date": "初一"},
    {"name": "元宵节", "lunar_month": "正月", "lunar_date": "十五"},
    {"name": "龙抬头", "lunar_month": "二月", "lunar_date": "初二"},
    {"name": "上巳节", "lunar_month": "三月", "lunar_date": "初三"},
    {"name": "端午节", "lunar_month": "五月", "lunar_date": "初五"},
    {"name": "七夕", "lunar_month": "七月", "lunar_date": "初七"},
    {"name": "中元节", "lunar_month": "七月", "lunar_date": "十五"},
    {"name": "中秋节", "lunar_month": "八月", "lunar_date": "十五"},
    {"name": "重阳节", "lunar_month": "九月", "lunar_date": "初九"},
    {"name": "寒衣节", "lunar_month": "十月", "lunar_date": "初一"},
    {"name": "下元节", "lunar_month": "十月", "lunar_date": "十五"},
]


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.parts.append(text)

def cn_md_to_iso(year: int, s: str) -> str:
    m = re.match(r"(\d+)月(\d+)日", s)
    if not m:
        raise ValueError(f"无法解析日期: {s}")
    month, day = int(m.group(1)), int(m.group(2))
    return f"{year:04d}-{month:02d}-{day:02d}"


def extract_text_lines(html: str) -> list[str]:
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.parts


def parse_notice_ranges(year: int, html: str) -> tuple[list[dict], list[dict]]:
    lines = extract_text_lines(html)
    details: dict[str, str] = {}

    for idx, line in enumerate(lines):
        holiday_name = HOLIDAY_HEADINGS.get(line)
        if holiday_name and idx + 1 < len(lines):
            details[holiday_name] = lines[idx + 1]

    holiday_ranges = []
    makeup_workdays = []
    for holiday_name in HOLIDAY_HEADINGS.values():
        detail = details.get(holiday_name)
        if not detail:
            continue

        start_match = re.search(r"(\d{1,2})月(\d{1,2})日", detail)
        end_match = re.search(r"至(?:(\d{1,2})月)?(\d{1,2})日", detail)
        if not start_match or not end_match:
            continue

        start_month = int(start_match.group(1))
        start_day = int(start_match.group(2))
        end_month = int(end_match.group(1)) if end_match.group(1) else start_month
        end_day = int(end_match.group(2))
        holiday_ranges.append({
            "name": holiday_name,
            "start": f"{year:04d}-{start_month:02d}-{start_day:02d}",
            "end": f"{year:04d}-{end_month:02d}-{end_day:02d}",
        })

        makeup_section = detail.split("。", 1)[1] if "。" in detail else ""
        for month, day in re.findall(r"(\d{1,2})月(\d{1,2})日", makeup_section):
            makeup_workdays.append({
                "date": f"{year:04d}-{int(month):02d}-{int(day):02d}",
                "name": "调休补班",
            })

    return holiday_ranges, makeup_workdays


def normalize_hko_gregorian_date(value: str) -> str:
    return dt.datetime.strptime(value, "%d-%b-%y").date().isoformat()

def fetch_notice_holidays(year: int) -> dict:
    resp = requests.get(GOV_NOTICE_URL, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    html = resp.text

    holiday_ranges, makeup_workdays = parse_notice_ranges(year, html)

    return {
        "year": year,
        "source": {
            "name": f"国务院办公厅关于{year}年部分节假日安排的通知",
            "url": GOV_NOTICE_URL,
        },
        "holiday_ranges": holiday_ranges,
        "makeup_workdays": makeup_workdays,
        "fetched_from_network": True,
    }

def _get_first(row: dict, candidates: list[str]) -> str | None:
    for key in candidates:
        if key in row and row[key]:
            return row[key].strip()
    return None

def fetch_hko_csv(year: int) -> dict:
    url = HKO_CSV_URL_TEMPLATE.format(year=year)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"

    rows = list(csv.DictReader(resp.text.splitlines()))
    return {
        "year": year,
        "source": {
            "name": "香港天文台 / DATA.GOV.HK 公历与农历对照表",
            "csv_url": url,
        },
        "rows": rows,
        "fetched_from_network": True,
    }

def build_traditional_festivals(year: int, lunar_rows: list[dict]) -> dict:
    lookup = {}
    for row in lunar_rows:
        gregorian = _get_first(row, ["Gregorian Date", "公历日期", "GregorianDate", "Date"])
        lunar_month = _get_first(row, ["Lunar month", "農曆月份", "农历月份", "LunarMonth"])
        lunar_date = _get_first(row, ["Lunar Date", "農曆日期", "农历日期", "LunarDate"])
        if gregorian and lunar_month and lunar_date:
            lookup[(lunar_month, lunar_date)] = normalize_hko_gregorian_date(gregorian)

    festivals = []
    for rule in LUNAR_FESTIVAL_RULES:
        gregorian = lookup.get((rule["lunar_month"], rule["lunar_date"]))
        if gregorian:
            festivals.append({
                "date": gregorian,
                "name": rule["name"],
                "basis": f"农历{rule['lunar_month']}{rule['lunar_date']}",
            })

    solar_term_path = DATA_DIR / f"solar_term_festivals_{year}.json"
    if solar_term_path.exists():
        solar_term_data = json.loads(solar_term_path.read_text(encoding="utf-8"))
        festivals.extend(solar_term_data.get("solar_term_festivals", []))

    festivals.sort(key=lambda x: x["date"])
    return {
        "year": year,
        "source": {
            "name": "香港天文台 / DATA.GOV.HK 公历与农历对照表",
            "csv_url": HKO_CSV_URL_TEMPLATE.format(year=year),
            "with_solar_term_overrides": str((DATA_DIR / f"solar_term_festivals_{year}.json").name),
        },
        "traditional_festivals": festivals,
        "fetched_from_network": True,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    args = parser.parse_args()

    holidays = fetch_notice_holidays(args.year)
    save_json(DATA_DIR / f"holidays_{args.year}.json", holidays)

    lunar_data = fetch_hko_csv(args.year)
    save_json(DATA_DIR / f"hko_lunar_{args.year}.json", lunar_data)

    festivals = build_traditional_festivals(args.year, lunar_data["rows"])
    save_json(DATA_DIR / f"traditional_festivals_{args.year}.json", festivals)

    print(f"[OK] refreshed network sources for {args.year}")

if __name__ == "__main__":
    main()

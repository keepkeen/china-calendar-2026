# China Calendar 2026

一个可直接部署到 GitHub 的 2026 年中国订阅日历项目，适用于 Mac / iPhone / iPad 的 Apple Calendar，也兼容大多数支持 iCalendar (`.ics`) 的客户端。

## 包含内容

- 中国法定节假日放假安排
- 调休补班
- 全年双休日（自动排除调休补班日）
- 传统节日（按香港天文台 / DATA.GOV.HK 的 2026 公历/农历对照自动生成，包含 `清明节`、`冬至` 等节气型节日）
- GitHub Actions 自动抓取、校验、生成、提交与发布
- GitHub Pages 静态托管，方便做订阅地址

## 输出文件

部署后会在站点根目录提供这些文件：

- `china-calendar-2026.ics`：综合版
- `holidays-2026.ics`：仅法定节假日与调休
- `weekends-2026.ics`：仅双休
- `traditional-festivals-2026.ics`：仅传统节日

## 数据源策略

### 1) 法定节假日：国务院办公厅通知（主数据源）
- 文档：国务院办公厅关于 2026 年部分节假日安排的通知
- 文号：国办发明电〔2025〕7号
- 链接：https://www.gov.cn/zhengce/zhengceku/202511/content_7047091.htm

### 2) 农历/传统节日：香港天文台 / DATA.GOV.HK（主校验源）
- 年度 CSV：https://data.weather.gov.hk/weatherAPI/hko_data/calendar/nongli_calendar_2026.csv
- API 说明：https://data.weather.gov.hk/weatherAPI/opendata/lunardate.php?date=[YYYY-MM-DD]
- 数据集页：https://data.gov.hk/sc-data/dataset/hk-hko-rss-gregorian-lunar-calendar-conversion-table/resource/384d45c0-c3c0-49bf-bd7f-57b7c9063056

## 推荐的 GitHub Pages 订阅地址

仓库开启 GitHub Pages 后，综合订阅地址通常是：

```text
https://<你的 GitHub 用户名>.github.io/<你的仓库名>/china-calendar-2026.ics
```

也可以分别订阅：

```text
https://<你的 GitHub 用户名>.github.io/<你的仓库名>/holidays-2026.ics
https://<你的 GitHub 用户名>.github.io/<你的仓库名>/weekends-2026.ics
https://<你的 GitHub 用户名>.github.io/<你的仓库名>/traditional-festivals-2026.ics
```

## Apple Calendar 导入 / 订阅

### iPhone / iPad
日历 App -> 日历 -> 添加日历 -> 添加订阅日历 -> 输入 `.ics` 地址

### Mac
日历 App -> 文件 -> 新建日历订阅 -> 输入 `.ics` 地址

订阅保存到 iCloud 后，会同步到同一 Apple 账号下的其他设备。

## 本地运行

先安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

只生成现有数据：

```bash
python scripts/generate_calendar.py --year 2026
```

如需联网抓取并刷新数据：

```bash
python scripts/fetch_sources.py --year 2026
python scripts/validate_sources.py --year 2026
python scripts/generate_calendar.py --year 2026
```

## 首次启用 GitHub Pages

1. 推送仓库到 GitHub
2. 打开仓库 `Settings -> Pages`
3. `Build and deployment` 选择 `GitHub Actions`
4. 手动运行一次 `Update and deploy calendar` 工作流
5. 等待部署完成后，用生成的 Pages 地址订阅 `.ics`

## 目录结构

```text
.
├── .github/workflows/update-calendar.yml
├── data/
│   ├── holidays_2026.json
│   ├── solar_term_festivals_2026.json
│   └── traditional_festivals_2026.json
├── dist/
│   ├── china-calendar-2026.ics
│   ├── holidays-2026.ics
│   ├── traditional-festivals-2026.ics
│   ├── weekends-2026.ics
│   └── index.html
└── scripts/
    ├── fetch_sources.py
    ├── generate_calendar.py
    └── validate_sources.py
```

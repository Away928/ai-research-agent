"""Compact, local, data-only research collection receipt.

This is NOT AI analysis or external fact verification. It never copies the
contents of user uploads, credentials, model prompts, or arbitrary raw JSON.
"""

from datetime import datetime


FIELDS = (
    ("roe_pct", "ROE"),
    ("gross_margin_pct", "毛利率"),
    ("revenue_growth_pct", "主营业务收入同比"),
    ("net_profit_growth_pct", "净利润同比"),
    ("debt_ratio_pct", "资产负债率"),
)
SOURCES = (
    ("market_data", "行情"),
    ("financial_data", "财务"),
    ("announcement_data", "公告"),
    ("news_data", "新闻"),
)


def _cell(value, max_length=120):
    """Escape Markdown table delimiters and limit untrusted provider strings."""
    if value is None or value == "":
        return "未提供"
    text = str(value).replace("|", "｜").replace("\r", " ").replace("\n", " ")
    text = " ".join(text.split())
    return text[:max_length] + ("…" if len(text) > max_length else "")


def _table(headers, rows):
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    return "\n".join([header, separator] + [
        "| " + " | ".join(_cell(c) for c in row) + " |" for row in rows
    ])


def format_collection_brief(industry: str, raw_data: dict) -> str:
    """Return a bounded Markdown receipt of actual collected observations.

    The returned document contains provider labels and sampled measurements,
    not AI output. No claim of validity or complete coverage is made.
    """
    data = raw_data or {}
    status = data.get("数据源状态") or {}
    collected = data.get("采集时间") or "未提供"
    lines = [
        f"# {_cell(industry)}｜数据采集简报（非 AI 投资报告）",
        "",
        "> **仅数据采集结果 / 未调用 AI 分析。**",
        "> 本简报记录本次可获取的供应商返回值，未核验原始财报、价格时效或数据真实性。",
        "> 数据缺失不等于企业未披露。不可据此形成投资建议。",
        "",
        f"**记录生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**数据采集时间（来源包提供）：** {_cell(collected)}",
        "",
        "## 1. 数据源状态",
        "",
    ]
    source_rows = []
    for key, label in SOURCES:
        obj = data.get(key) or {}
        source_rows.append((
            label,
            status.get(key, "未返回"),
            obj.get("source", "未注明") if isinstance(obj, dict) else "未注明",
            obj.get("fetch_timestamp", "未注明") if isinstance(obj, dict) else "未注明",
        ))
    lines += [
        _table(("维度", "采集状态", "来源标签（未经验证）", "获取时间"), source_rows),
        "",
        "来源标签及采集时间不能证明报价为实时，缓存可能过期。",
        "",
        "## 2. 行情样本（最多 12 家）",
        "",
    ]
    market = data.get("market_data") or {}
    quotes = market.get("行情") or {}
    constituents = market.get("成分股") or []
    lines.append(
        f"行情指数：{_cell(quotes.get('index_name'))}；"
        f"指数涨跌幅：{_cell(quotes.get('index_change_pct'))}%；"
        f"PE 中位数：{_cell(quotes.get('pe_median'))}；"
        f"本次成分股记录数：{len(constituents)}"
    )
    lines.append("")
    if constituents:
        lines.append(_table(
            ("公司", "代码", "价格", "涨跌幅(%)", "PE", "市值(亿元)"),
            [
                (r.get("name"), r.get("code"), r.get("price"),
                 r.get("change_pct"), r.get("pe"),
                 r.get("market_cap_billion"))
                for r in constituents[:12] if isinstance(r, dict)
            ],
        ))
    else:
        lines.append("未获取到可供列示的成分股。")
    lines += ["", "## 3. 财务样本与指标报告期（最多 12 家）", ""]
    fin = data.get("financial_data") or {}
    companies = fin.get("公司财务") or []
    lines.append(f"本次财务记录数：{len(companies)}。不同指标可能属于不同季度，不能直接混为同一横截面。")
    lines.append("")
    if companies:
        financial_rows = []
        for company in companies[:12]:
            if not isinstance(company, dict):
                continue
            periods = company.get("_metric_periods") or {}
            for key, label in FIELDS:
                val = company.get(key)
                if val is not None:
                    financial_rows.append((
                        company.get("name"), company.get("code"), label,
                        f"{val}%", periods.get(key) or company.get("_data_period"),
                        company.get("_source"),
                    ))
        if financial_rows:
            lines.append(_table(
                ("公司", "代码", "指标", "采集值", "指标报告期", "来源标签"),
                financial_rows,
            ))
        else:
            lines.append("财务记录中暂无可列示的有效指标。")
    else:
        lines.append("未获取到可列示的财务记录。")
    lines += ["", "## 4. 公告与新闻条目（各最多 8 条）", ""]
    for source_key, data_key, label in (
        ("announcement_data", "公告", "公告"),
        ("news_data", "新闻", "新闻"),
    ):
        source = data.get(source_key) or {}
        records = source.get(data_key) or []
        lines.append(f"### {label} · 本次记录数 {len(records)}")
        lines.append("")
        if records:
            lines.append(_table(
                ("日期", "标题", "记录来源"),
                [
                    (r.get("date"), r.get("title"),
                     r.get("company") if source_key == "announcement_data"
                     else r.get("source"))
                    for r in records[:8] if isinstance(r, dict)
                ],
            ))
        else:
            lines.append("未获取到条目。")
        lines.append("")
    lines += [
        "## 5. 重要边界",
        "",
        "- 没有运行模型分析，没有生成投资判断或评级。",
        "- 上述数值仅是采集快照，可能为缓存、缺项或不同口径。",
        "- 如曾上传用户补充材料，其**正文和文件名不会自动写入本简报**。",
        "- 重要数据需按交易所公告、上市公司原始财报或其他可信独立来源复核。",
        "",
    ]
    return "\n".join(lines)

"""
数据采集报告 — 结构化摘要构建 + 终端打印
=========================================

从 gather() 返回的原始数据包生成 Web/CLI 可用的结构化摘要。
纯展示层逻辑，不涉及数据采集。
"""

from typing import Dict


def build_summary(package: Dict) -> Dict:
    """基于 gather() 返回的数据包，生成结构化的数据采集摘要。

    供 Web 展示或 API 返回使用。每个维度包含：来源、采集时间、数据期间、内容详情。
    """
    summary = {
        "采集时间": package.get("采集时间", ""),
        "行业": package.get("行业", ""),
        "数据源状态": package.get("数据源状态", {}),
        "各维度明细": {},
    }

    # ── 行情 ──
    md = package.get("market_data", {})
    quotes = md.get("行情", {}) or {}
    constituents = md.get("成分股", []) or []

    quote_lines = []
    if quotes.get("index_name"):
        quote_lines.append(
            f"{quotes['index_name']} {quotes.get('index_price', 'N/A')}"
            f"  {quotes.get('index_change_pct', 'N/A')}%"
        )
    if quotes.get("pe_median"):
        valid_n = int(quotes.get("pe_note", "").split("/")[0].split()[-1]) if quotes.get("pe_note") else 0
        total_n = len(constituents)
        quote_lines.append(f"PE中位数 {quotes['pe_median']}（{valid_n}/{total_n}只成分股）")
    if quotes.get("market_cap_total"):
        mc = quotes["market_cap_total"]
        if mc >= 10000:
            quote_lines.append(f"总市值 约{mc/10000:.1f}万亿")
        else:
            quote_lines.append(f"总市值 约{mc:.0f}亿")

    summary["各维度明细"]["行情"] = {
        "来源": quotes.get("_source", "无") if quotes else "无可用数据源",
        "采集时间": md.get("fetch_timestamp", ""),
        "概览": "\n".join(quote_lines) if quote_lines else "无数据",
        "成分股": [
            {
                "代码": c.get("code", ""),
                "名称": c.get("name", ""),
                "价格": c.get("price"),
                "涨跌幅(%)": c.get("change_pct"),
                "PE": c.get("pe"),
                "市值(亿)": c.get("market_cap_billion"),
            }
            for c in constituents
        ],
    }

    # ── 用户补充数据 ──
    user = package.get("user_supplements", {})
    user_list = []
    if isinstance(user, list):
        # 新格式：直接是条目列表
        for item in user:
            user_list.append({
                "类别": item.get("类别", "其他"),
                "标题": item.get("标题", ""),
                "日期": item.get("日期", ""),
                "来源": item.get("来源", ""),
                "内容": item.get("内容", ""),
            })
    elif isinstance(user, dict):
        # 旧格式：{cat: [...]}
        for cat in ["会议纪要", "专家访谈", "调研笔记", "其他"]:
            for item in (user.get(cat, []) or []):
                user_list.append({
                    "类别": cat,
                    "标题": item.get("标题", ""),
                    "日期": item.get("日期", ""),
                    "来源": item.get("来源", ""),
                    "内容": item.get("内容", ""),
                })
    summary["各维度明细"]["用户补充数据"] = {
        "来源": "用户上传",
        "数量": len(user_list),
        "列表": user_list,
    }

    # ── 财务 ──
    fd = package.get("financial_data", {})
    fin_companies = fd.get("公司财务", []) or []
    fin_periods = set()
    for c in fin_companies:
        dp = c.get("_data_period")
        if dp:
            fin_periods.add(dp)
    fin_indicators = fd.get("指标说明", [])
    # 只取指标名，去掉解释
    indicator_names = []
    for ind in fin_indicators:
        name = ind.split(":")[0] if ":" in ind else ind
        indicator_names.append(name)

    summary["各维度明细"]["财务"] = {
        "来源": fd.get("source", "无"),
        "数据期间": " / ".join(sorted(fin_periods)) if fin_periods else "未知",
        "采集时间": fd.get("fetch_timestamp", ""),
        "覆盖公司数": len(fin_companies),
        "指标": indicator_names if indicator_names else ["ROE", "毛利率", "营收增速", "净利增速", "负债率"],
        "公司": [
            {
                "代码": c.get("code", ""),
                "名称": c.get("name", ""),
                "ROE(%)": c.get("roe_pct"),
                "毛利率(%)": c.get("gross_margin_pct"),
                "营收增速(%)": c.get("revenue_growth_pct"),
                "净利增速(%)": c.get("net_profit_growth_pct"),
                "负债率(%)": c.get("debt_ratio_pct"),
                "数据期间": c.get("_data_period", ""),
            }
            for c in fin_companies
        ],
    }

    # ── 公告 ──
    ad = package.get("announcement_data", {})
    announcements = ad.get("公告", []) or []
    summary["各维度明细"]["公告"] = {
        "来源": ad.get("source", "无"),
        "采集时间": ad.get("fetch_timestamp", ""),
        "数量": len(announcements),
        "列表": [
            {
                "日期": a.get("date", ""),
                "公司": a.get("company", ""),
                "类型": a.get("type", ""),
                "标题": a.get("title", ""),
                "链接": a.get("url", ""),
            }
            for a in announcements
        ],
    }

    # ── 新闻 ──
    nd = package.get("news_data", {})
    news_items = nd.get("新闻", []) or []
    summary["各维度明细"]["新闻"] = {
        "来源": nd.get("source", "无"),
        "采集时间": nd.get("fetch_timestamp", ""),
        "数量": nd.get("数量", len(news_items)),
        "列表": [
            {
                "日期": n.get("date", ""),
                "来源媒体": n.get("source", ""),
                "标题": n.get("title", ""),
                "摘要": n.get("summary", ""),
                "链接": n.get("url", ""),
            }
            for n in news_items
        ],
    }

    return summary

def print_summary(package: Dict):
    """在终端中打印格式化的数据采集报告。"""
    summary = build_summary(package)
    dims = summary.get("各维度明细", {})

    print(f"\n{'='*60}")
    print(f"📊 数据采集报告 — {summary['行业']}")
    print(f"   采集时间: {summary['采集时间']}")
    print(f"{'='*60}")

    # ── 行情 ──
    m = dims.get("行情", {})
    print(f"\n┌─ 📈 行情数据")
    print(f"│  来源: {m.get('来源', '无')}")
    print(f"│  采集时间: {m.get('采集时间', '')}")
    overview = m.get("概览", "")
    if overview:
        for line in overview.split("\n"):
            print(f"│  {line}")
    constituents = m.get("成分股", []) or []
    if constituents:
        print(f"│")
        print(f"│  成分股 ({len(constituents)}只):")
        # 表头
        print(f"│  {'名称':<8s} {'代码':<8s} {'价格':>10s} {'涨跌幅':>8s} {'PE':>8s} {'市值(亿)':>10s}")
        print(f"│  {'─'*56}")
        for c in constituents:
            price_str = f"¥{c['价格']:.2f}" if c.get('价格') else "N/A"
            chg_str = f"{c['涨跌幅(%)']:+.1f}%" if c.get('涨跌幅(%)') is not None else "N/A"
            pe_str = f"{c['PE']:.1f}" if c.get('PE') else "N/A"
            mc_str = f"{c['市值(亿)']:.0f}" if c.get('市值(亿)') else "N/A"
            print(f"│  {c['名称']:<8s} {c['代码']:<8s} {price_str:>10s} {chg_str:>8s} {pe_str:>8s} {mc_str:>10s}")

    # ── 财务 ──
    f = dims.get("财务", {})
    print(f"\n├─ 💰 财务数据")
    print(f"│  来源: {f.get('来源', '无')}")
    print(f"│  数据期间: {f.get('数据期间', '未知')}")
    print(f"│  覆盖: {f.get('覆盖公司数', 0)}家公司, {len(f.get('指标', []))}项指标")
    fin_cos = f.get("公司", []) or []
    if fin_cos:
        print(f"│")
        print(f"│  {'名称':<8s} {'ROE%':>8s} {'毛利率%':>8s} {'营收增速%':>10s} {'净利增速%':>10s} {'负债率%':>8s} {'期间':<6s}")
        print(f"│  {'─'*64}")
        for c in fin_cos:
            def _v(val):
                return f"{val:+.1f}" if val is not None else "N/A"
            print(f"│  {c['名称']:<8s} {_v(c.get('ROE(%)')):>8s} {_v(c.get('毛利率(%)')):>8s} "
                  f"{_v(c.get('营收增速(%)')):>10s} {_v(c.get('净利增速(%)')):>10s} "
                  f"{_v(c.get('负债率(%)')):>8s} {c.get('数据期间',''):<6s}")

    # ── 公告 ──
    a = dims.get("公告", {})
    print(f"\n├─ 📋 公告")
    print(f"│  来源: {a.get('来源', '无')}")
    print(f"│  共 {a.get('数量', 0)} 条")
    ann_list = a.get("列表", []) or []
    if ann_list:
        for ann in ann_list:
            print(f"│  [{ann['日期']}] [{ann['类型']}] {ann['公司']} — {ann['标题']}")

    # ── 新闻 ──
    n = dims.get("新闻", {})
    print(f"\n├─ 📰 新闻")
    print(f"│  来源: {n.get('来源', '无')}")
    print(f"│  共 {n.get('数量', 0)} 条")
    news_list = n.get("列表", []) or []
    if news_list:
        for item in news_list:
            summary_text = item.get('摘要', '')
            if len(summary_text) > 60:
                summary_text = summary_text[:60] + "..."
            print(f"│  [{item['日期']}] {item['来源媒体']} — {item['标题']}")

    # ── 用户补充数据 ──
    u = dims.get("用户补充数据", {})
    user_items = u.get("列表", []) or []
    total_user = u.get("数量", 0)
    print(f"\n└─ 📝 用户补充数据")
    if total_user == 0:
        print(f"   — 无用户补充数据（将 .md/.txt 文件放入 user_data/ 目录即可自动加载）")
    else:
        cat_counts = {}
        for item in user_items:
            cat = item.get("类别", "其他")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        cat_summary = " / ".join(f"{c}:{n}条" for c, n in cat_counts.items())
        print(f"   总计: {total_user}条 ({cat_summary})")
        for item in user_items:
            print(f"   [{item['日期']}] [{item['类别']}] {item['标题']}")

    print(f"\n{'='*60}\n")


# ── 便捷函数 ──────────────────────────────────────────────────

"""Offline and reproducible four-stage product demo from fictional fixtures.

NO external market/LLM calls, no user inputs, no history writes. Never describe
this as a real research run. Figures below come only from the synthetic fixture.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from statistics import mean

from tools.report_formatter import ReportFormatter

SYNTHETIC_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests" / "fixtures" / "synthetic_research_package.json"
)


def build_demo() -> dict:
    """Return an entirely local demonstration with a formatted downloadable report."""
    package = json.loads(SYNTHETIC_FIXTURE.read_text(encoding="utf-8"))
    assert package["行业"] == "虚构测试能源"
    package = copy.deepcopy(package)
    market = package["market_data"]
    financial = package["financial_data"]
    constituents = market["成分股"]
    fin = {c["code"]: c for c in financial["公司财务"]}
    companies = [
        {**c, **{k: v for k, v in fin[c["code"]].items() if k not in ("code", "name")}}
        for c in constituents if c["code"] in fin
    ]
    if len(companies) != 2:
        raise ValueError("Demo fixture requires exactly two fictional companies")

    capital = sum(float(c["market_cap_billion"]) for c in companies)
    leader_share = companies[0]["market_cap_billion"] / capital * 100
    average_roe = mean(float(c["roe_pct"]) for c in companies)
    roe_periods = {
        c["_metric_periods"].get("roe_pct") for c in companies
    }
    growth_periods = {
        c["_metric_periods"].get("revenue_growth_pct") for c in companies
    }
    # Refuse to average growth across non-comparable financial quarters.
    growth_comparable = None not in growth_periods and len(growth_periods) == 1
    average_growth = (
        mean(float(c["revenue_growth_pct"]) for c in companies)
        if growth_comparable else None
    )
    roe_comparable = None not in roe_periods and len(roe_periods) == 1
    summary = (
        "这是一份**完全虚构的行业投资研究演示**。样本包含两家合成公司，"
        f"合计模拟市值 {capital:.0f} 亿元；首家公司占比 {leader_share:.1f}%。"
        "报告展示数据整理、行业概况、公司对比与带有反方观点的研究判断，"
        "不反映真实市场，不构成投资建议。"
    )

    overview = f"""## 第二阶段｜行业全景分析

### 市场结构（合成样本）
虚构测试能源仅用于展示 Research Agent 的四阶段工作流，不代表任何真实行业。
样本覆盖 **{len(companies)} 家虚构公司**，合计模拟市值 **{capital:.0f} 亿元**，
模拟 PE 中位数为 **{market['行情']['pe_median']} 倍**。由于仅有两家样本，
不能据此推断真实行业集中度或产业链格局。

### 产业链及增长假设
假设产业链由上游设备、中游系统集成与下游能源用户构成。
这是展示分析逻辑的**情境假设**，没有真实市场规模、政策支持或公司调研证据。

### 研究问题
未来需要核实订单需求、盈利质量和产能利用率；缺少证据时不作确定性预测。
"""

    deep = f"""## 第三阶段｜公司深度比较

| 公司（均为虚构） | ROE | 毛利率 | 主营业务收入同比 | 净利润同比 | 负债率 | 模拟 PE |
|---|---:|---:|---:|---:|---:|---:|
| {companies[0]['name']} | {companies[0]['roe_pct']:.1f}% | {companies[0]['gross_margin_pct']:.1f}% | {companies[0]['revenue_growth_pct']:.1f}% | {companies[0]['net_profit_growth_pct']:.1f}% | {companies[0]['debt_ratio_pct']:.1f}% | {companies[0]['pe']:.1f} |
| {companies[1]['name']} | {companies[1]['roe_pct']:.1f}% | {companies[1]['gross_margin_pct']:.1f}% | {companies[1]['revenue_growth_pct']:.1f}% | {companies[1]['net_profit_growth_pct']:.1f}% | {companies[1]['debt_ratio_pct']:.1f}% | {companies[1]['pe']:.1f} |

### 数据阅读
- 两家公司 ROE 报告期均为 2025Q3，合成样本平均 ROE 为 **{average_roe:.1f}%**。
- 主营业务收入同比分别来自 **2025Q2** 和 **2025Q3**，不是同一横截面；**不计算跨季度平均增长率**。
- {companies[0]['name']}的 ROE 为 **{companies[0]['roe_pct']:.1f}%** `[[FIN-{companies[0]['code']}-roe_pct={companies[0]['roe_pct']}]]`，
  高于另一家，但不能据此认定竞争优势。
- {companies[1]['name']}的资产负债率为 **{companies[1]['debt_ratio_pct']:.1f}%**，
  仅表示合成输入中的资本结构，未经过任何财报核验。

### 数据局限
部分指标分属不同季度，任何横向比较都必须考虑报告期差异。
不凭这两家公司推断行业实际平均水平。
"""

    thesis = f"""## 第四阶段｜投资研判与反方论证（合成情景）

### 研究假设
假设需求恢复将带动模拟公司收入增长。如果未来出现**真实且可比**的订单、
收入与现金流数据，才可以进一步判断这一假设是否成立。

### 支持假设的演示证据
- {companies[0]['name']}的主营业务收入同比为
  **{companies[0]['revenue_growth_pct']:.1f}%** `[[FIN-{companies[0]['code']}-revenue_growth_pct={companies[0]['revenue_growth_pct']}]]`。
- {companies[0]['name']}的模拟毛利率高于{companies[1]['name']}，
  但现有信息不足以归因于定价权或成本优势。

### Red Team：反方观点
如果需求没有改善、成本上行或高增长只是基数效应，则此前的增长假设可能失效。
两家样本也不具备代表真实行业的统计条件。**不得据此给出买入/卖出建议。**

### 下一步应核实
1. 可核查的官方定期报告与同口径财务指标。
2. 企业经营情况、行业需求与供应链数据。
3. 不同季度的会计口径以及估值所采用的价格日期。
"""

    final = f"""# 执行摘要

{summary}

{overview}

{deep}

{thesis}

## 结论

该虚构案例演示了从结构化输入到可下载研究报告的完整路径。
所有证券名称、财务指标、行业信息与研究假设均为**合成演示材料**。
没有调用真实金融数据接口，没有调用 LLM，也没有验证真实投资结论。
"""

    sections = {
        "data_collection": "使用预置合成数据包；无 API 请求、无模型调用",
        "industry_overview": overview,
        "company_deep_dive": deep,
        "investment_thesis": thesis,
    }
    work_log = [
        {"stage": key, "duration_seconds": 0.0, "notes": "离线预设演示；非真实执行"}
        for key in sections
    ]
    report = ReportFormatter().format_report(
        final, package["行业"], work_log,
        {"raw_data": package, "demo_mode": True},
    )
    return {
        "industry": package["行业"],
        "snapshot_date": package["采集时间"],
        "package": package,
        "companies": companies,
        "summary": summary,
        "sections": sections,
        "work_log": work_log,
        "report": report,
        "average_roe": average_roe,
        "average_growth": average_growth,
        "growth_comparable": growth_comparable,
        "roe_comparable": roe_comparable,
        "total_market_cap": capital,
    }

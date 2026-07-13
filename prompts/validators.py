"""AI output validators — sanity-check each AI analysis stage's output.

If a stage's output is missing key sections or quality markers, we send a
targeted follow-up prompt asking the model to fill in what's missing.

Checks go beyond regex keyword matching — we verify:
- Data citation density (specific numbers, not just vague claims)
- Source attribution (does the model cite where data came from?)
- Uncertainty labeling (does the model admit when it's unsure?)
- Structural completeness (tables, sections, risk coverage)
"""

import re


# ── Helper ──────────────────────────────────────────────────────

def _count_numbers(text: str) -> int:
    """Count concrete numeric references in text (percentages, amounts, ratios)."""
    # Match: digits followed by % or 亿/万/倍/元, or standalone numbers >= 3 digits
    pct_matches = re.findall(r'\d+\.?\d*\s*%', text)
    unit_matches = re.findall(r'\d+\.?\d*\s*(?:亿|万|倍|元|家)', text)
    big_num = re.findall(r'(?<!\d)\d{3,}(?!\d)', text)
    return len(pct_matches) + len(unit_matches) + len(big_num)


# ── Per-stage validation specs ──────────────────────────────────

# Each spec: list of (check_label, check_fn(output) -> bool, hint_prompt)
# check_fn returns True if the check passes

_STAGE_VALIDATORS = {
    "industry_overview": [
        (
            "数字引用",
            lambda o: _count_numbers(o) >= 5,
            "请补充具体数字（百分比、金额、数量等），每个结论尽量引用采集到的数据。",
        ),
        (
            "来源标注",
            lambda o: bool(re.search(
                r'(?:腾讯|新浪|baostock|公告|新闻|巨潮)', o, re.IGNORECASE)),
            "请标注数据来源（如'腾讯实时行情''baostock 日线财报'）。",
        ),
        (
            "不确定标注",
            lambda o: bool(re.search(
                r'(?:待验证|不确定|推断|数据不足|缺乏)', o, re.IGNORECASE)),
            "对不确定的结论请标注'待验证'或'基于数据推断'。",
        ),
        (
            "产业链分析",
            lambda o: len(re.findall(
                r'(?:产业链|上游|中游|下游|供应链)', o, re.IGNORECASE)) >= 2,
            "请补充产业链分析：上游/中游/下游分别是什么？有哪些核心环节？",
        ),
    ],
    "company_deep_dive": [
        (
            "数字引用",
            lambda o: _count_numbers(o) >= 8,
            "请补充具体财务数字（ROE、毛利率、营收增速、净利增速、PE 等）。",
        ),
        (
            "Markdown表格",
            lambda o: o.count("|") >= 8,
            "请用 Markdown 表格列出公司对比数据（至少包含名称、PE、ROE、毛利率）。",
        ),
        (
            "推断标注",
            lambda o: len(re.findall(
                r'(?:推断|估算|近似|推测|基于.*数据)', o, re.IGNORECASE)) >= 3,
            "请对基于财务数据推导的结论标注'数据推断'或'近似估算'。",
        ),
        (
            "预警信号",
            lambda o: bool(re.search(
                r'(?:预警|风险|异常|警惕|隐患)', o, re.IGNORECASE)),
            "请补充财务预警信号：标注异常数据组合（如高PE+低增速、低毛利+高负债）。",
        ),
    ],
    "investment_thesis": [
        (
            "周期判断",
            lambda o: bool(re.search(
                r'(?:底部|复苏|扩张|顶峰|下行|过热|衰退)', o, re.IGNORECASE)),
            "请明确当前行业周期位置（底部/复苏/扩张/顶峰/下行）。",
        ),
        (
            "Red Team",
            lambda o: bool(re.search(
                r'(?:反方|看空|证伪|悲观|下行风险)', o, re.IGNORECASE)),
            "请补充 Red Team 反方观点：看空这个行业的核心逻辑是什么？",
        ),
        (
            "风险表",
            lambda o: o.count("|") >= 6,
            "请用表格列出风险类型及判断依据（参考 Prompt 第 4 节的模板）。",
        ),
        (
            "数字引用",
            lambda o: _count_numbers(o) >= 10,
            "请优先使用原始采集数据中的数字，减少基于 AI 分析二次引用的数字。",
        ),
    ],
}


def validate_stage_output(stage_key: str, output: str) -> list[dict]:
    """Run all validators for a stage and return a list of missing items.

    Each missing item is a dict with 'label' and 'hint' keys.
    Returns empty list if everything passes.
    """
    validators = _STAGE_VALIDATORS.get(stage_key, [])
    missing = []
    for label, check_fn, hint in validators:
        if not check_fn(output):
            missing.append({"label": label, "hint": hint})
    if missing:
        labels = ", ".join(m["label"] for m in missing)
        print(f"  🔍 {stage_key} 质量检查未通过：缺少 {labels}")
    return missing


def build_chase_prompt(stage_key: str, missing_items: list[dict],
                       previous_output: str) -> str:
    """Build a follow-up prompt to fill in missing sections.

    Args:
        stage_key: the stage identifier
        missing_items: list of {label, hint} dicts from validate_stage_output
        previous_output: the original AI output to append to

    Returns:
        A prompt string asking the model to supplement the missing parts.
    """
    if not missing_items:
        return ""

    items_desc = "\n".join(
        f"  - {item['label']}：{item['hint']}" for item in missing_items
    )

    return (
        f"你上一次的分析缺少以下关键内容，请补充这些部分，"
        f"用简洁的段落格式直接输出，不要重复已有内容：\n\n"
        f"{items_desc}\n\n"
        f"只输出上述补充内容即可，不需要重新写完整报告。"
    )


def merge_chase_output(original: str, chase_output: str) -> str:
    """Append chase output to original, with a clear separator."""
    if not chase_output.strip():
        return original
    return original + "\n\n---\n\n## 📌 补充内容\n\n" + chase_output

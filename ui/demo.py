"""Workflow-first, offline Streamlit demo from a fully synthetic fixture.

This view never instantiates the live Agent, reads provider secrets, performs
network I/O, or writes a research history. Its progress is *navigation* through
prewritten stages, not a claim that an LLM is doing research.
"""

import pandas as pd
import streamlit as st

from tools.demo_experience import build_demo
from tools.demo_export import render_demo_html


# Four research stages, plus the output they produce. Preserve this order.
STEPS = (
    ("数据采集", "预置合成数据、来源与口径"),
    ("行业全景", "市场结构、产业链与待验证假设"),
    ("公司深度", "公司对比、报告期与财务证据"),
    ("投资研判", "研究假设、反方论证与风险"),
    ("报告交付", "成果审阅、下载与复核范围"),
)


def _stepper(active_step: int) -> None:
    """Compact, responsive overview of the workflow (not live progress)."""
    items = []
    for index, (name, _) in enumerate(STEPS, 1):
        state = (" is-current" if active_step == index else
                 " is-visited" if 0 < index < active_step else "")
        items.append(
            f'<li class="demo-step{state}">'
            f'<span class="demo-step-number">{index:02d}</span>'
            f'<span class="demo-step-name">{name}</span></li>'
        )
    st.markdown(
        '<ol class="demo-stepper" aria-label="预设研究工作流">'
        + "".join(items) + "</ol>",
        unsafe_allow_html=True,
    )


def _section_without_duplicate_heading(section: str) -> str:
    """Use the original documented stage content without a duplicate H2."""
    if section.startswith("## "):
        return section.split("\n", 1)[1].strip()
    return section


def _render_data_stage(demo: dict) -> None:
    st.markdown(
        "本阶段从**内置合成快照**读取示例行业、公司和财务数据。"
        "不是正在抓取真实行情，也没有运行模型。"
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("虚构公司", len(demo["companies"]))
    c2.metric("模拟总市值（亿元）", f'{demo["total_market_cap"]:.0f}')
    c3.metric("快照性质", "完全合成")

    rows = [
        {"数据类型": label,
         "来源": demo["package"].get(key, {}).get("source", "未提供"),
         "性质": "合成数据 · 非实时"}
        for key, label in (
            ("market_data", "行情"), ("financial_data", "财务"),
            ("announcement_data", "公告"), ("news_data", "新闻"),
        )
    ]
    st.markdown("#### 数据来源与范围")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("所有证券及相关数值均为虚构；标签仅用于模拟证据追踪。")
    with st.expander("查看合成快照与流程元数据", expanded=False):
        st.json({
            "mode": "offline_synthetic_demo",
            "fixture_snapshot": demo["snapshot_date"],
            "research_stages": list(demo["sections"]),
            "model_called": False,
            "network_called": False,
        })


def _render_industry_stage(demo: dict) -> None:
    st.markdown(_section_without_duplicate_heading(
        demo["sections"]["industry_overview"]))
    st.caption("这里展示预先写好的情境分析，不代表实际行业调查或实时推理。")


def _render_company_stage(demo: dict) -> None:
    a, b = st.columns(2)
    a.metric("合成样本平均 ROE（%）", f'{demo["average_roe"]:.1f}')
    b.metric("收入增速报告期", "不可直接比较" if not demo["growth_comparable"] else "一致")

    rows = [
        {
            "公司": company["name"],
            "模拟 PE": company["pe"],
            "ROE（%）": company["roe_pct"],
            "毛利率（%）": company["gross_margin_pct"],
            "收入同比（%）": company["revenue_growth_pct"],
            "收入同比报告期": (company.get("_metric_periods") or {}).get(
                "revenue_growth_pct"),
        }
        for company in demo["companies"]
    ]
    comparison = pd.DataFrame(rows)
    st.markdown("#### 两家虚构公司对比")
    st.dataframe(comparison, hide_index=True, width="stretch")
    if not demo["growth_comparable"]:
        st.warning("收入增速来自不同报告季度，不能直接计算横截面平均增长率。")
    with st.expander("查看可比财务指标图", expanded=False):
        st.bar_chart(comparison.set_index("公司")[["ROE（%）", "毛利率（%）"]])
    # The structured company table above replaces the duplicate Markdown table
    # in the prewritten stage; retain its original reading and limitation text.
    full = demo["sections"]["company_deep_dive"]
    if "### 数据阅读" in full:
        st.markdown("#### 数据阅读" + full.split("### 数据阅读", 1)[1])
    else:
        st.markdown(_section_without_duplicate_heading(full))
    st.caption("仅展示两家虚构公司，不对应真实证券。")


def _render_thesis_stage(demo: dict) -> None:
    st.markdown(_section_without_duplicate_heading(
        demo["sections"]["investment_thesis"]))
    st.caption("以上论证是预设教学案例，未由 LLM 实时生成，不构成投资建议。")


def _render_delivery_stage(demo: dict) -> None:
    st.markdown(demo["summary"])
    st.markdown("#### 获取本次演示交付物")
    left, right = st.columns(2)
    with left:
        st.download_button(
            "📄 下载完整研究报告",
            data=demo["report"],
            file_name="Research_Agent_合成数据_演示报告.md",
            mime="text/markdown",
            key="demo_download",
            width="stretch",
        )
    with right:
        st.download_button(
            "🌐 下载独立演示网页",
            data=render_demo_html(demo),
            file_name="Research_Agent_纯合成数据_独立演示.html",
            mime="text/html",
            key="demo_share_html",
            width="stretch",
            help="浏览器离线可读；不会运行研究或请求外部数据。",
        )
    with st.expander("审阅完整 Markdown 报告", expanded=False):
        st.markdown(demo["report"])
    with st.expander("证据边界与尚未验证的事项", expanded=False):
        st.markdown(
            "**可复核：** 合成输入快照、公司财务数字、报告季度、"
            "正文中的 FIN 引用标记及格式化过程。\n\n"
            "**不可推断：** 真实市场事实、供应商数据可靠性、实际 LLM 推理质量、"
            "真实投资结果。本次没有调用金融数据接口或大模型。"
        )


def render_demo() -> None:
    st.markdown(
        '<div class="demo-eyebrow">INTERACTIVE WALKTHROUGH · SYNTHETIC DATA</div>'
        '<div class="demo-headline">沿研究工作流，逐步完成一份行业研究</div>'
        '<p class="demo-lead">从合成数据到行业判断、公司比较、反方论证与最终报告。'
        '每一步只展示当下需要的内容，支持前后切换和下载成果。</p>',
        unsafe_allow_html=True,
    )
    st.caption("🧪 预设离线案例 · 不连接真实数据源 · 不调用 LLM · 不产生模型费用")

    current_step = int(st.session_state.get("demo_step", 0))
    if current_step < 0 or current_step > len(STEPS):
        current_step = 0
        st.session_state["demo_step"] = 0
    _stepper(current_step)
    if current_step == 0:
        st.markdown("#### 四阶段研究 + 最终交付")
        st.markdown(
            "点击开始，从数据采集进入行业全景、公司深度、投资研判，"
            "最后查看报告及证据边界。整个过程是**交互式浏览预设案例**，"
            "不是模拟真实的网络请求或模型执行。"
        )
        if st.button(
            "▶ 开始工作流演示",
            key="demo_launch",
            type="primary",
            width="stretch",
        ):
            st.session_state["demo_step"] = 1
            st.rerun()
        return

    demo = build_demo()
    title, subheading = STEPS[current_step - 1]
    st.progress(current_step / len(STEPS),
                text=f"研究演示 · 第 {current_step} / {len(STEPS)} 步")
    st.markdown(f"### {current_step:02d} · {title}")
    st.caption(subheading)

    if current_step == 1:
        _render_data_stage(demo)
    elif current_step == 2:
        _render_industry_stage(demo)
    elif current_step == 3:
        _render_company_stage(demo)
    elif current_step == 4:
        _render_thesis_stage(demo)
    else:
        _render_delivery_stage(demo)

    st.divider()
    previous, next_stage = st.columns(2)
    with previous:
        if st.button(
            "← 上一阶段",
            key="demo_prev",
            disabled=current_step == 1,
            width="stretch",
        ):
            st.session_state["demo_step"] = current_step - 1
            st.rerun()
    with next_stage:
        if current_step < len(STEPS):
            if st.button(
                "下一阶段 →",
                key="demo_next",
                type="primary",
                width="stretch",
            ):
                st.session_state["demo_step"] = current_step + 1
                st.rerun()
        elif st.button("↻ 重新体验", key="demo_restart", width="stretch"):
            st.session_state["demo_step"] = 0
            st.rerun()

"""A dedicated no-key demonstration interface, deliberately separate from live research."""

import pandas as pd
import streamlit as st

from tools.demo_experience import build_demo
from tools.demo_export import render_demo_html


def render_demo():
    st.markdown(
        '<div class="demo-eyebrow">PRODUCT WALKTHROUGH · v0.1 · SYNTHETIC</div>'
        '<div class="demo-headline">一键体验一份完整的行业研究</div>'
        '<p class="demo-lead">看清 AI Research Agent 如何组织结构化信息、比较企业、'
        '提出投资假设并保留证据边界。无需账户、API Key 或金融数据连接。</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown("**这份 Demo 能让你看到什么？**")
        col_data, col_method, col_delivery = st.columns(3)
        with col_data:
            st.markdown("**01 · 数据可追溯**")
            st.caption("虚构公司、财务指标、报告季度和引用标记")
        with col_method:
            st.markdown("**02 · 研究可审查**")
            st.caption("行业全景、公司比较、假设与 Red Team 反方论证")
        with col_delivery:
            st.markdown("**03 · 成果可分享**")
            st.caption("完整 Markdown 报告和可直接发送的离线 HTML")

    st.info(
        "🧪 **固定合成案例，并非真实 AI 运行。** 所有公司、财务数字及判断均为虚构，"
        "不会联网、调用 LLM 或写入你的研究历史。"
    )

    if st.button(
        "▶ 一键体验完整研究 Demo",
        key="demo_launch",
        type="primary",
        width="stretch",
    ):
        st.session_state["demo_ready"] = True

    if not st.session_state.get("demo_ready"):
        st.caption("点击上方按钮直接查看完整研究成果。演示无费用，建议从「研究摘要」开始浏览。")
        return

    demo = build_demo()
    st.success("示例研究已加载 · 四阶段预设内容 · 无网络、无模型费用")
    st.markdown("### 演示成果总览")
    st.caption("先浏览下方的研究摘要与公司比较，或直接获取完整可分享的文件。")
    download_html, download_markdown = st.columns(2)
    with download_html:
        st.download_button(
            "📥 下载独立展示网页（HTML）",
            data=render_demo_html(demo),
            file_name="Research_Agent_纯合成数据_独立演示.html",
            mime="text/html",
            key="demo_share_html",
            width="stretch",
            help="无需安装，可在浏览器中打开；仅包含合成研究案例。",
        )
    with download_markdown:
        st.download_button(
            "📄 下载完整研究报告（Markdown）",
            data=demo["report"],
            file_name="Research_Agent_合成数据_演示报告.md",
            mime="text/markdown",
            key="demo_download",
            width="stretch",
        )
    cols = st.columns(4)
    with cols[0]:
        st.metric("合成公司", len(demo["companies"]))
    with cols[1]:
        st.metric("模拟总市值（亿元）", f"{demo['total_market_cap']:.0f}")
    with cols[2]:
        st.metric("平均 ROE（%）", f"{demo['average_roe']:.1f}")
    with cols[3]:
        st.metric("收入增速报告期", "不一致" if not demo["growth_comparable"]
                  else "一致")
    if not demo["growth_comparable"]:
        st.caption("主营业务收入同比来自不同季度，不计算样本平均值。")

    st.markdown("#### 四阶段研究路径")
    for i, (title, detail) in enumerate((
        ("数据采集", "读取内置合成快照"),
        ("行业全景", "构建规模、格局和待核实假设"),
        ("公司深度", "比较指标、所属季度与证据标签"),
        ("投资研判", "研究假设、反方观点与风险核验"),
    ), start=1):
        st.markdown(f"**{i}. {title}** · {detail}")

    tabs = st.tabs(["01 · 研究摘要", "02 · 公司比较", "03 · 完整报告", "04 · 证据与限制"])
    with tabs[0]:
        st.markdown(demo["summary"])
        st.markdown(demo["sections"]["industry_overview"])
        st.markdown(demo["sections"]["investment_thesis"])
    with tabs[1]:
        comparison = pd.DataFrame([
            {
                "公司": c["name"], "代码": c["code"],
                "模拟市值（亿元）": c["market_cap_billion"], "模拟 PE": c["pe"],
                "ROE（%）": c["roe_pct"], "毛利率（%）": c["gross_margin_pct"],
                "主营业务收入同比（%）": c["revenue_growth_pct"],
                "资产负债率（%）": c["debt_ratio_pct"],
                "ROE 报告期": (c.get("_metric_periods") or {}).get("roe_pct"),
            }
            for c in demo["companies"]
        ])
        st.dataframe(comparison, hide_index=True, width="stretch")
        st.bar_chart(comparison.set_index("公司")[["ROE（%）", "毛利率（%）"]])
        st.caption("仅展示两家虚构公司，不能外推真实行业结论。")
        st.markdown(demo["sections"]["company_deep_dive"])
    with tabs[2]:
        st.caption("此处展示完整 Markdown 正文、采集来源标签、财务数字对照和工作流附录。")
        st.markdown(demo["report"])
    with tabs[3]:
        st.markdown(
            "**哪些环节可以复核？** 预设行业数据、两家公司的每项财务数字、所属季度，"
            "以及报告正文中带 FIN 标记的数字，可以对照本次合成数据快照。"
        )
        st.markdown(
            "**哪些结论没有被验证？** 真实市场事实、供应商数据真实性、"
            "AI 在真实研究中的推理质量、真实投资决策结果。"
        )
        source_rows = [
            {"数据维度": title,
             "来源标签": demo["package"].get(key, {}).get("source", "未提供"),
             "类别": "合成数据"}
            for key, title in (
                ("market_data", "行情"), ("financial_data", "财务"),
                ("announcement_data", "公告"), ("news_data", "新闻"),
            )
        ]
        st.dataframe(pd.DataFrame(source_rows), hide_index=True, width="stretch")
        with st.expander("查看演示快照与流程元数据"):
            st.json({
                "mode": "offline_synthetic_demo",
                "fixture_snapshot": demo["snapshot_date"],
                "stages": list(demo["sections"]),
                "model_called": False,
                "network_called": False,
                "report_characters": len(demo["report"]),
            })
    st.divider()
    st.caption(
        "想运行自己的行业研究？在页面顶部选择「🔬 真实研究」，再配置数据源与模型。"
        "真实模式依赖在线接口，研究结果仍须独立核验。"
    )

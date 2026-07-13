"""Charts — interactive Altair visualizations for the Streamlit UI."""

import pandas as pd
import streamlit as st
from ui.styles import COLORS

try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False


def render_market_charts(context):
    """Render interactive charts after stage 1 data collection."""
    if not HAS_ALTAIR:
        st.caption("📊 图表功能需要安装 altair: `pip install altair`")
        return

    market_data = context.get("market_data", {})
    fin_data = context.get("financial_data", {})

    constituents = market_data.get("成分股", []) or []
    fin_companies = fin_data.get("公司财务", []) or []

    if not constituents:
        st.caption("无成分股数据，跳过图表")
        return

    # Merge market + financial
    fin_by_code = {c.get("code", ""): c for c in fin_companies}
    rows = []
    for c in constituents:
        code = c.get("code", "")
        fc = fin_by_code.get(code, {})
        rows.append({
            "name": c.get("name", code),
            "price": c.get("price"),
            "change_pct": c.get("change_pct"),
            "pe": c.get("pe"),
            "market_cap_billion": c.get("market_cap_billion"),
            "roe": fc.get("roe_pct"),
            "gross_margin": fc.get("gross_margin_pct"),
            "revenue_growth": fc.get("revenue_growth_pct"),
            "debt_ratio": fc.get("debt_ratio_pct"),
        })

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["price"]).copy()
    if df.empty:
        return

    st.markdown("---")
    st.markdown('<p class="section-title">📊 数据可视化</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        _render_market_cap_chart(df)
    with col2:
        _render_pe_chart(df)

    col3, col4 = st.columns(2)
    with col3:
        _render_change_chart(df)
    with col4:
        _render_profitability_scatter(df)


def _render_market_cap_chart(df: pd.DataFrame):
    """Top 15 constituents by market cap."""
    chart_df = df.dropna(subset=["market_cap_billion"]).copy()
    if chart_df.empty:
        st.caption("无市值数据")
        return

    chart_df = chart_df.nlargest(15, "market_cap_billion")

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("market_cap_billion:Q", title="市值（亿）"),
            y=alt.Y("name:N", sort="-x", title=None),
            color=alt.Color("market_cap_billion:Q",
                           scale=alt.Scale(scheme="blues"),
                           legend=None),
            tooltip=["name", "market_cap_billion", "pe", "change_pct"],
        )
        .properties(title="成分股市值排名", height=350)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_pe_chart(df: pd.DataFrame):
    """PE distribution histogram."""
    chart_df = df.dropna(subset=["pe"]).copy()
    chart_df = chart_df[chart_df["pe"] > 0]
    if chart_df.empty:
        st.caption("无 PE 数据")
        return

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("pe:Q", bin=alt.Bin(maxbins=12), title="PE (TTM)"),
            y=alt.Y("count()", title="公司数量"),
            color=alt.value(COLORS["green"]),
            tooltip=["count()"],
        )
        .properties(title="PE 分布", height=350)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_change_chart(df: pd.DataFrame):
    """Change % bar chart."""
    chart_df = df.dropna(subset=["change_pct"]).copy()
    if chart_df.empty:
        st.caption("无涨跌幅数据")
        return

    chart_df = chart_df.copy()
    chart_df["color"] = chart_df["change_pct"].apply(
        lambda x: COLORS["red"] if x > 0 else COLORS["blue"]
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("change_pct:Q", title="涨跌幅 (%)"),
            y=alt.Y("name:N", sort="-x", title=None),
            color=alt.Color("color:N", scale=None, legend=None),
            tooltip=["name", "change_pct", "price"],
        )
        .properties(title="涨跌幅排行", height=350)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_profitability_scatter(df: pd.DataFrame):
    """ROE vs Gross Margin scatter."""
    chart_df = df.dropna(subset=["roe", "gross_margin"]).copy()
    if chart_df.empty:
        st.caption("无盈利数据")
        return

    chart = (
        alt.Chart(chart_df)
        .mark_circle(size=80)
        .encode(
            x=alt.X("gross_margin:Q", title="毛利率 (%)"),
            y=alt.Y("roe:Q", title="ROE (%)"),
            color=alt.Color("market_cap_billion:Q",
                           scale=alt.Scale(scheme="blues"),
                           title="市值(亿)"),
            tooltip=["name", "roe", "gross_margin", "revenue_growth", "debt_ratio"],
        )
        .properties(title="盈利质量：ROE vs 毛利率", height=350)
    )
    st.altair_chart(chart, use_container_width=True)

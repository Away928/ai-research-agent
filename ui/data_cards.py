"""Data cards — stage 1 data display (market, financial, announcements, news, user data)."""

import pandas as pd
import streamlit as st


def render_data_cards(context: dict):
    """Render data cards after stage 1 (data collection) completes."""
    from tools import DataSourceManager

    raw = context.get("raw_data", {})
    summary = DataSourceManager.build_summary(raw)
    dims = summary.get("各维度明细", {})

    user_data = dims.get("用户补充数据", {})
    _render_status_bar(summary)
    _render_market_and_financial(dims.get("行情", {}), dims.get("财务", {}))
    _render_announcements_and_news(dims.get("公告", {}), dims.get("新闻", {}))
    _render_user_supplements(user_data)


def _render_status_bar(summary: dict):
    """Top-line status bar showing data source health."""
    status_text = "  |  ".join(
        f"{'✅' if '✅' in str(summary.get('数据源状态', {}).get(k, '')) else ('⚠️' if '⚠️' in str(summary.get('数据源状态', {}).get(k, '')) else '❌')} {label}"
        for k, label in [
            ("market_data", "行情"), ("financial_data", "财务"),
            ("announcement_data", "公告"), ("news_data", "新闻"),
            ("user_data", "用户"),
        ]
    )
    st.success(f"📊 数据采集完成 — {summary.get('采集时间', '')}  |  {status_text}")


def _render_market_and_financial(mkt: dict, fin: dict):
    """Row 1: market data + financial data side by side."""
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown('<p class="section-title-small">📈 行情数据</p>', unsafe_allow_html=True)
            st.caption("来源：腾讯财经 + 新浪财经 + baostock · 时效：🟢 实时")
            st.caption(f"采集时间：{mkt.get('采集时间', 'N/A')}")

            overview = mkt.get("概览", "")
            if overview:
                for line in overview.split("\n"):
                    st.markdown(f"**{line}**")

            constituents = mkt.get("成分股", []) or []
            st.markdown(f"成分股：**{len(constituents)} 只**")

            with st.expander(f"查看全部成分股 ({len(constituents)} 只)"):
                if constituents:
                    df = pd.DataFrame(constituents)
                    st.dataframe(
                        df,
                        column_config={
                            "代码": "代码", "名称": "名称",
                            "价格": st.column_config.NumberColumn("价格", format="¥%.2f"),
                            "涨跌幅(%)": st.column_config.NumberColumn("涨跌幅", format="%+.1f%%"),
                            "PE": st.column_config.NumberColumn("PE", format="%.1f"),
                            "市值(亿)": st.column_config.NumberColumn("市值(亿)", format="%.0f"),
                        },
                        hide_index=True,
                        use_container_width=True,
                    )

    with c2:
        with st.container(border=True):
            st.markdown('<p class="section-title-small">💰 财务数据</p>', unsafe_allow_html=True)
            fin_period = fin.get('数据期间', '未知')
            st.caption(f"来源：baostock 日线财报 · 时效：🟡 T+1 · 期间：**{fin_period}**")
            st.caption(f"采集时间：{fin.get('采集时间', 'N/A')}")
            st.markdown(f"覆盖公司：**{fin.get('覆盖公司数', 0)} 家**")
            indicators = fin.get("指标", [])
            if indicators:
                st.markdown(f"指标：{' / '.join(indicators)}")

            fin_cos = fin.get("公司", []) or []
            with st.expander(f"查看全部财务指标 ({len(fin_cos)} 家公司)"):
                if fin_cos:
                    df_fin = pd.DataFrame(fin_cos)
                    st.dataframe(
                        df_fin,
                        column_config={
                            "代码": None,
                            "名称": "公司",
                            "数据期间": "财报季度",
                            "ROE(%)": st.column_config.NumberColumn("ROE%", format="%+.1f"),
                            "毛利率(%)": st.column_config.NumberColumn("毛利率%", format="%.1f"),
                            "营收增速(%)": st.column_config.NumberColumn("营收增速%", format="%+.1f"),
                            "净利增速(%)": st.column_config.NumberColumn("净利增速%", format="%+.1f"),
                            "负债率(%)": st.column_config.NumberColumn("负债率%", format="%.1f"),
                        },
                        hide_index=True,
                        use_container_width=True,
                    )


def _render_announcements_and_news(ann: dict, nws: dict):
    """Row 2: announcements + news side by side."""
    c3, c4 = st.columns(2)

    with c3:
        with st.container(border=True):
            st.markdown('<p class="section-title-small">📋 公告</p>', unsafe_allow_html=True)
            st.caption("来源：巨潮资讯网 cninfo.com.cn")
            ann_list = ann.get("列表", []) or []
            ann_dates = [a['日期'] for a in ann_list if a.get('日期')]
            date_range = f"{min(ann_dates)} ~ {max(ann_dates)}" if ann_dates else "未知"
            st.caption(f"日期范围：{date_range} · 共 **{ann.get('数量', 0)} 条**")
            if ann_list:
                _render_item_list(ann_list, fmt=lambda a: f"[{a['日期']}] **[{a['类型']}]** {a['公司']} — {a['标题']}")
            else:
                st.caption("暂无公告数据")

    with c4:
        with st.container(border=True):
            st.markdown('<p class="section-title-small">📰 新闻</p>', unsafe_allow_html=True)
            st.caption("来源：AKShare 聚合公开财经媒体")
            nws_list = nws.get("列表", []) or []
            nws_dates = [n['日期'] for n in nws_list if n.get('日期')]
            date_range = f"{min(nws_dates)} ~ {max(nws_dates)}" if nws_dates else "未知"
            st.caption(f"日期范围：{date_range} · 共 **{nws.get('数量', 0)} 条**")
            if nws_list:
                _render_item_list(nws_list, fmt=lambda n: f"[{n['日期']}] {n.get('来源媒体', '')} — {n['标题']}")
            else:
                st.caption("暂无新闻数据")


def _render_item_list(items: list, fmt):
    """Render first 3 items in a list, with expander for the rest."""
    show_count = min(3, len(items))
    for item in items[:show_count]:
        st.markdown(f"- {fmt(item)}")
    if len(items) > show_count:
        with st.expander(f"查看全部 {len(items)} 条"):
            for item in items[show_count:]:
                st.markdown(f"- {fmt(item)}")


def _render_user_supplements(user_data: dict):
    """Row 3: user supplementary data."""
    user_items = user_data.get("列表", []) or []
    if user_items:
        st.markdown("---")
        st.markdown('<p class="section-title-small">📝 用户补充数据</p>', unsafe_allow_html=True)
        st.caption(f"来源：用户上传文件 · 共 **{len(user_items)} 条**")
        cat_emoji = {"会议纪要": "🎙️", "专家访谈": "👤", "调研笔记": "📓"}
        for item in user_items:
            emoji = cat_emoji.get(item.get("类别", ""), "📄")
            st.markdown(
                f"- {emoji} [{item['日期']}] **{item['标题']}** — {item.get('来源', '未知')}"
            )
    else:
        st.markdown("---")
        st.caption("📝 用户补充数据：无（上传 .md/.txt/.pdf/.docx 文件即可纳入分析）")

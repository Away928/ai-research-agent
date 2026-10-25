"""Present a real research attempt with honest success, data-only and failure states.

Persist only displayable results in a Streamlit session. Never store API keys,
uploaded file bytes or raw input bundles in the result view model.
"""

from datetime import datetime
from tools.collection_brief import format_collection_brief


def build_run_result(agent, errors: dict) -> dict:
    """Create a safe-to-display summary without credentials or file inputs."""
    raw = agent.context.get("raw_data") or {}
    formatted = agent.context.get("formatted_report") or ""
    if errors:
        status = "failed"
    elif agent.ai_mode and formatted.strip():
        status = "report"
    else:
        status = "data_only"
    return {
        "status": status,
        "industry": agent.industry,
        "session_id": agent.session_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "formatted_report": formatted if status == "report" else "",
        "collection_brief": (
            format_collection_brief(agent.industry, raw)
            if status == "data_only" else ""
        ),
        "errors": list(errors.keys()),
        "source_status": {
            key: str((raw.get("数据源状态") or {}).get(key, "未返回"))
            for key in ("market_data", "financial_data",
                        "announcement_data", "news_data")
        },
        "completed_stages": [log["stage"] for log in agent.work_log],
    }


STAGE_NAMES = {
    "data_collection": "数据采集",
    "industry_overview": "行业全景",
    "company_deep_dive": "公司深度",
    "investment_thesis": "投资研判",
}


def render_run_result(result: dict):
    """Render actionable deliverables; can be called on later Streamlit reruns."""
    import streamlit as st

    status = result.get("status")
    industry = result.get("industry", "未命名")
    time = result.get("created_at", "")
    st.divider()
    st.markdown("### 最近一次真实研究结果")
    st.caption(f"行业：{industry} · {time} · 当前会话可查看；不会自动生成公开分享链接")

    if status == "report":
        st.success("✅ 四阶段研究已完成，格式化报告可查看、下载；结论仍需人工核验。")
        report = result.get("formatted_report") or ""
        if report:
            st.download_button(
                "📥 下载完整研究报告（Markdown，含来源与附录）",
                data=report,
                file_name=f"Research_Agent_{result['session_id']}_完整报告.md",
                mime="text/markdown",
                key="real_report_download",
                width="stretch",
            )
            with st.expander("📖 阅读完整格式化报告", expanded=True):
                st.markdown(report)
    elif status == "data_only":
        st.info(
            "📊 已结束数据采集阶段（没有执行 AI 研究），"
            "已生成可下载的采集简报；是否有足够数据请查看来源状态。"
        )
        brief = result.get("collection_brief") or ""
        if brief:
            st.download_button(
                "📥 下载数据采集简报（Markdown，非 AI 投资报告）",
                data=brief,
                file_name=f"Research_Agent_{result['session_id']}_数据采集简报.md",
                mime="text/markdown",
                key="real_collection_download",
                width="stretch",
            )
            with st.expander("📖 查看本次采集简报", expanded=True):
                st.markdown(brief)
    else:
        failed = "、".join(
            STAGE_NAMES.get(name, name) for name in result.get("errors", [])
        )
        st.error(
            f"❌ 研究中断（失败阶段：{failed or '未知'}）。"
            "后续依赖阶段已停止，未将结果标记为完整研究。"
        )
        st.caption("请检查网络、数据源状态、模型配置或工作流日志后重试。")

    source_status = result.get("source_status") or {}
    with st.expander("数据源状态及本次执行范围"):
        for key, label in (
            ("market_data", "行情"), ("financial_data", "财务"),
            ("announcement_data", "公告"), ("news_data", "新闻"),
        ):
            st.caption(f"{label}：{source_status.get(key, '未返回')}")
        done = [
            STAGE_NAMES.get(stage, stage)
            for stage in result.get("completed_stages", [])
        ]
        st.caption("已记录阶段：" + (" → ".join(done) if done else "无"))
        st.caption("数据来源状态来自采集程序，不能直接证明内容真实性或实时报价时效。")

"""Sidebar — API config, industry list, data source info."""

import os
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent


def render_sidebar(industries: dict) -> dict:
    """Render the sidebar and return user's API config values.

    Returns:
        dict with keys: model_backend, api_key, base_url, model_name
    """
    with st.sidebar:
        st.markdown("### 🔑 API 配置")

        # 后端选择
        backend_options = ["openai_compat", "anthropic"]
        backend_labels = {
            "openai_compat": "OpenAI 兼容 (DeepSeek / 千问 / 豆包…)",
            "anthropic": "Anthropic (Claude)",
        }
        model_backend = st.selectbox(
            "模型后端",
            options=backend_options,
            format_func=lambda x: backend_labels[x],
            help="选择使用哪个模型后端",
            key="sidebar_backend",
        )

        # API Key — 用户输入优先，留空走环境变量
        if model_backend == "anthropic":
            env_key = (
                os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or os.environ.get("ANTHROPIC_API_KEY") or ""
            )
            key_placeholder = "sk-ant-...（留空则自动读取环境变量）"
        else:
            env_key = os.environ.get("OPENAI_API_KEY") or ""
            key_placeholder = "sk-...（留空则自动读取环境变量）"

        api_key = st.text_input(
            "API Key",
            type="password",
            value=env_key,
            placeholder=key_placeholder,
            help="留空则自动读取环境变量，此处输入仅本次会话有效且不存储",
            key="sidebar_apikey",
        )
        api_key = api_key or env_key

        # Base URL 和 Model — 两种后端都显示
        if model_backend == "anthropic":
            base_url_default = os.environ.get(
                "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
            model_default = os.environ.get(
                "ANTHROPIC_MODEL", "claude-sonnet-4-6")
        else:
            base_url_default = os.environ.get(
                "OPENAI_BASE_URL", "https://api.deepseek.com/v1")
            model_default = os.environ.get(
                "OPENAI_MODEL", "deepseek-chat")

        base_url = st.text_input(
            "Base URL",
            value=base_url_default,
            placeholder="https://api.deepseek.com/v1" if model_backend == "openai_compat" else "https://api.anthropic.com/v1",
            help="API 端点地址，可修改为代理或其他兼容服务",
            key="sidebar_baseurl",
        )
        base_url = base_url or base_url_default

        model_name = st.text_input(
            "Model",
            value=model_default,
            placeholder="deepseek-chat" if model_backend == "openai_compat" else "claude-sonnet-4-6",
            help="模型名称",
            key="sidebar_model",
        )
        model_name = model_name or model_default

        # 状态提示
        if api_key:
            backend_hint = "Anthropic" if model_backend == "anthropic" else "OpenAI 兼容"
            st.success(f"✅ API Key 已设置 — {backend_hint} 后端就绪")
        else:
            st.warning(
                "⚠️ 降级模式\n\n"
                "未设置 API Key，数据采集正常但 AI 分析不运行。"
                "各阶段 Prompt 会打印到终端，可手动复制到 AI 工具使用。"
            )

        st.divider()
        _render_industry_list(industries)
        st.divider()
        _render_history()
        st.divider()
        _render_data_source_info()
        st.divider()
        _render_footer()

    return {
        "model_backend": model_backend,
        "api_key": api_key,
        "base_url": base_url,
        "model_name": model_name,
    }


def _render_industry_list(industries: dict):
    """Render available industries grouped by category."""
    st.markdown("### 🔍 可用行业")
    if not industries:
        st.caption("未能加载行业列表")
        return
    for cat in ["AI与科技", "先进制造", "消费与金融", "医疗健康", "其他"]:
        items = {k: v for k, v in industries.items() if v["category"] == cat}
        if not items:
            continue
        st.markdown(
            f'<span style="font-size:0.78rem;font-weight:600;color:#0a1628;">{cat}</span>',
            unsafe_allow_html=True)
        for name in items:
            st.caption(f"  {name}")


def _render_data_source_info():
    """Render data source architecture table."""
    st.markdown("### ⚙️ 数据源")
    st.caption("**行情** — 腾讯 + 新浪 + baostock")
    st.caption("**财务** — baostock 日线财报")
    st.caption("**公告** — 巨潮资讯网")
    st.caption("**新闻** — AKShare")
    st.caption("**用户** — 上传 .md/.pdf/.docx")

    st.markdown("### 🗂️ 方式")
    st.caption("**服务** — 行情 + 新闻 实时拉取")
    st.caption("**缓存** — 财务 + 公告 7 天缓存")
    st.caption("**补充** — 用户上传 .md/.pdf/.docx")


def _render_footer():
    """Render sidebar footer."""
    if st.button("📖 查看 README"):
        readme_path = ROOT / "README.md"
        if readme_path.exists():
            st.markdown(readme_path.read_text(encoding="utf-8"))
    st.divider()
    st.caption("作者：William Lu")
    st.caption("CUHKSZ 金融 2028 届")
    st.caption("[GitHub](https://github.com/Away928/ai-research-agent)")


def _render_history():
    """Render recent research history from _history.json."""
    st.markdown('### 📜 历史')
    history_path = ROOT / 'demo_output' / '_history.json'
    if not history_path.exists():
        st.caption('暂无历史记录')
        return

    try:
        import json
        records = json.loads(history_path.read_text(encoding='utf-8'))
    except Exception:
        st.caption('历史记录读取失败')
        return

    if not records:
        st.caption('暂无历史记录')
        return

    for r in reversed(records[-5:]):  # 最近 5 条
        emoji = '🤖' if 'AI' in r.get('mode', '') else '📋'
        ds = r.get('data_sources', {})
        ok = sum(1 for v in ds.values() if '✅' in str(v))
        total = len(ds) if ds else 4
        with st.expander(
            f'{emoji} {r["industry"]} — {r["duration_s"]}s ({ok}/{total}源)',
            expanded=False,
        ):
            st.caption(f'时间: {r["time"]}')
            st.caption(f'模式: {r["mode"]}')
            sources_text = ' | '.join(f'{k}:{v}' for k, v in ds.items())
            st.caption(f'数据源: {sources_text}')
            preview = r.get('preview', '')
            if preview:
                st.caption(f'预览: {preview[:150]}...')
            report_file = r.get('report_file', '')
            if report_file:
                report_path = ROOT / 'demo_output' / report_file
                if report_path.exists():
                    st.caption(f'📄 {report_file}')

"""
Streamlit Web 界面 — AI Research Agent
=======================================

启动方式:
    streamlit run app.py
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from agent_workflow import AIResearchAgentV2

from ui.styles import CUSTOM_CSS
from ui.sidebar import render_sidebar
from ui.input_area import render_input_area
from ui.data_cards import render_data_cards
from ui.charts import render_market_charts
from ui.welcome import render_welcome
from ui.research_result import build_run_result, render_run_result
from ui.live_access import live_access_configured, verify_live_token


# ── 页面配置 ──────────────────────────────────────────────

st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── 可用行业列表 ──────────────────────────────────────────

def _load_industries():
    """从新浪概念板块 Node Map 加载可用行业列表，附分类标签。"""
    try:
        from tools.data_sources.market_sources import _SINA_CONCEPT_NODE_MAP
    except Exception:
        return {}

    ai_tech = {"AI算力", "人工智能", "信息技术", "移动互联网", "智能汽车", "半导体", "新硬件"}
    advanced_mfg = {"机器人", "工业4.0", "新能源汽车", "能源金属"}
    consumer_fin = {"消费", "金融科技"}
    healthcare = {"生物医药", "医药健康"}

    result = {}
    for name in _SINA_CONCEPT_NODE_MAP:
        if name in ai_tech:
            cat = "AI与科技"
        elif name in advanced_mfg:
            cat = "先进制造"
        elif name in consumer_fin:
            cat = "消费与金融"
        elif name in healthcare:
            cat = "医疗健康"
        else:
            cat = "其他"
        result[name] = {"count": None, "category": cat}
    return result


AVAILABLE_INDUSTRIES = _load_industries()


# ── 样式 ──────────────────────────────────────────────────

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── 标题区 ────────────────────────────────────────────────

st.markdown(
    '<p class="hero-title">Research<span class="hero-dot">.</span>Agent</p>',
    unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">面向投资研究的数据采集、行业分析、公司比较与证据复核工作流</p>',
    unsafe_allow_html=True)

st.divider()


# ── 选择体验方式 ───────────────────────────────────────────
# Public deployments intentionally offer only the synthetic offline demo.
# Merely knowing this app's URL or a provider API key must never expose the
# network/LLM path. An owner must configure BOTH server-side options and
# provide the independent access token before the real-research UI is built.
demo_option = "🧪 体验演示（无需配置）"
live_option = "🔬 真实研究（使用数据源）"
live_configured = live_access_configured()
if live_configured and not st.session_state.get("live_unlocked", False):
    with st.sidebar:
        st.markdown("#### 🔐 私人研究入口")
        st.caption("仅限授权使用。公开演示不调用数据源或大模型。")
        with st.form("private_live_access", clear_on_submit=True):
            owner_token = st.text_input(
                "私人访问凭证", type="password", autocomplete="off",
                help="此凭证不同于模型 API Key；不会上传到 GitHub。")
            submitted = st.form_submit_button("解锁私人研究")
        if submitted:
            if verify_live_token(owner_token):
                st.session_state["live_unlocked"] = True
                st.rerun()
            else:
                st.error("凭证无效。")
elif live_configured and st.session_state.get("live_unlocked", False):
    with st.sidebar:
        st.caption("🔓 已授权使用私人研究")
        if st.button("锁定私人研究", key="lock_live"):
            st.session_state["live_unlocked"] = False
            # Drop private widget values/results when the owner locks the UI.
            for key in list(st.session_state):
                if key.startswith("sidebar_apikey_") or key in {
                    "real_last_result", "experience_mode", "input_uploader",
                    "input_select", "sidebar_baseurl", "sidebar_model",
                    "sidebar_backend",
                }:
                    st.session_state.pop(key, None)
            st.rerun()

live_allowed = live_configured and bool(st.session_state.get("live_unlocked", False))
if live_allowed:
    experience = st.radio(
        "选择体验方式",
        [demo_option, live_option],
        horizontal=True,
        key="experience_mode",
    )
else:
    # A public-only app has no choice to make. Avoid a redundant one-item radio.
    experience = demo_option

if experience.startswith("🧪"):
    # This path deliberately never instantiates the live agent or API client.
    from ui.demo import render_demo
    render_demo()
    industry = ""
    started = False
else:
    # Defense in depth against forged UI state or accidental feature exposure.
    if not (live_access_configured() and st.session_state.get("live_unlocked", False)):
        st.error("真实研究未获得服务端授权。")
        st.stop()
    sidebar_config = render_sidebar(AVAILABLE_INDUSTRIES)
    model_backend = sidebar_config["model_backend"]
    api_key = sidebar_config["api_key"]
    base_url = sidebar_config["base_url"]
    model_name = sidebar_config["model_name"]

    input_data = render_input_area(AVAILABLE_INDUSTRIES)
    industry = input_data["industry"]
    uploaded_files = input_data["uploaded_files"]
    upload_category = input_data.get("upload_category", "其他")
    started = input_data["started"]

    if industry:
        if api_key:
            st.info(
                "🤖 **完整研究模式**：将访问外部金融数据源并调用所选模型 API。"
                "模型调用可能产生费用；已找到密钥不代表连通性或余额得到验证。"
            )
        else:
            st.info(
                "📊 **仅数据采集模式**：没有 API Key。本次只尝试收集实际可用的"
                "市场、财务、公告与新闻数据，不调用大模型，也不会生成 AI 投研报告。"
            )
        if uploaded_files:
            st.warning(
                "上传材料会进入本次研究的数据处理流程。配置模型时，"
                "部分内容可能被发送至所选第三方模型服务；请勿上传未经授权的资料。"
            )


# ── Pipeline 渲染器 ─────────────────────────────────────

def _render_pipeline_html(current: int, error_stage: int = -1,
                          stage_times: dict = None):
    """Generate the 4-node pipeline timeline HTML.

    Args:
        current: 当前进行到的阶段索引 (0-based, -1 表示未开始)
        error_stage: 出错的阶段索引，-1 表示无错误
        stage_times: {stage_index: seconds} 已完成的阶段耗时
    """
    stage_times = stage_times or {}
    stages = [
        ("1", "数据采集"),
        ("2", "行业全景"),
        ("3", "公司深度"),
        ("4", "投资研判"),
    ]
    nodes_html = []
    for i, (num, label) in enumerate(stages):
        if error_stage >= 0 and i == error_stage:
            cls = "error"
        elif i < current:
            cls = "done"
        elif i == current:
            cls = "active"
        else:
            cls = ""

        # 耗时标注
        if i in stage_times:
            time_str = f"{stage_times[i]:.0f}s"
        elif i == current:
            time_str = "…"
        else:
            time_str = ""

        time_markup = f'<div class="pipeline-time">{time_str}</div>' if time_str else ""
        nodes_html.append(
            f'<div class="pipeline-node">'
            f'<div class="pipeline-dot {cls}">{num}</div>'
            f'<div class="pipeline-label {cls}">{label}</div>'
            f'{time_markup}'
            f'</div>'
        )
    track = (
        '<div class="pipeline-track">'
        f'<div class="pipeline-line"></div>'
        f'{"".join(nodes_html)}'
        '</div>'
    )
    return track


# ── 执行区 ────────────────────────────────────────────────

if started and industry:
    # A new run replaces the prior in-session deliverable; do not reuse a stale
    # report when a new attempt fails or returns data-only.
    st.session_state.pop("real_last_result", None)
    # 准备上传文件（携带类别信息）
    upload_list = []
    if uploaded_files:
        for f in uploaded_files:
            data = f.read()
            f.seek(0)
            upload_list.append({
                "name": f.name,
                "content": data,
                "category": upload_category,
            })

    agent = AIResearchAgentV2(
        industry=industry,
        api_key=api_key,
        model_backend=model_backend,
        base_url=base_url,
        model=model_name,
        uploads=upload_list,
    )

    # ── Pipeline 时间轴（一次性渲染，避免 DOM 冲突）──
    st.markdown("### ⏳ 执行进度")

    # 执行工作流
    stages = [
        ("data_collection", agent.stage_context_gathering, "数据采集", "腾讯+新浪+baostock 行情/财务/公告/新闻"),
        ("industry_overview", agent.stage_industry_overview, "行业全景", "行业定义、市场空间、竞争格局、政策技术"),
        ("company_deep_dive", agent.stage_company_deep_dive, "公司深度", "头部对比、盈利质量、估值、预警信号"),
        ("investment_thesis", agent.stage_investment_thesis, "投资研判", "周期判断、催化剂、机会排序 → 最终报告"),
    ]

    # Without a model, run collection only. Do not stage empty AI analysis
    # steps or render an empty result as a complete investment report.
    if not agent.ai_mode:
        stages = stages[:1]

    progress_bar = st.progress(0, text="准备开始…")
    stage_times = {}
    stage_reports = {}
    stage_errors = {}

    for i, (name, func, label, _desc) in enumerate(stages):
        progress_bar.progress((i) / len(stages), text=f"🔍 {label} — 执行中…")
        t0 = time.time()
        try:
            output = func()
        except Exception as e:
            stage_errors[name] = f"{type(e).__name__}: {e}"
            progress_bar.progress((i) / len(stages), text=f"❌ {label} — 出错")
            # Each later stage depends on earlier data/analysis. Never present a
            # report constructed from incomplete evidence as a completed study.
            break
        elapsed = time.time() - t0
        stage_times[i] = elapsed

        # Collection success must not be invalidated by optional charts/cards.
        # Preserve the evidence receipt and result download even if a specific
        # visualization is incompatible with a sparse provider payload.
        if i == 0:
            for label, renderer in (
                ("数据卡片", render_data_cards),
                ("可视化图表", render_market_charts),
            ):
                try:
                    renderer(agent.context)
                except Exception:
                    st.warning(
                        f"⚠️ {label}暂时无法展示。数据采集结果仍保留在下方简报中，"
                        "不代表采集失败。"
                    )

        # 阶段 2/3/4 完成后展示中间报告
        if i >= 1 and output and len(output) > 50:
            stage_keys = {1: "industry_overview", 2: "company_deep_dive", 3: "investment_thesis"}
            stage_key = stage_keys[i]
            stage_reports[stage_key] = output
            icons = {1: ("🔍", "行业全景分析"), 2: ("🏢", "公司深度分析"), 3: ("📈", "投资研判（最终报告）")}
            icon, title = icons[i]
            with st.expander(f"{icon} {title} — 耗时 {elapsed:.0f}s", expanded=(i == 1)):
                st.markdown(output)
                st.download_button(
                    label=f"📥 下载{title}报告",
                    data=output,
                    file_name=f"{industry}_{stage_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key=f"dl_{stage_key}",
                )

    # ── Result is retained for subsequent Streamlit widget reruns ──
    if not stage_errors:
        progress_bar.progress(100, text=(
            "✅ 数据采集结束（无 AI 报告）" if not agent.ai_mode
            else "✅ 四阶段研究完成"
        ))
    total_duration = sum(s["duration_seconds"] for s in agent.work_log)

    # Record local attempt metadata, even if one stage failed. This is not
    # an endorsement of the produced figures.
    from agent_workflow import _append_history
    try:
        _append_history(agent, total_duration)
    except (OSError, ValueError, TypeError):
        st.warning("本地历史索引未能更新；本次研究结果仍可在下方查看或下载。")

    saved_result = build_run_result(agent, stage_errors)
    st.session_state["real_last_result"] = saved_result
    render_run_result(saved_result)

    # 历史报告文件
    demo_dir = ROOT / "demo_output"
    if demo_dir.exists():
        reports = sorted(
            [f for f in demo_dir.glob(f"*{industry.replace(' ', '_')}*")],
            key=lambda p: p.stat().st_mtime, reverse=True,
        )[:5]
        if reports:
            with st.expander("📂 最近报告文件", expanded=False):
                for rp in reports:
                    size_kb = rp.stat().st_size / 1024
                    mod_time = datetime.fromtimestamp(rp.stat().st_mtime).strftime("%H:%M:%S")
                    st.caption(f"📄 {rp.name}  |  {size_kb:.1f} KB  |  {mod_time}")

    # 工作日志
    with st.expander("📊 工作流日志"):
        st.json(agent.work_log)

elif not experience.startswith("🧪"):
    saved_result = st.session_state.get("real_last_result")
    if saved_result:
        render_run_result(saved_result)
    else:
        render_welcome()

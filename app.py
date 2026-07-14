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
    '<p class="hero-sub">行业投研自动化 — 输入行业，AI 完成数据采集、分析、报告全链路</p>',
    unsafe_allow_html=True)

st.divider()


# ── 侧边栏 ────────────────────────────────────────────────

sidebar_config = render_sidebar(AVAILABLE_INDUSTRIES)
model_backend = sidebar_config["model_backend"]
api_key = sidebar_config["api_key"]
base_url = sidebar_config["base_url"]
model_name = sidebar_config["model_name"]


# ── 输入区 ────────────────────────────────────────────────

input_data = render_input_area(AVAILABLE_INDUSTRIES)
industry = input_data["industry"]
uploaded_files = input_data["uploaded_files"]
upload_category = input_data.get("upload_category", "其他")
started = input_data["started"]


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

    progress_bar = st.progress(0, text="准备开始…")
    stage_times = {}
    stage_reports = {}

    for i, (name, func, label, _desc) in enumerate(stages):
        progress_bar.progress((i) / len(stages), text=f"🔍 {label} — 执行中…")
        t0 = time.time()
        try:
            output = func()
        except Exception as e:
            output = f"错误: {e}"
            progress_bar.progress((i) / len(stages), text=f"❌ {label} — 出错")
        elapsed = time.time() - t0
        stage_times[i] = elapsed

        # 阶段 1 完成后展示数据亮点
        if i == 0:
            render_data_cards(agent.context)
            render_market_charts(agent.context)

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

    # ── 完成 ──
    progress_bar.progress(100, text="✅ 研究完成")
    total_ai = sum(s["duration_seconds"] for s in agent.work_log)

    # 写入历史索引
    from agent_workflow import _append_history
    _append_history(agent, total_ai)

    final_report = agent.context.get("final_report", "")
    formatted_report = agent.context.get("formatted_report", "")
    is_ai = bool(final_report and len(final_report) > 100)

    st.success(
        f"### {'✅' if is_ai else '📋'} 研究完成 — "
        f"总耗时 {total_ai:.0f} 秒（约 {total_ai/60:.1f} 分钟）"
    )
    if not is_ai:
        st.info(
            "降级模式：数据采集正常完成，报告框架已保存至 `demo_output/`，"
            "各阶段 Prompt 打印在终端，可手动复制到 AI 工具。"
        )

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

else:
    render_welcome()

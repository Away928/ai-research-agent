"""Welcome / initial state — card-based layout for first-time users."""

import streamlit as st


WELCOME_MARKDOWN = """\
### 👋 开始之前

1. 从下拉框选一个行业，或选择"自定义输入…"输入你想研究的行业名称
2. （可选）上传会议纪要、专家访谈或调研笔记
3. 点击 **「开始研究」**，Agent 将按 4 阶段自动完成全流程
"""

STAGES_INFO = [
    ("📊", "数据采集", "腾讯、新浪、baostock、巨潮、AKShare 五维数据 + 用户上传文件，纯 Python 采集"),
    ("🔍", "行业全景", "行业定义、市场空间、发展驱动力、竞争格局，标注所有不确定推断"),
    ("🏢", "公司深度", "头部公司对比、盈利质量、估值水平、财务预警，15+ 公司一次性扫描"),
    ("📝", "投资研判", "周期判断、催化剂排序、Red Team 压力测试，原始数据与 AI 分析并列防幻觉"),
]


def render_welcome():
    # ── 4 阶段卡片 ──
    cols = st.columns(4)
    for i, (emoji, title, desc) in enumerate(STAGES_INFO):
        with cols[i]:
            with st.container(height=170, border=True):
                st.markdown(
                    f'<div class="welcome-card-num">{emoji}</div>'
                    f'<div class="welcome-card-title">{title}</div>'
                    f'<div class="welcome-card-desc">{desc}</div>',
                    unsafe_allow_html=True)

    st.markdown("")

    # ── 使用说明 ──
    st.markdown(WELCOME_MARKDOWN)

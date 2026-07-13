"""Input area — industry selection, file upload, start button."""

import streamlit as st


def render_input_area(industries: dict) -> dict:
    """Render the industry selection and file upload area.

    Returns:
        dict with keys: industry (str), uploaded_files (list), upload_category (str), started (bool)
    """
    col_select, col_action = st.columns([4, 1])

    with col_select:
        # 与左侧一致的分类顺序
        cat_order = ["AI与科技", "先进制造", "消费与金融", "医疗健康", "其他"]
        grouped = {cat: {} for cat in cat_order}
        for name, info in (industries or {}).items():
            cat = info.get("category", "其他")
            grouped.setdefault(cat, {})[name] = info

        options = ["—— 选择行业 ——"]
        for cat in cat_order:
            for name in sorted(grouped.get(cat, {}).keys()):
                options.append(f"{name}  ({cat})")

        selected = st.selectbox(
            "选择行业",
            options=options,
            label_visibility="collapsed",
            key="input_select",
        )

    with col_action:
        started = st.button("🔍 开始研究", type="primary", use_container_width=True)

    industry = ""
    if selected and selected != "—— 选择行业 ——":
        industry = selected.split("  (")[0]

    # 上传补充数据
    with st.expander("📎 上传补充数据（会议纪要 / 专家访谈 / 调研笔记 / 其他）", expanded=False):
        st.caption("支持 .md / .txt / .pdf / .docx，上传后纳入 AI 全部 4 个分析阶段")
        uploaded_files = st.file_uploader(
            "选择文件",
            type=["md", "txt", "pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="可同时上传多个文件",
            key="input_uploader",
        )
        upload_category = st.selectbox(
            "数据类别",
            options=["会议纪要", "专家访谈", "调研笔记", "其他"],
            help="所有上传文件标记此类别",
            key="input_category",
        )
        if uploaded_files:
            st.caption(f"已选择 {len(uploaded_files)} 个文件 · 类别：{upload_category}")

    return {
        "industry": industry,
        "uploaded_files": uploaded_files or [],
        "upload_category": upload_category,
        "started": started,
    }

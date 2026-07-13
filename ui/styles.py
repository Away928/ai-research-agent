"""Custom CSS styles — Terminal Blue design system."""

# ── 色彩系统：专业深蓝 ──────────────────────────────────────
COLORS = {
    # 核心
    "navy":         "#0a1628",   # 主文字
    "blue":         "#1e4b8c",   # 强调色、链接、active 态
    "blue_light":   "#e8f0fe",   # active 底色/光晕
    "slate":        "#f4f6f9",   # 页面背景
    "white":        "#ffffff",   # 卡片背景
    # 语义
    "green":        "#0d7c4e",   # 完成态
    "green_light":  "#e6f4ec",   # 完成底色
    "red":          "#c52828",   # 错误/风险
    "red_light":    "#fce8e8",   # 错误底色
    # 辅助
    "gray_100":     "#f1f3f5",   # 浅分割
    "gray_200":     "#e2e6ea",   # 分割线
    "gray_400":     "#8b95a1",   # 辅助文字
    "gray_500":     "#5f6b7a",   # caption
}

CUSTOM_CSS = """\
<style>
/* ── Google Fonts ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600;700&display=swap');

/* ── 全局 ──────────────────────────────────────────────── */
* { font-family: 'Inter', -apple-system, sans-serif; }

/* ── Hero ───────────────────────────────────────────────── */
.hero-title {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 400;
    color: #0a1628;
    margin-bottom: 0;
    letter-spacing: -0.02em;
}
.hero-dot {
    color: #1e4b8c;
}
.hero-sub {
    font-size: 0.9rem;
    color: #5f6b7a;
    margin-top: 0.15rem;
    margin-bottom: 0;
    font-weight: 400;
}

/* ── Pipeline 时间轴 ───────────────────────────────────── */
.pipeline-track {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0.5rem 0.6rem 0.5rem;
    position: relative;
}
.pipeline-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
    flex: 0 0 auto;
    width: 90px;
    position: relative;
    z-index: 1;
}
.pipeline-dot {
    width: 42px;
    height: 42px;
    min-width: 42px;
    min-height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    font-weight: 600;
    background: #f1f3f5;
    color: #8b95a1;
    border: 2.5px solid #e2e6ea;
    transition: all 0.35s ease;
    font-family: 'Inter', sans-serif;
}
.pipeline-dot.active {
    background: #1e4b8c;
    color: #fff;
    border-color: #1e4b8c;
    box-shadow: 0 0 0 6px #e8f0fe;
}
.pipeline-dot.done {
    background: #0d7c4e;
    color: #fff;
    border-color: #0d7c4e;
    box-shadow: 0 0 0 6px #e6f4ec;
}
.pipeline-dot.error {
    background: #c52828;
    color: #fff;
    border-color: #c52828;
    box-shadow: 0 0 0 6px #fce8e8;
}
.pipeline-label {
    font-size: 0.73rem;
    font-weight: 500;
    color: #8b95a1;
    text-align: center;
    line-height: 1.3;
    max-width: 80px;
    transition: color 0.35s;
}
.pipeline-label.active { color: #1e4b8c; font-weight: 600; }
.pipeline-label.done { color: #0d7c4e; }
.pipeline-time {
    font-size: 0.7rem;
    color: #8b95a1;
    margin-top: -0.1rem;
}
.pipeline-line {
    position: absolute;
    top: 50%;
    left: calc(16.67% + 21px);
    right: calc(16.67% + 21px);
    height: 2.5px;
    background: #e2e6ea;
    border-radius: 2px;
    z-index: 0;
    transform: translateY(-26px);
}

/* ── Metric cards ──────────────────────────────────────── */
.metric-row {
    display: flex;
    gap: 0.8rem;
    margin: 0.3rem 0 0.8rem 0;
}
.metric-card {
    background: #fff;
    border: 1px solid #e2e6ea;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    flex: 1;
    min-width: 140px;
}
.metric-card-value {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.7rem;
    color: #0a1628;
    line-height: 1.2;
}
.metric-card-label {
    font-size: 0.76rem;
    color: #5f6b7a;
    margin-top: 0.15rem;
}

/* ── Badges ────────────────────────────────────────────── */
.ai-badge {
    background: #e6f4ec;
    color: #0d7c4e;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
}
.fallback-badge {
    background: #e8f0fe;
    color: #1e4b8c;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
}
.rm-badge {
    background: #fce8e8;
    color: #c52828;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* ── Stage cards ───────────────────────────────────────── */
.stage-card {
    background: #fff;
    border: 1px solid #e2e6ea;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
}
.stage-card-done {
    background: #f4f6f9;
    border: 1px solid #e6f4ec;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
}
.stage-card-active {
    background: #fff;
    border: 1.5px solid #1e4b8c;
    border-left: 3px solid #1e4b8c;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
}

/* ── Section titles ────────────────────────────────────── */
.section-title {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.25rem;
    color: #0a1628;
    margin: 0.8rem 0 0.3rem 0;
    letter-spacing: -0.01em;
}
.section-title-small {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.05rem;
    color: #0a1628;
    margin-bottom: 0.3rem;
}

/* ── Welcome cards ─────────────────────────────────────── */
.welcome-card {
    background: #fff;
    border: 1px solid #e2e6ea;
    border-radius: 12px;
    padding: 1.1rem;
    height: 100%;
    min-height: 155px;
    display: flex;
    flex-direction: column;
}
.welcome-card-num {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.9rem;
    color: #1e4b8c;
    line-height: 1;
}
.welcome-card-title {
    font-weight: 600;
    color: #0a1628;
    margin: 0.3rem 0 0.25rem 0;
    font-size: 0.92rem;
}
.welcome-card-desc {
    font-size: 0.8rem;
    color: #5f6b7a;
    line-height: 1.5;
}

/* ── Data summary box ──────────────────────────────────── */
.data-summary {
    background: #f4f6f9;
    border: 1px solid #e2e6ea;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.3rem 0;
}

/* ── Report ────────────────────────────────────────────── */
.report-container {
    max-width: 780px;
    font-size: 0.92rem;
    line-height: 1.75;
    color: #1e293b;
}
.report-container h1, .report-container h2, .report-container h3 {
    font-family: 'DM Serif Display', Georgia, serif;
    letter-spacing: -0.01em;
}
.report-container h1 { font-size: 1.6rem; color: #0a1628; }
.report-container h2 { font-size: 1.25rem; color: #0a1628; margin-top: 1.6rem; }
.report-container h3 { font-size: 1.05rem; color: #334155; }
.report-container table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.8rem 0;
    font-size: 0.82rem;
}
.report-container th {
    background: #f1f3f5;
    padding: 0.5rem 0.6rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e2e6ea;
}
.report-container td {
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid #f1f3f5;
}

/* ── Footer ────────────────────────────────────────────── */
.app-footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #e2e6ea;
    color: #8b95a1;
    font-size: 0.78rem;
    text-align: center;
}
.app-footer a { color: #5f6b7a; text-decoration: none; }
.app-footer a:hover { color: #1e4b8c; }

/* ── Misc ──────────────────────────────────────────────── */
.industry-tag {
    display: inline-block;
    background: #e8f0fe;
    color: #1e4b8c;
    padding: 1px 6px;
    border-radius: 8px;
    font-size: 0.7rem;
    margin-right: 4px;
}
.divider-fancy {
    height: 1px;
    background: #e2e6ea;
    margin: 1rem 0;
}

/* ── Custom input ───────────────────────────────────────── */
.custom-input-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
</style>"""

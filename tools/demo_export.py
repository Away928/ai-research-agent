"""Dependency-free, static and offline showcase export for the fictional Demo.

The rendered document contains only the built-in synthetic example. It makes no
network calls, embeds no scripts or external assets, and has no real user data.
"""
from html import escape
from tools.demo_experience import build_demo


_STYLE = """
:root{color-scheme:light;--ink:#101f36;--muted:#607189;--line:#dfe7f0;
--blue:#2e59a5;--pale:#edf3ff;--bg:#f5f7fb;--white:#fff;--warn:#9e431e}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,
BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7}
header,main,footer{max-width:1080px;margin:0 auto;padding:0 30px}
.brandline{display:flex;align-items:center;justify-content:space-between;gap:16px;
border-bottom:1px solid var(--line);padding-top:22px;padding-bottom:16px}
.wordmark{font-size:18px;font-weight:750;letter-spacing:-.5px}.wordmark span{color:var(--blue)}
.meta{color:var(--muted);font-size:12px}
nav{display:flex;gap:20px;flex-wrap:wrap;margin:14px 0 0;font-size:13px}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
.banner{padding:11px 16px;border:1px solid #efc8ac;border-radius:10px;
background:#fff7f1;color:#873a17;font-size:13px;font-weight:600;margin-top:28px}
.hero{padding:45px 0 33px}.eyebrow{text-transform:uppercase;font-size:11px;
font-weight:700;letter-spacing:2.1px;color:var(--blue)}
h1{font-size:clamp(30px,5vw,49px);line-height:1.22;letter-spacing:-1.4px;margin:14px 0}
h2{font-size:24px;letter-spacing:-.5px;line-height:1.35;margin:0 0 14px}
h3{font-size:17px;line-height:1.4;margin:0 0 10px}
p{margin:0 0 12px}.lede{font-size:16px;color:#475c74;max-width:720px}
.grid{display:grid;gap:15px}.metrics{grid-template-columns:repeat(4,minmax(0,1fr))}
.card,section.panel{background:var(--white);border:1px solid var(--line);
border-radius:13px;padding:22px;box-shadow:0 5px 24px rgba(25,47,79,.035)}
.kicker{color:var(--muted);font-size:12px;margin-bottom:5px}
.number{font-size:29px;font-weight:750;letter-spacing:-1px;line-height:1.2}
.sub{color:var(--muted);font-size:12px;margin-top:6px}
section.panel{margin:25px 0;padding:30px}
.stage-grid{grid-template-columns:repeat(4,minmax(0,1fr))}
.stage{padding:19px;border:1px solid var(--line);background:#fff;border-radius:12px}
.stage .step{font-size:11px;font-weight:750;color:var(--blue);margin-bottom:8px}
.stage h3{font-size:15px}.stage p{font-size:12px;color:var(--muted);margin:0}
.split{display:grid;grid-template-columns:1.1fr .9fr;gap:22px}
table{width:100%;border-collapse:collapse;min-width:680px;font-size:13px}
th{text-align:left;background:#eef3fb;color:#445c7a;font-weight:650}
td,th{padding:11px;border-bottom:1px solid var(--line);vertical-align:top}
td:not(:first-child){font-variant-numeric:tabular-nums}
.tablewrap{overflow-x:auto}
.note{color:var(--muted);font-size:12px;margin-top:14px}
.callout{border-left:3px solid var(--blue);padding:13px 17px;
background:var(--pale);border-radius:0 10px 10px 0}
.risk{border-left-color:#c17850;background:#fff6ee}
.pill{display:inline-block;border-radius:6px;background:var(--pale);
color:var(--blue);padding:2px 8px;font-size:11px;font-weight:700}
.check{color:#1a7257;font-weight:700}
details{border-top:1px solid var(--line);margin-top:20px;padding-top:13px}
summary{cursor:pointer;font-weight:650;color:var(--blue)}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.7 ui-monospace,
SFMono-Regular,Consolas,monospace;background:#f8fafd;border-radius:8px;padding:18px;
max-height:470px;overflow:auto}
footer{padding-bottom:45px;font-size:12px;color:var(--muted)}
@media(max-width:780px){header,main,footer{padding-left:17px;padding-right:17px}
.metrics,.stage-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.split{grid-template-columns:1fr}.card,section.panel{padding:20px}}
@media(max-width:420px){.metrics,.stage-grid{grid-template-columns:1fr}
.brandline{flex-direction:column;align-items:flex-start}.hero{padding-top:26px}}
@media print{body{background:#fff}nav,details{display:none}section.panel{break-inside:avoid}
.card,.stage,section.panel{box-shadow:none}header,main,footer{max-width:none}
.banner{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


def _cell(value) -> str:
    return escape(str(value), quote=True)


def render_demo_html(demo: dict = None) -> str:
    """Full self-contained demo web page, with original formatted report embedded."""
    demo = demo if demo is not None else build_demo()
    cos = demo["companies"]
    assert cos and all(c.get("name") for c in cos)
    headers = ("公司（虚构）", "模拟市值（亿元）", "ROE", "毛利率",
               "主营业务收入同比", "收入指标期间", "资产负债率")
    rows = []
    for c in cos:
        periods = c.get("_metric_periods") or {}
        row = (
            c["name"], f'{float(c["market_cap_billion"]):.0f}',
            f'{float(c["roe_pct"]):.1f}%',
            f'{float(c["gross_margin_pct"]):.1f}%',
            f'{float(c["revenue_growth_pct"]):.1f}%',
            periods.get("revenue_growth_pct", "未知"),
            f'{float(c["debt_ratio_pct"]):.1f}%',
        )
        rows.append("<tr>" + "".join(f"<td>{_cell(val)}</td>" for val in row) + "</tr>")
    heading = "".join(f"<th>{_cell(h)}</th>" for h in headers)
    table_rows = "\n".join(rows)
    company_names = "、".join(_cell(c["name"]) for c in cos)
    growth_caveat = (
        "两家公司主营业务收入同比的报告期不一致，未计算跨季度平均增速。"
        if not demo["growth_comparable"] else
        "两家公司的主营业务收入同比报告期相同；样本极小，统计不具代表性。"
    )
    steps = (
        ("01", "数据采集", "固定 JSON 合成快照，无金融 API"),
        ("02", "行业全景", "市场结构、产业链情景与待核实问题"),
        ("03", "公司深度", "指标对比、报告期和数据限制"),
        ("04", "投资研判", "假设、反方论证与下一步核实"),
    )
    cards = "\n".join(
        '<article class="stage"><div class="step">STEP '+no+'</div><h3>'
        +_cell(title)+'</h3><p>'+_cell(info)+'</p></article>'
        for no,title,info in steps
    )
    full_report = _cell(demo["report"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; img-src data:">
<meta name="description" content="AI Research Agent v0.1：完全虚构、离线、无模型调用的投资研究产品演示。">
<title>Research Agent | 离线产品演示 · 纯合成数据</title>
<style>{_STYLE}</style>
</head>
<body>
<header>
<div class="brandline"><div class="wordmark">Research<span>.</span>Agent <span class="pill">v0.1 Demo</span></div>
<div class="meta">独立 HTML 演示 · 无外部资产 · 不含真实用户资料</div></div>
<nav aria-label="页面导航"><a href="#overview">概览</a><a href="#pipeline">研究流程</a>
<a href="#comparison">公司对比</a><a href="#thesis">投资判断演示</a><a href="#sources">证据与限制</a></nav>
</header>
<main>
<div class="banner" role="note">🧪 全部为合成演示数据、虚构公司及预设研究文案。不是实时金融信息，没有调用大模型，不构成投资建议。</div>
<section class="hero" id="overview">
<div class="eyebrow">AI × INVESTMENT RESEARCH · PRODUCT DEMONSTRATION</div>
<h1>从结构化数据<br>到可核查的投资研究交付</h1>
<p class="lede">Research Agent 将数据采集、行业分析、公司比较和投资研判组织成四阶段流程。
此页面展示其报告形态及分析逻辑；所有结果均由固定虚构样本预设生成。</p>
<div class="meta">演示样本：{_cell(demo['industry'])} · 合成数据快照：{_cell(demo['snapshot_date'])}</div>
</section>
<div class="grid metrics" aria-label="合成研究关键指标">
<article class="card"><div class="kicker">虚构公司</div><div class="number">{len(cos)}</div><div class="sub">仅用于验证对比流程</div></article>
<article class="card"><div class="kicker">合成市值合计</div><div class="number">{demo['total_market_cap']:.0f} 亿</div><div class="sub">人民币示意单位</div></article>
<article class="card"><div class="kicker">同季度平均 ROE</div><div class="number">{demo['average_roe']:.1f}%</div><div class="sub">仅两家虚构公司</div></article>
<article class="card"><div class="kicker">营收同比可比性</div><div class="number">{"跨季度" if not demo["growth_comparable"] else "同季度"}</div><div class="sub">不混合口径计算均值</div></article>
</div>
<section class="panel" id="pipeline">
<div class="eyebrow">WORKFLOW</div><h2>四阶段研究流程</h2>
<div class="grid stage-grid">{cards}</div>
<p class="note">演示中的四阶段内容来自固定文案，而非实际运行金融数据抓取或 LLM 分析。</p>
</section>
<section class="panel" id="comparison">
<div class="eyebrow">FINANCIAL COMPARISON</div><h2>公司财务对比</h2>
<p>合成公司：{company_names}。指标均取自随项目提供的合成样本。</p>
<div class="tablewrap"><table><thead><tr>{heading}</tr></thead><tbody>{table_rows}</tbody></table></div>
<p class="note"><strong>可比性警告：</strong>{_cell(growth_caveat)}
模拟市值、PE 与财务数据均未经真实市场核验。</p>
<div class="callout"><strong>示例研究结论</strong><p>
{_cell(cos[0]['name'])} 的模拟 ROE 高于 {_cell(cos[1]['name'])}，但两家公司数据不足以
识别竞争优势、盈利驱动或行业投资价值。</p></div>
</section>
<section class="panel" id="thesis">
<div class="eyebrow">INVESTMENT THESIS / RED TEAM</div><h2>研究判断：先提出假设，再尝试证伪</h2>
<div class="split">
<div class="callout"><h3>研究假设 · 待验证</h3>
<p>假设虚构行业需求回暖，企业营收增长得以延续。合成数据只能演示分析路径，
不能据此认定趋势或提供买卖建议。</p></div>
<div class="callout risk"><h3>反方论证 · Red Team</h3>
<p>基数效应、需求不及预期与成本上行均可能使假设失效。
需要原始财报、现金流、订单和同行可比样本支持。</p></div>
</div>
<details><summary>展开预设研究正文（假设、依据与验证问题）</summary><pre>{_cell(demo["sections"]["investment_thesis"])}</pre></details>
</section>
<section class="panel" id="sources">
<div class="eyebrow">TRACEABILITY & LIMITATIONS</div><h2>证据链：明确知道什么，还不知道什么</h2>
<p><span class="check">✓</span> 逐项记录来源标签和所属季度；报告中 FIN 标记与合成快照数值对账。</p>
<p><span class="check">✓</span> 演示数据不包含真实用户资料；页面完全静态，无 JS、CDN、外部字体或 API 请求。</p>
<p><strong>不能证明：</strong>提供方真实性、模型推理能力、真实财报准确性或投资决策质量。</p>
<details><summary>查看完整 Markdown 演示报告（含财务对照表和附录）</summary>
<pre>{full_report}</pre></details>
</section>
</main>
<footer>Research Agent · v0.1 本地展示版 · 固定合成样本 · 本页面可在无网络环境下独立打开。
任何分析均不构成投资建议。</footer>
</body></html>
"""


def export_demo_html(path):
    """Write only to an explicit destination; callers decide where to save."""
    from pathlib import Path
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_demo_html(), encoding="utf-8")
    return target

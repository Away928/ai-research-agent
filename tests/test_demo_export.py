"""An entire product demo can be shared as a zero-dependency offline HTML file."""
from html.parser import HTMLParser

from tools.demo_experience import build_demo
from tools.demo_export import export_demo_html, render_demo_html


class DocumentInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = set()
        self.hrefs = []
        self.remote_assets = []

    def handle_starttag(self, tag, attributes):
        self.tags.append(tag)
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag in ("script", "iframe", "link", "img", "video", "audio"):
            self.remote_assets.append(tag)


def test_offline_export_contains_complete_showcase_with_all_sections():
    html = render_demo_html()
    parser = DocumentInspector()
    parser.feed(html)
    assert html.startswith("<!doctype html>")
    assert parser.tags.count("html") == 1
    assert parser.tags.count("table") >= 1
    assert parser.ids >= {
        "overview", "pipeline", "comparison", "thesis", "sources"
    }
    assert len([x for x in parser.tags if x == "article"]) >= 8
    assert all(url.startswith("#") for url in parser.hrefs)
    assert parser.remote_assets == []
    assert 'Content-Security-Policy' in html
    assert "无网络" not in html or "合成" in html
    assert "完整 Markdown 演示报告" in html
    assert "采集数值匹配 2 条" in html
    assert "未计算跨季度平均增速" in html
    assert '2' in html and '255' in html


def test_export_has_no_real_user_material_or_auto_generated_ai_claim():
    html = render_demo_html()
    assert "未调用大模型" in html
    assert "虚构" in html
    assert "@163.com" not in html
    assert "William Lu" not in html
    assert "sk-ant-" not in html
    assert "BEGIN PRIVATE KEY" not in html
    assert "<script" not in html.lower()
    assert "javascript:" not in html.lower()
    assert "平均收入增长（%）" not in html


def test_export_creates_shareable_file_only_where_requested(tmp_path):
    destination = tmp_path / "standalone" / "research_demo.html"
    result = export_demo_html(destination)
    assert result == destination
    assert destination.is_file()
    assert destination.stat().st_size > 10_000
    assert "离线产品演示" in result.read_text(encoding="utf-8")


def test_demo_report_matches_static_html_with_no_sensitive_profile():
    demo = build_demo()
    html = render_demo_html(demo)
    assert "Research Agent Demo" in demo["report"]
    assert "@163.com" not in demo["report"]
    assert "FIN-TST001-roe_pct" in demo["report"]
    assert "FIN-TST001-roe_pct" in html
    assert demo["growth_comparable"] is False

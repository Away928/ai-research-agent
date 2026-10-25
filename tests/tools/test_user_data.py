"""Tests for tools/user_data.py — _parse_frontmatter and summarize_supplements."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.user_data import UserDataManager


class TestParseFrontmatter:
    """UserDataManager._parse_frontmatter — extract metadata from markdown text."""

    def setup_method(self):
        self.mgr = UserDataManager()

    def test_full_frontmatter(self):
        text = """# 季度策略会纪要
2026-07-01
来源: 某券商研究部

这是正文内容，包含详细的策略讨论和分析。"""
        title, date, source, body = self.mgr._parse_frontmatter(text, "raw.md")
        assert title == "季度策略会纪要"
        assert date == "2026-07-01"
        assert source == "某券商研究部"
        assert "正文内容" in body

    def test_title_only_no_date_or_source(self):
        text = """# 只有标题
这是正文。"""
        title, date, source, body = self.mgr._parse_frontmatter(text, "doc.md")
        assert title == "只有标题"
        assert date == ""
        assert source == ""
        assert "正文" in body

    def test_date_in_markdown_h2_format(self):
        text = """# 会议记录
## 2026-06-15
来源：内部团队

正文内容。"""
        title, date, source, body = self.mgr._parse_frontmatter(text, "notes.md")
        assert title == "会议记录"
        assert date == "2026-06-15"
        assert source == "内部团队"

    def test_no_frontmatter_title_from_filename(self):
        text = "直接开始正文内容，没有任何元信息。"
        title, date, source, body = self.mgr._parse_frontmatter(text, "report_2026-03-01.md")
        assert title == "report_2026-03-01"
        assert date == "2026-03-01"  # extracted from filename
        assert source == ""
        assert "正文" in body

    def test_date_in_both_frontmatter_and_filename(self):
        """Frontmatter date wins over filename."""
        text = """# 调研笔记
2026-05-20

正文。"""
        title, date, source, body = self.mgr._parse_frontmatter(text, "notes_2026-01-01.md")
        assert date == "2026-05-20"  # frontmatter wins

    def test_source_with_chinese_colon(self):
        text = """# 访谈
2026-04-01
来源：某咨询公司

正文。"""
        title, date, source, body = self.mgr._parse_frontmatter(text, "interview.md")
        assert source == "某咨询公司"

    def test_source_with_english_colon(self):
        text = """# Interview
2026-04-01
Source: A consulting firm

Content. """
        title, date, source, body = self.mgr._parse_frontmatter(text, "interview.md")
        assert "A consulting firm" in source

    def test_cjk_title_and_content(self):
        text = """# 行业调研：AI算力产业链深度分析
2026-07-10
来源: 内部研究

算力是人工智能的基础设施，近年来随着大模型的发展，算力需求呈现爆发式增长。"""
        title, date, source, body = self.mgr._parse_frontmatter(text, "report.md")
        assert "AI算力" in title
        assert date == "2026-07-10"
        assert "算力是" in body

    def test_empty_text_body(self):
        text = "# 标题"
        title, date, source, body = self.mgr._parse_frontmatter(text, "empty.md")
        assert title == "标题"
        assert body == ""

    def test_filename_without_date_pattern(self):
        text = "正文内容"
        title, date, source, body = self.mgr._parse_frontmatter(text, "notes.md")
        assert title == "notes"
        assert date == ""  # no date in filename either


class TestSummarizeSupplements:
    """UserDataManager.summarize_supplements — static method."""

    def test_none_input(self):
        result = UserDataManager.summarize_supplements(None)
        assert result["总计"] == 0
        assert "无用户补充数据" in result["说明"]

    def test_empty_list(self):
        result = UserDataManager.summarize_supplements([])
        assert result["总计"] == 0

    def test_list_format(self):
        data = [
            {"类别": "会议纪要", "标题": "策略会", "日期": "2026-07-01",
             "来源": "某券商", "内容": "纪要正文" * 100},
            {"类别": "专家访谈", "标题": "行业专家", "日期": "2026-06-15",
             "来源": "某咨询", "内容": "访谈内容" * 50},
        ]
        result = UserDataManager.summarize_supplements(data)
        assert result["总计"] == 2
        assert len(result["明细"]["会议纪要"]) == 1
        assert len(result["明细"]["专家访谈"]) == 1

    def test_dict_format(self):
        data = {
            "会议纪要": [
                {"标题": "纪要1", "日期": "", "来源": "", "内容": "text"},
            ],
            "专家访谈": [],
        }
        result = UserDataManager.summarize_supplements(data)
        assert result["总计"] == 1

    def test_content_truncation(self):
        """Content > 1500 chars should be truncated."""
        long_content = "长内容" * 1000  # ~3000 chars
        data = [{"类别": "调研笔记", "标题": "测试", "日期": "",
                  "来源": "", "内容": long_content}]
        result = UserDataManager.summarize_supplements(data)
        summary = result["明细"]["调研笔记"][0]["摘要"]
        assert len(summary) <= 1500

    def test_short_content_preserved(self):
        short = "短内容"
        data = [{"类别": "其他", "标题": "测试", "日期": "",
                  "来源": "", "内容": short}]
        result = UserDataManager.summarize_supplements(data)
        summary = result["明细"]["其他"][0]["摘要"]
        assert summary == short

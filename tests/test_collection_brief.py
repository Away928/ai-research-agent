"""A no-model research attempt still produces a bounded, honest deliverable."""

from copy import deepcopy
import json
from pathlib import Path

from tools.collection_brief import format_collection_brief


FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_research_package.json"


def sample():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_synthetic_snapshot_has_full_receipt_and_source_quarters():
    report = format_collection_brief("虚构测试能源", sample())
    assert report.startswith("# 虚构测试能源｜数据采集简报（非 AI 投资报告）")
    assert "未调用 AI 分析" in report
    for name in ("行情", "财务", "公告", "新闻"):
        assert name in report
    assert "合成甲公司" in report
    assert "合成乙公司" in report
    assert "2025Q2" in report and "2025Q3" in report
    assert "SYNTHETIC_TEST_FINANCIAL" in report
    assert "## 5. 重要边界" in report


def test_does_not_copy_user_uploads_or_secrets():
    package = sample()
    package["user_supplements"] = [{
        "标题": "PRIVATE_FILENAME_DO_NOT_EXPORT",
        "内容": "PRIVATE_UPLOAD_BYTES_DO_NOT_EXPORT",
        "来源": "private://file",
    }]
    package["api_key"] = "secret-private-key"
    package["prompt"] = "PRIVATE_INTERNAL_LLM_PROMPT"
    result = format_collection_brief("虚构行业", package)
    assert "PRIVATE_FILENAME_DO_NOT_EXPORT" not in result
    assert "PRIVATE_UPLOAD_BYTES_DO_NOT_EXPORT" not in result
    assert "secret-private-key" not in result
    assert "PRIVATE_INTERNAL_LLM_PROMPT" not in result
    assert "正文和文件名不会自动写入本简报" in result


def test_missing_data_does_not_invent_success_or_zeros():
    result = format_collection_brief("空数据行业", {
        "数据源状态": {"market_data": "⚠️ 无有效数据"},
        "market_data": {"行情": {}, "成分股": []},
        "financial_data": {"公司财务": []},
        "announcement_data": {"公告": []},
        "news_data": {"新闻": []},
    })
    assert "⚠️ 无有效数据" in result
    assert "未获取到可供列示的成分股" in result
    assert "未获取到可列示的财务记录" in result
    assert "未获取到条目" in result
    assert "未提供" in result
    assert "完成四阶段" not in result


def test_provider_text_is_bounded_and_cannot_break_markdown_columns():
    package = sample()
    package["market_data"]["source"] = "fake | source\nnew row"
    package["news_data"]["新闻"][0]["title"] = "ATTACK|" + ("x" * 900) + "\ninjected"
    result = format_collection_brief("测试 | 行业\n一", package)
    assert "fake ｜ source new row" in result
    assert "ATTACK｜" in result
    assert "injected" not in result
    assert len(result) < 18_000


def test_multiple_renders_do_not_mutate_input():
    package = sample()
    before = deepcopy(package)
    assert format_collection_brief("合成行业", package)
    assert package == before

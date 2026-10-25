"""Local-record agreement tests; not external fact verification."""

from tools.claim_audit import audit_financial_markers
from tools.report_formatter import ReportFormatter


SNAPSHOT = {"financial_data": {"公司财务": [
    {"code": "000001", "name": "虚构甲公司", "roe_pct": 8.0,
     "revenue_growth_pct": 12.5, "debt_ratio_pct": None,
     "_metric_periods": {"roe_pct": "2026Q1", "revenue_growth_pct": "2025Q4"},
     "_source": "合成测试数据"},
]}}


def test_exact_marker_agrees_with_record_not_truth():
    result = audit_financial_markers(
        "ROE为8.0%。 [[FIN-000001-roe_pct=8.0]]", SNAPSHOT
    )
    assert len(result) == 1
    assert result[0]["status"] == "record_value_match"
    assert result[0]["source_period"] == "2026Q1"


def test_wrong_numeric_value_detected():
    result = audit_financial_markers(
        "[[FIN-000001-roe_pct=8.5]]", SNAPSHOT
    )
    assert result[0]["status"] == "value_mismatch"
    assert result[0]["source_value"] == 8.0


def test_unknown_or_malformed_and_missing_value_are_not_passes():
    body = (
        "[[FIN-999999-roe_pct=8]] "
        "[[FIN-000001-debt_ratio_pct=10]] "
        "[[FIN-000001-roe_pct=not-a-number]]"
    )
    results = audit_financial_markers(body, SNAPSHOT)
    assert [r["status"] for r in results] == [
        "unknown_record", "missing_value", "malformed"
    ]


def test_duplicate_codes_are_ambiguous():
    dup = {"financial_data": {"公司财务": [
        {"code": "000001", "roe_pct": 8}, {"code": "000001", "roe_pct": 8}
    ]}}
    result = audit_financial_markers(
        "[[FIN-000001-roe_pct=8]]", dup
    )
    assert result[0]["status"] == "ambiguous_record"


def test_no_marker_is_not_a_success_claim():
    report = ReportFormatter().format_report(
        "ROE为8%，未经证实。", "合成行业",
        [{"stage": "offline", "duration_seconds": 0.1, "notes": "offline"}],
        {"raw_data": SNAPSHOT},
    )
    assert "未发现可机读的财务引用标记；不能视为检查通过" in report
    assert "### F. 作者" in report


def test_generated_report_audits_only_original_body_not_appendix():
    report = ReportFormatter().format_report(
        "收益指标 [[FIN-000001-roe_pct=8.5]]", "合成行业",
        [{"stage": "offline", "duration_seconds": 0.1, "notes": "offline"}],
        {"raw_data": SNAPSHOT},
    )
    assert "可机读标记共 1 条；采集数值匹配 0 条，需复核 1 条" in report
    assert "value_mismatch" in report
    assert "FIN-000001-roe_pct" in report


def test_source_table_not_hardcoded_to_specific_industry():
    report = ReportFormatter().format_report(
        "测试", "虚构能源行业",
        [{"stage": "offline", "duration_seconds": 0.1, "notes": "offline"}],
        {"raw_data": {
            "market_data": {"source": "合成来源", "fetch_timestamp": "2026-10-24 14:00:00"},
            "financial_data": {"source": "缓存"},
        }},
    )
    assert "| 行情 | 合成来源 | 2026-10-24 14:00:00 | 未核验 |" in report
    assert "| 财务 | 缓存 | 未提供 | 未核验 |" in report
    assert "| 公告 | 无可用数据 | 未提供 | 未核验 |" in report
    assert "国证算力" not in report

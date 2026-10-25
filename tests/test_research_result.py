"""Real-research delivery classification, separate from the synthetic demo."""

from types import SimpleNamespace

from ui.research_result import build_run_result


def example_agent(ai_mode=True, report="") -> SimpleNamespace:
    return SimpleNamespace(
        industry="合成测试行业",
        session_id="local-test-session",
        ai_mode=ai_mode,
        context={
            "formatted_report": report,
            "raw_data": {
                "数据源状态": {
                    "market_data": "✅ 成功",
                    "financial_data": "⚠️ 无有效数据",
                },
            },
        },
        work_log=[
            {"stage": "data_collection"},
            {"stage": "investment_thesis"},
        ],
    )


def test_success_requires_real_ai_and_nonempty_formatted_report():
    result = build_run_result(example_agent(True, "# 完整研究报告" * 20), {})
    assert result["status"] == "report"
    assert result["formatted_report"].startswith("# 完整研究报告")
    assert result["source_status"]["market_data"] == "✅ 成功"
    assert result["completed_stages"] == ["data_collection", "investment_thesis"]


def test_no_model_never_passes_as_report_even_if_it_contains_old_text():
    result = build_run_result(example_agent(False, "# 旧内容"), {})
    assert result["status"] == "data_only"
    assert result["formatted_report"] == ""
    assert "数据采集简报" in result["collection_brief"]


def test_missing_report_is_data_only_and_cannot_claim_success():
    result = build_run_result(example_agent(True, ""), {})
    assert result["status"] == "data_only"
    assert result["formatted_report"] == ""


def test_failed_stage_takes_priority_over_report():
    result = build_run_result(
        example_agent(True, "# 之前遗留的报告"),
        {"company_deep_dive": "backend error with secret-sk-test"},
    )
    assert result["status"] == "failed"
    assert result["formatted_report"] == ""
    assert result["collection_brief"] == ""
    assert result["errors"] == ["company_deep_dive"]
    assert "secret-sk-test" not in str(result)
    assert "api_key" not in result
    assert "uploads" not in result
    assert "raw_data" not in result

"""Synthetic end-to-end regression: zero API calls and no user files.

Checks actual stage orchestration, prompt inputs, report output, source labels,
financial periods and explicit financial marker mismatches using fictional data.
"""

import copy
import json

import pytest
from pathlib import Path

import agent_workflow
from tools.data_sources.provenance import inspect_provenance

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_research_package.json"


def test_synthetic_four_stage_workflow_reports_a_mismatched_claim(monkeypatch, tmp_path):
    package = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert package["行业"] == "虚构测试能源"
    assert all(company["code"].startswith("TST") for company in
               package["financial_data"]["公司财务"])

    class OfflineLLM:
        prompts = []
        model_backend = "anthropic"
        model = "offline-canned"
        is_available = True

        def __init__(self, **kwargs):
            pass

        def ask_with_log(self, prompt, *, system="", label="", max_tokens=1000):
            self.prompts.append((label, prompt))
            if label == "行业全景":
                return (
                    "虚构能源产业链：上游芯片，中游发电，下游测试终端。"
                    "来源为 SYNTHETIC_TEST_FINANCIAL，以下均是推断且不确定，待验证。"
                    "ROE为8.0%，增长12.0%，毛利35.0%，杠杆40.0%，"
                    "行业资金55.0%，运营28.0%。无真实投资含义。"
                )
            if label == "公司深度":
                return (
                    "| 公司 | ROE | 增速 | 风险 |\n"
                    "|---|---|---|---|\n"
                    "| 合成甲 | 8.0% | 12.0% | 待核实 |\n"
                    "| 合成乙 | 5.0% | 7.0% | 待核实 |\n"
                    "数据推断、经营推断、风险推断，预警需复核。"
                    "毛利35.0%，净利9.0%，负债40.0%，"
                    "估值15.0%，同比13.0%，变化10.0%。"
                )
            if label == "投资研判":
                return (
                    "虚构能源处于复苏阶段，以下为合成数据，不构成建议。"
                    "反方观点：周期可能下行，需要证伪。\n"
                    "| 风险 | 采集值 |\n"
                    "|---|---|\n"
                    "| 杠杆 | 40.0% |\n"
                    "| 增长 | 12.0% |\n"
                    "合成甲 ROE 8.0% [[FIN-TST001-roe_pct=8.0]]；"
                    "合成甲营收增速声称13.0% [[FIN-TST001-revenue_growth_pct=13.0]]。"
                    "其他测试数字：5.0%、7.0%、9.0%、35.0%、40.0%、"
                    "45.0%、12.5%、15.0%、20.0%、25.0%。"
                    "这些数值与结论未经事实认证。"
                )
            raise AssertionError("Unexpected model call: " + label)

    def synthetic_gather(self, industry):
        assert industry == package["行业"]
        result = copy.deepcopy(package)
        result["来源核查"] = inspect_provenance(result)
        return result

    def network_forbidden(*args, **kwargs):
        raise AssertionError("Network access is forbidden during offline regression")

    monkeypatch.setattr(agent_workflow, "LLMClient", OfflineLLM)
    monkeypatch.setattr(agent_workflow.DataSourceManager, "gather", synthetic_gather)
    monkeypatch.setattr(agent_workflow.DataSourceManager, "print_summary",
                        staticmethod(lambda package: None))
    monkeypatch.setattr(agent_workflow, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(agent_workflow, "_HISTORY_FILE", tmp_path / "history.json")
    # A hard stop for accidental HTTP through the common transport.
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", network_forbidden)

    agent = agent_workflow.AIResearchAgentV2(industry="虚构测试能源")
    outcome = agent.run()
    report = agent.context["formatted_report"]
    assert outcome["ai_mode"]
    assert outcome["status"] == "completed"
    assert outcome["stage_errors"] == {}
    assert outcome["skipped_stages"] == []
    assert len(agent.work_log) == 4
    assert len([x for x in agent.llm.prompts if x[0] in
                ("行业全景", "公司深度", "投资研判")]) == 3
    assert "**研究阶段：** 4 个阶段" in report
    assert "| 4 | investment_thesis |" in report
    assert "可机读标记共 2 条；采集数值匹配 1 条，需复核 1 条" in report
    assert "value_mismatch" in report
    assert "2025Q3" in report and "2025Q2" in report
    assert "SYNTHETIC_TEST_FINANCIAL" in report
    assert "虚构能源指数" in agent.llm.prompts[0][1]
    assert "财务指标报告期" in agent.llm.prompts[1][1]
    assert "公司财务记录（待核验）" in agent.llm.prompts[2][1]
    assert len(list(tmp_path.glob("*_行业扫描报告_*.md"))) == 1
    assert len(list(tmp_path.glob("work_log_*.json"))) == 1
    assert (tmp_path / "history.json").exists()


def test_workflow_stage_error_is_not_labeled_success(monkeypatch, tmp_path):
    monkeypatch.setattr(agent_workflow, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(agent_workflow, "_HISTORY_FILE", tmp_path / "history.json")
    agent = agent_workflow.AIResearchAgentV2(
        industry="合成出错案例", model_backend="openai_compat", api_key=""
    )

    def failing_source():
        raise RuntimeError("合成采集失败")

    agent.stage_context_gathering = failing_source

    def should_not_run():
        raise AssertionError("A later stage ran after a failed dependency")

    agent.stage_industry_overview = should_not_run
    agent.stage_company_deep_dive = should_not_run
    agent.stage_investment_thesis = should_not_run

    result = agent.run()
    assert result["status"] == "partial_failure"
    assert result["stage_errors"] == {"data_collection": "合成采集失败"}
    assert result["skipped_stages"] == [
        "industry_overview", "company_deep_dive", "investment_thesis"
    ]
    assert not list(tmp_path.glob("*_行业扫描报告_*.md"))
    assert (tmp_path / "history.json").exists()
    history = json.loads((tmp_path / "history.json").read_text(encoding="utf-8"))
    assert history[-1]["report_file"] == ""


def test_industry_stage_failure_prevents_company_and_report(monkeypatch, tmp_path):
    monkeypatch.setattr(agent_workflow, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(agent_workflow, "_HISTORY_FILE", tmp_path / "history.json")
    agent = agent_workflow.AIResearchAgentV2(
        industry="合成失败案例", model_backend="openai_compat", api_key=""
    )
    stages_called = []
    def collection():
        stages_called.append("data_collection")
        agent.context["raw_data"] = {"数据源状态": {}}
        return ""
    def overview():
        stages_called.append("industry_overview")
        raise RuntimeError("离线模拟分析异常")
    def should_not_run():
        raise AssertionError("Dependent stage should not run")
    agent.stage_context_gathering = collection
    agent.stage_industry_overview = overview
    agent.stage_company_deep_dive = should_not_run
    agent.stage_investment_thesis = should_not_run

    result = agent.run()
    assert stages_called == ["data_collection", "industry_overview"]
    assert result["status"] == "partial_failure"
    assert result["skipped_stages"] == ["company_deep_dive", "investment_thesis"]
    assert "investment_thesis" not in agent.context
    assert not list(tmp_path.glob("*_行业扫描报告_*.md"))
    assert (tmp_path / "history.json").is_file()


def test_cli_returns_error_code_if_workflow_failed(monkeypatch):
    import cli
    import sys

    class OfflineBrokenAgent:
        def __init__(self, **kwargs):
            assert kwargs["industry"] == "合成失败"
        def run(self):
            return {"status": "partial_failure", "stages": []}

    monkeypatch.setattr(cli, "AIResearchAgentV2", OfflineBrokenAgent)
    monkeypatch.setattr(sys, "argv", ["cli.py", "--industry", "合成失败"])
    assert cli.main() == 1


def test_cli_returns_success_code_if_workflow_succeeded(monkeypatch):
    import cli
    import sys

    class OfflineCompleteAgent:
        def __init__(self, **kwargs):
            assert kwargs["industry"] == "合成成功"
        def run(self):
            return {"status": "completed", "stages": []}

    monkeypatch.setattr(cli, "AIResearchAgentV2", OfflineCompleteAgent)
    monkeypatch.setattr(sys, "argv", ["cli.py", "--industry", "合成成功"])
    assert cli.main() == 0


@pytest.mark.parametrize("stage_method", [
    "stage_industry_overview", "stage_company_deep_dive",
    "stage_investment_thesis",
])
def test_ai_mode_empty_output_refuses_to_generate_complete_report(
        monkeypatch, tmp_path, stage_method):
    agent = agent_workflow.AIResearchAgentV2(
        industry="虚构行业", model_backend="openai_compat", api_key=""
    )
    # Fake the AI mode while making every LLM invocation deterministic/offline.
    agent.ai_mode = True
    agent.context = {
        "raw_data": {"数据源状态": {}},
        "market_data": {"成分股": [], "行情": {}},
        "financial_data": {"公司财务": []},
        "announcement_data": {"公告": []},
        "news_data": {"新闻": []},
        "user_supplements": [],
        "industry_overview": "",
        "company_deep_dive": "",
    }
    monkeypatch.setattr(agent_workflow, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(agent_workflow, "call_ai_or_fallback",
                        lambda *args, **kwargs: "")
    with pytest.raises(RuntimeError, match="未返回有效正文"):
        getattr(agent, stage_method)()
    assert "formatted_report" not in agent.context
    assert not list(tmp_path.glob("*_行业扫描报告_*.md"))



def test_no_observations_blocks_entire_research_and_writes_failure_log(
        monkeypatch, tmp_path):
    monkeypatch.setattr(agent_workflow, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(agent_workflow, "_HISTORY_FILE", tmp_path / "history.json")
    agent = agent_workflow.AIResearchAgentV2(
        industry="虚构无数据行业", model_backend="openai_compat", api_key=""
    )
    empty = {
        "行业": "虚构无数据行业",
        "数据源状态": {key: "⚠️ 无有效数据" for key in (
            "market_data", "financial_data", "announcement_data", "news_data"
        )},
        "market_data": {"行情": {}, "成分股": [], "source": "无可用数据"},
        "financial_data": {"公司财务": [], "source": "无数据"},
        "announcement_data": {"公告": [], "研报": [], "source": "无可用数据"},
        "news_data": {"新闻": [], "source": "无可用数据"},
    }
    monkeypatch.setattr(agent.data_manager, "gather", lambda _: copy.deepcopy(empty))
    monkeypatch.setattr(agent.data_manager, "print_summary", lambda _: None)
    agent.stage_industry_overview = lambda: pytest.fail("Should have stopped before LLM")
    agent.stage_company_deep_dive = lambda: pytest.fail("Should have stopped")
    agent.stage_investment_thesis = lambda: pytest.fail("Should have stopped")
    result = agent.run()
    assert result["status"] == "partial_failure"
    assert "均无有效观测" in result["stage_errors"]["data_collection"]
    assert result["skipped_stages"] == [
        "industry_overview", "company_deep_dive", "investment_thesis"
    ]
    assert not list(tmp_path.glob("*_行业扫描报告_*.md"))
    assert (tmp_path / "history.json").exists()


def test_available_news_without_financials_is_not_blocked(
        monkeypatch, tmp_path):
    agent = agent_workflow.AIResearchAgentV2(
        industry="虚构新闻行业", model_backend="openai_compat", api_key=""
    )
    packet = {
        "数据源状态": {},
        "market_data": {"成分股": [], "行情": {}},
        "financial_data": {"公司财务": []},
        "announcement_data": {"公告": []},
        "news_data": {"新闻": [{"title": "合成测试新闻"}]},
    }
    monkeypatch.setattr(agent.data_manager, "gather", lambda _: copy.deepcopy(packet))
    monkeypatch.setattr(agent.data_manager, "print_summary", lambda _: None)
    assert agent.stage_context_gathering() == ""
    assert len(agent.work_log) == 1



def test_history_index_failure_does_not_erase_completed_workflow_log(
        monkeypatch, tmp_path):
    monkeypatch.setattr(agent_workflow, "OUTPUT_DIR", tmp_path)

    def fail_history(*args):
        raise OSError("test-only history not writable")

    monkeypatch.setattr(agent_workflow, "_append_history", fail_history)
    agent = agent_workflow.AIResearchAgentV2(
        industry="合成历史写入失败",
        model_backend="openai_compat", api_key=""
    )
    calls = []
    for attr, label in (
        ("stage_context_gathering", "collection"),
        ("stage_industry_overview", "overview"),
        ("stage_company_deep_dive", "deep_dive"),
        ("stage_investment_thesis", "thesis"),
    ):
        setattr(agent, attr, lambda label=label: calls.append(label))
    result = agent.run()
    assert result["status"] == "completed"
    assert result["stage_errors"] == {}
    assert calls == ["collection", "overview", "deep_dive", "thesis"]
    assert list(tmp_path.glob("work_log_*.json"))

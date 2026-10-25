"""Verify real-mode states without contacting any model or external provider.

Use Streamlit's script runner with a synthetic stand-in for the research agent:
    python scripts/verify_real_entry.py

This tests the real-mode UI, not the fidelity of live APIs or model outputs.
"""
from unittest.mock import patch
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest

import agent_workflow


class FakeOfflineAgent:
    calls = []
    fail_collection = False

    def __init__(self, industry, api_key="", **kwargs):
        self.industry = industry
        self.session_id = "synthetic-ui-check"
        self.ai_mode = bool(api_key)
        self.context = {}
        self.work_log = []
        self.calls.append("initialized")

    def stage_context_gathering(self):
        self.calls.append("collection")
        if self.fail_collection:
            raise RuntimeError("synthetic collection failure")
        data = {
            "行业": self.industry,
            "采集时间": "2026-01-01 10:00:00",
            "数据源状态": {
                "market_data": "✅ 测试记录",
                "financial_data": "⚠️ 无有效数据",
                "announcement_data": "⚠️ 无有效数据",
                "news_data": "⚠️ 无有效数据",
            },
            "market_data": {
                "行情": {"index_name": "模拟指数", "index_price": 100.0,
                          "index_change_pct": 0.0, "_source": "SYNTHETIC"},
                "成分股": [],
            },
            "financial_data": {"公司财务": []},
            "announcement_data": {"公告": [], "研报": []},
            "news_data": {"新闻": []},
            "user_supplements": [],
        }
        self.context.update({"raw_data": data, **{
            key: data[key] for key in (
                "market_data", "financial_data", "announcement_data", "news_data"
            )
        }})
        self.work_log.append({"stage": "data_collection", "duration_seconds": 0.0})
        return ""

    def stage_industry_overview(self):
        self.calls.append("overview")
        self.work_log.append({"stage": "industry_overview", "duration_seconds": 0.0})
        return "合成行业分析" * 25

    def stage_company_deep_dive(self):
        self.calls.append("company")
        self.work_log.append({"stage": "company_deep_dive", "duration_seconds": 0.0})
        return "合成公司分析" * 25

    def stage_investment_thesis(self):
        self.calls.append("thesis")
        self.context["final_report"] = "合成投资研判" * 25
        self.context["formatted_report"] = (
            "# 真实研究界面测试报告\n\n"
            "仅用于验证网页状态与下载功能。没有使用外部金融数据或模型。"
        )
        self.work_log.append({"stage": "investment_thesis", "duration_seconds": 0.0})
        return self.context["final_report"]


def main():
    import requests
    def network_forbidden(*args, **kwargs):
        raise AssertionError("A real network request occurred during a UI smoke test")

    with patch.object(agent_workflow, "AIResearchAgentV2", FakeOfflineAgent),          patch.object(agent_workflow, "_append_history", lambda *args: None),          patch.object(requests.sessions.Session, "request", network_forbidden):
        test = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        assert not test.exception, [e.message for e in test.exception]
        test.radio[0].set_value("🔬 真实研究（使用数据源）").run()
        assert not test.exception, [e.message for e in test.exception]
        start = next(b for b in test.button if b.label == "🔍 开始研究")
        assert start.disabled
        choices = test.selectbox(key="input_select").options
        industry = next(x for x in choices if x != "—— 选择行业 ——")
        test.selectbox(key="input_select").set_value(industry).run()
        assert not test.exception, [e.message for e in test.exception]

        FakeOfflineAgent.calls = []
        next(b for b in test.button if b.label == "🔍 开始研究").click().run()
        assert not test.exception, [e.message for e in test.exception]
        assert FakeOfflineAgent.calls == ["initialized", "collection"]
        assert test.session_state["real_last_result"]["status"] == "data_only"
        assert not test.session_state["real_last_result"]["formatted_report"]
        assert "数据采集简报" in test.session_state["real_last_result"]["collection_brief"]
        assert any("数据采集简报" in str(m.value) for m in test.markdown)
        test.run()
        assert test.session_state["real_last_result"]["status"] == "data_only"
        assert any("数据采集简报" in str(m.value) for m in test.markdown)
        print("PASS: no-key collection provides a persistent data receipt")

        # With a stand-in key, the fake agent performs four mocked local steps.
        FakeOfflineAgent.calls = []
        test.text_input(key="sidebar_apikey_openai_compat").set_value("synthetic-only-not-a-secret").run()
        next(b for b in test.button if b.label == "🔍 开始研究").click().run()
        assert not test.exception, [e.message for e in test.exception]
        assert FakeOfflineAgent.calls == [
            "initialized", "collection", "overview", "company", "thesis"
        ]
        assert test.session_state["real_last_result"]["status"] == "report"
        assert test.session_state["real_last_result"]["formatted_report"].startswith("#")
        test.run()
        assert not test.exception, [e.message for e in test.exception]
        assert test.session_state["real_last_result"]["status"] == "report"
        assert any("最近一次真实研究结果" in m.value for m in test.markdown)
        print("PASS: model-configured branch presents and retains full mocked report")
        FakeOfflineAgent.fail_collection = True
        try:
            next(b for b in test.button if b.label == "🔍 开始研究").click().run()
            assert not test.exception, [e.message for e in test.exception]
            assert test.session_state["real_last_result"]["status"] == "failed"
            assert test.session_state["real_last_result"]["formatted_report"] == ""
            test.run()
            assert test.session_state["real_last_result"]["status"] == "failed"
            assert len(test.error) >= 1
            print("PASS: failure replaces prior report and remains visible after rerun")
            # Switching model providers must not resend a key entered for the
            # previous provider (e.g. OpenAI-compatible -> Anthropic).
            test.selectbox(key="sidebar_backend").set_value("anthropic").run()
            assert not test.exception, [e.message for e in test.exception]
            assert test.text_input(key="sidebar_apikey_anthropic").value == ""
            print("PASS: API key input isolated by model provider")
            # Visual components are optional. Their exceptions must not erase
            # successful data-only collection and the downloadable brief.
            FakeOfflineAgent.fail_collection = False
            from ui import data_cards, charts

            def broken_renderer(_context):
                raise RuntimeError("synthetic chart/render failure")

            with patch.object(data_cards, "render_data_cards", broken_renderer), \
                 patch.object(charts, "render_market_charts", broken_renderer):
                next(b for b in test.button if b.label == "🔍 开始研究").click().run()
                assert not test.exception, [e.message for e in test.exception]
                assert test.session_state["real_last_result"]["status"] == "data_only"
                assert len(test.warning) >= 2
                assert "数据采集简报" in test.session_state["real_last_result"]["collection_brief"]
                print("PASS: card/chart failures do not destroy collection deliverable")
            with patch.object(agent_workflow, "_append_history",
                              side_effect=OSError("synthetic unavailable history file")):
                next(b for b in test.button if b.label == "🔍 开始研究").click().run()
                assert not test.exception, [e.message for e in test.exception]
                assert test.session_state["real_last_result"]["status"] == "data_only"
                assert "数据采集简报" in test.session_state["real_last_result"]["collection_brief"]
                assert len(test.warning) >= 1
                print("PASS: local history write failure does not erase deliverable")
        finally:
            FakeOfflineAgent.fail_collection = False


if __name__ == "__main__":
    main()

"""Offline Streamlit walkthrough acceptance test.

Run with Streamlit installed. All stages use synthetic local fixtures; no
financial APIs, network, or LLM may execute.
"""

from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def _markdown(page) -> str:
    return "\n".join(str(x.value) for x in page.markdown)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with patch.dict("os.environ", {
        "AGENT_LIVE_RESEARCH_ENABLED": "0",
        "AGENT_LIVE_ACCESS_SHA256": "not-enabled",
        "OPENAI_API_KEY": "synthetic-placeholder-not-real",
    }):
        page = AppTest.from_file(str(root / "app.py"), default_timeout=25).run()

    assert not page.exception, [exc.message for exc in page.exception]
    assert len(page.radio) == 0, "Anonymous visitors should not see a one-option mode selector."
    assert any(x.key == "demo_launch" for x in page.button)
    assert not any("完整报告" in str(x.value) for x in page.markdown)
    assert not any(x.label == "🔍 开始研究" for x in page.button)
    assert not any(x.key and str(x.key).startswith("sidebar_apikey")
                   for x in page.text_input)
    print("PASS: public initial state shows the 5-step walkthrough only, no private entry")

    page.button(key="demo_launch").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.session_state["demo_step"] == 1
    assert {m.label for m in page.metric} == {
        "虚构公司", "模拟总市值（亿元）", "快照性质",
    }
    assert "合成数据" in _markdown(page)
    assert "#### 数据来源与范围" in _markdown(page)
    assert "Red Team" not in _markdown(page)
    print("PASS: stage 1 data provenance only")

    page.button(key="demo_next").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.session_state["demo_step"] == 2
    assert "市场结构" in _markdown(page)
    assert "产业链" in _markdown(page)
    assert len(page.metric) == 0
    print("PASS: stage 2 industry overview only")

    page.button(key="demo_next").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.session_state["demo_step"] == 3
    assert {m.label for m in page.metric} == {
        "合成样本平均 ROE（%）", "收入增速报告期",
    }
    assert any("公司对比" in str(x.value) for x in page.markdown)
    assert "跨季度" in _markdown(page) or any(
        "报告季度" in str(x.message) for x in page.warning)
    print("PASS: stage 3 company comparison, comparable-period warning")

    page.button(key="demo_prev").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.session_state["demo_step"] == 2
    page.button(key="demo_next").click().run()
    page.button(key="demo_next").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.session_state["demo_step"] == 4
    assert "Red Team" in _markdown(page)
    assert not any("完整研究报告" == x.label for x in page.button)
    print("PASS: stage 4 investment thesis and Red Team; previous step works")

    page.button(key="demo_next").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.session_state["demo_step"] == 5
    assert any("获取本次演示交付物" in str(x.value) for x in page.markdown)
    assert any("离线产品演示报告" in str(x.value) for x in page.markdown)
    assert any("虚构" in str(x.value) for x in page.markdown)
    print("PASS: stage 5 deliverables and complete report, not mixed into earlier steps")

    page.button(key="demo_restart").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.session_state["demo_step"] == 0
    assert any(x.key == "demo_launch" for x in page.button)
    print("PASS: restart resets to introduction without running live research")


if __name__ == "__main__":
    main()

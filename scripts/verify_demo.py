"""Smoke-check the showcase and the original research entry with Streamlit AppTest.

Run in an environment with streamlit installed:
    python scripts/verify_demo.py

Does not launch a live research run, network data calls, or an LLM.
"""
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    # The public demo must remain safe even when a provider key is configured.
    with patch.dict("os.environ", {"AGENT_LIVE_RESEARCH_ENABLED": "0",
                                    "AGENT_LIVE_ACCESS_SHA256": "not-enabled",
                                    "OPENAI_API_KEY": "synthetic-do-not-send-to-network"}):
        page = AppTest.from_file(str(root / "app.py"), default_timeout=25).run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert page.radio[0].value == "🧪 体验演示（无需配置）"
    assert any(button.key == "demo_launch" for button in page.button)
    page.button(key="demo_launch").click().run()
    assert not page.exception, [exc.message for exc in page.exception]
    assert any("离线产品演示报告" in str(item.value) for item in page.markdown)
    assert any("虚构" in str(item.value) for item in page.markdown)
    assert {m.label for m in page.metric} == {
        "合成公司", "模拟总市值（亿元）",
        "平均 ROE（%）", "收入增速报告期",
    }
    print("PASS: default Demo, launch, summary metrics, complete report")
    # A public/anonymous visitor must see no provider/API upload controls.
    assert page.radio[0].options == ["🧪 体验演示（无需配置）"]
    assert not any(button.label == "🔍 开始研究" for button in page.button)
    assert not any(item.key and str(item.key).startswith("sidebar_apikey")
                   for item in page.text_input)
    print("PASS: unauthenticated public UI is synthetic-only; no live controls")


if __name__ == "__main__":
    main()

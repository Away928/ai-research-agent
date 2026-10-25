"""Smoke-check the showcase and the original research entry with Streamlit AppTest.

Run in an environment with streamlit installed:
    python scripts/verify_demo.py

Does not launch a live research run, network data calls, or an LLM.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
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
    page.radio[0].set_value("🔬 真实研究（使用数据源）").run()
    assert not page.exception, [exc.message for exc in page.exception]
    start = next(button for button in page.button
                 if button.label == "🔍 开始研究")
    assert start.disabled, "The launch button must stay disabled until industry selection."
    # Must not silently turn real research on without an industry.
    assert not page.exception
    print("PASS: real research mode accessible; start guarded by industry selection")


if __name__ == "__main__":
    main()

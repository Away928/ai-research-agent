"""Export a fully offline, fictional showcase HTML file.

    python scripts/export_demo.py
    python scripts/export_demo.py --output /tmp/research-agent-demo.html
"""
import argparse
import sys
from pathlib import Path

# Allow direct execution without requiring package installation/editable mode.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.demo_export import export_demo_html  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="生成只含合成数据、无需网络的 Research Agent 展示 HTML"
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "demo_output" / "Research_Agent_离线产品演示.html",
        help="HTML 输出路径（默认 demo_output 下）",
    )
    args = parser.parse_args(argv)
    target = export_demo_html(args.output)
    print(f"已生成离线演示页面：{target}")
    print("纯合成数据，不含真实市场信息；可在浏览器中独立打开。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

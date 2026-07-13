"""
CLI 入口 — AI Research Agent
=============================

使用方法:
    python cli.py --industry "AI算力"
    python cli.py --industry "新能源" --api-key "sk-ant-xxx"
"""

import argparse
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from agent_workflow import AIResearchAgentV2


def main():
    parser = argparse.ArgumentParser(
        description="AI Research Agent v2 — 行业投研自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  # 降级模式（无 API key）
  python cli.py --industry "AI算力"

  # Anthropic 后端
  python cli.py --industry "新能源" --api-key "sk-ant-xxx"

  # DeepSeek 后端
  export OPENAI_API_KEY="sk-xxx"
  export OPENAI_BASE_URL="https://api.deepseek.com/v1"
  python cli.py --industry "AI算力"

  # 通义千问后端
  export OPENAI_API_KEY="sk-xxx"
  export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
  export OPENAI_MODEL="qwen-plus"
  python cli.py --industry "消费电子"

  # 上传补充数据
  python cli.py --industry "AI算力" --uploads "纪要1.md" "访谈1.txt"
        """,
    )
    parser.add_argument("--industry", "-i", required=True, help="目标行业名称")
    parser.add_argument("--api-key", default="", help="LLM API Key")
    parser.add_argument("--model-backend", default="",
                        help="模型后端: anthropic 或 openai_compat")
    parser.add_argument("--model", default="", help="模型名称")
    parser.add_argument("--uploads", nargs="*", default=[],
                        help="上传补充数据文件（.md/.txt/.pdf/.docx）")

    args = parser.parse_args()

    upload_files = []
    for path_str in args.uploads:
        p = Path(path_str)
        if p.exists():
            upload_files.append(str(p))
        else:
            print(f"警告: 文件不存在，已跳过: {path_str}")

    agent = AIResearchAgentV2(
        industry=args.industry,
        api_key=args.api_key,
        model=args.model,
        model_backend=args.model_backend,
        uploads=upload_files,
    )

    result = agent.run()

    print("\n阶段耗时详情:")
    print(f"{'阶段':<25s} {'耗时':>8s} {'AI生成':>6s}")
    print("-" * 42)
    for s in result["stages"]:
        ai_label = "是" if s.get("ai_generated") else "—"
        print(f"{s['stage']:<25s} {s['duration_seconds']:>6.1f}s {ai_label:>6s}")


if __name__ == "__main__":
    main()

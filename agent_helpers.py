"""Agent stage helpers — token safety, validation, and AI call orchestration.

Extracted from agent_workflow.py to keep it under the 400-line limit.
"""

import json
import time

from config import config
from prompts.system_prompts import SYSTEM_PROMPTS


# ── Per-stage configuration ─────────────────────────────────

# ── Per-stage configuration ─────────────────────────────────

STAGE_CONFIG = {
    "industry_overview": {
        "max_tokens": config.STAGE_MAX_TOKENS["industry_overview"],
        "retry_count": config.RETRY_COUNT,
    },
    "company_deep_dive": {
        "max_tokens": config.STAGE_MAX_TOKENS["company_deep_dive"],
        "retry_count": config.RETRY_COUNT,
    },
    "investment_thesis": {
        "max_tokens": config.STAGE_MAX_TOKENS["investment_thesis"],
        "retry_count": config.RETRY_COUNT,
    },
}


def call_ai_or_fallback(agent, stage: str, prompt: str, label: str,
                        max_tokens: int = 4096, retry_count: int = 2) -> str:
    """Core fallback logic with per-stage retry.

    - AI mode → call LLM with up to retry_count+1 attempts.
    - Fallback mode → print prompt to terminal.
    """
    llm = agent.llm
    ai_mode = agent.ai_mode

    if ai_mode:
        system = SYSTEM_PROMPTS.get(stage, "")
        for attempt in range(retry_count + 1):
            result = llm.ask_with_log(
                prompt, system=system, label=label, max_tokens=max_tokens,
            )
            if result and len(result) > 50:
                return result
            if attempt < retry_count:
                wait = 2 ** (attempt + 1)
                print(
                    f"  ↳ [{label}] 第 {attempt+1} 次输出过短/为空，"
                    f"{wait}s 后重试…"
                )
                time.sleep(wait)
        print(f"  ↳ [{label}] {retry_count+1} 次尝试均失败，降级为 prompt 输出")

    # Fallback
    print(f"\n{'─'*50}")
    print(f"📋 [{label}] Prompt 模板（发送给 Claude Code 或任何 AI 工具）：")
    print(f"{'─'*50}")
    print(prompt[:800])
    if len(prompt) > 800:
        print(f"... [共 {len(prompt)} 字符，完整内容见 prompts/{stage}.md]")
    print(f"{'─'*50}\n")
    return ""


def validate_and_chase(agent, stage_key: str, output: str,
                       max_tokens: int) -> str:
    """Validate AI output; chase missing sections via follow-up call.

    Returns the (possibly supplemented) output unchanged if in fallback mode.
    """
    if not (output and agent.ai_mode):
        return output
    from prompts.validators import (
        build_chase_prompt, merge_chase_output, validate_stage_output,
    )
    missing = validate_stage_output(stage_key, output)
    if not missing:
        return output
    print(f"  🔍 {stage_key} 校验：缺少 {[m['label'] for m in missing]}")
    chase = call_ai_or_fallback(
        agent, stage_key,
        build_chase_prompt(stage_key, missing, output),
        f"{stage_key}补全",
        max_tokens=max_tokens // 2, retry_count=1,
    )
    return merge_chase_output(output, chase) if chase else output


def compress_context_for_prompt(llm_model: str,
                                *texts: str) -> list[str]:
    """Compress each text if estimated total tokens exceed model safe limit."""
    from utils.token_counter import compress_if_needed, count_tokens
    try:
        from utils.token_counter import safe_context_size
        limit = safe_context_size(llm_model)
    except Exception:
        limit = config.FALLBACK_CONTEXT_LIMIT  # conservative default
    total = sum(count_tokens(t) for t in texts)
    if total <= limit:
        return list(texts)
    # 用 token 数（而非字符长度）按比例分配，中文/英文混合文本分配更均匀
    token_counts = [count_tokens(t) for t in texts]
    allocations = [
        max(int(limit * tc / max(total, 1)), 500) for tc in token_counts
    ]
    return [
        compress_if_needed(t, a, f"历史分析[{i+1}]")
        for i, (t, a) in enumerate(zip(texts, allocations))
    ]

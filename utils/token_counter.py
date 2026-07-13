"""Token counting — estimate prompt size to guard against context window overflow."""

import sys


def _get_encoder():
    """Lazy-load tiktoken encoder. Returns None if tiktoken is unavailable."""
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str) -> int:
    """Estimate token count for a given text.

    Uses tiktoken if available, otherwise falls back to a character-based
    heuristic (~1 token per 3.5 chars for CJK, ~1 per 4 chars for English).
    """
    encoder = _get_encoder()
    if encoder is not None:
        return len(encoder.encode(text))
    # Fallback heuristic
    cjk = sum(1 for c in text if '一' <= c <= '鿿')
    other = len(text) - cjk
    return int(cjk / 1.5 + other / 4)


# Model context windows (conservative estimates)
MODEL_LIMITS = {
    # Anthropic
    "claude-opus-4":    180000,
    "claude-sonnet-4":  180000,
    "claude-haiku-4":   180000,
    "claude-opus-4-5":  180000,
    "claude-sonnet-4-5":180000,
    "claude-haiku-4-5": 180000,
    "claude-sonnet-4-6":180000,
    # OpenAI compat
    "deepseek-chat":    65536,
    "deepseek-reasoner":65536,
    "qwen-plus":       131072,
    "qwen-max":        32768,
    "gpt-4o":          128000,
    "gpt-4o-mini":     128000,
    # Default
    "default":          65536,
}


def model_context_limit(model: str) -> int:
    """Return the context window size for a given model name."""
    model_lower = model.lower()
    for key, limit in MODEL_LIMITS.items():
        if key in model_lower:
            return limit
    return MODEL_LIMITS["default"]


def safe_context_size(model: str, safety_ratio: float = 0.80) -> int:
    """Return 80% of the model's context window — the safe zone for input."""
    return int(model_context_limit(model) * safety_ratio)


def compress_if_needed(text: str, max_tokens: int, label: str = "") -> str:
    """Compress text by truncating the middle if it exceeds max_tokens.

    Keeps first 60% and last 35% of the content, inserting a truncation marker.
    This preserves intro context and final conclusions while reducing size.
    """
    current = count_tokens(text)
    if current <= max_tokens:
        return text

    # Truncate: keep first 60% + last 35% = 95% of max_tokens
    keep_first = int(max_tokens * 0.60)
    keep_last = int(max_tokens * 0.35)

    # Token-level truncation: use character approximation
    chars_per_token = len(text) / current if current > 0 else 4
    first_chars = int(keep_first * chars_per_token)
    last_chars = int(keep_last * chars_per_token)

    head = text[:first_chars]
    tail = text[-last_chars:]

    # Find natural break points
    for sep in ["\n\n", "\n", "。", ". "]:
        idx = head.rfind(sep)
        if idx > len(head) * 0.7:
            head = head[:idx]
            break

    marker = (
        f"\n\n─── [{label}内容因超出上下文限制已压缩"
        f"（原 {current} tokens → ~{keep_first + keep_last} tokens）] ───\n\n"
    )

    return head + marker + tail

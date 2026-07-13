"""Tests for utils/token_counter.py — all pure functions, zero mocking."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from utils.token_counter import (
    count_tokens,
    model_context_limit,
    safe_context_size,
    compress_if_needed,
    MODEL_LIMITS,
    _get_encoder,
)


class TestCountTokens:
    """count_tokens — tiktoken primary, CJK fallback."""

    def test_empty_string_returns_zero(self):
        assert count_tokens("") == 0

    def test_ascii_text_returns_positive(self):
        # Simple English sentence should produce a few tokens
        result = count_tokens("Hello world this is a test")
        assert result > 0
        assert isinstance(result, int)

    def test_cjk_text_returns_positive(self):
        result = count_tokens("这是一段中文测试文本用于验证分词计数功能")
        assert result > 0
        assert isinstance(result, int)

    def test_mixed_cjk_and_ascii(self):
        result = count_tokens("AI算力行业 2026年 market analysis")
        assert result > 0
        assert isinstance(result, int)

    def test_fallback_without_tiktoken(self, monkeypatch):
        """When tiktoken is unavailable, fallback heuristic gives positive count."""
        monkeypatch.setattr(
            "utils.token_counter._get_encoder", lambda: None
        )
        result = count_tokens("这是一段中文文本test English混合内容")
        assert result > 0
        assert isinstance(result, int)

    def test_long_text(self):
        text = "这是一段较长的文本。" * 200
        result = count_tokens(text)
        assert result > 100


class TestModelContextLimit:
    """model_context_limit — model name → context window size."""

    def test_exact_match_claude_sonnet(self):
        assert model_context_limit("claude-sonnet-4-6") == 180000

    def test_exact_match_deepseek(self):
        assert model_context_limit("deepseek-chat") == 65536

    def test_substring_match(self):
        # "claude-sonnet-4" is a substring of "claude-sonnet-4-6"
        assert model_context_limit("claude-sonnet-4-6-20241022") == 180000

    def test_case_insensitive(self):
        assert model_context_limit("Claude-Opus-4") == 180000

    def test_unknown_model_returns_default(self):
        assert model_context_limit("nonexistent-model-xyz") == MODEL_LIMITS["default"]

    def test_empty_string_returns_default(self):
        assert model_context_limit("") == MODEL_LIMITS["default"]

    def test_qwen_plus(self):
        assert model_context_limit("qwen-plus") == 131072

    def test_gpt4o(self):
        assert model_context_limit("gpt-4o") == 128000


class TestSafeContextSize:
    """safe_context_size — 80% safety margin by default."""

    def test_default_ratio_claude(self):
        # 80% of 180000 = 144000
        assert safe_context_size("claude-sonnet-4") == 144000

    def test_custom_ratio(self):
        assert safe_context_size("claude-sonnet-4", safety_ratio=0.5) == 90000

    def test_full_window(self):
        assert safe_context_size("claude-sonnet-4", safety_ratio=1.0) == 180000

    def test_zero_ratio(self):
        assert safe_context_size("claude-sonnet-4", safety_ratio=0.0) == 0

    def test_unknown_model_fallback(self):
        assert safe_context_size("unknown", safety_ratio=0.5) == int(65536 * 0.5)


class TestCompressIfNeeded:
    """compress_if_needed — truncate middle if over limit."""

    def test_under_limit_returns_unchanged(self):
        text = "short text"
        result = compress_if_needed(text, max_tokens=1000, label="test")
        assert result == text

    def test_over_limit_truncates(self):
        # Create a long text that definitely exceeds a small token limit
        long_text = "This is a sentence. " * 500
        max_tokens = 50
        result = compress_if_needed(long_text, max_tokens, label="测试")
        assert len(result) < len(long_text)
        assert "───" in result  # truncation marker present
        assert "测试" in result  # label preserved

    def test_label_in_marker(self):
        long_text = "Hello world. " * 500
        result = compress_if_needed(long_text, max_tokens=30, label="行业全景")
        assert "行业全景" in result
        assert "已压缩" in result

    def test_cjk_text_truncation(self):
        cjk_text = "这是一个中文句子用于测试压缩功能。" * 100
        max_tokens = 40
        result = compress_if_needed(cjk_text, max_tokens, label="中文")
        assert len(result) < len(cjk_text)
        # Should still contain CJK content
        assert "中文" in result

    def test_empty_label_default(self):
        long_text = "x " * 500
        result = compress_if_needed(long_text, max_tokens=20)
        assert "───" in result

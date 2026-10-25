"""Tests for tools/data_sources/industry_config.py — pure helper functions."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.data_sources.industry_config import _bk_code, _match_key


class TestBkCode:
    """_bk_code — fuzzy-match industry → EastMoney BK code."""

    def test_exact_match(self):
        assert _bk_code("AI算力") == "BK1163"

    def test_substring_match(self):
        # "AI算力相关" contains "AI算力"
        assert _bk_code("AI算力板块") == "BK1163"

    def test_reverse_substring_match(self):
        # "AI算力" is substring of the key "AI算力"? No, it's exact
        # but the function checks key in industry OR industry in key
        assert _bk_code("算力") == "BK1163"  # "AI算力" contains "算力"? no: "算力" in "AI算力"

    def test_unmatched_returns_unknown(self):
        assert _bk_code("完全不存在的行业xyz") == "未知"

    def test_bidirectional_matching(self):
        # key in industry works
        result = _bk_code("半导体")
        assert result != "未知"


class TestMatchKey:
    """_match_key — fuzzy-match a target against a list of keys."""

    def test_exact_match(self):
        assert _match_key("AI算力", ["AI算力", "人工智能"]) == "AI算力"

    def test_substring_match(self):
        assert _match_key("AI算力相关", ["AI算力", "消费"]) == "AI算力"

    def test_reverse_substring_match(self):
        assert _match_key("算力", ["AI算力", "消费"]) == "AI算力"

    def test_no_match_returns_none(self):
        assert _match_key("xyz", ["AI算力", "消费"]) is None

    def test_empty_keys_list(self):
        assert _match_key("AI算力", []) is None

    def test_first_match_wins(self):
        # Both match "AI算力", first should win
        assert _match_key("AI算力", ["AI算力", "AI算力板块"]) == "AI算力"

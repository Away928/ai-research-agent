"""Tests for tools/data_sources/market_sources.py — extracted pure functions."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.data_sources.market_sources import _is_valid_code, _normalize_mcap


class TestIsValidCode:
    """_is_valid_code — exclude 北交所/新三板/退市 stock codes."""

    def test_valid_shanghai(self):
        assert _is_valid_code("600941") is True

    def test_valid_shenzhen(self):
        assert _is_valid_code("000063") is True

    def test_valid_gem(self):
        assert _is_valid_code("300476") is True

    def test_valid_star(self):
        assert _is_valid_code("688256") is True

    def test_exclude_beijing_exchange(self):
        assert _is_valid_code("920123") is False

    def test_exclude_neeq_83(self):
        assert _is_valid_code("830001") is False

    def test_exclude_neeq_87(self):
        assert _is_valid_code("870001") is False

    def test_exclude_delisted(self):
        assert _is_valid_code("400001") is False

    def test_empty_string(self):
        # Empty string doesn't start with any prefix, so it's "valid"
        assert _is_valid_code("") is True

    def test_exclude_prefix_edge_cases(self):
        assert _is_valid_code("4") is False
        assert _is_valid_code("83") is False


class TestNormalizeMcap:
    """_normalize_mcap — normalize raw market cap to billions."""

    def test_normal_value(self):
        assert _normalize_mcap("195110000") == 19511.0

    def test_empty_string(self):
        assert _normalize_mcap("") == 0

    def test_none(self):
        assert _normalize_mcap(None) == 0

    def test_non_numeric(self):
        assert _normalize_mcap("not_a_number") == 0

    def test_zero(self):
        assert _normalize_mcap("0") == 0

    def test_small_value(self):
        """Raw value 50000 (万元) → 5.0 亿."""
        assert _normalize_mcap("50000") == 5.0

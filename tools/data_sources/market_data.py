"""
个股行情 + 行业指数 — 多源交叉验证取精度最高
================================================

成分股来自新浪概念板块 API，行情从成分股汇总推导 PE 中位数和总市值。
"""

import json
import statistics
import time
from typing import Dict, List, Optional

from tools.data_sources.industry_config import _INDUSTRY_INDEX_MAP, _bk_code
from tools.data_sources.market_sources import (
    _sina_concept_constituents,
    _sina_index_quote,
)


# ======================================================================
# MarketDataSource
# ======================================================================

class MarketDataSource:
    """行业行情 + 成分股。多源多层降级。"""

    name = "market_data"

    def __init__(self):
        pass

    # ── 主入口 ──────────────────────────────────────────────────

    def fetch(self, industry: str) -> Optional[Dict]:
        constituents = self._fetch_constituents(industry)
        quotes = self._fetch_quotes(industry, constituents)

        q_src = quotes.get("_source", "none") if quotes else "none"
        c_src = constituents[0].get("_source", "unknown") if constituents else "unknown"

        return {
            "行业": industry,
            "板块代码": _bk_code(industry),
            "行情": quotes,
            "成分股": constituents,
            "source": f"行情:{q_src} 成分股:{c_src}",
            "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ── 行情（行业级别：PE 中位数、总市值）─────────────────────

    def _fetch_quotes(self, industry: str, constituents: List[Dict]) -> Optional[Dict]:
        """行业行情。独立获取：指数点位(新浪API) + PE/市值(成分股汇总)。"""
        result = {"index_price": None, "index_change_pct": None,
                  "pe_median": None, "market_cap_total": None}

        # —— 板块指数点位（独立获取）——
        idx_code = _INDUSTRY_INDEX_MAP.get(industry)
        if idx_code:
            idx = _sina_index_quote(idx_code)
            if idx:
                result["index_name"] = idx["name"]
                result["index_price"] = idx["price"]
                result["index_change_pct"] = idx["change_pct"]
                result["index_source"] = idx["_source"]

        # —— PE中位数 + 总市值（从成分股汇总）——
        valid_pe = [c["pe"] for c in constituents if c.get("pe") and c["pe"] > 0]
        valid_mc = [c.get("market_cap_billion") for c in constituents
                    if c.get("market_cap_billion") and c["market_cap_billion"] > 0]
        if valid_pe:
            result["pe_median"] = round(statistics.median(valid_pe), 1)
            result["pe_note"] = f"PE 中位数由 {len(valid_pe)}/{len(constituents)} 只成分股计算"
        if valid_mc:
            result["market_cap_total"] = round(sum(valid_mc), 1)

        # ——来源标注——
        sources = []
        if result.get("index_source"):
            sources.append(result["index_source"])
        if valid_pe:
            sources.append("成分股汇总推导")
        result["_source"] = " + ".join(sources) if sources else "无可用数据源"

        return result

    # ── 成分股 ──────────────────────────────────────────────────

    def _fetch_constituents(self, industry: str) -> Optional[List[Dict]]:
        """获取成分股 — 新浪概念板块 API，按流通市值排序。"""
        return _sina_concept_constituents(industry)


# ── CLI ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    source = MarketDataSource()
    industry = sys.argv[1] if len(sys.argv) > 1 else "AI算力"
    data = source.fetch(industry)
    print(json.dumps(data, ensure_ascii=False, indent=2))

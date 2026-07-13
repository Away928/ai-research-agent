"""
财务数据源 — 通过 baostock 获取行业/公司关键财务指标
===========================================================

降级链：
    baostock 日线数据（在线）
      → 本地缓存（financial_data.json，7天过期）
        → 返回空（财务数据非必须，不阻塞工作流）

统一接口：
    from tools.data_sources.financial_data import FinancialDataSource
    source = FinancialDataSource()
    data = source.fetch("AI算力")
    # 返回 {公司财务: [...], source: "..."}
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import config

# 缓存
_CACHE_DIR = Path(__file__).parent.parent / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_FINANCIAL_CACHE_FILE = _CACHE_DIR / "financial_data.json"


class FinancialDataSource:
    """财务数据源。baostock 在线 > 缓存 > 返回空。"""

    name = "financial_data"

    def fetch(self, industry: str, constituents: list = None) -> Optional[Dict]:
        """获取行业关键公司的核心财务指标。"""
        companies = self._fetch_companies(industry, constituents)
        source_label = companies[0].get("_source", "无数据") if companies else "无数据"
        return {
            "行业": industry,
            "公司财务": companies,
            "指标说明": [
                "revenue_growth_pct: 营收同比增速(%)",
                "net_profit_growth_pct: 净利润同比增速(%)",
                "roe_pct: ROE(%)",
                "gross_margin_pct: 毛利率(%)",
                "debt_ratio_pct: 资产负债率(%)",
            ],
            "source": source_label,
            "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "财务数据来源为 baostock 日线 + 公开财报，具体数字需通过Wind终端验证",
        }

    def _fetch_companies(self, industry: str, constituents: list = None) -> List[Dict]:
        """降级获取财务数据。"""
        # 第1层：baostock
        data = self._from_baostock(industry, constituents)
        if data:
            return data

        # 第2层：本地缓存
        data = self._from_cache(industry)
        if data:
            return data

        return []

    # ── baostock ────────────────────────────────────────────────

    def _from_baostock(self, industry: str, constituents: list = None) -> Optional[List[Dict]]:
        """通过 baostock 获取成分股的财报核心指标。

        query_profit_data:  ROE、毛利率、净利润
        query_growth_data:  营收增速、净利润增速
        query_dupont_data:   资产负债率
        """
        if constituents is None:
            try:
                from tools.data_sources.market_data import MarketDataSource
                constituents = MarketDataSource()._fetch_constituents(industry)
            except Exception:
                pass  # constituents unavailable, will try cache
        if not constituents:
            return None

        try:
            import baostock as bs
            bs.login()
        except Exception:
            return None

        try:
            import socket
            socket.setdefaulttimeout(10)
            results = []
            for c in constituents[:config.MAX_FINANCIAL_COMPANIES]:
                code = c.get("code", "")
                name = c.get("name", "")
                if not code:
                    continue

                try:
                    row = self._query_stock_financials(bs, code, name)
                except Exception:
                    continue  # 单只股票查询失败，跳过
                if row:
                    results.append(row)

            bs.logout()
        except Exception:
            pass

        if results:
            self._save_to_cache(industry, results)
            return results
        return None

    def _query_stock_financials(self, bs, code: str, name: str) -> Optional[Dict]:
        """查询单只股票的财务指标。baostock 返回的是小数（0~1），需要 ×100 转百分比。

        动态选择最新可用季度：从当前最新季度往前尝试，取第一个有有效数据的季度。
        三个接口（profit/growth/dupont）各自独立降级。
        """
        prefix = "sh" if code.startswith(("6", "5")) else "sz"
        full_code = f"{prefix}.{code}"

        quarters = self._get_latest_quarters()

        roe = None
        gross_margin = None
        revenue_growth = None
        net_profit_growth = None
        debt_ratio = None
        data_period = None  # 实际使用的数据期间，如 "2026Q1"

        try:
            # 利润表 → ROE + 毛利率（遍历季度直到有数据）
            for year, quarter in quarters:
                rs = bs.query_profit_data(code=full_code, year=year, quarter=quarter)
                if rs.error_code == "0":
                    while rs.next():
                        r = rs.get_row_data()
                        roe = _pct(r[3])           # 加权ROE
                        gross_margin = _pct(r[5])  # 毛利率
                        if roe is not None or gross_margin is not None:
                            data_period = data_period or f"{year}Q{quarter}"
                            break
                    if roe is not None or gross_margin is not None:
                        break

            # 增长数据 → 营收增速 + 净利润增速
            for year, quarter in quarters:
                rs = bs.query_growth_data(code=full_code, year=year, quarter=quarter)
                if rs.error_code == "0":
                    while rs.next():
                        r = rs.get_row_data()
                        revenue_growth = _pct(r[3])       # 营收同比
                        net_profit_growth = _pct(r[5])    # 净利润同比
                        if revenue_growth is not None or net_profit_growth is not None:
                            break
                    if revenue_growth is not None or net_profit_growth is not None:
                        break

            # 杜邦分析 → 资产负债率
            for year, quarter in quarters:
                rs = bs.query_dupont_data(code=full_code, year=year, quarter=quarter)
                if rs.error_code == "0":
                    while rs.next():
                        r = rs.get_row_data()
                        debt_ratio = _pct(r[10])  # 资产负债率
                        if debt_ratio is not None:
                            break
                    if debt_ratio is not None:
                        break

        except Exception:
            pass  # single stock financial query failed, skip this stock

        # 如果所有字段都是 None，跳过这家公司
        if all(v is None for v in [roe, gross_margin, revenue_growth, net_profit_growth, debt_ratio]):
            return None

        source_label = "baostock（日线财报）"
        if data_period:
            period_year = int(data_period[:4])
            if datetime.now().year - period_year >= 2:
                source_label = "baostock（历史财报，数据陈旧）"

        return {
            "code": code,
            "name": name,
            "revenue_growth_pct": revenue_growth,
            "net_profit_growth_pct": net_profit_growth,
            "roe_pct": roe,
            "gross_margin_pct": gross_margin,
            "debt_ratio_pct": debt_ratio,
            "_source": source_label,
            "_data_period": data_period,
        }

    @staticmethod
    def _get_latest_quarters() -> list:
        """返回应尝试的 (year, quarter) 列表，从最新到最旧。

        A 股季报披露截止日：
          - Q1 (1-3月) 截止 4/30
          - Q2 (4-6月) 截止 8/31
          - Q3 (7-9月) 截止 10/31
          - Q4/年报 (10-12月) 截止次年 4/30

        保守策略：月份 >= 截止月 + 1 时才认为数据可用。
        """
        now = datetime.now()
        candidates = []
        current_year = now.year
        current_month = now.month

        # 当前年份已完成的季度
        if current_month >= 5:   # Q1 数据 5 月后可用
            candidates.append((current_year, 1))
        if current_month >= 9:   # Q2 数据 9 月后可用
            candidates.append((current_year, 2))
        if current_month >= 11:  # Q3 数据 11 月后可用
            candidates.append((current_year, 3))

        # 上一年年报和各季度（核心兜底）
        candidates.append((current_year - 1, 4))
        candidates.append((current_year - 1, 3))
        candidates.append((current_year - 1, 2))
        candidates.append((current_year - 1, 1))

        # 再往前一年，所有四个季度
        candidates.append((current_year - 2, 4))
        candidates.append((current_year - 2, 3))
        candidates.append((current_year - 2, 2))
        candidates.append((current_year - 2, 1))

        # 三年前，最终兜底（数据超过 2 年标注为陈旧）
        candidates.append((current_year - 3, 4))
        candidates.append((current_year - 3, 3))

        return candidates

    # ── 缓存 ────────────────────────────────────────────────────

    def _from_cache(self, industry: str) -> Optional[List[Dict]]:
        try:
            if not _FINANCIAL_CACHE_FILE.exists():
                return None
            with open(_FINANCIAL_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)

            # 模糊匹配行业名
            matched_key = None
            for key in cache:
                if key in industry or industry in key:
                    matched_key = key
                    break
            if not matched_key:
                return None

            entry = cache.get(matched_key, {})
            expired = True
            cached_at = entry.get("_cached_at", "")
            if cached_at:
                try:
                    t = time.mktime(time.strptime(cached_at, "%Y-%m-%d %H:%M:%S"))
                    if (time.time() - t) / 86400 <= config.CACHE_MAX_AGE_DAYS:
                        expired = False
                except (ValueError, OverflowError):
                    pass  # invalid timestamp, treat as expired

            companies = list(entry.get("data", []))  # 浅拷贝
            source_label = "缓存" if not expired else f"缓存(过期{config.CACHE_MAX_AGE_DAYS}天+)"
            for c in companies:
                c["_source"] = source_label
            return companies
        except Exception:
            return None

    def _save_to_cache(self, industry: str, companies: List[Dict]) -> None:
        try:
            cache = {}
            if _FINANCIAL_CACHE_FILE.exists():
                with open(_FINANCIAL_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            # 去掉 _source 再存
            clean = [{k: v for k, v in c.items() if k != "_source"} for c in companies]
            cache[industry] = {
                "data": clean,
                "_cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_FINANCIAL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _pct(raw: str) -> Optional[float]:
    """将 baostock 的原始小数转成百分比。返回 None 如果值无效。"""
    if not raw:
        return None
    try:
        v = float(raw)
        return round(v * 100, 2) if v != 0 else None
    except (ValueError, TypeError):
        return None

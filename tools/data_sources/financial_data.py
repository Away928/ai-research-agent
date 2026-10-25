"""
财务数据源 — 通过 baostock 获取行业/公司关键财务指标
===========================================================

降级链：
    baostock 季频财务接口（在线）
      → 本地缓存（financial_data.json，7天过期）
        → 返回空（财务数据非必须，不阻塞工作流）

统一接口：
    from tools.data_sources.financial_data import FinancialDataSource
    source = FinancialDataSource()
    data = source.fetch("AI算力")
    # 返回 {公司财务: [...], source: "..."}
"""

import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import config

# 缓存
_CACHE_DIR = Path(__file__).parent.parent / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_FINANCIAL_CACHE_FILE = _CACHE_DIR / "financial_data.json"
# Earlier cache records could contain incorrect YOYEquity/debt mappings.
_FINANCIAL_CACHE_SCHEMA_VERSION = 2


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
                "revenue_growth_pct: 主营业务收入同季度同比增速(%，按MBRevenue计算)",
                "net_profit_growth_pct: 净利润同比增速(%)",
                "roe_pct: ROE(%)",
                "gross_margin_pct: 毛利率(%)",
                "debt_ratio_pct: 资产负债率(%，balance.liabilityToAsset)",
            ],
            "source": source_label,
            "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "财务数据来自 baostock 财务接口或缓存；需以原始公开财报独立复核",
        }

    def _fetch_companies(self, industry: str, constituents: list = None) -> List[Dict]:
        """降级获取财务数据。"""
        # 第1层：baostock
        data = self._from_baostock(industry, constituents)
        if data:
            return data

        # 第2层：本地缓存
        data = self._from_cache(industry, constituents)
        if data:
            return data

        return []

    # ── baostock ────────────────────────────────────────────────

    def _from_baostock(self, industry: str, constituents: list = None) -> Optional[List[Dict]]:
        """通过 baostock 获取成分股的财报核心指标。

        query_profit_data:  ROE、毛利率、主营业务收入
        query_growth_data:  净利润同比增长率
        query_balance_data:  资产负债率
        """
        if constituents is None:
            try:
                from tools.data_sources.market_data import MarketDataSource
                constituents = MarketDataSource()._fetch_constituents(industry)
            except Exception:
                pass  # constituents unavailable, will try cache
        if not constituents:
            return None

        import socket
        old_timeout = socket.getdefaulttimeout()
        results = []
        session_ok = False
        try:
            import baostock as bs
            # Bound both login and individual queries. Restore the process-wide
            # default on exit; a permanent change can break unrelated clients.
            socket.setdefaulttimeout(10)
            session = bs.login()
            if str(getattr(session, "error_code", "")) != "0":
                return None
            session_ok = True
            for c in constituents[:config.MAX_FINANCIAL_COMPANIES]:
                code = c.get("code", "")
                name = c.get("name", "")
                if not code:
                    continue
                try:
                    row = self._query_stock_financials(bs, code, name)
                except Exception:
                    continue  # Per-stock failure must not erase earlier records.
                if row:
                    results.append(row)
        except Exception:
            return None
        finally:
            if session_ok:
                try:
                    bs.logout()
                except Exception:
                    pass
            socket.setdefaulttimeout(old_timeout)

        if results:
            self._save_to_cache(industry, results)
            return results
        return None

    def _query_stock_financials(self, bs, code: str, name: str) -> Optional[Dict]:
        """Read documented baostock field names, never positional guesses.

        Official API contracts:
        - profit: roeAvg, gpMargin, MBRevenue
        - growth: YOYNI (NOT YOYEquity, which is equity growth)
        - balance: liabilityToAsset (NOT the DuPont endpoint)
        - main-business revenue YoY: MBRevenue(now)/MBRevenue(same quarter
          previous year)-1, when both same-quarter figures are available.

        Missing schema, mismatched statistics dates and missing denominators are
        treated as unavailable instead of being presented as financial facts.
        """
        prefix = "sh" if code.startswith(("6", "5")) else "sz"
        full_code = f"{prefix}.{code}"
        quarters = self._get_latest_quarters()
        metric_periods = {}
        metric_publication_dates = {}
        metric_methods = {}
        metrics = {
            "roe_pct": None, "gross_margin_pct": None,
            "revenue_growth_pct": None, "net_profit_growth_pct": None,
            "debt_ratio_pct": None,
        }
        profit_cache = {}

        def rows_for(method, year, quarter):
            """Validate schema, record date and publication date per result."""
            try:
                rs = method(code=full_code, year=year, quarter=quarter)
                if str(rs.error_code) != "0":
                    return []
                fields = getattr(rs, "fields", None) or []
                if not fields or len(fields) != len(set(fields)):
                    return []
                expected = f"{year}-{quarter * 3:02d}-" + (
                    "31" if quarter in (1, 4) else "30"
                )
                rows = []
                while rs.next():
                    raw = rs.get_row_data()
                    if not isinstance(raw, (list, tuple)) or len(raw) != len(fields):
                        continue
                    row = dict(zip(fields, raw))
                    if row.get("statDate") != expected:
                        continue
                    pub = row.get("pubDate")
                    if pub:
                        try:
                            if datetime.strptime(pub, "%Y-%m-%d").date() > datetime.now().date():
                                continue
                        except (TypeError, ValueError):
                            continue
                    rows.append(row)
                return rows
            except (AttributeError, KeyError, TypeError, ValueError, IndexError):
                return []

        def set_metric(key, candidate, year, quarter, publication, method):
            if metrics[key] is not None or candidate is None:
                return
            metrics[key] = candidate
            metric_periods[key] = f"{year}Q{quarter}"
            if publication:
                metric_publication_dates[key] = publication
            metric_methods[key] = method

        def get_profit_rows(year, quarter):
            key = year, quarter
            if key not in profit_cache:
                profit_cache[key] = rows_for(bs.query_profit_data, year, quarter)
            return profit_cache[key]

        # Most-recent-first: each metric may have a different valid quarter.
        for year, quarter in quarters:
            if all(metrics[k] is not None for k in (
                "roe_pct", "gross_margin_pct", "revenue_growth_pct"
            )):
                break
            for row in get_profit_rows(year, quarter):
                set_metric("roe_pct", _pct(row.get("roeAvg")), year, quarter,
                           row.get("pubDate"), "profit.roeAvg")
                set_metric("gross_margin_pct", _pct(row.get("gpMargin")), year, quarter,
                           row.get("pubDate"), "profit.gpMargin")
                if metrics["revenue_growth_pct"] is None:
                    cur = _number(row.get("MBRevenue"))
                    if cur is None or cur < 0:
                        continue
                    for prior in get_profit_rows(year - 1, quarter):
                        baseline = _number(prior.get("MBRevenue"))
                        if baseline is None or baseline <= 0:
                            continue
                        change = (cur / baseline - 1) * 100
                        if not math.isfinite(change):
                            continue
                        set_metric(
                            "revenue_growth_pct", round(change, 2),
                            year, quarter, row.get("pubDate"),
                            f"profit.MBRevenue 同季同比 ({year}Q{quarter}/"
                            f"{year-1}Q{quarter}-1)",
                        )
                        break

        # growth.YOYNI is net income YoY. growth.YOYEquity is equity YoY.
        for year, quarter in quarters:
            if metrics["net_profit_growth_pct"] is not None:
                break
            for row in rows_for(bs.query_growth_data, year, quarter):
                set_metric("net_profit_growth_pct", _pct(row.get("YOYNI")),
                           year, quarter, row.get("pubDate"), "growth.YOYNI")

        # Solvency ratios must come from balance, not DuPont.
        for year, quarter in quarters:
            if metrics["debt_ratio_pct"] is not None:
                break
            for row in rows_for(bs.query_balance_data, year, quarter):
                set_metric("debt_ratio_pct", _pct(row.get("liabilityToAsset")),
                           year, quarter, row.get("pubDate"), "balance.liabilityToAsset")

        if all(value is None for value in metrics.values()):
            return None
        periods = set(metric_periods.values())
        data_period = next(iter(periods)) if len(periods) == 1 else None
        source_label = "baostock（财务接口，字段名校验）"
        if any(datetime.now().year - int(period[:4]) >= 2 for period in periods):
            source_label = "baostock（含历史财报，部分数据陈旧）"
        return {
            "code": code,
            "name": name,
            **metrics,
            "_source": source_label,
            "_data_period": data_period,
            "_metric_periods": metric_periods,
            "_metric_publication_dates": metric_publication_dates,
            "_metric_methods": metric_methods,
        }

    @staticmethod
    def _get_latest_quarters(as_of: Optional[datetime] = None) -> list:
        """Return fiscal quarters in newest-first order after disclosure cutoff.

        Conservative A-share disclosure cutoffs:
          Q1: May 1 of year; Q2: Sep 1; Q3: Nov 1;
          Q4 annual report: May 1 of following year.

        These are eligibility windows, not proof that an individual company
        has published its statements. Missing quarters still require fallback.
        """
        now = as_of or datetime.now()
        quarters = []
        for year in range(now.year - 3, now.year + 1):
            for quarter in (1, 2, 3, 4):
                # Keep the original three-year fallback bound.
                if year == now.year - 3 and quarter < 3:
                    continue
                cutoff = {
                    1: datetime(year, 5, 1),
                    2: datetime(year, 9, 1),
                    3: datetime(year, 11, 1),
                    4: datetime(year + 1, 5, 1),
                }[quarter]
                if now >= cutoff:
                    quarters.append((year, quarter))
        return sorted(quarters, reverse=True)

    # ── 缓存 ────────────────────────────────────────────────────

    def _from_cache(
        self, industry: str, constituents: Optional[List[Dict]] = None
    ) -> Optional[List[Dict]]:
        try:
            if not _FINANCIAL_CACHE_FILE.exists():
                return None
            with open(_FINANCIAL_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)

            # Exact industry key only: fuzzy matching could silently mix
            # unrelated sectors (e.g. "AI" and "AI算力").
            entry = cache.get(industry)
            if (not isinstance(entry, dict) or
                    entry.get("_schema_version") != _FINANCIAL_CACHE_SCHEMA_VERSION):
                # Fail closed: old caches may contain wrongly mapped metrics.
                return None
            expired = True
            cached_at = entry.get("_cached_at", "")
            if cached_at:
                try:
                    t = time.mktime(time.strptime(cached_at, "%Y-%m-%d %H:%M:%S"))
                    if (time.time() - t) / 86400 <= config.CACHE_MAX_AGE_DAYS:
                        expired = False
                except (ValueError, OverflowError):
                    pass  # invalid timestamp, treat as expired

            # Never mutate the cached dictionaries in place. If a fresh list
            # of constituents exists, reject unrelated historical constituents.
            current_codes = {
                str(c.get("code")) for c in (constituents or [])
                if isinstance(c, dict) and c.get("code") is not None
            }
            companies = [
                dict(c) for c in (entry.get("data") or [])
                if isinstance(c, dict)
                and (not current_codes or str(c.get("code")) in current_codes)
            ]
            if not companies:
                return None
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
                "_schema_version": _FINANCIAL_CACHE_SCHEMA_VERSION,
                "_cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_FINANCIAL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _number(raw) -> Optional[float]:
    """Parse numeric financial fields; preserve zero and reject NaN/Infinity."""
    if raw is None or raw == "":
        return None
    try:
        number = float(raw)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _pct(raw: str) -> Optional[float]:
    """将 baostock 的原始小数转成百分比。返回 None 如果值无效。"""
    v = _number(raw)
    return round(v * 100, 2) if v is not None else None

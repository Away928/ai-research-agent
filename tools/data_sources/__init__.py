"""
数据源管理器 — 统一入口，多源并发采集，单点失败不阻塞
=============================================================

将所有数据源（行情、财务、公告、新闻）统一封装，提供 gather() 方法
一次性采集研究所需的全维度数据。

统一接口：
    from tools.data_sources import DataSourceManager
    mgr = DataSourceManager()
    package = mgr.gather("AI算力")
    # 返回 dict: {industry, timestamp, market_data: {...}, financial_data: {...}, ...}

    # 打印数据采集报告
    mgr.print_summary(package)

    # 获取结构化摘要（供 Web 展示）
    summary = mgr.build_summary(package)

向后兼容：
    from tools.data_fetcher import IndustryDataFetcher  # 仍然可用（已废弃）
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

from tools.data_sources.market_data import MarketDataSource
from tools.data_sources.financial_data import FinancialDataSource
from tools.data_sources.announcement_data import AnnouncementDataSource
from tools.data_sources.news_data import NewsDataSource
from tools.user_data import UserDataManager
from tools.data_sources.provenance import inspect_provenance


class DataSourceManager:
    """统一数据采集管理器。"""

    def __init__(self):
        self._market_source = MarketDataSource()
        self._sources = [
            ("market_data", self._market_source),
            ("financial_data", FinancialDataSource()),
            ("announcement_data", AnnouncementDataSource()),
            ("news_data", NewsDataSource()),
        ]
    @staticmethod
    def _has_payload(name: str, result: dict) -> bool:
        """Distinguish an envelope dict from actual collected observations."""
        if not isinstance(result, dict):
            return False
        if name == "market_data":
            quotes = result.get("行情") or {}
            return bool(result.get("成分股")) or any(
                quotes.get(field) is not None for field in (
                    "index_price", "index_change_pct",
                    "pe_median", "market_cap_total",
                )
            )
        if name == "financial_data":
            return any(
                isinstance(c, dict) and any(
                    c.get(metric) is not None for metric in (
                        "roe_pct", "gross_margin_pct", "revenue_growth_pct",
                        "net_profit_growth_pct", "debt_ratio_pct",
                    )
                )
                for c in (result.get("公司财务") or [])
            )
        if name == "announcement_data":
            return bool(result.get("公告") or result.get("研报"))
        if name == "news_data":
            return bool(result.get("新闻"))
        return False

    @staticmethod
    def _payload_status(result: dict) -> str:
        """Never call expired cache a fresh successful collection."""
        if "过期" in str(result.get("source", "")):
            return "⚠️ 缓存数据过期"
        if any("过期" in str(item.get("_source", "")) for key in (
            "公司财务", "公告", "新闻",
        ) for item in (result.get(key) or []) if isinstance(item, dict)):
            return "⚠️ 缓存数据过期"
        return "✅ 成功"

    def gather(self, industry: str) -> Dict:
        """
        采集所有可用的数据源，组装成统一数据包。

        架构：行情主线程先完成（baostock 不能在线程间共享连接），
        然后财务 + 公告 + 新闻并发采集。
        单个数据源失败不影响其他数据源。
        """
        package = {
            "行业": industry,
            "采集时间": time.strftime("%Y-%m-%d %H:%M:%S"),
            "数据源状态": {},
        }

        # Retrieve one constituent snapshot per gather invocation and share it
        # across market, financial, announcements and news. Never reuse a stale
        # snapshot across later runs on the same DataSourceManager instance.
        try:
            constituents = self._market_source._fetch_constituents(industry) or []
        except Exception as exc:
            constituents = []
            package["数据源状态"]["constituents"] = f"❌ 成分股获取异常: {exc}"

        try:
            result = self._market_source.fetch(industry, constituents=constituents)
            package["market_data"] = result or {"行业": industry, "source": "无可用数据"}
            package["数据源状态"]["market_data"] = (
                self._payload_status(result) if self._has_payload("market_data", result)
                else "⚠️ 无有效数据"
            )
        except Exception as e:
            package["market_data"] = {
                "行业": industry,
                "source": "不可用",
                "error": str(e),
            }
            package["数据源状态"]["market_data"] = f"❌ 异常: {e}"

        # Step 2: 并发 — 财务 + 公告 + 新闻
        def _fetch_one(source_name, source, **kwargs):
            return source_name, source.fetch(industry, **kwargs)

        other_tasks = [
            ("financial_data", self._sources[1][1], {"constituents": constituents}),
            ("announcement_data", self._sources[2][1], {"constituents": constituents}),
            ("news_data", self._sources[3][1], {"constituents": constituents}),
        ]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_fetch_one, name, src, **kwargs): name
                for name, src, kwargs in other_tasks
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    source_name, result = future.result()
                    package[source_name] = result or {
                        "行业": industry, "source": "无可用数据"
                    }
                    package["数据源状态"][source_name] = (
                        self._payload_status(result)
                        if self._has_payload(source_name, result)
                        else "⚠️ 无有效数据"
                    )
                except Exception as e:
                    package[source_name] = {
                        "行业": industry,
                        "source": "不可用",
                        "error": str(e),
                    }
                    package["数据源状态"][source_name] = f"❌ 异常: {e}"

        package["数据源状态"]["user_supplements"] = "— 无用户补充数据"
        # Additional metadata only: this does not certify any underlying claims.
        package["来源核查"] = inspect_provenance(package)

        return package

    def gather_summary(self, industry: str) -> str:
        """生成数据采集摘要，供 CLI 快速查看。"""
        package = self.gather(industry)
        lines = [
            f"📊 数据采集摘要 — {industry}",
            f"采集时间: {package['采集时间']}",
            f"\n数据源状态:",
        ]
        for name, status in package.get("数据源状态", {}).items():
            label = {
                "market_data": "行业行情",
                "financial_data": "财务数据",
                "announcement_data": "公告/研报",
                "news_data": "财经新闻",
            }.get(name, name)
            lines.append(f"  {label}: {status}")

        # 数据量统计
        lines.append(f"\n数据量统计:")
        for name, data in package.items():
            if name == "数据源状态" or name == "行业" or name == "采集时间":
                continue
            if name == "market_data" and data.get("行情"):
                lines.append(f"  行情数据: 1条（{data['行情'].get('_source', '?')}）")
                constituents = data.get("成分股", [])
                if constituents:
                    lines.append(f"  成分股: {len(constituents)}家")
            elif name == "financial_data":
                companies = data.get("公司财务", [])
                if companies:
                    lines.append(f"  财务数据: {len(companies)}家公司")
            elif name == "announcement_data":
                announcements = data.get("公告", [])
                reports = data.get("研报", [])
                lines.append(f"  公告: {len(announcements)}条")
                lines.append(f"  研报: {len(reports)}条")
            elif name == "news_data":
                news = data.get("新闻", [])
                if news:
                    lines.append(f"  新闻: {len(news)}条")

        return "\n".join(lines)

    # ── 展示层方法（委托给 summary 模块）───────────────────────

    @staticmethod
    def build_summary(package):
        from tools.data_sources.summary import build_summary as _build
        return _build(package)

    @staticmethod
    def print_summary(package):
        from tools.data_sources.summary import print_summary as _print
        _print(package)

    @staticmethod
    def build_company_data(market_data: dict, fin_data: dict) -> list:
        """构建每家公司全量数据 dict（行情 + 财务），各阶段共用。"""
        constituents = market_data.get("成分股", []) or []
        fin_companies = {
            c["code"]: c for c in (fin_data.get("公司财务", []) or [])
        }
        companies = []
        for const in constituents[:15]:
            code = const.get("code", "")
            fc = fin_companies.get(code, {})
            companies.append({
                "代码": code,
                "名称": const.get("name", ""),
                "市值(亿)": const.get("market_cap_billion"),
                "PE": const.get("pe"),
                "ROE(%)": fc.get("roe_pct"),
                "毛利率(%)": fc.get("gross_margin_pct"),
                "营收增速(%)": fc.get("revenue_growth_pct"),
                "净利增速(%)": fc.get("net_profit_growth_pct"),
                "负债率(%)": fc.get("debt_ratio_pct"),
                "财务数据来源": fc.get("_source"),
                "财务指标披露日": fc.get("_metric_publication_dates") or {},
                "财务指标计算口径": fc.get("_metric_methods") or {},
                "财务指标报告期": {
                    "ROE(%)": (fc.get("_metric_periods") or {}).get("roe_pct"),
                    "毛利率(%)": (fc.get("_metric_periods") or {}).get("gross_margin_pct"),
                    "营收增速(%)": (fc.get("_metric_periods") or {}).get("revenue_growth_pct"),
                    "净利增速(%)": (fc.get("_metric_periods") or {}).get("net_profit_growth_pct"),
                    "负债率(%)": (fc.get("_metric_periods") or {}).get("debt_ratio_pct"),
                },
                # Internal record references, not independent verification.
                "财务指标证据ID": {
                    label: f"FIN-{code}-{field}"
                    for label, field in (
                        ("ROE(%)", "roe_pct"),
                        ("毛利率(%)", "gross_margin_pct"),
                        ("营收增速(%)", "revenue_growth_pct"),
                        ("净利增速(%)", "net_profit_growth_pct"),
                        ("负债率(%)", "debt_ratio_pct"),
                    )
                    if code and fc.get(field) is not None
                },
            })
        return companies


# ── 便捷函数 ──────────────────────────────────────────────────


def quick_gather(industry: str):
    """快速采集，一行代码。"""
    return DataSourceManager().gather(industry)


# ── CLI ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    industry = sys.argv[1] if len(sys.argv) > 1 else "AI算力"
    mgr = DataSourceManager()
    print(mgr.gather_summary(industry))

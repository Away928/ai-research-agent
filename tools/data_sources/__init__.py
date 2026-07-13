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
        # 成分股缓存（单次采集生命周期内共享，避免重复拉取）
        self._cached_constituents: Dict[str, list] = {}

    def _get_constituents(self, industry: str) -> list:
        """获取成分股（带缓存，单次采集周期内只拉一次）。

        同时完成行情采集（行情也在 market_data 拉取过程中完成），
        然后并发调用财务、新闻、公告（它们只依赖成分股列表）。
        """
        if industry not in self._cached_constituents:
            # 行情也在这一步完成（market_data.fetch 内部调 _fetch_constituents）
            self._cached_constituents[industry] = (
                self._market_source._fetch_constituents(industry) or []
            )
        return self._cached_constituents[industry]

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

        # Step 1: 行情 — 主线程完成（内部调成分股 + 腾讯/新浪/baostock）
        # 成分股结果同时缓存，供下游使用
        constituents = self._get_constituents(industry)

        try:
            result = self._market_source.fetch(industry)
            if result:
                package["market_data"] = result
                package["数据源状态"]["market_data"] = "✅ 成功"
            else:
                package["market_data"] = {"行业": industry, "source": "无可用数据"}
                package["数据源状态"]["market_data"] = "⚠️ 无数据"
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
                    if result:
                        package[source_name] = result
                        package["数据源状态"][source_name] = "✅ 成功"
                    else:
                        package[source_name] = {"行业": industry, "source": "无可用数据"}
                        package["数据源状态"][source_name] = "⚠️ 无数据"
                except Exception as e:
                    package[source_name] = {
                        "行业": industry,
                        "source": "不可用",
                        "error": str(e),
                    }
                    package["数据源状态"][source_name] = f"❌ 异常: {e}"

        package["数据源状态"]["user_supplements"] = "— 无用户补充数据"

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

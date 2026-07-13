"""
财经新闻数据源 — 行业相关新闻聚合
======================================

降级链：
    AKShare stock_news_em（在线，按公司名 + 行业关键词搜索）
      → 返回空（新闻必须是实时的，不做缓存）

统一接口：
    from tools.data_sources.news_data import NewsDataSource
    source = NewsDataSource()
    data = source.fetch("AI算力")
    # 返回 {新闻: [...], source: "..."}
"""

import time
from typing import Dict, List, Optional

from config import config

# 情感关键词（轻量，不做 NLP）
_POSITIVE_WORDS = ["增长", "突破", "中标", "利好", "签约", "增持", "盈利", "扩产", "涨停", "新高"]
_NEGATIVE_WORDS = ["下降", "亏损", "减持", "处罚", "警告", "退市", "下滑", "跌停", "暴雷", "违约"]


class NewsDataSource:
    """财经新闻数据源。AKShare stock_news_em 在线 > 返回空。"""

    name = "news_data"

    def fetch(self, industry: str, max_items: int = None, constituents: list = None) -> Optional[Dict]:
        """获取行业相关财经新闻。"""
        if max_items is None:
            max_items = config.NEWS_MAX_ITEMS
        news = self._fetch_news(industry, max_items, constituents)
        sources = set(n.get("source", "") for n in news) if news else set()
        return {
            "行业": industry,
            "新闻": news if news else [],
            "数量": len(news) if news else 0,
            "source": f"来源: {', '.join(sources)}" if sources else "无可用数据源",
            "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _fetch_news(self, industry: str, max_items: int, constituents: list = None) -> Optional[List[Dict]]:
        # AKShare 个股新闻 + 行业关键词搜索，无缓存
        data = self._from_akshare(industry, constituents)
        if data:
            return data[:max_items]
        return None

    def _from_akshare(self, industry: str, constituents: list = None) -> Optional[List[Dict]]:
        """通过 AKShare stock_news_em 按公司名 + 行业关键词搜索新闻。

        策略：
        1. 取行业前 N 家龙头公司，逐只搜公司名
        2. 追加行业关键词搜索（覆盖行业级新闻）
        3. 汇总去重后返回
        """
        if constituents is None:
            try:
                from tools.data_sources.market_data import MarketDataSource
                constituents = MarketDataSource()._fetch_constituents(industry)
            except Exception:
                pass
        if not constituents:
            return None

        try:
            import akshare as ak
        except ImportError:
            return None

        all_news = []
        seen_titles = set()

        def _collect_news(search_keyword: str):
            try:
                df = ak.stock_news_em(symbol=search_keyword)
                if df is None or len(df) == 0:
                    return
                for _, row in df.iterrows():
                    title = str(row.get("新闻标题", ""))
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    all_news.append({
                        "title": title,
                        "date": str(row.get("发布时间", ""))[:10],
                        "source": str(row.get("文章来源", "")),
                        "summary": str(row.get("新闻内容", ""))[:150],
                        "url": str(row.get("新闻链接", "")),
                        "sentiment": _classify_sentiment(title),
                        "_source": "AKShare",
                    })
            except Exception:
                pass  # single search failed

        # 1. 按龙头公司名搜索（前 3 家）
        for c in constituents[:config.TOP_COMPANIES_FOR_NEWS]:
            name = c.get("name", "")
            if name:
                _collect_news(name)

        # 2. 行业关键词搜索
        _collect_news(industry)

        return all_news if all_news else None


def _classify_sentiment(title: str) -> str:
    """基于标题关键词做情感标注。"""
    for w in _POSITIVE_WORDS:
        if w in title:
            return "正面"
    for w in _NEGATIVE_WORDS:
        if w in title:
            return "负面"
    return "中性"

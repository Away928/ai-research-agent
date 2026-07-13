"""
公告与研报数据源 — 从巨潮资讯网获取上市公司公告
=============================================================

降级链：
    巨潮资讯网 API（在线，POST /new/hisAnnouncement/query）
      → 本地缓存（announcement_cache.json，7天过期）
        → 返回空

统一接口：
    from tools.data_sources.announcement_data import AnnouncementDataSource
    source = AnnouncementDataSource()
    data = source.fetch("AI算力")
    # 返回 {公告: [...], 研报: [...], source: "..."}
"""

import json
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from config import config

# 缓存
_CACHE_DIR = Path(__file__).parent.parent / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_ANNOUNCEMENT_CACHE_FILE = _CACHE_DIR / "announcement_cache.json"


class AnnouncementDataSource:
    """上市公司公告数据源。巨潮资讯网在线 > 缓存 > 返回空。"""

    name = "announcement_data"

    # 巨潮资讯网接口
    CNINFO_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

    def fetch(self, industry: str, constituents: list = None) -> Optional[Dict]:
        """获取公告列表和研报引用。"""
        announcements, ann_source = self._fetch_announcements(industry, constituents)
        reports = self._fetch_reports(industry)

        return {
            "行业": industry,
            "公告": announcements if announcements else [],
            "研报": reports if reports else [],
            "source": ann_source if announcements else "无可用数据源",
            "fetch_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": (
                "公告来自巨潮资讯网公共查询接口。"
                "不下载PDF全文，仅提供标题和链接。"
                "研报暂无免费在线源，如需完整研报请使用Wind/iFinD等终端。"
            ),
        }

    # ── 公告 ──────────────────────────────────────────────────

    def _fetch_announcements(
        self, industry: str, constituents: list = None, page_size: int = 10
    ) -> tuple[List[Dict], str]:
        """获取公告。降级：巨潮在线 → 缓存 → 返回空。"""
        # 第1层：巨潮资讯网在线
        data = self._from_cninfo(industry, constituents, page_size)
        if data:
            self._save_to_cache(industry, data)
            return data, "巨潮资讯网"

        # 第2层：本地缓存
        data = self._from_cache(industry)
        if data:
            return data[:page_size], data[0].get("_source", "缓存") if data else "缓存"

        return None, "无可用数据源"

    def _from_cninfo(self, industry: str, constituents: list = None, page_size: int = None) -> Optional[List[Dict]]:
        """遍历前 N 家成分股公司，每家取最新公告，去重后按日期降序返回。"""
        if page_size is None:
            page_size = config.ANNOUNCEMENT_MAX_ITEMS
        if constituents is None:
            try:
                from tools.data_sources.market_data import MarketDataSource
                constituents = MarketDataSource()._fetch_constituents(industry)
            except Exception:
                constituents = None

        if not constituents:
            return None

        seen_ids = set()
        results = []

        # 遍历前 TOP_N 家公司，每家取最新 2 条公告（不做关键词过滤）
        top_n = config.ANNOUNCEMENT_TOP_COMPANIES
        for c in constituents[:top_n]:
            company_name = c.get("name", "")
            if not company_name:
                continue
            # 直接搜公司名，按日期降序，取最新 2 条
            ann = self._query_cninfo(company_name, page_size=2)
            if ann:
                for a in ann:
                    aid = a.get("id", "")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        results.append(a)

        # 去重后按日期降序排列
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        return results[:page_size] if results else None

    def _query_cninfo(
        self, searchkey: str, page_size: int = 5
    ) -> Optional[List[Dict]]:
        """单次查询巨潮资讯网公告接口。"""
        try:
            data = urllib.parse.urlencode({
                "pageNum": "1",
                "pageSize": str(page_size),
                "tabName": "fulltext",
                "searchkey": searchkey,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.CNINFO_URL,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                announcements = raw.get("announcements", [])
                if not announcements:
                    return None

                return [
                    {
                        "id": a.get("announcementId", ""),
                        "title": a.get("announcementTitle", ""),
                        "company": a.get("secName", ""),
                        "date": _parse_timestamp(a.get("announcementTime", 0)),
                        "url": (
                            f"http://static.cninfo.com.cn/{a['adjunctUrl']}"
                            if a.get("adjunctUrl") else ""
                        ),
                        "type": _classify_announcement(a.get("announcementTitle", "")),
                    }
                    for a in announcements
                ]
        except Exception:
            return None

    # ── 研报 ──────────────────────────────────────────────────

    def _fetch_reports(self, industry: str) -> Optional[List[Dict]]:
        """研报数据。暂无免费在线源，返回空。"""
        return None

    # ── 缓存 ──────────────────────────────────────────────────

    def _from_cache(self, industry: str) -> Optional[List[Dict]]:
        try:
            if not _ANNOUNCEMENT_CACHE_FILE.exists():
                return None
            with open(_ANNOUNCEMENT_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)

            matched_key = None
            for key in cache:
                if key in industry or industry in key:
                    matched_key = key
                    break
            if not matched_key:
                return None

            entry = cache[matched_key]
            expired = True
            cached_at = entry.get("_cached_at", "")
            if cached_at:
                try:
                    t = time.mktime(time.strptime(cached_at, "%Y-%m-%d %H:%M:%S"))
                    if (time.time() - t) / 86400 <= config.CACHE_MAX_AGE_DAYS:
                        expired = False
                except (ValueError, OverflowError):
                    pass  # invalid timestamp

            source_label = "缓存" if not expired else f"缓存(过期{config.CACHE_MAX_AGE_DAYS}天+)"
            data = list(entry.get("data", []))
            for d in data:
                d["_source"] = source_label
            return data
        except Exception:
            return None

    def _save_to_cache(self, industry: str, announcements: List[Dict]) -> None:
        try:
            cache = {}
            if _ANNOUNCEMENT_CACHE_FILE.exists():
                with open(_ANNOUNCEMENT_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            clean = [{k: v for k, v in a.items() if k != "_source"} for a in announcements]
            cache[industry] = {
                "data": clean,
                "_cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(_ANNOUNCEMENT_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# ── 工具函数 ────────────────────────────────────────────────────

def _parse_timestamp(ts: int) -> str:
    """将毫秒时间戳转为可读日期。"""
    if not ts:
        return "未知"
    try:
        return time.strftime("%Y-%m-%d", time.localtime(ts / 1000))
    except Exception:
        return str(ts)


def _classify_announcement(title: str) -> str:
    """根据标题自动分类公告类型。"""
    t = title.lower() if title else ""
    if "年报" in t or "年度报告" in t:
        return "年报"
    if "半年报" in t or "半年度报告" in t:
        return "半年报"
    if "季报" in t or "季度报告" in t:
        return "季报"
    if "投资者关系" in t:
        return "投资者关系活动"
    if "合同" in t or "中标" in t:
        return "重大合同"
    if "业绩预告" in t or "业绩快报" in t:
        return "业绩预告"
    return "公告"

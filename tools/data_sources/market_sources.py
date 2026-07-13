"""
行情数据源 — 腾讯 / 新浪 / 东方财富 / akshare / baostock
==========================================================

各函数独立获取数据，不依赖 MarketDataSource 类。
"""

import json
import time
import urllib.request
from typing import Dict, List, Optional

from config import config

from tools.data_sources.industry_config import _bk_code


# ── 新浪指数 ──────────────────────────────────────────────────────

def _sina_index_quote(sina_code: str) -> Optional[Dict]:
    """通过新浪 API 获取指数行情（国证/中证等）。

    Args:
        sina_code: e.g. 'sz399363' (国证算力)

    Returns:
        {name, price, change_pct, _source}
    """
    url = f"https://hq.sinajs.cn/list={sina_code}"
    req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
    try:
        raw = urllib.request.urlopen(req, timeout=8).read().decode("gbk")
        parts = raw.split('"')[1].split(",")
        prev_close = float(parts[2]) if len(parts) > 2 and parts[2] else 0
        price = float(parts[3]) if len(parts) > 3 and parts[3] else 0
        chg = round((price - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0.0
        return {
            "name": parts[0],
            "price": price,
            "change_pct": chg,
            "_source": "新浪指数行情",
        }
    except Exception:
        return None


# ── 新浪财经 ──────────────────────────────────────────────────────

def _sina_quotes(codes: List[str]) -> List[Dict]:
    """通过新浪财经 API 获取个股实时行情。

    返回 code 为纯数字（不含 sh/sz 前缀），便于跟种子数据合并。
    """
    sina_codes = []
    for c in codes:
        raw_code = c.replace("sh", "").replace("sz", "")
        if raw_code.startswith(("6", "5")):
            sina_codes.append(f"sh{raw_code}")
        else:
            sina_codes.append(f"sz{raw_code}")

    if not sina_codes:
        return []

    url = f"https://hq.sinajs.cn/list={','.join(sina_codes)}"
    req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
    try:
        raw = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
    except Exception:
        return []

    results = []
    for line in raw.strip().split("\n"):
        if not line or "=" not in line:
            continue
        try:
            parts = line.split('="')[1].strip('";').split(",")
            if len(parts) < 4:
                continue
            full_code = line.split("=")[0].split("_")[-1]
            pure_code = full_code.replace("sh", "").replace("sz", "")
            name = parts[0]
            prev_close = float(parts[2]) if len(parts) > 2 and parts[2] else 0
            price = float(parts[3]) if parts[3] else 0
            if prev_close > 0:
                change_pct = round((price - prev_close) / prev_close * 100, 2)
            else:
                change_pct = 0.0
            results.append({
                "code": pure_code,
                "name": name,
                "price": price,
                "change_pct": change_pct,
                "pe": None,
                "_source": "新浪财经",
            })
        except (IndexError, ValueError):
            continue
    return results


# ── 腾讯财经 ──────────────────────────────────────────────────────

def _tencent_quotes(codes: List[str]) -> List[Dict]:
    """通过腾讯财经 API 获取个股实时行情。

    返回 code 为纯数字（不含 sh/sz 前缀）。
    """
    tx_codes = []
    for c in codes:
        raw_code = c.replace("sh", "").replace("sz", "")
        if raw_code.startswith(("6", "5")):
            tx_codes.append(f"sh{raw_code}")
        else:
            tx_codes.append(f"sz{raw_code}")

    if not tx_codes:
        return []

    url = f"https://qt.gtimg.cn/q={','.join(tx_codes)}"
    req = urllib.request.Request(url, headers={"Referer": "https://gu.qq.com/"})
    try:
        raw = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
    except Exception:
        return []

    results = []
    for line in raw.strip().split("\n"):
        if not line.strip() or "~" not in line:
            continue
        try:
            content = line.split('"')[1] if '"' in line else line.split("=")[1]
            parts = content.split("~")
            if len(parts) < 10:
                continue
            # 腾讯 88 字段索引:
            # [1]=名称 [2]=代码 [3]=现价 [4]=昨收
            # [32]=涨跌幅(%)  [39]=PE(TTM)  [44]=流通市值(亿) [45]=总市值(亿)
            pure_code = parts[2]
            name = parts[1]
            price = float(parts[3]) if parts[3] else 0
            change_pct = float(parts[32]) if len(parts) > 32 and parts[32] else 0.0
            pe = None
            if len(parts) > 39 and parts[39]:
                try: pe = float(parts[39])
                except (ValueError, TypeError): pass
            mc = None
            if len(parts) > 45 and parts[45]:
                try: mc = float(parts[45])
                except (ValueError, TypeError): pass
            if not mc and len(parts) > 44 and parts[44]:
                try: mc = float(parts[44])
                except (ValueError, TypeError): pass
            results.append({
                "code": pure_code, "name": name,
                "price": price, "change_pct": change_pct,
                "pe": pe if pe and pe > 0 else None,
                "market_cap_billion": mc if mc and mc > 0 else None,
                "_source": "腾讯财经",
            })
        except (IndexError, ValueError):
            continue
    return results


# ── 东方财富 ──────────────────────────────────────────────────────

def _eastmoney_sector_quotes(industry: str) -> Optional[Dict]:
    """东方财富板块指数行情（push2 API，可能被封锁）。"""
    bk = _bk_code(industry)
    if bk == "未知":
        return None
    try:
        url = (
            "https://push2.eastmoney.com/api/qt/stock/get"
            f"?secid=90.{bk}&fields=f2,f3,f4,f20,f115"
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            d = raw.get("data", {})
            if d and d.get("f2") is not None:
                return {
                    "index_price": d.get("f2", 0),
                    "index_change_pct": d.get("f3", 0),
                    "pe_median": d.get("f115", 0),
                    "market_cap_total": d.get("f20", 0) / 1e8 if d.get("f20") else 0,
                }
    except Exception as e:
        return None  # API blocked/timeout


def _eastmoney_constituents(industry: str) -> Optional[List[Dict]]:
    """东方财富板块成分股（push2 API）。"""
    bk = _bk_code(industry)
    if bk == "未知":
        return None
    try:
        url = (
            "https://push2.eastmoney.com/api/qt/clist/get"
            f"?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
            f"&fltt=2&invt=2&fid=f3&fs=b:{bk}+f:!200"
            "&fields=f12,f14,f9,f20"
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            items = raw.get("data", {}).get("diff", [])
            if items:
                return [{
                    "code": it.get("f12", ""), "name": it.get("f14", ""),
                    "pe": it.get("f9", 0) or 0,
                    "market_cap_billion": (it.get("f20", 0) or 0) / 1e8,
                    "_source": "东方财富API",
                } for it in items]
    except Exception as e:
        return None  # API blocked/timeout


# ── akshare ───────────────────────────────────────────────────────

def _akshare_constituents(industry: str) -> Optional[List[Dict]]:
    bk = _bk_code(industry)
    if bk == "未知":
        return None
    try:
        import akshare as ak
        df = ak.stock_board_concept_cons_em(symbol=bk)
        if df is not None and not df.empty:
            return [{
                "code": str(row.get("代码", row.iloc[0] if len(row) > 0 else "")),
                "name": str(row.get("名称", row.iloc[1] if len(row) > 1 else "")),
                "pe": 0.0, "market_cap_billion": 0.0, "_source": "akshare",
            } for _, row in df.head(20).iterrows()]
    except (ImportError, Exception) as e:
        return None  # API blocked/timeout


# ── baostock ───────────────────────────────────────────────────────

def _baostock_constituents(industry: str, codes: List[str],
                           skeleton: List[Dict]) -> Optional[List[Dict]]:
    """通过 baostock 获取日线最新 PE(TTM) 和收盘价，补充在线 PE 数据。

    适用于交易时段腾讯/新浪不通、但需要近期 PE 数据的场景。
    skeleton 仅提供公司名称（code → name 映射），不提供行情数据兜底。

    每只股票独立查询，单只失败不影响其他。
    日期范围缩小到 30 天以减少海外网络断连概率。
    """
    import socket

    try:
        import baostock as bs
        bs.login()
    except Exception:
        return None

    results = []
    code_to_name = {s["code"]: s.get("name", "") for s in skeleton}
    today = time.strftime("%Y-%m-%d")
    start_date = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))

    for code in codes:
        try:
            socket.setdefaulttimeout(8)
            prefix = "sh" if code.startswith(("6", "5")) else "sz"
            rs = bs.query_history_k_data_plus(
                f"{prefix}.{code}",
                "date,close,peTTM",
                start_date=start_date,
                end_date=today,
            )
            if rs.error_code != '0':
                continue

            close_val = None
            pe_val = None
            while rs.next():
                row = rs.get_row_data()
                try:
                    c = float(row[1]) if row[1] else 0
                    p = float(row[2]) if row[2] else 0
                    if p > 0:
                        close_val = c
                        pe_val = p
                except (ValueError, IndexError):
                    continue

            results.append({
                "code": code,
                "name": code_to_name.get(code, ""),
                "price": close_val,
                "change_pct": None,
                "pe": pe_val if pe_val and pe_val > 0 else None,
                "market_cap_billion": None,
                "_source": "baostock（日线PE）",
            })
        except Exception:
            continue  # 单只股票查询失败，跳过

    try:
        bs.logout()
    except Exception:
        pass

    return results if len(results) >= 3 else None


# ── 新浪概念板块成分股 ──────────────────────────────────────

# 行业 → 新浪概念板块 node ID 映射
_SINA_CONCEPT_NODE_MAP = {
    "AI算力":     "chgn_701051",  # 算力概念
    "人工智能":   "chgn_700230",  # 人工智能
    "信息技术":   "chgn_700579",  # 芯片概念
    "移动互联网": "chgn_700136",  # 5G
    "智能汽车":   "chgn_700179",  # 智能汽车
    "机器人":     "chgn_700124",  # 机器人概念
    "工业4.0":    "chgn_700210",  # 工业4.0
    "半导体":     "chgn_700458",  # 半导体
    "新能源汽车": "chgn_700410",  # 新能源车
    "新硬件":     "chgn_701218",  # 消费电子
    "消费":       "chgn_700182",  # 白酒
    "金融科技":   "chgn_700680",  # 金融科技
    "生物医药":   "chgn_730141",  # 生物医药
    "医药健康":   "chgn_700127",  # 医疗器械
    "能源金属":   "chgn_700097",  # 锂电池
}


def _is_valid_code(code: str) -> bool:
    """排除北交所 (920xxx)、新三板 (83xxx/87xxx)、退市股 (4xxx)。"""
    return not code.startswith(("920", "83", "87", "4"))


def _normalize_mcap(raw: str) -> float:
    """将新浪 API 的流通市值（万元）归一化为亿。"""
    try:
        val = float(raw) / 10000 if raw and raw != "" else 0
        return round(val, 1) if val > 0 else 0
    except (ValueError, TypeError):
        return 0


def _sina_concept_constituents(industry: str, top_n: int = None
                               ) -> Optional[List[Dict]]:
    """通过新浪概念板块 API 获取行业成分股，按流通市值排序取 Top N。

    数据字段：code, name, price, change_pct, pe, market_cap_billion

    Returns None if the API is unavailable.
    """
    if top_n is None:
        top_n = config.MAX_CONSTITUENTS
    node_id = None
    for key, nid in _SINA_CONCEPT_NODE_MAP.items():
        if key in industry or industry in key:
            node_id = nid
            break
    if not node_id:
        return None

    url = (
        "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "Market_Center.getHQNodeData"
        f"?page=1&num=80&sort=mktcap&asc=0&node={node_id}"
    )
    req = urllib.request.Request(url)
    try:
        raw = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
        data = json.loads(raw)
    except Exception:
        return None

    if not isinstance(data, list) or len(data) == 0:
        return None

    results = []
    for s in data:
        code = str(s.get("code", ""))
        if not _is_valid_code(code):
            continue
        mcap_b = _normalize_mcap(s.get("mktcap", ""))
        pe_raw = s.get("per", "")
        try:
            pe = float(pe_raw) if pe_raw and pe_raw != "" else None
        except (ValueError, TypeError):
            pe = None
        results.append({
            "code": code,
            "name": str(s.get("name", "")),
            "price": float(s.get("trade", 0) or 0),
            "change_pct": float(s.get("changepercent", 0) or 0),
            "pe": pe if pe and pe > 0 else None,
            "market_cap_billion": round(mcap_b, 1) if mcap_b > 0 else None,
            "_source": "新浪概念板块",
        })

    # 按流通市值降序排列
    results.sort(key=lambda x: x["market_cap_billion"] or 0, reverse=True)
    return results[:top_n] if len(results) >= 3 else None

"""Tests for tools/data_sources/summary.py — build_summary is pure dict→dict."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from tools.data_sources.summary import build_summary


@pytest.fixture
def minimal_package():
    return {
        "采集时间": "2026-07-12 10:00:00",
        "行业": "测试行业",
        "数据源状态": {},
    }


@pytest.fixture
def full_market_package():
    return {
        "采集时间": "2026-07-12 10:00:00",
        "行业": "AI算力",
        "数据源状态": {
            "market_data": "✅ 成功",
            "financial_data": "✅ 成功",
        },
        "market_data": {
            "fetch_timestamp": "2026-07-12 10:00:01",
            "行情": {
                "index_name": "国证算力",
                "index_price": 15228.5,
                "index_change_pct": -4.43,
                "pe_median": 53.6,
                "pe_note": "PE 中位数由 17/20 只成分股计算",
                "market_cap_total": 83000,
                "_source": "新浪指数行情 + 成分股汇总推导",
            },
            "成分股": [
                {
                    "code": "600941", "name": "中国移动", "price": 89.98,
                    "change_pct": 1.4, "pe": 14.2,
                    "market_cap_billion": 19511.0,
                },
                {
                    "code": "601138", "name": "工业富联", "price": 66.27,
                    "change_pct": -4.7, "pe": 37.2,
                    "market_cap_billion": 13151.0,
                },
            ],
        },
        "financial_data": {
            "fetch_timestamp": "2026-07-12 10:00:02",
            "source": "baostock（日线财报）",
            "指标说明": ["ROE:净资产收益率", "毛利率:毛利润/营收"],
            "公司财务": [
                {
                    "code": "600941", "name": "中国移动", "roe_pct": 2.1,
                    "gross_margin_pct": 25.4, "revenue_growth_pct": 2.3,
                    "net_profit_growth_pct": -4.2, "debt_ratio_pct": 14.0,
                    "_data_period": "2026Q1",
                },
                {
                    "code": "601138", "name": "工业富联", "roe_pct": 6.2,
                    "gross_margin_pct": 7.3, "revenue_growth_pct": 12.1,
                    "net_profit_growth_pct": 101.8, "debt_ratio_pct": 5.4,
                    "_data_period": "2026Q1",
                },
            ],
        },
        "announcement_data": {
            "fetch_timestamp": "2026-07-12 10:00:03",
            "source": "巨潮资讯网",
            "公告": [
                {
                    "date": "2026-04-23", "company": "中国移动",
                    "type": "年报", "title": "二零二五年年报",
                    "url": "http://example.com/1",
                },
            ],
        },
        "news_data": {
            "fetch_timestamp": "2026-07-12 10:00:04",
            "source": "来源: 证券日报, 财联社",
            "数量": 5,
            "新闻": [
                {
                    "date": "2026-07-10", "source": "大河财立方",
                    "title": "中国移动亮相大会", "summary": "摘要内容",
                    "url": "http://example.com/n1",
                },
            ],
        },
        "user_supplements": [
            {"类别": "会议纪要", "标题": "季度策略会", "日期": "2026-07-01",
             "来源": "某券商", "内容": "纪要正文..."},
        ],
    }


class TestBuildSummaryMinimal:
    """build_summary with minimal input — all fields present but empty."""

    def test_returns_summary_with_all_dimension_keys(self, minimal_package):
        s = build_summary(minimal_package)
        dims = s["各维度明细"]
        assert "行情" in dims
        assert "财务" in dims
        assert "公告" in dims
        assert "新闻" in dims
        assert "用户补充数据" in dims

    def test_preserves_metadata(self, minimal_package):
        s = build_summary(minimal_package)
        assert s["采集时间"] == "2026-07-12 10:00:00"
        assert s["行业"] == "测试行业"

    def test_empty_package_no_crash(self):
        s = build_summary({})
        assert s["采集时间"] == ""
        assert s["行业"] == ""
        for key in ["行情", "财务", "公告", "新闻", "用户补充数据"]:
            assert key in s["各维度明细"]


class TestMarketDataSummary:
    """build_summary market data extraction."""

    def test_market_overview_contains_index_info(self, full_market_package):
        s = build_summary(full_market_package)
        overview = s["各维度明细"]["行情"]["概览"]
        assert "国证算力" in overview
        assert "15228.5" in overview
        assert "-4.43" in overview

    def test_pe_median_line(self, full_market_package):
        s = build_summary(full_market_package)
        overview = s["各维度明细"]["行情"]["概览"]
        assert "PE中位数" in overview
        assert "53.6" in overview

    def test_market_cap_trillion_format(self, full_market_package):
        """>= 10000 亿 should show as 万亿."""
        s = build_summary(full_market_package)
        overview = s["各维度明细"]["行情"]["概览"]
        assert "8.3万亿" in overview

    def test_market_cap_billion_format(self):
        """< 10000 亿 should show as 亿."""
        pkg = {
            "market_data": {
                "fetch_timestamp": "",
                "行情": {"market_cap_total": 5000, "_source": ""},
                "成分股": [],
            },
        }
        s = build_summary(pkg)
        overview = s["各维度明细"]["行情"]["概览"]
        assert "5000亿" in overview

    def test_constituent_field_mapping(self, full_market_package):
        s = build_summary(full_market_package)
        constituents = s["各维度明细"]["行情"]["成分股"]
        assert len(constituents) == 2
        c = constituents[0]
        assert c["代码"] == "600941"
        assert c["名称"] == "中国移动"
        assert c["价格"] == 89.98
        assert c["涨跌幅(%)"] == 1.4
        assert c["PE"] == 14.2
        assert c["市值(亿)"] == 19511.0

    def test_empty_market_no_crash(self):
        pkg = {}
        s = build_summary(pkg)
        mkt = s["各维度明细"]["行情"]
        assert mkt["概览"] == "无数据"
        assert mkt["成分股"] == []


class TestFinancialDataSummary:
    def test_company_count(self, full_market_package):
        s = build_summary(full_market_package)
        assert s["各维度明细"]["财务"]["覆盖公司数"] == 2

    def test_data_period_deduplication(self, full_market_package):
        s = build_summary(full_market_package)
        period = s["各维度明细"]["财务"]["数据期间"]
        assert period == "2026Q1"

    def test_indicator_extraction(self, full_market_package):
        """Indicator names should strip explanations after :."""
        s = build_summary(full_market_package)
        indicators = s["各维度明细"]["财务"]["指标"]
        assert "ROE" in indicators
        assert "毛利率" in indicators

    def test_default_indicators_when_empty(self):
        pkg = {"financial_data": {"公司财务": []}}
        s = build_summary(pkg)
        indicators = s["各维度明细"]["财务"]["指标"]
        assert len(indicators) == 5  # default set

    def test_company_fields(self, full_market_package):
        s = build_summary(full_market_package)
        companies = s["各维度明细"]["财务"]["公司"]
        c = companies[0]
        assert c["ROE(%)"] == 2.1
        assert c["毛利率(%)"] == 25.4
        assert c["营收增速(%)"] == 2.3
        assert c["负债率(%)"] == 14.0


class TestAnnouncementSummary:
    def test_count(self, full_market_package):
        s = build_summary(full_market_package)
        assert s["各维度明细"]["公告"]["数量"] == 1

    def test_field_mapping(self, full_market_package):
        s = build_summary(full_market_package)
        a = s["各维度明细"]["公告"]["列表"][0]
        assert a["日期"] == "2026-04-23"
        assert a["公司"] == "中国移动"
        assert a["类型"] == "年报"
        assert a["标题"] == "二零二五年年报"

    def test_empty_announcements(self):
        pkg = {"announcement_data": {}}
        s = build_summary(pkg)
        assert s["各维度明细"]["公告"]["数量"] == 0
        assert s["各维度明细"]["公告"]["列表"] == []


class TestNewsSummary:
    def test_count_uses_explicit_field(self, full_market_package):
        s = build_summary(full_market_package)
        # 数量 field is explicitly 5, but only 1 news item in list
        # build_summary uses nd.get("数量", len(news_items))
        assert s["各维度明细"]["新闻"]["数量"] == 5

    def test_count_falls_back_to_list_length(self):
        pkg = {
            "news_data": {
                "source": "",
                "fetch_timestamp": "",
                "新闻": [{"date": "", "source": "", "title": "", "summary": ""}],
            },
        }
        s = build_summary(pkg)
        assert s["各维度明细"]["新闻"]["数量"] == 1

    def test_field_mapping(self, full_market_package):
        s = build_summary(full_market_package)
        n = s["各维度明细"]["新闻"]["列表"][0]
        assert n["日期"] == "2026-07-10"
        assert n["来源媒体"] == "大河财立方"
        assert n["标题"] == "中国移动亮相大会"


class TestUserSupplementsSummary:
    def test_list_format(self, full_market_package):
        s = build_summary(full_market_package)
        u = s["各维度明细"]["用户补充数据"]
        assert u["数量"] == 1
        assert u["列表"][0]["标题"] == "季度策略会"
        assert u["列表"][0]["类别"] == "会议纪要"

    def test_dict_format(self):
        pkg = {
            "user_supplements": {
                "会议纪要": [{"标题": "纪要1", "日期": "", "来源": "", "内容": ""}],
                "调研笔记": [],
            },
        }
        s = build_summary(pkg)
        u = s["各维度明细"]["用户补充数据"]
        assert u["数量"] == 1

    def test_empty_user_data(self):
        s = build_summary({})
        assert s["各维度明细"]["用户补充数据"]["数量"] == 0

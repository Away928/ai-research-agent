"""No-network regression: financial metrics can originate from different quarters."""

from tools.data_sources.financial_data import FinancialDataSource
from tools.data_sources import DataSourceManager


PROFIT_FIELDS = [
    "code", "pubDate", "statDate", "roeAvg", "npMargin", "gpMargin",
    "netProfit", "epsTTM", "MBRevenue", "totalShare", "liqaShare",
]
GROWTH_FIELDS = [
    "code", "pubDate", "statDate", "YOYEquity", "YOYAsset",
    "YOYNI", "YOYEPSBasic", "YOYPNI",
]
BALANCE_FIELDS = [
    "code", "pubDate", "statDate", "currentRatio", "quickRatio",
    "cashRatio", "YOYLiability", "liabilityToAsset", "assetToEquity",
]


class Result:
    error_code = "0"

    def __init__(self, fields, record):
        self.fields = fields
        self.row = [record.get(f, "") for f in fields] if record else None
        self.seen = False

    def next(self):
        if self.row is None or self.seen:
            return False
        self.seen = True
        return True

    def get_row_data(self):
        return self.row


def record(year, quarter, **fields):
    stat_date = f"{year}-{quarter * 3:02d}-" + (
        "31" if quarter in (1, 4) else "30"
    )
    return {"code": "sz.000001", "pubDate": "2026-04-20" if year < 2026 else "2026-09-05",
            "statDate": stat_date, **fields}


class MixedQuarters:
    def query_profit_data(self, **kw):
        period = kw["year"], kw["quarter"]
        rows = {
            (2026, 2): record(2026, 2, roeAvg="0.08", gpMargin="0.30", MBRevenue="112"),
            (2025, 2): record(2025, 2, MBRevenue="100"),
        }
        return Result(PROFIT_FIELDS, rows.get(period))

    def query_growth_data(self, **kw):
        period = kw["year"], kw["quarter"]
        row = record(2026, 1, YOYNI="0.05") if period == (2026, 1) else None
        return Result(GROWTH_FIELDS, row)

    def query_balance_data(self, **kw):
        period = kw["year"], kw["quarter"]
        row = record(2025, 4, liabilityToAsset="0.45") if period == (2025, 4) else None
        return Result(BALANCE_FIELDS, row)


def test_independent_quarter_per_financial_metric():
    source = FinancialDataSource()
    source._get_latest_quarters = lambda: [(2026, 2), (2026, 1), (2025, 4), (2025, 2)]
    row = source._query_stock_financials(MixedQuarters(), "000001", "合成公司")
    assert row["roe_pct"] == 8.0
    assert row["revenue_growth_pct"] == 12.0
    assert row["net_profit_growth_pct"] == 5.0
    assert row["debt_ratio_pct"] == 45.0
    assert row["_metric_periods"] == {
        "roe_pct": "2026Q2",
        "gross_margin_pct": "2026Q2",
        "revenue_growth_pct": "2026Q2",
        "net_profit_growth_pct": "2026Q1",
        "debt_ratio_pct": "2025Q4",
    }
    assert row["_data_period"] is None
    assert row["_metric_methods"]["revenue_growth_pct"].startswith("profit.MBRevenue")
    assert row["_metric_methods"]["debt_ratio_pct"] == "balance.liabilityToAsset"
    assert row["_metric_methods"]["net_profit_growth_pct"] == "growth.YOYNI"


def test_company_data_keeps_metric_dates_and_source_without_filling_gaps():
    market = {"成分股": [{"code": "000001", "name": "合成公司", "pe": 13.2}]}
    financial = {"公司财务": [{
        "code": "000001", "roe_pct": 8.0, "revenue_growth_pct": 12.0,
        "_source": "baostock（财务报表）",
        "_metric_periods": {"roe_pct": "2026Q2", "revenue_growth_pct": "2026Q1"},
    }]}
    row, = DataSourceManager.build_company_data(market, financial)
    assert row["财务数据来源"] == "baostock（财务报表）"
    assert row["财务指标报告期"]["ROE(%)"] == "2026Q2"
    assert row["财务指标报告期"]["营收增速(%)"] == "2026Q1"
    assert row["财务指标报告期"]["负债率(%)"] is None


def test_report_appendix_uses_record_ids_and_actual_metric_dates():
    from tools.report_formatter import ReportFormatter
    context = {"raw_data": {"financial_data": {"公司财务": [{
        "code": "000001", "name": "合成公司", "_source": "baostock",
        "roe_pct": 8.0, "revenue_growth_pct": 12.0,
        "debt_ratio_pct": 45.0,
        "_metric_periods": {"roe_pct": "2026Q2", "revenue_growth_pct": "2026Q1"},
    }]}}}
    report = ReportFormatter().format_report(
        "测试正文（没有事实核验）", "合成行业",
        [{"stage": "offline", "duration_seconds": 0.1, "notes": "测试"}],
        context,
    )
    assert "| `FIN-000001-roe_pct` | 000001 | 合成公司 | ROE(%) | 8.0 | 2026Q2" in report
    assert "| `FIN-000001-revenue_growth_pct` | 000001 | 合成公司 | 营收增速(%) | 12.0 | 2026Q1" in report
    assert "| `FIN-000001-debt_ratio_pct` | 000001 | 合成公司 | 负债率(%) | 45.0 | 未知" in report
    assert "不能证明供应商数字正确" in report
    assert "### F. 作者" in report


def test_summary_does_not_hide_cross_quarter_company_metrics():
    from tools.data_sources.summary import build_summary
    result = build_summary({"financial_data": {"公司财务": [{
        "code": "000001", "name": "合成公司", "_data_period": None,
        "roe_pct": 8.0, "revenue_growth_pct": 12.0,
        "_metric_periods": {"roe_pct": "2026Q2", "revenue_growth_pct": "2026Q1"},
    }]}})["各维度明细"]["财务"]
    assert result["数据期间"] == "2026Q1 / 2026Q2"
    assert result["公司"][0]["数据期间"] == "2026Q1 / 2026Q2"
    assert result["公司"][0]["指标报告期"]["roe_pct"] == "2026Q2"


class IncompleteRecentQuarters:
    """Realistic field-name rows requiring distinct reporting periods."""

    def query_profit_data(self, **kw):
        period = kw["year"], kw["quarter"]
        rows = {
            (2026, 2): record(2026, 2, roeAvg="0.08", MBRevenue="100"),
            (2026, 1): record(2026, 1, roeAvg="0.04", gpMargin="0.30"),
            (2025, 2): record(2025, 2, MBRevenue="100"),
        }
        return Result(PROFIT_FIELDS, rows.get(period))

    def query_growth_data(self, **kw):
        period = kw["year"], kw["quarter"]
        rows = {
            (2026, 2): record(2026, 2, YOYEquity="0.99"),  # NOT net profit growth
            (2026, 1): record(2026, 1, YOYNI="-0.05"),
        }
        return Result(GROWTH_FIELDS, rows.get(period))

    def query_balance_data(self, **kw):
        period = kw["year"], kw["quarter"]
        row = record(2026, 2, liabilityToAsset="0.40") if period == (2026, 2) else None
        return Result(BALANCE_FIELDS, row)


def test_missing_field_backfills_independently_but_recent_value_stays():
    source = FinancialDataSource()
    source._get_latest_quarters = lambda: [(2026, 2), (2026, 1), (2025, 2)]
    row = source._query_stock_financials(
        IncompleteRecentQuarters(), "000001", "合成公司")
    assert row["roe_pct"] == 8.0
    assert row["gross_margin_pct"] == 30.0
    assert row["revenue_growth_pct"] == 0.0  # 100 / 100 -> 0% is valid
    assert row["net_profit_growth_pct"] == -5.0
    assert row["debt_ratio_pct"] == 40.0
    assert row["_metric_periods"] == {
        "roe_pct": "2026Q2", "gross_margin_pct": "2026Q1",
        "revenue_growth_pct": "2026Q2", "net_profit_growth_pct": "2026Q1",
        "debt_ratio_pct": "2026Q2",
    }
    assert row["_data_period"] is None


def test_quarters_sorted_newest_first_and_disclosure_eligible():
    from datetime import datetime
    get = FinancialDataSource._get_latest_quarters
    january = get(datetime(2026, 1, 15))
    assert january[0] == (2025, 3)
    assert (2025, 4) not in january
    assert (2026, 1) not in january

    april = get(datetime(2026, 4, 30))
    assert april[0] == (2025, 3)
    may = get(datetime(2026, 5, 1))
    assert may[:2] == [(2026, 1), (2025, 4)]

    october = get(datetime(2026, 10, 24))
    assert october[:3] == [(2026, 2), (2026, 1), (2025, 4)]
    assert (2026, 3) not in october

    november = get(datetime(2026, 11, 1))
    assert november[:3] == [(2026, 3), (2026, 2), (2026, 1)]
    assert november == sorted(set(november), reverse=True)


def test_zero_percentage_and_nonfinite_are_handled_safely():
    from tools.data_sources.financial_data import _pct
    assert _pct("0") == 0.0
    assert _pct(0) == 0.0
    assert _pct("-0.05") == -5.0
    assert _pct("") is None
    assert _pct("NaN") is None
    assert _pct("inf") is None
    assert _pct("-inf") is None


def test_financial_cache_requires_exact_industry_not_substring(monkeypatch, tmp_path):
    import json
    import time
    import tools.data_sources.financial_data as module
    path = tmp_path / "financial.json"
    path.write_text(json.dumps({
        "AI": {"_schema_version": 2, "_cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
               "data": [{"code": "111111", "roe_pct": 8}]},
        "AI算力": {"_schema_version": 2, "_cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "data": [{"code": "222222", "roe_pct": 9},
                          {"code": "333333", "roe_pct": 7}]},
    }), encoding="utf-8")
    monkeypatch.setattr(module, "_FINANCIAL_CACHE_FILE", path)
    source = FinancialDataSource()
    assert source._from_cache("AI算力", [{"code": "222222"}]) == [
        {"code": "222222", "roe_pct": 9, "_source": "缓存"}
    ]
    assert source._from_cache("AI新板块") is None
    assert source._from_cache("AI算力", [{"code": "444444"}]) is None
    assert source._from_cache("AI")[0]["code"] == "111111"
    original = json.loads(path.read_text(encoding="utf-8"))
    assert "_source" not in original["AI算力"]["data"][0]


def test_financial_cache_exposes_expired_snapshot(monkeypatch, tmp_path):
    import json
    from datetime import datetime, timedelta
    import tools.data_sources.financial_data as module
    path = tmp_path / "financial.json"
    old = (datetime.now() - timedelta(days=11)).strftime("%Y-%m-%d %H:%M:%S")
    path.write_text(json.dumps({
        "合成行业": {"_schema_version": 2, "_cached_at": old, "data": [{"code": "000001", "roe_pct": 8}]}
    }), encoding="utf-8")
    monkeypatch.setattr(module, "_FINANCIAL_CACHE_FILE", path)
    result = FinancialDataSource()._from_cache("合成行业")
    assert result[0]["_source"].startswith("缓存(过期")



def test_pre_fix_cache_is_rejected_even_if_recent(monkeypatch, tmp_path):
    import json
    import time
    import tools.data_sources.financial_data as module
    path = tmp_path / "financial.json"
    path.write_text(json.dumps({
        "合成行业": {
            "_cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": [{"code": "000001", "revenue_growth_pct": 25.0,
                      "debt_ratio_pct": 500.0}],
        }
    }), encoding="utf-8")
    monkeypatch.setattr(module, "_FINANCIAL_CACHE_FILE", path)
    source = FinancialDataSource()
    assert source._from_cache("合成行业") is None

    source._save_to_cache("合成行业", [{
        "code": "000001", "roe_pct": 8.0,
        "_source": "baostock（财务接口）",
    }])
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["合成行业"]["_schema_version"] == 2
    assert source._from_cache("合成行业")[0]["roe_pct"] == 8.0


def test_provider_field_order_does_not_change_meaning():
    class ReverseProvider(MixedQuarters):
        def query_profit_data(self, **kw):
            rs = super().query_profit_data(**kw)
            if rs.row is not None:
                rs.fields = list(reversed(rs.fields))
                rs.row = list(reversed(rs.row))
            return rs

        def query_growth_data(self, **kw):
            rs = super().query_growth_data(**kw)
            if rs.row is not None:
                rs.fields = list(reversed(rs.fields))
                rs.row = list(reversed(rs.row))
            return rs

        def query_balance_data(self, **kw):
            rs = super().query_balance_data(**kw)
            if rs.row is not None:
                rs.fields = list(reversed(rs.fields))
                rs.row = list(reversed(rs.row))
            return rs

    source = FinancialDataSource()
    source._get_latest_quarters = lambda: [
        (2026, 2), (2026, 1), (2025, 4), (2025, 2)
    ]
    row = source._query_stock_financials(ReverseProvider(), "000001", "合成公司")
    assert row["roe_pct"] == 8.0
    assert row["gross_margin_pct"] == 30.0
    assert row["revenue_growth_pct"] == 12.0
    assert row["net_profit_growth_pct"] == 5.0
    assert row["debt_ratio_pct"] == 45.0


def test_growth_equity_not_misclassified_as_revenue_or_net_income():
    class EquityOnly:
        def query_profit_data(self, **kwargs):
            return Result(PROFIT_FIELDS, None)
        def query_growth_data(self, **kwargs):
            return Result(GROWTH_FIELDS, record(2026, 2, YOYEquity="0.25"))
        def query_balance_data(self, **kwargs):
            return Result(BALANCE_FIELDS, record(2026, 2, liabilityToAsset="0.35"))
    source = FinancialDataSource()
    source._get_latest_quarters = lambda: [(2026, 2)]
    row = source._query_stock_financials(EquityOnly(), "000001", "合成公司")
    assert row["revenue_growth_pct"] is None
    assert row["net_profit_growth_pct"] is None
    assert row["debt_ratio_pct"] == 35.0


def test_broken_schema_and_wrong_stat_date_are_skipped():
    class BadRows:
        def query_profit_data(self, **kwargs):
            return Result(PROFIT_FIELDS, record(2026, 1, roeAvg="0.9"))
        def query_growth_data(self, **kwargs):
            return Result(["code", "pubDate", "statDate", "YOYEquity"],
                          record(2026, 2, YOYEquity="0.77"))
        def query_balance_data(self, **kwargs):
            return Result(BALANCE_FIELDS, record(2026, 1, liabilityToAsset="0.99"))
    source = FinancialDataSource()
    source._get_latest_quarters = lambda: [(2026, 2)]
    assert source._query_stock_financials(BadRows(), "000001", "合成公司") is None



def test_future_disclosure_cannot_enter_current_research():
    class FutureRecord:
        def query_profit_data(self, **kw):
            return Result(PROFIT_FIELDS, {
                **record(2026, 2, roeAvg="0.33", gpMargin="0.10"),
                "pubDate": "2099-01-01",
            })
        def query_growth_data(self, **kw):
            return Result(GROWTH_FIELDS, None)
        def query_balance_data(self, **kw):
            return Result(BALANCE_FIELDS, None)
    source = FinancialDataSource()
    source._get_latest_quarters = lambda: [(2026, 2)]
    assert source._query_stock_financials(FutureRecord(), "000001", "合成公司") is None


def test_revenue_yoy_requires_nonzero_comparable_same_quarter_baseline():
    class NoValidDenominator:
        def query_profit_data(self, **kw):
            period = kw["year"], kw["quarter"]
            rows = {
                (2026, 2): record(2026, 2, roeAvg="0.1", MBRevenue="100"),
                (2025, 2): record(2025, 2, MBRevenue="0"),
            }
            return Result(PROFIT_FIELDS, rows.get(period))
        def query_growth_data(self, **kw):
            return Result(GROWTH_FIELDS, None)
        def query_balance_data(self, **kw):
            return Result(BALANCE_FIELDS, None)
    source = FinancialDataSource()
    source._get_latest_quarters = lambda: [(2026, 2), (2025, 2)]
    row = source._query_stock_financials(NoValidDenominator(), "000001", "合成公司")
    assert row["roe_pct"] == 10.0
    assert row["revenue_growth_pct"] is None
    assert "revenue_growth_pct" not in row["_metric_periods"]


def test_financial_record_provenance_reaches_company_data_and_appendix():
    from tools.report_formatter import ReportFormatter
    financial = {"公司财务": [{
        "code": "000001", "name": "合成公司",
        "roe_pct": 8.0, "revenue_growth_pct": 12.0,
        "_metric_periods": {"roe_pct": "2026Q2", "revenue_growth_pct": "2026Q2"},
        "_metric_publication_dates": {
            "roe_pct": "2026-09-05",
            "revenue_growth_pct": "2026-09-05",
        },
        "_metric_methods": {
            "roe_pct": "profit.roeAvg",
            "revenue_growth_pct": "profit.MBRevenue 同季同比 (2026Q2/2025Q2-1)",
        },
        "_source": "合成接口",
    }]}
    market = {"成分股": [{"code": "000001", "name": "合成公司"}]}
    company, = DataSourceManager.build_company_data(market, financial)
    assert company["财务指标披露日"]["roe_pct"] == "2026-09-05"
    assert "MBRevenue" in company["财务指标计算口径"]["revenue_growth_pct"]
    report = ReportFormatter._financial_evidence({"raw_data": {"financial_data": financial}})
    assert "2026-09-05" in report
    assert "profit.roeAvg" in report
    assert "2026Q2/2025Q2-1" in report



def test_baostock_login_failure_does_not_change_process_socket_timeout(
        monkeypatch):
    import socket
    import sys
    from types import SimpleNamespace
    fake = SimpleNamespace(
        login=lambda: SimpleNamespace(error_code="10002007"),
        logout=lambda: (_ for _ in ()).throw(
            AssertionError("No session to log out")
        ),
    )
    monkeypatch.setitem(sys.modules, "baostock", fake)
    before = socket.getdefaulttimeout()
    source = FinancialDataSource()
    assert source._from_baostock(
        "合成行业", constituents=[{"code": "000001", "name": "合成公司"}]
    ) is None
    assert socket.getdefaulttimeout() == before


def test_baostock_success_restores_timeout_and_logs_out(monkeypatch):
    import socket
    import sys
    from types import SimpleNamespace
    state = {"login": 0, "logout": 0, "seen_timeout": None}
    def login():
        state["login"] += 1
        return SimpleNamespace(error_code="0")
    def logout():
        state["logout"] += 1
    fake = SimpleNamespace(login=login, logout=logout)
    monkeypatch.setitem(sys.modules, "baostock", fake)
    source = FinancialDataSource()
    def query(_backend, code, name):
        state["seen_timeout"] = socket.getdefaulttimeout()
        return {"code": code, "name": name, "roe_pct": 8.0}
    monkeypatch.setattr(source, "_query_stock_financials", query)
    monkeypatch.setattr(source, "_save_to_cache", lambda *args: None)
    before = socket.getdefaulttimeout()
    results = source._from_baostock(
        "合成行业", constituents=[{"code": "000001", "name": "合成公司"}]
    )
    assert results[0]["roe_pct"] == 8.0
    assert state == {"login": 1, "logout": 1, "seen_timeout": 10}
    assert socket.getdefaulttimeout() == before

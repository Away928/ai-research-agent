from tools.data_sources.provenance import inspect_provenance


def test_missing_source_and_observation_date_are_flagged():
    result = inspect_provenance({"market_data": {"source": "无可用数据"}})
    assert result["market_data"]["needs_source_review"]
    assert result["market_data"]["needs_date_review"]
    assert result["financial_data"]["needs_source_review"]


def test_fetch_time_not_mistaken_for_market_observation_time():
    result = inspect_provenance({"market_data": {
        "source": "新浪", "fetch_timestamp": "2026-10-24 12:00:00"
    }})["market_data"]
    assert result["source_identified"]
    assert result["data_as_of"] is None
    assert result["needs_date_review"]


def test_explicit_data_date_preserved_without_verification_claim():
    result = inspect_provenance({"news_data": {
        "source": "新闻源", "data_as_of": "2026-10-23"
    }})["news_data"]
    assert result["data_as_of"] == "2026-10-23"
    assert not result["needs_date_review"]


def test_mixed_financial_periods_are_not_collapsed_into_single_date():
    record = inspect_provenance({"financial_data": {
        "source": "baostock",
        "公司财务": [
            {"code": "000001", "_data_period": "2026Q1"},
            {"code": "000002", "_data_period": "2025Q4"},
            {"code": "000003", "_data_period": None},
        ],
    }})["financial_data"]
    assert record["observed_dates_or_periods"] == ["2025Q4", "2026Q1"]
    assert record["dated_record_count"] == 2
    assert record["needs_date_review"]
    assert record["data_as_of"] is None


def test_news_dates_are_inventoried_without_inferred_freshness():
    record = inspect_provenance({"news_data": {
        "source": "AKShare",
        "新闻": [{"date": "2026-10-20"}, {"date": "2026-10-23"}],
    }})["news_data"]
    assert record["observed_dates_or_periods"] == ["2026-10-20", "2026-10-23"]
    assert not record["needs_date_review"]
    assert record["data_as_of"] is None


def test_complete_field_level_periods_can_pass_date_coverage_check():
    row = inspect_provenance({"financial_data": {
        "source": "baostock",
        "公司财务": [{
            "code": "000001", "roe_pct": 8.0, "revenue_growth_pct": 12.0,
            "_data_period": None,
            "_metric_periods": {"roe_pct": "2026Q2", "revenue_growth_pct": "2026Q1"},
        }],
    }})["financial_data"]
    assert row["observed_dates_or_periods"] == ["2026Q1", "2026Q2"]
    assert row["dated_record_count"] == 1
    assert row["dated_metric_count"] == 2
    assert row["missing_metric_period_count"] == 0
    assert not row["needs_date_review"]


def test_missing_metric_period_flagged_even_when_other_metrics_are_dated():
    row = inspect_provenance({"financial_data": {
        "source": "baostock",
        "公司财务": [{
            "code": "000001", "roe_pct": 8.0, "debt_ratio_pct": 45.0,
            "_metric_periods": {"roe_pct": "2026Q2"},
        }],
    }})["financial_data"]
    assert row["missing_metric_period_count"] == 1
    assert row["needs_date_review"]


def test_explicit_no_data_status_overrides_nonempty_source_envelope():
    inventory = inspect_provenance({
        "数据源状态": {"market_data": "⚠️ 无有效数据"},
        "market_data": {
            "source": "行情:无可用数据源 成分股:unknown",
            "行情": {"index_price": None},
            "成分股": [],
        },
    })
    assert not inventory["market_data"]["source_identified"]
    assert inventory["market_data"]["needs_source_review"]

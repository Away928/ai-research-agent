"""Sources returning empty envelopes are not successful observations."""

from tools.data_sources import DataSourceManager


def test_empty_dicts_not_mislabeled_success():
    manager = DataSourceManager()
    assert not manager._has_payload("market_data", {
        "行情": {"index_price": None, "pe_median": None}, "成分股": []
    })
    assert not manager._has_payload("financial_data", {
        "公司财务": [{"code": "X", "roe_pct": None}]
    })
    assert not manager._has_payload("announcement_data", {
        "公告": [], "研报": []
    })
    assert not manager._has_payload("news_data", {"新闻": []})


def test_actual_observations_count_and_valid_zero_not_missing():
    manager = DataSourceManager()
    assert manager._has_payload("market_data", {
        "行情": {"index_change_pct": 0.0}, "成分股": []
    })
    assert manager._has_payload("financial_data", {
        "公司财务": [{"roe_pct": 0.0}]
    })
    assert manager._has_payload("announcement_data", {"公告": [{"title": "synthetic"}]})
    assert manager._has_payload("news_data", {"新闻": [{"title": "synthetic"}]})


def test_expired_cache_returns_warning_even_with_records():
    manager = DataSourceManager()
    assert manager._payload_status({
        "source": "缓存(过期7天+)", "公司财务": [{"roe_pct": 9.0}]
    }).startswith("⚠️")
    assert manager._payload_status({
        "source": "baostock", "公司财务": [
            {"roe_pct": 9.0, "_source": "缓存(过期7天+)"}
        ]
    }).startswith("⚠️")
    assert manager._payload_status({
        "source": "baostock", "公司财务": [
            {"roe_pct": 9.0, "_source": "baostock"}
        ]
    }) == "✅ 成功"


def test_manager_records_empty_sources_as_no_data(monkeypatch):
    manager = DataSourceManager()
    monkeypatch.setattr(manager._market_source, "_fetch_constituents", lambda _: [])
    monkeypatch.setattr(manager._market_source, "_fetch_quotes",
                        lambda *_: {"index_price": None,
                                    "pe_median": None, "_source": "无可用数据源"})

    class EmptySource:
        def __init__(self, data):
            self.data = data

        def fetch(self, *args, **kwargs):
            return self.data

    outputs = (
        {"公司财务": [], "source": "无数据"},
        {"公告": [], "研报": [], "source": "无可用数据源"},
        {"新闻": [], "source": "无可用数据源"},
    )
    for index, source_data in zip((1, 2, 3), outputs):
        label, _ = manager._sources[index]
        manager._sources[index] = (label, EmptySource(source_data))

    result = manager.gather("合成空数据行业")
    for key in ("market_data", "financial_data", "announcement_data", "news_data"):
        assert result["数据源状态"][key] == "⚠️ 无有效数据"

"""Avoid duplicate constituent API calls and mixed-session datasets."""

from tools.data_sources import DataSourceManager
from tools.data_sources.market_data import MarketDataSource


class StubStage:
    def __init__(self):
        self.seen = []

    def fetch(self, industry, *, constituents):
        self.seen.append(constituents)
        return {"行业": industry, "source": "合成来源", "items": []}


def test_same_constituent_snapshot_used_across_sources(monkeypatch):
    manager = DataSourceManager()
    calls = []
    stage_instances = [StubStage(), StubStage(), StubStage()]
    def get_constituents(industry):
        calls.append(industry)
        return [{"code": "SYN01", "name": "合成甲", "pe": 12.0,
                 "market_cap_billion": 10.0, "_source": "SYNTHETIC"}]
    monkeypatch.setattr(manager._market_source, "_fetch_constituents", get_constituents)
    monkeypatch.setattr(manager._market_source, "_fetch_quotes",
                        lambda industry, constituents: {"_source": "合成指数",
                                                         "pe_median": 12.0})
    for i, stub in enumerate(stage_instances, start=1):
        name, _ = manager._sources[i]
        manager._sources[i] = (name, stub)
    packet = manager.gather("合成行业")
    market = packet["market_data"]
    assert calls == ["合成行业"]
    assert market["成分股"] and market["成分股"][0]["code"] == "SYN01"
    assert all(stub.seen[0] is market["成分股"] for stub in stage_instances)


def test_new_gather_fetches_fresh_snapshot(monkeypatch):
    manager = DataSourceManager()
    counter = []
    def get_constituents(_):
        counter.append(1)
        return [{"code": f"SYN{len(counter)}", "pe": 12.0,
                 "market_cap_billion": 1.0, "_source": "SYNTHETIC"}]
    monkeypatch.setattr(manager._market_source, "_fetch_constituents", get_constituents)
    monkeypatch.setattr(manager._market_source, "_fetch_quotes",
                        lambda *_: {"_source": "SYNTHETIC"})
    for i in (1, 2, 3):
        key, _ = manager._sources[i]
        manager._sources[i] = (key, StubStage())
    first = manager.gather("合成行业")
    second = manager.gather("合成行业")
    assert first["market_data"]["成分股"][0]["code"] == "SYN1"
    assert second["market_data"]["成分股"][0]["code"] == "SYN2"
    assert len(counter) == 2


def test_direct_market_fetch_still_fetches_independently(monkeypatch):
    source = MarketDataSource()
    call = []
    def get_constituents(_):
        call.append(1)
        return [{"code": "SYN01", "_source": "SYNTHETIC"}]
    monkeypatch.setattr(source, "_fetch_constituents", get_constituents)
    monkeypatch.setattr(source, "_fetch_quotes",
                        lambda *_: {"_source": "SYNTHETIC"})
    result = source.fetch("合成行业")
    assert len(call) == 1
    assert result["成分股"][0]["code"] == "SYN01"

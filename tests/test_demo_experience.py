"""Demo-ready MVP: stable, offline, clearly fictional artifact."""

from tools.demo_experience import SYNTHETIC_FIXTURE, build_demo


def test_demo_has_four_complete_stages_and_downloadable_markdown():
    demo = build_demo()
    assert len(demo["sections"]) == 4
    assert list(demo["sections"]) == [
        "data_collection", "industry_overview",
        "company_deep_dive", "investment_thesis",
    ]
    assert demo["total_market_cap"] == 255.0
    assert demo["average_roe"] == 6.5
    assert demo["average_growth"] is None
    assert not demo["growth_comparable"]
    assert demo["roe_comparable"]
    assert "不计算跨季度平均增长率" in demo["report"]
    report = demo["report"]
    assert report.startswith("# 🧪")
    assert "纯合成示例" in report
    assert "未连接行情或财务接口" in report
    assert "未调用大模型" in report
    assert "### D. 采集财务数字对照" in report
    assert "采集数值匹配 2 条，需复核 0 条" in report
    assert len(report) > 3000
    assert "Red Team" in report
    assert "虚构" in report


def test_demo_does_not_change_source_fixture_or_write_generated_reports(tmp_path, monkeypatch):
    before = SYNTHETIC_FIXTURE.read_bytes()
    demo1 = build_demo()
    demo1["package"]["financial_data"]["公司财务"][0]["roe_pct"] = 999
    demo2 = build_demo()
    assert demo2["package"]["financial_data"]["公司财务"][0]["roe_pct"] == 8.0
    assert SYNTHETIC_FIXTURE.read_bytes() == before
    assert demo2["package"]["数据源状态"]["user_supplements"] == "— 无用户补充数据"
    assert demo2["sections"] == demo1["sections"]



def test_streamlit_demo_styles_do_not_depend_on_remote_font_cdn():
    from ui.styles import CUSTOM_CSS
    assert "fonts.googleapis.com" not in CUSTOM_CSS
    assert "@import url(" not in CUSTOM_CSS

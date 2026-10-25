"""Primary disclosure benchmarks are verified separately from provider fields.

No network, no LLM: explicit 2025 H1 filing figures (SSE) and arithmetic
assertions. This does NOT assert the baostock values agree with the filing.
"""

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

FIXTURE = Path(__file__).parents[2] / "fixtures" / "primary_filing_600519_2025h1.json"


def official():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def pct_ratio(numerator, denominator):
    return (Decimal(numerator) / Decimal(denominator) * 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def test_official_filing_source_is_labeled_as_primary_and_no_provider_agreement_claim():
    fixture = official()
    assert fixture["stock_code"] == "600519"
    assert fixture["period"] == "2025Q2"
    assert fixture["source"]["publisher"] == "上海证券交易所"
    assert fixture["source"]["url"].startswith("https://big5.sse.com.cn/")
    assert fixture["comparison_status"] == (
        "official_formula_benchmark_only_provider_not_verified"
    )
    assert "NOT independently matched" in fixture["source"]["verification_scope"]


def test_official_operating_revenue_and_shareholder_profit_yoy():
    fixture = official()
    n = fixture["numbers_cny"]
    for prefix, current, prior in (
        ("operating_revenue_yoy_h1", "operating_revenue_h1_2025",
         "operating_revenue_h1_2024"),
        ("attributable_net_profit_yoy_h1",
         "attributable_net_profit_h1_2025", "attributable_net_profit_h1_2024"),
    ):
        derived = pct_ratio(
            Decimal(n[current]) - Decimal(n[prior]), n[prior]
        )
        assert derived == Decimal(fixture["derived_percent_expected"][prefix])
        assert derived == Decimal(fixture["reported_percent"][prefix])


def test_official_gross_margin_and_total_liabilities_to_assets():
    fixture = official()
    n = fixture["numbers_cny"]
    gross_margin = pct_ratio(
        Decimal(n["operating_revenue_h1_2025"]) -
        Decimal(n["cost_of_sales_h1_2025"]),
        n["operating_revenue_h1_2025"],
    )
    leverage = pct_ratio(
        n["total_liabilities_2025_06_30"], n["total_assets_2025_06_30"]
    )
    assert gross_margin == Decimal(
        fixture["derived_percent_expected"]["gross_margin_on_operating_revenue_h1"]
    )
    assert leverage == Decimal(
        fixture["derived_percent_expected"]["total_liabilities_to_assets_2025_06_30"]
    )


def test_source_definition_boundaries_prevent_silent_metric_equivalence():
    fixture = official()
    non_equivalent = fixture["non_equivalence"]
    assert "profit.MBRevenue" in non_equivalent
    assert "growth.YOYNI" in non_equivalent
    assert "profit.roeAvg" in non_equivalent
    assert "profit.gpMargin" in non_equivalent
    assert "cannot be assumed equal" in non_equivalent["profit.MBRevenue"]
    assert Decimal(fixture["reported_percent"]["weighted_average_roe_h1"]) == Decimal("17.89")



def test_provider_comparison_can_detect_leverage_match_without_certifying_other_metrics():
    from tools.data_sources.provenance import compare_filing_benchmark
    example = {
        "code": "600519",
        "roe_pct": 17.89,
        "gross_margin_pct": 91.30,
        "revenue_growth_pct": 9.10,
        "net_profit_growth_pct": 8.89,
        "debt_ratio_pct": 14.75,
        "_metric_periods": {key: "2025Q2" for key in (
            "roe_pct", "gross_margin_pct", "revenue_growth_pct",
            "net_profit_growth_pct", "debt_ratio_pct"
        )},
        "_metric_methods": {"debt_ratio_pct": "balance.liabilityToAsset"},
    }
    result = compare_filing_benchmark(example, official())
    assert result["scope"] == "provider_snapshot_arithmetic_only_not_fact_certification"
    assert result["checks"]["debt_ratio_pct"]["status"] == "snapshot_value_match"
    assert all(
        result["checks"][metric]["status"] == "definition_not_yet_verified"
        for metric in ("roe_pct", "gross_margin_pct", "revenue_growth_pct",
                       "net_profit_growth_pct")
    )


def test_provider_comparison_flags_wrong_company_period_and_field_value():
    from tools.data_sources.provenance import compare_filing_benchmark
    record = {
        "code": "600519", "debt_ratio_pct": 16.2,
        "_metric_periods": {"debt_ratio_pct": "2025Q2"},
        "_metric_methods": {"debt_ratio_pct": "balance.liabilityToAsset"},
    }
    result = compare_filing_benchmark(record, official())
    assert result["checks"]["debt_ratio_pct"]["status"] == "snapshot_value_mismatch"
    record["_metric_periods"]["debt_ratio_pct"] = "2025Q1"
    assert compare_filing_benchmark(record, official())["checks"][
        "debt_ratio_pct"]["status"] == "period_mismatch"
    record["code"] = "000001"
    assert compare_filing_benchmark(record, official())["checks"][
        "debt_ratio_pct"]["status"] == "company_mismatch"


def test_provider_comparison_rejects_wrong_method_missing_or_invalid_values():
    from tools.data_sources.provenance import compare_filing_benchmark
    from pytest import raises
    record = {
        "code": "600519", "debt_ratio_pct": 14.75,
        "_metric_periods": {"debt_ratio_pct": "2025Q2"},
        "_metric_methods": {"debt_ratio_pct": "dupont.unknown"},
    }
    assert compare_filing_benchmark(record, official())["checks"][
        "debt_ratio_pct"]["status"] == "method_mismatch"
    record["_metric_methods"]["debt_ratio_pct"] = "balance.liabilityToAsset"
    record["debt_ratio_pct"] = None
    assert compare_filing_benchmark(record, official())["checks"][
        "debt_ratio_pct"]["status"] == "invalid_number"
    with raises(ValueError):
        compare_filing_benchmark(record, official(), "NaN")

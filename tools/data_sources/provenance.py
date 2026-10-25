"""Conservative provenance inventory for a collected research data package.

Presence of a source label is not verification of underlying facts.
Do not fabricate observation dates or infer freshness from collection time.
"""

SOURCE_KEYS = ("market_data", "financial_data", "announcement_data", "news_data")


def inspect_provenance(package: dict) -> dict:
    """Summarize source-label and timestamp evidence without claiming fact validity."""
    inventory = {}
    for key in SOURCE_KEYS:
        data = package.get(key)
        label = data.get("source") if isinstance(data, dict) else None
        label = label.strip() if isinstance(label, str) else ""
        usable = bool(label) and label not in ("不可用", "无数据", "无可用数据", "无可用数据源")
        status = (package.get("数据源状态") or {}).get(key, "")
        # A nonempty envelope/source label must never override an explicit
        # collector result indicating that no usable observations were found.
        if isinstance(status, str) and (
            status.startswith("❌") or "无有效数据" in status or "无数据" in status
        ):
            usable = False
        observed = data.get("data_as_of") if isinstance(data, dict) else None
        # Record distinct observation periods/dates without collapsing mixed records
        # into a misleading single package-level as-of date.
        list_key, date_key = {
            "financial_data": ("公司财务", "_data_period"),
            "announcement_data": ("公告", "date"),
            "news_data": ("新闻", "date"),
        }.get(key, (None, None))
        items = data.get(list_key, []) if isinstance(data, dict) and list_key else []
        metric_fields = (
            "roe_pct", "gross_margin_pct", "revenue_growth_pct",
            "net_profit_growth_pct", "debt_ratio_pct",
        )
        known_dates = set()
        dated_record_count = 0
        missing_metric_period_count = 0
        dated_metric_count = 0
        missing_item_dates = False
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                missing_item_dates = True
                continue
            periods = item.get("_metric_periods") or {}
            item_dates = set()
            if isinstance(item.get(date_key), str) and item[date_key].strip():
                item_dates.add(item[date_key].strip())
            if key == "financial_data":
                for field in metric_fields:
                    if item.get(field) is None:
                        continue
                    period = periods.get(field) if isinstance(periods, dict) else None
                    if isinstance(period, str) and period.strip():
                        item_dates.add(period.strip())
                        dated_metric_count += 1
                    else:
                        missing_metric_period_count += 1
            if item_dates:
                dated_record_count += 1
                known_dates.update(item_dates)
            else:
                missing_item_dates = True
        dates = sorted(known_dates)
        inventory[key] = {
            "source_label": label or None,
            "source_identified": usable,
            "data_as_of": observed if isinstance(observed, str) and observed.strip() else None,
            "observed_dates_or_periods": dates,
            "dated_record_count": dated_record_count,
            "dated_metric_count": dated_metric_count,
            "missing_metric_period_count": missing_metric_period_count,
            "fetch_timestamp": data.get("fetch_timestamp") if isinstance(data, dict) else None,
            "needs_source_review": not usable,
            "needs_date_review": (
                not (isinstance(observed, str) and observed.strip())
                and (not dates or missing_item_dates)
            ) or missing_metric_period_count > 0,
        }
    return inventory



def compare_filing_benchmark(company: dict, benchmark: dict,
                             tolerance_percentage_points="0.05") -> dict:
    """Conservatively compare one provider record with a sourced filing fixture.

    Only leverage is currently considered sufficiently alike in formula for a
    numerical check; even that checks arithmetic agreement, NOT provider
    reliability or consolidated-versus-parent accounting scope. Other labels
    may resemble reported metrics but cannot be silently equated.
    """
    from decimal import Decimal, InvalidOperation

    field_reference = {
        "roe_pct": "weighted_average_roe_h1",
        "gross_margin_pct": "gross_margin_on_operating_revenue_h1",
        "revenue_growth_pct": "operating_revenue_yoy_h1",
        "net_profit_growth_pct": "attributable_net_profit_yoy_h1",
        "debt_ratio_pct": "total_liabilities_to_assets_2025_06_30",
    }
    reported = benchmark.get("reported_percent") or {}
    derived = benchmark.get("derived_percent_expected") or {}
    comparable_field = "debt_ratio_pct"
    result = {
        "benchmark_source": (benchmark.get("source") or {}).get("url"),
        "scope": "provider_snapshot_arithmetic_only_not_fact_certification",
        "comparison_period": benchmark.get("period"),
        "checks": {},
    }
    try:
        tolerance = Decimal(str(tolerance_percentage_points))
        if not tolerance.is_finite() or tolerance < 0:
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Tolerance must be a nonnegative finite decimal") from None

    company_matches = str(company.get("code", "")) == str(benchmark.get("stock_code", ""))
    periods = company.get("_metric_periods") or {}
    methods = company.get("_metric_methods") or {}
    for field, primary_key in field_reference.items():
        expected = (reported if field == "roe_pct" else derived).get(primary_key)
        check = {"status": None, "provider_value": company.get(field),
                 "official_value": expected,
                 "provider_period": periods.get(field),
                 "provider_method": methods.get(field)}
        if not company_matches:
            check["status"] = "company_mismatch"
        elif field != comparable_field:
            check["status"] = "definition_not_yet_verified"
        elif periods.get(field) != benchmark.get("period"):
            check["status"] = "period_mismatch"
        elif methods.get(field) != "balance.liabilityToAsset":
            check["status"] = "method_mismatch"
        else:
            try:
                current = Decimal(str(company.get(field)))
                reference = Decimal(str(expected))
                if not current.is_finite() or not reference.is_finite():
                    check["status"] = "invalid_number"
                elif abs(current - reference) <= tolerance:
                    check["status"] = "snapshot_value_match"
                else:
                    check["status"] = "snapshot_value_mismatch"
            except (InvalidOperation, ValueError, TypeError):
                check["status"] = "invalid_number"
        result["checks"][field] = check
    return result

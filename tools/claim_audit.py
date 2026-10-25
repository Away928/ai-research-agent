"""Deterministic checks for explicitly annotated financial data references.

This checks the pair (stock code, metric, numeric value) against the supplied
collection snapshot. It does not verify the external provider, the prose around
the marker, unannotated numbers, aggregates, or the investment conclusion.
"""

import re
from decimal import Decimal, InvalidOperation

FIELDS = frozenset((
    "roe_pct", "gross_margin_pct", "revenue_growth_pct",
    "net_profit_growth_pct", "debt_ratio_pct",
))
_MARKERS = re.compile(r"\[\[FIN-[^\]\n]*\]\]")
_VALID = re.compile(
    r"\[\[FIN-(?P<code>[A-Za-z0-9.]+)-"
    r"(?P<field>roe_pct|gross_margin_pct|revenue_growth_pct|"
    r"net_profit_growth_pct|debt_ratio_pct)="
    r"(?P<value>[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+))\]\]"
)


def audit_financial_markers(text: str, snapshot: dict) -> list[dict]:
    """Return one record per FIN marker, including malformed markers.

    Matched means *only* the annotated number agrees with one local snapshot.
    Empty results are not a successful fact check.
    """
    companies = ((snapshot or {}).get("financial_data") or {}).get("公司财务") or []
    by_code = {}
    for company in companies:
        if isinstance(company, dict) and company.get("code") is not None:
            by_code.setdefault(str(company["code"]), []).append(company)

    results = []
    for token in _MARKERS.finditer(text or ""):
        raw = token.group(0)
        parsed = _VALID.fullmatch(raw)
        result = {"marker": raw, "status": "malformed", "source_value": None,
                  "source_period": None, "source_label": None}
        if not parsed:
            results.append(result)
            continue
        code, field, supplied = (
            parsed.group("code"), parsed.group("field"), parsed.group("value")
        )
        result.update({"code": code, "field": field, "stated_value": supplied})
        matches = by_code.get(code, [])
        if not matches:
            result["status"] = "unknown_record"
        elif len(matches) != 1:
            result["status"] = "ambiguous_record"
        else:
            record = matches[0]
            actual = record.get(field)
            result["source_value"] = actual
            result["source_period"] = (record.get("_metric_periods") or {}).get(field)
            result["source_label"] = record.get("_source")
            try:
                if isinstance(actual, bool) or actual is None:
                    result["status"] = "missing_value"
                elif Decimal(str(actual)).is_finite() and Decimal(supplied) == Decimal(str(actual)):
                    result["status"] = "record_value_match"
                else:
                    result["status"] = "value_mismatch"
            except (InvalidOperation, ValueError, TypeError):
                result["status"] = "invalid_source_value"
        results.append(result)
    return results

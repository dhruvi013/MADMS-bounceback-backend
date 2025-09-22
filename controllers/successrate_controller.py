from typing import Dict, List, Tuple


def _parse_triple(value: str) -> int:
    """
    Parse strings like "60+06+00" or "60+NA+00" into an integer sum.
    Treats NA and empty parts as 0.
    """
    if not value:
        return 0
    parts = [p.strip().upper() for p in value.split("+")]
    total = 0
    for p in parts:
        if p in ("", "NA"):
            v = 0
        else:
            try:
                v = int(p)
            except Exception:
                v = 0
        total += v
    return total


def _sum_row(row: Dict[str, str]) -> int:
    return _parse_triple(row.get("y1", "")) + _parse_triple(row.get("y2", "")) + _parse_triple(row.get("y3", "")) + _parse_triple(row.get("y4", ""))


def _marks_from_percentage_10(p: float) -> int:
    if p >= 90:
        return 10
    if p >= 80:
        return 8
    if p >= 70:
        return 6
    if p >= 60:
        return 4
    return 2


def compute_success_rate_tables(
    without_backlog: List[Dict[str, str]],
    with_backlog: List[Dict[str, str]],
) -> Dict[str, object]:
    """
    Pure function to compute totals and marks for 4.2 tables.
    Input rows are dictionaries with keys: label, entry, y1, y2, y3, y4.
    Returns totals, percentages, and marks (each out of 10) and combined score (out of 20).
    """
    total_without = sum(_sum_row(r) for r in without_backlog)
    total_with = sum(_sum_row(r) for r in with_backlog)
    total_graduated = total_without + total_with

    pct_without = (total_without / total_graduated * 100.0) if total_graduated else 0.0
    pct_with = (total_with / total_graduated * 100.0) if total_graduated else 0.0

    marks_without = _marks_from_percentage_10(pct_without)
    marks_with = _marks_from_percentage_10(pct_with)

    return {
        "total_without": total_without,
        "total_with": total_with,
        "total_graduated": total_graduated,
        "pct_without": pct_without,
        "pct_with": pct_with,
        "marks_without": marks_without,
        "marks_with": marks_with,
        "score_4_2": marks_without + marks_with,
    }


# Note: This module is intentionally not registered in Flask. It can be imported
# by a controller endpoint in future if backend calculation is needed.



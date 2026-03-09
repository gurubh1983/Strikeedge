from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IndicatorCondition:
    field: str
    operator: str
    value: float


@dataclass(slots=True)
class ConditionGroup:
    logical_operator: str
    conditions: list[IndicatorCondition]


def check_condition(
    indicator_value: float | None,
    condition: IndicatorCondition,
    *,
    previous_value: float | None = None,
) -> bool:
    if indicator_value is None and condition.operator not in {"crosses_above", "crosses_below"}:
        return False
    left = float(indicator_value or 0)
    right = condition.value
    op = condition.operator
    if op == ">":
        return left > right
    if op == "<":
        return left < right
    if op == ">=":
        return left >= right
    if op == "<=":
        return left <= right
    if op == "crosses_above":
        if previous_value is None or indicator_value is None:
            return False
        return float(previous_value) <= right and left > right
    if op == "crosses_below":
        if previous_value is None or indicator_value is None:
            return False
        return float(previous_value) >= right and left < right
    return left == right


def evaluate_group(row: dict, previous_row: dict | None, group: ConditionGroup) -> bool:
    results: list[bool] = []
    for condition in group.conditions:
        current = row.get(condition.field)
        prev = previous_row.get(condition.field) if previous_row else None
        results.append(check_condition(current, condition, previous_value=prev))
    if not results:
        return True
    if group.logical_operator.upper() == "OR":
        return any(results)
    return all(results)


def screen_rows(rows: list[dict], conditions: list[IndicatorCondition], *, previous_rows: dict[str, dict] | None = None) -> list[dict]:
    matches: list[dict] = []
    previous_rows = previous_rows or {}
    for row in rows:
        ok = True
        for condition in conditions:
            prev = previous_rows.get(str(row.get("token", "")), {})
            if not check_condition(row.get(condition.field), condition, previous_value=prev.get(condition.field)):
                ok = False
                break
        if ok:
            matches.append(row)
    return matches


def screen_rows_by_groups(rows: list[dict], groups: list[ConditionGroup], *, previous_rows: dict[str, dict] | None = None) -> list[dict]:
    matches: list[dict] = []
    previous_rows = previous_rows or {}
    for row in rows:
        prev = previous_rows.get(str(row.get("token", "")))
        if all(evaluate_group(row, prev, group) for group in groups):
            matches.append(row)
    return matches


class Scanner:
    def __init__(self, groups: list[ConditionGroup] | None = None) -> None:
        self.groups = groups or []

    def run(self, rows: list[dict], previous_rows: dict[str, dict] | None = None) -> list[dict]:
        if not self.groups:
            return rows
        return screen_rows_by_groups(rows, self.groups, previous_rows=previous_rows)

from __future__ import annotations

from gm_roller.dice.context import RollContext


def matches(condition: str, ctx: RollContext) -> bool:
    if condition == "always":
        return True
    if condition == "crit":
        return ctx.is_crit
    if condition == "nat_20":
        return ctx.is_nat_20
    if condition.startswith("option:"):
        return condition.removeprefix("option:") in ctx.enabled_options
    if condition.startswith("tag:"):
        return condition.removeprefix("tag:") in ctx.component_tags
    if condition.startswith("not:"):
        return not matches(condition.removeprefix("not:"), ctx)
    raise ValueError(f"unknown condition: {condition!r}")
